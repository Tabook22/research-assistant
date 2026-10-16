"""Tests for structured AI suggestion apply workflow."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _token(email: str = "sug@example.com") -> str:
    r = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Suggestion Tester",
            "password": "securepass1",
            "preferred_language": "en",
        },
    )
    if r.status_code == 400:
        r = client.post("/api/auth/login", json={"email": email, "password": "securepass1"})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_offline_chat_emits_structure_suggestions_and_apply() -> None:
    token = _token("offline_sug@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/projects",
        headers=headers,
        json={
            "working_title": "Digital literacy among students",
            "research_field": "Education",
            "document_type": "research_proposal",
            "population_summary": "undergraduate students",
        },
    )
    assert r.status_code == 200
    pid = r.json()["id"]

    r = client.post(
        f"/api/projects/{pid}/chat/messages",
        headers=headers,
        json={
            "content": "Build research questions",
            "special_command": "Build research questions",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # Offline mode should produce structure cards
    assert "suggestions" in body
    # May be empty if offline heuristics don't fire; force via list after command
    r = client.get(f"/api/projects/{pid}/suggestions", headers=headers)
    assert r.status_code == 200
    pending = r.json()
    # Offline build_research_questions should create at least one card
    assert len(pending) >= 1, pending

    sid = pending[0]["id"]
    stype = pending[0]["suggestion_type"]

    r = client.post(
        f"/api/projects/{pid}/suggestions/{sid}/action",
        headers=headers,
        json={"action": "apply", "mark_approved": False},
    )
    assert r.status_code == 200, r.text
    assert r.json()["action"] == "apply"
    assert r.json()["created_element_id"] is not None

    # Applied suggestion no longer pending
    r = client.get(f"/api/projects/{pid}/suggestions", headers=headers)
    ids = {s["id"] for s in r.json()}
    assert sid not in ids

    if stype == "research_question":
        r = client.get(f"/api/projects/{pid}/questions", headers=headers)
        assert len(r.json()) >= 1


def test_reject_suggestion() -> None:
    token = _token("reject_sug@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post(
        "/api/projects",
        headers=headers,
        json={"working_title": "Reject flow project"},
    )
    pid = r.json()["id"]
    client.post(
        f"/api/projects/{pid}/chat/messages",
        headers=headers,
        json={"content": "Design methodology", "special_command": "Design methodology"},
    )
    pending = client.get(f"/api/projects/{pid}/suggestions", headers=headers).json()
    if not pending:
        return
    sid = pending[0]["id"]
    r = client.post(
        f"/api/projects/{pid}/suggestions/{sid}/action",
        headers=headers,
        json={"action": "reject"},
    )
    assert r.status_code == 200
    assert r.json()["approval_status"] == "rejected"
