"""Research desk isolation, immutable evidence, citation validation and durable tasks."""
import asyncio
from copy import deepcopy
from io import BytesIO
import json
import zipfile
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.paper_review import PaperReview
from app.models.research_desk import ResearchJob, ResearchPassage, ResearchBrief
from app.services import research_retrieval as retrieval, research_coach as coach, research_jobs as workers, research_discovery as discovery

client=TestClient(app)

def auth(email="desk@example.com"):
    payload={"email":email,"password":"DeskTest123!","full_name":"Research Desk Tester","preferred_language":"en"}
    r=client.post("/api/auth/register",json=payload)
    if r.status_code==400:r=client.post("/api/auth/login",json={"email":email,"password":payload["password"]})
    assert r.status_code==200,r.text
    return {"Authorization":"Bearer "+r.json()["access_token"]}

def workspace():
    h=auth();p=client.post("/api/projects",headers=h,json={"working_title":"Evidence-grounded research"}).json()["id"]
    with SessionLocal() as db:
        a=PaperReview(project_id=p,filename="coastal-study.pdf",language="en",state={"analysis_mode":"structure_only","source_format":"pdf","source_pages":[{"number":1,"text":"Background to coastal learning communities. "*12},{"number":2,"text":"Methods used a documentary review. Digital access barriers affected participation. Evidence was limited to published sources. "*10}],"sections":[{"id":1,"title":"Methods","page_start":2,"page_end":2,"original":"Original documentary method.","draft":"UNSUPPORTED NEW FINDING MUST NOT BE INDEXED"}]})
        b=PaperReview(project_id=p,filename="second-study.txt",language="en",state={"analysis_mode":"structure_only","sections":[{"id":1,"title":"Discussion","original":"Digital access barriers were discussed. This conceptual paper makes no empirical causal claim.","page_start":1,"page_end":1}]})
        db.add_all([a,b]);db.commit();aid=a.id;bid=b.id
    return h,p,f"/api/projects/{p}/desk",aid,bid

def task(h,url,kind="search",**extra):
    r=client.post(url+"/jobs",headers=h,json={"kind":kind,"query":"digital access barriers","semantic":False,**extra})
    assert r.status_code==202,r.text
    job=client.get(url+f"/jobs/{r.json()['id']}",headers=h)
    assert job.status_code==200,job.text
    return job.json()

def passage(h,url):
    response=task(h,url)
    assert response["status"]=="completed",response
    return response["result"]["matches"][0]

def save_card(h,url,p):
    r=client.post(url+"/evidence",headers=h,json={"passage_id":p["id"],"fingerprint":p["fingerprint"],"claim":"Digital access may limit participation.","quote":"Digital access barriers affected participation.","notes":"Documentary review; not causal evidence.","relationship":"context"})
    assert r.status_code==201,r.text
    return r.json()

def test_incremental_original_text_index_and_pdf_locations():
    h,p,url,a,b=workspace()
    first=client.get(url+"/sources",headers=h).json()
    assert first["index"]["sources"]==2
    second=client.get(url+"/sources",headers=h).json()
    assert second["index"]["updated_passages"]==0
    match=passage(h,url)
    assert match["location"]=="PDF page 2"
    with SessionLocal() as db:
        assert not any("UNSUPPORTED" in x.text for x in db.query(ResearchPassage).filter_by(project_id=p).all())

def test_search_is_scoped_and_unicode_normalized():
    assert retrieval.terms("إطار البيئة البحرية") == retrieval.terms("اطار البيئة البحرية")
    h,p,url,a,b=workspace();match=passage(h,url)
    other=auth("desk-intruder@example.com")
    assert client.get(url+"/sources",headers=other).status_code==403
    assert client.get(url+"/sources").status_code==401
    p2=client.post("/api/projects",headers=h,json={"working_title":"Other isolated project"}).json()["id"]
    second=f"/api/projects/{p2}/desk"
    assert task(h,second)["result"]["matches"]==[]
    assert client.get(second+f"/passages/{match['id']}",headers=h).status_code==404

