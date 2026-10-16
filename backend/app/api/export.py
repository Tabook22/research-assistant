"""Export routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.export import ExportOut, ExportRequest
from app.services.access import get_project_for_user
from app.services.export_service import export_project

router = APIRouter(prefix="/projects/{project_id}/export", tags=["export"])


@router.post("", response_model=ExportOut)
def create_export(
    project_id: int,
    payload: ExportRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ExportOut:
    project = get_project_for_user(db, project_id, user)
    record = export_project(db, project, payload.export_type, payload.format)
    content = getattr(record, "_full_content", record.content_preview or "")
    return ExportOut(
        id=record.id,
        project_id=record.project_id,
        export_type=record.export_type,
        format=record.format,
        content=content,
        created_at=record.created_at,
    )
