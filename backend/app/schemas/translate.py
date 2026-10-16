"""Schemas for on-demand text translation."""

from pydantic import BaseModel, Field


class TranslateTextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)
    target_language: str = "ar"
    source_language: str | None = "en"


class TranslateTextOut(BaseModel):
    original: str
    translated: str
    target_language: str
    used_service: bool = False
    message: str = ""
