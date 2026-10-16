"""AI orchestration via SpaceXAI / xAI (OpenAI-compatible API)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.services.ai_gateway import task_client
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.conversation import Conversation, Message
from app.models.decisions import AISuggestion
from app.models.project import ResearchProject
from app.i18n.lang import normalize_lang, t
from app.services.project_service import build_profile_context
from app.services.suggestion_service import (
    build_offline_structure_suggestions,
    persist_suggestions,
    strip_and_parse_suggestions,
    suggestion_to_dict,
)

logger = logging.getLogger(__name__)
settings = get_settings()

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "master_system_prompt.txt"


def load_master_prompt() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return (
        "You are ResearchGuide AI, a scientific research supervisor. "
        "Never invent references, data, or results. Guide step by step."
    )


def _client():
    return task_client("discussion")


def build_context_layers(
    project: ResearchProject,
    stage_key: str | None,
    extra_notes: str | None = None,
) -> str:
    profile = build_profile_context(project)
    layers = {
        "current_stage": stage_key or project.current_stage,
        "research_project_profile": profile,
        "document_type": project.document_type,
        "writing_language": project.writing_language,
        "integrity_reminder": (
            "Never invent references, data, results, or DOIs. "
            "Never auto-approve profile changes. Mark provisional content clearly."
        ),
    }
    if extra_notes:
        layers["additional_context"] = extra_notes
    return json.dumps(layers, ensure_ascii=False, indent=2)


SPECIAL_COMMANDS = {
    "start a new project": "The researcher invoked: Start a new project. Begin initial diagnostic questions.",
    "show research profile": "The researcher invoked: Show research profile. Display the current Research Project Profile clearly.",
    "check alignment": "The researcher invoked: Check alignment. Audit the research-consistency chain and list mismatches.",
    "find similar studies": "The researcher invoked: Find similar studies. Construct systematic search queries; do not invent results.",
    "build research questions": "The researcher invoked: Build research questions from the problem and gap.",
    "build hypotheses": "The researcher invoked: Determine if hypotheses are appropriate and formulate them if so.",
    "design methodology": "The researcher invoked: Design methodology. Recommend and compare suitable designs.",
    "build questionnaire": "The researcher invoked: Build questionnaire only if objectives, variables, and population are confirmed; otherwise ask first.",
    "create analysis plan": "The researcher invoked: Create analysis plan mapping every question/hypothesis to a method.",
    "review my paper": "The researcher invoked: Review my paper for structure, logic, methodology, evidence, and consistency.",
    "journal readiness check": "The researcher invoked: Journal readiness check against target journal guidelines when known.",
    "export project summary": "The researcher invoked: Export project summary of all approved decisions.",
}


STRUCTURED_OUTPUT_INSTRUCTION = """
When you propose concrete research elements the researcher could add to the project
(questions, objectives, hypotheses, variables, design, population, sampling, instrument items,
analysis mappings, or profile fields), ALSO append a machine-readable block at the VERY END:

---SUGGESTIONS_JSON---
{
  "suggestions": [
    {
      "type": "research_question",
      "title": "Short label",
      "rationale": "Why this is proposed",
      "payload": { "text": "...", "question_type": "descriptive", "proposed_analysis": "..." }
    }
  ]
}
---END_SUGGESTIONS---

Allowed types: profile_field, research_question, objective, hypothesis, variable, design,
population, sampling, instrument_item, analysis_mapping.

payload rules:
- profile_field: {"field":"overall_aim|research_problem|research_gap|...","value":"..."}
- research_question: {"text","question_type","proposed_analysis?"}
- objective: {"text","verb?","question_id?"}
- hypothesis: {"null_hypothesis","alternative_hypothesis","direction","independent_variable?","dependent_variable?","theoretical_basis?","proposed_test?","question_id?"}
- variable: {"name","role","measurement_scale?","operational_definition?","measurement_method?"}
- design: {"design_type","paradigm?","rationale?","strengths?","limitations?","bias_risks?"}
- population: {"target_population","accessible_population?","unit_of_analysis?","inclusion_criteria?","exclusion_criteria?"}
- sampling: {"sampling_method?","sample_size?","sample_size_rationale?","assumptions?"} — never invent a sample size without rationale
- instrument_item: {"item_text","instrument_name?","section_title?","response_type?","construct_name?","variable_name?"}
- analysis_mapping: {"statistical_test?","variables?","data_type?","question_id?","descriptive_stats?"}

