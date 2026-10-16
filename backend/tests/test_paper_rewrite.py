"""Whole-paper proposal integrity, resumability, ownership and independent-copy semantics."""
from copy import deepcopy
import json
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.services import paper_rewrite as rewrite, paper_review_service as ai
from test_paper_reviews import setup_review, auth

client = TestClient(app)


async def fixture_ai(system, payload, json_output=False):
    assert 'Do not invent references' in system and 'Never promise all conditions' in system
    assert json_output
    if 'selected_section' not in payload:
        return json.dumps({'title':'A clearer synthetic research paper', 'approach':'Clarify the argument and preserve source limits.',
                           'problem_formulation':'Provisional problem: unequal access to learning resources, subject to researcher verification.',
                           'requirements_needing_input':['Verify the bibliography and provide missing evidence.'],
                           'sections':[{'title':'Revised argument', 'purpose':'Explain the problem and existing argument.', 'source_section_ids':[s['id'] for s in payload['manuscript']]},
                                       {'title':'Limitations and future evidence', 'purpose':'Make missing evidence explicit.', 'source_section_ids':[]}]})
    return json.dumps({'text':'A proposed scholarly paragraph grounded in the supplied source. [RESEARCHER INPUT REQUIRED: verify supporting evidence.]',
                       'changes':['Clarified the research problem without inventing results.'], 'needs_input':['Verify supporting evidence.']})


def begin(monkeypatch):
    monkeypatch.setattr(ai,'ai_call',fixture_ai)
    h,url,original=setup_review();root=f"{url}/{original['id']}"
    response=client.post(root+'/rewrite/start',headers=h,json={'version':original['version'],'paper_type':'conceptual_legal','basis':'working','instruction':'Improve structure.'})
    assert response.status_code==200,response.text
    return h,root,original,response.json()


def advance(h,root,current):
    response=client.post(root+'/rewrite/next',headers=h,json={'version':current['version']})
    assert response.status_code==200,response.text
    return response.json()


def test_full_proposal_preserves_source_and_drafts_and_copy_is_independent(monkeypatch):
    h,root,original,current=begin(monkeypatch)
    assert 'context' not in current['rewrite']
    assert current['sections']==original['sections']
    assert client.post(root+'/rewrite/copy',headers=h,json={'version':current['version']}).status_code==409
    current=advance(h,root,current);assert not current['rewrite']['complete']
    current=advance(h,root,current);assert current['rewrite']['complete']
    assert current['sections']==original['sections']
    response=client.post(root+'/rewrite/copy',headers=h,json={'version':current['version']})
    assert response.status_code==200,response.text
    copied=response.json();assert copied['id']!=original['id']
    assert copied['origin_review_id']==original['id'] and copied['suggested_paper_type']=='conceptual_legal'
    assert len(copied['sections'])==2 and copied['overview'] is None
    assert all(s['draft'] is None for s in copied['sections'])
    assert 'RESEARCHER INPUT REQUIRED' in copied['sections'][0]['original']
    assert copied['proposal_needs_input'] and copied['warnings']
    original_saved=client.get(root,headers=h).json()
    assert original_saved['sections']==original['sections']
    repeated=client.post(root+'/rewrite/copy',headers=h,json={'version':original_saved['version']})
    assert repeated.status_code==200 and repeated.json()['id']==copied['id']
    # User changes in the independent copy do not touch the original manuscript.
    draft=client.patch(root.rsplit('/',1)[0]+f"/{copied['id']}/sections/{copied['sections'][0]['id']}/draft",headers=h,json={'version':copied['version'],'text':'Researcher-reviewed revised paragraph.'})
    assert draft.status_code==200
    assert client.get(root,headers=h).json()['sections']==original['sections']


