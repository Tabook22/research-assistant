"""AI conversation routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user
from app.database import get_db
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.schemas.chat import ChatMessageCreate, ChatResponse, ConversationOut, MessageOut
from app.schemas.suggestions import AISuggestionOut
from app.services.access import get_project_for_user
from app.services.ai_service import ensure_welcome_message, generate_assistant_reply

router = APIRouter(prefix="/projects/{project_id}/chat", tags=["chat"])


def _get_or_create_conversation(db: Session, project_id: int, stage_key: str | None) -> Conversation:
    conv = (
        db.query(Conversation)
        .filter(Conversation.project_id == project_id, Conversation.is_active.is_(True))
        .order_by(Conversation.id.desc())
        .first()
    )
    if not conv:
        conv = Conversation(
            project_id=project_id,
            title="Research guidance",
            stage_key=stage_key,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
    return conv


@router.get("/conversation", response_model=ConversationOut)
async def get_conversation(
    project_id: int,
    language: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConversationOut:
    project = get_project_for_user(db, project_id, user)
    conv = _get_or_create_conversation(db, project_id, project.current_stage)
    lang = language or user.preferred_language or project.writing_language
    await ensure_welcome_message(db, project, conv, language=lang)
    full = (
        db.query(Conversation)
        .options(joinedload(Conversation.messages))
        .filter(Conversation.id == conv.id)
        .first()
    )
    return ConversationOut.model_validate(full)


@router.post("/messages", response_model=ChatResponse)
async def post_message(
    project_id: int,
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatResponse:
    project = get_project_for_user(db, project_id, user)
    conv = _get_or_create_conversation(db, project_id, payload.stage_key or project.current_stage)
    lang = payload.language or user.preferred_language or project.writing_language
    await ensure_welcome_message(db, project, conv, language=lang)

    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=payload.content,
        stage_key=payload.stage_key or project.current_stage,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    text, suggestion_dicts, warnings = await generate_assistant_reply(
        db,
        project,
        conv,
        payload.content,
        stage_key=payload.stage_key,
        special_command=payload.special_command,
        language=lang,
    )

    import json

    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=text,
        stage_key=payload.stage_key or project.current_stage,
        structured_json=json.dumps(suggestion_dicts, ensure_ascii=False, default=str)
        if suggestion_dicts
        else None,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return ChatResponse(
        conversation_id=conv.id,
        user_message=MessageOut.model_validate(user_msg),
        assistant_message=MessageOut.model_validate(assistant_msg),
        profile_suggestions=None,
        suggestions=[AISuggestionOut(**s) for s in suggestion_dicts],
        integrity_warnings=warnings,
    )
