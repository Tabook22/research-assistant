"""Document schemas."""

from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: int
    project_id: int
    original_filename: str
    file_type: str
    file_size: int
    category: str
    processing_status: str
    extracted_text_status: str
    verification_status: str
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentTextOut(BaseModel):
    document_id: int
    original_filename: str
    chunks: list[str]
    total_chars: int