def test_provider_failure_retains_checkpoints_and_resume_skips_completed_sections(monkeypatch):
    h,root,original,current=begin(monkeypatch)
    current=advance(h,root,current)
    async def fail(*args,**kwargs):raise HTTPException(504,'AI_TIMEOUT: synthetic interruption')
    monkeypatch.setattr(ai,'ai_call',fail)
    failed=client.post(root+'/rewrite/next',headers=h,json={'version':current['version']})
    assert failed.status_code==504
    saved=client.get(root,headers=h).json();assert saved['rewrite']==current['rewrite']
    seen=[]
    async def resume(system,payload,json_output=False):
        seen.append(payload['selected_section']['id']);return await fixture_ai(system,payload,json_output)
    monkeypatch.setattr(ai,'ai_call',resume)
    completed=advance(h,root,saved)
    assert seen==[2] and completed['rewrite']['complete']


@pytest.mark.parametrize('bad',['missing_source','invented_source','invalid_json','oversized_outline'])
def test_invalid_new_plan_preserves_previous_proposal(monkeypatch,bad):
    h,root,_,current=begin(monkeypatch)
    async def invalid(system,payload,json_output=False):
        data=json.loads(await fixture_ai(system,payload,json_output))
        if bad=='invalid_json':return 'invalid JSON'
        if bad=='missing_source':data['sections'][0]['source_section_ids']=[]
        if bad=='invented_source':data['sections'][0]['source_section_ids'].append(9999)
        if bad=='oversized_outline':data['sections']*=16
        return json.dumps(data)
    monkeypatch.setattr(ai,'ai_call',invalid)
    failed=client.post(root+'/rewrite/start',headers=h,json={'version':current['version']})
    assert failed.status_code==502
    assert client.get(root,headers=h).json()['rewrite']==current['rewrite']


def test_editing_source_marks_proposal_stale_and_blocks_resume_and_copy(monkeypatch):
    h,root,_,current=begin(monkeypatch)
    current=advance(h,root,current);current=advance(h,root,current)
    sid=current['sections'][0]['id']
    changed=client.patch(root+f'/sections/{sid}/draft',headers=h,json={'version':current['version'],'text':'Changed source manuscript.'}).json()
    assert changed['rewrite']['stale']
    for suffix in ('next','copy'):
        assert client.post(root+'/rewrite/'+suffix,headers=h,json={'version':changed['version']}).status_code==409


def test_ownership_and_optimistic_version_are_enforced(monkeypatch):
    h,root,original,current=begin(monkeypatch)
    other=auth('rewrite-other@example.com')
    for suffix in ('start','next','copy'):
        assert client.post(root+'/rewrite/'+suffix,headers=other,json={'version':current['version']}).status_code==403
        assert client.post(root+'/rewrite/'+suffix,headers=h,json={'version':original['version']}).status_code==409


@pytest.mark.asyncio
async def test_long_source_is_rejected_before_replacing_proposal(monkeypatch):
    state=ai.build_state(['A source paragraph about conceptual research. '*12],'en')
    state['sections'][0]['original']='x'*(rewrite.MAX_SOURCE+1)
    state['rewrite']={'sentinel':'saved'};before=deepcopy(state)
    with pytest.raises(HTTPException) as exc:await rewrite.start(state,'en','general','original','')
    assert exc.value.status_code==413 and state==before


def test_invalid_section_result_is_atomic_and_old_proposal_is_retained(monkeypatch):
    h,root,_,current=begin(monkeypatch)
    async def invalid(*args,**kwargs):return json.dumps({'text':' ','changes':[],'needs_input':[]})
    monkeypatch.setattr(ai,'ai_call',invalid)
    assert client.post(root+'/rewrite/next',headers=h,json={'version':current['version']}).status_code==502
    assert client.get(root,headers=h).json()['rewrite']==current['rewrite']
    monkeypatch.setattr(ai,'ai_call',fixture_ai)
    new=client.post(root+'/rewrite/start',headers=h,json={'version':current['version'],'instruction':'A new plan.'}).json()
    assert new['previous_rewrite']['title']==current['rewrite']['title']
    assert new['sections']==current['sections']
