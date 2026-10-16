/**
 * Stage explainers for the Research Stages board.
 * Structure follows the DU workshop guide pattern:
 * inputs → processing → outputs → feed next stage + why it matters.
 * Content is adapted for the app's 18-stage research chain (EN + AR).
 */

export type StageGuide = {
  what: string;
  how: string;
  inputs: string;
  processing: string;
  outputs: string;
  nextStageKey: string | null;
  nextNote: string;
  why: string;
};

export type StageGuideMap = Record<string, StageGuide>;

const en: StageGuideMap = {
  idea: {
    what: "Clarify a focused, feasible research interest before writing a full problem statement.",
    how: "Turn a broad topic into a measurable interest with a clear population, setting, and phenomenon.",
    inputs:
      "Preliminary idea or observation, field knowledge, institutional context, and constraints (time, access, ethics).",
    processing:
      "Narrow the topic, define who/what is studied, separate what is known from what is unknown, and reject vague “good vs bad” questions.",
    outputs:
      "A refined research idea with population, context, and a provisional measurable focus (no invented results).",
    nextStageKey: "literature_search",
    nextNote:
      "Keywords and scope from this stage drive the literature search strategy.",
    why: "A weak idea produces unfocused questions, tools, and findings. Strong research starts with a scoped, answerable interest.",
  },
  literature_search: {
    what: "Systematically locate relevant prior studies and credible sources.",
    how: "Search trusted databases with Arabic/English keywords, remove duplicates, screen titles/abstracts, and keep source trails (DOI, volume, pages).",
    inputs:
      "Research idea, keywords, topic boundaries (field, population, concepts), and inclusion/exclusion hints.",
    processing:
      "Query databases, de-duplicate, screen for relevance, open originals, and log bibliographic details for verification.",
    outputs:
      "A curated set of candidate sources with verified references (not AI-invented citations).",
    nextStageKey: "literature_synthesis",
    nextNote:
      "Selected studies become the material for synthesis and gap formulation.",
    why: "Without a rigorous search, the gap is guesswork and novelty claims cannot be defended.",
  },
  literature_synthesis: {
    what: "Organize what is known and state a defensible research gap.",
    how: "Extract methods, samples, tools, findings, and limits from closest studies; build a matrix and conceptual framing.",
    inputs:
      "Screened literature, research questions themes, and definitions of key concepts.",
    processing:
      "Compare studies thematically (not paper-by-paper lists), map agreements/conflicts, and identify what is still unknown for your setting.",
    outputs:
      "Literature matrix, operational definitions draft, conceptual frame, and a clear gap statement.",
    nextStageKey: "problem_purpose",
    nextNote:
      "The gap and evidence base feed the problem, purpose, and significance statements.",
    why: "Synthesis prevents reinventing known work and justifies why your study is needed.",
  },
  problem_purpose: {
    what: "State the research problem, study purpose, and why the study matters.",
    how: "Convert the gap into a precise problem (no assumed results), then write purpose and scientific/practical significance.",
    inputs:
      "Gap statement, population/setting, and evidence that a problem exists.",
    processing:
      "Specify who is affected, what is missing (e.g. local quantitative estimates), what will be measured, and why it matters—without inventing percentages or outcomes.",
    outputs:
      "Approved problem statement, purpose/aim, and significance (scientific + practical).",
    nextStageKey: "questions_objectives",
    nextNote:
      "Problem and purpose become the direct inputs to measurable questions and objectives.",
    why: "If the problem is vague or already “answers” itself, every later stage becomes misaligned.",
  },
  questions_objectives: {
    what: "Write answerable research questions and matching objectives.",
    how: "Split the problem into questions with variables/indicators and analysis intent; pair each question with a strong-verb objective.",
    inputs:
      "Problem/purpose, target population, and core variables identified so far.",
    processing:
      "Map each problem part to a question (prevalence, differences, relationships, effect), then write objectives (describe, examine, compare…).",
    outputs:
      "Aligned set of RQs and objectives that define what data and analyses are required.",
    nextStageKey: "hypotheses",
    nextNote:
      "Where theory allows testing, questions feed directional or non-directional hypotheses.",
    why: "Questions drive design, tools, sample size, and analysis. Unclear questions produce unusable data.",
  },
  hypotheses: {
    what: "State testable predictions when the design and theory support them.",
    how: "Write H0/H1 (or directional forms) linked to variables and planned tests; skip forced hypotheses for purely descriptive aims.",
    inputs:
      "Research questions, variable definitions, and theoretical/empirical basis.",
    processing:
      "Decide which questions are inferential, specify expected relationships, and align wording with measurement scales and design limits.",
    outputs:
      "Hypotheses (or explicit N/A with reason) ready for the analysis plan.",
    nextStageKey: "constructs_variables",
    nextNote:
      "Hypotheses require clear construct and variable definitions to be measurable.",
    why: "Hypotheses make predictions falsifiable and prevent post-hoc story-fitting after results appear.",
  },
  constructs_variables: {
    what: "Define constructs and operational variables (what is measured and how).",
    how: "Turn concepts into indicators, scales, and roles (IV/DV/mediator/control).",
    inputs:
      "Questions/hypotheses, literature definitions, and measurement options from prior studies.",
    processing:
      "Write conceptual + operational definitions, list items/indicators, and assign variable roles and levels of measurement.",
    outputs:
      "Variable dictionary: names, roles, scales, and operational definitions.",
    nextStageKey: "methodology",
    nextNote:
      "Variables determine which designs and data sources can answer each question.",
    why: "Without operational definitions, instruments and analysis cannot be validly linked to the questions.",
  },
  methodology: {
    what: "Choose a research design that matches questions and inference limits.",
    how: "Select paradigm/design (e.g. survey, experiment, mixed methods) and justify fit, sequence, and limits of causal claims.",
    inputs:
      "Questions, hypotheses, variables, gap, and practical constraints (access, time).",
    processing:
      "Match each question to a data source and design component; define multi-phase order if mixed methods; document bias risks.",
    outputs:
      "Design protocol linking every question → data source → variable → analysis type, with timeline.",
    nextStageKey: "population_sampling",
    nextNote:
      "Design sets who must be sampled and how recruitment will work.",
    why: "Design is the bridge from questions to defensible evidence; wrong design invalidates conclusions.",
  },
  population_sampling: {
    what: "Define the population, inclusion/exclusion criteria, and sampling plan.",
    how: "Specify N when known, sampling method (e.g. stratified), size rationale, and recruitment path.",
    inputs:
      "Design protocol, target groups, and available population frames.",
    processing:
      "Set inclusion/exclusion, estimate sample size (with assumptions), allocate strata/quotas, and plan non-response handling.",
    outputs:
      "Sampling plan: criteria, size basis, strata/quotas, and recruitment procedures.",
    nextStageKey: "instruments",
    nextNote:
      "Sample plan informs instrument administration logistics and pilot needs.",
    why: "Representativeness and ethical access depend on a transparent sampling plan.",
  },
  instruments: {
    what: "Build data-collection tools mapped to variables and objectives.",
    how: "Draft items/tasks/rubrics, adapt published scales carefully, and align wording with operational definitions.",
    inputs:
      "Variable dictionary, RQs, literature measures, and design requirements (survey, task, interview guide).",
    processing:
      "Write clear non-leading items; create comparable versions if multiple groups; design tasks/rubrics; prepare coding instructions.",
    outputs:
      "Draft instruments (questionnaires, tasks, rubrics, guides) ready for validity work.",
    nextStageKey: "validity_quality",
    nextNote:
      "Draft tools move to expert review, cognitive interviews, and pilot testing.",
    why: "Data quality is only as good as the instrument; poor items cannot be fixed after main collection.",
  },
  validity_quality: {
    what: "Establish validity, reliability/trustworthiness before main data collection.",
    how: "Expert review, cognitive testing, pilot study, reliability indices, and item revision.",
    inputs:
      "Draft instruments, pilot sample access, and scoring rules.",
    processing:
      "Content validity, clarity checks, pilot administration, reliability (e.g. alpha/ICC), and revise/remove ambiguous items.",
    outputs:
      "Validated instruments, pilot evidence, reliability notes, and final administration versions.",
    nextStageKey: "ethics",
    nextNote:
      "Final tools are attached to ethics applications and consent materials.",
    why: "Without validity/reliability work, results may measure noise rather than the intended constructs.",
  },
  ethics: {
    what: "Protect participants and secure required ethical approvals and data protection.",
    how: "Consent, privacy, risk mitigation, data storage rules, and institutional approval before collection.",
    inputs:
      "Final protocol, instruments, population risks, and institutional requirements.",
    processing:
      "Prepare consent/assent, anonymization plan, access controls, and obtain ethics approval; forbid grade/power coercion.",
    outputs:
      "Approved ethics package, consent texts, and data-protection procedures.",
    nextStageKey: "analysis_plan",
    nextNote:
      "With ethical clearance and tools ready, pre-specify the analysis plan before (or locked before looking at) main data.",
    why: "Ethics is a scientific and legal prerequisite; late ethics risks invalidation of the entire study.",
  },
  analysis_plan: {
    what: "Pre-specify how each research question will be answered.",
    how: "Map RQ → variables → descriptive/inferential procedures, missing-data rules, effect sizes, and software.",
    inputs:
      "RQs/hypotheses, variable dictionary, design, and sampling weights if any.",
    processing:
      "Choose tests/models appropriate to scales and design (paired vs independent), define exclusion flags, and plan tables/figures.",
    outputs:
      "Analysis plan document that can be executed reproducibly after cleaning.",
    nextStageKey: "results",
    nextNote:
      "Clean data are analyzed according to this plan to produce results tables.",
    why: "Pre-specification reduces p-hacking and makes results auditable.",
  },
  results: {
    what: "Report findings without over-interpretation.",
    how: "Present estimates with uncertainty (CIs), effect sizes, and transparent sample flow; separate description from discussion.",
    inputs:
      "Clean dataset, analysis plan, and verified outputs from statistical/qualitative software.",
    processing:
      "Run planned analyses, produce tables/figures from approved results only, report n, CIs, and reliability of raters if relevant.",
    outputs:
      "Results section: tables, figures, and numerical/textual findings aligned to RQs.",
    nextStageKey: "discussion",
    nextNote:
      "Findings feed interpretation, literature comparison, and limitations.",
    why: "Clear results let readers verify claims; mixing interpretation here confuses evidence with opinion.",
  },
  discussion: {
    what: "Interpret findings against literature, theory, and limitations.",
    how: "Explain patterns, agreements/disagreements with prior work, alternative explanations, and design limits (no over-claiming causality).",
    inputs:
      "Results, literature synthesis, design strengths/limits, and qualitative themes if any.",
    processing:
      "Integrate multi-source evidence carefully; distinguish statistical from practical significance; state biases.",
    outputs:
      "Discussion narrative: interpretation, comparison, and limitations.",
    nextStageKey: "conclusion",
    nextNote:
      "Interpretation supports cautious conclusions and recommendations.",
    why: "Discussion converts numbers into scientific meaning without inventing certainty the design cannot support.",
  },
  conclusion: {
    what: "Answer the purpose and offer evidence-based recommendations.",
    how: "Summarize key answers to RQs, implications for practice/policy, and future research—conditioned on sample and design.",
    inputs:
      "Discussion, results, and institutional/practical context.",
    processing:
      "Write conclusions that match evidence strength; list actionable recommendations and remaining questions.",
    outputs:
      "Conclusions, recommendations, and future research agenda.",
    nextStageKey: "abstract_title",
    nextNote:
      "Core findings and purpose feed the abstract, title, and keywords.",
    why: "Conclusions close the research loop and guide decision-makers without overgeneralizing.",
  },
  abstract_title: {
    what: "Summarize the study for discovery: title, abstract, keywords.",
    how: "Write a precise title and structured abstract (purpose, methods, key findings, implications) with searchable keywords.",
    inputs:
      "Final purpose, methods outline, main results, and conclusions.",
    processing:
      "Compress accurately; avoid claims not in results; align keywords with literature terms.",
    outputs:
      "Title, abstract, and keywords ready for submission/indexing.",
    nextStageKey: "references",
    nextNote:
      "Abstract sources must match the verified reference list.",
    why: "Most readers decide from title/abstract; accuracy here protects integrity and discoverability.",
  },
  references: {
    what: "Document all sources accurately and consistently.",
    how: "Verify every citation against the original, complete metadata (DOI, pages), and apply the chosen citation style.",
    inputs:
      "All cited works from literature, methods, and discussion.",
    processing:
      "Cross-check in-text citations vs list, open sources, fix metadata, and reject fabricated AI references.",
    outputs:
      "Complete, consistent reference list and citation integrity check.",
    nextStageKey: null,
    nextNote:
      "References close the manuscript chain; unresolved gaps may restart a new research cycle.",
    why: "Citation integrity is non-negotiable for academic credibility and reproducibility.",
  },
};

