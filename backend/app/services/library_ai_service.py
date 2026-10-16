"""AI enrichment for library analysis and guided writing (integrity-first)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.services.ai_gateway import task_client

from app.config import get_settings
from app.i18n.lang import normalize_lang, stage_purpose, t
from app.models.library import DocumentStageMapping, SourceDocument
from app.models.mixins import RESEARCH_STAGES
from app.models.project import ResearchProject
from app.services.project_service import build_profile_context

logger = logging.getLogger(__name__)
settings = get_settings()


def _client():
    return task_client("analysis")


async def enrich_document_analysis(
    doc: SourceDocument,
    stage_rows: list[DocumentStageMapping],
    language: str | None = None,
) -> dict[str, Any]:
    """
    Optionally deepen learning report with AI.
    Returns enrichment dict or empty if AI unavailable/fails.
    Never rewrites exact source excerpts.
    """
    client = _client()
    if client is None:
        return {"ai_enriched": False, "reason": "Analysis AI profile not configured"}

    lang = normalize_lang(language or "en")
    lang_name = "Arabic" if lang == "ar" else "English"

    stage_brief = [
        {
            "stage": m.stage_key,
            "status": m.status,
            "heading": m.original_heading,
            "summary": (m.ai_summary or "")[:400],
        }
        for m in stage_rows
        if m.status in ("detected", "partially_detected")
    ][:14]

    prompt = f"""You are an academic methodology coach. Analyze this UPLOADED REFERENCE paper for LEARNING only.

Document type (provisional): {doc.document_type}
Design: {doc.research_design}
Paradigm: {doc.methodology_paradigm}
Title guess: {doc.title_detected}
Abstract excerpt: {(doc.abstract_excerpt or '')[:800]}

Detected stages:
{json.dumps(stage_brief, ensure_ascii=False)}

Return STRICT JSON only:
{{
  "writing_patterns": ["..."],
  "methodological_strengths": ["..."],
  "methodological_weaknesses": ["..."],
  "lessons_for_new_researchers": ["..."],
  "alignment_observations": ["..."],
  "what_not_to_copy": ["..."],
  "integrity_reminder": "short reminder against plagiarism"
}}

