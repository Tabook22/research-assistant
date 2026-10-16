"""Export project summary and related content."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.decisions import ExportRecord
from app.models.project import ResearchProject
from app.models.research import (
    AnalysisPlan,
    Hypothesis,
    Instrument,
    ResearchDesign,
    ResearchObjective,
    ResearchQuestion,
    Variable,
)
from app.services.project_service import build_profile_context

settings = get_settings()


def export_project(
    db: Session,
    project: ResearchProject,
    export_type: str = "project_summary",
    fmt: str = "markdown",
) -> ExportRecord:
    if export_type == "references":
        content = _export_references(project, fmt)
    elif export_type == "manuscript":
        content = _export_manuscript(project, fmt)
    else:
        content = _export_summary(db, project, fmt)

    out_dir = Path(settings.export_dir) / str(project.id)
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = "md" if fmt == "markdown" else "json"
    path = out_dir / f"{export_type}_{project.id}.{ext}"
    path.write_text(content, encoding="utf-8")

    record = ExportRecord(
        project_id=project.id,
        export_type=export_type,
        format=fmt,
        file_path=str(path),
        content_preview=content[:2000],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    # attach full content for response via attribute
    record._full_content = content  # type: ignore[attr-defined]
    return record


def _export_summary(db: Session, project: ResearchProject, fmt: str) -> str:
    profile = build_profile_context(project)
    questions = (
        db.query(ResearchQuestion).filter(ResearchQuestion.project_id == project.id).all()
    )
    objectives = (
        db.query(ResearchObjective).filter(ResearchObjective.project_id == project.id).all()
    )
    hypotheses = db.query(Hypothesis).filter(Hypothesis.project_id == project.id).all()
    variables = db.query(Variable).filter(Variable.project_id == project.id).all()
    designs = db.query(ResearchDesign).filter(ResearchDesign.project_id == project.id).all()
    instruments = db.query(Instrument).filter(Instrument.project_id == project.id).all()
    plans = db.query(AnalysisPlan).filter(AnalysisPlan.project_id == project.id).all()

    data = {
        "profile": profile,
        "questions": [
            {
                "id": q.id,
                "text": q.text,
                "type": q.question_type,
                "status": q.approval_status,
                "analysis": q.proposed_analysis,
            }
            for q in questions
        ],
        "objectives": [
            {"id": o.id, "text": o.text, "question_id": o.question_id, "status": o.approval_status}
            for o in objectives
        ],
        "hypotheses": [
            {
                "id": h.id,
                "H0": h.null_hypothesis,
                "H1": h.alternative_hypothesis,
                "status": h.approval_status,
            }
            for h in hypotheses
        ],
        "variables": [
            {"id": v.id, "name": v.name, "role": v.role, "status": v.approval_status}
            for v in variables
        ],
        "designs": [
            {"id": d.id, "type": d.design_type, "paradigm": d.paradigm, "status": d.approval_status}
            for d in designs
        ],
        "instruments": [{"id": i.id, "name": i.name, "type": i.instrument_type} for i in instruments],
        "analysis_plans": [{"id": p.id, "title": p.title, "status": p.approval_status} for p in plans],
        "references": [
            {
                "title": r.title,
                "authors": r.authors,
                "year": r.year,
                "doi": r.doi,
                "verification": r.verification_status,
            }
            for r in project.references
        ],
    }

    if fmt == "json":
        return json.dumps(data, ensure_ascii=False, indent=2)

    lines = [
        f"# Research Project Summary: {project.working_title}",
        "",
        f"- Document type: {project.document_type}",
        f"- Field: {project.research_field or '—'}",
        f"- Stage: {project.current_stage}",
        f"- Language: {project.writing_language}",
        f"- Citation style: {project.citation_style}",
        f"- Completion: {project.completion_percent}%",
        "",
        "## Research Project Profile",
        "",
    ]
    for k, v in profile.items():
        lines.append(f"- **{k}**: {v if v else '—'}")

    lines += ["", "## Research Questions", ""]
    for q in data["questions"]:
        lines.append(f"- [{q['status']}] ({q['type']}) {q['text']}")

    lines += ["", "## Objectives", ""]
    for o in data["objectives"]:
        lines.append(f"- [{o['status']}] {o['text']}")

    lines += ["", "## Hypotheses", ""]
    if data["hypotheses"]:
        for h in data["hypotheses"]:
            lines.append(f"- H0: {h['H0']}")
            lines.append(f"  H1: {h['H1']}")
    else:
        lines.append("- None recorded (may be appropriate for descriptive/qualitative work).")

    lines += ["", "## Variables", ""]
    for v in data["variables"]:
        lines.append(f"- [{v['status']}] {v['name']} ({v['role']})")

    lines += ["", "## Design", ""]
    for d in data["designs"]:
        lines.append(f"- [{d['status']}] {d['type']} ({d['paradigm'] or '—'})")

    lines += ["", "## References", ""]
    for r in data["references"]:
        lines.append(
            f"- [{r['verification']}] {r['authors'] or '—'} ({r['year'] or 'n.d.'}). {r['title']}"
            + (f" DOI: {r['doi']}" if r["doi"] else "")
        )

    lines += [
        "",
        "---",
        "Generated by ResearchGuide AI. Researcher remains the author and final decision-maker.",
        "AI suggestions are not approved until explicitly confirmed by the researcher.",
    ]
    return "\n".join(lines)


def _export_references(project: ResearchProject, fmt: str) -> str:
    refs = project.references
    if fmt == "json":
        return json.dumps(
            [
                {
                    "title": r.title,
                    "authors": r.authors,
                    "year": r.year,
                    "journal": r.journal,
                    "doi": r.doi,
                    "verification_status": r.verification_status,
                    "citation_apa": r.citation_apa,
                }
                for r in refs
            ],
            ensure_ascii=False,
            indent=2,
        )
    lines = [f"# References — {project.working_title}", ""]
    for i, r in enumerate(refs, 1):
        label = r.citation_apa or f"{r.authors or 'Unknown'} ({r.year or 'n.d.'}). {r.title}."
        flag = "" if r.verification_status in ("verified", "metadata_retrieved", "doi_format_ok") else " [REFERENCE NOT YET VERIFIED]"
        lines.append(f"{i}. {label}{flag}")
    return "\n".join(lines)


def _export_manuscript(project: ResearchProject, fmt: str) -> str:
    sections = sorted(project.manuscript_sections, key=lambda s: s.section_key)
    if fmt == "json":
        return json.dumps(
            [
                {
                    "section_key": s.section_key,
                    "title": s.title,
                    "content": s.content,
                    "approval_status": s.approval_status,
                    "is_template": s.is_template,
                }
                for s in sections
            ],
            ensure_ascii=False,
            indent=2,
        )
    lines = [f"# {project.working_title}", ""]
    if not sections:
        lines.append("[RESEARCHER INPUT REQUIRED] No manuscript sections yet.")
        return "\n".join(lines)
    for s in sections:
        lines.append(f"## {s.title}")
        lines.append("")
        lines.append(s.content or "[RESEARCHER INPUT REQUIRED]")
        lines.append("")
    return "\n".join(lines)
