"""Research structure schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ApprovalMixin(BaseModel):
    approval_status: str = "proposed"


class QuestionCreate(BaseModel):
    text: str = Field(min_length=1)
    question_type: str = "descriptive"
    sort_order: int = 0
    data_source: str | None = None
    proposed_analysis: str | None = None
    approval_status: str = "proposed"


class QuestionUpdate(BaseModel):
    text: str | None = None
    question_type: str | None = None
    sort_order: int | None = None
    data_source: str | None = None
    proposed_analysis: str | None = None
    approval_status: str | None = None


class QuestionOut(BaseModel):
    id: int
    project_id: int
    text: str
    question_type: str
    sort_order: int
    data_source: str | None
    proposed_analysis: str | None
    approval_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ObjectiveCreate(BaseModel):
    text: str = Field(min_length=1)
    question_id: int | None = None
    objective_type: str | None = None
    verb: str | None = None
    sort_order: int = 0
    approval_status: str = "proposed"


class ObjectiveUpdate(BaseModel):
    text: str | None = None
    question_id: int | None = None
    objective_type: str | None = None
    verb: str | None = None
    sort_order: int | None = None
    approval_status: str | None = None


class ObjectiveOut(BaseModel):
    id: int
    project_id: int
    question_id: int | None
    text: str
    objective_type: str | None
    verb: str | None
    sort_order: int
    approval_status: str

    model_config = {"from_attributes": True}


class HypothesisCreate(BaseModel):
    null_hypothesis: str
    alternative_hypothesis: str
    question_id: int | None = None
    direction: str = "non_directional"
    independent_variable: str | None = None
    dependent_variable: str | None = None
    population: str | None = None
    expected_direction: str | None = None
    proposed_test: str | None = None
    theoretical_basis: str | None = None
    sort_order: int = 0
    approval_status: str = "proposed"


class HypothesisOut(BaseModel):
    id: int
    project_id: int
    question_id: int | None
    null_hypothesis: str
    alternative_hypothesis: str
    direction: str
    independent_variable: str | None
    dependent_variable: str | None
    population: str | None
    expected_direction: str | None
    proposed_test: str | None
    theoretical_basis: str | None
    approval_status: str
    sort_order: int

    model_config = {"from_attributes": True}


class VariableCreate(BaseModel):
    name: str
    role: str = "dependent"
    construct_id: int | None = None
    measurement_scale: str | None = None
    data_source: str | None = None
    coding: str | None = None
    operational_definition: str | None = None
    measurement_method: str | None = None
    approval_status: str = "proposed"


class VariableOut(BaseModel):
    id: int
    project_id: int
    construct_id: int | None
    name: str
    role: str
    measurement_scale: str | None
    data_source: str | None
    coding: str | None
    approval_status: str

    model_config = {"from_attributes": True}


class DesignCreate(BaseModel):
    design_type: str
    paradigm: str | None = None
    rationale: str | None = None
    strengths: str | None = None
    limitations: str | None = None
    bias_risks: str | None = None
    is_primary: bool = True
    approval_status: str = "proposed"


class DesignOut(BaseModel):
    id: int
    project_id: int
    design_type: str
    paradigm: str | None
    rationale: str | None
    strengths: str | None
    limitations: str | None
    bias_risks: str | None
    is_primary: bool
    approval_status: str

    model_config = {"from_attributes": True}


class PopulationCreate(BaseModel):
    target_population: str
    accessible_population: str | None = None
    unit_of_analysis: str | None = None
    inclusion_criteria: str | None = None
    exclusion_criteria: str | None = None
    approval_status: str = "proposed"


class PopulationOut(BaseModel):
    id: int
    project_id: int
    target_population: str
    accessible_population: str | None
    unit_of_analysis: str | None
    inclusion_criteria: str | None
    exclusion_criteria: str | None
    approval_status: str

    model_config = {"from_attributes": True}


class SamplingCreate(BaseModel):
    sampling_frame: str | None = None
    sampling_method: str | None = None
    sample_size: int | None = None
    sample_size_rationale: str | None = None
    recruitment_method: str | None = None
    response_rate_strategy: str | None = None
    non_response_considerations: str | None = None
    assumptions: str | None = None
    approval_status: str = "proposed"


class SamplingOut(BaseModel):
    id: int
    project_id: int
    sampling_frame: str | None
    sampling_method: str | None
    sample_size: int | None
    sample_size_rationale: str | None
    recruitment_method: str | None
    response_rate_strategy: str | None
    non_response_considerations: str | None
    assumptions: str | None
    approval_status: str

    model_config = {"from_attributes": True}


class InstrumentItemCreate(BaseModel):
    item_text: str
    response_type: str = "likert"
    response_options: str | None = None
    construct_name: str | None = None
    variable_name: str | None = None
    linked_objective: str | None = None
    linked_question: str | None = None
    planned_analysis: str | None = None
    sort_order: int = 0


class InstrumentSectionCreate(BaseModel):
    title: str
    instructions: str | None = None
    sort_order: int = 0
    items: list[InstrumentItemCreate] = []


class InstrumentCreate(BaseModel):
    name: str
    instrument_type: str = "questionnaire"
    description: str | None = None
    is_established_scale: bool = False
    validation_notes: str | None = None
    licensing_notes: str | None = None
    sections: list[InstrumentSectionCreate] = []
    approval_status: str = "proposed"


class InstrumentItemOut(BaseModel):
    id: int
    item_text: str
    response_type: str
    response_options: str | None
    construct_name: str | None
    variable_name: str | None
    linked_objective: str | None
    linked_question: str | None
    planned_analysis: str | None
    sort_order: int
    approval_status: str

    model_config = {"from_attributes": True}


class InstrumentSectionOut(BaseModel):
    id: int
    title: str
    instructions: str | None
    sort_order: int
    items: list[InstrumentItemOut] = []

    model_config = {"from_attributes": True}


class InstrumentOut(BaseModel):
    id: int
    project_id: int
    name: str
    instrument_type: str
    description: str | None
    is_established_scale: bool
    validation_notes: str | None
    licensing_notes: str | None
    approval_status: str
    sections: list[InstrumentSectionOut] = []

    model_config = {"from_attributes": True}


class AnalysisMappingCreate(BaseModel):
    question_id: int | None = None
    hypothesis_id: int | None = None
    variables: str | None = None
    data_type: str | None = None
    descriptive_stats: str | None = None
    statistical_test: str | None = None
    test_assumptions: str | None = None
    effect_size: str | None = None
    planned_table_or_figure: str | None = None
    notes: str | None = None


class AnalysisPlanCreate(BaseModel):
    title: str = "Primary analysis plan"
    software: str | None = None
    significance_level: str | None = "0.05"
    missing_data_strategy: str | None = None
    notes: str | None = None
    mappings: list[AnalysisMappingCreate] = []


class AnalysisMappingOut(BaseModel):
    id: int
    question_id: int | None
    hypothesis_id: int | None
    variables: str | None
    data_type: str | None
    descriptive_stats: str | None
    statistical_test: str | None
    test_assumptions: str | None
    effect_size: str | None
    planned_table_or_figure: str | None
    notes: str | None
    approval_status: str

    model_config = {"from_attributes": True}


class AnalysisPlanOut(BaseModel):
    id: int
    project_id: int
    title: str
    software: str | None
    significance_level: str | None
    missing_data_strategy: str | None
    notes: str | None
    approval_status: str
    mappings: list[AnalysisMappingOut] = []

    model_config = {"from_attributes": True}


class AlignmentIssueOut(BaseModel):
    id: int
    project_id: int
    issue_type: str
    severity: str
    explanation: str
    affected_elements: str | None
    recommended_correction: str | None
    correction_options: str | None
    resolution_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AlignmentReportOut(BaseModel):
    project_id: int
    issues: list[AlignmentIssueOut]
    summary: dict[str, int]
    chain_status: dict[str, str]


class ApproveRequest(BaseModel):
    approval_status: str = "approved"
    notes: str | None = None
