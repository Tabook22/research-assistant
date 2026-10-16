"""Dated paper sessions preserve legacy transcripts and isolate resumed context."""
import asyncio
from copy import deepcopy
import json
import pytest
from fastapi import HTTPException
from test_paper_chat import client, fixture_ai, reply
from test_paper_reviews import setup_review, SAMPLE
from test_evaluation_only import create
from test_user_access import admin, login
from app.services import paper_chat, paper_review_service as ai


def test_legacy_history_is_projected_without_mutation_or_lost_evidence():
    state={'paper_chat':{'messages':[
        {'id':'q','role':'user','content':'A historical question','created_at':'2026-10-10T08:00:00+00:00'},
        {'id':'a','role':'assistant','content':'Saved answer','created_at':'2026-10-10T08:01:00+00:00','locations':[{'quote':'Preserved source quotation'}],'search_proposal':{'id':'proposal','query':'keywords','used':True}}],
        'searches':[{'id':'results','created_at':'2026-10-11T08:00:00+00:00','results':[{'title':'Saved discovery'}]}]}}
    before=deepcopy(state);projected=paper_chat.history(state)
    assert state==before
    session=projected['sessions'][0]
    assert session['id']=='legacy' and session['number']==1 and session['title']=='A historical question'
    assert session['created_at']=='2026-10-10T08:00:00+00:00' and session['updated_at']=='2026-10-11T08:00:00+00:00'
    assert session['question_count']==1 and session['message_count']==2 and session['search_count']==1
    paper_chat.create_session(state)
    assert [s['number'] for s in state['paper_chat']['sessions']]==[1,2]
    for kind in ('messages','searches'):
        assert [{k:v for k,v in item.items() if k!='session_id'} for item in state['paper_chat'][kind]]==before['paper_chat'][kind]
    once=paper_chat.history(state)
    assert paper_chat.history({'paper_chat':once})==once


def test_new_session_does_not_call_ai_and_titles_numbers_dates_persist(monkeypatch):
    h,url,row=setup_review();root=f"{url}/{row['id']}"
    async def forbidden(*args,**kwargs):raise AssertionError('Creating or renaming a session must not invoke AI.')
    monkeypatch.setattr(ai,'ai_call',forbidden)
    for number in (1,2):
        response=client.post(root+'/chat/sessions',headers=h,json={'version':row['version']})
        assert response.status_code==200,response.text
        row=response.json();session=row['paper_chat']['sessions'][-1]
        assert session['number']==number and session['created_at'] and session['updated_at']
        assert session['question_count']==0 and not row['paper_chat']['messages']
    sid=session['id']
    renamed=client.patch(root+'/chat/sessions/'+sid,headers=h,json={'version':row['version'],'title':'  Methodology   discussion  '})
    assert renamed.status_code==200,renamed.text
    saved=client.get(root,headers=h).json()
    assert saved['paper_chat']['sessions'][-1]['title']=='Methodology discussion'
    assert saved['paper_chat']['last_session_id']==sid
    assert saved['sections']==row['sections']


def test_resumed_session_uses_only_its_own_history_and_keeps_other_session_intact(monkeypatch):
    state=ai.build_state([SAMPLE],'en');section=state['sections'][1];captured=[]
    async def fixture(system,payload,json_output=False):
        captured.append(payload['recent_conversation'])
        return json.dumps(reply(section,search_query=''))
    monkeypatch.setattr(ai,'ai_call',fixture)
    state=asyncio.run(paper_chat.discuss(state,'en','First session unique question.'))
    first=state['paper_chat']['last_session_id'];old_messages=deepcopy(state['paper_chat']['messages'])
    paper_chat.create_session(state);second=state['paper_chat']['last_session_id']
    state=asyncio.run(paper_chat.discuss(state,'en','Second session unique question.',session_id=second))
    assert captured[-1]==[]
    state=asyncio.run(paper_chat.discuss(state,'en','Continue our first discussion.',session_id=first))
    assert [m['content'] for m in captured[-1]]==[m['content'] for m in old_messages]
    assert all('Second session unique' not in m['content'] for m in captured[-1])
    history=paper_chat.history(state)
    assert [s['question_count'] for s in history['sessions']]==[2,1]
    assert history['sessions'][0]['title']=='First session unique question.'
    assert history['last_session_id']==first


