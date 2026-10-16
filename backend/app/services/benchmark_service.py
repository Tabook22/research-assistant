"""
Benchmark the user's research project against uploaded library papers.

Purpose: show how the user's project compares to study references on structure,
methods, and completeness — without treating reference content as the user's work.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.i18n.lang import normalize_lang, stage_purpose, t
from app.models.library import DocumentStageMapping, SourceDocument
from app.models.mixins import RESEARCH_STAGES
from app.models.project import ResearchProject, StageProgress
from app.models.research import (
    AnalysisPlan,
    Hypothesis,
    Instrument,
    Population,
    ResearchDesign,
    ResearchObjective,
    ResearchQuestion,
    SamplingPlan,
    Variable,
)
from app.services.project_service import build_profile_context

logger = logging.getLogger(__name__)
settings = get_settings()

# Map project completeness signals to stage keys
PROJECT_STAGE_SIGNALS: dict[str, str] = {
    "idea": "refined_idea",
    "literature_synthesis": "research_gap",
    "problem_purpose": "research_problem",
    "questions_objectives": "questions",  # special: count
    "hypotheses": "hypotheses",
    "constructs_variables": "variables",
    "methodology": "designs",
    "population_sampling": "populations",
    "instruments": "instruments",
    "ethics": "ethics_requirements",
    "analysis_plan": "analysis_plans",
}


def _client() -> AsyncOpenAI | None:
    if not settings.xai_api_key:
        return None
    return AsyncOpenAI(api_key=settings.xai_api_key, base_url=settings.xai_base_url)


async def benchmark_project(
    db: Session,
    project: ResearchProject,
    document_ids: list[int] | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    lang = normalize_lang(language or project.writing_language or "en")

    q = (
        db.query(SourceDocument)
        .options(joinedload(SourceDocument.stage_mappings))
        .filter(SourceDocument.project_id == project.id)
    )
    if document_ids:
        q = q.filter(SourceDocument.id.in_(document_ids))
    papers = q.order_by(SourceDocument.id.desc()).all()

    if not papers:
        return {
            "language": lang,
            "status": "no_papers",
            "message": t(lang, "bench.no_papers"),
            "integrity_notice": t(lang, "bench.integrity"),
            "papers": [],
            "stage_benchmarks": [],
            "gaps": [],
            "strengths": [],
            "recommendations": [t(lang, "bench.rec_upload")],
            "overall_score": None,
            "ai_enriched": False,
        }

    project_state = _project_state(db, project)
    stage_rows: list[dict[str, Any]] = []
    gaps: list[str] = []
    strengths: list[str] = []

    for stage in RESEARCH_STAGES:
        key = stage["key"]
        label = stage["label_ar"] if lang == "ar" else stage["label_en"]
        user_status = project_state["stages"].get(key, "missing")
        paper_stats = _paper_stage_stats(papers, key)

        # Score: how user compares to common practice in references
        common_in_refs = paper_stats["detected_ratio"] >= 0.5
        user_has = user_status in ("present", "completed", "in_progress", "partial")

        if common_in_refs and not user_has:
            verdict = "behind"
            gaps.append(t(lang, "bench.gap_missing_stage", stage=label))
        elif user_has and paper_stats["detected_count"] == 0:
            verdict = "ahead_or_unique"
            strengths.append(t(lang, "bench.strength_user_has", stage=label))
        elif user_has and common_in_refs:
            verdict = "aligned"
            strengths.append(t(lang, "bench.strength_aligned", stage=label))
        elif not common_in_refs and not user_has:
            verdict = "optional"
        else:
            verdict = "review"

        examples = []
        for p in papers[:5]:
            m = next((x for x in p.stage_mappings if x.stage_key == key), None)
            if m and m.status in ("detected", "partially_detected"):
                examples.append(
                    {
                        "document_id": p.id,
                        "title": p.title_detected or p.original_filename,
                        "status": m.status,
                        "heading": m.original_heading,
                        "summary": (m.ai_summary or "")[:280],
                    }
                )

        stage_rows.append(
            {
                "stage_key": key,
                "label": label,
                "purpose": stage_purpose(lang, key),
                "user_status": user_status,
                "papers_detected": paper_stats["detected_count"],
                "papers_total": paper_stats["total"],
                "papers_detected_ratio": round(paper_stats["detected_ratio"], 2),
                "verdict": verdict,
                "verdict_label": t(lang, f"bench.verdict.{verdict}"),
                "recommendation": _stage_recommendation(lang, key, label, verdict, user_status),
                "reference_examples": examples[:3],
            }
        )

    # Method / design comparison
    design_notes = _compare_designs(db, project, papers, lang)
    coverage = _coverage_score(stage_rows)
    recommendations = _top_recommendations(stage_rows, lang, design_notes)

    result: dict[str, Any] = {
        "language": lang,
        "status": "ok",
        "message": t(lang, "bench.message_ok", n=len(papers)),
        "integrity_notice": t(lang, "bench.integrity"),
        "project": {
            "id": project.id,
            "working_title": project.working_title,
            "document_type": project.document_type,
            "current_stage": project.current_stage,
            "completion_percent": project.completion_percent,
            "profile": project_state["profile_flags"],
            "counts": project_state["counts"],
        },
        "papers": [
            {
                "id": p.id,
                "title": p.title_detected or p.original_filename,
                "document_type": p.document_type,
                "research_design": p.research_design,
                "methodology_paradigm": p.methodology_paradigm,
                "processing_status": p.processing_status,
            }
            for p in papers
        ],
        "stage_benchmarks": stage_rows,
        "design_comparison": design_notes,
        "gaps": gaps[:12],
        "strengths": strengths[:12],
        "recommendations": recommendations,
        "overall_score": coverage,
        "score_explanation": t(lang, "bench.score_explain"),
        "ai_enriched": False,
    }

    # Optional AI narrative
    ai = await _ai_narrative(project, papers, result, lang)
    if ai:
        result["ai_narrative"] = ai
        result["ai_enriched"] = True
        if ai.get("extra_recommendations"):
            result["recommendations"] = (
                list(result["recommendations"]) + list(ai["extra_recommendations"])
            )[:15]

    return result


def _project_state(db: Session, project: ResearchProject) -> dict[str, Any]:
    profile = project.profile
    questions = (
        db.query(ResearchQuestion).filter(ResearchQuestion.project_id == project.id).count()
    )
    objectives = (
        db.query(ResearchObjective).filter(ResearchObjective.project_id == project.id).count()
    )
    hypotheses = db.query(Hypothesis).filter(Hypothesis.project_id == project.id).count()
    variables = db.query(Variable).filter(Variable.project_id == project.id).count()
    designs = db.query(ResearchDesign).filter(ResearchDesign.project_id == project.id).count()
    populations = db.query(Population).filter(Population.project_id == project.id).count()
    sampling = db.query(SamplingPlan).filter(SamplingPlan.project_id == project.id).count()
    instruments = db.query(Instrument).filter(Instrument.project_id == project.id).count()
    analysis = db.query(AnalysisPlan).filter(AnalysisPlan.project_id == project.id).count()
    progress = {
        s.stage_key: s.status
        for s in db.query(StageProgress).filter(StageProgress.project_id == project.id).all()
    }

    def stage_user_status(key: str) -> str:
        if progress.get(key) == "completed":
            return "completed"
        if progress.get(key) == "in_progress":
            return "in_progress"
        # Content signals
        if key == "idea" and profile and profile.refined_idea:
            return "present"
        if key == "literature_synthesis" and profile and profile.research_gap:
            return "present"
        if key == "problem_purpose" and profile and (
            profile.research_problem or profile.overall_aim
        ):
            return "present"
        if key == "questions_objectives" and (questions or objectives):
            return "present" if questions and objectives else "partial"
        if key == "hypotheses" and hypotheses:
            return "present"
        if key == "constructs_variables" and variables:
            return "present"
        if key == "methodology" and designs:
            return "present"
        if key == "population_sampling" and (populations or sampling or project.population_summary):
            return "present"
        if key == "instruments" and instruments:
            return "present"
        if key == "ethics" and profile and profile.ethics_requirements:
            return "present"
        if key == "analysis_plan" and analysis:
            return "present"
        if key == "references":
            # user project refs table
            from app.models.literature import Reference

            if db.query(Reference).filter(Reference.project_id == project.id).count():
                return "present"
        return "missing"

    stages = {s["key"]: stage_user_status(s["key"]) for s in RESEARCH_STAGES}
    return {
        "stages": stages,
        "profile_flags": {
            "has_problem": bool(profile and profile.research_problem),
            "has_gap": bool(profile and profile.research_gap),
            "has_aim": bool(profile and profile.overall_aim),
            "has_ethics": bool(profile and profile.ethics_requirements),
        },
        "counts": {
            "questions": questions,
            "objectives": objectives,
            "hypotheses": hypotheses,
            "variables": variables,
            "designs": designs,
            "populations": populations,
            "sampling_plans": sampling,
            "instruments": instruments,
            "analysis_plans": analysis,
        },
    }


def _paper_stage_stats(papers: list[SourceDocument], stage_key: str) -> dict[str, Any]:
    total = len(papers)
    detected = 0
    for p in papers:
        m = next((x for x in p.stage_mappings if x.stage_key == stage_key), None)
        if m and m.status in ("detected", "partially_detected"):
            detected += 1
    return {
        "total": total,
        "detected_count": detected,
        "detected_ratio": (detected / total) if total else 0.0,
    }


def _stage_recommendation(
    lang: str, key: str, label: str, verdict: str, user_status: str
) -> str:
    if verdict == "behind":
        return t(lang, "bench.rec_fill_stage", stage=label)
    if verdict == "partial" or user_status == "partial":
        return t(lang, "bench.rec_complete_stage", stage=label)
    if verdict == "aligned":
        return t(lang, "bench.rec_refine_stage", stage=label)
    if verdict == "ahead_or_unique":
        return t(lang, "bench.rec_justify_stage", stage=label)
    return t(lang, "bench.rec_optional_stage", stage=label)


def _compare_designs(
    db: Session, project: ResearchProject, papers: list[SourceDocument], lang: str
) -> dict[str, Any]:
    user_designs = (
        db.query(ResearchDesign).filter(ResearchDesign.project_id == project.id).all()
    )
    user_types = [d.design_type for d in user_designs if d.design_type]
    paper_designs = [p.research_design for p in papers if p.research_design]
    paper_paradigms = [p.methodology_paradigm for p in papers if p.methodology_paradigm]

    notes = []
    if paper_designs and not user_types:
        notes.append(t(lang, "bench.design_user_missing", designs=", ".join(sorted(set(paper_designs))[:5])))
    elif user_types and paper_designs:
        notes.append(
            t(
                lang,
                "bench.design_compare",
                user=", ".join(user_types[:3]),
                papers=", ".join(sorted(set(paper_designs))[:5]),
            )
        )
    if paper_paradigms:
        notes.append(
            t(lang, "bench.paradigm_refs", paradigms=", ".join(sorted(set(paper_paradigms))))
        )

    return {
        "user_designs": user_types,
        "reference_designs": list(sorted(set(d for d in paper_designs if d))),
        "reference_paradigms": list(sorted(set(p for p in paper_paradigms if p))),
        "notes": notes,
    }


def _coverage_score(stage_rows: list[dict[str, Any]]) -> int:
    """0-100: share of stages that are aligned or not behind (excluding optional)."""
    relevant = [r for r in stage_rows if r["verdict"] != "optional"]
    if not relevant:
        return 0
    good = sum(1 for r in relevant if r["verdict"] in ("aligned", "ahead_or_unique", "review") and r["user_status"] != "missing")
    # stricter: present content
    present = sum(
        1
        for r in relevant
        if r["user_status"] in ("present", "completed", "in_progress", "partial")
    )
    return int(round(100 * present / len(relevant)))


def _top_recommendations(
    stage_rows: list[dict[str, Any]], lang: str, design_notes: dict[str, Any]
) -> list[str]:
    recs = []
    behind = [r for r in stage_rows if r["verdict"] == "behind"]
    behind.sort(key=lambda r: -r["papers_detected_ratio"])
    for r in behind[:5]:
        recs.append(r["recommendation"])
    partial = [r for r in stage_rows if r["user_status"] == "partial"]
    for r in partial[:3]:
        recs.append(r["recommendation"])
    for n in design_notes.get("notes") or []:
        recs.append(n)
    if not recs:
        recs.append(t(lang, "bench.rec_good"))
    recs.append(t(lang, "bench.rec_integrity"))
    return recs[:12]


async def _ai_narrative(
    project: ResearchProject,
    papers: list[SourceDocument],
    result: dict[str, Any],
    lang: str,
) -> dict[str, Any] | None:
    client = _client()
    if client is None:
        return None

    brief_papers = [
        {
            "title": p.title_detected or p.original_filename,
            "type": p.document_type,
            "design": p.research_design,
        }
        for p in papers[:8]
    ]
    behind = [r["label"] for r in result["stage_benchmarks"] if r["verdict"] == "behind"][:8]
    aligned = [r["label"] for r in result["stage_benchmarks"] if r["verdict"] == "aligned"][:8]
    profile = build_profile_context(project)

    lang_rule = t(lang, "chat.lang_instruction")
    prompt = f"""You are ResearchGuide AI. Benchmark the USER's research project against uploaded REFERENCE papers for LEARNING only.