Rules:
- Teach structure and reasoning, not copying.
- Do not invent bibliographic details not implied by the excerpts.
- Do not present this paper's results as the user's results.
- CRITICAL: Write ALL string values in the JSON entirely in {lang_name}.
"""
    try:
        resp = await client.chat.completions.create(
            model=settings.ai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You help researchers learn methodology from examples without plagiarism. "
                        f"Respond with JSON string values in {lang_name} only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        raw = resp.choices[0].message.content or ""
        data = _extract_json(raw)
        if not data:
            return {"ai_enriched": False, "reason": "Could not parse AI JSON"}
        data["ai_enriched"] = True
        data["model"] = getattr(client, "model", settings.ai_model)
        return data
    except Exception as exc:  # noqa: BLE001
        logger.warning("AI enrichment failed: %s", exc)
        return {"ai_enriched": False, "reason": f"{exc.__class__.__name__}"}


def build_write_section_guide(
    project: ResearchProject,
    doc: SourceDocument,
    stage_key: str,
    mapping: DocumentStageMapping | None,
    language: str | None = None,
) -> dict[str, Any]:
    """Deterministic guided writing scaffold from library stage + user project profile."""
    lang = normalize_lang(language or project.writing_language or "en")
    stage_meta = next((s for s in RESEARCH_STAGES if s["key"] == stage_key), None)
    label = (
        (stage_meta["label_ar"] if lang == "ar" else stage_meta["label_en"])
        if stage_meta
        else stage_key
    )
    purpose = stage_purpose(lang, stage_key) or t(lang, "write.purpose_fallback")
    profile = build_profile_context(project)

    ref_status = mapping.status if mapping else "not_detected"
    ref_summary = (mapping.ai_summary if mapping else None) or t(lang, "write.ref_not_detected")
    ref_heading = mapping.original_heading if mapping else None
    ref_excerpt = (mapping.extracted_excerpt if mapping else None) or ""
    if len(ref_excerpt) > 500:
        ref_excerpt = ref_excerpt[:500] + "…"

    questions = _stage_questions(stage_key, profile, lang)
    outline = _stage_outline(stage_key, label, lang)
    patterns = [
        t(lang, "write.pattern_status", status=ref_status),
        t(lang, "write.pattern_heading", heading=ref_heading or "—"),
        t(lang, "write.pattern_observe"),
        t(lang, "write.pattern_replace"),
    ]

    return {
        "stage_key": stage_key,
        "stage_label": label,
        "purpose": purpose,
        "language": lang,
        "reference": {
            "document_id": doc.id,
            "document_title": doc.title_detected or doc.original_filename,
            "status": ref_status,
            "heading": ref_heading,
            "summary": ref_summary,
            "short_excerpt_for_illustration_only": ref_excerpt or None,
            "lessons": mapping.lessons_for_user if mapping else None,
            "writing_strategy": mapping.writing_strategy if mapping else None,
        },
        "user_project_snapshot": {
            "working_title": project.working_title,
            "document_type": project.document_type,
            "population": project.population_summary,
            "research_problem": profile.get("research_problem"),
            "research_gap": profile.get("research_gap"),
            "overall_aim": profile.get("overall_aim"),
        },
        "structural_pattern_from_reference": patterns,
        "questions_for_you": questions,
        "outline_template": outline,
        "citation_placeholders": [
            t(lang, "write.cite1"),
            t(lang, "write.cite2"),
            t(lang, "write.cite3"),
        ],
        "integrity_rules": [
            t(lang, "write.rule1"),
            t(lang, "write.rule2"),
            t(lang, "write.rule3"),
            t(lang, "write.rule4"),
            t(lang, "write.rule5"),
        ],
        "mistakes_to_avoid": [
            t(lang, "write.mistake1"),
            t(lang, "write.mistake2"),
            t(lang, "write.mistake3"),
            t(lang, "write.mistake4"),
        ],
    }


async def draft_section_from_answers(
    project: ResearchProject,
    doc: SourceDocument,
    stage_key: str,
    guide: dict[str, Any],
    user_answers: dict[str, str],
    language: str | None = None,
) -> dict[str, Any]:
    """
    Create an ORIGINAL draft from user answers. Reference paper used only as structural coach.
    """
    lang = normalize_lang(language or guide.get("language") or project.writing_language or "en")
    client = _client()
    label = guide.get("stage_label", stage_key)
    answers_text = "\n".join(f"- {k}: {v}" for k, v in user_answers.items() if v and str(v).strip())
    outline_lines = "\n".join(f"- {b}" for b in guide.get("outline_template", []))

    if not answers_text.strip():
        return {
            "draft": t(
                lang,
                "write.draft_need_input",
                label=label,
                outline=outline_lines,
            ),
            "source": "template_only",
            "ai_used": False,
        }

    if client is None:
        numbered = "\n".join(
            f"{i+1}. {b}" for i, b in enumerate(guide.get("outline_template", []))
        )
        draft = t(
            lang,
            "write.draft_offline",
            label=label,
            title=project.working_title,
            answers=answers_text,
            outline=numbered,
        )
        return {"draft": draft, "source": "offline_scaffold", "ai_used": False}

    lang_name = t(lang, "write.lang_ar" if lang == "ar" else "write.lang_en")
    system = t(lang, "write.ai_system", lang_name=lang_name)
    user_msg = f"""Stage: {label}
User project title: {project.working_title}
Document type: {project.document_type}
Population: {project.population_summary}
Profile aim: {guide.get('user_project_snapshot', {}).get('overall_aim')}
Profile problem: {guide.get('user_project_snapshot', {}).get('research_problem')}

Reference paper (structure only — DO NOT imitate wording):
Title: {guide.get('reference', {}).get('document_title')}
Stage status: {guide.get('reference', {}).get('status')}
Reference summary of approach: {guide.get('reference', {}).get('summary')}

User answers (primary content source):
{answers_text}

Outline to follow:
{json.dumps(guide.get('outline_template'), ensure_ascii=False)}

