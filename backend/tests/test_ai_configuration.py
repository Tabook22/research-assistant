"""Task isolation, secret handling, administrator access and provider wire contracts."""
import json
from types import SimpleNamespace
import pytest
import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.config import get_settings
from app.database import SessionLocal
from app.models.ai_configuration import AIConfiguration
from app.services import ai_configuration as config, ai_gateway as gateway
from app.services import paper_review_service as papers
from test_user_access import admin, managed

client = TestClient(app)
KEY = 'synthetic-provider-credential-for-unit-tests'


@pytest.fixture(autouse=True)
def isolated_profiles(monkeypatch):
    monkeypatch.setattr(get_settings(), 'secret_key', 'Synthetic-only-encryption-secret-123456789')
    with SessionLocal() as db:
        db.query(AIConfiguration).delete(); db.commit()
    yield
    with SessionLocal() as db:
        db.query(AIConfiguration).delete(); db.commit()


def payload(provider='openai', model='synthetic-model', **extra):
    return dict(provider=provider, model=model, api_key=KEY, version=0, max_output_tokens=8192, **extra)


def test_admin_only_endpoints_and_no_secret_fields():
    headers, _ = admin()
    ordinary, _ = managed(headers)
    assert client.get('/api/admin/ai').status_code == 401
    for path, method in [('', 'get'), ('/analysis','put'), ('/analysis/test','post'), ('/analysis/models','post')]:
        args = {} if method == 'get' else {'json': payload()}
        assert getattr(client, method)('/api/admin/ai'+path, headers=ordinary, **args).status_code == 403
    response = client.get('/api/admin/ai', headers=headers)
    assert response.status_code == 200
    assert len(response.json()['providers']) == 6
    assert all('api_key' not in profile and 'encrypted_key' not in profile for profile in response.json()['profiles'])


def test_encrypted_keys_are_write_only_and_profiles_are_independent():
    headers, _ = admin()
    response = client.put('/api/admin/ai/analysis', headers=headers, json=payload())
    assert response.status_code == 200, response.text
    assert KEY not in response.text and response.json()['has_key']
    with SessionLocal() as db:
        row = db.get(AIConfiguration, 'analysis')
        assert row.encrypted_key and KEY not in row.encrypted_key
        assert config.load('analysis', db).key == KEY
        assert config.load('discussion', db).version == 0
    current = response.json()
    edited = {k:v for k,v in current.items() if k not in ('purpose','has_key')}
    edited['model'] = 'synthetic-model-v2'
    saved = client.put('/api/admin/ai/analysis', headers=headers, json=edited)
    assert saved.status_code == 200 and config.load('analysis').key == KEY
    assert client.put('/api/admin/ai/analysis', headers=headers, json=edited).status_code == 409
    edited.update(provider='anthropic', version=2)
    assert client.put('/api/admin/ai/analysis', headers=headers, json=edited).status_code == 422
    assert config.load('analysis').provider == 'openai'


def test_deployment_key_cannot_be_sent_to_a_different_provider(monkeypatch):
    headers, _ = admin()
    monkeypatch.setattr(get_settings(), 'ai_provider', 'xai')
    monkeypatch.setattr(get_settings(), 'xai_api_key', KEY)
    data = payload(); data.pop('api_key'); data['use_environment'] = True
    assert client.put('/api/admin/ai/analysis', headers=headers, json=data).status_code == 422
    data['provider'] = 'xai'
    response = client.put('/api/admin/ai/analysis', headers=headers, json=data)
    assert response.status_code == 200 and KEY not in response.text
    with SessionLocal() as db:
        assert db.get(AIConfiguration,'analysis').encrypted_key is None
    assert config.load('analysis').key == KEY


