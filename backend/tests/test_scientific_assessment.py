"""Scientific scoring semantics, verifiable anchors, checkpointing and tenant isolation."""
from copy import deepcopy
import json
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.services import scientific_assessment as assessment
from app.services import scientific_rubric as rubric
from app.services import paper_review_service as ai
from test_paper_reviews import setup_review,auth

client=TestClient(app)

def fake_judgments(payload,status='met'):
    section=payload['sections'][0]
    return {'items':[{'id':item['id'],'status':status,'explanation':'The supplied text supports this assessment; reviewer verification remains necessary.','improvement':'Clarify the scope and support the central claim.','evidence':[{'section_id':section['id'],'quote':section['text'][:80]}] if status in ('met','partial') else [],'target_section_id':section['id']} for item in payload['criteria']]}

def start_review(basis='working',paper_type='general'):
    h,url,r=setup_review();root=f"{url}/{r['id']}"
    response=client.post(root+'/compliance/start',headers=h,json={'version':r['version'],'paper_type':paper_type,'basis':basis})
    assert response.status_code==200,response.text
    return h,root,r,response.json()

def test_score_is_documented_fulfilment_with_explicit_unknowns_and_exemptions():
    items=[{'result':{'status':status}} if status else {'result':None} for status in ['met','partial','missing','unknown','not_applicable',None]]
    result=assessment.summarize({'items':items})
    assert result['score']==30 and result['score_upper']==70
    assert result['assessment_coverage']==60 and result['applicable_count']==5
    assert result['verdict']=='in_progress' and not result['complete']
    all_unknown=assessment.summarize({'items':[{'result':{'status':'unknown'}}]})
    assert all_unknown['score']==0 and all_unknown['score_upper']==100
    assert all_unknown['verdict']=='insufficient_evidence'
    excluded=assessment.summarize({'items':[{'result':{'status':'not_applicable'}}]})
    assert excluded['score'] is None and excluded['verdict']=='insufficient_evidence'

def test_high_percentage_is_not_an_arbitrary_quality_pass():
    result=assessment.summarize({'items':[{'result':{'status':'met'}} for _ in range(19)]+[{'result':{'status':'partial'}}]})
    assert result['score']==97.5 and result['verdict']=='needs_improvement'
    complete=assessment.summarize({'items':[{'result':{'status':'met'}}]})
    assert complete['verdict']=='meets_reviewed_text_criteria'

def test_catalog_adapts_requirements_and_does_not_apply_health_guidelines_universally():
    legal=rubric.rubric('conceptual_legal');quant=rubric.rubric('quantitative')
    assert 'legal_scope' in {item['id'] for item in legal}
    assert not any(item['source_id'] in ('consort','strobe') for item in legal+quant)
    assert {'review_search','review_appraisal','review_protocol'}<={item['id'] for item in rubric.rubric('systematic_review')}
    assert all(item['description_ar'] and item['guidance_ar'] for kind in rubric.TYPES for item in rubric.rubric(kind['id']))

def test_arabic_unicode_and_whitespace_anchors_preserve_the_exact_original_and_page():
    text='🙂 مقدمة\nنبحث في حماية\nالبيئة البحرية وتحقيق التوازن.'
    state=ai.build_state([text+'\n'+'نص إضافي. '*20],'ar')
    section=state['sections'][0]
    loc=assessment.location(state,section,'نبحث في حماية البيئة البحرية','original')
    assert loc['page']==1 and loc['section_id']==section['id']
    assert section['original'][loc['start']:loc['end']]==loc['quote']
    assert loc['quote']=='نبحث في حماية\nالبيئة البحرية'

def test_unverifiable_quotes_and_invalid_exemptions_cannot_inflate_the_score():
    state=ai.build_state(['A readable synthetic paper. '*12],'en');item=rubric.CORE[0]
    judgment=assessment.Judgment(id=item['id'],status='met',explanation='A claimed finding.',improvement='',evidence=[{'section_id':1,'quote':'This invented quote does not occur in the paper.'}],target_section_id=999)
    result=assessment.validate_judgment(state,item,judgment,'original')
    assert result['status']=='unknown' and result['locations']==[] and result['target_section_id'] is None
    exempt=judgment.model_copy(update={'status':'not_applicable','evidence':[]})
    assert assessment.validate_judgment(state,item,exempt,'original')['status']=='unknown'
    ethics=next(item for item in rubric.CORE if item['id']=='ethics')
    assert assessment.validate_judgment(state,ethics,exempt,'original')['status']=='not_applicable'