Never auto-apply. Mark drafts as provisional. Do not invent references, DOIs, or results.
If you have no structured proposals, omit the SUGGESTIONS_JSON block entirely.
Keep the human-readable answer complete BEFORE the block.
"""


async def generate_assistant_reply(
    db: Session,
    project: ResearchProject,
    conversation: Conversation,
    user_content: str,
    stage_key: str | None = None,
    special_command: str | None = None,
    language: str | None = None,
) -> tuple[str, list[dict[str, Any]], list[str]]:
    """
    Returns (assistant_text, suggestion_dicts, integrity_warnings).
    Suggestions are stored as proposed and never auto-applied to project structure.
    `language` is UI/response language (en|ar); defaults to project.writing_language.
    """
    lang = normalize_lang(language or project.writing_language or "en")
    integrity_warnings: list[str] = []
    cmd_note = None
    if special_command:
        key = special_command.strip().lower()
        cmd_note = SPECIAL_COMMANDS.get(key, f"Special command: {special_command}")

    if "invent references" in user_content.lower() or "fake citation" in user_content.lower():
        integrity_warnings.append(t(lang, "chat.fabricate_warn"))

    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.id.desc())
        .limit(settings.ai_max_context_messages)
        .all()
    )
    history = list(reversed(history))

    client = _client()
    stage = stage_key or project.current_stage
    suggestion_rows: list[AISuggestion] = []

    if client is None:
        text = _offline_reply(project, user_content, stage_key, cmd_note, lang)
        offline_items = build_offline_structure_suggestions(
            project, user_content, special_command, language=lang
        )
        if offline_items:
            suggestion_rows = persist_suggestions(db, project, stage, offline_items)
            integrity_warnings.append(t(lang, "chat.offline_cards"))
        else:
            integrity_warnings.append(t(lang, "chat.offline_warning"))
        return text, [suggestion_to_dict(s) for s in suggestion_rows], integrity_warnings

    system = load_master_prompt()
    context_block = build_context_layers(project, stage_key, cmd_note)
    lang_rule = t(lang, "chat.lang_instruction")
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system},
        {"role": "system", "content": lang_rule},
        {"role": "system", "content": STRUCTURED_OUTPUT_INSTRUCTION},
        {
            "role": "system",
            "content": (
                "PROJECT CONTEXT (structured; do not treat AI suggestions as approved):\n"
                + context_block
                + f"\nresponse_language: {lang}"
            ),
        },
    ]
    for m in history:
        if m.role in ("user", "assistant"):
            messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": user_content})

    try:
        response = await client.chat.completions.create(
            model=settings.ai_model,
            messages=messages,
            temperature=0.4,
        )
        raw_text = response.choices[0].message.content or ""
    except Exception as exc:  # noqa: BLE001
        logger.warning("AI request failed: type=%s", type(exc).__name__)
        raw_text = (
            (
                f"تعذّر الوصول إلى مزوّد الذكاء الاصطناعي. الخطأ: {exc.__class__.__name__}.\n\n"
                if lang == "ar"
                else f"I could not reach the AI provider. Error: {exc.__class__.__name__}.\n\n"
            )
            + _offline_reply(project, user_content, stage_key, cmd_note, lang)
        )
        integrity_warnings.append(t(lang, "chat.ai_failed"))
        offline_items = build_offline_structure_suggestions(
            project, user_content, special_command, language=lang
        )
        if offline_items:
            suggestion_rows = persist_suggestions(db, project, stage, offline_items)

    text, parsed = strip_and_parse_suggestions(raw_text)
    if parsed:
        suggestion_rows = persist_suggestions(db, project, stage, parsed, parent_content=None)
    elif text.strip() and not suggestion_rows:
        suggestion_rows = persist_suggestions(db, project, stage, [], parent_content=text)

    return text, [suggestion_to_dict(s) for s in suggestion_rows if s.suggestion_type != "chat_response"], integrity_warnings


def _offline_reply(
    project: ResearchProject,
    user_content: str,
    stage_key: str | None,
    cmd_note: str | None,
    language: str | None = None,
) -> str:
    lang = normalize_lang(language or project.writing_language or "en")
    stage = stage_key or project.current_stage
    profile = build_profile_context(project)
    lower = user_content.lower()
    missing = "[يلزم إدخال الباحث]" if lang == "ar" else "[RESEARCHER INPUT REQUIRED]"

    if "show research profile" in lower or (cmd_note and "Show research profile" in (cmd_note or "")):
        lines = [t(lang, "chat.profile_header")]
        for k, v in profile.items():
            lines.append(f"- **{k}**: {v if v else missing}")
        lines.append(t(lang, "chat.profile_footer", stage=stage))
        return "\n".join(lines)

    if not any(profile.get(k) for k in ("refined_idea", "research_problem", "overall_aim")):
        return t(lang, "chat.welcome") + t(
            lang,
            "chat.welcome_project",
            title=project.working_title,
            field=project.research_field or t(lang, "chat.field_not_set"),
            doc_type=project.document_type,
        )

    return t(
        lang,
        "chat.offline_body",
        stage=stage,
        user=user_content[:500],
        title=project.working_title,
        cmd=cmd_note or "",
    ).strip()


async def ensure_welcome_message(
    db: Session,
    project: ResearchProject,
    conversation: Conversation,
    language: str | None = None,
) -> Message | None:
    existing = (
        db.query(Message).filter(Message.conversation_id == conversation.id).first()
    )
    if existing:
        return None
    lang = normalize_lang(language or project.writing_language or "en")
    content = t(lang, "chat.welcome")
    msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=content,
        stage_key=project.current_stage,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