def test_invalid_settings_and_weak_secret_never_replace_profile(monkeypatch):
    headers, _ = admin()
    assert client.put('/api/admin/ai/analysis', headers=headers, json=payload(provider='unknown')).status_code == 422
    data = payload(); data['base_url'] = 'http://127.0.0.1/private'
    assert client.put('/api/admin/ai/analysis', headers=headers, json=data).status_code == 422
    data = payload(); data['max_output_tokens'] = 100000
    assert client.put('/api/admin/ai/analysis', headers=headers, json=data).status_code == 422
    monkeypatch.setattr(get_settings(), 'secret_key', 'change-me-in-production-use-long-random-string')
    headers, _ = admin()  # Re-authenticate after intentionally changing the signing secret.
    assert client.put('/api/admin/ai/analysis', headers=headers, json=payload()).status_code == 503
    assert config.load('analysis').version == 0


@pytest.mark.asyncio
@pytest.mark.parametrize('provider', list(config.PROVIDERS))
async def test_native_protocols_and_complete_json_responses(monkeypatch, provider):
    profile = config.Profile('analysis', provider, 'synthetic-model', KEY, base_url=config.PROVIDERS[provider]['base_url'])
    async def fake(profile, method, path, *, body=None, params=None):
        assert method == 'POST' and body['model'] == 'synthetic-model'
        assert KEY not in json.dumps(body)
        assert 'temperature' not in body
        if provider == 'openai':
            assert path == '/responses' and body['store'] is False
            assert body['text']['format']['type'] == 'json_object'
            return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'{"ok":true}'}]}]}
        if provider == 'anthropic':
            assert path == '/messages' and 'system rule' in body['system']
            assert all(m['role'] != 'system' for m in body['messages'])
            assert body['max_tokens'] == 8192
            return {'stop_reason':'end_turn','content':[{'type':'text','text':'{"ok":true}'}]}
        assert path == '/chat/completions' and body['response_format']['type'] == 'json_object'
        return {'choices':[{'finish_reason':'stop','message':{'content':'{"ok":true}'}}]}
    monkeypatch.setattr(gateway, 'exchange', fake)
    text = await gateway.complete(profile, [{'role':'system','content':'system rule'},{'role':'user','content':'Synthetic question'}], True)
    assert json.loads(text)['ok']
    adapted = await gateway.TaskClient(profile).create(model='ignored-old-model',messages=[{'role':'system','content':'system rule'},{'role':'user','content':'test'}],response_format={'type':'json_object'})
    assert adapted.model == 'synthetic-model'


@pytest.mark.asyncio
async def test_incomplete_response_is_not_saved_or_silently_rerouted(monkeypatch):
    seen=[]
    async def fake(profile, *args, **kwargs):
        seen.append(profile.provider)
        return {'choices':[{'finish_reason':'length','message':{'content':'{"partial":'}}]}
    monkeypatch.setattr(gateway,'exchange',fake)
    profile=config.Profile('analysis','xai','test',KEY,base_url='https://api.x.ai/v1')
    with pytest.raises(HTTPException) as exc:
        await gateway.complete(profile,[{'role':'user','content':'test'}])
    assert exc.value.status_code==502 and seen==['xai']


@pytest.mark.asyncio
async def test_presentation_schema_reaches_native_responses_endpoint(monkeypatch):
    schema={'type':'object','properties':{'title':{'type':'string'}},'required':['title'],'additionalProperties':False}
    async def fake(profile,method,path,**kwargs):
        assert path=='/responses'
        assert kwargs['body']['text']['format']=={'type':'json_schema','name':'scientific_presentation','strict':True,'schema':schema}
        assert kwargs['body']['store'] is False
        return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'{"title":"Synthetic outline"}'}]}]}
    monkeypatch.setattr(gateway,'exchange',fake)
    profile=config.Profile('analysis','openai','synthetic-model',KEY,base_url=config.PROVIDERS['openai']['base_url'])
    result=await gateway.TaskClient(profile).create(messages=[{'role':'user','content':'Synthetic task'}],response_format={'type':'json_schema','json_schema':{'schema':schema,'strict':True}})
    assert json.loads(result.choices[0].message.content)['title']=='Synthetic outline'


