"""Previous Research Library — source papers, analysis, comparisons (learning only)."""

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class SourceDocument(Base, TimestampMixin):
    """Uploaded previous study / thesis / proposal for learning (not the user's project content)."""

    __tablename__ = "source_documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    uploaded_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    safe_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer)

    # Processing
    processing_status: Mapped[str] = mapped_column(String(50), default="uploaded", index=True)
    ocr_status: Mapped[str] = mapped_column(String(50), default="not_needed")
    extraction_status: Mapped[str] = mapped_column(String(50), default="pending")
    detected_language: Mapped[str | None] = mapped_column(String(20))
    analysis_warnings: Mapped[str | None] = mapped_column(Text)  # JSON list

    # Classification (AI/heuristic — not confirmed until researcher verifies)
    document_type: Mapped[str | None] = mapped_column(String(100))
    document_type_confidence: Mapped[float | None] = mapped_column(Float)
    document_type_evidence: Mapped[str | None] = mapped_column(Text)
    document_type_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    academic_level: Mapped[str | None] = mapped_column(String(100))
    academic_level_confidence: Mapped[float | None] = mapped_column(Float)
    discipline: Mapped[str | None] = mapped_column(String(255))
    research_design: Mapped[str | None] = mapped_column(String(255))
    methodology_paradigm: Mapped[str | None] = mapped_column(String(50))  # quant/qual/mixed

    # Learning report (JSON)
    learning_report_json: Mapped[str | None] = mapped_column(Text)
    quality_analysis_json: Mapped[str | None] = mapped_column(Text)
    structure_map_json: Mapped[str | None] = mapped_column(Text)

    title_detected: Mapped[str | None] = mapped_column(String(1000))
    authors_detected: Mapped[str | None] = mapped_column(Text)
    year_detected: Mapped[int | None] = mapped_column(Integer)
    abstract_excerpt: Mapped[str | None] = mapped_column(Text)

    researcher_notes: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(String(50), default="unverified")

    # Integrity: never auto-merge into user project
    is_reference_only: Mapped[bool] = mapped_column(Boolean, default=True)

    project = relationship("ResearchProject", backref="source_documents")
    sections = relationship(
        "DocumentSection", back_populates="source_document", cascade="all, delete-orphan"
    )
    stage_mappings = relationship(
        "DocumentStageMapping", back_populates="source_document", cascade="all, delete-orphan"
    )
    elements = relationship(
        "ExtractedResearchElement",
        back_populates="source_document",
        cascade="all, delete-orphan",
    )
    jobs = relationship(
        "DocumentProcessingJob",
        back_populates="source_document",
        cascade="all, delete-orphan",
    )
    annotations = relationship(
        "SourceAnnotation", back_populates="source_document", cascade="all, delete-orphan"
    )


class DocumentSection(Base, TimestampMixin):
    __tablename__ = "document_sections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"), index=True
    )
    heading: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_heading: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    page_start: Mapped[int | None] = mapped_column(Integer)
    page_end: Mapped[int | None] = mapped_column(Integer)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    content_kind: Mapped[str] = mapped_column(
        String(50), default="exact"
    )  # exact | summary | mixed
    confidence: Mapped[float | None] = mapped_column(Float)

    source_document = relationship("SourceDocument", back_populates="sections")


class DocumentStageMapping(Base, TimestampMixin):
    """Maps source document content to the 18-stage research framework."""

    __tablename__ = "document_stage_mappings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"), index=True
    )
    stage_key: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(
        String(50), default="not_detected"
    )  # detected | partially_detected | not_detected | not_applicable | requires_manual_review
    original_heading: Mapped[str | None] = mapped_column(String(500))
    page_or_section: Mapped[str | None] = mapped_column(String(100))
    extracted_excerpt: Mapped[str | None] = mapped_column(Text)  # exact source
    ai_summary: Mapped[str | None] = mapped_column(Text)
    completeness: Mapped[str | None] = mapped_column(String(50))  # high | medium | low | n/a
    methodological_clarity: Mapped[str | None] = mapped_column(String(50))
    strengths: Mapped[str | None] = mapped_column(Text)
    limitations: Mapped[str | None] = mapped_column(Text)
    lessons_for_user: Mapped[str | None] = mapped_column(Text)
    connection_to_next: Mapped[str | None] = mapped_column(Text)
    writing_strategy: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    researcher_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    researcher_correction: Mapped[str | None] = mapped_column(Text)

    source_document = relationship("SourceDocument", back_populates="stage_mappings")


class ExtractedResearchElement(Base, TimestampMixin):
    __tablename__ = "extracted_research_elements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"), index=True
    )
    element_type: Mapped[str] = mapped_column(String(100), index=True)
    # exact source vs ai summary vs interpretation
    content_role: Mapped[str] = mapped_column(String(50), default="exact")
    value_text: Mapped[str] = mapped_column(Text, nullable=False)
    page_or_section: Mapped[str | None] = mapped_column(String(100))
    section_heading: Mapped[str | None] = mapped_column(String(500))
    confidence: Mapped[float | None] = mapped_column(Float)
    verification_status: Mapped[str] = mapped_column(String(50), default="unverified")
    # How user may use it: background | method_example | instrument | theory | citation | not_reusable
    reuse_category: Mapped[str] = mapped_column(String(50), default="background_evidence")

    source_document = relationship("SourceDocument", back_populates="elements")


class DocumentProcessingJob(Base, TimestampMixin):
    __tablename__ = "document_processing_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="queued")
    step: Mapped[str | None] = mapped_column(String(100))
    message: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)

    source_document = relationship("SourceDocument", back_populates="jobs")


class PaperComparison(Base, TimestampMixin):
    __tablename__ = "paper_comparisons"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(500), default="Paper comparison")
    document_ids_json: Mapped[str] = mapped_column(Text)  # JSON list of source_document ids
    summary_json: Mapped[str | None] = mapped_column(Text)
    lessons_json: Mapped[str | None] = mapped_column(Text)

    items = relationship(
        "ComparisonItem", back_populates="comparison", cascade="all, delete-orphan"
    )


class ComparisonItem(Base, TimestampMixin):
    __tablename__ = "comparison_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    comparison_id: Mapped[int] = mapped_column(
        ForeignKey("paper_comparisons.id", ondelete="CASCADE"), index=True
    )
    element_key: Mapped[str] = mapped_column(String(100))  # research_problem, gap, etc.
    values_json: Mapped[str] = mapped_column(Text)  # {doc_id: text}
    lessons: Mapped[str | None] = mapped_column(Text)

    comparison = relationship("PaperComparison", back_populates="items")


class LearningNote(Base, TimestampMixin):
    __tablename__ = "learning_notes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    source_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("source_documents.id", ondelete="SET NULL")
    )
    stage_key: Mapped[str | None] = mapped_column(String(50))
    note: Mapped[str] = mapped_column(Text, nullable=False)
    # Never auto-insert into user project
    linked_to_user_project: Mapped[bool] = mapped_column(Boolean, default=False)


class SourceAnnotation(Base, TimestampMixin):
    __tablename__ = "source_annotations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"), index=True
    )
    stage_key: Mapped[str | None] = mapped_column(String(50))
    annotation: Mapped[str] = mapped_column(Text, nullable=False)
    page_or_section: Mapped[str | None] = mapped_column(String(100))

    source_document = relationship("SourceDocument", back_populates="annotations")
