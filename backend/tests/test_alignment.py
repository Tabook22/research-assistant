"""Unit tests for alignment checker."""

import uuid

from app.database import Base, SessionLocal, engine
from app.models.project import ResearchProject, ResearchProjectProfile
from app.models.research import ResearchObjective, ResearchQuestion
from app.models.user import User
from app.core.security import hash_password
from app.services.alignment_service import run_alignment_check, chain_status


def setup_module() -> None:
    Base.metadata.create_all(bind=engine)


def test_alignment_detects_missing_problem_and_unlinked_question() -> None:
    db = SessionLocal()
    try:
        user = User(
            email=f"align_{uuid.uuid4().hex[:10]}@test.com",
            full_name="Align Tester",
            hashed_password=hash_password("password123"),
        )
        db.add(user)
        db.flush()
        project = ResearchProject(
            owner_id=user.id,
            working_title="Test alignment project",
            document_type="research_proposal",
        )
        db.add(project)
        db.flush()
        db.add(ResearchProjectProfile(project_id=project.id))
        q = ResearchQuestion(
            project_id=project.id,
            text="What is the prevalence of X?",
            question_type="descriptive",
        )
        db.add(q)
        db.commit()

        issues = run_alignment_check(db, project)
        types = {i.issue_type for i in issues}
        assert "missing_problem" in types
        assert "question_without_objective" in types
        assert "missing_aim" in types

        status = chain_status(project, db)
        assert status["research_questions"] == "present"
        assert status["research_problem"] == "missing"
    finally:
        db.close()


def test_alignment_question_with_objective_ok_for_that_rule() -> None:
    db = SessionLocal()
    try:
        user = User(
            email=f"align2_{uuid.uuid4().hex[:10]}@test.com",
            full_name="Align Tester 2",
            hashed_password=hash_password("password123"),
        )
        db.add(user)
        db.flush()
        project = ResearchProject(
            owner_id=user.id,
            working_title="Linked QO project",
        )
        db.add(project)
        db.flush()
        db.add(
            ResearchProjectProfile(
                project_id=project.id,
                research_problem="Problem exists",
                research_gap="Gap exists",
                overall_aim="Aim exists",
            )
        )
        q = ResearchQuestion(
            project_id=project.id,
            text="How do A and B relate?",
            question_type="correlational",
            proposed_analysis="Pearson correlation",
        )
        db.add(q)
        db.flush()
        db.add(
            ResearchObjective(
                project_id=project.id,
                question_id=q.id,
                text="Examine the relationship between A and B",
                verb="Examine",
            )
        )
        db.commit()
        issues = run_alignment_check(db, project)
        types = {i.issue_type for i in issues}
        assert "question_without_objective" not in types
        assert "missing_problem" not in types
    finally:
        db.close()