def test_evidence_quote_validation_snapshot_and_stale_source():
    h,p,url,a,b=workspace();match=passage(h,url);e=save_card(h,url,match)
    bad={"passage_id":match["id"],"fingerprint":match["fingerprint"],"claim":"Unsupported claim","quote":"This quote is fabricated."}
    assert client.post(url+"/evidence",headers=h,json=bad).status_code==422
    with SessionLocal() as db:
        row=db.get(PaperReview,a);state=deepcopy(row.state);state["source_pages"][1]["text"]="Changed original source content. "*20;row.state=state;db.commit()
    client.get(url+"/sources",headers=h)
    bad["quote"]=match["text"][:40]
    assert client.post(url+"/evidence",headers=h,json=bad).status_code==409
    saved=client.get(url+"/evidence",headers=h).json()[0]
    assert saved["source"]["text"]==e["source"]["text"]

def test_evidence_edits_and_memory_reject_stale_updates():
    h,p,url,a,b=workspace();e=save_card(h,url,passage(h,url))
    payload={"version":e["version"],"notes":"Potential contradictory evidence","relationship":"contradicts"}
    assert client.patch(url+f"/evidence/{e['id']}",headers=h,json=payload).status_code==200
    assert client.patch(url+f"/evidence/{e['id']}",headers=h,json=payload).status_code==409
    assert client.put(url+"/brief",headers=h,json={"version":0,"content":"Study scope: conceptual analysis only."}).status_code==200
    assert client.put(url+"/brief",headers=h,json={"version":0,"content":"Stale"}).status_code==409
    assert client.put(url+"/brief",headers=h,json={"version":1,"content":"Updated scope"}).status_code==200

def test_grounded_output_discards_forged_quotes_and_unknown_ids(monkeypatch):
    async def fake(*args,**kwargs):
        return json.dumps({"claims":[{"text":"Good","citations":[{"passage_id":7,"quote":"Exact source passage."}]},{"text":"Forged","citations":[{"passage_id":7,"quote":"Fabricated evidence."}]},{"text":"Foreign","citations":[{"passage_id":99,"quote":"Exact source passage."}]}]})
    monkeypatch.setattr(coach,"ai_call",fake)
    result=asyncio.run(coach.grounded("ask","What happened?",[{"id":7,"title":"Paper","location":"PDF page 2","text":"Exact source passage."}],"","en"))
    assert [c["text"] for c in result["claims"]]==["Good"]
    assert any("omitted" in s for s in result["limitations"])

def test_jobs_receive_brief_and_can_draft_export_without_mutating_sources(monkeypatch):
    h,p,url,a,b=workspace();e=save_card(h,url,passage(h,url))
    client.put(url+"/brief",headers=h,json={"version":0,"content":"Remember this scope."})
    async def fake(system,payload,json_output=False):
        assert "UNTRUSTED DATA" in system
        assert payload["research_brief"]=="Remember this scope."
        source=payload["source_passages"][0]
        return json.dumps({"claims":[{"text":"The reviewed evidence identifies barriers; this does not establish causation.","citations":[{"passage_id":source["passage_id"],"quote":"Digital access barriers affected participation."}]}]})
    monkeypatch.setattr(coach,"ai_call",fake)
    j=task(h,url,"write",evidence_ids=[e["id"]])
    assert j["status"]=="completed",j
    created=client.post(url+f"/jobs/{j['id']}/draft",headers=h)
    assert created.status_code==201,created.text
    d=created.json();assert f"[E{e['id']}]" in d["text"]
    patched=client.patch(url+f"/drafts/{d['id']}",headers=h,json={"version":d["version"],"title":"My draft","text":d["text"]+" Researcher edit."})
    assert patched.status_code==200,patched.text
    assert patched.json()["revisions"][0]["text"]==d["text"]
    assert client.patch(url+f"/drafts/{d['id']}",headers=h,json={"version":d["version"],"title":"Stale","text":"Overwrite"}).status_code==409
    exported=client.get(url+f"/drafts/{d['id']}/export?format=docx",headers=h)
    assert exported.status_code==200
    with zipfile.ZipFile(BytesIO(exported.content)) as archive:
        xml=archive.read("word/document.xml").decode()
        assert "Digital access barriers" in xml and "PDF page 2" in xml
    with SessionLocal() as db:assert db.get(PaperReview,a).state["sections"][0]["original"]=="Original documentary method."

