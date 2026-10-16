"""AI suggestion review and apply routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.decisions import AISuggestion
from app.models.user import User
from app.schemas.suggestions import AISuggestionOut, SuggestionApplyRequest, SuggestionApplyResult
from app.services.access import get_project_for_user
from app.services.suggestion_service import apply_suggestion, list_pending, suggestion_to_dict

router = APIRouter(prefix="/projects/{project_id}/suggestions", tags=["suggestions"])


@router.get("", response_model=list[AISuggestionOut])
def list_suggestions(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AISuggestionOut]:
    get_project_for_user(db, project_id, user)
    rows = list_pending(db, project_id)
    return [AISuggestionOut(**suggestion_to_dict(r)) for r in rows]


@router.post("/{suggestion_id}/action", response_model=SuggestionApplyResult)
def act_on_suggestion(
    project_id: int,
    suggestion_id: int,
    payload: SuggestionApplyRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SuggestionApplyResult:
    project = get_project_for_user(db, project_id, user)
    row = db.get(AISuggestion, suggestion_id)
    if not row or row.project_id != project_id:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    if row.approval_status in ("approved", "rejected", "superseded"):
        raise HTTPException(
            status_code=400,
            detail=f"Suggestion already {row.approval_status}",
        )
    result = apply_suggestion(
        db,
        project,
        row,
        user_id=user.id,
        action=payload.action,
        edited_payload=payload.edited_payload,
        notes=payload.notes,
        mark_approved=payload.mark_approved,
    )
    return SuggestionApplyResult(**result)
