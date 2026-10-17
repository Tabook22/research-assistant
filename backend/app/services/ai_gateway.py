"""Task routing with native OpenAI Responses / Claude Messages and compatible chat APIs."""
import json
import logging
from types import SimpleNamespace
import httpx
from fastapi import HTTPException
from app.services.ai_configuration import PROVIDERS, load


logger = logging.getLogger(__name__)


def provider_error(status, data=None):
    if status == 429:
        error = data.get('error', {}) if isinstance(data, dict) else {}
        error = error if isinstance(error, dict) else {}
        code, kind = error.get('code'), error.get('type')
        if code == 'credit_balance_exhausted':
            return HTTPException(429, 'AI_CREDIT_BALANCE: Provider API credits are exhausted. Administrator must add credits to the API billing account before retrying.')
        if code in ('organization_spend_limit_exceeded', 'project_spend_limit_exceeded'):
            return HTTPException(429, 'AI_SPEND_LIMIT: Provider spending ceiling reached. Administrator must check organization or project spending limits.')
        if code == 'organization_usage_limit_exceeded':
            return HTTPException(429, 'AI_USAGE_LIMIT: Provider approved usage ceiling reached. Administrator must request a higher usage limit.')
        if code == 'insufficient_quota' or kind == 'insufficient_quota':
            return HTTPException(429, 'AI_QUOTA: Provider API quota is exhausted. Administrator must check API billing and usage limits before retrying.')
        return HTTPException(429, 'AI_RATE_LIMIT: Provider request or token rate limit reached. Wait before retrying; shorten the request if it persists.')
    if status in (401, 403):
        return HTTPException(503, 'AI_ACCESS: Provider rejected the API key or model access.')
    if status in (400, 404, 422):
        return HTTPException(502, 'AI_CONFIGURATION: Model or request is unsupported. Check the selected model and output limit.')
    return HTTPException(502, 'AI_RESPONSE: The provider could not complete the request.')


async def exchange(profile, method, path, *, body=None, params=None):
    headers = {'Authorization': 'Bearer ' + profile.key}
    if profile.provider == 'anthropic':
        headers = {'x-api-key': profile.key, 'anthropic-version': '2023-06-01'}
    try:
        async with httpx.AsyncClient(timeout=150 if profile.purpose == 'images' else 120, follow_redirects=False) as client:
            response = await client.request(method, profile.base_url + path, headers=headers, json=body, params=params)
        if not 200 <= response.status_code < 300:
            try:
                data = response.json()
            except ValueError:
                data = None
            error = provider_error(response.status_code, data)
            # Log our own category only: upstream messages may echo keys or research text.
            logger.warning('AI provider rejected request: status=%s category=%s', response.status_code, error.detail.split(':', 1)[0])
            retry_after = response.headers.get('retry-after', '')
            if error.detail.startswith('AI_RATE_LIMIT:') and retry_after.isascii() and retry_after.isdigit() and len(retry_after) <= 6:
                error.headers = {'Retry-After': retry_after}
            raise error
        return response.json()
    except httpx.TimeoutException:
        raise HTTPException(504, 'AI_TIMEOUT: Provider request timed out. Saved progress is preserved.') from None
    except httpx.RequestError:
        raise HTTPException(502, 'AI_CONNECTION: Cannot connect to the selected provider.') from None
    except ValueError:
        raise HTTPException(502, 'AI_RESPONSE: Provider returned invalid JSON.') from None


