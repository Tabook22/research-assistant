"""Paper review integrity, authorization, parsing and versioned editing."""
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import paper_review_service as svc

client=TestClient(app)
SAMPLE="""A study of learning communities
1. Introduction
This paper explores access to learning resources in coastal communities. The research problem is unequal access to digital resources. The objective is to describe barriers rather than claim causal effects.
2. Methodology
The paper uses a conceptual analysis of published documents. No participant sample is appropriate for this design.
3. Conclusion
Clearer definitions and evidence are needed before policy conclusions can be drawn.
"""

def auth(email):
    data={"email":email,"password":"ReviewTest123!","full_name":"Paper Reviewer","preferred_language":"en"}
    r=client.post("/api/auth/register",json=data)
    if r.status_code==400:
        r=client.post("/api/auth/login",json={"email":email,"password":data["password"]})
    assert r.status_code==200,r.text
    return {"Authorization":"Bearer "+r.json()["access_token"]}

def setup_review():
    h=auth("paper-review@example.com")
    p=client.post("/api/projects",headers=h,json={"working_title":"Paper review test"}).json()["id"]
    url=f"/api/projects/{p}/paper-reviews"
    r=client.post(url,headers=h,files={"file":("paper.txt",SAMPLE.encode(),"text/plain")})
    assert r.status_code==201,r.text
    return h,url,r.json()

def test_arabic_headings_preserve_source_and_page_locations():
    state=svc.build_state(["عنوان الدراسة\n1. تمهيد\n"+"تبحث هذه الدراسة في حماية البيئة البحرية. "*8,"2. آليات تحقيق التوازن\n"+"يلزم توضيح الاختصاص القانوني. "*8,""],"ar")
    assert [s["title"] for s in state["sections"]][1:]==["تمهيد","آليات تحقيق التوازن"]
    assert state["sections"][2]["page_start"]==2
    assert "تبحث هذه الدراسة" in state["sections"][1]["original"]
    assert len(state["warnings"])>=2

def test_upload_validation():
    h,url,_=setup_review()
    assert client.post(url,headers=h,files={"file":("bad.exe",b"x")}).status_code==415
    assert client.post(url,headers=h,files={"file":("empty.txt",b"")}).status_code==400
    assert client.post(url,headers=h,files={"file":("scan.txt",b"no text")}).status_code==422

def test_save_versions_and_reject_stale_write():
    h,url,r=setup_review(); sid=r["sections"][1]["id"]; path=f"{url}/{r['id']}/sections/{sid}/draft"
    text="A researcher-approved revised introduction."
    saved=client.patch(path,headers=h,json={"version":r["version"],"text":text})
    assert saved.status_code==200,saved.text
    s=saved.json()["sections"][1]
    assert s["original"]==r["sections"][1]["original"]
    assert s["draft"]==text and s["revisions"][0]["text"]==text
    assert client.patch(path,headers=h,json={"version":r["version"],"text":"stale overwrite"}).status_code==409
    current=client.get(f"{url}/{r['id']}",headers=h).json()
    assert current["sections"][1]["draft"]==text

def test_reviews_require_project_access():
    h,url,r=setup_review()
    other=auth("paper-intruder@example.com")
    assert client.get(f"{url}/{r['id']}",headers=other).status_code==403
    assert client.get(url).status_code==401
    p=client.post("/api/projects",headers=h,json={"working_title":"Other project"}).json()["id"]
    assert client.get(f"/api/projects/{p}/paper-reviews/{r['id']}",headers=h).status_code==404

