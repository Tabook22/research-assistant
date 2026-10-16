"""Previous Research Library API."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.library import DocumentStageMapping, LearningNote, SourceDocument
from app.models.user import User
from app.schemas.library import (
    ClassificationConfirm,
    CompareRequest,
    ComparisonItemOut,
    ComparisonOut,
    MultiUploadResult,
    NotesUpdate,
    SourceDocumentDetail,
    SourceDocumentSummary,
    StageMappingOut,
    StageVerifyRequest,
    TranslateAnalysisOut,
    TranslateAnalysisRequest,
    WriteSectionDraftOut,
    WriteSectionDraftRequest,
    WriteSectionGuideOut,
    WriteSectionGuideRequest,
)
from app.i18n.lang import normalize_lang, t
from app.services.access import get_project_for_user
from app.services import paper_analysis_service as libsvc
from app.services.library_ai_service import (
    build_write_section_guide,
    draft_section_from_answers,
    translate_presented_analysis,
)

router = APIRouter(prefix="/projects/{project_id}/library", tags=["library"])


def _parse_json_list(raw: str | None) -> list:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _parse_json_obj(raw: str | None) -> dict | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _detail(doc: SourceDocument, language: str | None = None) -> SourceDocumentDetail:
    """Return document detail with analyses localized to the UI language."""
    lang = normalize_lang(language)
    base = SourceDocumentSummary.model_validate(doc)
    presented = libsvc.present_document_analysis(doc, language=lang)
    stage_rows = [
        StageMappingOut.model_validate(row) for row in presented["stage_mappings"]
    ]
    return SourceDocumentDetail(
        **base.model_dump(),
        document_type_evidence=doc.document_type_evidence,
        academic_level_confidence=doc.academic_level_confidence,
        authors_detected=doc.authors_detected,
        abstract_excerpt=doc.abstract_excerpt,
        analysis_warnings=presented["analysis_warnings"],
        learning_report=presented["learning_report"],
        quality_analysis=presented["quality_analysis"],
        structure_map=presented["structure_map"],
        study_summary=presented["study_summary"],
        researcher_notes=doc.researcher_notes,
        sections=doc.sections or [],
        stage_mappings=stage_rows,
        elements=doc.elements or [],
        integrity_notice=presented["integrity_notice"],
    )


@router.get("", response_model=list[SourceDocumentSummary])
def list_docs(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[SourceDocumentSummary]:
    get_project_for_user(db, project_id, user)
    rows = libsvc.list_library(db, project_id)
    return [SourceDocumentSummary.model_validate(r) for r in rows]


@router.post("/upload", response_model=SourceDocumentDetail)
async def upload_and_analyze(
    project_id: int,
    file: UploadFile = File(...),
    language: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SourceDocumentDetail:
    project = get_project_for_user(db, project_id, user)
    lang = language or user.preferred_language or project.writing_language
    doc = await libsvc.save_and_process(db, project, user.id, file, language=lang)
    return _detail(doc, language=lang)


@router.post("/upload-many", response_model=MultiUploadResult)
async def upload_many_and_analyze(
    project_id: int,
    files: list[UploadFile] = File(...),
    language: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MultiUploadResult:
    """Upload and analyze multiple study papers at once (learning library)."""
    project = get_project_for_user(db, project_id, user)
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    if len(files) > 15:
        raise HTTPException(status_code=400, detail="Maximum 15 files per batch")

    uploaded: list[SourceDocumentDetail] = []
    failed: list[dict[str, str]] = []
    lang = language or user.preferred_language or project.writing_language

    for f in files:
        name = f.filename or "unknown"
        try:
            doc = await libsvc.save_and_process(db, project, user.id, f, language=lang)
            uploaded.append(_detail(doc, language=lang))
        except HTTPException as exc:
            failed.append({"filename": name, "error": str(exc.detail)})
        except Exception as exc:  # noqa: BLE001
            failed.append({"filename": name, "error": exc.__class__.__name__})

    msg = (
        f"Processed {len(uploaded)} file(s)"
        + (f"; {len(failed)} failed" if failed else "")
        + ". These are study references, not your project manuscript."
    )
    if normalize_lang(lang) == "ar":
        msg = (
            f"تمت معالجة {len(uploaded)} ملف/ملفات"
            + (f"؛ فشل {len(failed)}" if failed else "")
            + ". هذه مراجع دراسية وليست مخطوطة مشروعك."
        )
    return MultiUploadResult(uploaded=uploaded, failed=failed, message=msg)


@router.get("/{document_id}", response_model=SourceDocumentDetail)
def get_doc(
    project_id: int,
    document_id: int,
    language: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SourceDocumentDetail:
    get_project_for_user(db, project_id, user)
    doc = libsvc.get_source_document(db, document_id)
    if not doc or doc.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found")
    return _detail(doc, language=language or user.preferred_language)


@router.post("/{document_id}/reprocess", response_model=SourceDocumentDetail)
async def reprocess(
    project_id: int,
    document_id: int,
    language: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SourceDocumentDetail:
    project = get_project_for_user(db, project_id, user)
    doc = libsvc.get_source_document(db, document_id)
    if not doc or doc.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found")
    lang = language or user.preferred_language or project.writing_language
    doc = await libsvc.reprocess(db, doc, language=lang)
    return _detail(doc, language=lang)


@router.get("/{document_id}/file")
def download_source_file(
    project_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Serve original file for in-app viewing (authenticated)."""
    get_project_for_user(db, project_id, user)
    doc = db.get(SourceDocument, document_id)
    if not doc or doc.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found")
    from pathlib import Path

    path = Path(doc.storage_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File missing on server")
    media = {
        "pdf": "application/pdf",
        "txt": "text/plain",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "rtf": "application/rtf",
    }.get(doc.file_type, "application/octet-stream")
    return FileResponse(
        path,
        media_type=media,
        filename=doc.original_filename,
        content_disposition_type="inline",
    )


@router.post("/{document_id}/translate-analysis", response_model=TranslateAnalysisOut)
async def translate_analysis(
    project_id: int,
    document_id: int,
    payload: TranslateAnalysisRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TranslateAnalysisOut:
    """
    Translate free-text analysis (study summary, stage excerpts, AI notes) to Arabic.
    Display-only — does not overwrite stored English source excerpts in the database.
    """
    get_project_for_user(db, project_id, user)
    doc = libsvc.get_source_document(db, document_id)
    if not doc or doc.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found")

    target = normalize_lang(payload.target_language or "ar")
    if target != "ar":
        raise HTTPException(status_code=400, detail="Only target_language=ar is supported")

    scope = (payload.scope or "full").strip().lower()
    if scope not in ("full", "stage"):
        raise HTTPException(status_code=400, detail="scope must be 'full' or 'stage'")
    if scope == "stage" and not payload.stage_key:
        raise HTTPException(status_code=400, detail="stage_key is required when scope=stage")

    # Start from Arabic-localized templates, then AI-translate remaining Latin free text.
    base = _detail(doc, language="ar")
    presented = {
        "analysis_warnings": base.analysis_warnings,
        "learning_report": base.learning_report,
        "quality_analysis": base.quality_analysis,
        "structure_map": base.structure_map,
        "study_summary": base.study_summary,
        "stage_mappings": [m.model_dump() for m in base.stage_mappings],
        "integrity_notice": base.integrity_notice,
    }
    result = await translate_presented_analysis(
        presented,
        scope=scope,
        stage_key=payload.stage_key,
        target_language="ar",
        abstract_excerpt=base.abstract_excerpt,
    )
    presented2 = result["presented"]
    stage_rows = [
        StageMappingOut.model_validate(row)
        for row in (presented2.get("stage_mappings") or [])
    ]
    detail = SourceDocumentDetail(
        **SourceDocumentSummary.model_validate(doc).model_dump(),
        document_type_evidence=doc.document_type_evidence,
        academic_level_confidence=doc.academic_level_confidence,
        authors_detected=doc.authors_detected,
        abstract_excerpt=result.get("abstract_excerpt") or base.abstract_excerpt,
        analysis_warnings=presented2.get("analysis_warnings") or [],
        learning_report=presented2.get("learning_report"),
        quality_analysis=presented2.get("quality_analysis"),
        structure_map=presented2.get("structure_map"),
        study_summary=presented2.get("study_summary"),
        researcher_notes=doc.researcher_notes,
        sections=doc.sections or [],
        stage_mappings=stage_rows,
        elements=doc.elements or [],
        integrity_notice=presented2.get("integrity_notice") or base.integrity_notice,
    )
    msg = result.get("message") or ""
    translated_n = int(result.get("translated_fields") or 0)
    candidates_n = int(result.get("candidate_fields") or 0)
    if translated_n == 0 and candidates_n > 0:
        msg = result.get("message") or t("ar", "translate.need_ai")
    elif translated_n == 0:
        msg = t("ar", "translate.none")
    elif not msg:
        msg = t("ar", "translate.ok")

    return TranslateAnalysisOut(
        document=detail,
        ai_used=bool(result.get("ai_used")),
        message=msg,
        translated_fields=translated_n,
        candidate_fields=candidates_n,
    )


@router.post("/{document_id}/write-section/guide", response_model=WriteSectionGuideOut)
def write_section_guide(
    project_id: int,
    document_id: int,
    payload: WriteSectionGuideRequest,
    language: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WriteSectionGuideOut:
    project = get_project_for_user(db, project_id, user)
    doc = libsvc.get_source_document(db, document_id)
    if not doc or doc.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found")
    mapping = next(
        (m for m in (doc.stage_mappings or []) if m.stage_key == payload.stage_key),
        None,
    )
    lang = payload.language or language or user.preferred_language or project.writing_language
    guide = build_write_section_guide(
        project, doc, payload.stage_key, mapping, language=lang
    )
    return WriteSectionGuideOut(guide=guide)


@router.post("/{document_id}/write-section/draft", response_model=WriteSectionDraftOut)
async def write_section_draft(
    project_id: int,
    document_id: int,
    payload: WriteSectionDraftRequest,
    language: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WriteSectionDraftOut:
    project = get_project_for_user(db, project_id, user)
    doc = libsvc.get_source_document(db, document_id)
    if not doc or doc.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found")
    mapping = next(
        (m for m in (doc.stage_mappings or []) if m.stage_key == payload.stage_key),
        None,
    )
    lang = payload.language or language or user.preferred_language or project.writing_language
    guide = build_write_section_guide(
        project, doc, payload.stage_key, mapping, language=lang
    )
    result = await draft_section_from_answers(
        project, doc, payload.stage_key, guide, payload.answers, language=lang
    )
    note_id = None
    if payload.save_as_learning_note and result.get("draft"):
        note = LearningNote(
            project_id=project_id,
            source_document_id=document_id,
            stage_key=payload.stage_key,
            note=result["draft"][:20000],
            linked_to_user_project=False,
        )
        db.add(note)
        db.commit()
        db.refresh(note)
        note_id = note.id
    return WriteSectionDraftOut(
        draft=result["draft"],
        source=result.get("source", "unknown"),
        ai_used=bool(result.get("ai_used")),
        learning_note_id=note_id,
    )


@router.post("/{document_id}/confirm-classification", response_model=SourceDocumentDetail)
def confirm_classification(
    project_id: int,
    document_id: int,
    payload: ClassificationConfirm,
    language: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SourceDocumentDetail:
    get_project_for_user(db, project_id, user)
    doc = libsvc.get_source_document(db, document_id)
    if not doc or doc.project_id != project_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Document not found")
    doc = libsvc.confirm_classification(
        db,
        doc,
        document_type=payload.document_type,
        academic_level=payload.academic_level,
        discipline=payload.discipline,
        research_design=payload.research_design,
    )
    return _detail(doc, language=language or user.preferred_language)


@router.patch("/{document_id}/notes", response_model=SourceDocumentDetail)
def update_notes(
    project_id: int,
    document_id: int,
    payload: NotesUpdate,
    language: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SourceDocumentDetail:
    get_project_for_user(db, project_id, user)
    doc = db.get(SourceDocument, document_id)
    if not doc or doc.project_id != project_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Document not found")
    doc.researcher_notes = payload.researcher_notes
    db.commit()
    full = libsvc.get_source_document(db, document_id)
    return _detail(full, language=language or user.preferred_language)  # type: ignore[arg-type]


@router.post(
    "/{document_id}/stages/{mapping_id}/verify",
    response_model=StageMappingOut,
)
def verify_stage(
    project_id: int,
    document_id: int,
    mapping_id: int,
    payload: StageVerifyRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StageMappingOut:
    get_project_for_user(db, project_id, user)
    mapping = db.get(DocumentStageMapping, mapping_id)
    if not mapping or mapping.source_document_id != document_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Stage mapping not found")
    doc = db.get(SourceDocument, document_id)
    if not doc or doc.project_id != project_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Document not found")
    mapping = libsvc.verify_stage(db, mapping, payload.status, payload.correction)
    return StageMappingOut.model_validate(mapping)


@router.post("/compare", response_model=ComparisonOut)
def compare(
    project_id: int,
    payload: CompareRequest,
    language: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ComparisonOut:
    """Compare 2+ library papers. Declared before /{document_id} routes in file order below."""
    project = get_project_for_user(db, project_id, user)
    if not payload.document_ids or len(payload.document_ids) < 2:
        raise HTTPException(
            status_code=400,
            detail="Select at least two library documents to compare.",
        )
    lang = language or user.preferred_language or project.writing_language
    try:
        comp = libsvc.compare_documents(
            db,
            project,
            payload.document_ids,
            payload.title or "Paper comparison",
            language=lang,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500,
            detail=f"Comparison failed: {exc.__class__.__name__}",
        ) from exc
    if not comp:
        raise HTTPException(status_code=500, detail="Comparison produced no result")
    items = []
    for it in comp.items:
        try:
            values = json.loads(it.values_json)
        except json.JSONDecodeError:
            values = {}
        items.append(
            ComparisonItemOut(
                id=it.id,
                element_key=it.element_key,
                values=values,
                lessons=it.lessons,
            )
        )
    return ComparisonOut(
        id=comp.id,
        project_id=comp.project_id,
        title=comp.title,
        document_ids=json.loads(comp.document_ids_json),
        summary=_parse_json_obj(comp.summary_json),
        lessons=_parse_json_obj(comp.lessons_json),
        items=items,
        created_at=comp.created_at,
    )
