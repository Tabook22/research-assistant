"""Application configuration via environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Absolute path so the key loads no matter which cwd uvicorn starts from
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ResearchGuide AI"
    app_env: str = "development"
    allow_registration: bool = True
    debug: bool = True
    secret_key: str = "change-me-in-production-use-long-random-string"
    access_token_expire_minutes: int = 60 * 24 * 7
    algorithm: str = "HS256"

    database_url: str = f"sqlite:///{(DEFAULT_DATA_DIR / 'researchguide.db').as_posix()}"
    upload_dir: str = str(DEFAULT_DATA_DIR / "uploads")
    export_dir: str = str(DEFAULT_DATA_DIR / "exports")
    max_upload_size_mb: int = 25

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"

    # SpaceXAI / xAI (OpenAI-compatible)
    xai_api_key: str = ""
    xai_base_url: str = "https://api.x.ai/v1"
    ai_model: str = "grok-4.5"
    ai_provider: str = "xai"
    ai_max_context_messages: int = 20

    # Literature search
    openalex_mailto: str = "researchguide@example.com"
    openalex_api_key: str = ""
    semantic_scholar_api_key: str = ""
    embedding_model: str = ""
    embedding_base_url: str = "https://api.openai.com/v1"
    embedding_api_key: str = ""
    crossref_mailto: str = "researchguide@example.com"

    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
