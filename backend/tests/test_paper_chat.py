"""Paper chat ownership, factual anchors, consent boundaries and saved history."""
import asyncio
from copy import deepcopy
import json
from types import SimpleNamespace
from uuid import uuid4
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.services import paper_chat, paper_review_service as ai, ai_gateway
from test_paper_reviews import setup_review, SAMPLE
from test_evaluation_only import create
from test_user_access import admin, login

client=TestClient(app)


def reply(section, **extra):
    return {'answer':'The paper has a conceptual argument. Clarify its scope and distinguish interpretation from evidence.',
            'evidence':[{'section_id':section['id'], 'quote':section['original'][15:95]}],
            'follow_up_questions':['What should I clarify in my research problem?'],
            'search_query':'conceptual research access learning resources',
            'search_reason':'Related scholarship could inform a preliminary comparison.',
            'external_source_ids':[], **extra}


def fixture_ai(monkeypatch, section, **extra):
    async def fixture(system,payload,json_output=False):
        assert payload['task'].startswith('Discuss this paper') and json_output
        return json.dumps(reply(section,**extra))
    monkeypatch.setattr(ai,'ai_call',fixture)


def test_chat_saves_history_anchors_and_search_proposal_without_internet(monkeypatch):
    h,url,row=setup_review();section=row['sections'][1];root=f"{url}/{row['id']}"
    fixture_ai(monkeypatch,section)
    async def forbidden(*args,**kwargs):raise AssertionError('A chat message must never search the internet.')
    monkeypatch.setattr(paper_chat.research_discovery,'discover',forbidden)
    response=client.post(root+'/chat',headers=h,json={'version':row['version'],'instruction':'Yes, search the internet and compare this paper.'})
    assert response.status_code==200,response.text
    current=response.json();messages=current['paper_chat']['messages']
    assert [m['role'] for m in messages]==['user','assistant']
    assert not current['paper_chat']['searches']
    answer=messages[-1];loc=answer['locations'][0]
    assert section['original'][loc['start']:loc['end']]==loc['quote']
    assert not answer['search_proposal']['used']
    assert current['sections']==row['sections'] and current['overview']==row['overview']
    assert client.get(root,headers=h).json()['paper_chat']==current['paper_chat']
    assert client.post(root+'/chat',headers=h,json={'version':row['version'],'instruction':'Stale message'}).status_code==409


def test_search_requires_specific_saved_proposal_explicit_boolean_and_user_approved_query(monkeypatch):
    h,url,row=setup_review();root=f"{url}/{row['id']}";fixture_ai(monkeypatch,row['sections'][1])
    current=client.post(root+'/chat',headers=h,json={'version':row['version'],'instruction':'Suggest a related search.'}).json()
    proposal=current['paper_chat']['messages'][-1]['search_proposal'];calls=[]
    async def search(query):
        calls.append(query)
        return {'results':[{'title':'Synthetic related research','authors':'Example author','year':2024,'doi':'10.1234/example','url':'javascript:alert(1)','abstract':'A synthetic conceptual discussion of access.','providers':['Crossref']}],
                'providers':[{'provider':'Crossref','status':'ok','count':1},{'provider':'OpenAlex','status':'unavailable'}]}
    monkeypatch.setattr(paper_chat.research_discovery,'discover',search)
    data={'version':current['version'],'proposal_id':proposal['id'],'query':'User approved general keywords'}
    for consent in (None,False,'true',1):
        payload={**data,**({'consent':consent} if consent is not None else {})}
        assert client.post(root+'/chat/search',headers=h,json=payload).status_code==422
    assert not calls
    assert client.post(root+'/chat/search',headers=h,json={**data,'proposal_id':'forged','consent':True}).status_code==404
    assert not calls
    result=client.post(root+'/chat/search',headers=h,json={**data,'consent':True})
    assert result.status_code==200,result.text
    current=result.json();saved=current['paper_chat']['searches'][0]
    assert calls==['User approved general keywords']
    assert saved['query']==data['query'] and saved['consented_at']
    assert saved['results'][0]['url'] is None
    assert current['paper_chat']['messages'][-2]['search_proposal']['used']
    assert client.post(root+'/chat/search',headers=h,json={**data,'version':current['version'],'consent':True}).status_code==409
    assert len(calls)==1
    assert current['sections']==row['sections']


