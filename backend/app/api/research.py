"""Research structure entity routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user
from app.database import get_db
from app.models.research import (
    AnalysisMapping,
    AnalysisPlan,
    Hypothesis,
    Instrument,
    InstrumentItem,
    InstrumentSection,
    OperationalDefinition,
    Population,
    ResearchDesign,
    ResearchObjective,
    ResearchQuestion,
    SamplingPlan,
    Variable,
)
from app.models.user import User
from app.schemas.research import (
    AnalysisPlanCreate,
    AnalysisPlanOut,
    DesignCreate,
    DesignOut,
    HypothesisCreate,
    HypothesisOut,
    InstrumentCreate,
    InstrumentOut,
    ObjectiveCreate,
    ObjectiveOut,
    PopulationCreate,
    PopulationOut,
    QuestionCreate,
    QuestionOut,
    QuestionUpdate,
    SamplingCreate,
    SamplingOut,
    VariableCreate,
    VariableOut,
)
from app.services.access import get_project_for_user

router = APIRouter(prefix="/projects/{project_id}", tags=["research"])


# ---- Questions ----
@router.get("/questions", response_model=list[QuestionOut])
def list_questions(
    project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[QuestionOut]:
    get_project_for_user(db, project_id, user)
    rows = (
        db.query(ResearchQuestion)
        .filter(ResearchQuestion.project_id == project_id)
        .order_by(ResearchQuestion.sort_order, ResearchQuestion.id)
        .all()
    )
    return [QuestionOut.model_validate(r) for r in rows]


@router.post("/questions", response_model=QuestionOut)
def create_question(
    project_id: int,
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> QuestionOut:
    get_project_for_user(db, project_id, user)
    row = ResearchQuestion(project_id=project_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return QuestionOut.model_validate(row)


@router.patch("/questions/{question_id}", response_model=QuestionOut)
def update_question(
    project_id: int,
    question_id: int,
    payload: QuestionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> QuestionOut:
    get_project_for_user(db, project_id, user)
    row = db.get(ResearchQuestion, question_id)
    if not row or row.project_id != project_id:
        raise HTTPException(status_code=404, detail="Question not found")
    # Never silently change approved content without explicit status change
    data = payload.model_dump(exclude_unset=True)
    if row.approval_status == "approved" and "approval_status" not in data:
        if any(k in data for k in ("text", "question_type")):
            raise HTTPException(
                status_code=400,
                detail="Cannot modify approved question without setting a new approval_status (e.g. needs_revision).",
            )
    for k, v in data.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return QuestionOut.model_validate(row)


@router.delete("/questions/{question_id}")
def delete_question(
    project_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    get_project_for_user(db, project_id, user)
    row = db.get(ResearchQuestion, question_id)
    if not row or row.project_id != project_id:
        raise HTTPException(status_code=404, detail="Question not found")
    if row.approval_status == "approved":
        raise HTTPException(status_code=400, detail="Reject or supersede approved question before delete.")
    db.delete(row)
    db.commit()
    return {"ok": True}


# ---- Objectives ----
@router.get("/objectives", response_model=list[ObjectiveOut])
def list_objectives(
    project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[ObjectiveOut]:
    get_project_for_user(db, project_id, user)
    rows = db.query(ResearchObjective).filter(ResearchObjective.project_id == project_id).all()
    return [ObjectiveOut.model_validate(r) for r in rows]


@router.post("/objectives", response_model=ObjectiveOut)
def create_objective(
    project_id: int,
    payload: ObjectiveCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ObjectiveOut:
    get_project_for_user(db, project_id, user)
    row = ResearchObjective(project_id=project_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return ObjectiveOut.model_validate(row)


# ---- Hypotheses ----
@router.get("/hypotheses", response_model=list[HypothesisOut])
def list_hypotheses(
    project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[HypothesisOut]:
    get_project_for_user(db, project_id, user)
    rows = db.query(Hypothesis).filter(Hypothesis.project_id == project_id).all()
    return [HypothesisOut.model_validate(r) for r in rows]


@router.post("/hypotheses", response_model=HypothesisOut)
def create_hypothesis(
    project_id: int,
    payload: HypothesisCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> HypothesisOut:
    get_project_for_user(db, project_id, user)
    row = Hypothesis(project_id=project_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return HypothesisOut.model_validate(row)


# ---- Variables ----
@router.get("/variables", response_model=list[VariableOut])
def list_variables(
    project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[VariableOut]:
    get_project_for_user(db, project_id, user)
    rows = db.query(Variable).filter(Variable.project_id == project_id).all()
    return [VariableOut.model_validate(r) for r in rows]


@router.post("/variables", response_model=VariableOut)
def create_variable(
    project_id: int,
    payload: VariableCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> VariableOut:
    get_project_for_user(db, project_id, user)
    data = payload.model_dump()
    op_def = data.pop("operational_definition", None)
    method = data.pop("measurement_method", None)
    row = Variable(project_id=project_id, **data)
    db.add(row)
    db.flush()
    if op_def:
        db.add(
            OperationalDefinition(
                variable_id=row.id,
                definition=op_def,
                measurement_method=method,
            )
        )
    db.commit()
    db.refresh(row)
    return VariableOut.model_validate(row)


# ---- Design ----
@router.get("/designs", response_model=list[DesignOut])
def list_designs(
    project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[DesignOut]:
    get_project_for_user(db, project_id, user)
    rows = db.query(ResearchDesign).filter(ResearchDesign.project_id == project_id).all()
    return [DesignOut.model_validate(r) for r in rows]


@router.post("/designs", response_model=DesignOut)
def create_design(
    project_id: int,
    payload: DesignCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DesignOut:
    get_project_for_user(db, project_id, user)
    row = ResearchDesign(project_id=project_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return DesignOut.model_validate(row)


# ---- Population & sampling ----
@router.post("/populations", response_model=PopulationOut)
def create_population(
    project_id: int,
    payload: PopulationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PopulationOut:
    get_project_for_user(db, project_id, user)
    row = Population(project_id=project_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return PopulationOut.model_validate(row)


@router.get("/populations", response_model=list[PopulationOut])
def list_populations(
    project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[PopulationOut]:
    get_project_for_user(db, project_id, user)
    rows = db.query(Population).filter(Population.project_id == project_id).all()
    return [PopulationOut.model_validate(r) for r in rows]


@router.post("/sampling-plans", response_model=SamplingOut)
def create_sampling(
    project_id: int,
    payload: SamplingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SamplingOut:
    get_project_for_user(db, project_id, user)
    if payload.sample_size is not None and not payload.sample_size_rationale:
        raise HTTPException(
            status_code=400,
            detail="Sample size requires sample_size_rationale and explicit assumptions.",
        )
    row = SamplingPlan(project_id=project_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return SamplingOut.model_validate(row)


@router.get("/sampling-plans", response_model=list[SamplingOut])
def list_sampling(
    project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[SamplingOut]:
    get_project_for_user(db, project_id, user)
    rows = db.query(SamplingPlan).filter(SamplingPlan.project_id == project_id).all()
    return [SamplingOut.model_validate(r) for r in rows]


# ---- Instruments ----
@router.get("/instruments", response_model=list[InstrumentOut])
def list_instruments(
    project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[InstrumentOut]:
    get_project_for_user(db, project_id, user)
    rows = (
        db.query(Instrument)
        .options(
            joinedload(Instrument.sections).joinedload(InstrumentSection.items)
        )
        .filter(Instrument.project_id == project_id)
        .all()
    )
    return [InstrumentOut.model_validate(r) for r in rows]


@router.post("/instruments", response_model=InstrumentOut)
def create_instrument(
    project_id: int,
    payload: InstrumentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InstrumentOut:
    get_project_for_user(db, project_id, user)
    data = payload.model_dump()
    sections_data = data.pop("sections", [])
    inst = Instrument(project_id=project_id, **data)
    db.add(inst)
    db.flush()
    for s in sections_data:
        items = s.pop("items", [])
        section = InstrumentSection(instrument_id=inst.id, **s)
        db.add(section)
        db.flush()
        for item in items:
            db.add(InstrumentItem(section_id=section.id, **item))
    db.commit()
    row = (
        db.query(Instrument)
        .options(joinedload(Instrument.sections).joinedload(InstrumentSection.items))
        .filter(Instrument.id == inst.id)
        .first()
    )
    return InstrumentOut.model_validate(row)


# ---- Analysis plans ----
@router.get("/analysis-plans", response_model=list[AnalysisPlanOut])
def list_analysis_plans(
    project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[AnalysisPlanOut]:
    get_project_for_user(db, project_id, user)
    rows = (
        db.query(AnalysisPlan)
        .options(joinedload(AnalysisPlan.mappings))
        .filter(AnalysisPlan.project_id == project_id)
        .all()
    )
    return [AnalysisPlanOut.model_validate(r) for r in rows]


@router.post("/analysis-plans", response_model=AnalysisPlanOut)
def create_analysis_plan(
    project_id: int,
    payload: AnalysisPlanCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnalysisPlanOut:
    get_project_for_user(db, project_id, user)
    data = payload.model_dump()
    mappings = data.pop("mappings", [])
    plan = AnalysisPlan(project_id=project_id, **data)
    db.add(plan)
    db.flush()
    for m in mappings:
        db.add(AnalysisMapping(plan_id=plan.id, **m))
    db.commit()
    row = (
        db.query(AnalysisPlan)
        .options(joinedload(AnalysisPlan.mappings))
        .filter(AnalysisPlan.id == plan.id)
        .first()
    )
    return AnalysisPlanOut.model_validate(row)
