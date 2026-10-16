from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, SecretStr

Purpose = Literal['analysis', 'discussion']
Provider = Literal['openai', 'anthropic', 'gemini', 'xai', 'deepseek', 'mistral']


class AIProfileInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    provider: Provider
    model: str = Field(default='', max_length=200, pattern=r'^[A-Za-z0-9_./:@-]*$')
    api_key: SecretStr | None = None
    use_environment: bool = False
    max_output_tokens: int = Field(default=8192, ge=512, le=32768)
    version: int = Field(default=0, ge=0)
