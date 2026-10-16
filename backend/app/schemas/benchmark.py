"""Schemas for project-vs-papers benchmark."""

from typing import Any

from pydantic import BaseModel, Field


class BenchmarkRequest(BaseModel):
    """Optional filter: which library papers to use (default = all)."""

    document_ids: list[int] | None = None
    language: str | None = None


class BenchmarkResponse(BaseModel):
    language: str
    status: str
    message: str
    integrity_notice: str
    project: dict[str, Any] | None = None
    papers: list[dict[str, Any]] = Field(default_factory=list)
    stage_benchmarks: list[dict[str, Any]] = Field(default_factory=list)
    design_comparison: dict[str, Any] | None = None
    gaps: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    overall_score: int | None = None
    score_explanation: str | None = None
    ai_enriched: bool = False
    ai_narrative: dict[str, Any] | None = None
