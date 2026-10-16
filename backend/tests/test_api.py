"""API integration tests for critical workflows."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _register(email: str = "researcher@example.com") -> str:
    r = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Test Researcher",
            "password": "securepass1",
            "preferred_language": "en",
        },
    )
    if r.status_code == 400:
        r = client.post(
            "/api/auth/login",
            json={"email": email, "password": "securepass1"},
        )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_health() -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_project_and_question_and_alignment() -> None:
    token = _register("flow@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/projects",
        headers=headers,
        json={
            "working_title": "Digital literacy among nursing students",
            "research_field": "Nursing education",
            "document_type": "research_proposal",
            "writing_language": "en",
            "population_summary": "Undergraduate nursing students",
            "study_context": "University setting",
            "research_idea": "Explore digital literacy levels",
        },
    )
    assert r.status_code == 200, r.text
    project_id = r.json()["id"]
    assert r.json()["profile"] is not None

    r = client.patch(
        f"/api/projects/{project_id}/profile",
        headers=headers,
        json={
            "research_problem": "Limited evidence on digital literacy in this context.",
            "research_gap": "Few local studies measure digital literacy with validated tools.",
            "overall_aim": "Assess digital literacy among undergraduate nursing students.",
        },
    )
    assert r.status_code == 200

    r = client.post(
        f"/api/projects/{project_id}/questions",
        headers=headers,
        json={
            "text": "What is the level of digital literacy among undergraduate nursing students?",
            "question_type": "descriptive",
            "proposed_analysis": "Descriptive statistics",
        },
    )
    assert r.status_code == 200
    qid = r.json()["id"]

    r = client.post(
        f"/api/projects/{project_id}/objectives",
        headers=headers,
        json={
            "text": "Describe the level of digital literacy among undergraduate nursing students.",
            "question_id": qid,
            "verb": "Describe",
        },
    )
    assert r.status_code == 200

    r = client.post(f"/api/projects/{project_id}/alignment/check", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert "issues" in body
    assert body["chain_status"]["research_questions"] == "present"
    assert body["chain_status"]["overall_aim"] == "present"

    r = client.post(
        f"/api/projects/{project_id}/export",
        headers=headers,
        json={"export_type": "project_summary", "format": "markdown"},
    )
    assert r.status_code == 200
    assert "Research Project Summary" in r.json()["content"]


def test_chat_offline_welcome() -> None:
    token = _register("chat@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post(
        "/api/projects",
        headers=headers,
        json={"working_title": "Chat test project", "document_type": "masters_thesis"},
    )
    pid = r.json()["id"]
    r = client.get(f"/api/projects/{pid}/chat/conversation", headers=headers)
    assert r.status_code == 200
    assert len(r.json()["messages"]) >= 1
    assert "Welcome" in r.json()["messages"][0]["content"]
