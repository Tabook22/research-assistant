from typing import Literal
from pydantic import BaseModel, Field, model_validator

class DeskTask(BaseModel):
    kind: Literal["search", "ask", "compare", "write", "discover"]
    query: str = Field(min_length=2, max_length=4000)
    language: Literal["en", "ar"] = "en"
    source_keys: list[str] = Field(default_factory=list, max_length=12)
    evidence_ids: list[int] = Field(default_factory=list, max_length=20)
    year_from: int | None = Field(default=None, ge=1800, le=2100)
    year_to: int | None = Field(default=None, ge=1800, le=2100)
    semantic: bool = True
    @model_validator(mode="after")
    def valid(self):
        self.query=self.query.strip()
        if len(self.query)<2: raise ValueError("Enter a research question or search terms.")
        if self.year_from and self.year_to and self.year_from>self.year_to: raise ValueError("Invalid year range.")
        if self.kind=="compare" and len(set(self.source_keys))<2: raise ValueError("Select at least two papers to compare.")
        if self.kind=="write" and not self.evidence_ids: raise ValueError("Select saved evidence for a supported draft.")
        return self

class EvidenceCreate(BaseModel):
    passage_id: int
    fingerprint: str
    quote: str = Field(min_length=5, max_length=2500)
    claim: str = Field(min_length=2, max_length=4000)
    notes: str = Field(default="", max_length=6000)
    relationship: Literal["supports", "contradicts", "context", "method"] = "context"

class EvidenceEdit(BaseModel):
    version: int = Field(ge=1)
    notes: str = Field(max_length=6000)
    relationship: Literal["supports", "contradicts", "context", "method"]

class BriefEdit(BaseModel):
    version: int = Field(ge=0)
    content: str = Field(max_length=16000)

class DraftEdit(BaseModel):
    version: int = Field(ge=1)
    title: str = Field(min_length=1,max_length=255)
    text: str = Field(max_length=80000)

class Citation(BaseModel):
    passage_id: int
    quote: str = Field(min_length=5,max_length=2500)

class SupportedClaim(BaseModel):
    text: str = Field(min_length=2,max_length=5000)
    citations: list[Citation] = Field(min_length=1,max_length=8)
    interpretation: bool = True

class GroundedResponse(BaseModel):
    claims: list[SupportedClaim] = Field(max_length=16)
    limitations: list[str] = Field(default_factory=list,max_length=10)
    follow_up_questions: list[str] = Field(default_factory=list,max_length=8)

class SourceReferenceUpdate(BaseModel):
    source_key: str = Field(max_length=100)
    reference_id: int
