import { FormEvent, useEffect, useState } from "react";
import { api } from "../api";
import type {
  AnalysisPlan,
  Design,
  Hypothesis,
  Instrument,
  Population,
  Question,
  SamplingPlan,
  Variable,
} from "../types";

type StructureTab =
  | "hypotheses"
  | "variables"
  | "design"
  | "population"
  | "instruments"
  | "analysis";

type Props = {
  token: string;
  projectId: number;
  questions: Question[];
  labels: Record<string, string>;
};

export default function StructurePanel({ token, projectId, questions, labels }: Props) {
  const [tab, setTab] = useState<StructureTab>("hypotheses");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [variables, setVariables] = useState<Variable[]>([]);
  const [designs, setDesigns] = useState<Design[]>([]);
  const [populations, setPopulations] = useState<Population[]>([]);
  const [sampling, setSampling] = useState<SamplingPlan[]>([]);
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [plans, setPlans] = useState<AnalysisPlan[]>([]);

  const [hForm, setHForm] = useState({
    null_hypothesis: "",
    alternative_hypothesis: "",
    direction: "non_directional",
    independent_variable: "",
    dependent_variable: "",
    theoretical_basis: "",
    proposed_test: "",
    question_id: "",
  });
  const [vForm, setVForm] = useState({
    name: "",
    role: "dependent",
    measurement_scale: "",
    operational_definition: "",
    measurement_method: "",
  });
  const [dForm, setDForm] = useState({
    design_type: "Cross-sectional survey",
    paradigm: "quantitative",
    rationale: "",
    strengths: "",
    limitations: "",
    bias_risks: "",
  });
  const [pForm, setPForm] = useState({
    target_population: "",
    accessible_population: "",
    unit_of_analysis: "",
    inclusion_criteria: "",
    exclusion_criteria: "",
  });
  const [sForm, setSForm] = useState({
    sampling_method: "",
    sample_size: "",
    sample_size_rationale: "",
    assumptions: "",
    recruitment_method: "",
  });
  const [iForm, setIForm] = useState({
    name: "Primary questionnaire",
    item_text: "",
    section_title: "Main section",
    response_type: "likert",
    construct_name: "",
    variable_name: "",
    linked_objective: "",
  });
  const [aForm, setAForm] = useState({
    question_id: "",
    statistical_test: "",
    variables: "",
    data_type: "",
    descriptive_stats: "",
    test_assumptions: "",
  });

  async function reload(which: StructureTab = tab) {
    setError(null);
    try {
      if (which === "hypotheses") setHypotheses(await api.listHypotheses(token, projectId));
      if (which === "variables") setVariables(await api.listVariables(token, projectId));
      if (which === "design") setDesigns(await api.listDesigns(token, projectId));
      if (which === "population") {
        setPopulations(await api.listPopulations(token, projectId));
        setSampling(await api.listSampling(token, projectId));
      }
      if (which === "instruments") setInstruments(await api.listInstruments(token, projectId));
      if (which === "analysis") setPlans(await api.listAnalysisPlans(token, projectId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Load failed");
    }
  }

  useEffect(() => {
    reload(tab);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, projectId, token]);

  async function submit(e: FormEvent, kind: StructureTab) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (kind === "hypotheses") {
        await api.createHypothesis(token, projectId, {
          ...hForm,
          question_id: hForm.question_id ? Number(hForm.question_id) : null,
        });
        setHForm({
          null_hypothesis: "",
          alternative_hypothesis: "",
          direction: "non_directional",
          independent_variable: "",
          dependent_variable: "",
          theoretical_basis: "",
          proposed_test: "",
          question_id: "",
        });
      } else if (kind === "variables") {
        await api.createVariable(token, projectId, vForm);
        setVForm({
          name: "",
          role: "dependent",
          measurement_scale: "",
          operational_definition: "",
          measurement_method: "",
        });
      } else if (kind === "design") {
        await api.createDesign(token, projectId, { ...dForm, is_primary: true });
      } else if (kind === "population") {
        // dual forms: population + optional sampling
        if (pForm.target_population.trim()) {
          await api.createPopulation(token, projectId, pForm);
          setPForm({
            target_population: "",
            accessible_population: "",
            unit_of_analysis: "",
            inclusion_criteria: "",
            exclusion_criteria: "",
          });
        }
        if (sForm.sampling_method || sForm.sample_size) {
          await api.createSampling(token, projectId, {
            sampling_method: sForm.sampling_method || null,
            sample_size: sForm.sample_size ? Number(sForm.sample_size) : null,
            sample_size_rationale: sForm.sample_size_rationale || null,
            assumptions: sForm.assumptions || null,
            recruitment_method: sForm.recruitment_method || null,
          });
          setSForm({
            sampling_method: "",
            sample_size: "",
            sample_size_rationale: "",
            assumptions: "",
            recruitment_method: "",
          });
        }
      } else if (kind === "instruments") {
        await api.createInstrument(token, projectId, {
          name: iForm.name,
          instrument_type: "questionnaire",
          sections: [
            {
              title: iForm.section_title,
              items: [
                {
                  item_text: iForm.item_text,
                  response_type: iForm.response_type,
                  construct_name: iForm.construct_name || null,
                  variable_name: iForm.variable_name || null,
                  linked_objective: iForm.linked_objective || null,
                },
              ],
            },
          ],
        });
        setIForm({ ...iForm, item_text: "", construct_name: "", variable_name: "", linked_objective: "" });
      } else if (kind === "analysis") {
        await api.createAnalysisPlan(token, projectId, {
          title: "Primary analysis plan",
          mappings: [
            {
              question_id: aForm.question_id ? Number(aForm.question_id) : null,
              statistical_test: aForm.statistical_test || null,
              variables: aForm.variables || null,
              data_type: aForm.data_type || null,
              descriptive_stats: aForm.descriptive_stats || null,
              test_assumptions: aForm.test_assumptions || null,
            },
          ],
        });
        setAForm({
          question_id: "",
          statistical_test: "",
          variables: "",
          data_type: "",
          descriptive_stats: "",
          test_assumptions: "",
        });
      }
      await reload(kind);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }

  const tabs: { key: StructureTab; label: string }[] = [
    { key: "hypotheses", label: labels.hypotheses },
    { key: "variables", label: labels.variables },
    { key: "design", label: labels.design },
    { key: "population", label: labels.population },
    { key: "instruments", label: labels.instruments },
    { key: "analysis", label: labels.analysis },
  ];

  return (
    <div className="stack">
      <p className="muted" style={{ fontSize: "0.85rem" }}>
        {labels.structureHint}
      </p>
      <div className="tabs">
        {tabs.map((t) => (
          <button
            key={t.key}
            type="button"
            className={`tab ${tab === t.key ? "active" : ""}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>
      {error && <div className="error">{error}</div>}

      {tab === "hypotheses" && (
        <div className="stack">
          {hypotheses.map((h) => (
            <div key={h.id} className="issue">
              <span className="badge">{h.approval_status}</span>{" "}
              <span className="badge">{h.direction}</span>
              <p>
                <strong>H0:</strong> {h.null_hypothesis}
              </p>
              <p>
                <strong>H1:</strong> {h.alternative_hypothesis}
              </p>
              <p className="muted" style={{ fontSize: "0.8rem" }}>
                IV: {h.independent_variable || "—"} · DV: {h.dependent_variable || "—"} · Q#
                {h.question_id ?? "—"}
              </p>
            </div>
          ))}
          <form className="stack" onSubmit={(e) => submit(e, "hypotheses")}>
            <div className="field">
              <label>{labels.h0}</label>
              <textarea
                required
                value={hForm.null_hypothesis}
                onChange={(e) => setHForm({ ...hForm, null_hypothesis: e.target.value })}
              />
            </div>
            <div className="field">
              <label>{labels.h1}</label>
              <textarea
                required
                value={hForm.alternative_hypothesis}
                onChange={(e) => setHForm({ ...hForm, alternative_hypothesis: e.target.value })}
              />
            </div>
            <div className="grid-2">
              <div className="field">
                <label>{labels.direction}</label>
                <select
                  value={hForm.direction}
                  onChange={(e) => setHForm({ ...hForm, direction: e.target.value })}
                >
                  <option value="non_directional">{labels.nonDirectional}</option>
                  <option value="directional">{labels.directional}</option>
                </select>
              </div>
              <div className="field">
                <label>{labels.linkQuestion}</label>
                <select
                  value={hForm.question_id}
                  onChange={(e) => setHForm({ ...hForm, question_id: e.target.value })}
                >
                  <option value="">—</option>
                  {questions.map((q) => (
                    <option key={q.id} value={q.id}>
                      #{q.id}: {q.text.slice(0, 50)}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="grid-2">
              <div className="field">
                <label>IV</label>
                <input
                  value={hForm.independent_variable}
                  onChange={(e) => setHForm({ ...hForm, independent_variable: e.target.value })}
                />
              </div>
              <div className="field">
                <label>DV</label>
                <input
                  value={hForm.dependent_variable}
                  onChange={(e) => setHForm({ ...hForm, dependent_variable: e.target.value })}
                />
              </div>
            </div>
            <div className="field">
              <label>{labels.theoreticalBasis}</label>
              <textarea
                value={hForm.theoretical_basis}
                onChange={(e) => setHForm({ ...hForm, theoretical_basis: e.target.value })}
              />
            </div>
            <div className="field">
              <label>{labels.proposedTest}</label>
              <input
                value={hForm.proposed_test}
                onChange={(e) => setHForm({ ...hForm, proposed_test: e.target.value })}
              />
            </div>
            <button className="btn btn-primary" type="submit" disabled={busy}>
              {labels.addHypothesis}
            </button>
          </form>
        </div>
      )}

      {tab === "variables" && (
        <div className="stack">
          {variables.map((v) => (
            <div key={v.id} className="issue">
              <span className="badge">{v.role}</span>{" "}
              <span className="badge">{v.approval_status}</span>
              <p>
                <strong>{v.name}</strong>
                {v.measurement_scale ? ` · ${v.measurement_scale}` : ""}
              </p>
            </div>
          ))}
          <form className="stack" onSubmit={(e) => submit(e, "variables")}>
            <div className="field">
              <label>{labels.varName}</label>
              <input
                required
                value={vForm.name}
                onChange={(e) => setVForm({ ...vForm, name: e.target.value })}
              />
            </div>
            <div className="grid-2">
              <div className="field">
                <label>{labels.varRole}</label>
                <select
                  value={vForm.role}
                  onChange={(e) => setVForm({ ...vForm, role: e.target.value })}
                >
                  <option value="independent">independent</option>
                  <option value="dependent">dependent</option>
                  <option value="control">control</option>
                  <option value="moderator">moderator</option>
                  <option value="mediator">mediator</option>
                  <option value="demographic">demographic</option>
                </select>
              </div>
              <div className="field">
                <label>{labels.scale}</label>
                <input
                  value={vForm.measurement_scale}
                  onChange={(e) => setVForm({ ...vForm, measurement_scale: e.target.value })}
                  placeholder="nominal / ordinal / interval / ratio"
                />
              </div>
            </div>
            <div className="field">
              <label>{labels.operationalDef}</label>
              <textarea
                value={vForm.operational_definition}
                onChange={(e) => setVForm({ ...vForm, operational_definition: e.target.value })}
              />
            </div>
            <div className="field">
              <label>{labels.measurementMethod}</label>
              <input
                value={vForm.measurement_method}
                onChange={(e) => setVForm({ ...vForm, measurement_method: e.target.value })}
              />
            </div>
            <button className="btn btn-primary" type="submit" disabled={busy}>
              {labels.addVariable}
            </button>
          </form>
        </div>
      )}

      {tab === "design" && (
        <div className="stack">
          {designs.map((d) => (
            <div key={d.id} className="issue">
              <span className="badge">{d.paradigm || "—"}</span>{" "}
              <span className="badge">{d.approval_status}</span>
              <p>
                <strong>{d.design_type}</strong>
              </p>
              {d.rationale && <p className="muted">{d.rationale}</p>}
              {d.limitations && (
                <p className="muted" style={{ fontSize: "0.85rem" }}>
                  {labels.limitations}: {d.limitations}
                </p>
              )}
            </div>
          ))}
          <form className="stack" onSubmit={(e) => submit(e, "design")}>
            <div className="grid-2">
              <div className="field">
                <label>{labels.designType}</label>
                <input
                  required
                  value={dForm.design_type}
                  onChange={(e) => setDForm({ ...dForm, design_type: e.target.value })}
                />
              </div>
              <div className="field">
                <label>{labels.paradigm}</label>
                <select
                  value={dForm.paradigm}
                  onChange={(e) => setDForm({ ...dForm, paradigm: e.target.value })}
                >
                  <option value="quantitative">quantitative</option>
                  <option value="qualitative">qualitative</option>
                  <option value="mixed">mixed</option>
                </select>
              </div>
            </div>
            <div className="field">
              <label>{labels.rationale}</label>
              <textarea
                value={dForm.rationale}
                onChange={(e) => setDForm({ ...dForm, rationale: e.target.value })}
              />
            </div>
            <div className="field">
              <label>{labels.strengths}</label>
              <textarea
                value={dForm.strengths}
                onChange={(e) => setDForm({ ...dForm, strengths: e.target.value })}
              />
            </div>
            <div className="field">
              <label>{labels.limitations}</label>
              <textarea
                value={dForm.limitations}
                onChange={(e) => setDForm({ ...dForm, limitations: e.target.value })}
              />
            </div>
            <div className="field">
              <label>{labels.biasRisks}</label>
              <textarea
                value={dForm.bias_risks}
                onChange={(e) => setDForm({ ...dForm, bias_risks: e.target.value })}
              />
            </div>
            <button className="btn btn-primary" type="submit" disabled={busy}>
              {labels.addDesign}
            </button>
          </form>
        </div>
      )}

      {tab === "population" && (
        <div className="stack">
          <h4>{labels.population}</h4>
          {populations.map((p) => (
            <div key={p.id} className="issue">
              <span className="badge">{p.approval_status}</span>
              <p>{p.target_population}</p>
              <p className="muted" style={{ fontSize: "0.85rem" }}>
                {p.unit_of_analysis || "—"} · {p.inclusion_criteria || ""}
              </p>
            </div>
          ))}
          <h4>{labels.sampling}</h4>
          {sampling.map((s) => (
            <div key={s.id} className="issue">
              <span className="badge">{s.approval_status}</span>
              <p>
                {s.sampling_method || "—"}
                {s.sample_size != null ? ` · n=${s.sample_size}` : ""}
              </p>
              {s.sample_size_rationale && (
                <p className="muted" style={{ fontSize: "0.85rem" }}>
                  {s.sample_size_rationale}
                </p>
              )}
            </div>
          ))}
          <form className="stack" onSubmit={(e) => submit(e, "population")}>
            <div className="field">
              <label>{labels.targetPop}</label>
              <textarea
                value={pForm.target_population}
                onChange={(e) => setPForm({ ...pForm, target_population: e.target.value })}
              />
            </div>
            <div className="field">
              <label>{labels.inclusion}</label>
              <textarea
                value={pForm.inclusion_criteria}
                onChange={(e) => setPForm({ ...pForm, inclusion_criteria: e.target.value })}
              />
            </div>
            <div className="field">
              <label>{labels.exclusion}</label>
              <textarea
                value={pForm.exclusion_criteria}
                onChange={(e) => setPForm({ ...pForm, exclusion_criteria: e.target.value })}
              />
            </div>
            <div className="field">
              <label>{labels.samplingMethod}</label>
              <input
                value={sForm.sampling_method}
                onChange={(e) => setSForm({ ...sForm, sampling_method: e.target.value })}
              />
            </div>
            <div className="grid-2">
              <div className="field">
                <label>{labels.sampleSize}</label>
                <input
                  type="number"
                  value={sForm.sample_size}
                  onChange={(e) => setSForm({ ...sForm, sample_size: e.target.value })}
                />
              </div>
              <div className="field">
                <label>{labels.sampleRationale}</label>
                <input
                  value={sForm.sample_size_rationale}
                  onChange={(e) => setSForm({ ...sForm, sample_size_rationale: e.target.value })}
                  placeholder={labels.sampleRationaleHint}
                />
              </div>
            </div>
            <div className="field">
              <label>{labels.assumptions}</label>
              <textarea
                value={sForm.assumptions}
                onChange={(e) => setSForm({ ...sForm, assumptions: e.target.value })}
              />
            </div>
            <button className="btn btn-primary" type="submit" disabled={busy}>
              {labels.savePopSampling}
            </button>
          </form>
        </div>
      )}

      {tab === "instruments" && (
        <div className="stack">
          {instruments.map((inst) => (
            <div key={inst.id} className="issue">
              <strong>{inst.name}</strong>{" "}
              <span className="badge">{inst.approval_status}</span>
              {inst.sections?.map((sec) => (
                <div key={sec.id} style={{ marginTop: 8 }}>
                  <div className="muted">{sec.title}</div>
                  <ul style={{ margin: "0.25rem 0", paddingInlineStart: "1.2rem" }}>
                    {sec.items?.map((it) => (
                      <li key={it.id}>
                        {it.item_text}
                        {it.construct_name ? (
                          <span className="muted"> · {it.construct_name}</span>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          ))}
          <form className="stack" onSubmit={(e) => submit(e, "instruments")}>
            <div className="field">
              <label>{labels.instrumentName}</label>
              <input
                value={iForm.name}
                onChange={(e) => setIForm({ ...iForm, name: e.target.value })}
              />
            </div>
            <div className="field">
              <label>{labels.itemText}</label>
              <textarea
                required
                value={iForm.item_text}
                onChange={(e) => setIForm({ ...iForm, item_text: e.target.value })}
              />
            </div>
            <div className="grid-2">
              <div className="field">
                <label>{labels.construct}</label>
                <input
                  value={iForm.construct_name}
                  onChange={(e) => setIForm({ ...iForm, construct_name: e.target.value })}
                />
              </div>
              <div className="field">
                <label>{labels.variable}</label>
                <input
                  value={iForm.variable_name}
                  onChange={(e) => setIForm({ ...iForm, variable_name: e.target.value })}
                />
              </div>
            </div>
            <button className="btn btn-primary" type="submit" disabled={busy}>
              {labels.addItem}
            </button>
          </form>
        </div>
      )}

      {tab === "analysis" && (
        <div className="stack">
          {plans.map((plan) => (
            <div key={plan.id} className="issue">
              <strong>{plan.title}</strong>{" "}
              <span className="badge">{plan.approval_status}</span>
              <table className="table" style={{ marginTop: 8 }}>
                <thead>
                  <tr>
                    <th>Q#</th>
                    <th>{labels.test}</th>
                    <th>{labels.variables}</th>
                  </tr>
                </thead>
                <tbody>
                  {plan.mappings?.map((m) => (
                    <tr key={m.id}>
                      <td>{m.question_id ?? "—"}</td>
                      <td>{m.statistical_test || "—"}</td>
                      <td>{m.variables || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
          <form className="stack" onSubmit={(e) => submit(e, "analysis")}>
            <div className="field">
              <label>{labels.linkQuestion}</label>
              <select
                value={aForm.question_id}
                onChange={(e) => setAForm({ ...aForm, question_id: e.target.value })}
              >
                <option value="">—</option>
                {questions.map((q) => (
                  <option key={q.id} value={q.id}>
                    #{q.id}: {q.text.slice(0, 50)}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>{labels.test}</label>
              <input
                value={aForm.statistical_test}
                onChange={(e) => setAForm({ ...aForm, statistical_test: e.target.value })}
              />
            </div>
            <div className="field">
              <label>{labels.variables}</label>
              <input
                value={aForm.variables}
                onChange={(e) => setAForm({ ...aForm, variables: e.target.value })}
              />
            </div>
            <div className="field">
              <label>{labels.descriptive}</label>
              <input
                value={aForm.descriptive_stats}
                onChange={(e) => setAForm({ ...aForm, descriptive_stats: e.target.value })}
              />
            </div>
            <div className="field">
              <label>{labels.assumptions}</label>
              <textarea
                value={aForm.test_assumptions}
                onChange={(e) => setAForm({ ...aForm, test_assumptions: e.target.value })}
              />
            </div>
            <button className="btn btn-primary" type="submit" disabled={busy}>
              {labels.addAnalysis}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
