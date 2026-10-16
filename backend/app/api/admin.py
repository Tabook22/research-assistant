"""Administrator-managed accounts and explicit access to researchers' workspaces."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, exists, update, func
from sqlalchemy.orm import Session, aliased
from sqlalchemy.exc import IntegrityError
from app.core.deps import get_admin
from app.core.security import hash_password
from app.database import get_db
from app.models.user import User
from app.models.project import ResearchProject
from app.models.paper_review import PaperReview
from app.models.library import SourceDocument
from app.models.document import UploadedDocument
from app.schemas.auth import UserOut, ManagedUserCreate, ManagedUserUpdate
from app.schemas.project import ProjectCreate, ProjectSummaryOut
from app.services import project_service
from app.services.permissions import PERMISSIONS

router=APIRouter(prefix='/admin',tags=['administration'],dependencies=[Depends(get_admin)])

def target(db,ident):
    row=db.get(User,ident)
    if not row:raise HTTPException(404,'User not found.')
    return row

def commit(db):
    try:db.commit()
    except IntegrityError:
        db.rollback();raise HTTPException(409,'Username or email is already in use.')

@router.get('/permissions')
def permissions():return PERMISSIONS

@router.get('/users')
def users(db:Session=Depends(get_db)):
    counts=dict(db.query(ResearchProject.owner_id,func.count(ResearchProject.id)).group_by(ResearchProject.owner_id).all())
    return [{**UserOut.model_validate(row).model_dump(),'project_count':counts.get(row.id,0)} for row in db.query(User).order_by(User.id).all()]

@router.post('/users',response_model=UserOut,status_code=201)
def create_user(payload:ManagedUserCreate,db:Session=Depends(get_db)):
    data=payload.model_dump(exclude={'password'})
    data['email']=str(payload.email).lower() if payload.email else payload.username+'@accounts.invalid'
    row=User(**data,hashed_password=hash_password(payload.password),must_change_password=True)
    db.add(row);commit(db);db.refresh(row)
    return row

@router.patch('/users/{user_id}',response_model=UserOut)
def edit_user(user_id:int,payload:ManagedUserUpdate,db:Session=Depends(get_db),admin:User=Depends(get_admin)):
    row=target(db,user_id)
    values=payload.model_dump(exclude_none=True,exclude={'password'})
    if user_id==admin.id and (values.get('is_active') is False or values.get('is_superuser') is False):
        raise HTTPException(409,'You cannot deactivate or demote your own administrator account.')
    if payload.password:
        values.update(hashed_password=hash_password(payload.password),must_change_password=True)
    values['auth_version']=User.auth_version+1
    query=update(User).where(User.id==user_id)
    if values.get('is_active') is False or values.get('is_superuser') is False:
        other=aliased(User)
        another=exists(select(other.id).where(other.id!=user_id,other.is_active.is_(True),other.is_superuser.is_(True)))
        query=query.where((User.is_superuser.is_(False)) | (User.is_active.is_(False)) | another)
    result=db.execute(query.values(**values))
    if not result.rowcount:
        db.rollback();raise HTTPException(409,'At least one active administrator must remain.')
    commit(db);db.refresh(row)
    return row

@router.get('/users/{user_id}/workspace')
def workspace(user_id:int,db:Session=Depends(get_db)):
    row=target(db,user_id)
    projects=project_service.list_projects(db,user_id)
    ids=[p.id for p in projects]
    papers=[{'id':r.id,'project_id':r.project_id,'title':r.filename,'kind':'review'} for r in db.query(PaperReview).filter(PaperReview.project_id.in_(ids)).all()]
    papers += [{'id':r.id,'project_id':r.project_id,'title':r.original_filename,'kind':'library'} for r in db.query(SourceDocument).filter(SourceDocument.project_id.in_(ids)).all()]
    papers += [{'id':r.id,'project_id':r.project_id,'title':r.original_filename,'kind':'document'} for r in db.query(UploadedDocument).filter(UploadedDocument.project_id.in_(ids)).all()]
    return {'user':UserOut.model_validate(row),'projects':[ProjectSummaryOut.model_validate(p) for p in projects],'papers':papers}

@router.post('/users/{user_id}/projects',response_model=ProjectSummaryOut,status_code=201)
def create_project(user_id:int,payload:ProjectCreate,db:Session=Depends(get_db)):
    target(db,user_id)
    return project_service.create_project(db,user_id,payload)
