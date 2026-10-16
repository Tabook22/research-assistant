"""Research project lifecycle service."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from app.models.mixins import RESEARCH_STAGES
from app.models.project import ResearchProject, ResearchProjectProfile, StageProgress
from app.schemas.project import ProfileUpdate, ProjectCreate, ProjectUpdate


def _init_stages(db: Session, project: ResearchProject) -> None:
    for stage in RESEARCH_STAGES:
        db.add(
            StageProgress(
                project_id=project.id,
                stage_key=stage["key"],
                status="in_progress" if stage["key"] == "idea" else "not_started",
            )
        )


def create_project(db: Session, owner_id: int, data: ProjectCreate) -> ResearchProject:
    project = ResearchProject(
        owner_id=owner_id,
        working_title=data.working_title,
        research_field=data.research_field,
        document_type=data.document_type,
        writing_language=data.writing_language,
        target_institution=data.target_institution,
        target_journal=data.target_journal,
        citation_style=data.citation_style,
        study_context=data.study_context,
        population_summary=data.population_summary,
        deadline=data.deadline,
        notes=data.notes,
        current_stage=data.current_stage_hint or "idea",
    )
    db.add(project)
    db.flush()

    materials = ", ".join(data.available_materials) if data.available_materials else None
    profile = ResearchProjectProfile(
        project_id=project.id,
        refined_idea=data.research_idea,
        unresolved_decisions=f"Available materials: {materials}" if materials else None,
    )
    db.add(profile)
    _init_stages(db, project)
    db.commit()
    return get_project(db, project.id)


def get_project(db: Session, project_id: int) -> ResearchProject | None:
    return (
        db.query(ResearchProject)
        .options(
            joinedload(ResearchProject.profile),
            joinedload(ResearchProject.stage_progress),
        )
        .filter(ResearchProject.id == project_id)
        .first()
    )


def list_projects(db: Session, owner_id: int) -> list[ResearchProject]:
    return (
        db.query(ResearchProject)
        .filter(ResearchProject.owner_id == owner_id)
        .order_by(ResearchProject.updated_at.desc())
        .all()
    )


def update_project(db: Session, project: ResearchProject, data: ProjectUpdate) -> ResearchProject:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    return get_project(db, project.id)  # type: ignore[return-value]


def update_profile(
    db: Session, project: ResearchProject, data: ProfileUpdate
) -> ResearchProjectProfile:
    profile = project.profile
    if not profile:
        profile = ResearchProjectProfile(project_id=project.id)
        db.add(profile)
        db.flush()
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


def update_stage(
    db: Session, project: ResearchProject, stage_key: str, status: str, notes: str | None = None
) -> StageProgress:
    progress = (
        db.query(StageProgress)
        .filter(StageProgress.project_id == project.id, StageProgress.stage_key == stage_key)
        .first()
    )
    if not progress:
        progress = StageProgress(project_id=project.id, stage_key=stage_key)
        db.add(progress)
    progress.status = status
    if notes is not None:
        progress.notes = notes
    if status == "completed":
        progress.completed_at = datetime.now(timezone.utc)
    project.current_stage = stage_key
    _recalc_completion(project)
    db.commit()
    db.refresh(progress)
    return progress


def _recalc_completion(project: ResearchProject) -> None:
    total = len(RESEARCH_STAGES)
    completed = sum(1 for s in project.stage_progress if s.status == "completed")
    project.completion_percent = int(round((completed / total) * 100)) if total else 0


def build_profile_context(project: ResearchProject) -> dict:
    """Structured profile snapshot for AI context and export."""
    profile = project.profile
    return {
        "working_title": project.working_title,
        "research_field": project.research_field,
        "document_type": project.document_type,
        "research_stage": project.current_stage,
        "writing_language": project.writing_language,
        "target_institution": project.target_institution,
        "target_journal": project.target_journal,
        "citation_style": project.citation_style,
        "study_context": project.study_context,
        "population": project.population_summary,
        "research_problem": profile.research_problem if profile else None,
        "existing_evidence": profile.existing_evidence if profile else None,
        "research_gap": profile.research_gap if profile else None,
        "overall_aim": profile.overall_aim if profile else None,
        "expected_contribution": profile.expected_contribution if profile else None,
        "ethics_requirements": profile.ethics_requirements if profile else None,
        "refined_idea": profile.refined_idea if profile else None,
        "proposed_scope": profile.proposed_scope if profile else None,
        "key_concepts": profile.key_concepts if profile else None,
        "initial_search_terms": profile.initial_search_terms if profile else None,
        "unresolved_decisions": profile.unresolved_decisions if profile else None,
        "assumptions_requiring_verification": (
            profile.assumptions_requiring_verification if profile else None
        ),
        "researcher_approved_summary": (
            profile.researcher_approved_summary if profile else None
        ),
        "ai_suggestions_awaiting_approval": (
            profile.ai_suggestions_summary if profile else None
        ),
    }