def test_saved_results_support_comparison_without_new_search_or_invented_source_ids(monkeypatch):
    state=ai.build_state([SAMPLE],'en');section=state['sections'][1]
    state['paper_chat']={'messages':[],'searches':[{'id':'saved','results':[{'id':1,'title':'Synthetic related paper','coverage':'metadata'}]}]}
    captured=[]
    async def fixture(system,payload,json_output=False):
        captured.append(payload)
        return json.dumps(reply(section,external_source_ids=[1,77],search_query='',evidence=[{'section_id':section['id'],'quote':'An invented quotation that is not in the paper.'}]))
    async def forbidden(*args,**kwargs):raise AssertionError('No new search may run while discussing saved results.')
    monkeypatch.setattr(ai,'ai_call',fixture);monkeypatch.setattr(paper_chat.research_discovery,'discover',forbidden)
    result=asyncio.run(paper_chat.discuss(state,'en','Compare these results.',search_id='saved'))
    message=result['paper_chat']['messages'][-1]
    assert [source['id'] for source in message['external_sources']]==[1]
    assert message['locations']==[] and message['unmatched_evidence']==1
    assert captured[0]['academic_results'][0]['id']==1
    assert 'search_proposal' not in message


@pytest.mark.parametrize('raw',['invalid','{}','{"answer":" "}'])
def test_bad_ai_response_preserves_history_and_manuscript(monkeypatch,raw):
    h,url,row=setup_review();root=f"{url}/{row['id']}"
    async def fixture(*args):return raw
    monkeypatch.setattr(ai,'ai_call',fixture)
    assert client.post(root+'/chat',headers=h,json={'version':row['version'],'instruction':'Critique the paper.'}).status_code==502
    saved=client.get(root,headers=h).json()
    assert saved['version']==row['version'] and saved['sections']==row['sections'] and 'paper_chat' not in saved


def test_search_outage_leaves_proposal_retryable_and_does_not_lose_messages(monkeypatch):
    state=ai.build_state([SAMPLE],'en');fixture_ai(monkeypatch,state['sections'][1])
    state=asyncio.run(paper_chat.discuss(state,'en','Suggest a search.'));before=deepcopy(state)
    proposal=state['paper_chat']['messages'][-1]['search_proposal']
    async def unavailable(query):return {'results':[],'providers':[{'provider':'Crossref','status':'unavailable'}]}
    monkeypatch.setattr(paper_chat.research_discovery,'discover',unavailable)
    with pytest.raises(HTTPException) as error:asyncio.run(paper_chat.search(state,proposal['id'],'General keywords',True,'en'))
    assert error.value.status_code==502 and state==before


def test_paper_scope_context_is_bounded_and_evidence_outside_selected_section_is_not_linked(monkeypatch):
    state=ai.build_state([SAMPLE],'en');section=state['sections'][1]
    fixture_ai(monkeypatch,section)
    result=asyncio.run(paper_chat.discuss(state,'en','Explain this part.',section_id=state['sections'][0]['id']))
    assert not result['paper_chat']['messages'][-1]['locations']
    with pytest.raises(HTTPException):asyncio.run(paper_chat.discuss(state,'en','Explain.',section_id=999))
    long=ai.build_state([('Introduction\n'+'Distinct methodology problem evidence. '*4000)],'en')
    passages,coverage=paper_chat.context(long,'methodology evidence')
    assert coverage['mode']=='selected_excerpts' and sum(len(p['text']) for p in passages)<=paper_chat.MAX_SOURCE