User project:
{json.dumps({k: profile.get(k) for k in ('working_title','document_type','research_problem','research_gap','overall_aim','population')}, ensure_ascii=False)}

Reference papers:
{json.dumps(brief_papers, ensure_ascii=False)}

Stages where user is behind common reference practice: {behind}
Stages already aligned: {aligned}
Coverage score: {result.get('overall_score')}

Return STRICT JSON:
{{
  "executive_summary": "3-6 sentences",
  "what_references_do_well": ["..."],
  "where_user_project_needs_work": ["..."],
  "method_fit_notes": ["..."],
  "extra_recommendations": ["..."],
  "caution": "remind not to copy reference papers"
}}

Rules:
- Do not invent findings from the references.
- Do not tell the user to paste reference text into their thesis.
- Focus on structure, methodology alignment, and missing decisions.
"""
    try:
        resp = await client.chat.completions.create(
            model=settings.ai_model,
            messages=[
                {"role": "system", "content": lang_rule},
                {
                    "role": "system",
                    "content": "Help researchers benchmark structure against study papers without plagiarism.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.35,
        )
        raw = resp.choices[0].message.content or ""
        data = _parse_json(raw)
        if not data:
            return None
        data["model"] = settings.ai_model
        return data
    except Exception as exc:  # noqa: BLE001
        logger.warning("Benchmark AI narrative failed: %s", exc)
        return None


def _parse_json(raw: str) -> dict[str, Any] | None:
    import re

    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None
