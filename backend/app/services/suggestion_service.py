"""Parse, store, and apply AI structured suggestions (researcher-approved only)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.decisions import AISuggestion, ResearcherDecision
from app.models.project import ResearchProject, ResearchProjectProfile
from app.models.research import (
    AnalysisMapping,
    AnalysisPlan,
    Hypothesis,
    Instrument,
    InstrumentItem,
    InstrumentSection,
    OperationalDefinition,
    Population,
    ResearchDesign,
    ResearchObjective,
    ResearchQuestion,
    SamplingPlan,
    Variable,
)
from app.schemas.suggestions import SuggestionPayload

logger = logging.getLogger(__name__)

SUGGESTION_BLOCK_RE = re.compile(
    r"---SUGGESTIONS_JSON---\s*(\{.*?\})\s*---END_SUGGESTIONS---",
    re.DOTALL | re.IGNORECASE,
)
JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)

ALLOWED_TYPES = {
    "profile_field",
    "research_question",
    "objective",
    "hypothesis",
    "variable",
    "design",
    "population",
    "sampling",
    "instrument_item",
    "analysis_mapping",
}

PROFILE_FIELDS = {
    "research_problem",
    "existing_evidence",
    "research_gap",
    "overall_aim",
    "expected_contribution",
    "ethics_requirements",
    "refined_idea",
    "proposed_scope",
    "key_concepts",
    "initial_search_terms",
    "scientific_significance",
    "practical_significance",
    "unresolved_decisions",
    "assumptions_requiring_verification",
}


def strip_and_parse_suggestions(raw_text: str) -> tuple[str, list[SuggestionPayload]]:
    """
    Extract structured suggestions from the model reply.
    Returns (display_text_without_block, list of suggestion payloads).
    """
    text = raw_text or ""
    suggestions: list[SuggestionPayload] = []

    match = SUGGESTION_BLOCK_RE.search(text)
    json_blob = None
    if match:
        json_blob = match.group(1)
        text = SUGGESTION_BLOCK_RE.sub("", text).strip()
    else:
        # Fallback: last JSON fence that contains "suggestions"
        fences = list(JSON_FENCE_RE.finditer(text))
        for m in reversed(fences):
            try:
                data = json.loads(m.group(1))
                if isinstance(data, dict) and "suggestions" in data:
                    json_blob = m.group(1)
                    text = (text[: m.start()] + text[m.end() :]).strip()
                    break
            except json.JSONDecodeError:
                continue

    if json_blob:
        try:
            data = json.loads(json_blob)
            items = data.get("suggestions") if isinstance(data, dict) else None
            if isinstance(items, list):
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    stype = str(item.get("type") or "").strip()
                    if stype not in ALLOWED_TYPES:
                        continue
                    title = str(item.get("title") or stype).strip()[:500]
                    payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
                    rationale = item.get("rationale")
                    suggestions.append(
                        SuggestionPayload(
                            type=stype,
                            title=title,
                            payload=payload,
                            rationale=str(rationale) if rationale else None,
                        )
                    )
        except json.JSONDecodeError:
            logger.warning("Failed to parse suggestions JSON block")

    return text, suggestions


def persist_suggestions(
    db: Session,
    project: ResearchProject,
    stage_key: str | None,
    items: list[SuggestionPayload],
    parent_content: str | None = None,
) -> list[AISuggestion]:
    saved: list[AISuggestion] = []
    for item in items:
        body = {
            "type": item.type,
            "title": item.title,
            "payload": item.payload,
            "rationale": item.rationale,
        }
        row = AISuggestion(
            project_id=project.id,
            stage_key=stage_key,
            suggestion_type=item.type,
            title=item.title,
            content=item.rationale or item.title,
            structured_json=json.dumps(body, ensure_ascii=False),
            approval_status="proposed",
            target_element_type=item.type,
        )
        db.add(row)
        saved.append(row)
    if parent_content and not items:
        # Keep a single chat-level suggestion for audit
        row = AISuggestion(
            project_id=project.id,
            stage_key=stage_key,
            suggestion_type="chat_response",
            title=f"Stage guidance: {stage_key or project.current_stage}",
            content=(parent_content or "")[:5000],
            approval_status="proposed",
        )
        db.add(row)
        saved.append(row)
    db.commit()
    for r in saved:
        db.refresh(r)
    return saved


def suggestion_to_dict(row: AISuggestion) -> dict[str, Any]:
    payload = None
    rationale = None
    if row.structured_json:
        try:
            data = json.loads(row.structured_json)
            payload = data.get("payload")
            rationale = data.get("rationale")
        except json.JSONDecodeError:
            pass
    return {
        "id": row.id,
        "project_id": row.project_id,
        "stage_key": row.stage_key,
        "suggestion_type": row.suggestion_type,
        "title": row.title,
        "content": row.content,
        "structured_json": row.structured_json,
        "approval_status": row.approval_status,
        "target_element_type": row.target_element_type,
        "target_element_id": row.target_element_id,
        "created_at": row.created_at,
        "payload": payload,
        "rationale": rationale,
    }


def list_pending(db: Session, project_id: int) -> list[AISuggestion]:
    return (
        db.query(AISuggestion)
        .filter(
            AISuggestion.project_id == project_id,
            AISuggestion.approval_status.in_(["proposed", "needs_revision", "under_review"]),
            AISuggestion.suggestion_type != "chat_response",
        )
        .order_by(AISuggestion.id.desc())
        .limit(50)
        .all()
    )


def apply_suggestion(
    db: Session,
    project: ResearchProject,
    suggestion: AISuggestion,
    user_id: int | None,
    action: str,
    edited_payload: dict[str, Any] | None = None,
    notes: str | None = None,
    mark_approved: bool = False,
) -> dict[str, Any]:
    if suggestion.project_id != project.id:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    if action == "reject":
        prev = suggestion.approval_status
        suggestion.approval_status = "rejected"
        db.add(
            ResearcherDecision(
                project_id=project.id,
                user_id=user_id,
                element_type="ai_suggestion",
                element_id=suggestion.id,
                decision="reject",
                notes=notes,
                previous_status=prev,
                new_status="rejected",
            )
        )
        db.commit()
        return {
            "suggestion_id": suggestion.id,
            "action": "reject",
            "approval_status": "rejected",
            "message": "Suggestion rejected. It was not written to the project structure.",
        }

    if action not in ("apply", "revise"):
        raise HTTPException(status_code=400, detail="action must be apply, reject, or revise")

    data: dict[str, Any] = {}
    if suggestion.structured_json:
        try:
            data = json.loads(suggestion.structured_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="Invalid suggestion payload") from exc

    stype = data.get("type") or suggestion.suggestion_type
    payload = edited_payload if edited_payload is not None else (data.get("payload") or {})
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload must be an object")

    status = "approved" if mark_approved else "proposed"
    created_type: str | None = None
    created_id: int | None = None

    if stype == "profile_field":
        created_type, created_id = _apply_profile(db, project, payload)
    elif stype == "research_question":
        created_type, created_id = _apply_question(db, project, payload, status)
    elif stype == "objective":
        created_type, created_id = _apply_objective(db, project, payload, status)
    elif stype == "hypothesis":
        created_type, created_id = _apply_hypothesis(db, project, payload, status)
    elif stype == "variable":
        created_type, created_id = _apply_variable(db, project, payload, status)
    elif stype == "design":
        created_type, created_id = _apply_design(db, project, payload, status)
    elif stype == "population":
        created_type, created_id = _apply_population(db, project, payload, status)
    elif stype == "sampling":
        created_type, created_id = _apply_sampling(db, project, payload, status)
    elif stype == "instrument_item":
        created_type, created_id = _apply_instrument_item(db, project, payload, status)
    elif stype == "analysis_mapping":
        created_type, created_id = _apply_analysis_mapping(db, project, payload, status)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported suggestion type: {stype}")

    prev = suggestion.approval_status
    suggestion.approval_status = "approved"
    suggestion.target_element_type = created_type
    suggestion.target_element_id = created_id
    # Store final applied payload
    data["payload"] = payload
    suggestion.structured_json = json.dumps(data, ensure_ascii=False)

    db.add(
        ResearcherDecision(
            project_id=project.id,
            user_id=user_id,
            element_type="ai_suggestion",
            element_id=suggestion.id,
            decision="approve" if action == "apply" else "revise",
            notes=notes,
            previous_status=prev,
            new_status="approved",
        )
    )
    db.commit()
    db.refresh(suggestion)

    return {
        "suggestion_id": suggestion.id,
        "action": action,
        "approval_status": "approved",
        "created_element_type": created_type,
        "created_element_id": created_id,
        "message": f"Applied as {created_type} #{created_id} (record status: {status}).",
    }


def _apply_profile(
    db: Session, project: ResearchProject, payload: dict[str, Any]
) -> tuple[str, int]:
    profile = project.profile
    if not profile:
        profile = ResearchProjectProfile(project_id=project.id)
        db.add(profile)
        db.flush()
    # Accept either {field, value} or multiple field keys
    if "field" in payload and "value" in payload:
        field = str(payload["field"])
        if field not in PROFILE_FIELDS:
            raise HTTPException(status_code=400, detail=f"Unknown profile field: {field}")
        setattr(profile, field, str(payload["value"]))
    else:
        applied = False
        for field, value in payload.items():
            if field in PROFILE_FIELDS and value is not None:
                setattr(profile, field, str(value))
                applied = True
        if not applied:
            raise HTTPException(
                status_code=400,
                detail="profile_field payload needs {field, value} or known profile keys",
            )
    db.commit()
    db.refresh(profile)
    return "profile", profile.id


def _apply_question(
    db: Session, project: ResearchProject, payload: dict[str, Any], status: str
) -> tuple[str, int]:
    text = (payload.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="research_question requires text")
    row = ResearchQuestion(
        project_id=project.id,
        text=text,
        question_type=str(payload.get("question_type") or "descriptive"),
        proposed_analysis=payload.get("proposed_analysis"),
        data_source=payload.get("data_source"),
        approval_status=status,
        sort_order=int(payload.get("sort_order") or 0),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return "research_question", row.id


def _apply_objective(
    db: Session, project: ResearchProject, payload: dict[str, Any], status: str
) -> tuple[str, int]:
    text = (payload.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="objective requires text")
    qid = payload.get("question_id")
    if qid is not None:
        q = db.get(ResearchQuestion, int(qid))
        if not q or q.project_id != project.id:
            raise HTTPException(status_code=400, detail="question_id not found on this project")
    row = ResearchObjective(
        project_id=project.id,
        text=text,
        question_id=int(qid) if qid is not None else None,
        verb=payload.get("verb"),
        objective_type=payload.get("objective_type"),
        approval_status=status,
        sort_order=int(payload.get("sort_order") or 0),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return "objective", row.id


def _apply_hypothesis(
    db: Session, project: ResearchProject, payload: dict[str, Any], status: str
) -> tuple[str, int]:
    h0 = (payload.get("null_hypothesis") or payload.get("h0") or "").strip()
    h1 = (payload.get("alternative_hypothesis") or payload.get("h1") or "").strip()
    if not h0 or not h1:
        raise HTTPException(status_code=400, detail="hypothesis requires null and alternative")
    row = Hypothesis(
        project_id=project.id,
        null_hypothesis=h0,
        alternative_hypothesis=h1,
        question_id=int(payload["question_id"]) if payload.get("question_id") else None,
        direction=str(payload.get("direction") or "non_directional"),
        independent_variable=payload.get("independent_variable"),
        dependent_variable=payload.get("dependent_variable"),
        population=payload.get("population"),
        expected_direction=payload.get("expected_direction"),
        proposed_test=payload.get("proposed_test"),
        theoretical_basis=payload.get("theoretical_basis"),
        approval_status=status,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return "hypothesis", row.id


def _apply_variable(
    db: Session, project: ResearchProject, payload: dict[str, Any], status: str
) -> tuple[str, int]:
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="variable requires name")
    row = Variable(
        project_id=project.id,
        name=name,
        role=str(payload.get("role") or "dependent"),
        measurement_scale=payload.get("measurement_scale"),
        data_source=payload.get("data_source"),
        coding=payload.get("coding"),
        approval_status=status,
    )
    db.add(row)
    db.flush()
    op = payload.get("operational_definition")
    if op:
        db.add(
            OperationalDefinition(
                variable_id=row.id,
                definition=str(op),
                measurement_method=payload.get("measurement_method"),
                instrument_name=payload.get("instrument_name"),
                approval_status=status,
            )
        )
    db.commit()
    db.refresh(row)
    return "variable", row.id


def _apply_design(
    db: Session, project: ResearchProject, payload: dict[str, Any], status: str
) -> tuple[str, int]:
    design_type = (payload.get("design_type") or "").strip()
    if not design_type:
        raise HTTPException(status_code=400, detail="design requires design_type")
    row = ResearchDesign(
        project_id=project.id,
        design_type=design_type,
        paradigm=payload.get("paradigm"),
        rationale=payload.get("rationale"),
        strengths=payload.get("strengths"),
        limitations=payload.get("limitations"),
        bias_risks=payload.get("bias_risks"),
        is_primary=bool(payload.get("is_primary", True)),
        approval_status=status,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return "design", row.id


def _apply_population(
    db: Session, project: ResearchProject, payload: dict[str, Any], status: str
) -> tuple[str, int]:
    target = (payload.get("target_population") or "").strip()
    if not target:
        raise HTTPException(status_code=400, detail="population requires target_population")
    row = Population(
        project_id=project.id,
        target_population=target,
        accessible_population=payload.get("accessible_population"),
        unit_of_analysis=payload.get("unit_of_analysis"),
        inclusion_criteria=payload.get("inclusion_criteria"),
        exclusion_criteria=payload.get("exclusion_criteria"),
        approval_status=status,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return "population", row.id


def _apply_sampling(
    db: Session, project: ResearchProject, payload: dict[str, Any], status: str
) -> tuple[str, int]:
    sample_size = payload.get("sample_size")
    rationale = payload.get("sample_size_rationale")
    if sample_size is not None and not rationale:
        raise HTTPException(
            status_code=400,
            detail="sample_size requires sample_size_rationale (and stated assumptions)",
        )
    row = SamplingPlan(
        project_id=project.id,
        sampling_frame=payload.get("sampling_frame"),
        sampling_method=payload.get("sampling_method"),
        sample_size=int(sample_size) if sample_size is not None else None,
        sample_size_rationale=rationale,
        recruitment_method=payload.get("recruitment_method"),
        response_rate_strategy=payload.get("response_rate_strategy"),
        non_response_considerations=payload.get("non_response_considerations"),
        assumptions=payload.get("assumptions"),
        approval_status=status,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return "sampling", row.id


def _apply_instrument_item(
    db: Session, project: ResearchProject, payload: dict[str, Any], status: str
) -> tuple[str, int]:
    item_text = (payload.get("item_text") or "").strip()
    if not item_text:
        raise HTTPException(status_code=400, detail="instrument_item requires item_text")
    instrument_name = (payload.get("instrument_name") or "Primary questionnaire").strip()
    section_title = (payload.get("section_title") or "Main section").strip()

    inst = (
        db.query(Instrument)
        .filter(Instrument.project_id == project.id, Instrument.name == instrument_name)
        .first()
    )
    if not inst:
        inst = Instrument(
            project_id=project.id,
            name=instrument_name,
            instrument_type=str(payload.get("instrument_type") or "questionnaire"),
            approval_status=status,
        )
        db.add(inst)
        db.flush()

    section = (
        db.query(InstrumentSection)
        .filter(
            InstrumentSection.instrument_id == inst.id,
            InstrumentSection.title == section_title,
        )
        .first()
    )
    if not section:
        section = InstrumentSection(instrument_id=inst.id, title=section_title)
        db.add(section)
        db.flush()

    item = InstrumentItem(
        section_id=section.id,
        item_text=item_text,
        response_type=str(payload.get("response_type") or "likert"),
        response_options=payload.get("response_options"),
        construct_name=payload.get("construct_name"),
        variable_name=payload.get("variable_name"),
        linked_objective=payload.get("linked_objective"),
        linked_question=payload.get("linked_question"),
        planned_analysis=payload.get("planned_analysis"),
        approval_status=status,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return "instrument_item", item.id


def _apply_analysis_mapping(
    db: Session, project: ResearchProject, payload: dict[str, Any], status: str
) -> tuple[str, int]:
    plan = (
        db.query(AnalysisPlan)
        .filter(AnalysisPlan.project_id == project.id)
        .order_by(AnalysisPlan.id.asc())
        .first()
    )
    if not plan:
        plan = AnalysisPlan(
            project_id=project.id,
            title=str(payload.get("plan_title") or "Primary analysis plan"),
            software=payload.get("software"),
            approval_status=status,
        )
        db.add(plan)
        db.flush()

    mapping = AnalysisMapping(
        plan_id=plan.id,
        question_id=int(payload["question_id"]) if payload.get("question_id") else None,
        hypothesis_id=int(payload["hypothesis_id"]) if payload.get("hypothesis_id") else None,
        variables=payload.get("variables"),
        data_type=payload.get("data_type"),
        descriptive_stats=payload.get("descriptive_stats"),
        statistical_test=payload.get("statistical_test"),
        test_assumptions=payload.get("test_assumptions"),
        effect_size=payload.get("effect_size"),
        planned_table_or_figure=payload.get("planned_table_or_figure"),
        notes=payload.get("notes"),
        approval_status=status,
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return "analysis_mapping", mapping.id


def build_offline_structure_suggestions(
    project: ResearchProject,
    user_content: str,
    special_command: str | None,
    language: str | None = None,
) -> list[SuggestionPayload]:
    """Heuristic structured suggestions when the AI provider is offline."""
    from app.i18n.lang import normalize_lang, t

    lang = normalize_lang(language or project.writing_language or "en")
    items: list[SuggestionPayload] = []
    cmd = (special_command or user_content or "").lower()
    # Arabic command synonyms
    if any(x in cmd for x in ("أسئلة", "سؤال بحث", "build research")):
        cmd = cmd + " research question"
    if any(x in cmd for x in ("فرض", "hypothes")):
        cmd = cmd + " hypothesis"
    if any(x in cmd for x in ("منهجي", "تصميم", "methodolog", "design")):
        cmd = cmd + " methodology"
    if any(x in cmd for x in ("استبيان", "أداة", "questionnaire", "instrument")):
        cmd = cmd + " questionnaire"
    if any(x in cmd for x in ("تحليل", "analysis plan")):
        cmd = cmd + " analysis plan"

    title = project.working_title
    pop = project.population_summary or ("[المجتمع]" if lang == "ar" else "[population]")
    field = project.research_field or ("المجال" if lang == "ar" else "the field")

    if "research question" in cmd or "build research questions" in cmd:
        items.append(
            SuggestionPayload(
                type="research_question",
                title=t(lang, "sug.rq_title"),
                rationale=t(lang, "integrity.offline_draft"),
                payload={
                    "text": t(lang, "sug.rq_text", title=title, pop=pop),
                    "question_type": "descriptive",
                    "proposed_analysis": t(lang, "sug.rq_analysis"),
                },
            )
        )
        items.append(
            SuggestionPayload(
                type="objective",
                title=t(lang, "sug.obj_title"),
                rationale=t(lang, "sug.obj_rationale"),
                payload={
                    "text": t(lang, "sug.obj_text", title=title, pop=pop),
                    "verb": "Describe" if lang == "en" else "وصف",
                },
            )
        )
    if "hypothes" in cmd:
        items.append(
            SuggestionPayload(
                type="hypothesis",
                title=t(lang, "sug.hyp_title"),
                rationale=t(lang, "integrity.offline_hyp"),
                payload={
                    "null_hypothesis": t(lang, "sug.h0"),
                    "alternative_hypothesis": t(lang, "sug.h1"),
                    "direction": "non_directional",
                    "independent_variable": t(lang, "sug.iv"),
                    "dependent_variable": t(lang, "sug.dv"),
                    "theoretical_basis": t(lang, "sug.theory"),
                    "proposed_test": t(lang, "sug.test"),
                },
            )
        )
    if "methodolog" in cmd or "design" in cmd:
        items.append(
            SuggestionPayload(
                type="design",
                title=t(lang, "sug.design_title"),
                rationale=t(lang, "integrity.offline_design"),
                payload={
                    "design_type": t(lang, "sug.design_type"),
                    "paradigm": "quantitative",
                    "rationale": t(lang, "sug.design_rationale", title=title, field=field),
                    "strengths": t(lang, "sug.design_strengths"),
                    "limitations": t(lang, "sug.design_limits"),
                    "bias_risks": t(lang, "sug.design_bias"),
                    "is_primary": True,
                },
            )
        )
    if "questionnaire" in cmd or "instrument" in cmd:
        items.append(
            SuggestionPayload(
                type="instrument_item",
                title=t(lang, "sug.item_title"),
                payload={
                    "instrument_name": "Primary questionnaire" if lang == "en" else "الاستبيان الأساسي",
                    "section_title": "Main constructs" if lang == "en" else "المفاهيم الرئيسية",
                    "item_text": t(lang, "sug.item_text"),
                    "response_type": "likert",
                    "response_options": (
                        "1=Strongly disagree … 5=Strongly agree"
                        if lang == "en"
                        else "1=لا أوافق بشدة … 5=أوافق بشدة"
                    ),
                    "construct_name": "[Construct]" if lang == "en" else "[المفهوم]",
                    "variable_name": "[Variable]" if lang == "en" else "[المتغير]",
                },
            )
        )
    if "analysis plan" in cmd:
        items.append(
            SuggestionPayload(
                type="analysis_mapping",
                title=t(lang, "sug.analysis_title"),
                payload={
                    "statistical_test": t(lang, "sug.analysis_test"),
                    "descriptive_stats": t(lang, "sug.analysis_desc"),
                    "data_type": t(lang, "sug.analysis_dtype"),
                    "variables": t(lang, "sug.analysis_vars"),
                    "test_assumptions": t(lang, "sug.analysis_assumptions"),
                },
            )
        )
    if "profile" in cmd or not items:
        if not (project.profile and project.profile.overall_aim):
            items.append(
                SuggestionPayload(
                    type="profile_field",
                    title=t(lang, "sug.aim_title"),
                    payload={
                        "field": "overall_aim",
                        "value": t(lang, "sug.aim_value", title=title, pop=pop, field=field),
                    },
                    rationale=t(lang, "sug.aim_rationale"),
                )
            )
    return items[:8]