def test_analysis_discussion_and_suggestions_do_not_replace_source(monkeypatch):
    h,url,r=setup_review()
    finding={"summary":"A conceptual study of access.","main_ideas":["Define digital access."],"problem_statement":"Unequal access.","problem_status":"inferred","strengths":[],"improvements":["Clarify the scope."],"evidence":["This quotation is invented."],"verification_needed":["Check cited evidence."]}
    async def fake(system,payload,json_output=False):
        assert "UNTRUSTED DATA" in system
        if json_output:
            return json.dumps(finding)
        return "Suggested section wording." if "proposed revised" in payload["task"] else "Explain the boundaries of your research problem."
    monkeypatch.setattr(svc,"ai_call",fake)
    analyzed=client.post(f"{url}/{r['id']}/analyze",headers=h,json={"version":r["version"]})
    assert analyzed.status_code==200,analyzed.text
    r=analyzed.json(); assert r["overview"]["evidence"]==[]
    sid=r["sections"][1]["id"]; root=f"{url}/{r['id']}/sections/{sid}"
    discussed=client.post(root+"/discuss",headers=h,json={"version":r["version"],"instruction":"Explain the problem."})
    assert discussed.status_code==200,discussed.text
    r=discussed.json(); assert len(r["sections"][1]["messages"])==2
    assert len(r["sections"][0]["messages"])==0
    proposed=client.post(root+"/suggest",headers=h,json={"version":r["version"],"instruction":"Improve clarity."})
    assert proposed.status_code==200,proposed.text
    section=proposed.json()["sections"][1]
    assert section["draft"] is None and section["revisions"]==[]
    assert section["proposed_text"]=="Suggested section wording."
    assert section["original"]==r["sections"][1]["original"]

def test_ai_unavailable_keeps_saved_text(monkeypatch):
    h,url,r=setup_review()
    monkeypatch.setattr(svc.get_settings(),"xai_api_key","")
    response=client.post(f"{url}/{r['id']}/analyze",headers=h,json={"version":r["version"]})
    assert response.status_code==503
    current=client.get(f"{url}/{r['id']}",headers=h).json()
    assert current["version"]==r["version"] and current["sections"]==r["sections"]

def test_invalid_ai_analysis_is_not_saved(monkeypatch):
    h,url,r=setup_review()
    async def invalid(*args,**kwargs):
        return '{"overview":{"summary":"Missing all section analyses"},"sections":[]}'
    monkeypatch.setattr(svc,"ai_call",invalid)
    assert client.post(f"{url}/{r['id']}/analyze",headers=h,json={"version":r["version"]}).status_code==502
    assert client.get(f"{url}/{r['id']}",headers=h).json()["overview"] is None


def test_page_counters_and_appendix_do_not_extend_previous_section():
    pages=["1\n1. Introduction\n"+"Background evidence. "*10,"2\n2. Conclusion\n"+"Conclusion content. "*10,"3\nAppendix A\nChart captions and data."]
    state=svc.build_state(pages,"en")
    assert state["sections"][0]["page_end"]==1
    assert state["sections"][1]["page_end"]==2
    assert state["sections"][2]["title"]=="Appendix A"


def test_long_paragraph_is_bounded_without_losing_text():
    text="An uninterrupted paragraph. "*2000
    state=svc.build_state([text],"en")
    assert all(len(s["original"])<=16000 for s in state["sections"])
    assert "".join(s["original"] for s in state["sections"])==text.strip()


def test_only_verbatim_evidence_is_retained():
    result=svc.evidence_check({"evidence":["Actual source sentence.","Invented quotation."]},"Actual source sentence. The rest of the source.")
    assert result["evidence"]==["Actual source sentence."]


