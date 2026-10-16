export interface User {
  id: number;
  email: string;
  full_name: string;
  preferred_language: string;
  is_active: boolean;
  created_at: string;
  username: string | null;
  is_superuser: boolean;
  permissions: string[];
  must_change_password: boolean;
}

export interface StageDefinition {
  key: string;
  order: number;
  label_en: string;
  label_ar: string;
}

export interface StageProgress {
  id: number;
  stage_key: string;
  status: string;
  notes?: string | null;
  completed_at?: string | null;
}

export interface Profile {
  id: number;
  project_id: number;
  research_problem?: string | null;
  existing_evidence?: string | null;
  research_gap?: string | null;
  overall_aim?: string | null;
  expected_contribution?: string | null;
  ethics_requirements?: string | null;
  unresolved_decisions?: string | null;
  assumptions_requiring_verification?: string | null;
  refined_idea?: string | null;
  proposed_scope?: string | null;
  key_concepts?: string | null;
  initial_search_terms?: string | null;
  scientific_significance?: string | null;
  practical_significance?: string | null;
  researcher_approved_summary?: string | null;
  ai_suggestions_summary?: string | null;
  updated_at: string;
}

export interface ProjectSummary {
  id: number;
  working_title: string;
  research_field?: string | null;
  document_type: string;
  current_stage: string;
  writing_language: string;
  status: string;
  completion_percent: number;
  updated_at: string;
}

export interface Project extends ProjectSummary {
  owner_id: number;
  target_institution?: string | null;
  target_journal?: string | null;
  citation_style: string;
  study_context?: string | null;
  population_summary?: string | null;
  deadline?: string | null;
  notes?: string | null;
  created_at: string;
  profile?: Profile | null;
  stage_progress: StageProgress[];
}

export interface Message {
  id: number;
  conversation_id: number;
  role: string;
  content: string;
  stage_key?: string | null;
  structured_json?: string | null;
  created_at: string;
}

export interface Conversation {
  id: number;
  project_id: number;
  title: string;
  stage_key?: string | null;
  is_active: boolean;
  messages: Message[];
  created_at: string;
}

export interface Question {
  id: number;
  project_id: number;
  text: string;
  question_type: string;
  sort_order: number;
  data_source?: string | null;
  proposed_analysis?: string | null;
  approval_status: string;
  created_at: string;
}

export interface Objective {
  id: number;
  project_id: number;
  question_id?: number | null;
  text: string;
  objective_type?: string | null;
  verb?: string | null;
  sort_order: number;
  approval_status: string;
}

export interface AlignmentIssue {
  id: number;
  project_id: number;
  issue_type: string;
  severity: string;
  explanation: string;
  affected_elements?: string | null;
  recommended_correction?: string | null;
  correction_options?: string | null;
  resolution_status: string;
  created_at: string;
}

export interface AlignmentReport {
  project_id: number;
  issues: AlignmentIssue[];
  summary: Record<string, number>;
  chain_status: Record<string, string>;
}

