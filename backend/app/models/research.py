"""Core research structure entities."""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class ResearchProblem(Base, TimestampMixin):
    __tablename__ = "research_problems"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    background: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[str | None] = mapped_column(Text)
    approval_status: Mapped[str] = mapped_column(String(50), default="proposed")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    project = relationship("ResearchProject", back_populates="problems")


class ResearchGap(Base, TimestampMixin):
    __tablename__ = "research_gaps"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    gap_type: Mapped[str] = mapped_column(String(50), default="literature")  # literature, methodological, population, etc.
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_basis: Mapped[str | None] = mapped_column(Text)
    approval_status: Mapped[str] = mapped_column(String(50), default="proposed")

    project = relationship("ResearchProject", back_populates="gaps")


class ResearchObjective(Base, TimestampMixin):
    __tablename__ = "research_objectives"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[int | None] = mapped_column(
        ForeignKey("research_questions.id", ondelete="SET NULL"), index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    objective_type: Mapped[str | None] = mapped_column(String(50))
    verb: Mapped[str | None] = mapped_column(String(50))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    approval_status: Mapped[str] = mapped_column(String(50), default="proposed")

    project = relationship("ResearchProject", back_populates="objectives")
    question = relationship("ResearchQuestion", back_populates="objectives", foreign_keys=[question_id])


class ResearchQuestion(Base, TimestampMixin):
    __tablename__ = "research_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), default="descriptive")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    approval_status: Mapped[str] = mapped_column(String(50), default="proposed")
    data_source: Mapped[str | None] = mapped_column(Text)
    proposed_analysis: Mapped[str | None] = mapped_column(Text)

    project = relationship("ResearchProject", back_populates="questions")
    objectives = relationship(
        "ResearchObjective",
        back_populates="question",
        foreign_keys="ResearchObjective.question_id",
    )
    hypotheses = relationship("Hypothesis", back_populates="question")


class Hypothesis(Base, TimestampMixin):
    __tablename__ = "hypotheses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[int | None] = mapped_column(
        ForeignKey("research_questions.id", ondelete="SET NULL"), index=True
    )
    null_hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    alternative_hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    direction: Mapped[str] = mapped_column(String(50), default="non_directional")  # directional | non_directional
    independent_variable: Mapped[str | None] = mapped_column(String(255))
    dependent_variable: Mapped[str | None] = mapped_column(String(255))
    population: Mapped[str | None] = mapped_column(Text)
    expected_direction: Mapped[str | None] = mapped_column(Text)
    proposed_test: Mapped[str | None] = mapped_column(String(255))
    theoretical_basis: Mapped[str | None] = mapped_column(Text)
    approval_status: Mapped[str] = mapped_column(String(50), default="proposed")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    project = relationship("ResearchProject", back_populates="hypotheses")
    question = relationship("ResearchQuestion", back_populates="hypotheses")


class Construct(Base, TimestampMixin):
    __tablename__ = "constructs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    conceptual_definition: Mapped[str | None] = mapped_column(Text)
    approval_status: Mapped[str] = mapped_column(String(50), default="proposed")

    project = relationship("ResearchProject", back_populates="constructs")
    variables = relationship("Variable", back_populates="construct")


class Variable(Base, TimestampMixin):
    __tablename__ = "variables"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    construct_id: Mapped[int | None] = mapped_column(
        ForeignKey("constructs.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="dependent")  # independent, dependent, control, etc.
    measurement_scale: Mapped[str | None] = mapped_column(String(50))
    data_source: Mapped[str | None] = mapped_column(Text)
    coding: Mapped[str | None] = mapped_column(Text)
    approval_status: Mapped[str] = mapped_column(String(50), default="proposed")

    project = relationship("ResearchProject", back_populates="variables")
    construct = relationship("Construct", back_populates="variables")
    operational_definitions = relationship(
        "OperationalDefinition", back_populates="variable", cascade="all, delete-orphan"
    )


class OperationalDefinition(Base, TimestampMixin):
    __tablename__ = "operational_definitions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    variable_id: Mapped[int] = mapped_column(
        ForeignKey("variables.id", ondelete="CASCADE"), index=True
    )
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    measurement_method: Mapped[str | None] = mapped_column(Text)
    instrument_name: Mapped[str | None] = mapped_column(String(255))
    time_of_measurement: Mapped[str | None] = mapped_column(String(255))
    approval_status: Mapped[str] = mapped_column(String(50), default="proposed")

    variable = relationship("Variable", back_populates="operational_definitions")


class ResearchDesign(Base, TimestampMixin):
    __tablename__ = "research_designs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    design_type: Mapped[str] = mapped_column(String(100), nullable=False)
    paradigm: Mapped[str | None] = mapped_column(String(50))  # quantitative, qualitative, mixed
    rationale: Mapped[str | None] = mapped_column(Text)
    strengths: Mapped[str | None] = mapped_column(Text)
    limitations: Mapped[str | None] = mapped_column(Text)
    bias_risks: Mapped[str | None] = mapped_column(Text)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)
    approval_status: Mapped[str] = mapped_column(String(50), default="proposed")

    project = relationship("ResearchProject", back_populates="designs")