Write the entire draft in {lang_name}.
"""
    try:
        resp = await client.chat.completions.create(
            model=settings.ai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.35,
        )
        text = resp.choices[0].message.content or ""
        marker = "مؤقت" if lang == "ar" else "PROVISIONAL"
        if marker not in text.upper() and "PROVISIONAL" not in text.upper() and "مؤقت" not in text:
            prefix = "[مؤقت—يتطلب الموافقة]\n\n" if lang == "ar" else "[PROVISIONAL—REQUIRES APPROVAL]\n\n"
            text = prefix + text
        return {"draft": text, "source": "ai", "ai_used": True, "model": getattr(client, "model", settings.ai_model)}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Draft generation failed: %s", exc)
        return {
            "draft": t(
                lang,
                "write.draft_fail",
                label=label,
                error=exc.__class__.__name__,
                answers=answers_text,
            ),
            "source": "error_fallback",
            "ai_used": False,
        }


def _extract_json(raw: str) -> dict[str, Any] | None:
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


def _looks_latin_heavy(text: str | None, min_latin: int = 12) -> bool:
    """Heuristic: free text that still appears mostly English/Latin script."""
    if not text or not str(text).strip():
        return False
    s = str(text)
    latin = len(re.findall(r"[A-Za-z]", s))
    arabic = len(re.findall(r"[\u0600-\u06FF]", s))
    if latin < min_latin:
        return False
    return latin > max(arabic * 1.1, 1)


async def _free_translate_en_to_ar(text: str) -> str | None:
    """
    Free EN→AR without XAI_API_KEY. Tries multiple public services.
    Best-effort; returns None on failure.
    """
    import httpx
    from urllib.parse import quote

    q = (text or "").strip()
    if not q:
        return None

    def _ok(src: str, out: str | None) -> str | None:
        if not out or not str(out).strip():
            return None
        out_s = str(out).strip()
        low = out_s.lower()
        if "mymemory warning" in low or "quota" in low:
            return None
        if low == src.strip().lower() and len(src) > 40:
            return None
        # Prefer results that actually contain Arabic letters
        if not re.search(r"[\u0600-\u06FF]", out_s) and len(src) > 20:
            return None
        return out_s

    # Chunk long text for public APIs
    chunks: list[str] = []
    remaining = q
    while remaining:
        chunks.append(remaining[:450])
        remaining = remaining[450:]
    chunks = chunks[:14]

    async def via_google(client: httpx.AsyncClient, chunk: str) -> str | None:
        # Unofficial free Google Translate endpoint (no key)
        url = (
            "https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl=en&tl=ar&dt=t&q={quote(chunk)}"
        )
        resp = await client.get(url)
        if resp.status_code != 200:
            return None
        data = resp.json()
        # data[0] is list of [translated, original, ...]
        parts = []
        try:
            for row in data[0] or []:
                if row and row[0]:
                    parts.append(str(row[0]))
        except (TypeError, IndexError, KeyError):
            return None
        return _ok(chunk, "".join(parts))

    async def via_mymemory(client: httpx.AsyncClient, chunk: str) -> str | None:
        resp = await client.get(
            "https://api.mymemory.translated.net/get",
            params={"q": chunk, "langpair": "en|ar"},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        translated = (data.get("responseData") or {}).get("translatedText")
        return _ok(chunk, translated)

    async def via_libre(client: httpx.AsyncClient, chunk: str) -> str | None:
        for base in (
            "https://libretranslate.com/translate",
            "https://translate.argosopentech.com/translate",
        ):
            try:
                resp = await client.post(
                    base,
                    json={"q": chunk, "source": "en", "target": "ar", "format": "text"},
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code != 200:
                    continue
                data = resp.json()
                return _ok(chunk, data.get("translatedText"))
            except Exception:  # noqa: BLE001
                continue
        return None

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            out_parts: list[str] = []
            for chunk in chunks:
                translated = None
                for fn in (via_google, via_mymemory, via_libre):
                    try:
                        translated = await fn(client, chunk)
                    except Exception as exc:  # noqa: BLE001
                        logger.debug("Translate backend %s failed: %s", fn.__name__, exc)
                        translated = None
                    if translated:
                        break
                if not translated:
                    return None
                out_parts.append(translated)
            return " ".join(out_parts) if out_parts else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Free translate failed: %s", exc)
        return None


async def _free_translate_map(items: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in items.items():
        tr = await _free_translate_en_to_ar(value)
        if tr:
            out[key] = tr
    return out


async def _ai_translate_map(
    items: dict[str, str],
    target_lang: str,
) -> tuple[dict[str, str], bool, str]:
    """
    Translate a map of short texts to target language.
    Prefer xAI when configured; otherwise free MyMemory EN→AR fallback.
    Returns (translated_map, ai_or_service_used, note).
    """
    lang = normalize_lang(target_lang)
    if lang != "ar":
        return items, False, "Only Arabic on-demand translation is supported currently."

    # Drop empties
    work = {k: v for k, v in items.items() if v and str(v).strip()}
    if not work:
        return {}, False, t("ar", "translate.none")

    client = _client()
    out: dict[str, str] = {}
    used = False

    if client is not None:
        # Batch to keep prompt size manageable
        keys = list(work.keys())
        chunk_size = 18
        for i in range(0, len(keys), chunk_size):
            chunk_keys = keys[i : i + chunk_size]
            payload = {k: work[k][:3500] for k in chunk_keys}
            prompt = f"""Translate each value to Modern Standard Arabic for a research assistant UI.

