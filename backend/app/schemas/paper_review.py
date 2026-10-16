from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

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
