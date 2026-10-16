"""Multi-document synthesis dashboard tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

P1 = """
Digital Literacy in Nursing Education
Abstract
This study examined digital literacy among nursing students using a survey.
Introduction
Digital tools are essential in clinical training.
Methods
A cross-sectional design with a questionnaire was used.
Results
Students showed moderate digital literacy.
Conclusion
Training workshops are recommended.
References
Smith J. (2020). Digital nursing. Journal.
"""

P2 = """
Technology Readiness of Medical Students
Abstract
We assessed technology readiness with mixed methods.
Background
Medical schools adopt e-learning rapidly.
Methodology
Interviews and a readiness scale were applied.
Findings
Readiness varied by year of study.
Discussion
Findings differ from earlier surveys.
Conclusion
Curriculum redesign is needed.
Bibliography
Lee A. (2021). E-learning. Education Press.
"""


def _token(email: str) -> str:
    r = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Syn User",
            "password": "securepass1",
            "preferred_language": "en",
        },
    )
    if r.status_code == 400:
        r = client.post("/api/auth/login", json={"email": email, "password": "securepass1"})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_synthesis_empty() -> None:
    token = _token("syn_empty@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    pid = client.post(
        "/api/projects", headers=headers, json={"working_title": "Syn empty"}
    ).json()["id"]
    r = client.post(f"/api/projects/{pid}/synthesis/dashboard", headers=headers, json={})
    assert r.status_code == 200
    assert r.json()["status"] == "empty"
    assert r.json()["paper_count"] == 0


def test_synthesis_with_two_papers() -> None:
    token = _token("syn_two@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    pid = client.post(
        "/api/projects",
        headers=headers,
        json={"working_title": "Syn corpus", "writing_language": "en"},
    ).json()["id"]

    for name, text in [("a.txt", P1), ("b.txt", P2)]:
        r = client.post(
            f"/api/projects/{pid}/library/upload",
            headers=headers,
            files={"file": (name, text.encode("utf-8"), "text/plain")},
        )
        assert r.status_code == 200, r.text

    r = client.post(
        f"/api/projects/{pid}/synthesis/dashboard",
        headers=headers,
        json={"language": "en"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok"
    assert body["paper_count"] == 2
    assert len(body["insight_cards"]) >= 2
    assert len(body["stage_heatmap"]) == 18
    assert len(body["comparison_matrix"]) == 2
    assert body["learning_path"]
    assert body["integrity_notice"]
    assert body["theme_cloud"] is not None
