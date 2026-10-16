"""Simple EN/AR message catalog for backend-generated text."""

from __future__ import annotations

from typing import Any


def normalize_lang(lang: str | None) -> str:
    if not lang:
        return "en"
    code = lang.strip().lower()
    if code.startswith("ar"):
        return "ar"
    return "en"


def t(lang: str | None, key: str, **kwargs: Any) -> str:
    code = normalize_lang(lang)
    table = AR if code == "ar" else EN
    text = table.get(key) or EN.get(key) or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text


def stage_purpose(lang: str | None, stage_key: str) -> str:
    return t(lang, f"stage_purpose.{stage_key}")


# ---------------------------------------------------------------------------
# English
# ---------------------------------------------------------------------------
EN: dict[str, str] = {
    # Chat welcome / offline
    "chat.welcome": (
        "Welcome. I will help you build your research step by step, from the initial idea "
        "to a methodologically aligned manuscript.\n\n"
        "I will not invent references, data, or results. I will explain each important research "
        "decision before drafting it.\n\n"
        "To begin, please provide:\n\n"
        "1. Your preliminary research idea or title.\n"
        "2. Your academic field.\n"
        "3. The type of document you are preparing.\n"
        "4. The proposed population and location, if known.\n"
        "5. Your current research stage.\n"
        "6. Any documents already available.\n"
        "7. Your preferred writing language.\n"
        "8. Your target university, journal, or citation style, if known.\n\n"
        "You may upload your proposal, introduction, dataset, institutional template, "
        "questionnaire, or reference papers.\n\n"
        "I will first analyze what you provide and then recommend the correct next step."
    ),
    "chat.welcome_project": (
        "\n\n(I see your project title is “{title}” in field “{field}”, "
        "document type “{doc_type}”.)"
    ),
    "chat.offline_warning": "XAI_API_KEY is not configured. Running in offline guidance mode.",
    "chat.offline_cards": "Offline mode: draft structure cards generated for your review (not auto-applied).",
    "chat.ai_failed": "AI provider call failed; offline fallback used.",
    "chat.fabricate_warn": (
        "Request appears to ask for fabricated references; AI will refuse and offer search guidance only."
    ),
    "chat.offline_body": (
        "Current stage:\n{stage}\n\n"
        "What I understood:\nYou said: “{user}”\n\n"
        "What is scientifically sound:\n"
        "Your project workspace is set up with title “{title}”. "
        "Structured fields that are filled will guide later stages.\n\n"
        "What needs clarification or correction:\n"
        "[RESEARCHER INPUT REQUIRED] — Complete profile fields (problem, gap, aim, questions) "
        "in the workspace panels. Configure XAI_API_KEY for full AI dialogue.\n\n"
        "Recommended approach:\n"
        "1. Fill the Research Project Profile with approved decisions only.\n"
        "2. Use the stage navigator to advance after each approval.\n"
        "3. Run **Check alignment** before drafting methods or instruments.\n\n"
        "Draft output:\n"
        "[PROVISIONAL—REQUIRES APPROVAL] Offline mode cannot generate full AI drafts.\n\n"
        "Evidence and references:\n"
        "I cannot independently verify live academic sources without search tools and will not invent references.\n\n"
        "Researcher decision required:\n"
        "Provide or confirm: research problem, population, document type details, and current materials.\n\n"
        "Next stage:\n"
        "After profile basics are set, move to literature search and gap formulation.\n\n{cmd}"
    ),
    "chat.profile_header": "Current stage: Profile review\n\nResearch Project Profile:\n",
    "chat.profile_footer": (
        "\nResearcher decision required:\n"
        "Confirm which fields are accurate and which need revision.\n\n"
        "Next stage:\nContinue work on stage: {stage}"
    ),
    "chat.lang_instruction": (
        "CRITICAL LANGUAGE RULE: Respond entirely in English. All explanations, drafts, "
        "questions, tables headers in prose, and guidance must be in English unless the user "
        "explicitly pastes Arabic source text that should be quoted."
    ),
    "chat.field_not_set": "not set",
    "integrity.offline_draft": "Offline draft — review wording before applying.",
    "integrity.offline_hyp": "Only use if design is comparative/correlational/experimental.",
    "integrity.offline_design": "Common feasible default for many beginner studies — confirm fit with questions.",
    "sug.aim_title": "Overall aim (draft)",
    "sug.aim_value": "To examine aspects of “{title}” among {pop} within the context of {field}.",
    "sug.aim_rationale": "Offline draft for researcher review.",
    "sug.rq_title": "Descriptive research question (draft)",
    "sug.rq_text": (
        "What is the level/status of the main phenomenon related to “{title}” among {pop}?"
    ),
    "sug.rq_analysis": "Descriptive statistics (frequencies, means/medians as appropriate)",
    "sug.obj_title": "Objective linked to descriptive question",
    "sug.obj_rationale": "Apply after creating the question; then link question_id if needed.",
    "sug.obj_text": "Describe the main phenomenon related to “{title}” among {pop}.",
    "sug.hyp_title": "Non-directional hypothesis template",
    "sug.h0": "There is no association between the independent and dependent variables in the study population.",
    "sug.h1": "There is an association between the independent and dependent variables in the study population.",
    "sug.iv": "[IV — researcher input]",
    "sug.dv": "[DV — researcher input]",
    "sug.theory": "[Add theoretical or empirical basis before directional form]",
    "sug.test": "[Select after confirming variable scales]",
    "sug.design_title": "Cross-sectional survey design (provisional)",
    "sug.design_type": "Cross-sectional survey",
    "sug.design_rationale": (
        "To examine characteristics related to “{title}” in {field} at a single time point."
    ),
    "sug.design_strengths": "Feasible, efficient for describing associations.",
    "sug.design_limits": "Does not establish causality; temporal order may be unclear.",
    "sug.design_bias": "Selection bias, non-response bias, social-desirability bias.",
    "sug.item_title": "Sample questionnaire item",
    "sug.item_text": "[Construct-related statement — researcher input]",
    "sug.analysis_title": "Analysis mapping template",
    "sug.analysis_test": "[Match to question and variable types]",
    "sug.analysis_desc": "Frequencies/percentages; means±SD or medians(IQR)",
    "sug.analysis_vars": "[List variables]",
    "sug.analysis_assumptions": "[Normality, independence, etc. as applicable]",
    "sug.analysis_dtype": "[nominal/ordinal/interval/ratio]",
    "lib.integrity_preamble": (
        "This report is for learning structure and methodology. "
        "It is not a license to plagiarize. Cite ideas, verify sources, and write originally. "
        "AI analysis is not a substitute for peer review or supervisor evaluation."
    ),
    "lib.uncertain_type": "Document type classification is uncertain. Confirm or correct the classification.",
    "lib.stages_review": "Some research stages require manual review.",
    "lib.ocr_quality": (
        "Text obtained via OCR. OCR quality may vary — verify critical excerpts."
    ),
    "lib.ocr_empty": "OCR produced little usable text. Manual review required; avoid confident conclusions.",
    "lib.ocr_needed": (
        "Little or no extractable text in PDF. OCR is recommended. "
        "Install optional packages and system Tesseract. Manual review required."
    ),
    "lib.no_text": "No text extracted.",
    "lib.not_detected_summary": "Not detected with sufficient confidence. Manual review required.",
    "lib.not_detected_lesson": (
        "Purpose of this stage: {purpose} "
        "If relevant to your study, plan how you will address it explicitly."
    ),
    "lib.strength_clear": "Clear dedicated section.",
    "lib.limit_thin": "Thin or indirect evidence in extraction.",
    "lib.na_summary": "Often not required for this document type/paradigm ({dtype}).",
    "lib.partial_keywords": (
        "Keywords suggest this stage is present but a clear section heading was not found."
    ),
    "lib.lessons": (
        "What this stage does: {purpose} "
        "How this paper approached it: status={status}. "
        "Learn the structure and reasoning; do not copy distinctive wording. "
        "Evaluate fit to YOUR questions, population, resources, and ethics."
    ),
    "lib.connection": "Check that this stage logically supports the next stage in the alignment chain.",
    "lib.writing": (
        "Observe how authors move from claims to evidence, and how they signal purpose. "
        "Write your own version from your project information with citation placeholders."
    ),
    "lib.user_q1": "How will you address “{label}” in your own project?",
    "lib.user_q2": "What evidence or decisions do you still need from a supervisor or sources?",
    "lib.template_hint": "Outline your {label} in 3–5 original bullets based on YOUR project only.",
    "lib.mistake1": "Copying distinctive wording from the reference paper",
    "lib.mistake2": "Treating this paper’s results as your results",
    "lib.mistake3": "Skipping alignment with your research questions",
    "lib.pattern_intro": "Look for movement from broad context → specific problem → gap → purpose.",
    "lib.pattern_methods": "Check past tense (completed study) vs future tense (proposal/protocol).",
    "lib.pattern_results": "Results should report; discussion should interpret and compare.",
    "lib.quality_note": "Quality notes are educational, not a formal peer-review grade.",
    "lib.issue_problem": "Problem/purpose section not clearly detected",
    "lib.issue_problem_why": "Readers need a clear problem and purpose.",
    "lib.issue_problem_lesson": "State problem, evidence, gap, and purpose explicitly in your work.",
    "lib.issue_type": "Low-confidence document type",
    "lib.issue_type_why": "Stage expectations depend on document type.",
    "lib.issue_type_lesson": "Confirm type before using this paper as a structural model.",
    "lib.map_note": "Reference-paper stage status is independent of your project stage progress.",
    "lib.compare_lesson": (
        "Compare how each paper handled “{element}”. "
        "Do not copy wording; adapt structure only if it fits your questions, population, and ethics."
    ),
    "lib.compare_integrity": (
        "Comparison is for methodological learning only. "
        "Do not insert another study’s results or text into your project as your own."
    ),
    "lib.compare_warning": "Assess suitability against YOUR research questions and context.",
    "lib.status_detected": "detected",
    "lib.status_partial": "partially detected",
    "lib.status_not_detected": "not detected",
    "lib.status_na": "not applicable",
    "lib.status_review": "needs manual review",
    "lib.compare_types": "Different document types present: {types}.",
    "lib.compare_designs": "Designs observed: {designs}.",
    "lib.compare_gap": (
        "Look for recurring variables, instruments, and limitations across papers to refine your gap."
    ),
    "lib.integrity_notice": (
        "This document is a learning reference only. Content is not your research. "
        "Do not copy distinctive wording or present another study’s results as your own."
    ),
    "lib.confirm_note": "Uncertain classifications must be confirmed by the researcher.",
    "write.purpose_fallback": "Develop this research component carefully.",
    "write.ref_not_detected": "Not clearly detected in the reference paper.",
    "write.pattern_status": "Reference paper status for this stage: {status}.",
    "write.pattern_heading": "Reference heading (if any): {heading}.",
    "write.pattern_observe": (
        "Observe how the authors ordered claims and evidence; rebuild the logic for YOUR project."
    ),
    "write.pattern_replace": "Replace all example content with your population, context, and decisions.",
    "write.cite1": "[CITATION REQUIRED: foundational source]",
    "write.cite2": "[CITATION REQUIRED: recent related study]",
    "write.cite3": "[CITATION REQUIRED: local/contextual evidence if available]",
    "write.rule1": "Write originally from YOUR project answers — no plagiarism.",
    "write.rule2": "Do not copy or closely imitate the reference paper’s distinctive wording.",
    "write.rule3": "Do not present the reference paper’s results as yours.",
    "write.rule4": "Cite ideas and verify sources before manuscript submission.",
    "write.rule5": "This draft is provisional and requires your approval.",
    "write.mistake1": "Skipping the research gap when stating the problem",
    "write.mistake2": "Using causal language with a non-causal design",
    "write.mistake3": "Objectives without matching research questions",
    "write.mistake4": "Copying instrument items without permission/license",
    "write.q.context": "What is the specific context or setting of YOUR study?",
    "write.q.population": "Who/what is your population or unit of analysis?",
    "write.q.problem": "What practical or scientific problem motivates your study?",
    "write.q.gap": "What is missing in prior research that your study addresses?",
    "write.q.aim": "What is your overall aim in one sentence?",
    "write.q.significance": "Why does answering this matter scientifically and/or practically?",
    "write.q.main_question": "What is your main research question?",
    "write.q.objectives": "List 2–4 specific objectives with strong verbs (describe, examine, compare…).",
    "write.q.design": "What research design fits your questions (and what inference does it allow)?",
    "write.q.data": "What data will you collect and from where?",
    "write.q.limits_design": "What conclusions will this design NOT support?",
    "write.q.themes": "What themes emerge from prior studies you have actually reviewed?",
    "write.q.gap_statement": "Write a cautious gap statement based only on sources you verified.",
    "write.q.inclusion": "What are inclusion and exclusion criteria?",
    "write.q.sampling": "What sampling method will you use and why?",
    "write.q.size_basis": "If you propose a sample size, what is the rationale and assumptions?",
    "write.q.findings_link": "Which of YOUR actual findings (or expected structure) will you interpret?",
    "write.q.prior_work": "Which verified prior studies will you compare against?",
    "write.q.limits": "What limitations and biases must you acknowledge?",
    "write.q.main_points": "What must YOUR {stage} section include?",
    "write.q.evidence": "What evidence or decisions do you already have?",
    "write.outline.pp1": "Open with study context (not a conclusion)",
    "write.outline.pp2": "State the problem with evidence placeholders",
    "write.outline.pp3": "Identify the gap cautiously",
    "write.outline.pp4": "State purpose/aim",
    "write.outline.pp5": "Note scientific and practical significance",
    "write.outline.qo1": "Restate the gap briefly",
    "write.outline.qo2": "List research questions (typed appropriately)",
    "write.outline.qo3": "Map each question to an objective with a strong verb",
    "write.outline.qo4": "Note feasibility and ethical constraints",
    "write.outline.m1": "Name design and paradigm",
    "write.outline.m2": "Justify fit to questions",
    "write.outline.m3": "Describe procedures at high level",
    "write.outline.m4": "State inference limits and main bias risks",
    "write.outline.default1": "Define the purpose of the {label} section",
    "write.outline.default2": "Present your project-specific content",
    "write.outline.default3": "Link to previous and next stages",
    "write.outline.default4": "Add [CITATION REQUIRED] where claims need sources",
    "write.outline.default5": "Note limitations or open decisions",
    "write.draft_need_input": (
        "[PROVISIONAL—REQUIRES APPROVAL]\n\n## {label}\n\n"
        "[RESEARCHER INPUT REQUIRED] Provide answers to the guiding questions before a full draft can be generated.\n\n"
        "Outline:\n{outline}"
    ),
    "write.draft_offline": (
        "[PROVISIONAL—REQUIRES APPROVAL]\n\n## {label}\n\n"
        "Project: {title}\n\n"
        "Based on your inputs (original wording required for submission):\n{answers}\n\n"
        "Suggested structure:\n{outline}\n\n[CITATION REQUIRED]\n\n"
        "Integrity: This text was scaffolded from your answers. Expand in your own academic voice. "
        "Do not copy the reference paper."
    ),
    "write.draft_fail": (
        "[PROVISIONAL—REQUIRES APPROVAL]\n\n## {label}\n\n"
        "AI draft unavailable ({error}). Use your answers:\n{answers}"
    ),
    "write.ai_system": (
        "You are ResearchGuide AI. Draft ORIGINAL academic text for the user's project only. "
        "Use the reference paper only as a structural lesson. "
        "Never copy distinctive phrasing from the reference. "
        "Never invent results, sample sizes, or citations. "
        "Use [CITATION REQUIRED] and [RESEARCHER INPUT REQUIRED] where needed. "
        "Mark the whole draft as provisional. "
        "Write the entire draft in {lang_name}."
    ),
    "write.lang_ar": "Arabic",
    "write.lang_en": "English",
    "detail.integrity_notice": (
        "This document is a learning reference only. Content is not your research. "
        "Do not copy distinctive wording or present another study’s results as your own."
    ),
    # Stage purposes
    "stage_purpose.idea": "Focus the research interest into a feasible topic.",
    "stage_purpose.literature_search": "Locate relevant prior evidence systematically.",
    "stage_purpose.literature_synthesis": "Organize what is known and identify a defensible gap.",
    "stage_purpose.problem_purpose": "State the problem, purpose, and why the study matters.",
    "stage_purpose.questions_objectives": "Formulate answerable questions and aligned objectives.",
    "stage_purpose.hypotheses": "State testable predictions when the design warrants them.",
    "stage_purpose.constructs_variables": "Define constructs and how they will be measured.",
    "stage_purpose.methodology": "Choose a design that matches the questions and limits of inference.",
    "stage_purpose.population_sampling": "Define who/what is studied and how the sample is obtained.",
    "stage_purpose.instruments": "Specify tools that map to variables and objectives.",
    "stage_purpose.validity_quality": "Address credibility, reliability, or trustworthiness.",
    "stage_purpose.ethics": "Protect participants and report ethical procedures.",
    "stage_purpose.analysis_plan": "Pre-specify how each question will be answered.",
    "stage_purpose.results": "Report findings without premature interpretation.",
    "stage_purpose.discussion": "Interpret findings against prior work and limitations.",
    "stage_purpose.conclusion": "Answer the purpose and offer evidence-based recommendations.",
    "stage_purpose.abstract_title": "Summarize the study for discovery and indexing.",
    "stage_purpose.references": "Document sources accurately and consistently.",
    "align.missing_problem": "No research problem statement is recorded in the project profile.",
    "align.missing_problem_fix": "Define a clear research problem grounded in evidence before finalizing questions.",
    "align.missing_gap": "No research gap is documented.",
    "align.missing_gap_fix": "Synthesize literature and state a defensible gap (not an unsupported novelty claim).",
    "align.missing_aim": "Overall aim is missing.",
    "align.missing_aim_fix": "Write one overall aim that addresses the research problem and gap.",
    "align.q_no_obj": "Research question has no linked objective: “{text}”",
    "align.q_no_obj_fix": "Create a corresponding objective with a strong verb (describe, examine, compare, etc.).",
    "align.q_no_analysis": "Research question has no proposed analysis method: “{text}”",
    "align.q_no_analysis_fix": "Map this question to a planned analysis method before data collection.",
    "align.opt_draft_problem": "Draft a problem statement from known evidence",
    "align.opt_upload_problem": "Upload a proposal and extract the problem",
    "align.opt_refine_idea": "Refine the idea stage first",
    "translate.need_ai": (
        "XAI_API_KEY is not configured. Template labels can switch to Arabic, "
        "but paper excerpts and free-text analysis need AI translation."
    ),
    "translate.ok": "Translated free-text analysis fields to Arabic with AI.",
    "translate.ok_free": (
        "Translated free-text analysis fields to Arabic (free translator). "
        "Review carefully — quality may vary."
    ),
    "translate.partial": "Some fields translated. Review Arabic carefully.",
    "translate.none": "Already in Arabic, or nothing left to translate.",
    "translate.already_ar": "This text is already mostly Arabic — no translation needed.",
    "translate.failed_service": (
        "Translation service failed. Check internet connection and try again. "
        "Optional: set XAI_API_KEY for more reliable translation."
    ),
    # Study mode (learn from papers — not user's project)
    "study.purpose": (
        "Study summary for learning only. This is a reference paper, not your research project."
    ),
    "study.not_found": "Not clearly found — open the Structure Map or Source viewer for details.",
    "study.not_found_results": (
        "Results section not clearly found (common in proposals/protocols, or weak extraction)."
    ),
    "study.style_first_person": "Often uses first person or “this study” framing.",
    "study.style_passive": "Uses impersonal/passive academic voice in places.",
    "study.style_future": "Uses future/proposal language (planned work).",
    "study.style_past": "Uses past tense for completed research reporting.",
    "study.style_qual": "Qualitative-oriented wording and methods signals.",
    "study.style_quant": "Quantitative-oriented wording and methods signals.",
    "study.style_default": "Standard academic prose; check sections for local conventions.",
    "study.structure_count": "About {n} of {total} research-stage areas were detected or partially detected.",
    "study.structure_has_problem": "Includes a problem/purpose-style opening.",
    "study.structure_has_methods": "Includes a methods/methodology block.",
    "study.structure_has_results": "Includes results/findings reporting.",
    "study.structure_has_refs": "Includes a references/bibliography section.",
    "study.how1": "Read the main ideas first (abstract / introduction).",
    "study.how2": "Note how methods are justified against the questions.",
    "study.how3": "Separate what the paper reports (results) from how it interprets (discussion).",
    "study.how4": "Use the Structure Map to see how sections connect.",
    "study.how5": "Learn patterns; do not copy distinctive wording into your own work.",
    "study.integrity": (
        "Learning reference only. Do not present this paper’s text or results as your own."
    ),
    # Benchmark assistant
    "bench.no_papers": "Upload study papers in the Library first, then run the benchmark.",
    "bench.integrity": (
        "Benchmarking compares YOUR project structure to reference papers for learning. "
        "Do not copy their wording or claim their results as yours."
    ),
    "bench.rec_upload": "Upload one or more related scientific papers in Library, then run Benchmark again.",
    "bench.message_ok": "Compared your project against {n} uploaded reference paper(s).",
    "bench.gap_missing_stage": "Most reference papers address “{stage}”, but your project still lacks it.",
    "bench.strength_user_has": "You already have content for “{stage}” even if some references do not emphasize it.",
    "bench.strength_aligned": "Your project and the reference set both address “{stage}”.",
    "bench.verdict.behind": "Needs work vs references",
    "bench.verdict.aligned": "Aligned with references",
    "bench.verdict.ahead_or_unique": "Present in your project (less common in refs)",
    "bench.verdict.optional": "Often not required for these papers",
    "bench.verdict.review": "Review",
    "bench.rec_fill_stage": "Add or clarify “{stage}” in your project (profile/structure), then re-check alignment.",
    "bench.rec_complete_stage": "Complete the partial “{stage}” section so it matches your questions.",
    "bench.rec_refine_stage": "Refine “{stage}” using lessons from the Structure Map of your best reference paper.",
    "bench.rec_justify_stage": "Keep “{stage}” but justify why it fits your design if references omit it.",
    "bench.rec_optional_stage": "“{stage}” may be optional for your document type; confirm with your supervisor.",
    "bench.design_user_missing": "Reference designs include: {designs}. Define your methodology/design in Structure.",
    "bench.design_compare": "Your design(s): {user}. Reference design(s): {papers}. Check fit to your questions.",
    "bench.paradigm_refs": "Reference paradigms observed: {paradigms}.",
    "bench.score_explain": (
        "Score estimates how many research stages you have started relative to stages commonly "
        "present in your uploaded papers (not a journal quality grade)."
    ),
    "bench.rec_good": "Your coverage looks reasonable against these papers; refine weak stages and run alignment check.",
    "bench.rec_integrity": "Use references for structure and methods ideas only — write originally and cite sources.",
    # Synthesis dashboard
    "syn.empty_headline": "Your synthesis dashboard is ready",
    "syn.empty_msg": "Upload 2+ research papers in Library to auto-build a cross-paper learning dashboard.",
    "syn.integrity": (
        "This dashboard synthesizes uploaded papers for study only. "
        "Do not copy text or claim their findings as your own research."
    ),
    "syn.headline": "Synthesis of {n} research source(s)",
    "syn.message": "Automated insights across your uploaded papers — patterns, methods, gaps, and how to learn from them.",
    "syn.path_upload": "Upload scientific papers in the Library (you can select many at once).",
    "syn.no_themes": "Add more papers to detect shared themes",
    "syn.method_design": "Design “{name}” appears in {n}/{total} papers.",
    "syn.method_paradigm": "Paradigm “{name}” appears in {n}/{total} papers.",
    "syn.heat_lesson": "“{stage}” shows up in about {pct}% of your uploaded sources — study how they write it.",
    "syn.gap_under_title": "Under-documented: {stage}",
    "syn.gap_under_body": "Only ~{pct}% of these papers clearly cover “{stage}”. That may signal a writing gap—or a real research gap in this set.",
    "syn.gap_design_title": "Methodological diversity in your set",
    "syn.gap_design_body": "These papers use different designs ({designs}). Compare why each design fits its questions.",
    "syn.gap_context_title": "Check context & transferability",
    "syn.gap_context_body": "Ask: which settings/populations are missing? That often becomes your contribution space.",
    "syn.move_problem": "Problem / purpose framing",
    "syn.move_problem_tip": "Strong papers move from context → problem → purpose without answering the question early.",
    "syn.move_gap": "Gap / literature synthesis",
    "syn.move_gap_tip": "Look for thematic synthesis, not paper-by-paper lists.",
    "syn.move_methods": "Methods justification",
    "syn.move_methods_tip": "Note how authors link design to questions and admit inference limits.",
    "syn.move_results": "Results vs discussion split",
    "syn.move_results_tip": "Results report; discussion interprets. Keep them separate in your own writing.",
    "syn.card_corpus_title": "Your reading corpus",
    "syn.card_corpus_body": "You are synthesizing {n} uploaded source(s). Start with insight cards, then open the matrix.",
    "syn.card_theme_title": "Recurring themes",
    "syn.card_theme_body": "Words that recur across titles/abstracts: {terms}. Use them to map the conversation in this literature.",
    "syn.card_method_title": "Dominant method signal",
    "syn.card_structure_title": "Common structure strengths",
    "syn.card_structure_body": "These stages are well covered across sources: {stages}.",
    "syn.card_learn_title": "Study smarter",
    "syn.card_learn_body": "Pick one paper, open Study view, then compare writing moves—not just findings.",
    "syn.card_ai_title": "AI insight",
    "syn.path1": "Skim the insight cards for a 2-minute overview.",
    "syn.path2": "Open the comparison matrix: ideas → methods → findings side by side.",
    "syn.path3": "Deep-dive the strongest shared stage: “{stage}”.",
    "syn.path4": "Explore a gap signal: {gap}.",
    "syn.path5": "Use Benchmark to compare YOUR project against these sources.",
    "syn.path6": "Write notes in your own words; never paste distinctive sentences.",
}

