"""Visual review must ground highlights, preserve source and respect page grants."""
import asyncio
from copy import deepcopy
import json
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.services import paper_review_service as ai
from app.services import paper_annotations
from test_paper_reviews import setup_review, SAMPLE
from test_user_access import admin, login
from test_evaluation_only import create

client=TestClient(app)


def note(quote,category='improvement',replacement='A carefully qualified revision of the source.'):
    return {'category':category,'severity':'high','title':'Clarify the scope','explanation':'Identify the scope and support the argument with verified evidence.','quote':quote,'replacement':replacement}


def test_anchors_use_unicode_original_offsets_and_verified_page(monkeypatch):
    text='🙂 مقدمة\nتبحث هذه الدراسة في إتاحة الموارد التعليمية في الساحل.'
    state=ai.build_state([text*4],'ar');s=state['sections'][0]
    quote='تبحث هذه الدراسة في إتاحة الموارد التعليمية'
    s['draft']='This draft-only passage must not become an original anchor.'
    async def fixture(*args):return json.dumps({'items':[note(quote),note('This excerpt does not exist anywhere.'),note(quote,'strength'),note(s['draft'])]})
    monkeypatch.setattr(ai,'ai_call',fixture)
    before=deepcopy(state)
    result=asyncio.run(paper_annotations.annotate(state,s,'ar'))
    items=result['sections'][0]['annotations']['items'];loc=items[0]['location']
    assert s['original'][loc['start']:loc['end']]==quote
    assert loc['basis']=='original' and loc['page']==1
    assert items[1]['location'] is None and items[1]['replacement']==''
    assert items[2]['replacement']=='' and items[2]['severity']=='low'
    assert items[3]['location'] is None and items[3]['replacement']==''
    assert all(s[key]==before['sections'][0][key] for key in ('original','draft','revisions','messages'))


@pytest.mark.parametrize('raw',['invalid', '{"items":[{"title":"incomplete"}]}'])
def test_invalid_result_preserves_saved_notes(monkeypatch,raw):
    state=ai.build_state([SAMPLE],'en');section=state['sections'][0]
    section['annotations']={'items':[],'created_at':'previous'};before=deepcopy(state)
    async def fixture(*args):return raw
    monkeypatch.setattr(ai,'ai_call',fixture)
    with pytest.raises(HTTPException) as error:asyncio.run(paper_annotations.annotate(state,section,'en'))
    assert error.value.status_code==502 and state==before


def test_version_failure_and_provider_failure_preserve_saved_review(monkeypatch):
    h,url,row=setup_review();section=row['sections'][1];root=f"{url}/{row['id']}";path=root+f"/sections/{section['id']}/annotations"
    async def fixture(*args):return json.dumps({'items':[note(section['original'][20:85])]})
    monkeypatch.setattr(ai,'ai_call',fixture)
    saved=client.post(path,headers=h,json={'version':row['version']})
    assert saved.status_code==200,saved.text
    assert saved.json()['sections'][1]['annotations']['items'][0]['location']
    assert client.post(path,headers=h,json={'version':row['version']}).status_code==409
    async def failed(*args):raise HTTPException(502,'AI_CONNECTION')
    monkeypatch.setattr(ai,'ai_call',failed)
    assert client.post(path,headers=h,json={'version':saved.json()['version']}).status_code==502
    current=client.get(root,headers=h).json()
    assert current['version']==saved.json()['version']
    assert current['sections']==saved.json()['sections']


def test_evaluation_only_can_read_anchored_feedback_without_editor_permissions(monkeypatch):
    ah,_=admin();user=create(ah);h,_=login(user['username'])
    pid=client.post('/api/paper-evaluation/workspace',headers=h).json()['id']
    url=f'/api/projects/{pid}/paper-reviews'
    row=client.post(url,headers=h,files={'file':('paper.txt',SAMPLE.encode(),'text/plain')}).json()
    section=row['sections'][1];root=url+f"/{row['id']}";path=root+f"/sections/{section['id']}/annotations"
    async def fixture(*args):return json.dumps({'items':[note(section['original'][20:85])]})
    monkeypatch.setattr(ai,'ai_call',fixture)
    result=client.post(path,headers=h,json={'version':row['version']})
    assert result.status_code==200,result.text
    assert all(s['draft'] is None and not s['revisions'] for s in result.json()['sections'])
    for action in ('suggest','discuss'):
        assert client.post(root+f"/sections/{section['id']}/{action}",headers=h,json={'version':result.json()['version'],'instruction':'Do it'}).status_code==403
    assert client.patch(root+f"/sections/{section['id']}/draft",headers=h,json={'version':result.json()['version'],'text':'edit'}).status_code==403
    other=create(ah);other_h,_=login(other['username'])
    assert client.post(path,headers=other_h,json={'version':result.json()['version']}).status_code==403
    assert client.post(path,json={'version':result.json()['version']}).status_code==401
