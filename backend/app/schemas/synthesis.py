"""Schemas for multi-document synthesis dashboard."""

from typing import Any

from pydantic import BaseModel, Field


class SynthesisRequest(BaseModel):
    document_ids: list[int] | None = None
    language: str | None = None


class SynthesisResponse(BaseModel):
    language: str
    status: str
    headline: str
    message: str
    integrity_notice: str
    paper_count: int = 0
    papers: list[dict[str, Any]] = Field(default_factory=list)
    insight_cards: list[dict[str, Any]] = Field(default_factory=list)
    theme_cloud: list[dict[str, Any]] = Field(default_factory=list)
    method_patterns: list[dict[str, Any]] = Field(default_factory=list)
    stage_heatmap: list[dict[str, Any]] = Field(default_factory=list)
    gap_signals: list[dict[str, Any]] = Field(default_factory=list)
    writing_moves: list[dict[str, Any]] = Field(default_factory=list)
    learning_path: list[str] = Field(default_factory=list)
    comparison_matrix: list[dict[str, Any]] = Field(default_factory=list)
    stats: dict[str, Any] | None = None
    ai_enriched: bool = False
    ai_synthesis: dict[str, Any] | None = None