const ar: StageGuideMap = {
  idea: {
    what: "توضيح اهتمام بحثي مركّز وقابل للتنفيذ قبل كتابة بيان المشكلة الكامل.",
    how: "تحويل موضوع عام إلى اهتمام قابل للقياس مع مجتمع وسياق وظاهرة واضحة.",
    inputs:
      "فكرة أولية أو ملاحظة، معرفة المجال، سياق المؤسسة، والقيود (الوقت، الوصول، الأخلاقيات).",
    processing:
      "تضييق الموضوع، تحديد من/ما يُدرس، فصل المعروف عن المجهول، وتجنب الأسئلة الفضفاضة من نوع «هل الذكاء الاصطناعي جيد أم سيئ؟».",
    outputs:
      "فكرة بحث محسّنة تحدد المجتمع والسياق والتركيز القابل للقياس (دون اختراع نتائج).",
    nextStageKey: "literature_search",
    nextNote:
      "الكلمات المفتاحية ونطاق الفكرة يغذيان استراتيجية البحث في الأدبيات.",
    why: "الفكرة الضعيفة تولّد أسئلة وأدوات ونتائج غير متسقة. قوة البحث تبدأ من نطاق واضح قابل للإجابة.",
  },
  literature_search: {
    what: "البحث المنهجي عن الدراسات السابقة والمصادر الموثوقة.",
    how: "البحث في قواعد علمية بكلمات عربية/إنجليزية، إزالة التكرار، فحص العناوين والملخصات، وتوثيق مسار المصدر (DOI، المجلد، الصفحات).",
    inputs:
      "فكرة البحث، الكلمات المفتاحية، حدود الموضوع (التخصص، المجتمع، المفاهيم)، وإشارات الإدراج/الاستبعاد.",
    processing:
      "تنفيذ الاستعلامات، إزالة المكرر، الفرز حسب الصلة، فتح الأصل، وتسجيل البيانات الببليوغرافية للتحقق.",
    outputs:
      "مجموعة مصادر مرشّحة مع مراجع موثّقة (وليس استشهادات مختلقة بالذكاء الاصطناعي).",
    nextStageKey: "literature_synthesis",
    nextNote:
      "الدراسات المختارة تصبح مادة التركيب وصياغة الفجوة.",
    why: "بدون بحث صارم تصبح الفجوة تخمينًا ولا يمكن الدفاع عن ادّعاء الجدة.",
  },
  literature_synthesis: {
    what: "تنظيم ما هو معروف وصياغة فجوة بحثية قابلة للدفاع.",
    how: "استخراج المناهج والعينات والأدوات والنتائج والقيود من أقرب الدراسات، وبناء مصفوفة وإطار مفاهيمي.",
    inputs:
      "الأدبيات المفروزة، محاور الأسئلة، وتعريفات المفاهيم الرئيسة.",
    processing:
      "المقارنة الموضوعية (لا تلخيص ورقة بورقة فقط)، رصد الاتفاق/الخلاف، وتحديد ما لا يزال مجهولًا في سياقك.",
    outputs:
      "مصفوفة أدبيات، مسودة تعريفات تشغيلية، إطار مفاهيمي، وبيان فجوة واضح.",
    nextStageKey: "problem_purpose",
    nextNote:
      "الفجوة وقاعدة الأدلة تغذيان صياغة المشكلة والغرض والأهمية.",
    why: "التركيب يمنع إعادة اختراع المعروف ويبرر الحاجة لدراستك.",
  },
  problem_purpose: {
    what: "صياغة مشكلة البحث وغرض الدراسة ولماذا تهم علميًا وعمليًا.",
    how: "تحويل الفجوة إلى مشكلة دقيقة (دون نتائج مفترضة)، ثم كتابة الغرض والأهمية.",
    inputs:
      "بيان الفجوة، المجتمع/السياق، وأدلة على وجود المشكلة.",
    processing:
      "تحديد من يتأثر، ما الناقص (مثل تقدير كمي محلي)، ما سيُقاس، ولماذا يهم—دون كتابة نسب أو نتائج قبل الجمع.",
    outputs:
      "بيان مشكلة معتمد، غرض/هدف عام، وأهمية علمية وعملية.",
    nextStageKey: "questions_objectives",
    nextNote:
      "المشكلة والغرض مدخل مباشر لصياغة أسئلة وأهداف قابلة للقياس.",
    why: "إذا كانت المشكلة غامضة أو تجيب عن نفسها مسبقًا، ينهار الاتساق في كل المراحل اللاحقة.",
  },
  questions_objectives: {
    what: "كتابة أسئلة بحث قابلة للإجابة وأهداف مطابقة لها.",
    how: "تقسيم المشكلة إلى أسئلة لها متغيرات/مؤشرات وقصد تحليلي، وربط كل سؤال بهدف بفعل قوي.",
    inputs:
      "المشكلة/الغرض، المجتمع المستهدف، والمتغيرات الأساسية.",
    processing:
      "ربط كل جزء من المشكلة بسؤال (انتشار، فروق، علاقات، أثر)، ثم كتابة أهداف (وصف، فحص، مقارنة…).",
    outputs:
      "حزمة مترابطة من الأسئلة والأهداف تحدد البيانات والتحليلات المطلوبة.",
    nextStageKey: "hypotheses",
    nextNote:
      "حيث يسمح الأساس النظري، تغذي الأسئلة صياغة فرضيات قابلة للاختبار.",
    why: "الأسئلة تقود التصميم والأدوات وحجم العينة والتحليل. السؤال غير الواضح ينتج بيانات غير قابلة للاستخدام.",
  },
  hypotheses: {
    what: "صياغة تنبؤات قابلة للاختبار عندما يناسب التصميم والنظرية ذلك.",
    how: "كتابة فرضيات صفرية/بديلة (أو اتجاهية) مرتبطة بالمتغيرات والاختبارات المخططة؛ وتجنّب الفرضيات القسرية للأهداف الوصفية البحتة.",
    inputs:
      "أسئلة البحث، تعريفات المتغيرات، والأساس النظري/التجريبي.",
    processing:
      "تحديد الأسئلة الاستدلالية، صياغة العلاقات المتوقعة، ومواءمة الصياغة مع مستويات القياس وحدود التصميم.",
    outputs:
      "فرضيات (أو تصريح بعدم الانطباق مع السبب) جاهزة لخطة التحليل.",
    nextStageKey: "constructs_variables",
    nextNote:
      "الفرضيات تتطلب تعريفات واضحة للمفاهيم والمتغيرات لتكون قابلة للقياس.",
    why: "الفرضيات تجعل التنبؤ قابلاً للدحض وتمنع تفسير النتائج بأثر رجعي.",
  },
  constructs_variables: {
    what: "تعريف المفاهيم والمتغيرات التشغيلية (ماذا يُقاس وكيف).",
    how: "تحويل المفاهيم إلى مؤشرات ومقاييس وأدوار (مستقل/تابع/وسيط/ضابط).",
    inputs:
      "الأسئلة/الفرضيات، تعريفات الأدبيات، وخيارات القياس من الدراسات السابقة.",
    processing:
      "كتابة تعريف مفاهيمي وتشغيلي، سرد البنود/المؤشرات، وتعيين أدوار المتغيرات ومستويات القياس.",
    outputs:
      "قاموس متغيرات: الأسماء، الأدوار، المقاييس، والتعريفات التشغيلية.",
    nextStageKey: "methodology",
    nextNote:
      "المتغيرات تحدد أي تصميم ومصادر بيانات تجيب عن كل سؤال.",
    why: "بدون تعريفات تشغيلية لا يمكن ربط الأدوات والتحليل بالأسئلة بصدق.",
  },
  methodology: {
    what: "اختيار تصميم بحث يطابق الأسئلة وحدود الاستدلال.",
    how: "اختيار النموذج/التصميم (مسح، تجريبي، مختلط…) وتبرير الملاءمة والتسلسل وحدود السببية.",
    inputs:
      "الأسئلة، الفرضيات، المتغيرات، الفجوة، والقيود العملية (الوصول، الوقت).",
    processing:
      "ربط كل سؤال بمصدر بيانات ومكوّن تصميم؛ تحديد ترتيب المراحل إن كان مختلطًا؛ وتوثيق مخاطر التحيز.",
    outputs:
      "بروتوكول تصميم يربط كل سؤال ← مصدر بيانات ← متغير ← نوع تحليل، مع خط زمني.",
    nextStageKey: "population_sampling",
    nextNote:
      "التصميم يحدد من يجب معاينته وكيف يتم التجنيد.",
    why: "التصميم جسر بين الأسئلة والأدلة القابلة للدفاع؛ التصميم الخاطئ يُبطل الاستنتاجات.",
  },
  population_sampling: {
    what: "تحديد المجتمع ومعايير الإدراج/الاستبعاد وخطة المعاينة.",
    how: "تحديد حجم المجتمع إن وُجد، أسلوب المعاينة (مثل الطبقية)، مبرر الحجم، ومسار التجنيد.",
    inputs:
      "بروتوكول التصميم، الفئات المستهدفة، وإطارات المجتمع المتاحة.",
    processing:
      "وضع معايير الإدراج/الاستبعاد، تقدير حجم العينة مع الافتراضات، توزيع الطبقات/الحصص، وخطة عدم الاستجابة.",
    outputs:
      "خطة معاينة: المعايير، أساس الحجم، الطبقات/الحصص، وإجراءات التجنيد.",
    nextStageKey: "instruments",
    nextNote:
      "خطة العينة تؤثر على لوجستيات تطبيق الأدوات والتجريب الاستطلاعي.",
    why: "التمثيلية والوصول الأخلاقي يعتمدان على خطة معاينة شفافة.",
  },
  instruments: {
    what: "بناء أدوات جمع البيانات المرتبطة بالمتغيرات والأهداف.",
    how: "صياغة بنود/مهام/سلالم تقييم، وتكييف المقاييس المنشورة بحذر، ومواءمة الصياغة مع التعريفات التشغيلية.",
    inputs:
      "قاموس المتغيرات، أسئلة البحث، مقاييس الأدبيات، ومتطلبات التصميم (استبانة، مهمة، دليل مقابلة).",
    processing:
      "كتابة بنود واضحة غير اتهامية؛ إعداد نسخ قابلة للمقارنة بين الفئات؛ تصميم المهام وسلالم التقييم؛ وإعداد تعليمات الترميز.",
    outputs:
      "مسودات أدوات (استبانات، مهام، سلالم، أدلة) جاهزة لأعمال الصدق والثبات.",
    nextStageKey: "validity_quality",
    nextNote:
      "تنتقل المسودات إلى التحكيم والمقابلات المعرفية والتجريب الاستطلاعي.",
    why: "جودة البيانات بجودة الأداة؛ البنود الضعيفة لا تُصلح بعد انتهاء الجمع الرئيسي.",
  },
  validity_quality: {
    what: "تأسيس الصدق والثبات/الموثوقية قبل الجمع الرئيسي.",
    how: "تحكيم خبراء، مقابلات معرفية، دراسة استطلاعية، مؤشرات ثبات، ومراجعة البنود.",
    inputs:
      "مسودات الأدوات، إمكانية تجريب استطلاعي، وقواعد التصحيح.",
    processing:
      "صدق المحتوى، فحص الوضوح، التطبيق الاستطلاعي، الثبات (مثل ألفا/ICC)، وتعديل/حذف البنود الملتبسة.",
    outputs:
      "أدوات معتمدة، أدلة استطلاعية، ملاحظات ثبات، ونسخ نهائية للتطبيق.",
    nextStageKey: "ethics",
    nextNote:
      "تُرفق الأدوات النهائية بطلب الموافقة الأخلاقية ونصوص الموافقة.",
    why: "بدون صدق/ثبات قد تقيس النتائج ضوضاء لا المفاهيم المقصودة.",
  },
  ethics: {
    what: "حماية المشاركين وتأمين الموافقات الأخلاقية وحماية البيانات.",
    how: "الموافقة المستنيرة، الخصوصية، تخفيف المخاطر، قواعد التخزين، وموافقة المؤسسة قبل الجمع.",
    inputs:
      "البروتوكول النهائي، الأدوات، مخاطر المجتمع، ومتطلبات المؤسسة.",
    processing:
      "إعداد نصوص الموافقة، خطة إخفاء الهوية، ضوابط الوصول، والحصول على الموافقة الأخلاقية؛ ومنع الإكراه الأكاديمي.",
    outputs:
      "حزمة أخلاقية معتمدة، نصوص موافقة، وإجراءات حماية البيانات.",
    nextStageKey: "analysis_plan",
    nextNote:
      "بعد الجاهزية الأخلاقية والأدوات، تُثبَّت خطة التحليل قبل (أو قبل النظر في) بيانات الدراسة الرئيسية.",
    why: "الأخلاقيات شرط علمي وقانوني؛ تأخيرها يعرّض الدراسة كلها للإبطال.",
  },
  analysis_plan: {
    what: "تحديد مسبق لكيفية الإجابة عن كل سؤال بحثي.",
    how: "ربط السؤال ← المتغيرات ← إجراءات وصفية/استدلالية، قواعد المفقود، أحجام الأثر، والبرمجيات.",
    inputs:
      "الأسئلة/الفرضيات، قاموس المتغيرات، التصميم، وأوزان المسح إن وُجدت.",
    processing:
      "اختيار اختبارات/نماذج ملائمة للمقاييس والتصميم (مقترن/مستقل)، تعريف أعلام الاستبعاد، وتخطيط الجداول والرسوم.",
    outputs:
      "وثيقة خطة تحليل قابلة للتنفيذ بعد تنظيف البيانات.",
    nextStageKey: "results",
    nextNote:
      "تُحلَّل البيانات النظيفة وفق هذه الخطة لإنتاج جداول النتائج.",
    why: "التحديد المسبق يقلل التلاعب الانتقائي ويجعل النتائج قابلة للتدقيق.",
  },
  results: {
    what: "عرض النتائج دون تفسير مفرط.",
    how: "تقديم التقديرات مع عدم اليقين (فواصل ثقة) وأحجام الأثر وسريان العينة؛ وفصل الوصف عن المناقشة.",
    inputs:
      "قاعدة بيانات نظيفة، خطة التحليل، ومخرجات موثّقة من البرمجيات.",
    processing:
      "تنفيذ التحليلات المخططة، إنتاج جداول/رسوم من النتائج المعتمدة فقط، والإبلاغ عن n وفواصل الثقة وموثوقية المقيمين إن لزم.",
    outputs:
      "قسم نتائج: جداول ورسوم ونتائج رقمية/نصية مرتبطة بالأسئلة.",
    nextStageKey: "discussion",
    nextNote:
      "النتائج تغذّي التفسير والمقارنة بالأدبيات والقيود.",
    why: "وضوح النتائج يمكّن التحقق؛ خلط التفسير هنا يلبس الرأي ثوب الدليل.",
  },
  discussion: {
    what: "تفسير النتائج مقابل الأدبيات والنظرية والقيود.",
    how: "شرح الأنماط، الاتفاق/الخلاف مع الدراسات السابقة، التفسيرات البديلة، وحدود التصميم (دون ادعاء سببية لا يدعمها التصميم).",
    inputs:
      "النتائج، تركيب الأدبيات، نقاط قوة/ضعف التصميم، والموضوعات النوعية إن وُجدت.",
    processing:
      "دمج مصادر الأدلة بحذر؛ التمييز بين الدلالة الإحصائية والأهمية العملية؛ وذكر التحيزات.",
    outputs:
      "نص مناقشة: تفسير ومقارنة وقيود.",
    nextStageKey: "conclusion",
    nextNote:
      "التفسير يدعم خاتمة حذرة وتوصيات مبنية على الأدلة.",
    why: "المناقشة تحوّل الأرقام إلى معنى علمي دون اختلاق يقين لا يدعمه التصميم.",
  },
  conclusion: {
    what: "الإجابة عن الغرض وتقديم توصيات مبنية على الأدلة.",
    how: "تلخيص إجابات الأسئلة، الآثار العملية/السياسية، والبحوث المستقبلية—مقيّدة بالعينة والتصميم.",
    inputs:
      "المناقشة، النتائج، والسياق المؤسسي/العملي.",
    processing:
      "صياغة استنتاجات تطابق قوة الأدلة؛ سرد توصيات قابلة للتنفيذ وأسئلة متبقية.",
    outputs:
      "خاتمة وتوصيات وأجندة بحث لاحق.",
    nextStageKey: "abstract_title",
    nextNote:
      "النتائج والغرض الأساسيان يغذيان الملخص والعنوان والكلمات المفتاحية.",
    why: "الخاتمة تغلق حلقة البحث وتوجّه متخذي القرار دون تعميم مفرط.",
  },
  abstract_title: {
    what: "تلخيص الدراسة للاكتشاف: العنوان والملخص والكلمات المفتاحية.",
    how: "كتابة عنوان دقيق وملخص منظم (الغرض، المنهج، أبرز النتائج، الآثار) بكلمات مفتاحية قابلة للبحث.",
    inputs:
      "الغرض النهائي، ملخص المنهج، النتائج الرئيسة، والخاتمة.",
    processing:
      "ضغط دقيق؛ تجنب ادعاءات غير موجودة في النتائج؛ مواءمة الكلمات المفتاحية مع مصطلحات الأدبيات.",
    outputs:
      "عنوان وملخص وكلمات مفتاحية جاهزة للتقديم/الفهرسة.",
    nextStageKey: "references",
    nextNote:
      "مصادر الملخص يجب أن تطابق قائمة المراجع الموثّقة.",
    why: "معظم القرّاء يقررون من العنوان/الملخص؛ الدقة هنا تحمي النزاهة وقابلية الاكتشاف.",
  },
  references: {
    what: "توثيق كل المصادر بدقة واتساق.",
    how: "التحقق من كل استشهاد من الأصل، استكمال البيانات (DOI، الصفحات)، وتطبيق أسلوب التوثيق المختار.",
    inputs:
      "كل الأعمال المستشهد بها في الأدبيات والمنهج والمناقشة.",
    processing:
      "مطابقة الاستشهادات داخل النص بالقائمة، فتح المصادر، إصلاح البيانات، ورفض المراجع المختلقة.",
    outputs:
      "قائمة مراجع كاملة ومتسقة وفحص نزاهة الاستشهاد.",
    nextStageKey: null,
    nextNote:
      "المراجع تغلق سلسلة المخطوطة؛ الفجوات قد تفتح دورة بحث جديدة.",
    why: "نزاهة التوثيق شرط غير قابل للتفاوض للمصداقية الأكاديمية وقابلية إعادة الإنتاج.",
  },
};