@pytest.mark.asyncio
async def test_exhausted_response_budget_has_actionable_error(monkeypatch):
    async def fake(*args,**kwargs):return {'status':'incomplete','incomplete_details':{'reason':'max_output_tokens'},'output':[]}
    monkeypatch.setattr(gateway,'exchange',fake)
    profile=config.Profile('analysis','openai','synthetic-model',KEY,base_url=config.PROVIDERS['openai']['base_url'])
    with pytest.raises(HTTPException) as exc:await gateway.complete(profile,[{'role':'user','content':'Synthetic task'}],True)
    assert exc.value.detail.startswith('AI_OUTPUT_LIMIT:')


def test_discovery_and_synthetic_test_do_not_save_unsaved_credentials(monkeypatch):
    headers,_=admin();seen=[]
    async def fake(profile, method, path, **kwargs):
        seen.append((profile.provider,method,path))
        if method=='GET':return {'data':[{'id':'synthetic-v1'},{'id':'text-embedding-test'}]}
        assert 'Synthetic connection test' in json.dumps(kwargs['body'])
        return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'{"ok":true}'}]}]}
    monkeypatch.setattr(gateway,'exchange',fake)
    listed=client.post('/api/admin/ai/analysis/models',headers=headers,json=payload())
    assert listed.status_code==200 and listed.json()['models']==[{'id':'synthetic-v1','name':'synthetic-v1','created':None}]
    tested=client.post('/api/admin/ai/analysis/test',headers=headers,json=payload())
    assert tested.status_code==200 and tested.json()['ok'] and KEY not in tested.text
    assert config.load('analysis').version==0
    assert seen==[('openai','GET','/models'),('openai','POST','/responses')]


@pytest.mark.asyncio
async def test_anthropic_model_pagination(monkeypatch):
    profile=config.Profile('analysis','anthropic','test',KEY,base_url='https://api.anthropic.com/v1')
    calls=[]
    async def fake(profile,method,path,**kwargs):
        calls.append(kwargs['params'])
        return {'data':[{'id':'claude-test-1'}],'has_more':len(calls)==1,'last_id':'claude-test-1'}
    monkeypatch.setattr(gateway,'exchange',fake)
    assert len(await gateway.models(profile))==1
    assert calls[1]['after_id']=='claude-test-1'


@pytest.mark.asyncio
@pytest.mark.parametrize('provider', ['anthropic', 'gemini'])
async def test_credentials_only_go_to_selected_fixed_endpoint(monkeypatch, provider):
    original = httpx.AsyncClient
    def handle(request):
        assert str(request.url).startswith(config.PROVIDERS[provider]['base_url'] + '/models')
        if provider == 'anthropic':
            assert request.headers['x-api-key'] == KEY
            assert request.headers['anthropic-version'] == '2023-06-01'
            assert 'authorization' not in request.headers
        else:
            assert request.headers['authorization'] == 'Bearer ' + KEY
        return httpx.Response(403, json={'private': KEY})
    monkeypatch.setattr(gateway.httpx, 'AsyncClient', lambda **kw: original(transport=httpx.MockTransport(handle), **kw))
    profile=config.Profile('analysis',provider,'test',KEY,base_url=config.PROVIDERS[provider]['base_url'])
    with pytest.raises(HTTPException) as exc:
        await gateway.models(profile)
    assert exc.value.status_code == 503 and KEY not in exc.value.detail


@pytest.mark.asyncio
async def test_paper_task_routes_analysis_and_discussion_separately(monkeypatch):
    purposes=[]
    class Fake:
        def __init__(self): self.chat=SimpleNamespace(completions=self)
        async def create(self,**kwargs):return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='synthetic answer'))])
    def choose(purpose):purposes.append(purpose);return Fake()
    monkeypatch.setattr(gateway,'task_client',choose)
    for task in ['Analyze paper','Discuss this section. Explain the argument','Return ONLY a proposed revised version','Answer the question using retrieved evidence.']:
        await papers.ai_call('test',{'task':task})
    assert purposes==['analysis','discussion','analysis','discussion']
