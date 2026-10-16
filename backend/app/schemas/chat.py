"""Chat and AI schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.suggestions import AISuggestionOut


class ChatMessageCreate(BaseModel):
    content: str = Field(min_length=1)
    stage_key: str | None = None
    special_command: str | None = None
    # UI language (en|ar) — drives assistant response language for Arabic audiences
    language: str | None = None


class MessageOut(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    stage_key: str | None
    structured_json: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: int
    project_id: int
    title: str
    stage_key: str | None
    is_active: bool
    messages: list[MessageOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    conversation_id: int
    user_message: MessageOut
    assistant_message: MessageOut
    profile_suggestions: dict | None = None
    suggestions: list[AISuggestionOut] = []
    integrity_warnings: list[str] = []