def test_compare_context_includes_each_selected_paper(monkeypatch):
    h,p,url,a,b=workspace()
    async def fake(kind,query,items,brief,language):
        assert {s["source_key"] for s in items}=={f"review:{a}",f"review:{b}"}
        return {"claims":[],"limitations":["No causal comparison is supported."]}
    monkeypatch.setattr(workers,"grounded",fake)
    j=task(h,url,"compare",source_keys=[f"review:{a}",f"review:{b}"])
    assert j["status"]=="completed",j
    assert client.post(url+"/jobs",headers=h,json={"kind":"compare","query":"Compare methods","source_keys":[f"review:{a}"]}).status_code==422

def test_cancelled_job_does_not_save_late_result(monkeypatch):
    h,p,url,a,b=workspace()
    async def cancel_midflight(*args,**kwargs):
        with SessionLocal() as db:
            row=db.query(ResearchJob).filter_by(project_id=p,status="running").first();row.status="cancelled";db.commit()
        return {"claims":[{"text":"Late response"}]}
    monkeypatch.setattr(workers,"grounded",cancel_midflight)
    j=task(h,url,"ask")
    assert j["status"]=="cancelled" and j["result"] is None

def test_discovery_deduplicates_and_reports_provider_failure(monkeypatch):
    async def fake(client,url,params=None,headers=None):
        if "openalex" in url:return {"results":[{"title":"A shared paper","doi":"https://doi.org/10.1234/test","publication_year":2024,"authorships":[]}]}
        if "crossref" in url:return {"message":{"items":[{"title":["A shared paper"],"DOI":"10.1234/test","author":[]}]}}
        raise RuntimeError("rate limited")
    monkeypatch.setattr(discovery,"fetch_json",fake)
    result=asyncio.run(discovery.discover("digital learning"))
    assert len(result["results"])==1
    assert result["results"][0]["providers"]==["Crossref","OpenAlex"]
    assert result["results"][0]["coverage"]=="metadata"
    assert result["providers"][2]["status"]=="unavailable"

def test_discovery_import_is_scoped_deduplicated_and_not_fulltext(monkeypatch):
    h,p,url,a,b=workspace()
    async def fake(*args,**kwargs):return {"results":[{"title":"Discovered paper","authors":"Researcher A","year":2024,"doi":"10.1234/paper","url":"https://doi.org/10.1234/paper","providers":["Crossref"]}],"providers":[{"provider":"Crossref","status":"ok"}]}
    monkeypatch.setattr(workers,"discover",fake)
    j=task(h,url,"discover")
    imported=client.post(url+f"/jobs/{j['id']}/import/0",headers=h).json()
    again=client.post(url+f"/jobs/{j['id']}/import/0",headers=h).json()
    assert imported["id"]==again["id"] and again["already_saved"]
    refs=client.get(f"/api/projects/{p}/references",headers=h).json()
    assert refs[0]["full_text_reviewed"] is False and refs[0]["verification_status"]=="metadata_retrieved"

def test_crossref_title_mismatch_and_retraction_notice(monkeypatch):
    class Ref:doi="10.1234/test";title="An unrelated manuscript"
    async def fake(*args,**kwargs):return {"message":{"title":["Different registered paper"],"updated-by":[{"type":"retraction","DOI":"10.1234/retraction"}]}}
    monkeypatch.setattr(discovery,"fetch_json",fake)
    result=asyncio.run(discovery.verify_reference(Ref()))
    assert result["status"]=="metadata_mismatch" and result["retraction_notice"]

def test_semantic_unavailable_falls_back_honestly(monkeypatch):
    h,p,url,a,b=workspace()
    monkeypatch.setattr(retrieval.get_settings(),"embedding_model","")
    result=asyncio.run(_search_project(p))
    assert result["mode"]=="keyword" and result["matches"]
    assert any("not configured" in w for w in result["warnings"])

async def _search_project(p):
    with SessionLocal() as db:return await retrieval.search(db,p,"digital access",semantic=True)


