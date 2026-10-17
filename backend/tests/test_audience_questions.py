"""Audience preparation: scoped evidence, exact formats, checkpoints and ownership."""
import asyncio
from copy import deepcopy
import json
from types import SimpleNamespace
from uuid import uuid4
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.services import audience_questions as audience, paper_review_service as ai, ai_gateway
from test_paper_reviews import setup_review, auth, SAMPLE
from test_evaluation_only import create
from test_user_access import admin, login

client = TestClient(app)


def fake_questions(payload):
    passage = next(p for p in payload['source_passages'] if len(p['text']) >= 12)
    offset = len(payload['previous_questions'])
    return {'questions': [dict(format=fmt, topic='Research contribution',
        question=f'What does the paper establish {offset+i+1}?' if fmt!='fill_blank' else f'The contribution {offset+i+1} is ____.',
        why_asked='The audience may question the scope of the findings.', answer='A conceptual analysis; discuss the limitations stated in the source.',
        options=['Conceptual analysis','Experiment','Survey','Meta-analysis'] if fmt=='multiple_choice' else [],
        correct_index=0 if fmt=='multiple_choice' else None,
        evidence={'section_id': passage['section_id'], 'quote': passage['text'][:60]}) for i,fmt in enumerate(payload['requested_formats'])]}


def fixture_ai(monkeypatch, change=None):
    async def fake(system, payload, json_output=False):
        assert payload['task'].startswith('Discuss this paper') and json_output
        assert 'UNTRUSTED' in system
        data = fake_questions(payload)
        if change: change(data)
        return json.dumps(data)
    monkeypatch.setattr(ai, 'ai_call', fake)


@pytest.mark.parametrize('count', [1,2,3,5,10])
@pytest.mark.parametrize('format', ['essay','multiple_choice','fill_blank','mixed'])
def test_exact_counts_formats_and_source_anchors(monkeypatch, count, format):
    fixture_ai(monkeypatch)
    state = ai.build_state([SAMPLE], 'en')
    before = deepcopy(state['sections'])
    state = asyncio.run(audience.start(state, 'ar', count, format))
    while not state['audience_questions']['complete']:
        state = asyncio.run(audience.advance(state))
    report = state['audience_questions']
    assert len(report['questions']) == count and report['language']=='ar'
    assert state['sections'] == before
    for index, question in enumerate(report['questions']):
        assert question['format'] == audience.question_format(report, index)
        anchor = question['location']
        section = next(s for s in before if s['id']==anchor['section_id'])
        assert section['original'][anchor['start']:anchor['end']] == anchor['quote']


def test_saved_progress_survives_failure_resume_and_stale_version(monkeypatch):
    h,url,row=setup_review();root=f"{url}/{row['id']}";fixture_ai(monkeypatch)
    start=client.post(root+'/audience-questions/start',headers=h,json={'version':row['version'],'count':5,'format':'mixed'})
    assert start.status_code==200,start.text
    saved=start.json();assert len(saved['audience_questions']['questions'])==2
    async def fail(*args,**kwargs):raise HTTPException(429,'AI_CREDIT_BALANCE: Exhausted')
    monkeypatch.setattr(ai,'ai_call',fail)
    failed=client.post(root+'/audience-questions/next',headers=h,json={'version':saved['version']})
    assert failed.status_code==429
    assert client.get(root,headers=h).json()['audience_questions']==saved['audience_questions']
    # A failed replacement must also retain the previously saved set and version.
    assert client.post(root+'/audience-questions/start',headers=h,json={'version':saved['version'],'count':1}).status_code==429
    assert client.get(root,headers=h).json()['version']==saved['version']
    fixture_ai(monkeypatch)
    assert client.post(root+'/audience-questions/next',headers=h,json={'version':row['version']}).status_code==409
    resumed=client.post(root+'/audience-questions/next',headers=h,json={'version':saved['version']}).json()
    assert len(resumed['audience_questions']['questions'])==4
    assert resumed['audience_questions']['questions'][:2]==saved['audience_questions']['questions']
    new=client.post(root+'/audience-questions/start',headers=h,json={'version':resumed['version'],'count':1}).json()
    assert new['previous_audience_questions']['questions']==resumed['audience_questions']['questions']


@pytest.mark.parametrize('corruption', ['quote','format','options','blank','duplicate','count'])
def test_invalid_generated_material_is_rejected(monkeypatch, corruption):
    state=ai.build_state([SAMPLE],'en')
    def change(data):
        q=data['questions'][0]
        if corruption=='quote':q['evidence']['quote']='This invented quotation is not in the source.'
        elif corruption=='format':q['format']='essay'
        elif corruption=='options':q['options']=['duplicate']*4
        elif corruption=='blank':q['question']='There is no missing phrase in this question.'
        elif corruption=='duplicate':data['questions'][1]['question']=q['question']
        elif corruption=='count':data['questions']=[]
    fixture_ai(monkeypatch,change)
    fmt='fill_blank' if corruption=='blank' else 'multiple_choice'
    with pytest.raises(HTTPException) as exc:asyncio.run(audience.start(state,'en',2,fmt))
    assert exc.value.status_code==502


def test_section_scope_and_changed_source_are_enforced(monkeypatch):
    fixture_ai(monkeypatch);state=ai.build_state([SAMPLE],'en');sid=state['sections'][1]['id']
    state=asyncio.run(audience.start(state,'en',3,'essay',sid))
    assert all(q['location']['section_id']==sid for q in state['audience_questions']['questions'])
    state['sections'][1]['original']+=' Source changed.'
    with pytest.raises(HTTPException) as exc:asyncio.run(audience.advance(state))
    assert exc.value.status_code==409
    with pytest.raises(HTTPException):asyncio.run(audience.start(state,'en',3,'essay',99999))


def test_request_validation_and_ownership(monkeypatch):
    h,url,row=setup_review();root=f"{url}/{row['id']}";fixture_ai(monkeypatch)
    for data in [{'count':0},{'count':11},{'count':True},{'format':'unknown'}]:
        assert client.post(root+'/audience-questions/start',headers=h,json={'version':row['version'],**data}).status_code==422
    other=auth('audience-'+uuid4().hex+'@example.com')
    assert client.post(root+'/audience-questions/start',headers=other,json={'version':row['version']}).status_code==403
    assert client.post(root+'/audience-questions/start',json={'version':row['version']}).status_code==401


def test_evaluation_only_user_can_prepare_own_questions(monkeypatch):
    ah,_=admin();user=create(ah);h,_=login(user['username']);fixture_ai(monkeypatch)
    project=client.post('/api/paper-evaluation/workspace',headers=h).json()['id']
    root=f'/api/projects/{project}/paper-reviews'
    row=client.post(root,headers=h,files={'file':('test.txt',SAMPLE.encode(),'text/plain')}).json()
    response=client.post(f"{root}/{row['id']}/audience-questions/start",headers=h,json={'version':row['version'],'count':1})
    assert response.status_code==200,response.text


@pytest.mark.asyncio
async def test_question_generation_uses_admin_discussion_profile(monkeypatch):
    purposes=[]
    class Fake:
        def __init__(self):self.chat=SimpleNamespace(completions=self)
        async def create(self,**kwargs):
            data=fake_questions(json.loads(kwargs['messages'][1]['content']))
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(data)))])
    def choose(purpose):purposes.append(purpose);return Fake()
    monkeypatch.setattr(ai_gateway,'task_client',choose)
    await audience.start(ai.build_state([SAMPLE],'en'),'en',1,'essay')
    assert purposes==['discussion']