# ---------------------------------------------------------------------------
# Arabic
# ---------------------------------------------------------------------------
AR: dict[str, str] = {
    "chat.welcome": (
        "مرحباً. سأساعدك في بناء بحثك خطوة بخطوة، من الفكرة الأولى "
        "إلى مخطوطة متسقة منهجياً.\n\n"
        "لن أخترع مراجع أو بيانات أو نتائج. سأشرح كل قرار بحثي مهم قبل صياغة المسودة.\n\n"
        "للبدء، يرجى تزويدي بما يلي:\n\n"
        "1. فكرة البحث المبدئية أو العنوان.\n"
        "2. تخصصك أو مجالك الأكاديمي.\n"
        "3. نوع الوثيقة التي تعدّها.\n"
        "4. المجتمع أو وحدة التحليل والموقع إن وُجد.\n"
        "5. مرحلتك البحثية الحالية.\n"
        "6. أي وثائق متوفرة لديك.\n"
        "7. لغة الكتابة المفضلة.\n"
        "8. الجامعة أو المجلة أو دليل التوثيق المستهدف إن وُجد.\n\n"
        "يمكنك رفع مقترحك أو المقدمة أو مجموعة البيانات أو القالب المؤسسي أو الاستبيان أو الأوراق المرجعية.\n\n"
        "سأحلّل أولاً ما تقدّمه ثم أقترح الخطوة الصحيحة التالية."
    ),
    "chat.welcome_project": (
        "\n\n(أرى أن عنوان مشروعك «{title}» في مجال «{field}»، "
        "ونوع الوثيقة «{doc_type}».)"
    ),
    "chat.offline_warning": "مفتاح XAI_API_KEY غير مُعدّ. يعمل النظام في وضع الإرشاد دون اتصال بالذكاء الاصطناعي الكامل.",
    "chat.offline_cards": "وضع دون اتصال: تم إنشاء بطاقات بنية مسودة لمراجعتك (دون تطبيق تلقائي).",
    "chat.ai_failed": "فشل الاتصال بمزوّد الذكاء الاصطناعي؛ تم استخدام الوضع الاحتياطي دون اتصال.",
    "chat.fabricate_warn": (
        "يبدو أن الطلب يطلب مراجع مختلقة؛ سيرفض المساعد ذلك ويقدّم إرشاداً للبحث فقط."
    ),
    "chat.offline_body": (
        "المرحلة الحالية:\n{stage}\n\n"
        "ما فهمته:\nقلتَ: «{user}»\n\n"
        "ما هو سليم علمياً:\n"
        "مساحة مشروعك جاهزة بالعنوان «{title}». "
        "الحقول المنظمة المعبأة ستوجّه المراحل اللاحقة.\n\n"
        "ما يحتاج توضيحاً أو تصحيحاً:\n"
        "[يلزم إدخال الباحث] — أكمل حقول الملف (المشكلة، الفجوة، الهدف، الأسئلة) "
        "من لوحات مساحة العمل. فعّل XAI_API_KEY للحوار الكامل مع الذكاء الاصطناعي.\n\n"
        "النهج الموصى به:\n"
        "1. املأ ملف المشروع البحثي بالقرارات المعتمدة فقط.\n"
        "2. استخدم متصفح المراحل للتقدّم بعد كل اعتماد.\n"
        "3. شغّل **فحص الاتساق** قبل صياغة المنهجية أو الأدوات.\n\n"
        "مسودة المخرجات:\n"
        "[مؤقت—يتطلب الموافقة] الوضع دون اتصال لا يولّد مسودات ذكاء اصطناعي كاملة.\n\n"
        "الأدلة والمراجع:\n"
        "لا يمكنني التحقق بشكل مستقل من مصادر أكاديمية حية دون أدوات بحث، ولن أخترع مراجع.\n\n"
        "قرار مطلوب من الباحث:\n"
        "قدّم أو أكّد: مشكلة البحث، المجتمع، تفاصيل نوع الوثيقة، والمواد المتوفرة.\n\n"
        "المرحلة التالية:\n"
        "بعد تثبيت أساسيات الملف، انتقل إلى البحث في الأدبيات وصياغة الفجوة.\n\n{cmd}"
    ),
    "chat.profile_header": "المرحلة الحالية: مراجعة الملف\n\nملف المشروع البحثي:\n",
    "chat.profile_footer": (
        "\nقرار مطلوب من الباحث:\n"
        "أكّد الحقول الدقيقة والتي تحتاج مراجعة.\n\n"
        "المرحلة التالية:\nتابع العمل في المرحلة: {stage}"
    ),
    "chat.lang_instruction": (
        "قاعدة لغة إلزامية: أجب بالكامل باللغة العربية الفصحى الواضحة المناسبة للباحثين. "
        "كل الشروحات والمسودات والأسئلة والإرشادات يجب أن تكون بالعربية، "
        "ما لم يقتبس المستخدم نصاً إنجليزياً يجب الإبقاء عليه بين علامتي اقتباس."
    ),
    "chat.field_not_set": "غير محدد",
    "integrity.offline_draft": "مسودة دون اتصال — راجع الصياغة قبل التطبيق.",
    "integrity.offline_hyp": "استخدمها فقط إذا كان التصميم مقارناً/ارتباطياً/تجريبياً.",
    "integrity.offline_design": "خيار شائع وممكن لكثير من دراسات المبتدئين — تأكد من ملاءمته للأسئلة.",
    "sug.aim_title": "الهدف العام (مسودة)",
    "sug.aim_value": "فحص جوانب «{title}» لدى {pop} ضمن سياق {field}.",
    "sug.aim_rationale": "مسودة دون اتصال لمراجعة الباحث.",
    "sug.rq_title": "سؤال بحث وصفي (مسودة)",
    "sug.rq_text": "ما مستوى/حالة الظاهرة الرئيسية المرتبطة بـ «{title}» لدى {pop}؟",
    "sug.rq_analysis": "إحصاء وصفي (تكرارات، متوسطات/وسيط حسب المناسب)",
    "sug.obj_title": "هدف مرتبط بالسؤال الوصفي",
    "sug.obj_rationale": "طبّق بعد إنشاء السؤال؛ ثم اربط question_id عند الحاجة.",
    "sug.obj_text": "وصف الظاهرة الرئيسية المرتبطة بـ «{title}» لدى {pop}.",
    "sug.hyp_title": "قالب فرضية غير اتجاهية",
    "sug.h0": "لا توجد علاقة بين المتغير المستقل والمتغير التابع في مجتمع الدراسة.",
    "sug.h1": "توجد علاقة بين المتغير المستقل والمتغير التابع في مجتمع الدراسة.",
    "sug.iv": "[المتغير المستقل — إدخال الباحث]",
    "sug.dv": "[المتغير التابع — إدخال الباحث]",
    "sug.theory": "[أضف أساساً نظرياً أو تجريبياً قبل الصيغة الاتجاهية]",
    "sug.test": "[يُختار بعد تأكيد مستويات قياس المتغيرات]",
    "sug.design_title": "تصميم مسح مقطعي (مؤقت)",
    "sug.design_type": "مسح مقطعي",
    "sug.design_rationale": "لفحص خصائص مرتبطة بـ «{title}» في {field} في نقطة زمنية واحدة.",
    "sug.design_strengths": "عملي وفعّال لوصف الارتباطات.",
    "sug.design_limits": "لا يثبت السببية؛ قد يكون الترتيب الزمني غير واضح.",
    "sug.design_bias": "تحيز الاختيار، عدم الاستجابة، والرغبة الاجتماعية.",
    "sug.item_title": "بند استبيان نموذجي",
    "sug.item_text": "[عبارة مرتبطة بالمفهوم — إدخال الباحث]",
    "sug.analysis_title": "قالب ربط تحليلي",
    "sug.analysis_test": "[يُطابق نوع السؤال والمتغيرات]",
    "sug.analysis_desc": "تكرارات/نسب؛ متوسط±انحراف أو وسيط(مدى ربيعي)",
    "sug.analysis_vars": "[قائمة المتغيرات]",
    "sug.analysis_assumptions": "[الاعتدالية، الاستقلال، إلخ حسب الحالة]",
    "sug.analysis_dtype": "[اسمي/رتبي/فئوي/نسبي]",
    "lib.integrity_preamble": (
        "هذا التقرير للتعلّم من البنية والمنهجية. "
        "وليس ترخيصاً للانتحال. وثّق الأفكار وتحقق من المصادر واكتب بأسلوبك. "
        "تحليل الذكاء الاصطناعي لا يغني عن التحكيم العلمي أو إشراف المشرف."
    ),
    "lib.uncertain_type": "تصنيف نوع الوثيقة غير مؤكد. أكّد التصنيف أو صحّحه.",
    "lib.stages_review": "بعض مراحل البحث تحتاج مراجعة يدوية.",
    "lib.ocr_quality": "تم الحصول على النص عبر OCR. قد تتفاوت الجودة — تحقّق من المقتطفات المهمة.",
    "lib.ocr_empty": "أنتج OCR نصاً قليلاً. يلزم مراجعة يدوية؛ تجنّب استنتاجات واثقة.",
    "lib.ocr_needed": (
        "نص قابل للاستخراج قليل أو معدوم في ملف PDF. يُنصح بـ OCR. "
        "ثبّت الحزم الاختيارية وTesseract. يلزم مراجعة يدوية."
    ),
    "lib.no_text": "لم يُستخرج أي نص.",
    "lib.not_detected_summary": "لم يُكتشف بثقة كافية. يلزم مراجعة يدوية.",
    "lib.not_detected_lesson": (
        "غرض هذه المرحلة: {purpose} "
        "إن كانت ذات صلة بدراستك، خطّط لكيفية معالجتها بوضوح."
    ),
    "lib.strength_clear": "قسم واضح ومخصص.",
    "lib.limit_thin": "دليل ضعيف أو غير مباشر في الاستخراج.",
    "lib.na_summary": "غالباً غير مطلوب لهذا النوع/النموذج ({dtype}).",
    "lib.partial_keywords": (
        "تشير كلمات مفتاحية إلى وجود المرحلة لكن لم يُعثر على عنوان قسم واضح."
    ),
    "lib.lessons": (
        "ما تفعله هذه المرحلة: {purpose} "
        "كيف عالجتها الورقة: الحالة={status}. "
        "تعلّم البنية والاستدلال؛ لا تنسخ الصياغة المميزة. "
        "قيّم الملاءمة لأسئلتك ومجتمعك ومواردك وأخلاقياتك."
    ),
    "lib.connection": "تحقّق من أن هذه المرحلة تدعم منطقياً المرحلة التالية في سلسلة الاتساق.",
    "lib.writing": (
        "لاحظ كيف ينتقل المؤلفون من الادعاء إلى الدليل وكيف يعلنون الغرض. "
        "اكتب نسختك من معلومات مشروعك مع مواضع للتوثيق."
    ),
    "lib.user_q1": "كيف ستعالج «{label}» في مشروعك؟",
    "lib.user_q2": "ما الأدلة أو القرارات التي ما زلت تحتاجها من المشرف أو المصادر؟",
    "lib.template_hint": "ضع مخططاً لـ {label} في 3–5 نقاط أصلية من مشروعك فقط.",
    "lib.mistake1": "نسخ الصياغة المميزة من الورقة المرجعية",
    "lib.mistake2": "تقديم نتائج هذه الورقة وكأنها نتائجك",
    "lib.mistake3": "تجاهل الاتساق مع أسئلة بحثك",
    "lib.pattern_intro": "لاحظ الانتقال من السياق العام → المشكلة المحددة → الفجوة → الغرض.",
    "lib.pattern_methods": "تحقّق من صيغة الماضي (بحث مكتمل) مقابل المستقبل (مقترح/بروتوكول).",
    "lib.pattern_results": "النتائج تعرض؛ المناقشة تفسّر وتقارن.",
    "lib.quality_note": "ملاحظات الجودة تعليمية وليست درجة تحكيم رسمية.",
    "lib.issue_problem": "قسم المشكلة/الغرض غير واضح",
    "lib.issue_problem_why": "يحتاج القارئ إلى مشكلة وغرض واضحين.",
    "lib.issue_problem_lesson": "اذكر المشكلة والدليل والفجوة والغرض صراحة في عملك.",
    "lib.issue_type": "ثقة منخفضة في نوع الوثيقة",
    "lib.issue_type_why": "توقعات المراحل تعتمد على نوع الوثيقة.",
    "lib.issue_type_lesson": "أكّد النوع قبل اتخاذ الورقة نموذجاً بنيوياً.",
    "lib.map_note": "حالة مراحل الورقة المرجعية مستقلة عن تقدّم مشروعك.",
    "lib.compare_lesson": (
        "قارن كيف عالجت كل ورقة «{element}». "
        "لا تنسخ الصياغة؛ كيّف البنية فقط إن ناسبت أسئلتك ومجتمعك وأخلاقياتك."
    ),
    "lib.compare_integrity": (
        "المقارنة للتعلّم المنهجي فقط. "
        "لا تدرج نتائج أو نص دراسة أخرى في مشروعك وكأنها لك."
    ),
    "lib.compare_warning": "قيّم الملاءمة لأسئلة بحثك وسياقك.",
    "lib.status_detected": "مُكتشف",
    "lib.status_partial": "مُكتشف جزئياً",
    "lib.status_not_detected": "غير مُكتشف",
    "lib.status_na": "غير منطبق",
    "lib.status_review": "يحتاج مراجعة يدوية",
    "lib.compare_types": "أنواع وثائق مختلفة: {types}.",
    "lib.compare_designs": "التصاميم المرصودة: {designs}.",
    "lib.compare_gap": (
        "ابحث عن متغيرات وأدوات وقيود متكررة عبر الأوراق لصقل فجوتك."
    ),
    "lib.integrity_notice": (
        "هذه الوثيقة مرجع تعلّم فقط. المحتوى ليس بحثك. "
        "لا تنسخ الصياغة المميزة ولا تقدّم نتائج دراسة أخرى كأنها نتائجك."
    ),
    "lib.confirm_note": "التصنيفات غير المؤكدة يجب أن يؤكّدها الباحث.",
    "write.purpose_fallback": "طوّر هذا المكوّن البحثي بعناية.",
    "write.ref_not_detected": "لم يُكتشف بوضوح في الورقة المرجعية.",
    "write.pattern_status": "حالة الورقة المرجعية لهذه المرحلة: {status}.",
    "write.pattern_heading": "عنوان القسم المرجعي (إن وُجد): {heading}.",
    "write.pattern_observe": (
        "لاحظ ترتيب الادعاءات والأدلة لدى المؤلفين؛ أعد بناء المنطق لمشروعك."
    ),
    "write.pattern_replace": "استبدل كل المحتوى النموذجي بمجتمعك وسياقك وقراراتك.",
    "write.cite1": "[يلزم توثيق: مصدر تأسيسي]",
    "write.cite2": "[يلزم توثيق: دراسة حديثة ذات صلة]",
    "write.cite3": "[يلزم توثيق: دليل محلي/سياقي إن وُجد]",
    "write.rule1": "اكتب أصالةً من إجابات مشروعك — بلا انتحال.",
    "write.rule2": "لا تنسخ أو تقلّد الصياغة المميزة للورقة المرجعية.",
    "write.rule3": "لا تقدّم نتائج الورقة المرجعية كأنها نتائجك.",
    "write.rule4": "وثّق الأفكار وتحقق من المصادر قبل التسليم.",
    "write.rule5": "هذه المسودة مؤقتة وتتطلب موافقتك.",
    "write.mistake1": "تجاوز فجوة البحث عند صياغة المشكلة",
    "write.mistake2": "لغة سببية مع تصميم لا يدعم السببية",
    "write.mistake3": "أهداف بلا أسئلة بحث مطابقة",
    "write.mistake4": "نسخ بنود أداة دون إذن/ترخيص",
    "write.q.context": "ما السياق أو المكان المحدد لدراستك؟",
    "write.q.population": "من/ما مجتمع الدراسة أو وحدة التحليل؟",
    "write.q.problem": "ما المشكلة العملية أو العلمية التي تحفّز دراستك؟",
    "write.q.gap": "ما الذي ينقص في البحوث السابقة وتعالجه دراستك؟",
    "write.q.aim": "ما هدفك العام في جملة واحدة؟",
    "write.q.significance": "لماذا يهمّ الإجابة علمياً و/أو عملياً؟",
    "write.q.main_question": "ما سؤال بحثك الرئيسي؟",
    "write.q.objectives": "اذكر 2–4 أهداف محددة بأفعال قوية (وصف، فحص، مقارنة…).",
    "write.q.design": "ما التصميم البحثي المناسب لأسئلتك (وما الاستنتاجات التي يسمح بها)؟",
    "write.q.data": "ما البيانات التي ستجمعها ومن أين؟",
    "write.q.limits_design": "ما الاستنتاجات التي لا يدعمها هذا التصميم؟",
    "write.q.themes": "ما الموضوعات التي تظهر من الدراسات التي راجعتها فعلياً؟",
    "write.q.gap_statement": "اكتب بيان فجوة حذراً مبنياً فقط على مصادر تحققت منها.",
    "write.q.inclusion": "ما معايير التضمين والاستبعاد؟",
    "write.q.sampling": "ما طريقة المعاينة ولماذا؟",
    "write.q.size_basis": "إن اقترحت حجم عينة، ما المبرر والافتراضات؟",
    "write.q.findings_link": "أي من نتائجك الفعلية (أو هيكلها المتوقع) ستفسّرها؟",
    "write.q.prior_work": "أي دراسات سابقة موثّقة ستقارن بها؟",
    "write.q.limits": "ما القيود والتحيزات التي يجب الاعتراف بها؟",
    "write.q.main_points": "ما الذي يجب أن يتضمنه قسم {stage} في بحثك؟",
    "write.q.evidence": "ما الأدلة أو القرارات المتوفرة لديك؟",
    "write.outline.pp1": "ابدأ بسياق الدراسة (وليس بنتيجة)",
    "write.outline.pp2": "صغ المشكلة مع مواضع للأدلة",
    "write.outline.pp3": "حدّد الفجوة بحذر",
    "write.outline.pp4": "اذكر الغرض/الهدف",
    "write.outline.pp5": "أشر إلى الأهمية العلمية والعملية",
    "write.outline.qo1": "أعد ذكر الفجوة باختصار",
    "write.outline.qo2": "اسرد أسئلة البحث (بأنواع مناسبة)",
    "write.outline.qo3": "اربط كل سؤال بهدف بفعل قوي",
    "write.outline.qo4": "لاحظ القيود العملية والأخلاقية",
    "write.outline.m1": "سمِّ التصميم والنموذج",
    "write.outline.m2": "برّر ملاءمته للأسئلة",
    "write.outline.m3": "صف الإجراءات بإيجاز",
    "write.outline.m4": "اذكر حدود الاستدلال ومخاطر التحيز الرئيسية",
    "write.outline.default1": "حدّد غرض قسم {label}",
    "write.outline.default2": "قدّم محتوى خاصاً بمشروعك",
    "write.outline.default3": "اربط بالمرحلة السابقة والتالية",
    "write.outline.default4": "أضف [يلزم توثيق] حيث تحتاج الادعاءات مصادر",
    "write.outline.default5": "أشر إلى القيود أو القرارات المفتوحة",
    "write.draft_need_input": (
        "[مؤقت—يتطلب الموافقة]\n\n## {label}\n\n"
        "[يلزم إدخال الباحث] أجب عن الأسئلة الإرشادية قبل توليد مسودة كاملة.\n\n"
        "الهيكل:\n{outline}"
    ),
    "write.draft_offline": (
        "[مؤقت—يتطلب الموافقة]\n\n## {label}\n\n"
        "المشروع: {title}\n\n"
        "بناءً على إجاباتك (يلزم صياغة أصلية عند التسليم):\n{answers}\n\n"
        "هيكل مقترح:\n{outline}\n\n[يلزم توثيق]\n\n"
        "نزاهة: نُسجت هذه المسودة من إجاباتك. وسّعها بأسلوبك الأكاديمي. "
        "لا تنسخ الورقة المرجعية."
    ),
    "write.draft_fail": (
        "[مؤقت—يتطلب الموافقة]\n\n## {label}\n\n"
        "مسودة الذكاء الاصطناعي غير متاحة ({error}). استخدم إجاباتك:\n{answers}"
    ),
    "write.ai_system": (
        "أنت ResearchGuide AI. اكتب نصاً أكاديمياً أصيلاً لمشروع المستخدم فقط. "
        "استخدم الورقة المرجعية كدرس بنيوي فقط. "
        "لا تنسخ عبارات مميزة من المرجع. "
        "لا تخترع نتائج أو أحجام عينات أو استشهادات. "
        "استخدم [يلزم توثيق] و[يلزم إدخال الباحث] عند الحاجة. "
        "علّم المسودة كاملة بأنها مؤقتة. "
        "اكتب المسودة بالكامل باللغة: {lang_name}."
    ),
    "write.lang_ar": "العربية",
    "write.lang_en": "الإنجليزية",
    "detail.integrity_notice": (
        "هذه الوثيقة مرجع تعلّم فقط. المحتوى ليس بحثك. "
        "لا تنسخ الصياغة المميزة ولا تقدّم نتائج دراسة أخرى كأنها نتائجك."
    ),
    "stage_purpose.idea": "تحويل الاهتمام البحثي إلى موضوع قابل للتنفيذ.",
    "stage_purpose.literature_search": "تحديد الأدلة السابقة ذات الصلة بشكل منهجي.",
    "stage_purpose.literature_synthesis": "تنظيم ما هو معروف وتحديد فجوة قابلة للدفاع.",
    "stage_purpose.problem_purpose": "صياغة المشكلة والغرض وأهمية الدراسة.",
    "stage_purpose.questions_objectives": "صياغة أسئلة قابلة للإجابة وأهداف متسقة معها.",
    "stage_purpose.hypotheses": "صياغة تنبؤات قابلة للاختبار عندما يناسب التصميم ذلك.",
    "stage_purpose.constructs_variables": "تعريف المفاهيم وكيفية قياسها.",
    "stage_purpose.methodology": "اختيار تصميم يطابق الأسئلة وحدود الاستدلال.",
    "stage_purpose.population_sampling": "تحديد من/ما يُدرس وكيف تُؤخذ العينة.",
    "stage_purpose.instruments": "تحديد أدوات ترتبط بالمتغيرات والأهداف.",
    "stage_purpose.validity_quality": "معالجة الصدق والثبات أو الموثوقية.",
    "stage_purpose.ethics": "حماية المشاركين والإبلاغ عن الإجراءات الأخلاقية.",
    "stage_purpose.analysis_plan": "تحديد مسبق لكيفية الإجابة عن كل سؤال.",
    "stage_purpose.results": "عرض النتائج دون تفسير مبكر.",
    "stage_purpose.discussion": "تفسير النتائج مقابل الدراسات السابقة والقيود.",
    "stage_purpose.conclusion": "الإجابة عن الغرض وتقديم توصيات مبنية على الأدلة.",
    "stage_purpose.abstract_title": "تلخيص الدراسة للاكتشاف والفهرسة.",
    "stage_purpose.references": "توثيق المصادر بدقة واتساق.",
    "align.missing_problem": "لا يوجد بيان لمشكلة البحث في ملف المشروع.",
    "align.missing_problem_fix": "عرّف مشكلة بحث واضحة مبنية على أدلة قبل تثبيت الأسئلة.",
    "align.missing_gap": "لم تُوثَّق فجوة البحث.",
    "align.missing_gap_fix": "ركّب الأدبيات واذكر فجوة قابلة للدفاع (وليس ادعاء جدة بلا سند).",
    "align.missing_aim": "الهدف العام مفقود.",
    "align.missing_aim_fix": "اكتب هدفاً عاماً واحداً يعالج المشكلة والفجوة.",
    "align.q_no_obj": "سؤال البحث بلا هدف مرتبط: «{text}»",
    "align.q_no_obj_fix": "أنشئ هدفاً مقابلاً بفعل قوي (وصف، فحص، مقارنة، إلخ).",
    "align.q_no_analysis": "سؤال البحث بلا طريقة تحليل مقترحة: «{text}»",
    "align.q_no_analysis_fix": "اربط هذا السؤال بطريقة تحليل مخططة قبل جمع البيانات.",
    "align.opt_draft_problem": "صغ بيان المشكلة من الأدلة المعروفة",
    "align.opt_upload_problem": "ارفع مقترحاً واستخرج المشكلة",
    "align.opt_refine_idea": "حسّن مرحلة الفكرة أولاً",
    "translate.need_ai": (
        "مفتاح XAI_API_KEY غير مضبوط. يمكن تعريب القوالب والواجهات، "
        "لكن مقتطفات الورقة والنصوص الحرة تحتاج ترجمة بالذكاء الاصطناعي."
    ),
    "translate.ok": "تُرجمت حقول التحليل النصية إلى العربية بالذكاء الاصطناعي.",
    "translate.ok_free": (
        "تُرجمت حقول التحليل النصية إلى العربية (مترجم مجاني). "
        "راجع النص بعناية — قد تختلف الجودة."
    ),
    "translate.partial": "تُرجمت بعض الحقول. راجع العربية بعناية.",
    "translate.none": "المحتوى بالعربية مسبقاً، أو لا يوجد نص للترجمة.",
    "translate.already_ar": "هذا النص بالعربية غالباً — لا حاجة للترجمة.",
    "translate.failed_service": (
        "فشلت خدمة الترجمة. تحقق من الاتصال بالإنترنت وأعد المحاولة. "
        "اختياري: اضبط XAI_API_KEY لترجمة أكثر موثوقية."
    ),
    "study.purpose": (
        "ملخص دراسي للتعلّم فقط. هذه ورقة مرجعية وليست مشروعك البحثي."
    ),
    "study.not_found": "غير واضح — افتح خريطة البنية أو عارض المصدر للتفاصيل.",
    "study.not_found_results": (
        "قسم النتائج غير واضح (شائع في المقترحات/البروتوكولات، أو ضعف الاستخراج)."
    ),
    "study.style_first_person": "يستخدم غالباً صيغة المتكلم أو إطار «هذه الدراسة».",
    "study.style_passive": "يستخدم صيغة مبنية للمجهول/أكاديمية غير شخصية في مواضع.",
    "study.style_future": "يستخدم لغة المستقبل/المقترح (عمل مخطط).",
    "study.style_past": "يستخدم صيغة الماضي لعرض بحث مكتمل.",
    "study.style_qual": "إشارات صياغة ومنهج نوعي.",
    "study.style_quant": "إشارات صياغة ومنهج كمي.",
    "study.style_default": "نثر أكاديمي معتاد؛ راجع الأقسام لأعراف التخصص.",
    "study.structure_count": "تم رصد حوالي {n} من {total} مجالات مراحل البحث (كلياً أو جزئياً).",
    "study.structure_has_problem": "يتضمن افتتاحاً بأسلوب المشكلة/الغرض.",
    "study.structure_has_methods": "يتضمن كتلة طرق/منهجية.",
    "study.structure_has_results": "يتضمن عرض نتائج/مكتشفات.",
    "study.structure_has_refs": "يتضمن قسم مراجع/قائمة مصادر.",
    "study.how1": "اقرأ الأفكار الرئيسية أولاً (الملخص / المقدمة).",
    "study.how2": "لاحظ كيف تُبرَّر المنهجية مقابل الأسئلة.",
    "study.how3": "افصل ما تعرضه الورقة (النتائج) عما تفسّره (المناقشة).",
    "study.how4": "استخدم خريطة البنية لرؤية ترابط الأقسام.",
    "study.how5": "تعلّم الأنماط؛ لا تنسخ الصياغة المميزة إلى عملك.",
    "study.integrity": (
        "مرجع تعلّم فقط. لا تقدّم نص هذه الورقة أو نتائجها كأنها لك."
    ),
    "bench.no_papers": "ارفع أولاً أوراقاً دراسية في المكتبة، ثم شغّل المقارنة المعيارية.",
    "bench.integrity": (
        "المقارنة المعيارية تقيس بنية مشروعك مقابل الأوراق المرجعية للتعلّم. "
        "لا تنسخ صياغتها ولا تدّعِ نتائجها."
    ),
    "bench.rec_upload": "ارفع ورقة علمية واحدة أو أكثر في المكتبة، ثم أعد تشغيل المقارنة.",
    "bench.message_ok": "تمت مقارنة مشروعك مع {n} ورقة/أوراق مرجعية مرفوعة.",
    "bench.gap_missing_stage": "معظم الأوراق المرجعية تعالج «{stage}»، بينما مشروعك ما زال يفتقدها.",
    "bench.strength_user_has": "لديك محتوى لـ «{stage}» حتى لو لم تُبرِزها بعض المراجع.",
    "bench.strength_aligned": "مشروعك ومجموعة المراجع يعالجان «{stage}».",
    "bench.verdict.behind": "يحتاج عملاً مقابل المراجع",
    "bench.verdict.aligned": "متسق مع المراجع",
    "bench.verdict.ahead_or_unique": "موجود في مشروعك (أقل شيوعاً في المراجع)",
    "bench.verdict.optional": "غالباً غير مطلوب لهذه الأوراق",
    "bench.verdict.review": "للمراجعة",
    "bench.rec_fill_stage": "أضف أو وضّح «{stage}» في مشروعك (الملف/البنية)، ثم أعد فحص الاتساق.",
    "bench.rec_complete_stage": "أكمل الجزء الناقص من «{stage}» ليتوافق مع أسئلتك.",
    "bench.rec_refine_stage": "حسّن «{stage}» باستخدام دروس خريطة البنية لأفضل ورقة مرجعية.",
    "bench.rec_justify_stage": "أبقِ «{stage}» مع تبرير ملاءمتها لتصميمك إن أغفلتها المراجع.",
    "bench.rec_optional_stage": "قد تكون «{stage}» اختيارية لنوع وثيقتك؛ أكّد مع مشرفك.",
    "bench.design_user_missing": "تصاميم المراجع تشمل: {designs}. عرّف منهجيتك/تصميمك في البنية.",
    "bench.design_compare": "تصميمك: {user}. تصاميم المراجع: {papers}. تحقّق من الملاءمة لأسئلتك.",
    "bench.paradigm_refs": "نماذج المراجع المرصودة: {paradigms}.",
    "bench.score_explain": (
        "الدرجة تقدّر كم مرحلة بحثية بدأتها مقارنة بالمراحل الشائعة في أوراقك المرفوعة "
        "(وليست درجة جودة لمجلة)."
    ),
    "bench.rec_good": "تغطيتك معقولة مقابل هذه الأوراق؛ حسّن المراحل الضعيفة وشغّل فحص الاتساق.",
    "bench.rec_integrity": "استخدم المراجع لبنية الأفكار والمنهج فقط — اكتب بأسلوبك ووثّق المصادر.",
    "syn.empty_headline": "لوحة التوليف جاهزة",
    "syn.empty_msg": "ارفع ورقتين علميتين أو أكثر في المكتبة لبناء لوحة تعلّم تلقائية عبر المصادر.",
    "syn.integrity": (
        "هذه اللوحة تولّف الأوراق المرفوعة للدراسة فقط. "
        "لا تنسخ النص ولا تقدّم نتائجها كأنها نتائجك."
    ),
    "syn.headline": "توليف {n} مصدر/مصادر بحثية",
    "syn.message": "رؤى تلقائية عبر أوراقك: أنماط، مناهج، فجوات، وكيف تتعلّم منها.",
    "syn.path_upload": "ارفع أوراقاً علمية في المكتبة (يمكنك اختيار عدة ملفات معاً).",
    "syn.no_themes": "أضف المزيد من الأوراق لاكتشاف موضوعات مشتركة",
    "syn.method_design": "يظهر التصميم «{name}» في {n}/{total} ورقة.",
    "syn.method_paradigm": "يظهر النموذج «{name}» في {n}/{total} ورقة.",
    "syn.heat_lesson": "تظهر «{stage}» في حوالي {pct}% من مصادرك — ادرس كيف يكتبونها.",
    "syn.gap_under_title": "موثّق بشكل ضعيف: {stage}",
    "syn.gap_under_body": "حوالي {pct}% فقط من هذه الأوراق تغطي «{stage}» بوضوح. قد تكون فجوة كتابة—أو فجوة بحثية في هذه المجموعة.",
    "syn.gap_design_title": "تنوّع منهجي في مجموعتك",
    "syn.gap_design_body": "هذه الأوراق تستخدم تصاميم مختلفة ({designs}). قارن لماذا يناسب كل تصميم أسئلته.",
    "syn.gap_context_title": "افحص السياق وقابلية النقل",
    "syn.gap_context_body": "اسأل: أي سياقات/مجتمعات ناقصة؟ غالباً هنا مساحة إسهامك.",
    "syn.move_problem": "تأطير المشكلة / الغرض",
    "syn.move_problem_tip": "الأوراق القوية تنتقل من السياق → المشكلة → الغرض دون الإجابة مبكراً.",
    "syn.move_gap": "الفجوة / تركيب الأدبيات",
    "syn.move_gap_tip": "ابحث عن تركيب موضوعي لا سرد ورقة بورقة.",
    "syn.move_methods": "تبرير المنهج",
    "syn.move_methods_tip": "لاحظ ربط التصميم بالأسئلة والاعتراف بحدود الاستدلال.",
    "syn.move_results": "فصل النتائج عن المناقشة",
    "syn.move_results_tip": "النتائج تعرض؛ المناقشة تفسّر. افصل بينهما في كتابتك.",
    "syn.card_corpus_title": "مجموعة قراءتك",
    "syn.card_corpus_body": "أنت تولّف {n} مصدر/مصادر. ابدأ ببطاقات الرؤى ثم افتح المصفوفة.",
    "syn.card_theme_title": "موضوعات متكررة",
    "syn.card_theme_body": "كلمات تتكرر في العناوين/الملخصات: {terms}. استخدمها لرسم خريطة الحوار في الأدبيات.",
    "syn.card_method_title": "إشارة المنهج السائدة",
    "syn.card_structure_title": "نقاط قوة بنيوية مشتركة",
    "syn.card_structure_body": "هذه المراحل مغطاة جيداً عبر المصادر: {stages}.",
    "syn.card_learn_title": "ادرس بذكاء",
    "syn.card_learn_body": "اختر ورقة، افتح العرض الدراسي، ثم قارن حركات الكتابة—لا النتائج فقط.",
    "syn.card_ai_title": "رؤية بالذكاء",
    "syn.path1": "تصفّح بطاقات الرؤى لنظرة خلال دقيقتين.",
    "syn.path2": "افتح مصفوفة المقارنة: أفكار → مناهج → نتائج جنباً إلى جنب.",
    "syn.path3": "تعمّق في أقوى مرحلة مشتركة: «{stage}».",
    "syn.path4": "استكشف إشارة فجوة: {gap}.",
    "syn.path5": "استخدم المقارنة المعيارية لوضع مشروعك مقابل هذه المصادر.",
    "syn.path6": "اكتب ملاحظاتك بكلماتك؛ لا تلصق جملاً مميزة.",
}