class Population(Base, TimestampMixin):
    __tablename__ = "populations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    target_population: Mapped[str] = mapped_column(Text, nullable=False)
    accessible_population: Mapped[str | None] = mapped_column(Text)
    unit_of_analysis: Mapped[str | None] = mapped_column(String(255))
    inclusion_criteria: Mapped[str | None] = mapped_column(Text)
    exclusion_criteria: Mapped[str | None] = mapped_column(Text)
    approval_status: Mapped[str] = mapped_column(String(50), default="proposed")

    project = relationship("ResearchProject", back_populates="populations")


class SamplingPlan(Base, TimestampMixin):
    __tablename__ = "sampling_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    sampling_frame: Mapped[str | None] = mapped_column(Text)
    sampling_method: Mapped[str | None] = mapped_column(String(100))
    sample_size: Mapped[int | None] = mapped_column(Integer)
    sample_size_rationale: Mapped[str | None] = mapped_column(Text)
    recruitment_method: Mapped[str | None] = mapped_column(Text)
    response_rate_strategy: Mapped[str | None] = mapped_column(Text)
    non_response_considerations: Mapped[str | None] = mapped_column(Text)
    assumptions: Mapped[str | None] = mapped_column(Text)
    approval_status: Mapped[str] = mapped_column(String(50), default="proposed")

    project = relationship("ResearchProject", back_populates="sampling_plans")


class Instrument(Base, TimestampMixin):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    instrument_type: Mapped[str] = mapped_column(String(50), default="questionnaire")
    description: Mapped[str | None] = mapped_column(Text)
    is_established_scale: Mapped[bool] = mapped_column(Boolean, default=False)
    validation_notes: Mapped[str | None] = mapped_column(Text)
    licensing_notes: Mapped[str | None] = mapped_column(Text)
    approval_status: Mapped[str] = mapped_column(String(50), default="proposed")

    project = relationship("ResearchProject", back_populates="instruments")
    sections = relationship(
        "InstrumentSection", back_populates="instrument", cascade="all, delete-orphan"
    )


class InstrumentSection(Base, TimestampMixin):
    __tablename__ = "instrument_sections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instrument_id: Mapped[int] = mapped_column(
        ForeignKey("instruments.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    instrument = relationship("Instrument", back_populates="sections")
    items = relationship(
        "InstrumentItem", back_populates="section", cascade="all, delete-orphan"
    )


class InstrumentItem(Base, TimestampMixin):
    __tablename__ = "instrument_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(
        ForeignKey("instrument_sections.id", ondelete="CASCADE"), index=True
    )
    item_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_type: Mapped[str] = mapped_column(String(50), default="likert")
    response_options: Mapped[str | None] = mapped_column(Text)
    construct_name: Mapped[str | None] = mapped_column(String(255))
    variable_name: Mapped[str | None] = mapped_column(String(255))
    linked_objective: Mapped[str | None] = mapped_column(Text)
    linked_question: Mapped[str | None] = mapped_column(Text)
    planned_analysis: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    approval_status: Mapped[str] = mapped_column(String(50), default="proposed")

    section = relationship("InstrumentSection", back_populates="items")


class AnalysisPlan(Base, TimestampMixin):
    __tablename__ = "analysis_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), default="Primary analysis plan")
    software: Mapped[str | None] = mapped_column(String(100))
    significance_level: Mapped[str | None] = mapped_column(String(50), default="0.05")
    missing_data_strategy: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    approval_status: Mapped[str] = mapped_column(String(50), default="proposed")

    project = relationship("ResearchProject", back_populates="analysis_plans")
    mappings = relationship(
        "AnalysisMapping", back_populates="plan", cascade="all, delete-orphan"
    )


class AnalysisMapping(Base, TimestampMixin):
    __tablename__ = "analysis_mappings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_plans.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[int | None] = mapped_column(
        ForeignKey("research_questions.id", ondelete="SET NULL"), index=True
    )
    hypothesis_id: Mapped[int | None] = mapped_column(
        ForeignKey("hypotheses.id", ondelete="SET NULL"), index=True
    )
    variables: Mapped[str | None] = mapped_column(Text)
    data_type: Mapped[str | None] = mapped_column(String(100))
    descriptive_stats: Mapped[str | None] = mapped_column(Text)
    statistical_test: Mapped[str | None] = mapped_column(String(255))
    test_assumptions: Mapped[str | None] = mapped_column(Text)
    effect_size: Mapped[str | None] = mapped_column(String(100))
    planned_table_or_figure: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    approval_status: Mapped[str] = mapped_column(String(50), default="proposed")

    plan = relationship("AnalysisPlan", back_populates="mappings")
