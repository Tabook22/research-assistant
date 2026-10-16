"""Research project routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.mixins import DOCUMENT_TYPES, RESEARCH_STAGES
from app.models.user import User
from app.schemas.project import (
    ProfileOut,
    ProfileUpdate,
    ProjectCreate,
    ProjectOut,
    ProjectSummaryOut,
    ProjectUpdate,
    StageDefinitionOut,
    StageProgressOut,
    StageProgressUpdate,
)
from app.services import project_service
from app.services.access import get_project_for_user

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/meta/stages", response_model=list[StageDefinitionOut])
def list_stages() -> list[StageDefinitionOut]:
    return [StageDefinitionOut(**s) for s in RESEARCH_STAGES]


@router.get("/meta/document-types")
def list_document_types() -> list[str]:
    return DOCUMENT_TYPES


@router.post("", response_model=ProjectOut)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectOut:
    project = project_service.create_project(db, user.id, payload)
    return ProjectOut.model_validate(project)


@router.get("", response_model=list[ProjectSummaryOut])
def list_projects(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ProjectSummaryOut]:
    if user.is_superuser:
        from app.models.project import ResearchProject
        projects = db.query(ResearchProject).order_by(ResearchProject.updated_at.desc()).all()
    else:
        projects = project_service.list_projects(db, user.id)
    return [ProjectSummaryOut.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectOut:
    project = get_project_for_user(db, project_id, user)
    full = project_service.get_project(db, project.id)
    return ProjectOut.model_validate(full)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectOut:
    project = get_project_for_user(db, project_id, user)
    updated = project_service.update_project(db, project, payload)
    return ProjectOut.model_validate(updated)


@router.patch("/{project_id}/profile", response_model=ProfileOut)
def update_profile(
    project_id: int,
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProfileOut:
    project = get_project_for_user(db, project_id, user)
    profile = project_service.update_profile(db, project, payload)
    return ProfileOut.model_validate(profile)


@router.get("/{project_id}/profile", response_model=ProfileOut)
def get_profile(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProfileOut:
    project = get_project_for_user(db, project_id, user)
    if not project.profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProfileOut.model_validate(project.profile)


@router.patch("/{project_id}/stages/{stage_key}", response_model=StageProgressOut)
def update_stage(
    project_id: int,
    stage_key: str,
    payload: StageProgressUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StageProgressOut:
    project = get_project_for_user(db, project_id, user)
    valid_keys = {s["key"] for s in RESEARCH_STAGES}
    if stage_key not in valid_keys:
        raise HTTPException(status_code=400, detail="Unknown stage key")
    progress = project_service.update_stage(db, project, stage_key, payload.status, payload.notes)
    return StageProgressOut.model_validate(progress)
