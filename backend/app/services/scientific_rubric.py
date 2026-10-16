"""Application-authored review rubric; not an official checklist or validated quality scale."""
VERSION = '2026-10-16.1'
SOURCES = [
    {'id':'equator','name':'EQUATOR — guideline selection by study design','url':'https://www.equator-network.org/','scope':'Health-research reporting; select the actual design-specific checklist.'},
    {'id':'icmje','name':'ICMJE — manuscript preparation','url':'https://www.icmje.org/recommendations/browse/manuscript-preparation/preparing-for-submission.html','scope':'Medical-journal guidance; structure varies by article type.'},
    {'id':'prisma','name':'PRISMA 2020','url':'https://www.prisma-statement.org/prisma-2020','scope':'Reporting systematic reviews; not a universal research-quality score.'},
    {'id':'strobe','name':'STROBE','url':'https://www.strobe-statement.org/','scope':'Observational epidemiology; not a study-quality appraisal instrument.'},
    {'id':'consort','name':'CONSORT 2025 / SPIRIT 2025','url':'https://www.consort-spirit.org/','scope':'Randomised-trial reports / trial protocols respectively.'},
    {'id':'srqr','name':'SRQR','url':'https://www.equator-network.org/reporting-guidelines/srqr/','scope':'Qualitative-research reporting.'},
    {'id':'top','name':'TOP 2025','url':'https://www.cos.io/initiatives/top-guidelines','scope':'Transparency policy framework; adoption depends on discipline and journal.'},
]
TYPES = [
    {'id':'general','en':'General / unspecified research','ar':'بحث عام / نوع غير محدد'},
    {'id':'conceptual_legal','en':'Conceptual, theoretical or doctrinal legal paper','ar':'بحث نظري أو مفاهيمي أو قانوني تحليلي'},
    {'id':'quantitative','en':'Quantitative empirical research','ar':'بحث كمي تجريبي أو ميداني'},
    {'id':'observational_health','en':'Observational health study','ar':'دراسة صحية رصدية'},
    {'id':'qualitative','en':'Qualitative research','ar':'بحث نوعي'},
    {'id':'systematic_review','en':'Systematic review','ar':'مراجعة منهجية'},
    {'id':'randomized_trial','en':'Randomized trial report','ar':'تقرير تجربة عشوائية'},
    {'id':'proposal','en':'Research proposal / protocol','ar':'مقترح بحث / بروتوكول'},
]

def criterion(key,en,ar,detail_en,detail_ar,guide_en,guide_ar,source='app',conditional=False):
    return {'id':key,'title_en':en,'title_ar':ar,'description_en':detail_en,'description_ar':detail_ar,'guidance_en':guide_en,'guidance_ar':guide_ar,'source_id':source,'conditional':conditional}

