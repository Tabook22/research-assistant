"""AI suggestion schemas and apply payloads."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SuggestionPayload(BaseModel):
    """One structured proposal from the AI (never auto-applied)."""

    type: str = Field(
        description=(
            "profile_field | research_question | objective | hypothesis | variable | "
            "design | population | sampling | instrument_item | analysis_mapping"
        )
    )
    title: str
    payload: dict[str, Any] = Field(default_factory=dict)
    rationale: str | None = None


class AISuggestionOut(BaseModel):
    id: int
    project_id: int
    stage_key: str | None
    suggestion_type: str
    title: str
    content: str
    structured_json: str | None
    approval_status: str
    target_element_type: str | None
    target_element_id: int | None
    created_at: datetime
    # Parsed convenience fields for the UI
    payload: dict[str, Any] | None = None
    rationale: str | None = None

    model_config = {"from_attributes": True}


class SuggestionApplyRequest(BaseModel):
    """Researcher applies a suggestion, optionally after editing the payload."""

    action: str = "apply"  # apply | reject | revise
    notes: str | None = None
    # Optional edited payload overrides stored structured_json.payload
    edited_payload: dict[str, Any] | None = None
    mark_approved: bool = False  # if True, create records as approved; else proposed


class SuggestionApplyResult(BaseModel):
    suggestion_id: int
    action: str
    approval_status: str
    created_element_type: str | None = None
    created_element_id: int | None = None
    message: str
