"""No secrets are returned by administration APIs or cached in browser storage."""
import base64
import hashlib
from dataclasses import dataclass, field
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from app.config import get_settings
from app.database import SessionLocal
from app.models.ai_configuration import AIConfiguration

PROVIDERS = {
    'openai': {'name': 'OpenAI', 'base_url': 'https://api.openai.com/v1', 'protocol': 'responses', 'docs': 'https://developers.openai.com/api/docs/models'},
    'anthropic': {'name': 'Anthropic · Claude', 'base_url': 'https://api.anthropic.com/v1', 'protocol': 'anthropic', 'docs': 'https://platform.claude.com/docs/en/about-claude/models/overview'},
    'gemini': {'name': 'Google · Gemini', 'base_url': 'https://generativelanguage.googleapis.com/v1beta/openai', 'protocol': 'chat', 'docs': 'https://ai.google.dev/gemini-api/docs/models'},
    'xai': {'name': 'xAI · Grok', 'base_url': 'https://api.x.ai/v1', 'protocol': 'chat', 'docs': 'https://docs.x.ai/developers/models'},
    'deepseek': {'name': 'DeepSeek', 'base_url': 'https://api.deepseek.com', 'protocol': 'chat', 'docs': 'https://api-docs.deepseek.com/'},
    'mistral': {'name': 'Mistral AI', 'base_url': 'https://api.mistral.ai/v1', 'protocol': 'chat', 'docs': 'https://docs.mistral.ai/models/'},
}


@dataclass
class Profile:
    purpose: str
    provider: str
    model: str
    key: str = field(repr=False)
    max_output_tokens: int = 8192
    version: int = 0
    use_environment: bool = True
    base_url: str = ''


def cipher():
    secret = get_settings().secret_key
    if len(secret) < 24 or secret.startswith('change-me') or secret.startswith('replace-with'):
        raise HTTPException(503, 'AI_KEY_STORAGE: Configure a strong server SECRET_KEY before saving API keys.')
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(('researchguide-ai-v1:' + secret).encode()).digest()))


def decrypt(value):
    if not value:
        return ''
    try:
        return cipher().decrypt(value.encode()).decode()
    except InvalidToken:
        raise HTTPException(503, 'AI_KEY_STORAGE: The saved key cannot be decrypted. Re-enter it using the current server secret.') from None


def environment(purpose):
    cfg = get_settings()
    provider = cfg.ai_provider if cfg.ai_provider in PROVIDERS else 'xai'
    return Profile(purpose, provider, cfg.ai_model, cfg.xai_api_key,
                   8192 if purpose == 'analysis' else 4096, base_url=cfg.xai_base_url.rstrip('/'))


def load(purpose, db=None):
    if db is None:
        with SessionLocal() as session:
            return load(purpose, session)
    row = db.get(AIConfiguration, purpose)
    if row is None:
        return environment(purpose)
    key = environment(purpose).key if row.use_environment else decrypt(row.encrypted_key)
    base = environment(purpose).base_url if row.use_environment else PROVIDERS[row.provider]['base_url']
    return Profile(purpose, row.provider, row.model, key, row.max_output_tokens, row.version, bool(row.use_environment), base)


def public(profile):
    return {k: getattr(profile, k) for k in ('purpose', 'provider', 'model', 'max_output_tokens', 'version', 'use_environment')} | {'has_key': bool(profile.key)}


def candidate(purpose, payload, db, require_model=True):
    current = load(purpose, db)
    if payload.use_environment and payload.provider != environment(purpose).provider:
        raise HTTPException(422, 'The deployment key can only be used with its original provider.')
    key = payload.api_key.get_secret_value().strip() if payload.api_key else ''
    if key and (len(key) > 4096 or any(c.isspace() for c in key)):
        raise HTTPException(422, 'API key format is invalid.')
    if payload.use_environment:
        key = environment(purpose).key
    elif not key and current.provider == payload.provider and not current.use_environment:
        key = current.key
    if not key:
        raise HTTPException(422, 'AI_KEY_REQUIRED: Enter a key belonging to the selected provider.')
    if require_model and not payload.model:
        raise HTTPException(422, 'Select or enter a model identifier.')
    return Profile(purpose, payload.provider, payload.model, key, payload.max_output_tokens, current.version,
                   payload.use_environment, environment(purpose).base_url if payload.use_environment else PROVIDERS[payload.provider]['base_url'])


def save(purpose, payload, db):
    profile = candidate(purpose, payload, db)
    if payload.version != profile.version:
        raise HTTPException(409, 'AI_SETTINGS_CHANGED: Reload settings before saving; another administrator changed this profile.')
    values = dict(provider=profile.provider, model=profile.model, max_output_tokens=profile.max_output_tokens,
                  use_environment=int(profile.use_environment),
                  encrypted_key=None if profile.use_environment else cipher().encrypt(profile.key.encode()).decode(),
                  version=profile.version + 1)
    try:
        if profile.version == 0:
            db.add(AIConfiguration(purpose=purpose, **values))
        else:
            result = db.execute(update(AIConfiguration).where(AIConfiguration.purpose == purpose, AIConfiguration.version == profile.version).values(**values))
            if result.rowcount != 1:
                db.rollback()
                raise HTTPException(409, 'AI_SETTINGS_CHANGED: Reload settings before saving.')
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'AI_SETTINGS_CHANGED: Reload settings before saving.') from None
    db.expire_all()
    return public(load(purpose, db))