CORE = [
    criterion('focus','Clear title and informative summary','وضوح العنوان والملخص',
        'The title identifies the subject and scope. A summary explains the question, approach and main message; a proposal describes intended work rather than inventing results.',
        'يعرّف العنوان موضوع البحث وحدوده. ويشرح الملخص السؤال والمنهج والرسالة الأساسية؛ أما المقترح فيعرض العمل المزمع تنفيذه دون اختلاق نتائج.',
        'Align the title with the actual scope. Write a compact summary covering purpose, approach and contribution; check the target institution’s abstract requirements.',
        'طابق العنوان مع النطاق الفعلي، واكتب ملخصاً يوضح الغرض والمنهج والإضافة، وراجع متطلبات الملخص لدى المؤسسة أو المجلة.'),
    criterion('problem','Defined research problem','تحديد مشكلة البحث',
        'The reader can identify the unresolved issue, its context and why it deserves investigation. A broad topic alone does not define a research problem.',
        'يستطيع القارئ تحديد المسألة غير المحسومة وسياقها وأهميتها. عرض موضوع واسع وحده لا يكفي لتحديد مشكلة بحثية.',
        'State the specific uncertainty or tension and delimit the context. Connect its importance to supported evidence rather than general claims.',
        'صغ موضع الغموض أو التعارض بدقة وحدد سياقه، واربط أهميته بأدلة بدلاً من العبارات العامة.'),
    criterion('gap','Justified gap and contribution','تبرير الفجوة والإضافة العلمية',
        'The paper explains what existing knowledge does not resolve and what its own analysis adds. Novelty must not be assumed from a claim that no prior studies exist.',
        'يوضح البحث ما لم تحسمه المعرفة السابقة وما يضيفه تحليله. ولا تُستنتج الجدة بمجرد الادعاء بعدم وجود دراسات سابقة.',
        'Compare relevant work, identify a precise unresolved issue, and state the contribution at a scale supported by the paper.',
        'قارن الأعمال ذات الصلة وحدد مسألة غير محسومة، ثم صغ الإضافة بقدر ما يدعمه البحث.'),
    criterion('aims','Specific, aligned aims and questions','اتساق الأهداف والأسئلة',
        'Aims and questions are clear enough to be answered by the chosen approach. Hypotheses are needed only when appropriate to the design.',
        'تكون الأهداف والأسئلة واضحة وقابلة للإجابة بالمنهج المختار. ولا تُفرض فرضيات حين لا يستلزمها تصميم الدراسة.',
        'Map each question to an objective, an evidence source and a corresponding analytical step.',
        'اربط كل سؤال بهدف ومصدر أدلة وخطوة تحليل مناسبة.'),
    criterion('context','Critical engagement with prior work','مناقشة المعرفة والدراسات السابقة',
        'Relevant literature or authoritative materials are synthesised critically. The discussion explains agreements, disagreements and the paper’s position rather than merely listing sources.',
        'تُناقش الأدبيات أو المواد المرجعية الموثوقة نقدياً، مع بيان الاتفاق والاختلاف وموقع البحث منها بدلاً من سرد المصادر فقط.',
        'Organise prior work around themes and disagreements, and explain how each theme informs the problem or argument.',
        'نظّم المصادر حول الموضوعات والخلافات، وبيّن صلتها بالمشكلة أو الحجة البحثية.'),
    criterion('method','Transparent and appropriate approach','وضوح المنهج وملاءمته',
        'The paper explains how it selects and analyses evidence. Legal and theoretical work can use interpretive or comparative methods without participants or statistical samples.',
        'يشرح البحث كيف يختار الأدلة ويحللها. وقد يعتمد البحث القانوني أو النظري منهجاً تفسيرياً أو مقارناً دون مشاركين أو عينات إحصائية.',
        'Describe the materials, selection boundaries and analytical steps so a reader can follow the reasoning; proposals describe planned steps.',
        'اشرح المواد وحدود اختيارها وخطوات تحليلها بحيث يستطيع القارئ تتبع الاستدلال؛ وفي المقترح تُشرح الخطوات المخططة.'),
    criterion('support','Claims supported by evidence','إسناد الادعاءات بالأدلة',
        'Central claims are supported by identifiable data, source material or a reasoned argument. Observations, interpretations and recommendations remain distinguishable.',
        'تستند الادعاءات الأساسية إلى بيانات أو مواد مصدرية محددة أو حجة منطقية، مع الفصل بين الملاحظة والتفسير والتوصية.',
        'For each major claim, supply the relevant evidence and explain the inference. Mark unsupported additions as requiring evidence.',
        'قدّم لكل ادعاء رئيس دليله وفسّر الانتقال منه إلى الاستنتاج، وميّز الإضافات التي تحتاج إلى سند.'),
    criterion('conclusions','Interpretation and conclusions answer the question','اتساق المناقشة والخاتمة مع السؤال',
        'Interpretation addresses the stated aims and competing explanations. Conclusions stay within the evidence. Proposals connect planned work to expected contributions without claiming completed findings.',
        'تعالج المناقشة الأهداف والتفسيرات البديلة وتلتزم الخاتمة بالأدلة. وفي المقترحات يُربط العمل المخطط بإضافته المتوقعة دون ادعاء نتائج منجزة.',
        'Connect each conclusion to a question and its evidence. Separate implications from claims already established.',
        'اربط كل استنتاج بسؤال ودليل، وافصل الدلالات والتوصيات عما أثبته التحليل فعلاً.'),
    criterion('limitations','Explicit limitations and scope','بيان الحدود والقيود',
        'The paper identifies constraints on its sources, method and interpretation, and explains their consequences for transferability or generalisation.',
        'يوضح البحث القيود المتعلقة بالمصادر والمنهج والتفسير وأثرها في قابلية التعميم أو نقل النتائج إلى سياقات أخرى.',
        'Describe concrete limitations and their effects rather than adding a generic disclaimer. Explain useful next investigations.',
        'اذكر قيوداً محددة وأثرها الفعلي بدلاً من تحفظات عامة، وحدد ما ينبغي بحثه لاحقاً.'),
    criterion('references','Traceable citations and references','قابلية تتبع الاستشهادات والمراجع',
        'Readers can trace important claims to citations and sufficiently described references. This text review does not establish that a reference exists or that its contents support the claim.',
        'يمكن تتبع الادعاءات المهمة إلى استشهادات ومراجع موصوفة بوضوح. ولا يثبت الفحص النصي وجود المرجع فعلاً أو مطابقته للادعاء.',
        'Match in-text citations with the reference list and supply missing identifiers or publication details; verify originals independently.',
        'طابق الاستشهادات مع قائمة المراجع وأكمل البيانات والمعرّفات الناقصة، ثم تحقق من الأصول بصورة مستقلة.'),
    criterion('ethics','Ethics and participant protection where relevant','الأخلاقيات وحماية المشاركين عند انطباقها',
        'For human, animal or sensitive-data research, explain approvals or exemptions, consent and protection measures as appropriate. A purely textual paper can be inapplicable with a reason.',
        'عند دراسة البشر أو الحيوانات أو البيانات الحساسة، تُوضح الموافقات أو الإعفاءات والموافقة المستنيرة والحماية بحسب الحال. وقد لا ينطبق البند على بحث نصي بحت مع تبرير ذلك.',
        'State the applicable oversight and safeguards; never invent an approval number. Explain non-applicability when supported by the study type.',
        'اذكر الإشراف والضمانات الملائمة دون اختلاق رقم موافقة، وفسّر عدم الانطباق إذا كان نوع البحث يدعمه.',conditional=True),
    criterion('transparency','Transparency and relevant disclosures','الشفافية والإفصاحات الملائمة',
        'Explain relevant funding, interests, contributions and access to underlying materials or data, including justified restrictions. Requirements differ by discipline and venue.',
        'بيّن التمويل والمصالح والإسهامات والوصول إلى المواد أو البيانات بحسب صلتها بالبحث، مع تبرير القيود. تختلف المتطلبات باختلاف التخصص وجهة النشر.',
        'Add accurate disclosure and availability statements appropriate to the study. Restricted data need a reason, not an invented public link.',
        'أضف إفصاحات وبيان إتاحة يناسبان الدراسة. وعند تقييد البيانات وضّح السبب بدلاً من اختلاق رابط إتاحة.',source='top'),
]