def test_query_expansion_can_find_translated_terms(monkeypatch):
    h,p,url,a,b=workspace()
    async def expanded(project,query):return ["digital access barriers"],""
    monkeypatch.setattr(retrieval,"expand_query",expanded)
    result=asyncio.run(_translated_search(p))
    assert result["mode"]=="expanded_keyword" and result["matches"]
    assert result["query_expansions"]==["digital access barriers"]

async def _translated_search(project):
    with SessionLocal() as db:return await retrieval.search(db,project,"عوائق المشاركة الرقمية",semantic=True)


def test_semantic_vectors_are_cached_between_searches(monkeypatch):
    import openai
    from types import SimpleNamespace
    h,p,url,a,b=workspace();calls=[]
    cfg=retrieval.get_settings()
    monkeypatch.setattr(cfg,"embedding_model","test-model")
    monkeypatch.setattr(cfg,"embedding_api_key","synthetic-key")
    class Embeddings:
        async def create(self,model,input):
            calls.append(len(input))
            return SimpleNamespace(data=[SimpleNamespace(index=i,embedding=[1.0,.1]) for i,_ in enumerate(input)])
    class Client:
        def __init__(self,**kwargs):self.embeddings=Embeddings()
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
    monkeypatch.setattr(openai,"AsyncOpenAI",Client)
    with SessionLocal() as db:
        first=asyncio.run(retrieval.search(db,p,"digital access",semantic=True))
        before=len(calls)
        second=asyncio.run(retrieval.search(db,p,"digital access",semantic=True))
    assert first["mode"]==second["mode"]=="hybrid"
    assert len(calls)==before+1 # second call embeds only the query, not unchanged source passages


def test_original_upload_is_retrievable_and_private_paths_are_hidden():
    h,p,url,a,b=workspace()
    upload=client.post(f"/api/projects/{p}/paper-reviews",headers=h,files={"file":("retained.txt",("Original source text about digital evidence. "*12).encode(),"text/plain")})
    assert upload.status_code==201,upload.text
    result=upload.json();assert "_source_file" not in result
    original=client.get(f"/api/projects/{p}/paper-reviews/{result['id']}/file",headers=h)
    assert original.status_code==200 and "Original source text" in original.text
    other=auth("desk-file-intruder@example.com")
    assert client.get(f"/api/projects/{p}/paper-reviews/{result['id']}/file",headers=other).status_code==403


def test_reference_checks_are_persisted_and_cached(monkeypatch):
    import app.api.research_desk as routes
    h,p,url,a,b=workspace();count=[]
    ref=client.post(f"/api/projects/{p}/references",headers=h,json={"title":"Metadata test paper","doi":"10.1234/metadata"}).json()
    async def fake(row):count.append(row.id);return {"status":"metadata_found","message":"Metadata only."}
    monkeypatch.setattr(routes,"verify_reference",fake)
    one=client.post(url+f"/references/{ref['id']}/verify",headers=h)
    two=client.post(url+f"/references/{ref['id']}/verify",headers=h)
    assert one.status_code==two.status_code==200
    assert len(count)==1 and two.json()["cached"]
    saved=client.get(url+"/reference-checks",headers=h).json()
    assert saved[str(ref["id"])]["status"]=="metadata_found"


def test_source_reference_links_are_scoped_and_export_to_ris():
    h,p,url,a,b=workspace();match=passage(h,url)
    ref=client.post(f"/api/projects/{p}/references",headers=h,json={"title":"Linked source record","authors":"Author text to check","year":2024,"doi":"10.1234/link"}).json()
    linked=client.put(url+"/source-reference",headers=h,json={"source_key":match["source_key"],"reference_id":ref["id"]})
    assert linked.status_code==200,linked.text
    card=save_card(h,url,match)
    assert card["source"]["reference"]["doi"]=="10.1234/link"
    result=client.get(url+"/references/export",headers=h)
    assert result.status_code==200 and "DO  - 10.1234/link" in result.text
    assert "Author metadata needs checking" in result.text
    p2=client.post("/api/projects",headers=h,json={"working_title":"Other references"}).json()["id"]
    assert client.put(f"/api/projects/{p2}/desk/source-reference",headers=h,json={"source_key":match["source_key"],"reference_id":ref["id"]}).status_code==404
