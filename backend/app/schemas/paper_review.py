from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, StrictBool

class Finding(BaseModel):
    model_config = ConfigDict(extra="ignore")
    summary: str = Field(max_length=12000)
    main_ideas: list[str] = Field(default_factory=list, max_length=12)
    problem_statement: str = Field(default="", max_length=12000)
    problem_status: Literal["explicit", "inferred", "not_identified"] = "not_identified"
    strengths: list[str] = Field(default_factory=list, max_length=12)
    improvements: list[str] = Field(default_factory=list, max_length=12)
    evidence: list[str] = Field(default_factory=list, max_length=8)
    verification_needed: list[str] = Field(default_factory=list, max_length=12)

class Action(BaseModel):
    version: int = Field(ge=1)
    instruction: str = Field(min_length=1, max_length=6000)

class DraftUpdate(BaseModel):
    version: int = Field(ge=1)
    text: str = Field(max_length=80000)

class AnalyzeRequest(BaseModel):
    version: int = Field(ge=1)

class ComplianceStart(AnalyzeRequest):
    paper_type: Literal['general','conceptual_legal','quantitative','observational_health','qualitative','systematic_review','randomized_trial','proposal'] = 'general'
    basis: Literal['original','working'] = 'working'

class RewriteStart(ComplianceStart):
    instruction: str = Field(default="", max_length=6000)

class RewriteChoice(BaseModel):
    section_id: int = Field(ge=1)
    mode: Literal['source', 'enhanced', 'custom', 'omit']
    text: str = Field(default='', max_length=80000)

class RewriteMerge(AnalyzeRequest):
    choices: list[RewriteChoice] = Field(min_length=1, max_length=30)

class PaperChatRequest(Action):
    section_id: int | None = Field(default=None, ge=1)
    search_id: str | None = Field(default=None, max_length=40)
    language: Literal['en','ar'] | None = None
    session_id: str | None = Field(default=None, min_length=1, max_length=40)

class PaperChatSearch(AnalyzeRequest):
    proposal_id: str = Field(min_length=1, max_length=40)
    query: str = Field(min_length=3, max_length=240)
    consent: StrictBool
    language: Literal['en','ar'] | None = None
    session_id: str | None = Field(default=None, min_length=1, max_length=40)

class ChatSessionCreate(AnalyzeRequest):
    title: str = Field(default='', max_length=120)

class ChatSessionRename(AnalyzeRequest):
    title: str = Field(min_length=1, max_length=120)
