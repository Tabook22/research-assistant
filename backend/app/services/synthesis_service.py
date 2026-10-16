"""
Automated multi-document research synthesis dashboard.

Aggregates insights across uploaded library papers so researchers can learn
patterns, methods, gaps, and writing moves — without treating sources as their own work.
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter, defaultdict
from typing import Any

from app.services.ai_gateway import task_client
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.i18n.lang import normalize_lang, stage_purpose, t
from app.models.library import SourceDocument
from app.models.mixins import RESEARCH_STAGES
from app.models.project import ResearchProject

logger = logging.getLogger(__name__)
settings = get_settings()


def _client():
    return task_client("analysis")


async def build_synthesis_dashboard(
    db: Session,
    project: ResearchProject,
    document_ids: list[int] | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    lang = normalize_lang(language or project.writing_language or "en")

    q = (
        db.query(SourceDocument)
        .options(
            joinedload(SourceDocument.stage_mappings),
            joinedload(SourceDocument.elements),
        )
        .filter(SourceDocument.project_id == project.id)
    )
    if document_ids:
        q = q.filter(SourceDocument.id.in_(document_ids))
    papers = q.order_by(SourceDocument.id.desc()).all()

    if not papers:
        return {
            "language": lang,
            "status": "empty",
            "headline": t(lang, "syn.empty_headline"),
            "message": t(lang, "syn.empty_msg"),
            "integrity_notice": t(lang, "syn.integrity"),
            "paper_count": 0,
            "papers": [],
            "insight_cards": [],
            "theme_cloud": [],
            "method_patterns": [],
            "stage_heatmap": [],
            "gap_signals": [],
            "writing_moves": [],
            "learning_path": [t(lang, "syn.path_upload")],
            "comparison_matrix": [],
            "ai_enriched": False,
        }

    paper_briefs = [_paper_brief(p, lang) for p in papers]
    theme_cloud = _theme_cloud(papers, lang)
    method_patterns = _method_patterns(papers, lang)
    stage_heatmap = _stage_heatmap(papers, lang)
    gap_signals = _gap_signals(papers, lang)
    writing_moves = _writing_moves(papers, lang)
    comparison_matrix = _comparison_matrix(papers, lang)
    insight_cards = _insight_cards(
        papers, theme_cloud, method_patterns, gap_signals, stage_heatmap, lang
    )
    learning_path = _learning_path(papers, stage_heatmap, gap_signals, lang)

    result: dict[str, Any] = {
        "language": lang,
        "status": "ok",
        "headline": t(lang, "syn.headline", n=len(papers)),
        "message": t(lang, "syn.message"),
        "integrity_notice": t(lang, "syn.integrity"),
        "paper_count": len(papers),
        "papers": paper_briefs,
        "insight_cards": insight_cards,
        "theme_cloud": theme_cloud,
        "method_patterns": method_patterns,
        "stage_heatmap": stage_heatmap,
        "gap_signals": gap_signals,
        "writing_moves": writing_moves,
        "learning_path": learning_path,
        "comparison_matrix": comparison_matrix,
        "ai_enriched": False,
        "stats": {
            "types": dict(Counter(p.document_type or "unknown" for p in papers)),
            "paradigms": dict(
                Counter(p.methodology_paradigm or "unknown" for p in papers)
            ),
            "designs": dict(
                Counter(p.research_design or "unspecified" for p in papers)
            ),
            "with_results": sum(
                1
                for p in papers
                if _stage_status(p, "results") in ("detected", "partially_detected")
            ),
            "with_methods": sum(
                1
                for p in papers
                if _stage_status(p, "methodology") in ("detected", "partially_detected")
            ),
        },
    }

    ai = await _ai_synthesis_narrative(project, paper_briefs, result, lang)
    if ai:
        result["ai_synthesis"] = ai
        result["ai_enriched"] = True
        if ai.get("learning_path_extra"):
            result["learning_path"] = list(result["learning_path"]) + list(
                ai["learning_path_extra"]
            )[:5]
        if ai.get("insight_highlights"):
            for i, h in enumerate(ai["insight_highlights"][:3]):
                result["insight_cards"].insert(
                    0,
                    {
                        "id": f"ai_{i}",
                        "kind": "ai",
                        "title": t(lang, "syn.card_ai_title"),
                        "body": str(h),
                        "priority": "high",
                    },
                )

    return result


def _paper_brief(p: SourceDocument, lang: str) -> dict[str, Any]:
    study = {}
    if p.learning_report_json:
        try:
            lr = json.loads(p.learning_report_json)
            study = lr.get("study_summary") or {}
        except json.JSONDecodeError:
            study = {}
    return {
        "id": p.id,
        "title": p.title_detected or p.original_filename,
        "filename": p.original_filename,
        "document_type": p.document_type,
        "document_type_confidence": p.document_type_confidence,
        "academic_level": p.academic_level,
        "research_design": p.research_design,
        "methodology_paradigm": p.methodology_paradigm,
        "year": p.year_detected,
        "processing_status": p.processing_status,
        "main_ideas": study.get("main_ideas"),
        "methods": study.get("methods"),
        "findings": study.get("findings"),
        "conclusions": study.get("conclusions"),
        "writing_style": study.get("writing_style") or [],
    }


def _stage_status(p: SourceDocument, key: str) -> str:
    m = next((x for x in p.stage_mappings if x.stage_key == key), None)
    return m.status if m else "not_detected"


def _theme_cloud(papers: list[SourceDocument], lang: str) -> list[dict[str, Any]]:
    """Extract recurring keywords/phrases from titles, abstracts, gaps."""
    bag: Counter[str] = Counter()
    stop = {
        "the", "and", "of", "in", "to", "a", "for", "on", "with", "this", "study",
        "research", "among", "from", "that", "was", "were", "using", "based",
        "في", "من", "على", "إلى", "عن", "مع", "هذا", "هذه", "التي", "الذي", "دراسة",
    }
    for p in papers:
        chunks = [
            p.title_detected or "",
            p.abstract_excerpt or "",
            p.original_filename or "",
        ]
        for el in p.elements or []:
            if el.element_type in ("research_title", "overall_aim", "abstract"):
                chunks.append(el.value_text[:400])
        for m in p.stage_mappings or []:
            if m.stage_key in ("literature_synthesis", "problem_purpose") and m.ai_summary:
                chunks.append(m.ai_summary[:300])
        text = " ".join(chunks).lower()
        words = re.findall(r"[a-zA-Z\u0600-\u06FF]{4,}", text)
        for w in words:
            if w not in stop:
                bag[w] += 1

    top = bag.most_common(18)
    if not top:
        return [{"term": t(lang, "syn.no_themes"), "weight": 1, "papers": 0}]
    max_c = top[0][1] or 1
    return [
        {
            "term": term,
            "count": count,
            "weight": round(count / max_c, 2),
            "label": term,
        }
        for term, count in top
        if count >= 1
    ]


def _method_patterns(papers: list[SourceDocument], lang: str) -> list[dict[str, Any]]:
    designs = Counter(p.research_design or "unspecified" for p in papers)
    paradigms = Counter(p.methodology_paradigm or "unspecified" for p in papers)
    out = []
    for design, c in designs.most_common(8):
        out.append(
            {
                "kind": "design",
                "name": design,
                "count": c,
                "share": round(c / len(papers), 2),
                "insight": t(lang, "syn.method_design", name=design, n=c, total=len(papers)),
            }
        )
    for para, c in paradigms.most_common(5):
        out.append(
            {
                "kind": "paradigm",
                "name": para,
                "count": c,
                "share": round(c / len(papers), 2),
                "insight": t(lang, "syn.method_paradigm", name=para, n=c, total=len(papers)),
            }
        )
    return out


def _stage_heatmap(papers: list[SourceDocument], lang: str) -> list[dict[str, Any]]:
    n = len(papers)
    rows = []
    for stage in RESEARCH_STAGES:
        key = stage["key"]
        label = stage["label_ar"] if lang == "ar" else stage["label_en"]
        det = sum(
            1
            for p in papers
            if _stage_status(p, key) in ("detected", "partially_detected")
        )
        partial = sum(1 for p in papers if _stage_status(p, key) == "partially_detected")
        na = sum(1 for p in papers if _stage_status(p, key) == "not_applicable")
        ratio = det / n if n else 0
        rows.append(
            {
                "stage_key": key,
                "label": label,
                "purpose": stage_purpose(lang, key),
                "detected": det,
                "partial": partial,
                "not_applicable": na,
                "missing": n - det - na,
                "coverage": round(ratio, 2),
                "intensity": "high" if ratio >= 0.7 else "medium" if ratio >= 0.35 else "low",
                "lesson": t(lang, "syn.heat_lesson", stage=label, pct=int(ratio * 100)),
            }
        )
    return rows


def _gap_signals(papers: list[SourceDocument], lang: str) -> list[dict[str, Any]]:
    signals = []
    # Stages rarely covered → possible under-documented areas in this literature set
    heat = _stage_heatmap(papers, lang)
    rare = [h for h in heat if h["coverage"] < 0.35 and h["not_applicable"] < len(papers) * 0.5]
    for h in sorted(rare, key=lambda x: x["coverage"])[:6]:
        signals.append(
            {
                "type": "underdocumented_stage",
                "title": t(lang, "syn.gap_under_title", stage=h["label"]),
                "body": t(lang, "syn.gap_under_body", stage=h["label"], pct=int(h["coverage"] * 100)),
                "stage_key": h["stage_key"],
            }
        )

    # Mixed designs → methodological diversity opportunity
    designs = {p.research_design for p in papers if p.research_design}
    if len(designs) >= 2:
        signals.append(
            {
                "type": "design_diversity",
                "title": t(lang, "syn.gap_design_title"),
                "body": t(lang, "syn.gap_design_body", designs=", ".join(sorted(designs)[:6])),
            }
        )

    # Few with local/context signals in titles
    if len(papers) >= 2:
        signals.append(
            {
                "type": "context_check",
                "title": t(lang, "syn.gap_context_title"),
                "body": t(lang, "syn.gap_context_body"),
            }
        )
    return signals[:8]


def _writing_moves(papers: list[SourceDocument], lang: str) -> list[dict[str, Any]]:
    moves = []
    has_problem = sum(
        1 for p in papers if _stage_status(p, "problem_purpose") in ("detected", "partially_detected")
    )
    has_gap = sum(
        1
        for p in papers
        if _stage_status(p, "literature_synthesis") in ("detected", "partially_detected")
    )
    has_methods = sum(
        1 for p in papers if _stage_status(p, "methodology") in ("detected", "partially_detected")
    )
    has_results = sum(
        1 for p in papers if _stage_status(p, "results") in ("detected", "partially_detected")
    )
    n = len(papers)
    moves.append(
        {
            "move": t(lang, "syn.move_problem"),
            "frequency": has_problem,
            "tip": t(lang, "syn.move_problem_tip"),
            "share": round(has_problem / n, 2) if n else 0,
        }
    )
    moves.append(
        {
            "move": t(lang, "syn.move_gap"),
            "frequency": has_gap,
            "tip": t(lang, "syn.move_gap_tip"),
            "share": round(has_gap / n, 2) if n else 0,
        }
    )
    moves.append(
        {
            "move": t(lang, "syn.move_methods"),
            "frequency": has_methods,
            "tip": t(lang, "syn.move_methods_tip"),
            "share": round(has_methods / n, 2) if n else 0,
        }
    )
    moves.append(
        {
            "move": t(lang, "syn.move_results"),
            "frequency": has_results,
            "tip": t(lang, "syn.move_results_tip"),
            "share": round(has_results / n, 2) if n else 0,
        }
    )
    return moves


def _comparison_matrix(papers: list[SourceDocument], lang: str) -> list[dict[str, Any]]:
    """Compact per-paper insight row for dashboard table."""
    rows = []
    for p in papers:
        brief = _paper_brief(p, lang)
        rows.append(
            {
                "document_id": p.id,
                "title": brief["title"],
                "type": p.document_type or "—",
                "design": p.research_design or "—",
                "paradigm": p.methodology_paradigm or "—",
                "main_ideas": (brief.get("main_ideas") or "—")[:220],
                "methods": (brief.get("methods") or "—")[:180],
                "findings": (brief.get("findings") or "—")[:180],
                "conclusions": (brief.get("conclusions") or "—")[:180],
                "stages_covered": sum(
                    1
                    for m in p.stage_mappings
                    if m.status in ("detected", "partially_detected")
                ),
            }
        )
    return rows


def _insight_cards(
    papers: list[SourceDocument],
    themes: list[dict[str, Any]],
    methods: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    heat: list[dict[str, Any]],
    lang: str,
) -> list[dict[str, Any]]:
    cards = []
    cards.append(
        {
            "id": "corpus",
            "kind": "corpus",
            "title": t(lang, "syn.card_corpus_title"),
            "body": t(lang, "syn.card_corpus_body", n=len(papers)),
            "priority": "high",
        }
    )
    if themes and themes[0].get("count", 0) > 1:
        top = ", ".join(th["term"] for th in themes[:5])
        cards.append(
            {
                "id": "themes",
                "kind": "theme",
                "title": t(lang, "syn.card_theme_title"),
                "body": t(lang, "syn.card_theme_body", terms=top),
                "priority": "high",
            }
        )
    design_methods = [m for m in methods if m["kind"] == "design"]
    if design_methods:
        top_d = design_methods[0]
        cards.append(
            {
                "id": "methods",
                "kind": "method",
                "title": t(lang, "syn.card_method_title"),
                "body": top_d["insight"],
                "priority": "medium",
            }
        )
    strong = [h for h in heat if h["intensity"] == "high"][:3]
    if strong:
        cards.append(
            {
                "id": "strong_stages",
                "kind": "structure",
                "title": t(lang, "syn.card_structure_title"),
                "body": t(
                    lang,
                    "syn.card_structure_body",
                    stages=", ".join(h["label"] for h in strong),
                ),
                "priority": "medium",
            }
        )
    if gaps:
        cards.append(
            {
                "id": "gap0",
                "kind": "gap",
                "title": gaps[0]["title"],
                "body": gaps[0]["body"],
                "priority": "high",
            }
        )
    cards.append(
        {
            "id": "learn",
            "kind": "learn",
            "title": t(lang, "syn.card_learn_title"),
            "body": t(lang, "syn.card_learn_body"),
            "priority": "medium",
        }
    )
    return cards


def _learning_path(
    papers: list[SourceDocument],
    heat: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    lang: str,
) -> list[str]:
    path = [
        t(lang, "syn.path1"),
        t(lang, "syn.path2"),
    ]
    # Suggest studying a stage that is common
    common = sorted(heat, key=lambda h: -h["coverage"])
    if common:
        path.append(t(lang, "syn.path3", stage=common[0]["label"]))
    if gaps:
        path.append(t(lang, "syn.path4", gap=gaps[0]["title"]))
    path.append(t(lang, "syn.path5"))
    path.append(t(lang, "syn.path6"))
    return path


async def _ai_synthesis_narrative(
    project: ResearchProject,
    paper_briefs: list[dict[str, Any]],
    result: dict[str, Any],
    lang: str,
) -> dict[str, Any] | None:
    client = _client()
    if client is None:
        return None

    slim = [
        {
            "title": p.get("title"),
            "type": p.get("document_type"),
            "design": p.get("research_design"),
            "ideas": (p.get("main_ideas") or "")[:200],
            "methods": (p.get("methods") or "")[:160],
        }
        for p in paper_briefs[:10]
    ]
    lang_rule = t(lang, "chat.lang_instruction")
    prompt = f"""You are ResearchGuide AI. Create a multi-paper RESEARCH SYNTHESIS for LEARNING.

