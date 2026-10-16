"""Project-isolated retrieval, evidence snapshots, memory and resumable work records."""
from sqlalchemy import ForeignKey, Integer, String, Text, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.mixins import TimestampMixin

class ResearchPassage(Base, TimestampMixin):
    __tablename__ = "research_passages"
    __table_args__ = (UniqueConstraint("project_id", "source_key", "ordinal"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("research_projects.id", ondelete="CASCADE"), index=True)
    source_key: Mapped[str] = mapped_column(String(100), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    fingerprint: Mapped[str] = mapped_column(String(64))
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(255), nullable=True)

class ResearchEvidence(Base, TimestampMixin):
    __tablename__ = "research_evidence"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("research_projects.id", ondelete="CASCADE"), index=True)
    claim: Mapped[str] = mapped_column(Text)
    quote: Mapped[str] = mapped_column(Text)
    source: Mapped[dict] = mapped_column(JSON)
    notes: Mapped[str] = mapped_column(Text, default="")
    relationship: Mapped[str] = mapped_column(String(30), default="context")
    version: Mapped[int] = mapped_column(Integer, default=1)

class ResearchBrief(Base, TimestampMixin):
    __tablename__ = "research_briefs"
    project_id: Mapped[int] = mapped_column(ForeignKey("research_projects.id", ondelete="CASCADE"), primary_key=True)
    content: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)

class ResearchJob(Base, TimestampMixin):
    __tablename__ = "research_jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("research_projects.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    message: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class ResearchDraft(Base, TimestampMixin):
    __tablename__ = "research_drafts"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("research_projects.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    text: Mapped[str] = mapped_column(Text)
    evidence: Mapped[list] = mapped_column(JSON)
    revisions: Mapped[list] = mapped_column(JSON, default=list)
    version: Mapped[int] = mapped_column(Integer, default=1)

class ResearchReferenceCheck(Base, TimestampMixin):
    __tablename__ = "research_reference_checks"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("research_projects.id", ondelete="CASCADE"), index=True)
    reference_id: Mapped[int] = mapped_column(ForeignKey("references.id", ondelete="CASCADE"), index=True)
    fingerprint: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict] = mapped_column(JSON)

class ResearchSourceReference(Base, TimestampMixin):
    __tablename__ = "research_source_references"
    __table_args__ = (UniqueConstraint("project_id", "source_key"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("research_projects.id", ondelete="CASCADE"), index=True)
    source_key: Mapped[str] = mapped_column(String(100))
    reference_id: Mapped[int] = mapped_column(ForeignKey("references.id", ondelete="CASCADE"))
