"""Permanent admin-assigned credentials and a genuinely restricted upload/evaluation workflow."""
import json
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.services import paper_review_service as ai
from test_user_access import admin, login, TEMP, CHANGED
from test_paper_reviews import SAMPLE

client=TestClient(app)


def create(headers, grants=None, **extra):
    name='evaluate.'+uuid4().hex[:12]
    response=client.post('/api/admin/users',headers=headers,json={'username':name,'full_name':'Evaluation user','password':TEMP,'permissions':['paper_evaluate'] if grants is None else grants,**extra})
    assert response.status_code==201,response.text
    return response.json()


def test_admin_assigned_password_is_permanent_and_can_be_reset_without_forcing_change():
    ah,_=admin();user=create(ah)
    h,row=login(user['username'])
    assert not row['must_change_password']
    assert client.get('/api/projects',headers=h).status_code==200
    assert client.patch(f"/api/admin/users/{user['id']}",headers=ah,json={'password':CHANGED}).status_code==200
    fresh,row=login(user['username'],CHANGED)
    assert not row['must_change_password']
    assert client.get('/api/auth/me',headers=h).status_code==401
    assert client.get('/api/auth/me',headers=fresh).status_code==200


def test_force_change_is_optional_and_admin_can_remove_it_without_changing_the_password():
    ah,_=admin();user=create(ah,must_change_password=True)
    h,row=login(user['username'])
    assert row['must_change_password']
    assert client.post('/api/paper-evaluation/workspace',headers=h).status_code==403
    assert client.patch(f"/api/admin/users/{user['id']}",headers=ah,json={'must_change_password':False}).status_code==200
    fresh,row=login(user['username'])
    assert not row['must_change_password']
    assert client.post('/api/paper-evaluation/workspace',headers=fresh).status_code==200


def test_evaluation_user_can_upload_analyze_assess_and_read_but_cannot_write_or_discuss(monkeypatch):
    ah,_=admin();user=create(ah);h,_=login(user['username'])
    workspace=client.post('/api/paper-evaluation/workspace',headers=h)
    assert workspace.status_code==200
    pid=workspace.json()['id']
    assert client.post('/api/paper-evaluation/workspace',headers=h).json()['id']==pid
    assert client.post('/api/projects',headers=h,json={'working_title':'Unauthorized general project'}).status_code==403
    assert client.get(f'/api/projects/{pid}',headers=h).status_code==403
    url=f'/api/projects/{pid}/paper-reviews'
    uploaded=client.post(url,headers=h,files={'file':('paper.txt',SAMPLE.encode(),'text/plain')})
    assert uploaded.status_code==201,uploaded.text
    current=uploaded.json();root=url+f"/{current['id']}";sid=current['sections'][0]['id']
    async def fixture(system,payload,json_output=False):
        if 'criteria' in payload:
            section=payload['sections'][0]
            return json.dumps({'items':[{'id':item['id'],'status':'partial','explanation':'Synthetic assessment of the supplied source.','improvement':'Clarify the scope and provide verified supporting references.','evidence':[{'section_id':section['id'],'quote':section['text'][:60]}],'target_section_id':section['id']} for item in payload['criteria']]})
        return json.dumps({'summary':'Synthetic paper evaluation.','strengths':['An identifiable conceptual argument.'],'improvements':['Clarify the research problem and evidence.']})
    monkeypatch.setattr(ai,'ai_call',fixture)
    analyzed=client.post(root+'/analyze?overview_only=true',headers=h,json={'version':current['version']})
    assert analyzed.status_code==200,analyzed.text
    current=analyzed.json()
    assert current['overview']['strengths'] and current['overview']['improvements']
    section=client.post(root+f'/sections/{sid}/analyze',headers=h,json={'version':current['version']})
    assert section.status_code==200;current=section.json()
    assessed=client.post(root+'/compliance/start',headers=h,json={'version':current['version'],'paper_type':'conceptual_legal'})
    assert assessed.status_code==200;current=assessed.json()
    next_step=client.post(root+'/compliance/next',headers=h,json={'version':current['version']})
    assert next_step.status_code==200;current=next_step.json()
    assert current['compliance']['counts']['partial']==3
    assert client.get(root+'/file',headers=h).status_code==200
    for suffix in (f'sections/{sid}/discuss',f'sections/{sid}/suggest','rewrite/start','rewrite/next','rewrite/copy','rewrite/merge'):
        response=client.post(root+'/'+suffix,headers=h,json={'version':current['version'],'instruction':'Attempt forbidden operation.'})
        assert response.status_code==403,(suffix,response.text)
    assert client.patch(root+f'/sections/{sid}/draft',headers=h,json={'version':current['version'],'text':'Forbidden edit.'}).status_code==403
    for suffix in ('desk/sources','documents','library'):
        assert client.get(f'/api/projects/{pid}/'+suffix,headers=h).status_code==403
    assert client.post(f'/api/projects/{pid}/export',headers=h,json={'export_type':'project_summary','format':'markdown'}).status_code==403
    assert client.get('/api/admin/users',headers=h).status_code==403
    assert client.get(root,headers=ah).status_code==200
    other=create(ah);other_h,_=login(other['username'])
    other_pid=client.post('/api/paper-evaluation/workspace',headers=other_h).json()['id']
    assert other_pid!=pid and client.get(root,headers=other_h).status_code==403


def test_unprivileged_accounts_cannot_create_paper_containers():
    ah,_=admin();user=create(ah,grants=[]);h,_=login(user['username'])
    assert client.post('/api/paper-evaluation/workspace',headers=h).status_code==403
    assert client.post('/api/paper-evaluation/workspace').status_code==401


def test_review_user_without_project_creation_receives_private_project_number_one():
    ah,_=admin()
    user=create(ah,grants=['paper_review'],preferred_language='en')
    h,_=login(user['username'])
    assert client.get('/api/projects',headers=h).json()==[]
    first=client.post('/api/paper-evaluation/workspace',headers=h)
    assert first.status_code==200 and first.json()['working_title']=='Project Number One'
    again=client.post('/api/paper-evaluation/workspace',headers=h)
    assert again.json()==first.json()
    projects=client.get('/api/projects',headers=h).json()
    assert len(projects)==1 and projects[0]['id']==first.json()['id']
    assert client.post('/api/projects',headers=h,json={'working_title':'A second project'}).status_code==403
    uploaded=client.post(f"/api/projects/{first.json()['id']}/paper-reviews",headers=h,files={'file':('paper.txt',SAMPLE.encode(),'text/plain')})
    assert uploaded.status_code==201
    other=create(ah,grants=['paper_review'],preferred_language='ar')
    other_h,_=login(other['username'])
    private=client.post('/api/paper-evaluation/workspace',headers=other_h).json()
    assert private['working_title']=='المشروع رقم واحد' and private['id']!=first.json()['id']
    assert client.get(f"/api/projects/{first.json()['id']}/paper-reviews",headers=other_h).status_code==403
