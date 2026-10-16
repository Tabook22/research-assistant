"""Decisions, AI suggestions, exports, audit logs."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class ResearcherDecision(Base, TimestampMixin):
    __tablename__ = "researcher_decisions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    element_type: Mapped[str] = mapped_column(String(100), nullable=False)
    element_id: Mapped[int | None] = mapped_column(Integer)
    decision: Mapped[str] = mapped_column(String(50), nullable=False)  # approve | reject | revise
    notes: Mapped[str | None] = mapped_column(Text)
    previous_status: Mapped[str | None] = mapped_column(String(50))
    new_status: Mapped[str | None] = mapped_column(String(50))

    project = relationship("ResearchProject", back_populates="decisions")


class AISuggestion(Base, TimestampMixin):
    __tablename__ = "ai_suggestions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    stage_key: Mapped[str | None] = mapped_column(String(50))
    suggestion_type: Mapped[str] = mapped_column(String(100), default="general")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_json: Mapped[str | None] = mapped_column(Text)
    approval_status: Mapped[str] = mapped_column(String(50), default="proposed", index=True)
    target_element_type: Mapped[str | None] = mapped_column(String(100))
    target_element_id: Mapped[int | None] = mapped_column(Integer)

    project = relationship("ResearchProject", back_populates="ai_suggestions")


class ExportRecord(Base, TimestampMixin):
    __tablename__ = "exports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    export_type: Mapped[str] = mapped_column(String(50), default="project_summary")
    format: Mapped[str] = mapped_column(String(20), default="markdown")
    file_path: Mapped[str | None] = mapped_column(String(1000))
    content_preview: Mapped[str | None] = mapped_column(Text)

    project = relationship("ResearchProject", back_populates="exports")


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("research_projects.id", ondelete="SET NULL"), index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    details: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(50))
