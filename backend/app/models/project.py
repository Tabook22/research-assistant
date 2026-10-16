"""Research project, profile, members, and stage progress."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class ResearchProject(Base, TimestampMixin):
    __tablename__ = "research_projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    working_title: Mapped[str] = mapped_column(String(500), nullable=False)
    research_field: Mapped[str | None] = mapped_column(String(255))
    document_type: Mapped[str] = mapped_column(String(50), default="research_proposal")
    current_stage: Mapped[str] = mapped_column(String(50), default="idea", index=True)
    writing_language: Mapped[str] = mapped_column(String(10), default="en")
    target_institution: Mapped[str | None] = mapped_column(String(500))
    target_journal: Mapped[str | None] = mapped_column(String(500))
    citation_style: Mapped[str] = mapped_column(String(50), default="APA 7")
    study_context: Mapped[str | None] = mapped_column(Text)
    population_summary: Mapped[str | None] = mapped_column(Text)
    deadline: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)
    completion_percent: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text)

    owner = relationship("User", back_populates="projects")
    profile = relationship(
        "ResearchProjectProfile",
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan",
    )
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    stage_progress = relationship(
        "StageProgress", back_populates="project", cascade="all, delete-orphan"
    )
    conversations = relationship(
        "Conversation", back_populates="project", cascade="all, delete-orphan"
    )
    problems = relationship(
        "ResearchProblem", back_populates="project", cascade="all, delete-orphan"
    )
    gaps = relationship("ResearchGap", back_populates="project", cascade="all, delete-orphan")
    objectives = relationship(
        "ResearchObjective", back_populates="project", cascade="all, delete-orphan"
    )
    questions = relationship(
        "ResearchQuestion", back_populates="project", cascade="all, delete-orphan"
    )
    hypotheses = relationship("Hypothesis", back_populates="project", cascade="all, delete-orphan")
    constructs = relationship("Construct", back_populates="project", cascade="all, delete-orphan")
    variables = relationship("Variable", back_populates="project", cascade="all, delete-orphan")
    designs = relationship("ResearchDesign", back_populates="project", cascade="all, delete-orphan")
    populations = relationship("Population", back_populates="project", cascade="all, delete-orphan")
    sampling_plans = relationship(
        "SamplingPlan", back_populates="project", cascade="all, delete-orphan"
    )
    instruments = relationship("Instrument", back_populates="project", cascade="all, delete-orphan")
    analysis_plans = relationship(
        "AnalysisPlan", back_populates="project", cascade="all, delete-orphan"
    )
    documents = relationship(
        "UploadedDocument", back_populates="project", cascade="all, delete-orphan"
    )
    literature_searches = relationship(
        "LiteratureSearch", back_populates="project", cascade="all, delete-orphan"
    )
    references = relationship("Reference", back_populates="project", cascade="all, delete-orphan")
    manuscript_sections = relationship(
        "ManuscriptSection", back_populates="project", cascade="all, delete-orphan"
    )
    alignment_issues = relationship(
        "AlignmentIssue", back_populates="project", cascade="all, delete-orphan"
    )
    decisions = relationship(
        "ResearcherDecision", back_populates="project", cascade="all, delete-orphan"
    )
    ai_suggestions = relationship(
        "AISuggestion", back_populates="project", cascade="all, delete-orphan"
    )
    exports = relationship("ExportRecord", back_populates="project", cascade="all, delete-orphan")


class ResearchProjectProfile(Base, TimestampMixin):
    """Structured Research Project Profile workspace."""

    __tablename__ = "research_project_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), unique=True, index=True
    )
    research_problem: Mapped[str | None] = mapped_column(Text)
    existing_evidence: Mapped[str | None] = mapped_column(Text)
    research_gap: Mapped[str | None] = mapped_column(Text)
    overall_aim: Mapped[str | None] = mapped_column(Text)
    expected_contribution: Mapped[str | None] = mapped_column(Text)
    ethics_requirements: Mapped[str | None] = mapped_column(Text)
    unresolved_decisions: Mapped[str | None] = mapped_column(Text)
    assumptions_requiring_verification: Mapped[str | None] = mapped_column(Text)
    researcher_approved_summary: Mapped[str | None] = mapped_column(Text)
    ai_suggestions_summary: Mapped[str | None] = mapped_column(Text)
    refined_idea: Mapped[str | None] = mapped_column(Text)
    proposed_scope: Mapped[str | None] = mapped_column(Text)
    key_concepts: Mapped[str | None] = mapped_column(Text)
    initial_search_terms: Mapped[str | None] = mapped_column(Text)
    scientific_significance: Mapped[str | None] = mapped_column(Text)
    practical_significance: Mapped[str | None] = mapped_column(Text)
    extra_json: Mapped[str | None] = mapped_column(Text)  # JSON blob for flexible fields

    project = relationship("ResearchProject", back_populates="profile")


class ProjectMember(Base, TimestampMixin):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_member"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(50), default="collaborator")  # owner, collaborator, supervisor

    project = relationship("ResearchProject", back_populates="members")
    user = relationship("User", back_populates="memberships")


class StageProgress(Base, TimestampMixin):
    __tablename__ = "stage_progress"
    __table_args__ = (UniqueConstraint("project_id", "stage_key", name="uq_project_stage"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    stage_key: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(50), default="not_started")
    notes: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project = relationship("ResearchProject", back_populates="stage_progress")
