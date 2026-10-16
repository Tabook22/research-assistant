"""Manuscript sections and alignment issues."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class ManuscriptSection(Base, TimestampMixin):
    __tablename__ = "manuscript_sections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    section_key: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    source: Mapped[str] = mapped_column(String(50), default="researcher")  # researcher | ai | mixed
    approval_status: Mapped[str] = mapped_column(String(50), default="proposed")
    is_template: Mapped[bool] = mapped_column(default=False)

    project = relationship("ResearchProject", back_populates="manuscript_sections")


class AlignmentIssue(Base, TimestampMixin):
    __tablename__ = "alignment_issues"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    issue_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(50), default="warning", index=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    affected_elements: Mapped[str | None] = mapped_column(Text)  # JSON list of ids/labels
    recommended_correction: Mapped[str | None] = mapped_column(Text)
    correction_options: Mapped[str | None] = mapped_column(Text)  # JSON
    resolution_status: Mapped[str] = mapped_column(String(50), default="open", index=True)

    project = relationship("ResearchProject", back_populates="alignment_issues")
