"""Administrator-only ceilings, scoped inheritance and resumable enforcement."""
from copy import deepcopy
import json
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.rewrite_policy import RewritePolicy
from app.schemas.paper_review import RewriteChoice
from app.services import paper_rewrite as rewrite, paper_review_service as ai
from app.services.rewrite_policy import DEFAULTS
from test_paper_reviews import setup_review, SAMPLE
from test_paper_rewrite import fixture_ai
from test_user_access import admin

client=TestClient(app)


@pytest.fixture(autouse=True)
def clean_policies():
    with SessionLocal() as db:
        db.query(RewritePolicy).delete();db.commit()
    yield
    with SessionLocal() as db:
        db.query(RewritePolicy).delete();db.commit()


def url(scope, ident):return f'/api/admin/rewrite-limits/{scope}/{ident}'


def put(headers, scope, ident, mode, limits=None):
    version=client.get(url(scope,ident),headers=headers).json()['policy']['version']
    response=client.put(url(scope,ident),headers=headers,json={'version':version,'mode':mode,**(limits or {})})
    assert response.status_code==200,response.text
    return response.json()


def test_precedence_is_paper_project_global_and_other_papers_are_unchanged():
    ah,_=admin();h,root,paper=setup_review();other_h,other_root,other=setup_review()
    paper_url=root+f"/{paper['id']}";other_url=other_root+f"/{other['id']}"
    sibling=client.post(root,headers=h,files={'file':('sibling.txt',SAMPLE.encode(),'text/plain')}).json()
    limits={'source_limit':120000,'output_limit':130000,'discussion_limit':90000}
    put(ah,'global',0,'custom',limits)
    assert client.get(paper_url,headers=h).json()['rewrite_limits']['source_limit']==120000
    put(ah,'project',paper['project_id'],'unlimited')
    assert client.get(paper_url,headers=h).json()['rewrite_limits']['source_limit'] is None
    assert client.get(root+f"/{sibling['id']}",headers=h).json()['rewrite_limits']['scope']=='project'
    assert client.get(other_url,headers=other_h).json()['rewrite_limits']['source_limit']==120000
    put(ah,'review',paper['id'],'custom',DEFAULTS)
    current=client.get(paper_url,headers=h).json()
    assert current['rewrite_limits']['scope']=='review' and current['rewrite_limits']['source_limit']==110000
    assert current['version']==paper['version']  # Policy writes do not overwrite manuscript state.
    put(ah,'review',paper['id'],'inherit')
    assert client.get(paper_url,headers=h).json()['rewrite_limits']['source_limit'] is None
    put(ah,'project',paper['project_id'],'inherit')
    assert client.get(paper_url,headers=h).json()['rewrite_limits']['source_limit']==120000


def test_policy_permissions_validation_and_optimistic_version():
    ah,_=admin();h,_,paper=setup_review();endpoint=url('review',paper['id'])
    assert client.get(endpoint).status_code==401
    assert client.get(endpoint,headers=h).status_code==403
    assert client.put(endpoint,headers=h,json={'version':0,'mode':'unlimited'}).status_code==403
    saved=put(ah,'review',paper['id'],'unlimited')
    assert saved['policy']['version']==1 and saved['policy']['updated_by']>0
    assert client.put(endpoint,headers=ah,json={'version':0,'mode':'unlimited'}).status_code==409
    assert client.put(url('global',0),headers=ah,json={'version':0,'mode':'inherit'}).status_code==422
    assert client.put(url('global',0),headers=ah,json={'version':0,'mode':'unlimited'}).status_code==422
    assert client.get(url('project',2147483647),headers=ah).status_code==404
    assert client.get(url('global',1),headers=ah).status_code==422
    for body in [{'mode':'custom'}, {'mode':'custom',**DEFAULTS,'source_limit':-1}, {'mode':'custom',**DEFAULTS,'source_limit':True}, {'mode':'unlimited','extra':1}]:
        assert client.put(endpoint,headers=ah,json={'version':1,**body}).status_code==422


