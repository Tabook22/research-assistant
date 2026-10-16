"""
Previous Research Library — extract, classify, map 18 stages, learning reports.

Integrity rules:
- Never auto-insert extracted content into the user's project.
- Distinguish exact source text vs AI summary vs interpretation.
- Teach structure; do not encourage plagiarism or close imitation.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.models.library import (
    ComparisonItem,
    DocumentProcessingJob,
    DocumentSection,
    DocumentStageMapping,
    ExtractedResearchElement,
    PaperComparison,
    SourceDocument,
)
from app.i18n.lang import normalize_lang, stage_purpose, t
from app.models.mixins import RESEARCH_STAGES
from app.models.project import ResearchProject
from app.services.document_service import extract_text

logger = logging.getLogger(__name__)
settings = get_settings()

ALLOWED_EXT = {".pdf", ".docx", ".txt", ".rtf", ".csv"}

# Semantic heading → stage keys
HEADING_STAGE_PATTERNS: list[tuple[re.Pattern[str], str, float]] = [
    (re.compile(r"\b(abstract|summary)\b", re.I), "abstract_title", 0.9),
    (re.compile(r"\b(title|keywords?)\b", re.I), "abstract_title", 0.5),
    (re.compile(r"\b(introduction|background|study context|context of the study)\b", re.I), "problem_purpose", 0.75),
    (re.compile(r"\b(problem statement|statement of the problem|research problem)\b", re.I), "problem_purpose", 0.95),
    (re.compile(r"\b(purpose|aim|study purpose|overall aim)\b", re.I), "problem_purpose", 0.9),
    (re.compile(r"\b(significance|importance|justification)\b", re.I), "problem_purpose", 0.8),
    (re.compile(r"\b(literature review|related work|previous studies|theoretical framework|conceptual framework)\b", re.I), "literature_synthesis", 0.9),
    (re.compile(r"\b(research gap|gap in the literature|knowledge gap)\b", re.I), "literature_synthesis", 0.95),
    (re.compile(r"\b(research questions?|study questions?)\b", re.I), "questions_objectives", 0.95),
    (re.compile(r"\b(objectives?|specific objectives?|study goals?)\b", re.I), "questions_objectives", 0.9),
    (re.compile(r"\b(hypothes[ei]s|study predictions?)\b", re.I), "hypotheses", 0.95),
    (re.compile(r"\b(variables?|constructs?|operational definitions?)\b", re.I), "constructs_variables", 0.85),
    (re.compile(r"\b(methodology|methods|materials and methods|research design|study design)\b", re.I), "methodology", 0.95),
    (re.compile(r"\b(participants?|sample|sampling|study population|inclusion|exclusion)\b", re.I), "population_sampling", 0.9),
    (re.compile(r"\b(instruments?|measures?|questionnaire|data[- ]collection tools?|data collection)\b", re.I), "instruments", 0.9),
    (re.compile(r"\b(validity|reliability|trustworthiness|rigor)\b", re.I), "validity_quality", 0.9),
    (re.compile(r"\b(ethics|ethical|informed consent|irb|institutional review)\b", re.I), "ethics", 0.9),
    (re.compile(r"\b(data analysis|statistical analysis|analysis plan|analytical strategy)\b", re.I), "analysis_plan", 0.9),
    (re.compile(r"\b(results|findings)\b", re.I), "results", 0.9),
    (re.compile(r"\b(discussion|interpretation)\b", re.I), "discussion", 0.9),
    (re.compile(r"\b(limitations?)\b", re.I), "discussion", 0.7),
    (re.compile(r"\b(conclusion|concluding remarks|recommendations?|implications?)\b", re.I), "conclusion", 0.9),
    (re.compile(r"\b(references|bibliography|works cited)\b", re.I), "references", 0.95),
]

NOT_APPLICABLE_HINTS: dict[str, list[str]] = {
    "hypotheses": ["qualitative", "phenomenology", "grounded theory", "ethnography", "scoping", "systematic review", "conceptual"],
    "instruments": ["systematic review", "scoping", "meta-analysis", "conceptual", "theoretical"],
    "population_sampling": ["systematic review", "scoping", "meta-analysis", "conceptual"],
    "results": ["research proposal", "research protocol"],
}


async def save_and_process(
    db: Session,
    project: ResearchProject,
    user_id: int,
    file: UploadFile,
    language: str | None = None,
) -> SourceDocument:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Allowed: {', '.join(sorted(ALLOWED_EXT))}",
        )
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File too large")

    root = Path(settings.upload_dir) / "library" / str(project.id)
    root.mkdir(parents=True, exist_ok=True)
    safe = f"{uuid.uuid4().hex[:12]}_{re.sub(r'[^\w.\-() ]+', '_', Path(file.filename).name)[:180]}"
    path = root / safe
    path.write_bytes(content)

    doc = SourceDocument(
        project_id=project.id,
        uploaded_by_id=user_id,
        original_filename=file.filename,
        safe_filename=safe,
        file_type=ext.lstrip("."),
        file_size=len(content),
        storage_path=str(path),
        processing_status="waiting_for_processing",
        extraction_status="pending",
        is_reference_only=True,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    job = DocumentProcessingJob(
        source_document_id=doc.id, status="running", step="extracting_text"
    )
    db.add(job)
    db.commit()

    try:
        analysis_lang = normalize_lang(language or project.writing_language or "en")
        process_source_document(db, doc, language=analysis_lang)
        # Optional AI enrichment (best-effort)
        try:
            from app.services.library_ai_service import enrich_document_analysis

            rows = (
                db.query(DocumentStageMapping)
                .filter(DocumentStageMapping.source_document_id == doc.id)
                .all()
            )
            enrichment = await enrich_document_analysis(doc, rows, language=analysis_lang)
            if enrichment.get("ai_enriched"):
                report = {}
                if doc.learning_report_json:
                    try:
                        report = json.loads(doc.learning_report_json)
                    except json.JSONDecodeError:
                        report = {}
                report["ai_enrichment"] = enrichment
                if enrichment.get("writing_patterns"):
                    report["writing_patterns"] = {
                        **(report.get("writing_patterns") or {}),
                        "ai_patterns": enrichment["writing_patterns"],
                    }
                doc.learning_report_json = json.dumps(report, ensure_ascii=False)
                quality = {}
                if doc.quality_analysis_json:
                    try:
                        quality = json.loads(doc.quality_analysis_json)
                    except json.JSONDecodeError:
                        quality = {}
                quality["ai_enrichment"] = {
                    "strengths": enrichment.get("methodological_strengths"),
                    "weaknesses": enrichment.get("methodological_weaknesses"),
                    "what_not_to_copy": enrichment.get("what_not_to_copy"),
                }
                doc.quality_analysis_json = json.dumps(quality, ensure_ascii=False)
                # Improve per-stage lessons lightly from AI lessons list
                ai_lessons = enrichment.get("lessons_for_new_researchers") or []
                if ai_lessons and rows:
                    for i, row in enumerate(rows):
                        if row.status in ("detected", "partially_detected") and i < len(ai_lessons):
                            extra = str(ai_lessons[i % len(ai_lessons)])
                            if row.lessons_for_user and extra not in row.lessons_for_user:
                                row.lessons_for_user = f"{row.lessons_for_user} | AI note: {extra}"
                db.commit()
                job.message = "Analysis finished with AI learning enrichment. Researcher review recommended."
            else:
                job.message = (
                    "Analysis finished (heuristic). "
                    f"AI enrichment skipped: {enrichment.get('reason', 'n/a')}. "
                    "Researcher review recommended."
                )
        except Exception as enrich_exc:  # noqa: BLE001
            logger.warning("Enrichment step failed: %s", enrich_exc)
            job.message = "Analysis finished. Researcher review recommended."

        job.status = "completed"
        job.step = "completed"
    except Exception as exc:  # noqa: BLE001
        logger.exception("Library processing failed")
        doc.processing_status = "processing_failed"
        job.status = "failed"
        job.error = f"{exc.__class__.__name__}: {exc}"
        db.commit()
        raise HTTPException(status_code=500, detail="Document processing failed") from exc

    db.commit()
    db.refresh(doc)
    return get_source_document(db, doc.id)  # type: ignore[return-value]


def process_source_document(
    db: Session, doc: SourceDocument, language: str | None = None
) -> None:
    warnings: list[str] = []
    project = db.get(ResearchProject, doc.project_id)
    # Prefer explicit UI language so analysis text matches the interface language.
    lang = normalize_lang(
        language or (project.writing_language if project else None) or "en"
    )
    doc.processing_status = "extracting_text"
    db.commit()

    path = Path(doc.storage_path)
    ext = f".{doc.file_type}"
    text = ""
    try:
        if ext == ".rtf":
            text = _extract_rtf(path)
        else:
            text = extract_text(path, ext)
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"Extraction error: {exc.__class__.__name__}")
        text = ""

    # OCR for image-like / empty PDFs when optional stack is available
    if doc.file_type == "pdf" and len(text.strip()) < 80:
        doc.processing_status = "applying_ocr"
        db.commit()
        from app.services.ocr_service import extract_text_with_ocr, ocr_available

        if ocr_available():
            ocr_text, ocr_meta = extract_text_with_ocr(path)
            doc.ocr_status = ocr_meta.get("status") or "completed"
            if ocr_meta.get("warning"):
                warnings.append(str(ocr_meta["warning"]))
            if ocr_text.strip():
                text = ocr_text
                warnings.append(t(lang, "lib.ocr_quality"))
            else:
                warnings.append(t(lang, "lib.ocr_empty"))
        else:
            doc.ocr_status = "needed_but_unavailable"
            warnings.append(t(lang, "lib.ocr_needed"))
            if not text.strip():
                doc.processing_status = "completed_with_warnings"
                doc.extraction_status = "failed"
                doc.analysis_warnings = json.dumps(warnings)
                _ensure_stage_rows(db, doc, {}, {}, lang=lang)
                db.commit()
                return

    if not text.strip():
        doc.extraction_status = "failed"
        doc.processing_status = "processing_failed"
        warnings.append(t(lang, "lib.no_text"))
        doc.analysis_warnings = json.dumps(warnings, ensure_ascii=False)
        db.commit()
        return

    doc.extraction_status = "extracted"
    doc.detected_language = _detect_language(text)
    doc.page_count = text.count("\f") + 1 if "\f" in text else None

    doc.processing_status = "detecting_sections"
    db.commit()

    # Clear prior analysis on reprocess
    db.query(DocumentSection).filter(DocumentSection.source_document_id == doc.id).delete()
    db.query(DocumentStageMapping).filter(DocumentStageMapping.source_document_id == doc.id).delete()
    db.query(ExtractedResearchElement).filter(
        ExtractedResearchElement.source_document_id == doc.id
    ).delete()
    db.commit()

    sections = _split_sections(text)
    for i, sec in enumerate(sections):
        db.add(
            DocumentSection(
                source_document_id=doc.id,
                heading=sec["heading"],
                normalized_heading=sec.get("normalized"),
                content=sec["content"],
                summary=_short_summary(sec["content"]),
                sort_order=i,
                content_kind="exact",
                confidence=sec.get("confidence", 0.6),
            )
        )
    db.commit()

    doc.processing_status = "analyzing_research_structure"
    db.commit()

    classification = _classify_document(text, sections, doc.original_filename)
    doc.document_type = classification["document_type"]
    doc.document_type_confidence = classification["confidence"]
    doc.document_type_evidence = classification["evidence"]
    doc.document_type_confirmed = False
    doc.academic_level = classification.get("academic_level")
    doc.academic_level_confidence = classification.get("academic_level_confidence")
    doc.discipline = classification.get("discipline")
    doc.research_design = classification.get("research_design")
    doc.methodology_paradigm = classification.get("methodology_paradigm")
    doc.title_detected = classification.get("title")
    doc.authors_detected = classification.get("authors")
    doc.year_detected = classification.get("year")
    doc.abstract_excerpt = classification.get("abstract")

    stage_hits = _map_stages(text, sections, classification, lang=lang)
    _ensure_stage_rows(db, doc, stage_hits, classification, lang=lang)

    elements = _extract_elements(text, sections, classification)
    for el in elements:
        db.add(
            ExtractedResearchElement(
                source_document_id=doc.id,
                element_type=el["type"],
                content_role=el.get("role", "exact"),
                value_text=el["value"],
                page_or_section=el.get("location"),
                section_heading=el.get("heading"),
                confidence=el.get("confidence"),
                verification_status="unverified",
                reuse_category=el.get("reuse_category", "background_evidence"),
            )
        )

    learning = _build_learning_report(doc, stage_hits, classification, warnings, lang=lang)
    study = _build_study_summary(text, sections, classification, stage_hits, lang=lang)
    learning["study_summary"] = study
    quality = _build_quality_analysis(stage_hits, classification, text, lang=lang)
    structure_map = _build_structure_map(stage_hits, sections, lang=lang)

    doc.learning_report_json = json.dumps(learning, ensure_ascii=False)
    doc.quality_analysis_json = json.dumps(quality, ensure_ascii=False)
    doc.structure_map_json = json.dumps(structure_map, ensure_ascii=False)

    if classification["confidence"] < 0.65:
        warnings.append(t(lang, "lib.uncertain_type"))
    if any(h.get("confidence", 1) < 0.5 for h in stage_hits.values() if h.get("status") == "partially_detected"):
        warnings.append(t(lang, "lib.stages_review"))

    doc.analysis_warnings = json.dumps(warnings, ensure_ascii=False)
    doc.processing_status = (
        "completed_with_warnings" if warnings else "completed"
    )
    doc.verification_status = "awaiting_researcher_review"
    db.commit()


async def reprocess(
    db: Session, doc: SourceDocument, language: str | None = None
) -> SourceDocument:
    project = db.get(ResearchProject, doc.project_id)
    analysis_lang = normalize_lang(
        language or (project.writing_language if project else None) or "en"
    )
    process_source_document(db, doc, language=analysis_lang)
    try:
        from app.services.library_ai_service import enrich_document_analysis

        rows = (
            db.query(DocumentStageMapping)
            .filter(DocumentStageMapping.source_document_id == doc.id)
            .all()
        )
        enrichment = await enrich_document_analysis(doc, rows, language=analysis_lang)
        if enrichment.get("ai_enriched"):
            report = {}
            if doc.learning_report_json:
                try:
                    report = json.loads(doc.learning_report_json)
                except json.JSONDecodeError:
                    report = {}
            report["ai_enrichment"] = enrichment
            doc.learning_report_json = json.dumps(report, ensure_ascii=False)
            db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Reprocess enrichment failed: %s", exc)
    return get_source_document(db, doc.id)  # type: ignore[return-value]


def get_source_document(db: Session, doc_id: int) -> SourceDocument | None:
    return (
        db.query(SourceDocument)
        .options(
            joinedload(SourceDocument.sections),
            joinedload(SourceDocument.stage_mappings),
            joinedload(SourceDocument.elements),
        )
        .filter(SourceDocument.id == doc_id)
        .first()
    )


def list_library(db: Session, project_id: int) -> list[SourceDocument]:
    return (
        db.query(SourceDocument)
        .filter(SourceDocument.project_id == project_id)
        .order_by(SourceDocument.id.desc())
        .all()
    )


def confirm_classification(
    db: Session,
    doc: SourceDocument,
    document_type: str | None = None,
    academic_level: str | None = None,
    discipline: str | None = None,
    research_design: str | None = None,
) -> SourceDocument:
    if document_type:
        doc.document_type = document_type
        doc.document_type_confirmed = True
        doc.document_type_confidence = 1.0
    if academic_level:
        doc.academic_level = academic_level
        doc.academic_level_confidence = 1.0
    if discipline:
        doc.discipline = discipline
    if research_design:
        doc.research_design = research_design
    doc.verification_status = "researcher_confirmed"
    db.commit()
    return get_source_document(db, doc.id)  # type: ignore[return-value]


def verify_stage(
    db: Session,
    mapping: DocumentStageMapping,
    status: str | None = None,
    correction: str | None = None,
) -> DocumentStageMapping:
    mapping.researcher_verified = True
    if status:
        mapping.status = status
    if correction is not None:
        mapping.researcher_correction = correction
    db.commit()
    db.refresh(mapping)
    return mapping


def compare_documents(
    db: Session,
    project: ResearchProject,
    document_ids: list[int],
    title: str = "Paper comparison",
    language: str | None = None,
) -> PaperComparison:
    lang = normalize_lang(language or project.writing_language or "en")
    if len(document_ids) < 2:
        raise HTTPException(status_code=400, detail="Select at least two documents to compare")
    docs = (
        db.query(SourceDocument)
        .options(joinedload(SourceDocument.stage_mappings), joinedload(SourceDocument.elements))
        .filter(
            SourceDocument.project_id == project.id,
            SourceDocument.id.in_(document_ids),
        )
        .all()
    )
    if len(docs) < 2:
        raise HTTPException(status_code=404, detail="Documents not found for this project")

    element_keys = [
        "research_problem",
        "research_gap",
        "research_questions",
        "hypotheses",
        "methodology",
        "sampling",
        "instruments",
        "analysis",
        "results",
        "discussion",
    ]
    stage_for_element = {
        "research_problem": "problem_purpose",
        "research_gap": "literature_synthesis",
        "research_questions": "questions_objectives",
        "hypotheses": "hypotheses",
        "methodology": "methodology",
        "sampling": "population_sampling",
        "instruments": "instruments",
        "analysis": "analysis_plan",
        "results": "results",
        "discussion": "discussion",
    }

    comparison = PaperComparison(
        project_id=project.id,
        title=title,
        document_ids_json=json.dumps(document_ids),
    )
    db.add(comparison)
    db.flush()

    for key in element_keys:
        values: dict[str, str] = {}
        for d in docs:
            stage_key = stage_for_element[key]
            m = next((x for x in d.stage_mappings if x.stage_key == stage_key), None)
            if m and m.status in ("detected", "partially_detected"):
                values[str(d.id)] = (m.ai_summary or m.extracted_excerpt or m.status)[:500]
            else:
                values[str(d.id)] = m.status if m else "not_detected"
        lessons = t(lang, "lib.compare_lesson", element=key)
        db.add(
            ComparisonItem(
                comparison_id=comparison.id,
                element_key=key,
                values_json=json.dumps(values, ensure_ascii=False),
                lessons=lessons,
            )
        )

    summary = {
        "document_count": len(docs),
        "types": [d.document_type for d in docs],
        "designs": [d.research_design for d in docs],
        "common_patterns": _comparison_patterns(docs, lang),
        "integrity_note": t(lang, "lib.compare_integrity"),
    }
    comparison.summary_json = json.dumps(summary, ensure_ascii=False)
    comparison.lessons_json = json.dumps(
        {
            "lessons": summary["common_patterns"],
            "warning": t(lang, "lib.compare_warning"),
        },
        ensure_ascii=False,
    )
    db.commit()
    db.refresh(comparison)
    return (
        db.query(PaperComparison)
        .options(joinedload(PaperComparison.items))
        .filter(PaperComparison.id == comparison.id)
        .first()
    )  # type: ignore[return-value]


# ---- internals ----

def _extract_rtf(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    # crude RTF strip
    text = re.sub(r"\\[a-z]+(-?\d+)?[ ]?", " ", raw)
    text = re.sub(r"[{}]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _detect_language(text: str) -> str:
    arabic = len(re.findall(r"[\u0600-\u06FF]", text[:5000]))
    latin = len(re.findall(r"[A-Za-z]", text[:5000]))
    if arabic > latin * 0.3 and arabic > 20:
        return "ar"
    return "en"


def _split_sections(text: str) -> list[dict[str, Any]]:
    lines = text.replace("\r\n", "\n").split("\n")
    sections: list[dict[str, Any]] = []
    current_heading = "Preamble / front matter"
    current_lines: list[str] = []

    heading_re = re.compile(
        r"^(?:(?:chapter|section|part)\s+\d+[.:)]\s*)?"
        r"([A-Z][A-Za-z0-9 ,/\-&]{2,80}|[A-Z][A-Z0-9 ,/\-&]{2,80})$"
    )
    numbered_re = re.compile(r"^\d+(\.\d+)*\.?\s+[A-Z].{2,80}$")

    def flush() -> None:
        body = "\n".join(current_lines).strip()
        if body or current_heading:
            sections.append(
                {
                    "heading": current_heading,
                    "normalized": current_heading.strip().lower(),
                    "content": body[:20000],
                    "confidence": 0.7,
                }
            )

    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_lines.append("")
            continue
        is_heading = False
        if len(stripped) < 100 and (heading_re.match(stripped) or numbered_re.match(stripped)):
            # Avoid treating every short line as heading
            if stripped.isupper() or numbered_re.match(stripped) or stripped.istitle():
                is_heading = True
        if is_heading and len(current_lines) > 2:
            flush()
            current_heading = stripped
            current_lines = []
        else:
            current_lines.append(stripped)
    flush()

    if len(sections) <= 1:
        # Fallback chunk by length
        chunk = 3500
        return [
            {
                "heading": f"Segment {i + 1}",
                "normalized": f"segment_{i + 1}",
                "content": text[i : i + chunk],
                "confidence": 0.4,
            }
            for i in range(0, min(len(text), chunk * 8), chunk)
        ]
    return sections


def _short_summary(content: str, max_len: int = 400) -> str:
    clean = re.sub(r"\s+", " ", content).strip()
    if len(clean) <= max_len:
        return clean
    return clean[: max_len - 1] + "…"


def _classify_document(
    text: str, sections: list[dict[str, Any]], filename: str
) -> dict[str, Any]:
    lower = text[:15000].lower()
    fname = filename.lower()
    scores: dict[str, float] = {}
    evidence: list[str] = []

    def bump(key: str, amt: float, why: str) -> None:
        scores[key] = scores.get(key, 0) + amt
        evidence.append(f"{key}: {why} (+{amt})")

    if "dissertation" in lower or "dissertation" in fname:
        bump("doctoral_dissertation", 2.0, "keyword dissertation")
    if "thesis" in lower or "thesis" in fname:
        bump("masters_thesis", 1.5, "keyword thesis")
    if "bachelor" in lower or "undergraduate project" in lower:
        bump("bachelors_research_project", 1.8, "bachelor/undergraduate")
    if re.search(r"\bproposal\b", lower) or "proposal" in fname:
        bump("research_proposal", 1.6, "proposal language")
    if "protocol" in lower:
        bump("research_protocol", 1.5, "protocol")
    if "systematic review" in lower or "prisma" in lower:
        bump("systematic_review", 2.2, "systematic review/PRISMA")
    if "scoping review" in lower:
        bump("scoping_review", 2.0, "scoping review")
    if "meta-analysis" in lower or "meta analysis" in lower:
        bump("meta_analysis", 2.0, "meta-analysis")
    if re.search(r"\b(journal|doi:|volume\s+\d+|pp\.\s*\d)", lower):
        bump("journal_article", 1.2, "journal markers")
    if "conference" in lower or "proceedings" in lower:
        bump("conference_paper", 1.3, "conference")
    if "case study" in lower:
        bump("case_study", 1.4, "case study")
    if re.search(r"\bwill be (collected|conducted|examined)\b", lower):
        bump("research_proposal", 0.8, "future-tense methods language")
    if re.search(r"\b(participants completed|results showed|the analysis revealed)\b", lower):
        bump("journal_article", 0.6, "completed research language")

    if not scores:
        bump("journal_article", 0.4, "default fallback — low confidence")

    best = max(scores.items(), key=lambda x: x[1])
    total = sum(scores.values()) or 1
    conf = min(0.95, best[1] / (total * 0.6 + 0.5))

    paradigm = "quantitative"
    if re.search(r"\b(thematic analysis|phenomenolog|interview guide|grounded theory)\b", lower):
        paradigm = "qualitative"
    if re.search(r"\bmixed[- ]methods?\b", lower):
        paradigm = "mixed"

    design = None
    for label, pat in [
        ("experimental", r"\bexperimental\b"),
        ("quasi-experimental", r"\bquasi[- ]experimental\b"),
        ("cross-sectional", r"\bcross[- ]sectional\b"),
        ("longitudinal", r"\blongitudinal\b"),
        ("survey", r"\bsurvey\b"),
        ("systematic review", r"\bsystematic review\b"),
    ]:
        if re.search(pat, lower):
            design = label
            break

    level = None
    level_conf = None
    if best[0] == "doctoral_dissertation":
        level, level_conf = "doctoral", 0.8
    elif best[0] == "masters_thesis":
        level, level_conf = "masters", 0.75
    elif best[0] == "bachelors_research_project":
        level, level_conf = "bachelors", 0.7
    elif "undergraduate" in lower:
        level, level_conf = "bachelors", 0.55

    abstract = None
    for sec in sections:
        if re.search(r"abstract", sec["heading"], re.I):
            abstract = _short_summary(sec["content"], 800)
            break

    title = None
    for line in text.split("\n")[:30]:
        s = line.strip()
        if 15 < len(s) < 200 and not re.match(r"^(abstract|introduction|chapter)", s, re.I):
            title = s
            break

    year = None
    ym = re.search(r"\b(19|20)\d{2}\b", text[:3000])
    if ym:
        year = int(ym.group(0))

    return {
        "document_type": best[0],
        "confidence": round(conf, 2),
        "evidence": "; ".join(evidence[:12]),
        "academic_level": level,
        "academic_level_confidence": level_conf,
        "discipline": None,
        "research_design": design,
        "methodology_paradigm": paradigm,
        "title": title,
        "authors": None,
        "year": year,
        "abstract": abstract,
        "all_scores": scores,
    }


def _map_stages(
    text: str,
    sections: list[dict[str, Any]],
    classification: dict[str, Any],
    lang: str = "en",
) -> dict[str, dict[str, Any]]:
    hits: dict[str, dict[str, Any]] = {}
    lower_full = text.lower()
    dtype = (classification.get("document_type") or "").lower()
    paradigm = (classification.get("methodology_paradigm") or "").lower()

    for sec in sections:
        heading = sec["heading"]
        body = sec["content"]
        for pattern, stage_key, base_conf in HEADING_STAGE_PATTERNS:
            if pattern.search(heading) or pattern.search(body[:400]):
                conf = base_conf if pattern.search(heading) else base_conf * 0.7
                existing = hits.get(stage_key)
                excerpt = body[:1200]
                if not existing or conf > (existing.get("confidence") or 0):
                    hits[stage_key] = {
                        "status": "detected" if conf >= 0.75 else "partially_detected",
                        "original_heading": heading,
                        "extracted_excerpt": excerpt,
                        "ai_summary": _short_summary(body, 500),
                        "confidence": round(conf, 2),
                        "completeness": "medium" if len(body) > 400 else "low",
                        "methodological_clarity": "medium",
                    }

    # Keyword presence for stages not found by headings
    keyword_stages = {
        "ethics": [r"\binformed consent\b", r"\bethical approval\b", r"\birb\b"],
        "references": [r"\breferences\b", r"\bbibliography\b"],
        "hypotheses": [r"\bh0\b", r"\bnull hypothesis\b", r"\bwe hypothesize\b"],
        "literature_search": [r"\bdatabase(s)? searched\b", r"\bsearch strategy\b", r"\bpubmed\b"],
    }
    for stage_key, pats in keyword_stages.items():
        if stage_key in hits:
            continue
        if any(re.search(p, lower_full) for p in pats):
            hits[stage_key] = {
                "status": "partially_detected",
                "original_heading": None,
                "extracted_excerpt": None,
                "ai_summary": t(lang, "lib.partial_keywords"),
                "confidence": 0.45,
                "completeness": "low",
                "methodological_clarity": "unclear",
            }

    # Mark not applicable
    for stage_key, hints in NOT_APPLICABLE_HINTS.items():
        if stage_key in hits:
            continue
        if any(h in dtype or h in paradigm for h in hints):
            hits[stage_key] = {
                "status": "not_applicable",
                "original_heading": None,
                "extracted_excerpt": None,
                "ai_summary": t(lang, "lib.na_summary", dtype=dtype or paradigm),
                "confidence": 0.7,
                "completeness": "n/a",
                "methodological_clarity": "n/a",
            }

    return hits


def _ensure_stage_rows(
    db: Session,
    doc: SourceDocument,
    hits: dict[str, dict[str, Any]],
    classification: dict[str, Any],
    lang: str = "en",
) -> None:
    for stage in RESEARCH_STAGES:
        key = stage["key"]
        hit = hits.get(key)
        if hit:
            status = hit["status"]
            lessons = _lessons_for_stage(key, hit, classification, lang)
            db.add(
                DocumentStageMapping(
                    source_document_id=doc.id,
                    stage_key=key,
                    status=status,
                    original_heading=hit.get("original_heading"),
                    page_or_section=hit.get("original_heading"),
                    extracted_excerpt=hit.get("extracted_excerpt"),
                    ai_summary=hit.get("ai_summary"),
                    completeness=hit.get("completeness"),
                    methodological_clarity=hit.get("methodological_clarity"),
                    strengths=hit.get("strengths")
                    or (t(lang, "lib.strength_clear") if status == "detected" else None),
                    limitations=hit.get("limitations")
                    or (
                        t(lang, "lib.limit_thin")
                        if status == "partially_detected"
                        else None
                    ),
                    lessons_for_user=lessons["lessons"],
                    connection_to_next=lessons["connection"],
                    writing_strategy=lessons["writing"],
                    confidence=hit.get("confidence"),
                )
            )
        else:
            purpose = stage_purpose(lang, key)
            db.add(
                DocumentStageMapping(
                    source_document_id=doc.id,
                    stage_key=key,
                    status="not_detected",
                    ai_summary=t(lang, "lib.not_detected_summary"),
                    completeness="n/a",
                    confidence=0.2,
                    lessons_for_user=t(lang, "lib.not_detected_lesson", purpose=purpose),
                )
            )
    db.commit()


def _status_label(lang: str, status: str | None) -> str:
    key = {
        "detected": "lib.status_detected",
        "partially_detected": "lib.status_partial",
        "not_detected": "lib.status_not_detected",
        "not_applicable": "lib.status_na",
        "requires_manual_review": "lib.status_review",
    }.get(status or "", "")
    if key:
        return t(lang, key)
    return status or ""


def _lessons_for_stage(
    stage_key: str,
    hit: dict[str, Any],
    classification: dict[str, Any],
    lang: str = "en",
) -> dict[str, str]:
    purpose = stage_purpose(lang, stage_key)
    return {
        "lessons": t(
            lang,
            "lib.lessons",
            purpose=purpose,
            status=_status_label(lang, hit.get("status")),
        ),
        "connection": t(lang, "lib.connection"),
        "writing": t(lang, "lib.writing"),
    }


def _extract_elements(
    text: str, sections: list[dict[str, Any]], classification: dict[str, Any]
) -> list[dict[str, Any]]:
    els: list[dict[str, Any]] = []
    if classification.get("title"):
        els.append(
            {
                "type": "research_title",
                "value": classification["title"],
                "role": "ai_interpretation",
                "confidence": 0.5,
                "reuse_category": "writing_example",
            }
        )
    if classification.get("abstract"):
        els.append(
            {
                "type": "abstract",
                "value": classification["abstract"],
                "role": "exact",
                "confidence": 0.7,
                "reuse_category": "background_evidence",
                "heading": "Abstract",
            }
        )
    # Objectives-like sentences
    for m in re.finditer(
        r"(?:the (?:purpose|aim|objective)s? of this study (?:is|was|are|were)[^.]+.)",
        text[:12000],
        re.I,
    ):
        els.append(
            {
                "type": "overall_aim",
                "value": m.group(0).strip(),
                "role": "exact",
                "confidence": 0.65,
                "reuse_category": "writing_example",
                "location": "body",
            }
        )
        break
    for m in re.finditer(
        r"(?:research questions?[:\s]+)(.{20,400})",
        text[:15000],
        re.I,
    ):
        els.append(
            {
                "type": "research_questions",
                "value": m.group(0).strip()[:500],
                "role": "exact",
                "confidence": 0.55,
                "reuse_category": "writing_example",
            }
        )
        break
    return els[:30]


def _section_by_stage(
    hits: dict[str, dict[str, Any]], *stage_keys: str
) -> str:
    for key in stage_keys:
        hit = hits.get(key) or {}
        if hit.get("status") in ("detected", "partially_detected"):
            text = hit.get("ai_summary") or hit.get("extracted_excerpt") or ""
            if text.strip():
                return _short_summary(text, 600)
    return ""


def _build_study_summary(
    text: str,
    sections: list[dict[str, Any]],
    classification: dict[str, Any],
    hits: dict[str, dict[str, Any]],
    lang: str = "en",
) -> dict[str, Any]:
    """
    Simple study-oriented summary for learning from the paper
    (not the user's project). Ideas, methods, findings, conclusions, writing style.
    """
    abstract = classification.get("abstract") or ""
    if not abstract:
        for sec in sections:
            if re.search(r"abstract|ملخص", sec.get("heading", ""), re.I):
                abstract = _short_summary(sec.get("content", ""), 700)
                break

    main_ideas = abstract or _section_by_stage(
        hits, "problem_purpose", "literature_synthesis", "idea"
    )
    if not main_ideas:
        main_ideas = _short_summary(text[:2500], 500)

    methods = _section_by_stage(
        hits, "methodology", "population_sampling", "instruments", "analysis_plan"
    )
    findings = _section_by_stage(hits, "results")
    conclusions = _section_by_stage(hits, "conclusion", "discussion")

    # Writing style signals (educational, not grading)
    lower = text[:12000].lower()
    style_bits: list[str] = []
    if re.search(r"\b(we|our study|this study)\b", lower):
        style_bits.append(t(lang, "study.style_first_person"))
    if re.search(r"\b(the researchers|the authors|it was found)\b", lower):
        style_bits.append(t(lang, "study.style_passive"))
    if re.search(r"\b(will be|is proposed|this proposal)\b", lower):
        style_bits.append(t(lang, "study.style_future"))
    if re.search(r"\b(results showed|participants completed|was conducted)\b", lower):
        style_bits.append(t(lang, "study.style_past"))
    if classification.get("methodology_paradigm") == "qualitative":
        style_bits.append(t(lang, "study.style_qual"))
    elif classification.get("methodology_paradigm") == "quantitative":
        style_bits.append(t(lang, "study.style_quant"))
    if not style_bits:
        style_bits.append(t(lang, "study.style_default"))

    structure_bits = []
    detected = [
        k for k, v in hits.items() if v.get("status") in ("detected", "partially_detected")
    ]
    structure_bits.append(
        t(lang, "study.structure_count", n=len(detected), total=len(RESEARCH_STAGES))
    )
    if hits.get("problem_purpose", {}).get("status") == "detected":
        structure_bits.append(t(lang, "study.structure_has_problem"))
    if hits.get("methodology", {}).get("status") in ("detected", "partially_detected"):
        structure_bits.append(t(lang, "study.structure_has_methods"))
    if hits.get("results", {}).get("status") in ("detected", "partially_detected"):
        structure_bits.append(t(lang, "study.structure_has_results"))
    if hits.get("references", {}).get("status") in ("detected", "partially_detected"):
        structure_bits.append(t(lang, "study.structure_has_refs"))

    return {
        "purpose": t(lang, "study.purpose"),
        "title": classification.get("title"),
        "document_type": classification.get("document_type"),
        "document_type_confidence": classification.get("confidence"),
        "main_ideas": main_ideas or t(lang, "study.not_found"),
        "methods": methods or t(lang, "study.not_found"),
        "findings": findings or t(lang, "study.not_found_results"),
        "conclusions": conclusions or t(lang, "study.not_found"),
        "writing_style": style_bits,
        "structure_explanation": structure_bits,
        "how_to_study": [
            t(lang, "study.how1"),
            t(lang, "study.how2"),
            t(lang, "study.how3"),
            t(lang, "study.how4"),
            t(lang, "study.how5"),
        ],
        "integrity_note": t(lang, "study.integrity"),
    }


def _build_learning_report(
    doc: SourceDocument,
    hits: dict[str, dict[str, Any]],
    classification: dict[str, Any],
    warnings: list[str],
    lang: str = "en",
) -> dict[str, Any]:
    stages_out = []
    for stage in RESEARCH_STAGES:
        key = stage["key"]
        hit = hits.get(key, {"status": "not_detected"})
        label = stage["label_ar"] if lang == "ar" else stage["label_en"]
        stages_out.append(
            {
                "stage_key": key,
                "label_en": stage["label_en"],
                "label_ar": stage["label_ar"],
                "label": label,
                "status": hit.get("status", "not_detected"),
                "purpose": stage_purpose(lang, key),
                "how_paper_approached": hit.get("ai_summary"),
                "strengths": hit.get("strengths"),
                "improvements": hit.get("limitations"),
                "lessons": _lessons_for_stage(key, hit, classification, lang)["lessons"],
                "user_questions": [
                    t(lang, "lib.user_q1", label=label),
                    t(lang, "lib.user_q2"),
                ],
                "template_hint": t(lang, "lib.template_hint", label=label),
                "mistakes_to_avoid": [
                    t(lang, "lib.mistake1"),
                    t(lang, "lib.mistake2"),
                    t(lang, "lib.mistake3"),
                ],
                "confidence": hit.get("confidence"),
            }
        )
    return {
        "document_id": doc.id,
        "language": lang,
        "integrity_preamble": t(lang, "lib.integrity_preamble"),
        "classification": {
            "document_type": classification.get("document_type"),
            "confidence": classification.get("confidence"),
            "evidence": classification.get("evidence"),
            "confirmed": False,
            "note": t(lang, "lib.confirm_note"),
        },
        "stages": stages_out,
        "warnings": warnings,
        "writing_patterns": {
            "intro_to_problem": t(lang, "lib.pattern_intro"),
            "methods_language": t(lang, "lib.pattern_methods"),
            "results_vs_discussion": t(lang, "lib.pattern_results"),
        },
    }


def _build_quality_analysis(
    hits: dict[str, dict[str, Any]],
    classification: dict[str, Any],
    text: str,
    lang: str = "en",
) -> dict[str, Any]:
    issues = []
    if hits.get("problem_purpose", {}).get("status") in (None, "not_detected"):
        issues.append(
            {
                "issue": t(lang, "lib.issue_problem"),
                "why_it_matters": t(lang, "lib.issue_problem_why"),
                "evidence": "—",
                "lesson": t(lang, "lib.issue_problem_lesson"),
                "confidence": 0.5,
            }
        )
    if classification.get("confidence", 0) < 0.65:
        issues.append(
            {
                "issue": t(lang, "lib.issue_type"),
                "why_it_matters": t(lang, "lib.issue_type_why"),
                "evidence": classification.get("evidence"),
                "lesson": t(lang, "lib.issue_type_lesson"),
                "confidence": classification.get("confidence"),
            }
        )
    return {
        "educational_note": t(lang, "lib.quality_note"),
        "issues": issues,
        "strengths_observed": [
            k for k, v in hits.items() if v.get("status") == "detected"
        ][:8],
    }


def _build_structure_map(
    hits: dict[str, dict[str, Any]],
    sections: list[dict[str, Any]],
    lang: str = "en",
) -> dict[str, Any]:
    nodes = []
    for stage in RESEARCH_STAGES:
        key = stage["key"]
        hit = hits.get(key, {})
        label = stage["label_ar"] if lang == "ar" else stage["label_en"]
        nodes.append(
            {
                "stage_key": key,
                "label": label,
                "status": hit.get("status", "not_detected"),
                "original_section": hit.get("original_heading"),
                "methodological_purpose": stage_purpose(lang, key),
                "lesson": (
                    _lessons_for_stage(key, hit or {"status": "not_detected"}, {}, lang)[
                        "lessons"
                    ]
                )[:240],
            }
        )
    return {
        "nodes": nodes,
        "section_count": len(sections),
        "note": t(lang, "lib.map_note"),
    }


def _comparison_patterns(docs: list[SourceDocument], lang: str = "en") -> list[str]:
    patterns = []
    types = {d.document_type for d in docs if d.document_type}
    if len(types) > 1:
        patterns.append(
            t(lang, "lib.compare_types", types=", ".join(sorted(x for x in types if x)))
        )
    designs = {d.research_design for d in docs if d.research_design}
    if designs:
        patterns.append(t(lang, "lib.compare_designs", designs=", ".join(sorted(designs))))
    patterns.append(t(lang, "lib.compare_gap"))
    return patterns


def _hits_from_mappings(mappings: list[DocumentStageMapping]) -> dict[str, dict[str, Any]]:
    hits: dict[str, dict[str, Any]] = {}
    for m in mappings:
        hits[m.stage_key] = {
            "status": m.status,
            "ai_summary": m.ai_summary,
            "extracted_excerpt": m.extracted_excerpt,
            "original_heading": m.original_heading,
            "confidence": m.confidence,
            "strengths": m.strengths,
            "limitations": m.limitations,
            "completeness": m.completeness,
            "methodological_clarity": m.methodological_clarity,
        }
    return hits


def _is_placeholder_text(value: str | None, *keys: str) -> bool:
    if not value:
        return True
    candidates = {t("en", k) for k in keys} | {t("ar", k) for k in keys}
    return value.strip() in candidates


def _localize_warnings(raw: list[Any], lang: str) -> list[str]:
    """Map known EN/AR warning templates to the requested language; keep unknown as-is."""
    known_keys = [
        "lib.ocr_quality",
        "lib.ocr_empty",
        "lib.ocr_needed",
        "lib.no_text",
        "lib.uncertain_type",
        "lib.stages_review",
    ]
    en_to_key = {t("en", k): k for k in known_keys}
    ar_to_key = {t("ar", k): k for k in known_keys}
    out: list[str] = []
    for w in raw:
        s = str(w)
        key = en_to_key.get(s) or ar_to_key.get(s)
        if key:
            out.append(t(lang, key))
        else:
            out.append(s)
    return out


def present_document_analysis(doc: SourceDocument, language: str | None = None) -> dict[str, Any]:
    """
    Build localized analysis payload for API responses.

    Exact paper excerpts stay in the source language of the document.
    Educational summaries, lessons, warnings, structure map, and study guidance
    are regenerated in the requested UI language (en|ar).
    """
    lang = normalize_lang(language or "en")
    mappings = sorted(doc.stage_mappings or [], key=lambda m: m.stage_key)
    hits = _hits_from_mappings(mappings)
    classification = {
        "document_type": doc.document_type,
        "confidence": doc.document_type_confidence or 0.0,
        "evidence": doc.document_type_evidence,
        "title": doc.title_detected,
        "abstract": doc.abstract_excerpt,
        "methodology_paradigm": doc.methodology_paradigm,
    }
    try:
        stored_warnings = json.loads(doc.analysis_warnings or "[]")
        if not isinstance(stored_warnings, list):
            stored_warnings = []
    except json.JSONDecodeError:
        stored_warnings = []
    warnings = _localize_warnings(stored_warnings, lang)

    learning = _build_learning_report(doc, hits, classification, warnings, lang=lang)

    # Preserve AI enrichment blob if present (may already be in target language if reprocessed)
    try:
        stored_learning = json.loads(doc.learning_report_json or "{}")
    except json.JSONDecodeError:
        stored_learning = {}
    if isinstance(stored_learning, dict) and stored_learning.get("ai_enrichment"):
        learning["ai_enrichment"] = stored_learning["ai_enrichment"]
        if isinstance(stored_learning.get("writing_patterns"), dict):
            ai_p = stored_learning["writing_patterns"].get("ai_patterns")
            if ai_p:
                learning["writing_patterns"] = {
                    **learning["writing_patterns"],
                    "ai_patterns": ai_p,
                }

    stored_study = None
    if isinstance(stored_learning, dict):
        stored_study = stored_learning.get("study_summary")
    if not isinstance(stored_study, dict):
        stored_study = {}

    main_ideas = stored_study.get("main_ideas")
    methods = stored_study.get("methods")
    findings = stored_study.get("findings")
    conclusions = stored_study.get("conclusions")
    if _is_placeholder_text(main_ideas, "study.not_found"):
        main_ideas = t(lang, "study.not_found")
    if _is_placeholder_text(methods, "study.not_found"):
        methods = t(lang, "study.not_found")
    if _is_placeholder_text(findings, "study.not_found", "study.not_found_results"):
        findings = t(lang, "study.not_found_results")
    if _is_placeholder_text(conclusions, "study.not_found"):
        conclusions = t(lang, "study.not_found")

    # Rebuild educational study fields in the UI language
    sample = " ".join(
        filter(
            None,
            [
                doc.abstract_excerpt or "",
                str(main_ideas or "")[:1200],
                str(methods or "")[:800],
            ],
        )
    ).lower()
    style_bits: list[str] = []
    if re.search(r"\b(we|our study|this study)\b", sample) or "هذه الدراسة" in sample:
        style_bits.append(t(lang, "study.style_first_person"))
    if re.search(r"\b(the researchers|the authors|it was found)\b", sample):
        style_bits.append(t(lang, "study.style_passive"))
    if re.search(r"\b(will be|is proposed|this proposal)\b", sample):
        style_bits.append(t(lang, "study.style_future"))
    if re.search(r"\b(results showed|participants completed|was conducted)\b", sample):
        style_bits.append(t(lang, "study.style_past"))
    if classification.get("methodology_paradigm") == "qualitative":
        style_bits.append(t(lang, "study.style_qual"))
    elif classification.get("methodology_paradigm") == "quantitative":
        style_bits.append(t(lang, "study.style_quant"))
    if not style_bits:
        style_bits.append(t(lang, "study.style_default"))

    structure_bits: list[str] = []
    detected = [
        k for k, v in hits.items() if v.get("status") in ("detected", "partially_detected")
    ]
    structure_bits.append(
        t(lang, "study.structure_count", n=len(detected), total=len(RESEARCH_STAGES))
    )
    if hits.get("problem_purpose", {}).get("status") == "detected":
        structure_bits.append(t(lang, "study.structure_has_problem"))
    if hits.get("methodology", {}).get("status") in ("detected", "partially_detected"):
        structure_bits.append(t(lang, "study.structure_has_methods"))
    if hits.get("results", {}).get("status") in ("detected", "partially_detected"):
        structure_bits.append(t(lang, "study.structure_has_results"))
    if hits.get("references", {}).get("status") in ("detected", "partially_detected"):
        structure_bits.append(t(lang, "study.structure_has_refs"))

    study = {
        "purpose": t(lang, "study.purpose"),
        "title": stored_study.get("title") or doc.title_detected,
        "document_type": stored_study.get("document_type") or doc.document_type,
        "document_type_confidence": stored_study.get("document_type_confidence")
        or doc.document_type_confidence,
        "main_ideas": main_ideas or t(lang, "study.not_found"),
        "methods": methods or t(lang, "study.not_found"),
        "findings": findings or t(lang, "study.not_found_results"),
        "conclusions": conclusions or t(lang, "study.not_found"),
        "writing_style": style_bits,
        "structure_explanation": structure_bits,
        "how_to_study": [
            t(lang, "study.how1"),
            t(lang, "study.how2"),
            t(lang, "study.how3"),
            t(lang, "study.how4"),
            t(lang, "study.how5"),
        ],
        "integrity_note": t(lang, "study.integrity"),
    }
    learning["study_summary"] = study

    quality = _build_quality_analysis(hits, classification, "", lang=lang)
    # Keep optional AI quality enrichment lists if stored
    try:
        stored_quality = json.loads(doc.quality_analysis_json or "{}")
        if isinstance(stored_quality, dict) and stored_quality.get("ai_enrichment"):
            quality["ai_enrichment"] = stored_quality["ai_enrichment"]
    except json.JSONDecodeError:
        pass

    structure_map = _build_structure_map(hits, list(doc.sections or []), lang=lang)

    # Localized stage mapping views (do not mutate DB rows)
    stage_views: list[dict[str, Any]] = []
    for m in mappings:
        hit = hits.get(m.stage_key) or {"status": m.status}
        lessons = _lessons_for_stage(m.stage_key, hit, classification, lang)
        if m.status == "not_detected":
            ai_summary = t(lang, "lib.not_detected_summary")
            lessons_text = t(
                lang, "lib.not_detected_lesson", purpose=stage_purpose(lang, m.stage_key)
            )
            strengths = None
            limitations = None
            connection = None
            writing = None
        else:
            ai_summary = m.ai_summary
            if m.status == "partially_detected" and _is_placeholder_text(
                m.ai_summary, "lib.partial_keywords"
            ):
                ai_summary = t(lang, "lib.partial_keywords")
            lessons_text = lessons["lessons"]
            # Preserve AI notes appended after template
            if m.lessons_for_user and " | AI note: " in m.lessons_for_user:
                extra = m.lessons_for_user.split(" | AI note: ", 1)[1]
                label = "ملاحظة ذكاء" if lang == "ar" else "AI note"
                lessons_text = f"{lessons_text} | {label}: {extra}"
            strengths = m.strengths
            if m.status == "detected" and (
                not strengths or _is_placeholder_text(strengths, "lib.strength_clear")
            ):
                strengths = t(lang, "lib.strength_clear")
            limitations = m.limitations
            if m.status == "partially_detected" and (
                not limitations or _is_placeholder_text(limitations, "lib.limit_thin")
            ):
                limitations = t(lang, "lib.limit_thin")
            connection = lessons["connection"]
            writing = lessons["writing"]

        stage_views.append(
            {
                "id": m.id,
                "stage_key": m.stage_key,
                "status": m.status,
                "original_heading": m.original_heading,
                "page_or_section": m.page_or_section,
                "extracted_excerpt": m.extracted_excerpt,
                "ai_summary": ai_summary,
                "completeness": m.completeness,
                "methodological_clarity": m.methodological_clarity,
                "strengths": strengths,
                "limitations": limitations,
                "lessons_for_user": lessons_text,
                "connection_to_next": connection,
                "writing_strategy": writing,
                "confidence": m.confidence,
                "researcher_verified": m.researcher_verified,
                "researcher_correction": m.researcher_correction,
            }
        )

    return {
        "language": lang,
        "analysis_warnings": warnings,
        "learning_report": learning,
        "quality_analysis": quality,
        "structure_map": structure_map,
        "study_summary": study,
        "stage_mappings": stage_views,
        "integrity_notice": t(lang, "detail.integrity_notice"),
    }
