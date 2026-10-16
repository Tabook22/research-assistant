"""Internal consistency / alignment checker."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.i18n.lang import normalize_lang, t
from app.models.manuscript import AlignmentIssue
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


def _add_issue(
    issues: list[dict[str, Any]],
    issue_type: str,
    severity: str,
    explanation: str,
    affected: list[str],
    recommended: str,
    options: list[str] | None = None,
) -> None:
    issues.append(
        {
            "issue_type": issue_type,
            "severity": severity,
            "explanation": explanation,
            "affected_elements": json.dumps(affected),
            "recommended_correction": recommended,
            "correction_options": json.dumps(options or []),
        }
    )


def run_alignment_check(
    db: Session, project: ResearchProject, language: str | None = None
) -> list[AlignmentIssue]:
    """Clear previous open issues and recompute alignment for the project."""
    lang = normalize_lang(language or project.writing_language or "en")
    db.query(AlignmentIssue).filter(
        AlignmentIssue.project_id == project.id,
        AlignmentIssue.resolution_status == "open",
    ).delete()

    raw: list[dict[str, Any]] = []
    profile = project.profile
    questions = db.query(ResearchQuestion).filter(ResearchQuestion.project_id == project.id).all()
    objectives = (
        db.query(ResearchObjective).filter(ResearchObjective.project_id == project.id).all()
    )
    hypotheses = db.query(Hypothesis).filter(Hypothesis.project_id == project.id).all()
    variables = db.query(Variable).filter(Variable.project_id == project.id).all()
    designs = db.query(ResearchDesign).filter(ResearchDesign.project_id == project.id).all()
    instruments = db.query(Instrument).filter(Instrument.project_id == project.id).all()
    plans = db.query(AnalysisPlan).filter(AnalysisPlan.project_id == project.id).all()

    # Problem / gap / aim
    if not profile or not profile.research_problem:
        _add_issue(
            raw,
            "missing_problem",
            "major",
            t(lang, "align.missing_problem"),
            ["profile.research_problem"],
            t(lang, "align.missing_problem_fix"),
            [
                t(lang, "align.opt_draft_problem"),
                t(lang, "align.opt_upload_problem"),
                t(lang, "align.opt_refine_idea"),
            ],
        )
    if not profile or not profile.research_gap:
        _add_issue(
            raw,
            "missing_gap",
            "warning",
            t(lang, "align.missing_gap"),
            ["profile.research_gap"],
            t(lang, "align.missing_gap_fix"),
        )
    if not profile or not profile.overall_aim:
        _add_issue(
            raw,
            "missing_aim",
            "major",
            t(lang, "align.missing_aim"),
            ["profile.overall_aim"],
            t(lang, "align.missing_aim_fix"),
        )

    # Questions without objectives
    obj_by_q = {o.question_id for o in objectives if o.question_id}
    for q in questions:
        if q.id not in obj_by_q:
            _add_issue(
                raw,
                "question_without_objective",
                "major",
                t(lang, "align.q_no_obj", text=q.text[:120]),
                [f"question:{q.id}"],
                t(lang, "align.q_no_obj_fix"),
            )
        if not q.proposed_analysis:
            _add_issue(
                raw,
                "question_without_analysis",
                "warning",
                t(lang, "align.q_no_analysis", text=q.text[:120]),
                [f"question:{q.id}"],
                t(lang, "align.q_no_analysis_fix"),
            )

    # Objectives without questions
    for o in objectives:
        if not o.question_id:
            _add_issue(
                raw,
                "objective_without_question",
                "warning",
                f"Objective is not linked to a research question: “{o.text[:120]}”",
                [f"objective:{o.id}"],
                "Link the objective to a research question or add a matching question.",
            )

    # Hypotheses without measurable variables / question
    for h in hypotheses:
        if not h.question_id:
            _add_issue(
                raw,
                "hypothesis_without_question",
                "major",
                f"Hypothesis is not linked to a research question: H1 “{h.alternative_hypothesis[:80]}”",
                [f"hypothesis:{h.id}"],
                "Connect each hypothesis to an appropriate research question.",
            )
        if not h.independent_variable or not h.dependent_variable:
            _add_issue(
                raw,
                "hypothesis_without_variables",
                "major",
                "Hypothesis lacks clearly specified independent and/or dependent variables.",
                [f"hypothesis:{h.id}"],
                "Specify measurable IV and DV with operational definitions.",
            )
        if h.direction == "directional" and not h.theoretical_basis:
            _add_issue(
                raw,
                "directional_hypothesis_without_basis",
                "warning",
                "Directional hypothesis lacks documented theoretical or empirical basis.",
                [f"hypothesis:{h.id}"],
                "Add theoretical/empirical basis or use a non-directional form.",
            )

    # Variables without operational definitions
    for v in variables:
        if not v.operational_definitions:
            _add_issue(
                raw,
                "variable_without_operational_definition",
                "major",
                f"Variable “{v.name}” has no operational definition.",
                [f"variable:{v.id}"],
                "Define how the variable will be measured (instrument, coding, scale).",
            )

    # Causal language risk: causal question + non-experimental design
    causal_types = {"experimental_or_causal", "explanatory", "predictive"}
    non_causal_designs = {
        "cross-sectional",
        "survey",
        "correlational",
        "case study",
        "phenomenology",
        "ethnography",
    }
    primary_design = next((d for d in designs if d.is_primary), designs[0] if designs else None)
    if primary_design:
        design_lower = (primary_design.design_type or "").lower()
        for q in questions:
            if q.question_type in causal_types and any(nd in design_lower for nd in non_causal_designs):
                _add_issue(
                    raw,
                    "causal_question_noncausal_design",
                    "critical",
                    (
                        f"Question type “{q.question_type}” may imply stronger inference than design "
                        f"“{primary_design.design_type}” permits."
                    ),
                    [f"question:{q.id}", f"design:{primary_design.id}"],
                    "Align question wording with design (association vs causation) or change design.",
                    [
                        "Reword as associational/comparative question",
                        "Upgrade to experimental/quasi-experimental design if feasible",
                        "Keep design and limit claims in discussion/conclusions",
                    ],
                )

    # Instrument items unlinked
    for inst in instruments:
        for section in inst.sections:
            for item in section.items:
                if not item.construct_name and not item.variable_name and not item.linked_objective:
                    _add_issue(
                        raw,
                        "instrument_item_unlinked",
                        "warning",
                        f"Instrument item is not linked to a construct, variable, or objective: “{item.item_text[:80]}”",
                        [f"instrument_item:{item.id}", f"instrument:{inst.id}"],
                        "Map every item to a construct/variable and research objective.",
                    )

    # Analysis plan coverage
    mapped_q_ids: set[int] = set()
    for plan in plans:
        for m in plan.mappings:
            if m.question_id:
                mapped_q_ids.add(m.question_id)
    if questions and not plans:
        _add_issue(
            raw,
            "missing_analysis_plan",
            "major",
            "Research questions exist but no analysis plan is defined.",
            ["analysis_plan"],
            "Create an analysis plan mapping each question/hypothesis to a method.",
        )
    for q in questions:
        if plans and q.id not in mapped_q_ids and not q.proposed_analysis:
            _add_issue(
                raw,
                "question_unmapped_in_analysis",
                "warning",
                f"Question not covered in analysis plan mappings: “{q.text[:100]}”",
                [f"question:{q.id}"],
                "Add an analysis mapping for this question.",
            )

    # Document type vs results
    proposal_types = {
        "research_proposal",
        "research_protocol",
    }
    for section in project.manuscript_sections:
        if project.document_type in proposal_types and section.section_key == "results":
            content = (section.content or "").lower()
            if content and not section.is_template:
                if any(
                    w in content
                    for w in ("p =", "p<", "significant", "participants (n", "mean =")
                ):
                    _add_issue(
                        raw,
                        "results_in_proposal",
                        "critical",
                        "Proposal/protocol appears to present completed results language.",
                        [f"manuscript_section:{section.id}"],
                        "Remove actual results; use future tense and empty table shells only.",
                    )

    # Orphan references checks are light here
    unverified = [r for r in project.references if r.verification_status == "unverified"]
    if len(unverified) >= 5:
        _add_issue(
            raw,
            "many_unverified_references",
            "information",
            f"{len(unverified)} references are still unverified.",
            ["references"],
            "Verify DOIs/metadata before including claims in the manuscript.",
        )

    saved: list[AlignmentIssue] = []
    for item in raw:
        issue = AlignmentIssue(
            project_id=project.id,
            issue_type=item["issue_type"],
            severity=item["severity"],
            explanation=item["explanation"],
            affected_elements=item["affected_elements"],
            recommended_correction=item["recommended_correction"],
            correction_options=item["correction_options"],
            resolution_status="open",
        )
        db.add(issue)
        saved.append(issue)
    db.commit()
    for s in saved:
        db.refresh(s)
    return saved


def chain_status(project: ResearchProject, db: Session) -> dict[str, str]:
    profile = project.profile
    q_count = db.query(ResearchQuestion).filter(ResearchQuestion.project_id == project.id).count()
    o_count = db.query(ResearchObjective).filter(ResearchObjective.project_id == project.id).count()
    h_count = db.query(Hypothesis).filter(Hypothesis.project_id == project.id).count()
    v_count = db.query(Variable).filter(Variable.project_id == project.id).count()
    d_count = db.query(ResearchDesign).filter(ResearchDesign.project_id == project.id).count()
    i_count = db.query(Instrument).filter(Instrument.project_id == project.id).count()
    a_count = db.query(AnalysisPlan).filter(AnalysisPlan.project_id == project.id).count()

    def status(present: bool, partial: bool = False) -> str:
        if present:
            return "present"
        if partial:
            return "partial"
        return "missing"

    return {
        "research_problem": status(bool(profile and profile.research_problem)),
        "research_gap": status(bool(profile and profile.research_gap)),
        "overall_aim": status(bool(profile and profile.overall_aim)),
        "objectives": status(o_count > 0),
        "research_questions": status(q_count > 0),
        "hypotheses": status(h_count > 0) if h_count else "optional/missing",
        "variables": status(v_count > 0),
        "research_design": status(d_count > 0),
        "instruments": status(i_count > 0),
        "analysis_plan": status(a_count > 0),
        "population": status(bool(project.population_summary or project.populations)),
    }