def test_admin_can_open_only_one_paper_then_revoke_before_a_resumed_step(monkeypatch):
    monkeypatch.setattr(ai,'ai_call',fixture_ai)
    ah,_=admin();h,root,paper=setup_review();paper_url=root+f"/{paper['id']}"
    put(ah,'global',0,'custom',{**DEFAULTS,'source_limit':1})
    failed=client.post(paper_url+'/rewrite/start',headers=h,json={'version':paper['version'],'source_limit':None,'mode':'unlimited'})
    assert failed.status_code==413  # A forged researcher payload cannot lift server policy.
    put(ah,'review',paper['id'],'unlimited')
    current=client.post(paper_url+'/rewrite/start',headers=h,json={'version':paper['version']}).json()
    first=client.post(paper_url+'/rewrite/next',headers=h,json={'version':current['version']})
    assert first.status_code==200,first.text
    current=first.json();assert current['rewrite']['sections'][0]['result']
    put(ah,'review',paper['id'],'inherit')
    failed=client.post(paper_url+'/rewrite/next',headers=h,json={'version':current['version']})
    assert failed.status_code==413
    assert client.get(paper_url,headers=h).json()['rewrite']==current['rewrite']
    put(ah,'review',paper['id'],'unlimited')
    completed=client.post(paper_url+'/rewrite/next',headers=h,json={'version':current['version']})
    assert completed.status_code==200 and completed.json()['rewrite']['complete']


def test_output_ceiling_failure_keeps_plan_and_can_resume_after_admin_exception(monkeypatch):
    monkeypatch.setattr(ai,'ai_call',fixture_ai)
    ah,_=admin();h,root,paper=setup_review();paper_url=root+f"/{paper['id']}"
    current=client.post(paper_url+'/rewrite/start',headers=h,json={'version':paper['version']}).json()
    put(ah,'global',0,'custom',{**DEFAULTS,'output_limit':1})
    assert client.post(paper_url+'/rewrite/next',headers=h,json={'version':current['version']}).status_code==413
    assert client.get(paper_url,headers=h).json()['rewrite']==current['rewrite']
    put(ah,'review',paper['id'],'unlimited')
    response=client.post(paper_url+'/rewrite/next',headers=h,json={'version':current['version']})
    assert response.status_code==200 and response.json()['rewrite']['sections'][0]['result']


@pytest.mark.asyncio
async def test_unlimited_does_not_truncate_long_source_or_discussion_and_copy_can_exceed_old_cap(monkeypatch):
    monkeypatch.setattr(ai,'ai_call',fixture_ai)
    state=ai.build_state(['A conceptual scientific argument. '*12],'en')
    state['sections'][0]['original']='x'*(rewrite.MAX_SOURCE+1)
    state['paper_chat']={'messages':[{'role':'user','content':'y'*(rewrite.MAX_DISCUSSION+1)}]}
    unlimited={key:None for key in DEFAULTS}
    await rewrite.start(state,'en','general','original','',limits=unlimited)
    assert len(state['rewrite']['source_snapshot'][0]['text'])==rewrite.MAX_SOURCE+1
    assert len(state['rewrite']['context']['discussion']['paper_messages'][0]['content'])==rewrite.MAX_DISCUSSION+1
    await rewrite.advance(state,'en',limits=unlimited);await rewrite.advance(state,'en',limits=unlimited)
    choices=[RewriteChoice(section_id=s['id'],mode='custom',text='a'*60000) for s in state['rewrite']['sections']]
    before=deepcopy(state)
    with pytest.raises(HTTPException) as exc:rewrite.copy_state(state,'en',choices)
    assert exc.value.status_code==413 and state==before
    copy=rewrite.copy_state(state,'en',choices,limits=unlimited)
    assert copy['character_count']>rewrite.MAX_PROPOSAL
