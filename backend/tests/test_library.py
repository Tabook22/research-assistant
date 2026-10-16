"""Previous Research Library processing tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _token(email: str) -> str:
    r = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Library Tester",
            "password": "securepass1",
            "preferred_language": "en",
        },
    )
    if r.status_code == 400:
        r = client.post("/api/auth/login", json={"email": email, "password": "securepass1"})
    assert r.status_code == 200
    return r.json()["access_token"]


SAMPLE_PAPER = """
Digital Literacy Among Nursing Students: A Cross-Sectional Study

Abstract
This study examined digital literacy levels among undergraduate nursing students.

Introduction
Background on digital tools in nursing education is expanding.

Statement of the Problem
Limited local evidence exists on digital literacy among nursing students.

Purpose of the Study
The purpose of this study was to assess digital literacy among undergraduate nursing students.

Literature Review
Previous studies reported mixed findings on digital skills in health professions.

Research Gap
Few studies have examined this population in the local university context.

Research Questions
What is the level of digital literacy among undergraduate nursing students?

Methodology
A cross-sectional survey design was used.

Participants and Sample
The target population was undergraduate nursing students. Convenience sampling was used.

Instruments
A structured questionnaire measured digital literacy.

Validity and Reliability
Content validity was assessed by experts. Cronbach alpha was reported.

Ethical Considerations
Informed consent was obtained. Institutional approval was reported.

Data Analysis
Descriptive statistics and t-tests were used.

Results
Participants completed the questionnaire. Mean scores are reported in tables.

Discussion
Findings are compared with previous studies.

Limitations
Self-report bias and single-site sampling limit generalizability.

Conclusion and Recommendations
Digital literacy was moderate. Training workshops are recommended.

References
Author A. (2020). Title. Journal.
"""


def test_multi_upload_and_study_summary() -> None:
    token = _token("library_multi@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    pid = client.post(
        "/api/projects",
        headers=headers,
        json={"working_title": "Study shelf project", "writing_language": "en"},
    ).json()["id"]

    files = [
        ("files", ("paper_a.txt", SAMPLE_PAPER.encode("utf-8"), "text/plain")),
        (
            "files",
            (
                "paper_b.txt",
                SAMPLE_PAPER.replace("nursing", "medical").encode("utf-8"),
                "text/plain",
            ),
        ),
    ]
    r = client.post(f"/api/projects/{pid}/library/upload-many", headers=headers, files=files)
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["uploaded"]) == 2
    assert body["failed"] == []
    first = body["uploaded"][0]
    assert first.get("study_summary") is not None
    ss = first["study_summary"]
    assert ss.get("main_ideas")
    assert ss.get("methods")
    assert ss.get("how_to_study")
    assert "study" in (ss.get("purpose") or "").lower() or "learning" in (ss.get("purpose") or "").lower()


def test_upload_and_analyze_txt_paper() -> None:
    token = _token("library1@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post(
        "/api/projects",
        headers=headers,
        json={"working_title": "My nursing literacy study", "document_type": "research_proposal"},
    )
    pid = r.json()["id"]

    files = {"file": ("sample_study.txt", SAMPLE_PAPER.encode("utf-8"), "text/plain")}
    r = client.post(f"/api/projects/{pid}/library/upload", headers=headers, files=files)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["processing_status"] in ("completed", "completed_with_warnings")
    assert body["is_reference_only"] is True
    assert body["document_type"] is not None
    assert body["document_type_confirmed"] is False
    assert len(body["stage_mappings"]) == 18
    detected = [m for m in body["stage_mappings"] if m["status"] in ("detected", "partially_detected")]
    assert len(detected) >= 5
    assert body["learning_report"] is not None
    assert "integrity_preamble" in body["learning_report"]
    assert "plagiar" in body["integrity_notice"].lower() or "copy" in body["integrity_notice"].lower()

    doc_id = body["id"]
    r = client.post(
        f"/api/projects/{pid}/library/{doc_id}/confirm-classification",
        headers=headers,
        json={"document_type": "journal_article"},
    )
    assert r.status_code == 200
    assert r.json()["document_type_confirmed"] is True
    assert r.json()["document_type"] == "journal_article"

    r = client.get(f"/api/projects/{pid}/library", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_write_section_guide_and_draft() -> None:
    token = _token("library_write@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    pid = client.post(
        "/api/projects",
        headers=headers,
        json={
            "working_title": "My original study on digital skills",
            "population_summary": "first-year students",
            "document_type": "research_proposal",
        },
    ).json()["id"]
    client.patch(
        f"/api/projects/{pid}/profile",
        headers=headers,
        json={
            "research_problem": "Limited local evidence on digital skills.",
            "research_gap": "Few studies in this campus context.",
            "overall_aim": "Describe digital skill levels among first-year students.",
        },
    )
    r = client.post(
        f"/api/projects/{pid}/library/upload",
        headers=headers,
        files={"file": ("sample_study.txt", SAMPLE_PAPER.encode("utf-8"), "text/plain")},
    )
    assert r.status_code == 200
    doc_id = r.json()["id"]

    r = client.post(
        f"/api/projects/{pid}/library/{doc_id}/write-section/guide",
        headers=headers,
        json={"stage_key": "problem_purpose"},
    )
    assert r.status_code == 200, r.text
    guide = r.json()["guide"]
    assert guide["stage_key"] == "problem_purpose"
    assert guide["questions_for_you"]
    assert guide["outline_template"]
    assert any("plagiar" in x.lower() or "copy" in x.lower() for x in guide["integrity_rules"])

    answers = {q["id"]: f"Answer for {q['id']}" for q in guide["questions_for_you"]}
    r = client.post(
        f"/api/projects/{pid}/library/{doc_id}/write-section/draft",
        headers=headers,
        json={"stage_key": "problem_purpose", "answers": answers, "save_as_learning_note": True},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["draft"]
    assert "PROVISIONAL" in body["draft"].upper() or "provisional" in body["integrity_notice"].lower()
    assert body["learning_note_id"] is not None


def test_compare_two_papers() -> None:
    token = _token("library2@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    pid = client.post(
        "/api/projects",
        headers=headers,
        json={"working_title": "Compare project"},
    ).json()["id"]

    ids = []
    for name, text in [
        ("a.txt", SAMPLE_PAPER),
        ("b.txt", SAMPLE_PAPER.replace("Cross-Sectional", "Survey").replace("nursing", "medical")),
    ]:
        r = client.post(
            f"/api/projects/{pid}/library/upload",
            headers=headers,
            files={"file": (name, text.encode("utf-8"), "text/plain")},
        )
        assert r.status_code == 200
        ids.append(r.json()["id"])

    r = client.post(
        f"/api/projects/{pid}/library/compare",
        headers=headers,
        json={"document_ids": ids, "title": "Two papers"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["items"]) >= 5
    assert body["summary"] is not None