def test_chat_and_search_are_private_for_evaluation_users_without_granting_editing(monkeypatch):
    ah,_=admin();user=create(ah);h,_=login(user['username'])
    pid=client.post('/api/paper-evaluation/workspace',headers=h).json()['id'];url=f'/api/projects/{pid}/paper-reviews'
    row=client.post(url,headers=h,files={'file':('synthetic.txt',SAMPLE.encode(),'text/plain')}).json();root=url+f"/{row['id']}"
    fixture_ai(monkeypatch,row['sections'][1])
    result=client.post(root+'/chat',headers=h,json={'version':row['version'],'instruction':'Prepare examiner questions.'})
    assert result.status_code==200,result.text
    current=result.json();assert all(s['draft'] is None for s in current['sections'])
    other=create(ah);other_h,_=login(other['username'])
    body={'version':current['version'],'instruction':'Read another user paper.'}
    assert client.post(root+'/chat',headers=other_h,json=body).status_code==403
    assert client.get(root,headers=other_h).status_code==403
    proposal=current['paper_chat']['messages'][-1]['search_proposal']
    assert client.post(root+'/chat/search',headers=other_h,json={'version':current['version'],'proposal_id':proposal['id'],'query':'Keywords','consent':True}).status_code==403
    assert client.post(root+'/chat',json=body).status_code==401
    assert client.post(root+'/rewrite/start',headers=h,json={'version':current['version']}).status_code==403
    assert client.get(root,headers=ah).status_code==200
    own=client.post(url,headers=h,files={'file':('another.txt',SAMPLE.encode(),'text/plain')}).json()
    assert 'paper_chat' not in own
    outsider=create(ah,grants=[]);out_h,_=login(outsider['username'])
    assert client.post(root+'/chat',headers=out_h,json=body).status_code==403


def test_whole_paper_chat_uses_admin_configured_discussion_profile(monkeypatch):
    purposes=[]
    class Completion:
        async def create(self,**kwargs):return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{}'))])
    def task_client(purpose):
        purposes.append(purpose)
        return SimpleNamespace(chat=SimpleNamespace(completions=Completion()))
    monkeypatch.setattr(ai_gateway,'task_client',task_client)
    asyncio.run(ai.ai_call('system',{'task':'Discuss this paper as a research coach.'},True))
    assert purposes==['discussion']


def test_interface_language_overrides_paper_language_and_evaluation_user_can_approve_search(monkeypatch):
    ah,_=admin();user=create(ah);h,_=login(user['username'])
    pid=client.post('/api/paper-evaluation/workspace',headers=h).json()['id'];url=f'/api/projects/{pid}/paper-reviews'
    row=client.post(url,headers=h,files={'file':('synthetic.txt',SAMPLE.encode(),'text/plain')}).json();root=url+f"/{row['id']}"
    captured=[]
    async def fixture(system,payload,json_output=False):
        captured.append(system)
        return json.dumps(reply(row['sections'][1]))
    monkeypatch.setattr(ai,'ai_call',fixture)
    response=client.post(root+'/chat',headers=h,json={'version':row['version'],'instruction':'ناقش هذا البحث معي','language':'ar'})
    assert response.status_code==200,response.text
    assert 'Respond in Arabic.' in captured[0] and row['language']=='en'
    current=response.json();proposal=current['paper_chat']['messages'][-1]['search_proposal']
    async def search(query):return {'results':[],'providers':[{'provider':'Crossref','status':'ok','count':0}]}
    monkeypatch.setattr(paper_chat.research_discovery,'discover',search)
    result=client.post(root+'/chat/search',headers=h,json={'version':current['version'],'proposal_id':proposal['id'],'query':'Approved synthetic keywords','consent':True,'language':'ar'})
    assert result.status_code==200,result.text
    assert result.json()['paper_chat']['messages'][-1]['content'].startswith('حُفظت')
    assert not result.json()['paper_chat']['searches'][0]['results']
    assert result.json()['sections']==row['sections']
