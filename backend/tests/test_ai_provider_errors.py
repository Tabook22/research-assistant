"""Provider failures must distinguish billing from throttling without leaking payloads."""
import logging
import httpx
import pytest
from fastapi import HTTPException
from app.services import ai_gateway as gateway
from app.services.ai_configuration import Profile


@pytest.mark.asyncio
@pytest.mark.parametrize('code,kind,category', [
    ('credit_balance_exhausted', 'insufficient_quota', 'AI_CREDIT_BALANCE'),
    ('project_spend_limit_exceeded', 'insufficient_quota', 'AI_SPEND_LIMIT'),
    ('organization_spend_limit_exceeded', 'insufficient_quota', 'AI_SPEND_LIMIT'),
    ('organization_usage_limit_exceeded', 'insufficient_quota', 'AI_USAGE_LIMIT'),
    ('insufficient_quota', None, 'AI_QUOTA'),
    (None, 'insufficient_quota', 'AI_QUOTA'),
    ('rate_limit_exceeded', 'tokens', 'AI_RATE_LIMIT'),
    ('slow_down', 'rate_limit_error', 'AI_RATE_LIMIT'),
])
async def test_provider_categories_are_safe_and_not_retried(monkeypatch, caplog, code, kind, category):
    original = httpx.AsyncClient
    calls = []
    secret = 'private-key-and-manuscript-never-log'
    def respond(request):
        calls.append(request)
        return httpx.Response(429, headers={'retry-after': '20'}, json={
            'error': {'code': code, 'type': kind, 'message': secret}})
    monkeypatch.setattr(gateway.httpx, 'AsyncClient', lambda **kw: original(transport=httpx.MockTransport(respond), **kw))
    profile = Profile('discussion', 'openai', 'test', secret, base_url='https://api.openai.com/v1')
    with caplog.at_level(logging.WARNING), pytest.raises(HTTPException) as exc:
        await gateway.exchange(profile, 'POST', '/responses', body={'input': secret})
    assert exc.value.status_code == 429
    assert exc.value.detail.startswith(category + ':')
    assert secret not in exc.value.detail + caplog.text
    assert category in caplog.text and len(calls) == 1
    assert exc.value.headers == ({'Retry-After': '20'} if category == 'AI_RATE_LIMIT' else None)


@pytest.mark.parametrize('data', [None, [], {'error': 'private'}, {'error': None}])
def test_unstructured_error_is_safe(data):
    error = gateway.provider_error(429, data)
    assert error.detail.startswith('AI_RATE_LIMIT:')
    assert gateway.provider_error(403, data).detail.startswith('AI_ACCESS:')
