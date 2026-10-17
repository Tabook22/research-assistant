"""Scientific presentation limits, checkpoints, source grounding and private images."""
import asyncio
import base64
from copy import deepcopy
import json
from uuid import uuid4
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.config import get_settings
from app.database import SessionLocal
from app.models.ai_configuration import AIConfiguration
from app.schemas.paper_review import PresentationStart, SlideEdit, SlideImage
from app.services import paper_presentation as slides, paper_review_service as ai, ai_configuration as config, ai_gateway
from test_paper_reviews import setup_review, auth, SAMPLE
from test_user_access import admin

client=TestClient(app)
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jZt8AAAAASUVORK5CYII=')


def fake_payload(payload):
    if 'requested_slides' not in payload:
        return {'title':'Scientific presentation', 'slides':[{'title':f'Research topic {i+1}', 'focus':'Explain the contribution and its limits', 'visual':['network','process','library','globe','science','balance'][i%6]} for i in range(payload['count'])]}
    p=next(p for p in payload['source_passages'] if len(p['text'])>=12)
    return {'slides':[{'id':s['id'], 'bullets':['A conceptual study of access to learning resources','Interpret findings within the study limitations'], 'notes':'Explain what the source establishes; do not claim causal effects.', 'image_prompt':'An elegant conceptual illustration of knowledge access and connected research documents, no text.', 'section_id':p['section_id'], 'quote':p['text'][:60]} for s in payload['requested_slides']]}


def fixture_ai(monkeypatch,change=None):
    async def fake(system,payload,json_output=False):
        assert json_output and 'UNTRUSTED' in system
        result=fake_payload(payload)
        if change:change(result,payload)
        return json.dumps(result)
    monkeypatch.setattr(ai,'ai_call',fake)


@pytest.mark.parametrize('count',[5,10,20])
def test_exact_count_checkpoints_and_matched_quotes(monkeypatch,count):
    fixture_ai(monkeypatch);state=ai.build_state([SAMPLE],'ar');before=deepcopy(state['sections'])
    state=asyncio.run(slides.start(state,'ar',PresentationStart(version=1,count=count)))
    assert len(state['presentation']['slides'])==count and not any(s['content'] for s in state['presentation']['slides'])
    while not state['presentation']['complete']:state=asyncio.run(slides.advance(state))
    assert state['sections']==before
    assert sum(bool(s['content']) for s in state['presentation']['slides'])==count
    for item in state['presentation']['slides']:
        loc=item['content']['location'];source=next(s['original'] for s in before if s['id']==loc['section_id'])
        assert source[loc['start']:loc['end']]==loc['quote']


def test_routes_limits_scope_and_resume_preserve_saved_slides(monkeypatch):
    fixture_ai(monkeypatch);h,url,row=setup_review();root=f"{url}/{row['id']}"
    for data in [{'count':21},{'count':25},{'count':True},{'count':2},{'section_ids':[9999]}]:
        assert client.post(root+'/presentation/start',headers=h,json={'version':row['version'],**data}).status_code==422
    state=client.post(root+'/presentation/start',headers=h,json={'version':row['version'],'count':5}).json()
    state=client.post(root+'/presentation/next',headers=h,json={'version':state['version']}).json()
    assert sum(bool(s['content']) for s in state['presentation']['slides'])==1
    saved=deepcopy(state)
    async def fail(*args,**kwargs):raise HTTPException(429,'AI_CREDIT_BALANCE: Exhausted')
    monkeypatch.setattr(ai,'ai_call',fail)
    assert client.post(root+'/presentation/next',headers=h,json={'version':state['version']}).status_code==429
    assert client.post(root+'/presentation/start',headers=h,json={'version':state['version'],'count':10}).status_code==429
    assert client.get(root,headers=h).json()['presentation']==saved['presentation']
    fixture_ai(monkeypatch)
    assert client.post(root+'/presentation/next',headers=h,json={'version':row['version']}).status_code==409
    state=client.post(root+'/presentation/next',headers=h,json={'version':state['version']}).json()
    assert state['presentation']['slides'][:1]==saved['presentation']['slides'][:1]
    next_set=client.post(root+'/presentation/start',headers=h,json={'version':state['version'],'count':3}).json()
    assert next_set['previous_presentation']['slides']==state['presentation']['slides']
    other=auth('slides-'+uuid4().hex+'@example.com')
    assert client.post(root+'/presentation/start',headers=other,json={'version':next_set['version']}).status_code==403
    assert client.post(root+'/presentation/start',json={'version':next_set['version']}).status_code==401


