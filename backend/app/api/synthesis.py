"""Automated multi-document synthesis dashboard API."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.synthesis import SynthesisRequest, SynthesisResponse
from app.services.access import get_project_for_user
from app.services.synthesis_service import build_synthesis_dashboard

router = APIRouter(prefix="/projects/{project_id}/synthesis", tags=["synthesis"])


@router.post("/dashboard", response_model=SynthesisResponse)
async def synthesis_dashboard(
    project_id: int,
    payload: SynthesisRequest | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SynthesisResponse:
    project = get_project_for_user(db, project_id, user)
    body = payload or SynthesisRequest()
    lang = body.language or user.preferred_language or project.writing_language
    result = await build_synthesis_dashboard(
        db,
        project,
        document_ids=body.document_ids,
        language=lang,
    )
    return SynthesisResponse(**result)
