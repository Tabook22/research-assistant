"""Export schemas."""

from datetime import datetime

from pydantic import BaseModel


class ExportRequest(BaseModel):
    export_type: str = "project_summary"  # project_summary | manuscript | references
    format: str = "markdown"  # markdown | json


class ExportOut(BaseModel):
    id: int
    project_id: int
    export_type: str
    format: str
    content: str
    created_at: datetime
