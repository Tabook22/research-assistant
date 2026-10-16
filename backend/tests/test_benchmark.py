"""Project vs library papers benchmark tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE = """
Title: Digital Skills in Higher Education
Abstract
This study examined digital skills among students.
Introduction and Problem
Universities need better digital readiness.
Methods
A cross-sectional survey was used.
Participants
Undergraduate students were sampled.
Results
Mean digital skill scores are reported.
Discussion
Findings align with prior work.
Conclusion
Training is recommended.
References
Author A. (2021). Skills. Journal.
"""


def _token(email: str) -> str:
    r = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Bench User",
            "password": "securepass1",
            "preferred_language": "en",
        },
    )
    if r.status_code == 400:
        r = client.post("/api/auth/login", json={"email": email, "password": "securepass1"})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_benchmark_without_papers() -> None:
    token = _token("bench_empty@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    pid = client.post(
        "/api/projects",
        headers=headers,
        json={"working_title": "Empty bench project"},
    ).json()["id"]
    r = client.post(f"/api/projects/{pid}/benchmark", headers=headers, json={})
    assert r.status_code == 200
    assert r.json()["status"] == "no_papers"


def test_benchmark_with_paper_and_project_gap() -> None:
    token = _token("bench_gap@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    pid = client.post(
        "/api/projects",
        headers=headers,
        json={
            "working_title": "My digital skills study",
            "document_type": "research_proposal",
            "population_summary": "students",
        },
    ).json()["id"]
    # Minimal profile only — missing methods/questions → should show gaps vs paper
    client.patch(
        f"/api/projects/{pid}/profile",
        headers=headers,
        json={"research_problem": "Digital skills gaps locally."},
    )
    r = client.post(
        f"/api/projects/{pid}/library/upload",
        headers=headers,
        files={"file": ("ref.txt", SAMPLE.encode("utf-8"), "text/plain")},
    )
    assert r.status_code == 200
    r = client.post(
        f"/api/projects/{pid}/benchmark",
        headers=headers,
        json={"language": "en"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok"
    assert len(body["papers"]) >= 1
    assert len(body["stage_benchmarks"]) == 18
    assert body["overall_score"] is not None
    assert body["integrity_notice"]
    assert any(b["verdict"] == "behind" for b in body["stage_benchmarks"]) or body["gaps"]
