"""Project and profile schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    working_title: str = Field(min_length=1, max_length=500)
    research_field: str | None = None
    document_type: str = "research_proposal"
    writing_language: str = "en"
    target_institution: str | None = None
    target_journal: str | None = None
    citation_style: str = "APA 7"
    study_context: str | None = None
    population_summary: str | None = None
    deadline: date | None = None
    notes: str | None = None
    research_idea: str | None = None
    available_materials: list[str] | None = None
    current_stage_hint: str | None = None


class ProjectUpdate(BaseModel):
    working_title: str | None = None
    research_field: str | None = None
    document_type: str | None = None
    writing_language: str | None = None
    target_institution: str | None = None
    target_journal: str | None = None
    citation_style: str | None = None
    study_context: str | None = None
    population_summary: str | None = None
    deadline: date | None = None
    status: str | None = None
    notes: str | None = None
    current_stage: str | None = None


class ProfileUpdate(BaseModel):
    research_problem: str | None = None
    existing_evidence: str | None = None
    research_gap: str | None = None
    overall_aim: str | None = None
    expected_contribution: str | None = None
    ethics_requirements: str | None = None
    unresolved_decisions: str | None = None
    assumptions_requiring_verification: str | None = None
    refined_idea: str | None = None
    proposed_scope: str | None = None
    key_concepts: str | None = None
    initial_search_terms: str | None = None
    scientific_significance: str | None = None
    practical_significance: str | None = None
    researcher_approved_summary: str | None = None
    ai_suggestions_summary: str | None = None


class ProfileOut(BaseModel):
    id: int
    project_id: int
    research_problem: str | None = None
    existing_evidence: str | None = None
    research_gap: str | None = None
    overall_aim: str | None = None
    expected_contribution: str | None = None
    ethics_requirements: str | None = None
    unresolved_decisions: str | None = None
    assumptions_requiring_verification: str | None = None
    refined_idea: str | None = None
    proposed_scope: str | None = None
    key_concepts: str | None = None
    initial_search_terms: str | None = None
    scientific_significance: str | None = None
    practical_significance: str | None = None
    researcher_approved_summary: str | None = None
    ai_suggestions_summary: str | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class StageProgressOut(BaseModel):
    id: int
    stage_key: str
    status: str
    notes: str | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class StageProgressUpdate(BaseModel):
    status: str
    notes: str | None = None


class ProjectOut(BaseModel):
    id: int
    owner_id: int
    working_title: str
    research_field: str | None
    document_type: str
    current_stage: str
    writing_language: str
    target_institution: str | None
    target_journal: str | None
    citation_style: str
    study_context: str | None
    population_summary: str | None
    deadline: date | None
    status: str
    completion_percent: int
    notes: str | None
    created_at: datetime
    updated_at: datetime
    profile: ProfileOut | None = None
    stage_progress: list[StageProgressOut] = []

    model_config = {"from_attributes": True}


class ProjectSummaryOut(BaseModel):
    id: int
    working_title: str
    research_field: str | None
    document_type: str
    current_stage: str
    writing_language: str
    status: str
    completion_percent: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class StageDefinitionOut(BaseModel):
    key: str
    order: int
    label_en: str
    label_ar: str
