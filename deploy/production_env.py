"""Emit the required VPS environment to an SSH stdin pipe, never to a log/file.

The caller must pipe stdout directly to the user's authenticated VPS.
"""
import json
from app.config import get_settings

cfg = get_settings()
values = {
    'XAI_API_KEY': cfg.xai_api_key, 'XAI_BASE_URL': cfg.xai_base_url,
    'AI_MODEL': cfg.ai_model, 'AI_PROVIDER': cfg.ai_provider,
}
print(json.dumps(values, ensure_ascii=True))