export function getStageGuide(lang: "en" | "ar", key: string): StageGuide | null {
  const table = lang === "ar" ? ar : en;
  return table[key] || en[key] || null;
}

export function stageGuideLabels(lang: "en" | "ar") {
  if (lang === "ar") {
    return {
      what: "ما هذه المرحلة؟",
      how: "كيف تعمل؟",
      inputs: "المدخلات",
      processing: "المعالجة / كيف تُعالَج المدخلات",
      outputs: "المخرجات",
      next: "المرحلة التالية (التي تستقبل المخرجات)",
      why: "لماذا هذه المرحلة مهمة للبحث؟",
      chain: "سلسلة الانتقال",
      end: "نهاية السلسلة الرئيسة (أو بداية دورة جديدة)",
      toggleHint: "اضغط على اسم المرحلة لعرض الشرح",
      collapse: "إخفاء الشرح",
      expand: "عرض الشرح",
    };
  }
  return {
    what: "What is this stage?",
    how: "How does it work?",
    inputs: "Inputs",
    processing: "Processing / how inputs are handled",
    outputs: "Outputs",
    next: "Next stage (receives these outputs)",
    why: "Why this stage matters for research",
    chain: "Handoff chain",
    end: "End of the main chain (or start of a new cycle)",
    toggleHint: "Click the stage name to expand the guide",
    collapse: "Hide guide",
    expand: "Show guide",
  };
}
