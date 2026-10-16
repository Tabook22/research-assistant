"""ResearchGuide AI FastAPI application."""

from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import (
    admin,
    alignment,
    paper_reviews,
    research_desk,
    auth,
    benchmark,
    chat,
    documents,
    export,
    library,
    literature,
    projects,
    research,
    suggestions,
    synthesis,
    translate,
)
from app.config import get_settings
from app.database import Base, engine

# Import models so metadata is registered
import app.models  # noqa: F401

settings = get_settings()

# Ensure data directories exist
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.export_dir).mkdir(parents=True, exist_ok=True)
if settings.database_url.startswith("sqlite"):
    db_path = settings.database_url.replace("sqlite:///", "")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

# Create tables (Alembic can replace this in production workflows)
Base.metadata.create_all(bind=engine)
from app.services.user_migration import migrate_user_access
migrate_user_access(engine)

@asynccontextmanager
async def lifespan(app):
    from app.services.research_jobs import recover_interrupted
    recover_interrupted()
    yield

app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
    version=__version__,
    description=(
        "Structured scientific research-development platform: guided methodology, "
        "project profiles, alignment checking, literature tools, and AI supervision."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = FastAPI()  # not used; routers mounted on main
app.include_router(auth.router, prefix="/api")
from app.api import admin_ai, paper_evaluation
app.include_router(admin.router, prefix="/api")
app.include_router(admin_ai.router, prefix="/api")
app.include_router(paper_evaluation.router, prefix="/api")
app.include_router(paper_reviews.router, prefix="/api")
app.include_router(research_desk.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(research.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(alignment.router, prefix="/api")
app.include_router(literature.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(suggestions.router, prefix="/api")
app.include_router(library.router, prefix="/api")
app.include_router(benchmark.router, prefix="/api")
app.include_router(synthesis.router, prefix="/api")
app.include_router(translate.router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    # Clear cache so XAI_API_KEY from .env is always current after edits/reload
    get_settings.cache_clear()
    cfg = get_settings()
    from app.services.ai_configuration import load
    profile = load("analysis")
    return {
        "status": "ok",
        "app": cfg.app_name,
        "version": __version__,
        "ai_configured": bool(profile.key),
        "ai_model": profile.model,
        "ai_provider": profile.provider,
    }
