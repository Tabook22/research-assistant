"""Shared model mixins and enums."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=utcnow,
        onupdate=utcnow,
    )


# Configurable research stages (keys used in DB and UI)
RESEARCH_STAGES = [
    {"key": "idea", "order": 1, "label_en": "Research Idea", "label_ar": "فكرة البحث"},
    {"key": "literature_search", "order": 2, "label_en": "Literature Search", "label_ar": "البحث في الأدبيات"},
    {"key": "literature_synthesis", "order": 3, "label_en": "Literature Synthesis & Gap", "label_ar": "تركيب الأدبيات والفجوة"},
    {"key": "problem_purpose", "order": 4, "label_en": "Problem, Purpose & Significance", "label_ar": "المشكلة والغرض والأهمية"},
    {"key": "questions_objectives", "order": 5, "label_en": "Questions & Objectives", "label_ar": "الأسئلة والأهداف"},
    {"key": "hypotheses", "order": 6, "label_en": "Hypotheses", "label_ar": "الفرضيات"},
    {"key": "constructs_variables", "order": 7, "label_en": "Constructs & Variables", "label_ar": "المفاهيم والمتغيرات"},
    {"key": "methodology", "order": 8, "label_en": "Methodology", "label_ar": "المنهجية"},
    {"key": "population_sampling", "order": 9, "label_en": "Population & Sampling", "label_ar": "المجتمع والعينة"},
    {"key": "instruments", "order": 10, "label_en": "Data-Collection Instruments", "label_ar": "أدوات جمع البيانات"},
    {"key": "validity_quality", "order": 11, "label_en": "Validity, Reliability & Quality", "label_ar": "الصدق والثبات والجودة"},
    {"key": "ethics", "order": 12, "label_en": "Ethics & Data Protection", "label_ar": "الأخلاقيات وحماية البيانات"},
    {"key": "analysis_plan", "order": 13, "label_en": "Analysis Plan", "label_ar": "خطة التحليل"},
    {"key": "results", "order": 14, "label_en": "Results", "label_ar": "النتائج"},
    {"key": "discussion", "order": 15, "label_en": "Discussion", "label_ar": "المناقشة"},
    {"key": "conclusion", "order": 16, "label_en": "Conclusion & Recommendations", "label_ar": "الخاتمة والتوصيات"},
    {"key": "abstract_title", "order": 17, "label_en": "Abstract, Title & Keywords", "label_ar": "الملخص والعنوان والكلمات المفتاحية"},
    {"key": "references", "order": 18, "label_en": "References", "label_ar": "المراجع"},
]

DOCUMENT_TYPES = [
    "research_proposal",
    "research_protocol",
    "journal_article",
    "masters_thesis",
    "doctoral_dissertation",
    "conference_paper",
    "systematic_review",
    "scoping_review",
    "other",
]

APPROVAL_STATUSES = [
    "proposed",
    "under_review",
    "approved",
    "rejected",
    "needs_revision",
    "superseded",
]

STAGE_STATUSES = ["not_started", "in_progress", "pending_approval", "completed", "skipped"]

SEVERITY_LEVELS = ["information", "warning", "major", "critical"]
