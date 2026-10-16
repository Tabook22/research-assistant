"""Authenticated paper analysis, section discussion and versioned drafts."""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from fastapi.responses import FileResponse
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import update
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from app.core.deps import get_current_user
from app.database import get_db
from app.config import get_settings
from app.models.user import User
from app.models.paper_review import PaperReview
from app.schemas.paper_review import Action, AnalyzeRequest, DraftUpdate, ComplianceStart, RewriteStart, PaperChatRequest, PaperChatSearch, ChatSessionCreate, ChatSessionRename
from app.services import scientific_assessment as assessment
from app.services import paper_rewrite
from app.services import paper_annotations
from app.services import paper_chat
from app.services import scientific_rubric
from app.services.access import get_project_for_user
from app.services import paper_review_service as svc

router=APIRouter(prefix="/projects/{project_id}/paper-reviews", tags=["paper-reviews"])

def load(db, project_id, review_id, user):
    get_project_for_user(db,project_id,user)
    row=db.get(PaperReview,review_id)
    if row is None or row.project_id != project_id:
        raise HTTPException(404,"Paper review not found")
    return row

def result(row):
    state={k:deepcopy(v) for k,v in row.state.items() if not k.startswith('_')}
    if state.get('paper_chat'):
        state['paper_chat']=paper_chat.history(state)
    if state.get('compliance'):
        state['compliance']['stale']=assessment.stale(state,state['compliance'])
    if state.get('rewrite'):
        state['rewrite']['stale']=paper_rewrite.stale(state,state['rewrite'])
        state['rewrite'].pop('context',None)
    if state.get('previous_rewrite'):
        state['previous_rewrite'].pop('context',None)
    return {"id":row.id,"project_id":row.project_id,"filename":row.filename,"language":row.language,"version":row.version,"updated_at":row.updated_at,**state}

def save(db,row,state,version):
    changed=db.execute(update(PaperReview).where(PaperReview.id==row.id,PaperReview.version==version).values(state=state,version=version+1,updated_at=datetime.now(timezone.utc)))
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409,"This review changed in another tab. Reload before saving; your local draft has not been overwritten.")
    db.commit(); db.refresh(row)
    return result(row)

def section_state(row,section_id,version):
    if row.version != version:
        raise HTTPException(409,"This review changed. Reload before continuing.")
    state=deepcopy(row.state)
    section=next((s for s in state["sections"] if s["id"]==section_id),None)
    if section is None:
        raise HTTPException(404,"Section not found")
    return state,section

