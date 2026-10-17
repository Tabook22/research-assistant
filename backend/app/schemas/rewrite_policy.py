from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Scope = Literal['global', 'project', 'review']
Ceiling = Annotated[int, Field(strict=True, ge=1, le=2_000_000_000)]


class RewritePolicyInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    version: int = Field(ge=0)
    mode: Literal['inherit', 'custom', 'unlimited']
    source_limit: Ceiling | None = None
    output_limit: Ceiling | None = None
    discussion_limit: Ceiling | None = None

    @model_validator(mode='after')
    def complete_limits(self):
        if self.mode == 'custom' and any(getattr(self, key) is None for key in ('source_limit', 'output_limit', 'discussion_limit')):
            raise ValueError('Provide all three character ceilings for custom mode.')
        return self
