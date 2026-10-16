"""Document upload routes."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.document import UploadedDocument
from app.models.user import User
from app.schemas.document import DocumentOut, DocumentTextOut
from app.services.access import get_project_for_user
from app.services.document_service import get_document_text, save_upload

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
def list_documents(
    project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[DocumentOut]:
    get_project_for_user(db, project_id, user)
    rows = db.query(UploadedDocument).filter(UploadedDocument.project_id == project_id).all()
    return [DocumentOut.model_validate(r) for r in rows]


@router.post("", response_model=DocumentOut)
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    category: str = Form("reference_material"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DocumentOut:
    project = get_project_for_user(db, project_id, user)
    doc = await save_upload(db, project, user.id, file, category=category)
    return DocumentOut.model_validate(doc)


@router.get("/{document_id}/text", response_model=DocumentTextOut)
def document_text(
    project_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DocumentTextOut:
    get_project_for_user(db, project_id, user)
    doc = db.get(UploadedDocument, document_id)
    if not doc or doc.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks, total = get_document_text(db, doc)
    return DocumentTextOut(
        document_id=doc.id,
        original_filename=doc.original_filename,
        chunks=chunks,
        total_chars=total,
    )


@router.get("/{document_id}/file")
def original_document(project_id:int,document_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    from pathlib import Path
    from fastapi.responses import FileResponse
    get_project_for_user(db,project_id,user)
    doc=db.get(UploadedDocument,document_id)
    if not doc or doc.project_id!=project_id or not Path(doc.storage_path).is_file():raise HTTPException(404,"Original file not found")
    return FileResponse(doc.storage_path,filename=doc.original_filename,content_disposition_type="inline")