Rules:
- Return STRICT JSON object with the SAME keys.
- Translate meaning clearly; keep academic tone.
- Keep [CITATION REQUIRED], [RESEARCHER INPUT REQUIRED], URLs, DOI, numbers, and proper names when appropriate.
- Do not invent content not present in the source.
- Output Arabic only in values (not keys).

Input JSON:
{json.dumps(payload, ensure_ascii=False)}
"""
            try:
                resp = await client.chat.completions.create(
                    model=settings.ai_model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a careful academic translator EN→AR. "
                                "Return only a JSON object mapping keys to Arabic strings."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                )
                raw = resp.choices[0].message.content or ""
                data = _extract_json(raw)
                if not data:
                    continue
                for k in chunk_keys:
                    val = data.get(k)
                    if isinstance(val, str) and val.strip():
                        out[k] = val.strip()
                used = True
            except Exception as exc:  # noqa: BLE001
                logger.warning("Batch AI translate failed: %s", exc)
                continue

        if used and out:
            return out, True, t("ar", "translate.ok")

    # Free fallback (no XAI_API_KEY) — still translates analysis text to Arabic
    free_out = await _free_translate_map(work)
    if free_out:
        return free_out, True, t("ar", "translate.ok_free")

    return {}, False, t("ar", "translate.need_ai")


async def translate_presented_analysis(
    presented: dict[str, Any],
    *,
    scope: str = "full",
    stage_key: str | None = None,
    target_language: str = "ar",
    abstract_excerpt: str | None = None,
) -> dict[str, Any]:
    """
    Translate free-text parts of a presented analysis payload into Arabic.
    Does not mutate the database. `presented` is the output of present_document_analysis.
    """
    lang = normalize_lang(target_language)
    if lang != "ar":
        return {
            "presented": presented,
            "ai_used": False,
            "message": "Target language must be Arabic (ar).",
            "translated_fields": 0,
        }

    items: dict[str, str] = {}

    def add(key: str, value: str | None) -> None:
        if value and _looks_latin_heavy(value):
            items[key] = value

    study = presented.get("study_summary") or {}
    mappings: list[dict[str, Any]] = list(presented.get("stage_mappings") or [])
    learning = presented.get("learning_report") or {}
    quality = presented.get("quality_analysis") or {}

    if scope == "stage" and stage_key:
        for m in mappings:
            if m.get("stage_key") != stage_key:
                continue
            sid = m.get("id")
            add(f"stage.{sid}.ai_summary", m.get("ai_summary"))
            add(f"stage.{sid}.extracted_excerpt", m.get("extracted_excerpt"))
            add(f"stage.{sid}.lessons_for_user", m.get("lessons_for_user"))
            add(f"stage.{sid}.writing_strategy", m.get("writing_strategy"))
            add(f"stage.{sid}.connection_to_next", m.get("connection_to_next"))
            add(f"stage.{sid}.strengths", m.get("strengths"))
            add(f"stage.{sid}.limitations", m.get("limitations"))
            add(f"stage.{sid}.original_heading", m.get("original_heading"))
            break
        # Also stage entry in learning report
        for i, st in enumerate(learning.get("stages") or []):
            if st.get("stage_key") != stage_key:
                continue
            add(f"learn.{i}.how", st.get("how_paper_approached"))
            add(f"learn.{i}.strengths", st.get("strengths"))
            add(f"learn.{i}.improvements", st.get("improvements"))
            add(f"learn.{i}.lessons", st.get("lessons"))
            break
    else:
        # Full analysis free text
        add("abstract", abstract_excerpt)
        add("study.main_ideas", study.get("main_ideas"))
        add("study.methods", study.get("methods"))
        add("study.findings", study.get("findings"))
        add("study.conclusions", study.get("conclusions"))
        for i, line in enumerate(study.get("writing_style") or []):
            add(f"study.style.{i}", line)
        for i, line in enumerate(study.get("structure_explanation") or []):
            add(f"study.structure.{i}", line)
        for i, line in enumerate(study.get("how_to_study") or []):
            add(f"study.how.{i}", line)

        for m in mappings:
            sid = m.get("id")
            add(f"stage.{sid}.ai_summary", m.get("ai_summary"))
            add(f"stage.{sid}.extracted_excerpt", m.get("extracted_excerpt"))
            add(f"stage.{sid}.lessons_for_user", m.get("lessons_for_user"))
            add(f"stage.{sid}.writing_strategy", m.get("writing_strategy"))
            add(f"stage.{sid}.connection_to_next", m.get("connection_to_next"))
            add(f"stage.{sid}.strengths", m.get("strengths"))
            add(f"stage.{sid}.limitations", m.get("limitations"))
            add(f"stage.{sid}.original_heading", m.get("original_heading"))

        for i, st in enumerate(learning.get("stages") or []):
            add(f"learn.{i}.how", st.get("how_paper_approached"))
            add(f"learn.{i}.strengths", st.get("strengths"))
            add(f"learn.{i}.improvements", st.get("improvements"))
            add(f"learn.{i}.lessons", st.get("lessons"))
            for j, q in enumerate(st.get("user_questions") or []):
                add(f"learn.{i}.q.{j}", q)
            add(f"learn.{i}.template", st.get("template_hint"))

        for i, issue in enumerate(quality.get("issues") or []):
            add(f"quality.{i}.issue", issue.get("issue"))
            add(f"quality.{i}.why", issue.get("why_it_matters"))
            add(f"quality.{i}.lesson", issue.get("lesson"))
            add(f"quality.{i}.evidence", issue.get("evidence") if isinstance(issue.get("evidence"), str) else None)

        # AI enrichment lists
        enrich = learning.get("ai_enrichment") or quality.get("ai_enrichment") or {}
        if isinstance(enrich, dict):
            for field in (
                "writing_patterns",
                "methodological_strengths",
                "methodological_weaknesses",
                "lessons_for_new_researchers",
                "alignment_observations",
                "what_not_to_copy",
            ):
                val = enrich.get(field)
                if isinstance(val, list):
                    for j, line in enumerate(val):
                        if isinstance(line, str):
                            add(f"enrich.{field}.{j}", line)
                elif isinstance(val, str):
                    add(f"enrich.{field}", val)
            if isinstance(enrich.get("integrity_reminder"), str):
                add("enrich.integrity_reminder", enrich["integrity_reminder"])

        for i, w in enumerate(presented.get("analysis_warnings") or []):
            add(f"warn.{i}", w)

    translated, ai_used, note = await _ai_translate_map(items, "ar")

    # Apply translations back onto a deep copy
    import copy

    result = copy.deepcopy(presented)

    def get_t(key: str, original: str | None) -> str | None:
        if key in translated:
            return translated[key]
        return original

    study2 = result.get("study_summary") or {}
    if study2:
        study2["main_ideas"] = get_t("study.main_ideas", study2.get("main_ideas"))
        study2["methods"] = get_t("study.methods", study2.get("methods"))
        study2["findings"] = get_t("study.findings", study2.get("findings"))
        study2["conclusions"] = get_t("study.conclusions", study2.get("conclusions"))
        if study2.get("writing_style"):
            study2["writing_style"] = [
                get_t(f"study.style.{i}", line) or line
                for i, line in enumerate(study2["writing_style"])
            ]
        if study2.get("structure_explanation"):
            study2["structure_explanation"] = [
                get_t(f"study.structure.{i}", line) or line
                for i, line in enumerate(study2["structure_explanation"])
            ]
        if study2.get("how_to_study"):
            study2["how_to_study"] = [
                get_t(f"study.how.{i}", line) or line
                for i, line in enumerate(study2["how_to_study"])
            ]
        result["study_summary"] = study2

    for m in result.get("stage_mappings") or []:
        sid = m.get("id")
        m["ai_summary"] = get_t(f"stage.{sid}.ai_summary", m.get("ai_summary"))
        m["extracted_excerpt"] = get_t(
            f"stage.{sid}.extracted_excerpt", m.get("extracted_excerpt")
        )
        m["lessons_for_user"] = get_t(
            f"stage.{sid}.lessons_for_user", m.get("lessons_for_user")
        )
        m["writing_strategy"] = get_t(
            f"stage.{sid}.writing_strategy", m.get("writing_strategy")
        )
        m["connection_to_next"] = get_t(
            f"stage.{sid}.connection_to_next", m.get("connection_to_next")
        )
        m["strengths"] = get_t(f"stage.{sid}.strengths", m.get("strengths"))
        m["limitations"] = get_t(f"stage.{sid}.limitations", m.get("limitations"))
        m["original_heading"] = get_t(
            f"stage.{sid}.original_heading", m.get("original_heading")
        )

    learn2 = result.get("learning_report") or {}
    for i, st in enumerate(learn2.get("stages") or []):
        st["how_paper_approached"] = get_t(f"learn.{i}.how", st.get("how_paper_approached"))
        st["strengths"] = get_t(f"learn.{i}.strengths", st.get("strengths"))
        st["improvements"] = get_t(f"learn.{i}.improvements", st.get("improvements"))
        st["lessons"] = get_t(f"learn.{i}.lessons", st.get("lessons"))
        st["template_hint"] = get_t(f"learn.{i}.template", st.get("template_hint"))
        if st.get("user_questions"):
            st["user_questions"] = [
                get_t(f"learn.{i}.q.{j}", q) or q
                for j, q in enumerate(st["user_questions"])
            ]
    result["learning_report"] = learn2

    qual2 = result.get("quality_analysis") or {}
    for i, issue in enumerate(qual2.get("issues") or []):
        issue["issue"] = get_t(f"quality.{i}.issue", issue.get("issue"))
        issue["why_it_matters"] = get_t(f"quality.{i}.why", issue.get("why_it_matters"))
        issue["lesson"] = get_t(f"quality.{i}.lesson", issue.get("lesson"))
        if isinstance(issue.get("evidence"), str):
            issue["evidence"] = get_t(f"quality.{i}.evidence", issue.get("evidence"))
    result["quality_analysis"] = qual2

    warns = list(result.get("analysis_warnings") or [])
    result["analysis_warnings"] = [
        get_t(f"warn.{i}", w) or w for i, w in enumerate(warns)
    ]

    # Enrichment nested under learning or quality
    for host_key in ("learning_report", "quality_analysis"):
        host = result.get(host_key) or {}
        enrich = host.get("ai_enrichment")
        if not isinstance(enrich, dict):
            continue
        for field in (
            "writing_patterns",
            "methodological_strengths",
            "methodological_weaknesses",
            "lessons_for_new_researchers",
            "alignment_observations",
            "what_not_to_copy",
        ):
            val = enrich.get(field)
            if isinstance(val, list):
                enrich[field] = [
                    get_t(f"enrich.{field}.{j}", line) or line
                    for j, line in enumerate(val)
                    if isinstance(line, str)
                ]
            elif isinstance(val, str):
                enrich[field] = get_t(f"enrich.{field}", val)
        if isinstance(enrich.get("integrity_reminder"), str):
            enrich["integrity_reminder"] = get_t(
                "enrich.integrity_reminder", enrich["integrity_reminder"]
            )
        host["ai_enrichment"] = enrich
        result[host_key] = host

    abstract_tr = get_t("abstract", abstract_excerpt)

    return {
        "presented": result,
        "abstract_excerpt": abstract_tr,
        "ai_used": ai_used,
        "message": note if items else "Already in Arabic or nothing to translate.",
        "translated_fields": len(translated),
        "candidate_fields": len(items),
    }


def _stage_questions(
    stage_key: str, profile: dict[str, Any], lang: str
) -> list[dict[str, str]]:
    common = [
        {
            "id": "context",
            "prompt": t(lang, "write.q.context"),
            "hint": profile.get("study_context") or "",
        },
        {
            "id": "population",
            "prompt": t(lang, "write.q.population"),
            "hint": profile.get("population") or "",
        },
    ]
    specific: dict[str, list[dict[str, str]]] = {
        "problem_purpose": [
            {"id": "problem", "prompt": t(lang, "write.q.problem"), "hint": profile.get("research_problem") or ""},
            {"id": "gap", "prompt": t(lang, "write.q.gap"), "hint": profile.get("research_gap") or ""},
            {"id": "aim", "prompt": t(lang, "write.q.aim"), "hint": profile.get("overall_aim") or ""},
            {"id": "significance", "prompt": t(lang, "write.q.significance"), "hint": ""},
        ],
        "questions_objectives": [
            {"id": "main_question", "prompt": t(lang, "write.q.main_question"), "hint": ""},
            {"id": "objectives", "prompt": t(lang, "write.q.objectives"), "hint": ""},
        ],
        "methodology": [
            {"id": "design", "prompt": t(lang, "write.q.design"), "hint": ""},
            {"id": "data", "prompt": t(lang, "write.q.data"), "hint": ""},
            {"id": "limits", "prompt": t(lang, "write.q.limits_design"), "hint": ""},
        ],
        "literature_synthesis": [
            {"id": "themes", "prompt": t(lang, "write.q.themes"), "hint": ""},
            {"id": "gap_statement", "prompt": t(lang, "write.q.gap_statement"), "hint": profile.get("research_gap") or ""},
        ],
        "population_sampling": [
            {"id": "inclusion", "prompt": t(lang, "write.q.inclusion"), "hint": ""},
            {"id": "sampling", "prompt": t(lang, "write.q.sampling"), "hint": ""},
            {"id": "size_basis", "prompt": t(lang, "write.q.size_basis"), "hint": ""},
        ],
        "discussion": [
            {"id": "findings_link", "prompt": t(lang, "write.q.findings_link"), "hint": ""},
            {"id": "prior_work", "prompt": t(lang, "write.q.prior_work"), "hint": ""},
            {"id": "limits", "prompt": t(lang, "write.q.limits"), "hint": ""},
        ],
    }
    return common + specific.get(
        stage_key,
        [
            {
                "id": "main_points",
                "prompt": t(lang, "write.q.main_points", stage=stage_key.replace("_", " ")),
                "hint": "",
            },
            {"id": "evidence", "prompt": t(lang, "write.q.evidence"), "hint": ""},
        ],
    )


def _stage_outline(stage_key: str, label: str, lang: str) -> list[str]:
    outlines: dict[str, list[str]] = {
        "problem_purpose": [
            t(lang, "write.outline.pp1"),
            t(lang, "write.outline.pp2"),
            t(lang, "write.outline.pp3"),
            t(lang, "write.outline.pp4"),
            t(lang, "write.outline.pp5"),
        ],
        "questions_objectives": [
            t(lang, "write.outline.qo1"),
            t(lang, "write.outline.qo2"),
            t(lang, "write.outline.qo3"),
            t(lang, "write.outline.qo4"),
        ],
        "methodology": [
            t(lang, "write.outline.m1"),
            t(lang, "write.outline.m2"),
            t(lang, "write.outline.m3"),
            t(lang, "write.outline.m4"),
        ],
    }
    return outlines.get(
        stage_key,
        [
            t(lang, "write.outline.default1", label=label),
            t(lang, "write.outline.default2"),
            t(lang, "write.outline.default3"),
            t(lang, "write.outline.default4"),
            t(lang, "write.outline.default5"),
        ],
    )