@router.post('/{review_id}/sections/{section_id}/annotations')
async def passage_annotations(project_id:int, review_id:int, section_id:int, payload:AnalyzeRequest, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    row=load(db,project_id,review_id,user)
    state,section=section_state(row,section_id,payload.version)
    state=await paper_annotations.annotate(state,section,row.language)
    return save(db,row,state,payload.version)

@router.post('/{review_id}/chat')
async def chat_with_paper(project_id:int, review_id:int, payload:PaperChatRequest, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    row=load(db,project_id,review_id,user)
    if row.version!=payload.version:raise HTTPException(409,'This review changed. Reload before continuing.')
    state=await paper_chat.discuss(deepcopy(row.state),payload.language or row.language,payload.instruction,payload.section_id,payload.search_id,payload.session_id)
    return save(db,row,state,payload.version)

@router.post('/{review_id}/chat/search')
async def search_for_paper_chat(project_id:int, review_id:int, payload:PaperChatSearch, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    row=load(db,project_id,review_id,user)
    if row.version!=payload.version:raise HTTPException(409,'This review changed. Reload before continuing.')
    state=await paper_chat.search(deepcopy(row.state),payload.proposal_id,payload.query,payload.consent,payload.language or row.language,payload.session_id)
    return save(db,row,state,payload.version)

@router.post('/{review_id}/chat/sessions')
def create_chat_session(project_id:int, review_id:int, payload:ChatSessionCreate, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    row=load(db,project_id,review_id,user)
    if row.version!=payload.version:raise HTTPException(409,'This review changed. Reload before continuing.')
    return save(db,row,paper_chat.create_session(deepcopy(row.state),payload.title),payload.version)

@router.patch('/{review_id}/chat/sessions/{session_id}')
def rename_chat_session(project_id:int, review_id:int, session_id:str, payload:ChatSessionRename, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    row=load(db,project_id,review_id,user)
    if row.version!=payload.version:raise HTTPException(409,'This review changed. Reload before continuing.')
    return save(db,row,paper_chat.rename_session(deepcopy(row.state),session_id,payload.title),payload.version)

@router.get("")
def list_reviews(project_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    get_project_for_user(db,project_id,user)
    return [{"id":r.id,"filename":r.filename,"language":r.language,"updated_at":r.updated_at,"analysis_mode":r.state["analysis_mode"]} for r in db.query(PaperReview).filter_by(project_id=project_id).order_by(PaperReview.updated_at.desc()).all()]

@router.get('/criteria/catalog')
def criteria_catalog(project_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    get_project_for_user(db,project_id,user)
    return scientific_rubric.catalog()

@router.post('/{review_id}/compliance/start')
def start_compliance(project_id:int,review_id:int,payload:ComplianceStart,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    row=load(db,project_id,review_id,user)
    if row.version!=payload.version:raise HTTPException(409,'This review changed. Reload before continuing.')
    return save(db,row,assessment.start(deepcopy(row.state),payload.paper_type,payload.basis),payload.version)

@router.post('/{review_id}/compliance/next')
async def next_compliance(project_id:int,review_id:int,payload:AnalyzeRequest,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    row=load(db,project_id,review_id,user)
    if row.version!=payload.version:raise HTTPException(409,'This review changed. Reload before continuing.')
    state=await assessment.advance(deepcopy(row.state),row.language)
    return save(db,row,state,payload.version)

@router.post("",status_code=201)
async def upload(project_id:int,file:UploadFile=File(...),language:str=Query("en",pattern="^(en|ar)$"),db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    get_project_for_user(db,project_id,user)
    ext=Path(file.filename or "").suffix.lower()
    if ext not in {".pdf",".docx",".txt"}:
        raise HTTPException(415,"Upload a PDF, DOCX, or TXT paper.")
    limit=get_settings().max_upload_bytes
    content=await file.read(limit+1)
    if len(content)>limit:
        raise HTTPException(413,"File exceeds the upload size limit.")
    if not content:
        raise HTTPException(400,"The file is empty.")
    try:
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/("paper"+ext); path.write_bytes(content)
            pages=await run_in_threadpool(svc.extract_pages,path,ext)
            state=svc.build_state(pages,language)
            state["source_format"]=ext.lstrip(".")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(422,"This file could not be read. Try a searchable PDF, DOCX, or UTF-8 TXT file.") from exc
    # Save extraction first: an unavailable AI provider must not lose the uploaded text.
    source_root=Path(get_settings().upload_dir)/"paper-reviews"/str(project_id)
    source_root.mkdir(parents=True,exist_ok=True)
    original_path=source_root/(uuid4().hex+ext)
    original_path.write_bytes(content)
    state["_source_file"]=str(original_path.resolve())
    row=PaperReview(project_id=project_id,filename=Path(file.filename).name,language=language,state=state)
    try:
        db.add(row); db.commit(); db.refresh(row)
    except Exception:
        db.rollback();original_path.unlink(missing_ok=True);raise
    return result(row)

@router.get("/{review_id}")
def get_review(project_id:int,review_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    return result(load(db,project_id,review_id,user))

@router.post("/{review_id}/analyze")
async def analyze_review(project_id:int,review_id:int,payload:AnalyzeRequest,overview_only:bool=False,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    row=load(db,project_id,review_id,user)
    if row.version != payload.version:
        raise HTTPException(409,"This review changed. Reload before continuing.")
    state=await svc.analyze(deepcopy(row.state),row.language,overview_only=overview_only)
    return save(db,row,state,payload.version)

@router.post("/{review_id}/sections/{section_id}/analyze")
async def analyze_section(project_id:int,review_id:int,section_id:int,payload:AnalyzeRequest,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    row=load(db,project_id,review_id,user)
    state,section=section_state(row,section_id,payload.version)
    state=await svc.analyze_section(state,section,row.language)
    return save(db,row,state,payload.version)

@router.post("/{review_id}/sections/{section_id}/discuss")
async def discuss(project_id:int,review_id:int,section_id:int,payload:Action,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    row=load(db,project_id,review_id,user)
    state,section=section_state(row,section_id,payload.version)
    if not payload.instruction.strip():
        raise HTTPException(422,"Enter a question.")
    reply=await svc.section_action(state,section,row.language,payload.instruction,False)
    now=datetime.now(timezone.utc).isoformat()
    section["messages"].extend([{"role":"user","content":payload.instruction,"created_at":now},{"role":"assistant","content":reply,"created_at":now}])
    return save(db,row,state,payload.version)

@router.post("/{review_id}/sections/{section_id}/suggest")
async def suggest(project_id:int,review_id:int,section_id:int,payload:Action,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    row=load(db,project_id,review_id,user)
    state,section=section_state(row,section_id,payload.version)
    if not payload.instruction.strip():
        raise HTTPException(422,"Enter an improvement goal.")
    section["proposed_text"]=await svc.section_action(state,section,row.language,payload.instruction,True)
    return save(db,row,state,payload.version)

@router.patch("/{review_id}/sections/{section_id}/draft")
def save_draft(project_id:int,review_id:int,section_id:int,payload:DraftUpdate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    row=load(db,project_id,review_id,user)
    state,section=section_state(row,section_id,payload.version)
    if section.get("draft") != payload.text:
        section["revisions"].append({"text":payload.text,"saved_at":datetime.now(timezone.utc).isoformat()})
        section["draft"]=payload.text
    return save(db,row,state,payload.version)


@router.get("/{review_id}/file")
def original_file(project_id:int,review_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    row=load(db,project_id,review_id,user)
    stored=row.state.get("_source_file")
    if not stored:raise HTTPException(404,"This older review retains extracted text only. Upload the original again to enable file viewing.")
    path=Path(stored).resolve();root=(Path(get_settings().upload_dir)/"paper-reviews"/str(project_id)).resolve()
    if not path.is_relative_to(root) or not path.is_file():raise HTTPException(404,"Original file is unavailable.")
    media={".pdf":"application/pdf",".docx":"application/vnd.openxmlformats-officedocument.wordprocessingml.document",".txt":"text/plain"}.get(path.suffix,"application/octet-stream")
    return FileResponse(path,media_type=media,filename=row.filename,content_disposition_type="inline")

@router.post('/{review_id}/rewrite/start')
async def start_rewrite(project_id:int,review_id:int,payload:RewriteStart,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    row=load(db,project_id,review_id,user)
    if row.version!=payload.version:raise HTTPException(409,'This review changed. Reload before continuing.')
    state=await paper_rewrite.start(deepcopy(row.state),row.language,payload.paper_type,payload.basis,payload.instruction)
    return save(db,row,state,payload.version)

@router.post('/{review_id}/rewrite/next')
async def next_rewrite(project_id:int,review_id:int,payload:AnalyzeRequest,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    row=load(db,project_id,review_id,user)
    if row.version!=payload.version:raise HTTPException(409,'This review changed. Reload before continuing.')
    state=await paper_rewrite.advance(deepcopy(row.state),row.language)
    return save(db,row,state,payload.version)

@router.post('/{review_id}/rewrite/copy')
def copy_rewrite(project_id:int,review_id:int,payload:AnalyzeRequest,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    row=load(db,project_id,review_id,user)
    if row.version!=payload.version:raise HTTPException(409,'This review changed. Reload before continuing.')
    state=deepcopy(row.state)
    copied_state=paper_rewrite.copy_state(state,row.language)
    existing=state['rewrite'].get('copy_id')
    if existing:
        copied=load(db,project_id,existing,user)
        return result(copied)
    copied_state['origin_review_id']=row.id
    copied=PaperReview(project_id=project_id,filename=Path(row.filename).stem[:180]+'-AI-proposal.txt',language=row.language,state=copied_state)
    db.add(copied);db.flush()
    state['rewrite']['copy_id']=copied.id
    save(db,row,state,payload.version)
    db.refresh(copied)
    return result(copied)
