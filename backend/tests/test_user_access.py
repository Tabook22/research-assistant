"""Tenant isolation, server-enforced grants, account management and session revocation."""
import json
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, inspect
from app.main import app
from app.database import SessionLocal
from app.models.user import User
from app.models.project import ProjectMember
from app.core.security import hash_password
from app.config import get_settings
from app.services.permissions import PERMISSIONS
from app.services.user_migration import migrate_user_access

client=TestClient(app)
TEMP='SyntheticTemporary123!'
CHANGED='SyntheticChanged456!'

def login(username,password=TEMP):
    response=client.post('/api/auth/login',json={'username':username,'password':password})
    assert response.status_code==200,response.text
    return {'Authorization':'Bearer '+response.json()['access_token']},response.json()['user']

def admin():
    name='admin.'+uuid4().hex[:12]
    with SessionLocal() as db:
        row=User(username=name,email=name+'@example.com',full_name='QA Admin',hashed_password=hash_password(TEMP),is_superuser=True,permissions=PERMISSIONS)
        db.add(row);db.commit()
    return login(name)

def managed(headers,permissions=None):
    name='user.'+uuid4().hex[:12]
    response=client.post('/api/admin/users',headers=headers,json={'username':name,'full_name':'QA Researcher','password':TEMP,'permissions':PERMISSIONS if permissions is None else permissions})
    assert response.status_code==201,response.text
    session,user=login(name)
    assert user['must_change_password']
    assert client.get('/api/projects',headers=session).status_code==403
    changed=client.patch('/api/auth/account',headers=session,json={'current_password':TEMP,'new_password':CHANGED})
    assert changed.status_code==200,changed.text
    return {'Authorization':'Bearer '+changed.json()['access_token']},changed.json()['user']

def project(headers,user):
    response=client.post(f"/api/admin/users/{user['id']}/projects",headers=headers,json={'working_title':'Private project'})
    assert response.status_code==201,response.text
    return response.json()['id']

def test_account_creation_force_change_and_no_self_escalation():
    ah,_=admin();h,user=managed(ah,[])
    assert not user['is_superuser'] and user['permissions']==[]
    assert client.get('/api/admin/users',headers=h).status_code==403
    assert client.post('/api/projects',headers=h,json={'working_title':'Unauthorized'}).status_code==403
    response=client.patch('/api/auth/account',headers=h,json={'current_password':CHANGED,'is_superuser':True,'permissions':PERMISSIONS})
    assert response.status_code==200
    assert not response.json()['user']['is_superuser'] and response.json()['user']['permissions']==[]

def test_workspace_and_original_files_are_private_except_for_admin():
    ah,_=admin();h,a=managed(ah);other,b=managed(ah);pid=project(ah,a)
    path=f'/api/projects/{pid}/paper-reviews'
    uploaded=client.post(path,headers=h,files={'file':('private.txt',b'Synthetic private research source. '*15,'text/plain')})
    assert uploaded.status_code==201
    rid=uploaded.json()['id']
    assert all(p['id']!=pid for p in client.get('/api/projects',headers=other).json())
    with SessionLocal() as db:
        db.add(ProjectMember(project_id=pid,user_id=b['id'],role='editor'));db.commit()
    assert client.get(path,headers=other).status_code==403
    assert client.get(f'{path}/{rid}/file',headers=other).status_code==403
    assert client.get(f'{path}/{rid}/file',headers=ah).status_code==200
    assert [p['id'] for p in client.get('/api/auth/papers',headers=h).json()]==[rid]
    assert client.get('/api/auth/papers',headers=other).json()==[]
    workspace=client.get(f"/api/admin/users/{a['id']}/workspace",headers=ah).json()
    assert workspace['papers'][0]['id']==rid
    assert workspace['projects'][0]['id']==pid

def test_page_permissions_cover_api_and_immediate_updates():
    ah,_=admin();h,user=managed(ah,['paper_review']);pid=project(ah,user)
    assert client.get(f'/api/projects/{pid}/paper-reviews',headers=h).status_code==200
    for path in ['desk/sources','library','documents','chat/conversation','questions']:
        assert client.get(f'/api/projects/{pid}/{path}',headers=h).status_code==403,path
    updated=client.patch(f"/api/admin/users/{user['id']}",headers=ah,json={'permissions':['library']})
    assert updated.status_code==200
    assert client.get('/api/auth/me',headers=h).status_code==401
    fresh,_=login(user['username'],CHANGED)
    assert client.get(f'/api/projects/{pid}/paper-reviews',headers=fresh).status_code==403
    assert client.get(f'/api/projects/{pid}/library',headers=fresh).status_code==200

