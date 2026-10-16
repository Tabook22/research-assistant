"""Literature search and reference routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.literature import Reference
from app.models.user import User
from app.schemas.literature import (
    LiteratureSearchOut,
    LiteratureSearchRequest,
    ReferenceCreate,
    ReferenceOut,
    ReferenceUpdate,
)
from app.services.access import get_project_for_user
from app.services.literature_service import add_reference, run_search

router = APIRouter(prefix="/projects/{project_id}", tags=["literature"])


@router.post("/literature/search", response_model=LiteratureSearchOut)
async def search_literature(
    project_id: int,
    payload: LiteratureSearchRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LiteratureSearchOut:
    project = get_project_for_user(db, project_id, user)
    search, results = await run_search(
        db,
        project,
        query=payload.query,
        database_name=payload.database_name,
        year_from=payload.year_from,
        year_to=payload.year_to,
        max_results=payload.max_results,
    )
    return LiteratureSearchOut(
        id=search.id,
        project_id=project_id,
        query=search.query,
        database_name=search.database_name,
        result_count=search.result_count,
        results=results,
        created_at=search.created_at,
    )


@router.get("/references", response_model=list[ReferenceOut])
def list_references(
    project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[ReferenceOut]:
    get_project_for_user(db, project_id, user)
    rows = db.query(Reference).filter(Reference.project_id == project_id).all()
    return [ReferenceOut.model_validate(r) for r in rows]


@router.post("/references", response_model=ReferenceOut)
def create_reference(
    project_id: int,
    payload: ReferenceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReferenceOut:
    project = get_project_for_user(db, project_id, user)
    ref = add_reference(db, project, payload)
    return ReferenceOut.model_validate(ref)


@router.patch("/references/{reference_id}", response_model=ReferenceOut)
def update_reference(
    project_id: int,
    reference_id: int,
    payload: ReferenceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReferenceOut:
    get_project_for_user(db, project_id, user)
    row = db.get(Reference, reference_id)
    if not row or row.project_id != project_id:
        raise HTTPException(status_code=404, detail="Reference not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return ReferenceOut.model_validate(row)


@router.delete("/references/{reference_id}")
def delete_reference(
    project_id: int,
    reference_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    get_project_for_user(db, project_id, user)
    row = db.get(Reference, reference_id)
    if not row or row.project_id != project_id:
        raise HTTPException(status_code=404, detail="Reference not found")
    db.delete(row)
    db.commit()
    return {"ok": True}
