"""General on-demand translation for chat, suggestions, and stage analyses."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user
from app.i18n.lang import normalize_lang, t
from app.models.user import User
from app.schemas.translate import TranslateTextOut, TranslateTextRequest
from app.services.library_ai_service import _ai_translate_map, _looks_latin_heavy

router = APIRouter(prefix="/translate", tags=["translate"])


def _arabic_ratio(text: str) -> float:
    letters = re.findall(r"[A-Za-z\u0600-\u06FF]", text or "")
    if not letters:
        return 0.0
    ar = sum(1 for c in letters if "\u0600" <= c <= "\u06FF")
    return ar / max(len(letters), 1)


@router.post("/text", response_model=TranslateTextOut)
async def translate_text(
    payload: TranslateTextRequest,
    user: User = Depends(get_current_user),
) -> TranslateTextOut:
    """
    Translate a single free-text block to Arabic (chat message, suggestion, issue, etc.).
    Display-only — does not persist.
    """
    _ = user  # auth required
    target = normalize_lang(payload.target_language or "ar")
    if target != "ar":
        raise HTTPException(status_code=400, detail="Only target_language=ar is supported")

    original = (payload.text or "").strip()
    if not original:
        raise HTTPException(status_code=400, detail="Empty text")

    # Already mostly Arabic → return as-is with clear message
    if _arabic_ratio(original) >= 0.45 and not _looks_latin_heavy(original, min_latin=40):
        return TranslateTextOut(
            original=original,
            translated=original,
            target_language="ar",
            used_service=False,
            message=t("ar", "translate.already_ar"),
        )

    translated_map, used, note = await _ai_translate_map({"t0": original}, "ar")
    translated = (translated_map.get("t0") or "").strip()

    if not translated or (
        translated == original and _looks_latin_heavy(original, min_latin=12)
    ):
        raise HTTPException(
            status_code=502,
            detail=t("ar", "translate.failed_service"),
        )

    if _arabic_ratio(translated) < 0.2 and _looks_latin_heavy(original, min_latin=12):
        raise HTTPException(
            status_code=502,
            detail=t("ar", "translate.failed_service"),
        )

    return TranslateTextOut(
        original=original,
        translated=translated,
        target_language="ar",
        used_service=bool(used),
        message=note or t("ar", "translate.ok"),
    )