User is studying these uploaded papers (not writing them as their own results):
{json.dumps(slim, ensure_ascii=False)}

User project title (context only): {project.working_title}
Field: {project.research_field}

Top themes: {[th.get('term') for th in result.get('theme_cloud', [])[:8]]}
Method patterns: {[m.get('name') for m in result.get('method_patterns', [])[:6]]}

Return STRICT JSON:
{{
  "story_of_the_literature": "4-7 sentences narrative synthesis for a student",
  "what_authors_tend_to_do": ["writing/structure patterns"],
  "where_they_disagree_or_differ": ["..."],
  "insight_highlights": ["short punchy insights for dashboard cards"],
  "learning_path_extra": ["actionable study steps"],
  "caution": "anti-plagiarism reminder"
}}

Rules:
- Do not invent specific findings not implied by the briefs.
- Teach how to read papers; never encourage copying.
- Keep language accessible for early researchers.
"""
    try:
        resp = await client.chat.completions.create(
            model=settings.ai_model,
            messages=[
                {"role": "system", "content": lang_rule},
                {
                    "role": "system",
                    "content": "Synthesize study papers for learning; protect research integrity.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        raw = resp.choices[0].message.content or ""
        data = _parse_json(raw)
        if data:
            data["model"] = getattr(client, "model", settings.ai_model)
        return data
    except Exception as exc:  # noqa: BLE001
        logger.warning("AI synthesis failed: %s", exc)
        return None


def _parse_json(raw: str) -> dict[str, Any] | None:
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
