"""Schemas for Previous Research Library."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SourceDocumentSummary(BaseModel):
    id: int
    project_id: int
    original_filename: str
    file_type: str
    file_size: int
    page_count: int | None
    processing_status: str
    ocr_status: str
    extraction_status: str
    detected_language: str | None
    document_type: str | None
    document_type_confidence: float | None
    document_type_confirmed: bool
    academic_level: str | None
    discipline: str | None
    research_design: str | None
    methodology_paradigm: str | None
    title_detected: str | None
    year_detected: int | None
    verification_status: str
    is_reference_only: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentSectionOut(BaseModel):
    id: int
    heading: str
    normalized_heading: str | None
    content: str
    summary: str | None
    page_start: int | None
    page_end: int | None
    sort_order: int
    content_kind: str
    confidence: float | None

    model_config = {"from_attributes": True}


class StageMappingOut(BaseModel):
    id: int
    stage_key: str
    status: str
    original_heading: str | None
    page_or_section: str | None
    extracted_excerpt: str | None
    ai_summary: str | None
    completeness: str | None
    methodological_clarity: str | None
    strengths: str | None
    limitations: str | None
    lessons_for_user: str | None
    connection_to_next: str | None
    writing_strategy: str | None
    confidence: float | None
    researcher_verified: bool
    researcher_correction: str | None

    model_config = {"from_attributes": True}


class ExtractedElementOut(BaseModel):
    id: int
    element_type: str
    content_role: str
    value_text: str
    page_or_section: str | None
    section_heading: str | None
    confidence: float | None
    verification_status: str
    reuse_category: str

    model_config = {"from_attributes": True}


class SourceDocumentDetail(SourceDocumentSummary):
    document_type_evidence: str | None
    academic_level_confidence: float | None
    authors_detected: str | None
    abstract_excerpt: str | None
    analysis_warnings: list[str] = []
    learning_report: dict[str, Any] | None = None
    quality_analysis: dict[str, Any] | None = None
    structure_map: dict[str, Any] | None = None
    study_summary: dict[str, Any] | None = None
    researcher_notes: str | None
    sections: list[DocumentSectionOut] = []
    stage_mappings: list[StageMappingOut] = []
    elements: list[ExtractedElementOut] = []
    integrity_notice: str = (
        "This document is a learning reference only. Content is not your research. "
        "Do not copy distinctive wording or present another study’s results as your own."
    )


class MultiUploadResult(BaseModel):
    uploaded: list[SourceDocumentDetail] = []
    failed: list[dict[str, str]] = []
    message: str = ""


class ClassificationConfirm(BaseModel):
    document_type: str | None = None
    academic_level: str | None = None
    discipline: str | None = None
    research_design: str | None = None


class StageVerifyRequest(BaseModel):
    status: str | None = None
    correction: str | None = None


class CompareRequest(BaseModel):
    document_ids: list[int] = Field(min_length=2)
    title: str = "Paper comparison"


class ComparisonItemOut(BaseModel):
    id: int
    element_key: str
    values: dict[str, str]
    lessons: str | None

    model_config = {"from_attributes": True}


class ComparisonOut(BaseModel):
    id: int
    project_id: int
    title: str
    document_ids: list[int]
    summary: dict[str, Any] | None
    lessons: dict[str, Any] | None
    items: list[ComparisonItemOut]
    created_at: datetime


class NotesUpdate(BaseModel):
    researcher_notes: str


class WriteSectionGuideRequest(BaseModel):
    stage_key: str
    language: str | None = None


class WriteSectionDraftRequest(BaseModel):
    stage_key: str
    answers: dict[str, str] = Field(default_factory=dict)
    save_as_learning_note: bool = True
    language: str | None = None


class WriteSectionGuideOut(BaseModel):
    guide: dict[str, Any]


class WriteSectionDraftOut(BaseModel):
    draft: str
    source: str
    ai_used: bool
    learning_note_id: int | None = None
    integrity_notice: str = (
        "Original draft for your project. Do not submit without review. "
        "Cite sources and do not copy the reference paper."
    )


class TranslateAnalysisRequest(BaseModel):
    """On-demand translation of free-text analysis into Arabic."""

    target_language: str = "ar"
    scope: str = Field(
        default="full",
        description="full = whole analysis; stage = one selected stage only",
    )
    stage_key: str | None = None


class TranslateAnalysisOut(BaseModel):
    document: SourceDocumentDetail
    ai_used: bool = False
    message: str = ""
    translated_fields: int = 0
    candidate_fields: int = 0