@pytest.mark.parametrize('failure',['count','quote','ids','overflow'])
def test_malformed_or_unsupported_content_never_saved(monkeypatch,failure):
    def change(data,payload):
        if 'requested_slides' not in payload:
            if failure=='count':data['slides'].pop()
        elif failure=='quote':data['slides'][0]['quote']='An invented quotation from a nonexistent source.'
        elif failure=='ids':data['slides'][0]['id']=99
        elif failure=='overflow':data['slides'][0]['bullets']=['x'*121]
    fixture_ai(monkeypatch,change);state=ai.build_state([SAMPLE],'en')
    with pytest.raises(HTTPException) as exc:
        state=asyncio.run(slides.start(state,'en',PresentationStart(version=1,count=5)))
        asyncio.run(slides.advance(state))
    assert exc.value.status_code==502


def test_editing_and_stale_source(monkeypatch):
    fixture_ai(monkeypatch);state=ai.build_state([SAMPLE],'en');sid=state['sections'][1]['id']
    state=asyncio.run(slides.start(state,'en',PresentationStart(version=1,count=3,section_ids=[sid])))
    state=slides.edit(state,1,SlideEdit(version=1,title='My title',focus='My focus'))
    state=asyncio.run(slides.advance(state));item=state['presentation']['slides'][0]
    assert item['content']['location']['section_id']==sid
    slides.edit(state,1,SlideEdit(version=1,title='Edited slide',focus='Edited focus',bullets=['Supported point'],notes='Researcher notes'))
    assert item['content']['edited'] and item['content']['bullets']==['Supported point']
    assert state['presentation']['title']=='Edited slide'
    state['sections'][1]['original']+=' Changed source.'
    with pytest.raises(HTTPException) as exc:asyncio.run(slides.advance(state))
    assert exc.value.status_code==409


def test_image_is_opt_in_private_and_uses_dedicated_profile(monkeypatch):
    fixture_ai(monkeypatch);h,url,row=setup_review();root=f"{url}/{row['id']}"
    state=client.post(root+'/presentation/start',headers=h,json={'version':row['version'],'count':3}).json()
    state=client.post(root+'/presentation/next',headers=h,json={'version':state['version']}).json();calls=[]
    profile=config.Profile('images','openai','gpt-image-synthetic','test-key',use_environment=False,base_url=config.PROVIDERS['openai']['base_url'])
    monkeypatch.setattr(config,'load',lambda purpose:profile)
    async def exchange(p,method,path,**kwargs):
        assert p is profile and method=='POST' and path=='/images/generations'
        assert kwargs['body']['size']=='1536x1024' and 'source_passages' not in kwargs['body']
        calls.append(kwargs['body']);return {'data':[{'b64_json':base64.b64encode(PNG).decode()}]}
    monkeypatch.setattr(ai_gateway,'exchange',exchange)
    result=client.post(root+'/presentation/slides/1/image',headers=h,json={'version':state['version'],'prompt':'An elegant abstract research illustration.'})
    assert result.status_code==200,result.text
    state=result.json();assert len(calls)==1 and state['presentation']['slides'][0]['image_ready']
    assert '_image_file' not in result.text and get_settings().export_dir not in result.text
    path=root+f"/presentation/{state['presentation']['id']}/slides/1/image"
    assert client.get(path,headers=h).content==PNG
    assert client.get(path).status_code==401
    other=auth('image-'+uuid4().hex+'@example.com');assert client.get(path,headers=other).status_code==403
    assert client.get(path.replace(state['presentation']['id'],'0'*32),headers=h).status_code==404


def test_image_profile_is_disabled_by_default_and_admin_only(monkeypatch):
    with SessionLocal() as db:db.query(AIConfiguration).filter_by(purpose='images').delete();db.commit()
    assert not config.load('images').key
    ah,_=admin();h,_,_=setup_review()
    data={'provider':'openai','model':'gpt-image-synthetic','api_key':'synthetic-image-key','version':0}
    assert client.put('/api/admin/ai/images',headers=h,json=data).status_code==403
    monkeypatch.setattr(get_settings(),'secret_key','Synthetic-image-secret-for-encryption-123456789')
    ah,_=admin()
    assert client.put('/api/admin/ai/images',headers=ah,json={**data,'provider':'xai'}).status_code==422
    saved=client.put('/api/admin/ai/images',headers=ah,json=data)
    assert saved.status_code==200,saved.text
    assert 'synthetic-image-key' not in saved.text
    assert config.load('images').key=='synthetic-image-key'
    async def models(profile):return [{'id':'gpt-image-synthetic'}]
    monkeypatch.setattr(ai_gateway,'models',models)
    async def forbidden(*args,**kwargs):raise AssertionError('An admin connection test must never create a paid image')
    monkeypatch.setattr(ai_gateway,'exchange',forbidden)
    assert client.post('/api/admin/ai/images/test',headers=ah,json={**data,'version':1}).status_code==200
    with SessionLocal() as db:db.query(AIConfiguration).filter_by(purpose='images').delete();db.commit()
