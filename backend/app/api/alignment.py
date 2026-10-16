"""Alignment checker routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.manuscript import AlignmentIssue
from app.models.user import User
from app.schemas.research import AlignmentIssueOut, AlignmentReportOut
from app.services.access import get_project_for_user
from app.services.alignment_service import chain_status, run_alignment_check

router = APIRouter(prefix="/projects/{project_id}/alignment", tags=["alignment"])


@router.post("/check", response_model=AlignmentReportOut)
def check_alignment(
    project_id: int,
    language: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AlignmentReportOut:
    project = get_project_for_user(db, project_id, user)
    lang = language or user.preferred_language or project.writing_language
    issues = run_alignment_check(db, project, language=lang)
    summary: dict[str, int] = {"information": 0, "warning": 0, "major": 0, "critical": 0}
    for i in issues:
        summary[i.severity] = summary.get(i.severity, 0) + 1
    return AlignmentReportOut(
        project_id=project_id,
        issues=[AlignmentIssueOut.model_validate(i) for i in issues],
        summary=summary,
        chain_status=chain_status(project, db),
    )


@router.get("/issues", response_model=list[AlignmentIssueOut])
def list_issues(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AlignmentIssueOut]:
    get_project_for_user(db, project_id, user)
    rows = (
        db.query(AlignmentIssue)
        .filter(AlignmentIssue.project_id == project_id)
        .order_by(AlignmentIssue.id.desc())
        .all()
    )
    return [AlignmentIssueOut.model_validate(r) for r in rows]