def test_desk_only_user_can_load_sources_and_reference_metadata():
    ah,_=admin();h,user=managed(ah,['research_desk']);pid=project(ah,user)
    assert client.get(f'/api/projects/{pid}/desk/sources',headers=h).status_code==200
    assert client.get(f'/api/projects/{pid}/references',headers=h).status_code==200
    assert client.get(f'/api/projects/{pid}/documents',headers=h).status_code==403

def test_promotion_demotion_deactivation_and_password_reset():
    ah,owner=admin();h,user=managed(ah,[]);url=f"/api/admin/users/{user['id']}"
    assert client.patch(url,headers=ah,json={'is_superuser':True}).status_code==200
    elevated,_=login(user['username'],CHANGED)
    assert client.get('/api/admin/users',headers=elevated).status_code==200
    assert client.patch(f"/api/admin/users/{owner['id']}",headers=ah,json={'is_active':False}).status_code==409
    assert client.patch(f"/api/admin/users/{owner['id']}",headers=ah,json={'is_superuser':False}).status_code==409
    assert client.patch(url,headers=ah,json={'is_superuser':False,'is_active':False}).status_code==200
    assert client.get('/api/auth/me',headers=elevated).status_code==401
    assert client.post('/api/auth/login',json={'username':user['username'],'password':CHANGED}).status_code==401
    assert client.patch(url,headers=ah,json={'is_active':True,'password':TEMP}).status_code==200
    reset,row=login(user['username'])
    assert row['must_change_password'] and not row['is_superuser']
    assert client.get('/api/projects',headers=reset).status_code==403
    assert client.get('/api/auth/me',headers=h).status_code==401

def test_admin_can_change_own_username_password_without_old_sessions():
    ah,user=admin();newname='renamed.'+uuid4().hex[:12]
    assert client.patch('/api/auth/account',headers=ah,json={'current_password':'wrong','username':newname}).status_code==400
    changed=client.patch('/api/auth/account',headers=ah,json={'current_password':TEMP,'username':newname,'new_password':CHANGED})
    assert changed.status_code==200,changed.text
    assert changed.json()['user']['username']==newname
    assert client.get('/api/auth/me',headers=ah).status_code==401
    fresh,row=login(newname,CHANGED)
    assert row['is_superuser'] and client.get('/api/admin/users',headers=fresh).status_code==200
    assert client.post('/api/auth/login',json={'username':user['username'],'password':TEMP}).status_code==401

def test_closed_registration_and_duplicate_users(monkeypatch):
    ah,user=admin()
    monkeypatch.setattr(get_settings(),'allow_registration',False)
    assert not client.get('/api/auth/config').json()['allow_registration']
    assert client.post('/api/auth/register',json={'email':'new@example.com','full_name':'Public signup','password':TEMP,'is_superuser':True}).status_code==403
    assert client.post('/api/admin/users',headers=ah,json={'username':user['username'].upper(),'full_name':'Duplicate','password':TEMP}).status_code==409
    assert client.post('/api/admin/users',headers=ah,json={'username':'invalid name','full_name':'Invalid','password':TEMP}).status_code==422
    assert client.post('/api/admin/users',headers=ah,json={'username':'qa.valid','full_name':'Invalid grants','password':TEMP,'permissions':['admin']}).status_code==422

def test_additive_user_migration_preserves_legacy_rows():
    engine=create_engine('sqlite://')
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)'))
        connection.execute(text("INSERT INTO users (id,email) VALUES (1,'legacy@example.com')"))
    migrate_user_access(engine);migrate_user_access(engine)
    with engine.connect() as connection:
        row=connection.execute(text('SELECT * FROM users')).mappings().one()
        assert row['email']=='legacy@example.com' and row['auth_version']==0
        assert json.loads(row['permissions'])==PERMISSIONS
    assert 'username' in {c['name'] for c in inspect(engine).get_columns('users')}
