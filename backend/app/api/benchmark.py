"""Benchmark project against uploaded library papers."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.benchmark import BenchmarkRequest, BenchmarkResponse
from app.services.access import get_project_for_user
from app.services.benchmark_service import benchmark_project

router = APIRouter(prefix="/projects/{project_id}/benchmark", tags=["benchmark"])


@router.post("", response_model=BenchmarkResponse)
async def run_benchmark(
    project_id: int,
    payload: BenchmarkRequest | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BenchmarkResponse:
    project = get_project_for_user(db, project_id, user)
    body = payload or BenchmarkRequest()
    lang = body.language or user.preferred_language or project.writing_language
    result = await benchmark_project(
        db,
        project,
        document_ids=body.document_ids,
        language=lang,
    )
    return BenchmarkResponse(**result)