DESIGNS = {
 'conceptual_legal':[
    criterion('legal_scope','Defined conceptual or legal scope','تحديد النطاق المفاهيمي أو القانوني','Define concepts and theoretical boundaries; legal work also identifies the relevant jurisdiction and period.','حدّد المفاهيم والحدود النظرية؛ وفي البحث القانوني حدّد كذلك الاختصاص والفترة المعنيين.','Explain boundaries and, for legal work, distinguish current law from reform proposals.','وضّح الحدود، وافصل في البحث القانوني القانون النافذ عن مقترحات الإصلاح.'),
    criterion('authority','Source authority and selection','حجية المصادر وأسس اختيارها','Explain why texts, cases or theoretical sources are authoritative and relevant.','فسّر حجية النصوص أو الأحكام أو المصادر النظرية وصلتها بالبحث.','Identify source hierarchy and selection criteria; independently check legal currency.','بيّن تدرج المصادر ومعايير اختيارها، وتحقق مستقلاً من سريان الأحكام.'),
    criterion('counterarguments','Coherent reasoning and competing interpretations','تماسك الاستدلال ومناقشة الآراء البديلة','Consider credible alternative interpretations and explain the preferred argument.','ناقش تفسيرات بديلة معتبرة وعلّل ترجيح الحجة المختارة.','Address strong counterarguments without attributing unsupported positions to authors.','عالج الاعتراضات القوية دون نسبة آراء غير موثقة إلى أصحابها.'),
 ],
 'quantitative':[
    criterion('quant_design','Population, measures and design','المجتمع والقياس وتصميم الدراسة','Explain sampling, measurement and design choices relevant to the question.','اشرح الاختيار والقياس والتصميم بما يناسب السؤال.','Justify scope, instrument suitability and sources of bias.','علّل النطاق وملاءمة الأدوات ومصادر التحيز.'),
    criterion('quant_analysis','Analysis and uncertainty','التحليل وعدم اليقين','Report appropriate analyses, uncertainty and handling of incomplete observations.','اعرض التحليلات الملائمة وعدم اليقين ومعالجة المشاهدات الناقصة.','Connect analyses to questions and avoid unsupported causal interpretations.','اربط التحليلات بالأسئلة وتجنب التفسيرات السببية غير المدعومة.'),
 ],
 'observational_health':[
    criterion('obs_design','Observational design and participants','التصميم الرصدي والمشاركون','Describe design, setting, eligibility and how participants entered the study.','صف التصميم والسياق والأهلية وكيفية إدراج المشاركين.','Use the applicable STROBE design checklist for the complete requirements.','راجع قائمة STROBE المناسبة للتصميم لمعرفة المتطلبات الكاملة.',source='strobe'),
    criterion('obs_bias','Bias, confounding and precision','التحيز والعوامل المربكة والدقة','Explain important bias controls and uncertainty around estimated associations.','وضّح معالجة التحيز والعوامل المربكة وعدم اليقين في الارتباطات المقدرة.','Make assumptions and adjustments explicit; distinguish association from causation.','بيّن الافتراضات والتعديلات وافصل الارتباط عن السببية.',source='strobe'),
 ],
 'qualitative':[
    criterion('qual_context','Context, sampling and reflexivity','السياق واختيار المشاركين والانعكاسية','Explain context, selection and how the researcher’s position may influence the work.','اشرح السياق والاختيار وأثر موقع الباحث في العمل.','Use SRQR alongside the study’s actual qualitative tradition.','راجع SRQR مع مراعاة التقليد النوعي المستخدم.',source='srqr'),
    criterion('qual_analysis','Interpretive process and credibility','التحليل النوعي ومصداقيته','Describe how interpretations arose from material and how credibility was addressed.','صف نشأة التفسيرات من المادة وكيفية دعم مصداقيتها.','Connect analytical claims to material while protecting identities.','اربط الادعاءات التحليلية بالمادة مع حماية الهويات.',source='srqr'),
 ],
 'systematic_review':[
    criterion('review_search','Reproducible search and selection','وضوح البحث عن الدراسات واختيارها','Describe information sources, search timing, eligibility and selection procedures.','صف مصادر البحث وتوقيته والأهلية وإجراءات الاختيار.','Consult PRISMA 2020 for the complete reporting checklist.','ارجع إلى PRISMA 2020 للاطلاع على قائمة الإبلاغ الكاملة.',source='prisma'),
    criterion('review_appraisal','Appraisal, synthesis and certainty','التقييم النقدي والتركيب ويقين الأدلة','Explain appraisal and synthesis methods, reporting uncertainty and restrictions.','اشرح التقييم النقدي والتركيب وعدم اليقين والقيود.','Link conclusions to the included evidence and its limitations.','اربط الاستنتاجات بالأدلة المشمولة وحدودها.',source='prisma'),
    criterion('review_protocol','Protocol and study accounting','البروتوكول وتتبع الدراسات','Report protocol information and account for selection decisions.','اعرض معلومات البروتوكول وقرارات إدراج الدراسات واستبعادها.','Explain departures transparently rather than inventing registration.','فسّر الانحرافات بشفافية دون اختلاق تسجيل.',source='prisma'),
 ],
 'randomized_trial':[
    criterion('trial_allocation','Randomisation and allocation safeguards','العشوائية وضمانات التخصيص','Explain assignment and protections against allocation-related bias.','اشرح إسناد المشاركين وضمانات الحد من تحيز التخصيص.','Use the complete CONSORT 2025 checklist appropriate to the trial.','استخدم قائمة CONSORT 2025 الكاملة المناسبة للتجربة.',source='consort'),
    criterion('trial_flow','Participant flow, outcomes and harms','تدفق المشاركين والنتائج والأضرار','Report participant accounting, outcomes and harms transparently.','اعرض تتبع المشاركين والنتائج والأضرار بشفافية.','Explain exclusions and departures from planned outcomes.','فسّر الاستبعادات والتغييرات في النتائج المخططة.',source='consort'),
 ],
 'proposal':[
    criterion('proposal_plan','Feasible planned methods','قابلية تنفيذ المنهج المخطط','Specify planned evidence collection, analysis and resources without claiming completed results.','حدّد جمع الأدلة والتحليل والموارد المخططة دون ادعاء نتائج منجزة.','Explain practical constraints and contingencies.','وضّح القيود العملية والبدائل عند تعذر التنفيذ.'),
    criterion('proposal_outputs','Expected contribution and evaluation plan','الإضافة المتوقعة وخطة تقييمها','Explain intended outputs and how the question will be answered.','بيّن المخرجات المقصودة وكيف ستجاب الأسئلة.','Use the relevant protocol guideline if this is a clinical trial or systematic-review protocol.','استخدم دليل البروتوكول المختص إن كان المقترح لتجربة سريرية أو مراجعة منهجية.'),
 ],
}

def rubric(paper_type):
    if paper_type not in {item['id'] for item in TYPES}:raise ValueError('Unknown paper type')
    return [*CORE,*DESIGNS.get(paper_type,[])]

def catalog():
    return {'version':VERSION,'types':TYPES,'sources':SOURCES,'criteria':{kind['id']:rubric(kind['id']) for kind in TYPES},'reviewed_on':'2026-10-16'}