export interface Reference {
  id: number;
  project_id: number;
  title: string;
  authors?: string | null;
  year?: number | null;
  journal?: string | null;
  doi?: string | null;
  url?: string | null;
  verification_status: string;
  relevance_category: string;
  approval_status: string;
  main_finding?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface LiteratureResult {
  title: string;
  authors?: string | null;
  year?: number | null;
  journal?: string | null;
  doi?: string | null;
  url?: string | null;
  abstract?: string | null;
  verification_status: string;
}

export interface DocumentItem {
  id: number;
  project_id: number;
  original_filename: string;
  file_type: string;
  file_size: number;
  category: string;
  processing_status: string;
  extracted_text_status: string;
  verification_status: string;
  notes?: string | null;
  created_at: string;
}

export interface AISuggestion {
  id: number;
  project_id: number;
  stage_key?: string | null;
  suggestion_type: string;
  title: string;
  content: string;
  structured_json?: string | null;
  approval_status: string;
  target_element_type?: string | null;
  target_element_id?: number | null;
  created_at: string;
  payload?: Record<string, unknown> | null;
  rationale?: string | null;
}

export interface Hypothesis {
  id: number;
  project_id: number;
  question_id?: number | null;
  null_hypothesis: string;
  alternative_hypothesis: string;
  direction: string;
  independent_variable?: string | null;
  dependent_variable?: string | null;
  population?: string | null;
  expected_direction?: string | null;
  proposed_test?: string | null;
  theoretical_basis?: string | null;
  approval_status: string;
  sort_order: number;
}

export interface Variable {
  id: number;
  project_id: number;
  construct_id?: number | null;
  name: string;
  role: string;
  measurement_scale?: string | null;
  data_source?: string | null;
  coding?: string | null;
  approval_status: string;
}

export interface Design {
  id: number;
  project_id: number;
  design_type: string;
  paradigm?: string | null;
  rationale?: string | null;
  strengths?: string | null;
  limitations?: string | null;
  bias_risks?: string | null;
  is_primary: boolean;
  approval_status: string;
}

export interface Population {
  id: number;
  project_id: number;
  target_population: string;
  accessible_population?: string | null;
  unit_of_analysis?: string | null;
  inclusion_criteria?: string | null;
  exclusion_criteria?: string | null;
  approval_status: string;
}

export interface SamplingPlan {
  id: number;
  project_id: number;
  sampling_frame?: string | null;
  sampling_method?: string | null;
  sample_size?: number | null;
  sample_size_rationale?: string | null;
  recruitment_method?: string | null;
  response_rate_strategy?: string | null;
  non_response_considerations?: string | null;
  assumptions?: string | null;
  approval_status: string;
}

export interface InstrumentItem {
  id: number;
  item_text: string;
  response_type: string;
  response_options?: string | null;
  construct_name?: string | null;
  variable_name?: string | null;
  linked_objective?: string | null;
  linked_question?: string | null;
  planned_analysis?: string | null;
  sort_order: number;
  approval_status: string;
}

export interface InstrumentSection {
  id: number;
  title: string;
  instructions?: string | null;
  sort_order: number;
  items: InstrumentItem[];
}

export interface Instrument {
  id: number;
  project_id: number;
  name: string;
  instrument_type: string;
  description?: string | null;
  is_established_scale: boolean;
  validation_notes?: string | null;
  licensing_notes?: string | null;
  approval_status: string;
  sections: InstrumentSection[];
}

export interface AnalysisMapping {
  id: number;
  question_id?: number | null;
  hypothesis_id?: number | null;
  variables?: string | null;
  data_type?: string | null;
  descriptive_stats?: string | null;
  statistical_test?: string | null;
  test_assumptions?: string | null;
  effect_size?: string | null;
  planned_table_or_figure?: string | null;
  notes?: string | null;
  approval_status: string;
}

export interface AnalysisPlan {
  id: number;
  project_id: number;
  title: string;
  software?: string | null;
  significance_level?: string | null;
  missing_data_strategy?: string | null;
  notes?: string | null;
  approval_status: string;
  mappings: AnalysisMapping[];
}

export interface SourceDocumentSummary {
  id: number;
  project_id: number;
  original_filename: string;
  file_type: string;
  file_size: number;
  page_count?: number | null;
  processing_status: string;
  ocr_status: string;
  extraction_status: string;
  detected_language?: string | null;
  document_type?: string | null;
  document_type_confidence?: number | null;
  document_type_confirmed: boolean;
  academic_level?: string | null;
  discipline?: string | null;
  research_design?: string | null;
  methodology_paradigm?: string | null;
  title_detected?: string | null;
  year_detected?: number | null;
  verification_status: string;
  is_reference_only: boolean;
  created_at: string;
}

export interface LibrarySection {
  id: number;
  heading: string;
  normalized_heading?: string | null;
  content: string;
  summary?: string | null;
  sort_order: number;
  content_kind: string;
  confidence?: number | null;
}

export interface LibraryStageMapping {
  id: number;
  stage_key: string;
  status: string;
  original_heading?: string | null;
  page_or_section?: string | null;
  extracted_excerpt?: string | null;
  ai_summary?: string | null;
  completeness?: string | null;
  methodological_clarity?: string | null;
  strengths?: string | null;
  limitations?: string | null;
  lessons_for_user?: string | null;
  connection_to_next?: string | null;
  writing_strategy?: string | null;
  confidence?: number | null;
  researcher_verified: boolean;
  researcher_correction?: string | null;
}

export interface LibraryElement {
  id: number;
  element_type: string;
  content_role: string;
  value_text: string;
  page_or_section?: string | null;
  section_heading?: string | null;
  confidence?: number | null;
  verification_status: string;
  reuse_category: string;
}

export interface StudySummary {
  purpose?: string;
  title?: string | null;
  document_type?: string | null;
  document_type_confidence?: number | null;
  main_ideas?: string;
  methods?: string;
  findings?: string;
  conclusions?: string;
  writing_style?: string[];
  structure_explanation?: string[];
  how_to_study?: string[];
  integrity_note?: string;
}

export interface SourceDocumentDetail extends SourceDocumentSummary {
  document_type_evidence?: string | null;
  academic_level_confidence?: number | null;
  authors_detected?: string | null;
  abstract_excerpt?: string | null;
  analysis_warnings: string[];
  learning_report?: Record<string, unknown> | null;
  quality_analysis?: Record<string, unknown> | null;
  structure_map?: Record<string, unknown> | null;
  study_summary?: StudySummary | null;
  researcher_notes?: string | null;
  sections: LibrarySection[];
  stage_mappings: LibraryStageMapping[];
  elements: LibraryElement[];
  integrity_notice: string;
}

export interface MultiUploadResult {
  uploaded: SourceDocumentDetail[];
  failed: { filename: string; error: string }[];
  message: string;
}

export interface BenchmarkStageRow {
  stage_key: string;
  label: string;
  purpose?: string;
  user_status: string;
  papers_detected: number;
  papers_total: number;
  papers_detected_ratio: number;
  verdict: string;
  verdict_label: string;
  recommendation: string;
  reference_examples: {
    document_id: number;
    title?: string | null;
    status?: string;
    heading?: string | null;
    summary?: string;
  }[];
}

export interface SynthesisDashboard {
  language: string;
  status: string;
  headline: string;
  message: string;
  integrity_notice: string;
  paper_count: number;
  papers: Record<string, unknown>[];
  insight_cards: {
    id: string;
    kind?: string;
    title: string;
    body: string;
    priority?: string;
  }[];
  theme_cloud: { term: string; count?: number; weight?: number; label?: string }[];
  method_patterns: {
    kind: string;
    name: string;
    count: number;
    share: number;
    insight?: string;
  }[];
  stage_heatmap: {
    stage_key: string;
    label: string;
    purpose?: string;
    detected?: number;
    coverage: number;
    intensity: string;
    lesson?: string;
  }[];
  gap_signals: { type?: string; title: string; body: string; stage_key?: string }[];
  writing_moves: { move: string; frequency: number; tip: string; share?: number }[];
  learning_path: string[];
  comparison_matrix: {
    document_id: number;
    title: string;
    type: string;
    design: string;
    paradigm?: string;
    main_ideas: string;
    methods: string;
    findings: string;
    conclusions?: string;
    stages_covered: number;
  }[];
  stats?: {
    types?: Record<string, number>;
    paradigms?: Record<string, number>;
    designs?: Record<string, number>;
    with_results?: number;
    with_methods?: number;
  } | null;
  ai_enriched: boolean;
  ai_synthesis?: Record<string, unknown> | null;
}

export interface BenchmarkResult {
  language: string;
  status: string;
  message: string;
  integrity_notice: string;
  project?: Record<string, unknown> | null;
  papers: {
    id: number;
    title?: string | null;
    document_type?: string | null;
    research_design?: string | null;
    methodology_paradigm?: string | null;
    processing_status?: string;
  }[];
  stage_benchmarks: BenchmarkStageRow[];
  design_comparison?: {
    user_designs?: string[];
    reference_designs?: string[];
    reference_paradigms?: string[];
    notes?: string[];
  } | null;
  gaps: string[];
  strengths: string[];
  recommendations: string[];
  overall_score?: number | null;
  score_explanation?: string | null;
  ai_enriched: boolean;
  ai_narrative?: Record<string, unknown> | null;
}

export interface PaperComparison {
  id: number;
  project_id: number;
  title: string;
  document_ids: number[];
  summary?: Record<string, unknown> | null;
  lessons?: Record<string, unknown> | null;
  items: {
    id: number;
    element_key: string;
    values: Record<string, string>;
    lessons?: string | null;
  }[];
  created_at: string;
}

export interface WriteSectionGuide {
  stage_key: string;
  stage_label: string;
  purpose: string;
  reference: {
    document_id: number;
    document_title?: string | null;
    status?: string;
    heading?: string | null;
    summary?: string | null;
    short_excerpt_for_illustration_only?: string | null;
    lessons?: string | null;
    writing_strategy?: string | null;
  };
  user_project_snapshot: Record<string, unknown>;
  structural_pattern_from_reference: string[];
  questions_for_you: { id: string; prompt: string; hint?: string }[];
  outline_template: string[];
  citation_placeholders: string[];
  integrity_rules: string[];
  mistakes_to_avoid: string[];
}
