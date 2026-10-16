"""Literature and reference schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class LiteratureSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    database_name: str = "openalex"
    year_from: int | None = None
    year_to: int | None = None
    max_results: int = Field(default=20, ge=1, le=50)


class LiteratureResultItem(BaseModel):
    title: str
    authors: str | None = None
    year: int | None = None
    journal: str | None = None
    doi: str | None = None
    url: str | None = None
    abstract: str | None = None
    verification_status: str = "metadata_retrieved"


class LiteratureSearchOut(BaseModel):
    id: int
    project_id: int
    query: str
    database_name: str
    result_count: int
    results: list[LiteratureResultItem]
    created_at: datetime


class ReferenceCreate(BaseModel):
    title: str
    authors: str | None = None
    year: int | None = None
    journal: str | None = None
    publisher: str | None = None
    doi: str | None = None
    url: str | None = None
    study_location: str | None = None
    population: str | None = None
    research_design: str | None = None
    sample: str | None = None
    main_variables: str | None = None
    main_finding: str | None = None
    limitations: str | None = None
    relevance: str | None = None
    verification_status: str = "unverified"
    relevance_category: str = "potential"
    notes: str | None = None
    search_id: int | None = None


class ReferenceUpdate(BaseModel):
    title: str | None = None
    authors: str | None = None
    year: int | None = None
    journal: str | None = None
    doi: str | None = None
    url: str | None = None
    verification_status: str | None = None
    relevance_category: str | None = None
    full_text_reviewed: bool | None = None
    notes: str | None = None
    approval_status: str | None = None
    main_finding: str | None = None
    relevance: str | None = None


class ReferenceOut(BaseModel):
    id: int
    project_id: int
    title: str
    authors: str | None
    year: int | None
    journal: str | None
    publisher: str | None
    doi: str | None
    url: str | None
    study_location: str | None
    population: str | None
    research_design: str | None
    sample: str | None
    main_variables: str | None
    main_finding: str | None
    limitations: str | None
    relevance: str | None
    verification_status: str
    relevance_category: str
    full_text_reviewed: bool
    notes: str | None
    approval_status: str
    citation_apa: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