def test_search_permission_and_results_cannot_cross_session_boundaries(monkeypatch):
    state=ai.build_state([SAMPLE],'en');fixture_ai(monkeypatch,state['sections'][1])
    state=asyncio.run(paper_chat.discuss(state,'en','Propose a search.'));first=state['paper_chat']['last_session_id']
    proposal=state['paper_chat']['messages'][-1]['search_proposal']['id'];calls=[]
    async def discover(query):
        calls.append(query)
        return {'providers':[{'provider':'Crossref','status':'ok'}],'results':[]}
    monkeypatch.setattr(paper_chat.research_discovery,'discover',discover)
    paper_chat.create_session(state);second=state['paper_chat']['last_session_id']
    with pytest.raises(HTTPException) as error:asyncio.run(paper_chat.search(state,proposal,'Approved query',True,'en',second))
    assert error.value.status_code==404 and not calls
    state=asyncio.run(paper_chat.search(state,proposal,'Approved query',True,'en',first))
    search=state['paper_chat']['searches'][-1]
    assert search['session_id']==first and calls==['Approved query']
    with pytest.raises(HTTPException) as error:asyncio.run(paper_chat.discuss(state,'en','Compare.',search_id=search['id'],session_id=second))
    assert error.value.status_code==404


def test_session_api_rejects_stale_versions_and_unknown_sessions(monkeypatch):
    h,url,row=setup_review();root=f"{url}/{row['id']}";initial=row['version']
    row=client.post(root+'/chat/sessions',headers=h,json={'version':initial}).json();sid=row['paper_chat']['last_session_id']
    assert client.post(root+'/chat/sessions',headers=h,json={'version':initial}).status_code==409
    assert client.patch(root+'/chat/sessions/'+sid,headers=h,json={'version':initial,'title':'Stale'}).status_code==409
    assert client.patch(root+'/chat/sessions/'+sid,headers=h,json={'version':row['version'],'title':'   '}).status_code==422
    assert client.patch(root+'/chat/sessions/missing',headers=h,json={'version':row['version'],'title':'Missing'}).status_code==404
    async def forbidden(*args,**kwargs):raise AssertionError('A nonexistent session must not invoke a provider.')
    monkeypatch.setattr(ai,'ai_call',forbidden)
    assert client.post(root+'/chat',headers=h,json={'version':row['version'],'instruction':'Question','session_id':'missing'}).status_code==404
    saved=client.get(root,headers=h).json()
    assert saved['version']==row['version'] and saved['paper_chat']==row['paper_chat']


def test_paper_only_users_can_manage_their_sessions_without_access_to_other_users(monkeypatch):
    ah,_=admin();user=create(ah);h,_=login(user['username'])
    pid=client.post('/api/paper-evaluation/workspace',headers=h).json()['id'];url=f'/api/projects/{pid}/paper-reviews'
    row=client.post(url,headers=h,files={'file':('synthetic.txt',SAMPLE.encode(),'text/plain')}).json();root=url+f"/{row['id']}"
    original=deepcopy(row['sections'])
    created=client.post(root+'/chat/sessions',headers=h,json={'version':row['version']})
    assert created.status_code==200,created.text
    row=created.json();sid=row['paper_chat']['last_session_id']
    fixture_ai(monkeypatch,row['sections'][1])
    answered=client.post(root+'/chat',headers=h,json={'version':row['version'],'session_id':sid,'instruction':'Discuss methodology.'})
    assert answered.status_code==200;row=answered.json()
    assert row['paper_chat']['sessions'][0]['question_count']==1
    renamed=client.patch(root+'/chat/sessions/'+sid,headers=h,json={'version':row['version'],'title':'مناقشة المنهج'})
    assert renamed.status_code==200;row=renamed.json()
    other=create(ah);other_h,_=login(other['username'])
    assert client.post(root+'/chat/sessions',headers=other_h,json={'version':row['version']}).status_code==403
    assert client.patch(root+'/chat/sessions/'+sid,headers=other_h,json={'version':row['version'],'title':'Denied'}).status_code==403
    assert client.post(root+'/chat/sessions',json={'version':row['version']}).status_code==401
    assert client.patch(root+f"/sections/{row['sections'][0]['id']}/draft",headers=h,json={'version':row['version'],'text':'Forbidden'}).status_code==403
    assert client.get(root,headers=ah).json()['paper_chat']['sessions'][0]['title']=='مناقشة المنهج'
    assert row['sections']==original
