"""Literature search and references."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class LiteratureSearch(Base, TimestampMixin):
    __tablename__ = "literature_searches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    database_name: Mapped[str] = mapped_column(String(100), default="openalex")
    filters_json: Mapped[str | None] = mapped_column(Text)
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    raw_results_json: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    project = relationship("ResearchProject", back_populates="literature_searches")


class Reference(Base, TimestampMixin):
    __tablename__ = "references"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    search_id: Mapped[int | None] = mapped_column(
        ForeignKey("literature_searches.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer)
    journal: Mapped[str | None] = mapped_column(String(500))
    publisher: Mapped[str | None] = mapped_column(String(500))
    doi: Mapped[str | None] = mapped_column(String(255), index=True)
    url: Mapped[str | None] = mapped_column(String(1000))
    study_location: Mapped[str | None] = mapped_column(String(255))
    population: Mapped[str | None] = mapped_column(Text)
    research_design: Mapped[str | None] = mapped_column(String(255))
    sample: Mapped[str | None] = mapped_column(Text)
    main_variables: Mapped[str | None] = mapped_column(Text)
    main_finding: Mapped[str | None] = mapped_column(Text)
    limitations: Mapped[str | None] = mapped_column(Text)
    relevance: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(String(50), default="unverified", index=True)
    relevance_category: Mapped[str] = mapped_column(
        String(50), default="potential"
    )  # verified_relevant | potential | background
    full_text_reviewed: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str | None] = mapped_column(Text)
    approval_status: Mapped[str] = mapped_column(String(50), default="proposed")
    citation_apa: Mapped[str | None] = mapped_column(Text)
    citation_vancouver: Mapped[str | None] = mapped_column(Text)

    project = relationship("ResearchProject", back_populates="references")
    claims = relationship("ReferenceClaim", back_populates="reference", cascade="all, delete-orphan")


class ReferenceClaim(Base, TimestampMixin):
    __tablename__ = "reference_claims"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reference_id: Mapped[int] = mapped_column(
        ForeignKey("references.id", ondelete="CASCADE"), index=True
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    manuscript_section_id: Mapped[int | None] = mapped_column(
        ForeignKey("manuscript_sections.id", ondelete="SET NULL")
    )
    support_strength: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)

    reference = relationship("Reference", back_populates="claims")