async def complete(profile, messages, json_output=False, max_tokens=None, response_schema=None):
    if not profile.key:
        raise HTTPException(503, 'AI assistance is not configured. Ask the administrator to configure the task profile.')
    messages = [dict(message) for message in messages]
    if json_output:
        messages.insert(0, {'role': 'system', 'content': 'Return only a valid JSON object, without Markdown fences.'})
    limit = max_tokens or profile.max_output_tokens
    protocol = PROVIDERS[profile.provider]['protocol']
    if protocol == 'responses':
        body = {'model': profile.model, 'input': messages, 'max_output_tokens': limit, 'store': False}
        if json_output:
            body['text'] = {'format': ({'type':'json_schema', 'name':'scientific_presentation',
                                       'strict':True, 'schema':response_schema}
                                      if response_schema is not None else {'type':'json_object'})}
        data = await exchange(profile, 'POST', '/responses', body=body)
        if data.get('status') == 'incomplete' and (data.get('incomplete_details') or {}).get('reason') == 'max_output_tokens':
            logger.warning('AI response incomplete: category=AI_OUTPUT_LIMIT')
            raise HTTPException(502, 'AI_OUTPUT_LIMIT: Provider output budget exhausted. Increase the analysis output token limit or use fewer slides. Saved work is preserved.')
        if any(part.get('type') == 'refusal' for item in data.get('output', [])
               for part in item.get('content', [])):
            raise HTTPException(502, 'AI_REFUSAL: The provider declined this request. Review the requested scope; saved work is preserved.')
        text = ''.join(part.get('text', '') for item in data.get('output', []) if item.get('type') == 'message'
                       for part in item.get('content', []) if part.get('type') == 'output_text')
        finished = data.get('status') == 'completed'
    elif protocol == 'anthropic':
        system = '\n\n'.join(m['content'] for m in messages if m['role'] in ('system', 'developer'))
        conversation = [m for m in messages if m['role'] in ('user', 'assistant')]
        data = await exchange(profile, 'POST', '/messages', body={'model': profile.model, 'max_tokens': limit,
                              'system': system, 'messages': conversation})
        text = ''.join(part.get('text', '') for part in data.get('content', []) if part.get('type') == 'text')
        finished = data.get('stop_reason') in ('end_turn', 'stop_sequence')
    else:
        body = {'model': profile.model, 'messages': messages, 'max_tokens': limit}
        if json_output:
            body['response_format'] = {'type': 'json_object'}
        data = await exchange(profile, 'POST', '/chat/completions', body=body)
        choice = (data.get('choices') or [{}])[0]
        text = choice.get('message', {}).get('content') or ''
        finished = choice.get('finish_reason') == 'stop'
    if not finished or not isinstance(text, str) or not text.strip():
        raise HTTPException(502, 'AI_RESPONSE: Provider response was incomplete, refused or empty. Saved work is preserved.')
    return text


class TaskClient:
    """Small adapter for existing text-only chat call sites; model always comes from the selected profile."""
    def __init__(self, profile):
        self.profile = profile
        self.model = profile.model
        self.chat = SimpleNamespace(completions=self)

    async def create(self, *, messages, response_format=None, **_):
        schema = response_format.get('json_schema', {}).get('schema') if response_format and response_format.get('type') == 'json_schema' else None
        text = await complete(self.profile, messages, bool(response_format), response_schema=schema)
        return SimpleNamespace(model=self.profile.model, choices=[SimpleNamespace(message=SimpleNamespace(content=text), finish_reason='stop')])


def task_client(purpose='analysis'):
    profile = load(purpose)
    return TaskClient(profile) if profile.key else None


async def models(profile):
    """Fetch current account-visible versions. Never label an arbitrary hard-coded name as latest."""
    found = {}
    params = {'limit': 100} if profile.provider == 'anthropic' else None
    for _ in range(20):
        data = await exchange(profile, 'GET', '/models', params=params)
        items = data if isinstance(data, list) else data.get('data', [])
        for item in items:
            ident = item.get('id', '')
            if not isinstance(ident, str) or not ident:
                continue
            if profile.purpose == 'images':
                if ident.startswith('gpt-image-'):
                    found[ident] = {'id': ident, 'name': ident, 'created': item.get('created')}
                continue
            if item.get('capabilities', {}).get('completion_chat') is False:
                continue
            if any(term in ident.lower() for term in ('embed', 'moderation', 'tts-', 'whisper', 'dall-e', 'image-', 'realtime', 'transcribe', 'sora', 'audio')):
                continue
            found[ident] = {'id': ident, 'name': item.get('display_name') or item.get('name') or ident,
                            'created': item.get('created_at') or item.get('created')}
        if not isinstance(data, dict) or not data.get('has_more'):
            return sorted(found.values(), key=lambda item: item['id'])
        last = data.get('last_id')
        if not last:
            raise HTTPException(502, 'AI_RESPONSE: Model catalogue pagination was incomplete.')
        params = {'limit': 100, 'after_id' if profile.provider == 'anthropic' else 'after': last}
    raise HTTPException(502, 'AI_RESPONSE: Model catalogue exceeded the pagination limit. Enter a model identifier manually.')