def test_working_copy_and_original_have_separate_fingerprints_and_evidence():
    state=ai.build_state(['Original source material with a research question. '*5],'en')
    original=assessment.fingerprint(state,'original');working=assessment.fingerprint(state,'working')
    fallback=assessment.location(state,state['sections'][0],'Original source material','working')
    assert fallback['basis']=='original' and fallback['page']==1
    state['sections'][0]['draft']='An explicitly saved researcher revision.'
    assert assessment.fingerprint(state,'original')==original
    assert assessment.fingerprint(state,'working')!=working
    assert assessment.location(state,state['sections'][0],'explicitly saved researcher revision','original') is None
    assert assessment.location(state,state['sections'][0],'explicitly saved researcher revision','working')['page'] is None
    state['sections'][0]['draft']=''
    assert assessment.text_for(state['sections'][0],'working')==''

def test_failed_batch_keeps_checkpoints_and_retry_finishes_without_touching_drafts(monkeypatch):
    h,root,original,r=start_review(paper_type='conceptual_legal')
    assert r['compliance']['counts']['pending']==len(rubric.rubric('conceptual_legal'))
    async def good(system,payload,json_output=False):
        assert 'UNTRUSTED DATA' in system and 'NOT an official checklist' in system
        return json.dumps(fake_judgments(payload))
    monkeypatch.setattr(ai,'ai_call',good)
    first=client.post(root+'/compliance/next',headers=h,json={'version':r['version']})
    assert first.status_code==200,first.text
    r=first.json();assert r['compliance']['counts']['met']==3
    async def timeout(*args,**kwargs):raise HTTPException(504,'AI_TIMEOUT: synthetic timeout')
    monkeypatch.setattr(ai,'ai_call',timeout)
    assert client.post(root+'/compliance/next',headers=h,json={'version':r['version']}).status_code==504
    saved=client.get(root,headers=h).json()
    assert saved['version']==r['version'] and saved['compliance']==r['compliance']
    monkeypatch.setattr(ai,'ai_call',good)
    while not saved['compliance']['complete']:
        response=client.post(root+'/compliance/next',headers=h,json={'version':saved['version']})
        assert response.status_code==200,response.text
        saved=response.json()
    assert saved['compliance']['score']==100 and saved['compliance']['assessment_coverage']==100
    assert saved['sections']==original['sections'] and saved['overview']==original['overview']

@pytest.mark.parametrize('failure',['missing','duplicate','extra_score'])
def test_malformed_batches_are_not_saved(monkeypatch,failure):
    h,root,_,r=start_review()
    async def bad(system,payload,json_output=False):
        data=fake_judgments(payload)
        if failure=='missing':data['items'].pop()
        elif failure=='duplicate':data['items'][1]=data['items'][0]
        else:data['score']=100
        return json.dumps(data)
    monkeypatch.setattr(ai,'ai_call',bad)
    assert client.post(root+'/compliance/next',headers=h,json={'version':r['version']}).status_code==502
    saved=client.get(root,headers=h).json()
    assert saved['version']==r['version'] and saved['compliance']['counts']['met']==0

def test_draft_edits_invalidate_working_report_and_keep_previous_report_on_restart():
    h,root,original,r=start_review()
    section=r['sections'][0]
    changed=client.patch(f"{root}/sections/{section['id']}/draft",headers=h,json={'version':r['version'],'text':'A new saved working paragraph.'})
    assert changed.status_code==200
    saved=changed.json();assert saved['compliance']['stale']
    assert client.post(root+'/compliance/next',headers=h,json={'version':saved['version']}).status_code==409
    refreshed=client.post(root+'/compliance/start',headers=h,json={'version':saved['version'],'paper_type':'proposal','basis':'working'}).json()
    assert not refreshed['compliance']['stale'] and refreshed['previous_compliance']['paper_type']=='general'
    assert refreshed['sections'][0]['draft']=='A new saved working paragraph.'

def test_version_conflicts_and_unauthorized_users_cannot_assess_another_paper():
    h,root,_,r=start_review()
    other=auth('criteria-intruder@example.com')
    assert client.post(root+'/compliance/next',headers=other,json={'version':r['version']}).status_code==403
    assert client.post(root+'/compliance/start',headers=h,json={'version':r['version']-1}).status_code==409
    assert client.post(root+'/compliance/start',headers=h,json={'version':r['version'],'paper_type':'invented'}).status_code==422
    catalog=client.get(root.rsplit('/',1)[0]+'/criteria/catalog',headers=h)
    assert catalog.status_code==200 and catalog.json()['version']==rubric.VERSION

def test_long_text_is_never_silently_truncated_or_scored():
    state=ai.build_state(['A long document paragraph. '*6000],'en')
    with pytest.raises(HTTPException) as caught:assessment.start(deepcopy(state),'general','original')
    assert caught.value.status_code==413 and 'compliance' not in state

def test_original_assessment_survives_unrelated_draft_changes_and_rubric_revision_invalidates(monkeypatch):
    state=ai.build_state(['Original source text. '*12],'en')
    assessment.start(state,'general','original');report=state['compliance']
    state['sections'][0]['draft']='An unrelated draft change.'
    assert not assessment.stale(state,report)
    monkeypatch.setattr(rubric,'VERSION','future-version')
    assert assessment.stale(state,report)