def test_incremental_analysis_preserves_checkpoints_and_drafts(monkeypatch):
    from fastapi import HTTPException
    h,url,r=setup_review()
    root=f"{url}/{r['id']}"
    sid=r["sections"][0]["id"]
    r=client.patch(f"{root}/sections/{sid}/draft",headers=h,json={"version":r["version"],"text":"My approved draft."}).json()
    originals=[s["original"] for s in r["sections"]]
    async def good(*args,**kwargs):return json.dumps({"summary":"Grounded review."})
    monkeypatch.setattr(svc,"ai_call",good)
    r=client.post(root+"/analyze?overview_only=true",headers=h,json={"version":r["version"]}).json()
    assert r["overview"] and all(s["analysis"] is None for s in r["sections"])
    assert r["analysis_mode"]=="partial"
    r=client.post(f"{root}/sections/{sid}/analyze",headers=h,json={"version":r["version"]}).json()
    assert sid not in r["analysis_pending_ids"]
    async def timeout(*args,**kwargs):raise HTTPException(504,"AI_TIMEOUT: test timeout")
    monkeypatch.setattr(svc,"ai_call",timeout)
    next_id=r["sections"][1]["id"]
    failed=client.post(f"{root}/sections/{next_id}/analyze",headers=h,json={"version":r["version"]})
    assert failed.status_code==504
    saved=client.get(root,headers=h).json()
    assert saved["version"]==r["version"] and saved["overview"]==r["overview"]
    assert saved["sections"][0]["analysis"]==r["sections"][0]["analysis"]
    assert saved["sections"][0]["draft"]=="My approved draft."
    assert [s["original"] for s in saved["sections"]]==originals
    # A reload can finish the remaining parts without replacing completed analysis.
    monkeypatch.setattr(svc,"ai_call",good)
    for section in saved["sections"][1:]:
        response=client.post(f"{root}/sections/{section['id']}/analyze",headers=h,json={"version":saved["version"]})
        assert response.status_code==200
        saved=response.json()
    assert saved["analysis_mode"]=="ai" and not saved["analysis_pending_ids"]
    # Refresh preserves older findings while tracking which ones still need updating.
    refreshed=client.post(root+"/analyze?overview_only=true",headers=h,json={"version":saved["version"]}).json()
    assert refreshed["analysis_pending_ids"]==[s["id"] for s in saved["sections"]]
    assert refreshed["sections"]==saved["sections"]
    assert refreshed["analysis_mode"]=="partial"


def test_first_overview_keeps_individually_completed_sections(monkeypatch):
    import asyncio
    state=svc.build_state([SAMPLE],"en")
    state["sections"][0]["analysis"]={"summary":"Existing section review."}
    async def good(*args,**kwargs):return json.dumps({"summary":"New overview."})
    monkeypatch.setattr(svc,"ai_call",good)
    reviewed=asyncio.run(svc.analyze(state,"en",overview_only=True))
    assert reviewed["sections"][0]["id"] not in reviewed["analysis_pending_ids"]
    assert reviewed["sections"][0]["analysis"]["summary"]=="Existing section review."


@pytest.mark.parametrize("kind,status,prefix",[("timeout",504,"AI_TIMEOUT"),("connection",502,"AI_CONNECTION"),(429,429,"AI_RATE_LIMIT"),(401,503,"AI_ACCESS"),(400,502,"AI_CONFIGURATION")])
def test_provider_errors_are_actionable_and_do_not_expose_provider_body(monkeypatch,kind,status,prefix):
    import asyncio
    import httpx
    from app.services import ai_gateway
    from fastapi import HTTPException
    request=httpx.Request("POST","https://example.invalid/chat/completions")
    class FakeClient:
        def __init__(self,**kwargs):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*args):return False
        async def request(self,*args,**kwargs):
            if kind=="timeout":raise httpx.ReadTimeout("private secret",request=request)
            if kind=="connection":raise httpx.ConnectError("private secret",request=request)
            return httpx.Response(kind,request=request,json={"private":"secret"})
    monkeypatch.setattr(ai_gateway.httpx,"AsyncClient",FakeClient)
    monkeypatch.setattr(svc.get_settings(),"xai_api_key","dummy-test-key")
    with pytest.raises(HTTPException) as caught:asyncio.run(svc.ai_call("test",{"source":"synthetic"},True))
    assert caught.value.status_code==status and caught.value.detail.startswith(prefix)
    assert "private" not in caught.value.detail and "secret" not in caught.value.detail
