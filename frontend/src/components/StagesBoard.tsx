import { useMemo, useState } from "react";
import { getStageGuide, stageGuideLabels, type StageGuide } from "../i18n/stageGuides";
import type { StageProjectContext } from "../lib/stageSnapshot";
import type { StageDefinition } from "../types";
import StageFlowDiagram from "./StageFlowDiagram";
import TranslateButton from "./TranslateButton";

type Props = {
  stages: StageDefinition[];
  stageStatus: Map<string, string>;
  currentStage: string;
  completionPercent: number;
  lang: "en" | "ar";
  /** Compact sidebar list vs full-page reading board */
  variant?: "sidebar" | "page";
  /** Live project data for diagrams (optional but recommended). */
  projectCtx?: StageProjectContext;
  labels: {
    markComplete: string;
    current: string;
    progress: string;
    stagesHint: string;
    setCurrent: string;
    showDiagram: string;
    hideDiagram: string;
    diagramTitle: string;
    flowInputs: string;
    flowProcess: string;
    flowOutputs: string;
    flowNext: string;
    flowStatus: string;
    flowCompleted: string;
    flowNotCompleted: string;
    flowInProgress: string;
    flowNotStarted: string;
    flowRealData: string;
    flowEmpty: string;
    flowReadiness: string;
    flowWhy: string;
    close: string;
  };
  statusLabel: (status: string) => string;
  onSetStage: (key: string) => void;
  onCompleteStage: (key: string) => void;
  openBar?: React.ReactNode;
};

function statusClass(status: string): string {
  if (status === "completed") return "ok";
  if (status === "in_progress" || status === "pending_approval") return "warn";
  if (status === "skipped") return "";
  return "";
}

/** Research stages list (sidebar) or full-page board with expandable guides. */
export default function StagesBoard({
  stages,
  stageStatus,
  currentStage,
  completionPercent,
  lang,
  variant = "sidebar",
  projectCtx,
  labels,
  statusLabel,
  onSetStage,
  onCompleteStage,
  openBar,
}: Props) {
  const [openKey, setOpenKey] = useState<string | null>(null);
  const [diagramKey, setDiagramKey] = useState<string | null>(null);
  const gLabels = useMemo(() => stageGuideLabels(lang), [lang]);
  const byKey = useMemo(() => {
    const m = new Map<string, StageDefinition>();
    for (const s of stages) m.set(s.key, s);
    return m;
  }, [stages]);

  function toggleGuide(key: string) {
    setOpenKey((prev) => (prev === key ? null : key));
  }

  const diagramLabels = {
    title: labels.diagramTitle,
    inputs: labels.flowInputs,
    process: labels.flowProcess,
    outputs: labels.flowOutputs,
    next: labels.flowNext,
    status: labels.flowStatus,
    completed: labels.flowCompleted,
    notCompleted: labels.flowNotCompleted,
    inProgress: labels.flowInProgress,
    notStarted: labels.flowNotStarted,
    realData: labels.flowRealData,
    empty: labels.flowEmpty,
    readiness: labels.flowReadiness,
    current: labels.current,
    close: labels.close,
    why: labels.flowWhy,
  };

  const diagramStage = diagramKey ? byKey.get(diagramKey) : null;
  const diagramStatus = diagramKey
    ? stageStatus.get(diagramKey) || "not_started"
    : "not_started";

  function stageTitle(s: StageDefinition) {
    return lang === "ar" ? s.label_ar : s.label_en;
  }

  function nextStageTitle(nextKey: string | null) {
    if (!nextKey) return gLabels.end;
    const s = byKey.get(nextKey);
    if (!s) return nextKey;
    return stageTitle(s);
  }

  const [guideTr, setGuideTr] = useState<Record<string, StageGuide>>({});

  function GuidePanel({ stageKey }: { stageKey: string }) {
    const base = getStageGuide(lang, stageKey);
    if (!base) return null;
    const guide = guideTr[stageKey] || base;
    const pack = [
      base.what,
      base.how,
      base.inputs,
      base.processing,
      base.outputs,
      base.nextNote,
      base.why,
    ].join("\n\n---\n\n");
    return (
      <div className="stage-guide" role="region" aria-label={gLabels.what}>
        <div style={{ marginBottom: 8 }}>
          <TranslateButton
            text={pack}
            compact
            onTranslated={(text) => {
              const parts = text.split(/\n\n---\n\n/);
              if (parts.length >= 7) {
                setGuideTr((prev) => ({
                  ...prev,
                  [stageKey]: {
                    ...base,
                    what: parts[0],
                    how: parts[1],
                    inputs: parts[2],
                    processing: parts[3],
                    outputs: parts[4],
                    nextNote: parts[5],
                    why: parts[6],
                  },
                }));
              } else {
                setGuideTr((prev) => ({
                  ...prev,
                  [stageKey]: { ...base, what: text },
                }));
              }
            }}
          />
        </div>
        <div className="stage-guide-block">
          <strong>{gLabels.what}</strong>
          <p>{guide.what}</p>
        </div>
        <div className="stage-guide-block">
          <strong>{gLabels.how}</strong>
          <p>{guide.how}</p>
        </div>
        <div className="stage-guide-block">
          <strong>{gLabels.inputs}</strong>
          <p>{guide.inputs}</p>
        </div>
        <div className="stage-guide-block">
          <strong>{gLabels.processing}</strong>
          <p>{guide.processing}</p>
        </div>
        <div className="stage-guide-block">
          <strong>{gLabels.outputs}</strong>
          <p>{guide.outputs}</p>
        </div>
        <div className="stage-guide-block stage-guide-next">
          <strong>{gLabels.next}</strong>
          <p>
            <span className="badge">{nextStageTitle(guide.nextStageKey)}</span>
          </p>
          <p className="muted" style={{ fontSize: "0.85rem", marginBottom: 0 }}>
            {guide.nextNote}
          </p>
        </div>
        <div className="stage-guide-block">
          <strong>{gLabels.why}</strong>
          <p>{guide.why}</p>
        </div>
        <p className="muted stage-guide-chain">
          {gLabels.chain}: {stageKey}
          {guide.nextStageKey ? ` → ${guide.nextStageKey}` : ""}
        </p>
      </div>
    );
  }

  if (variant === "page") {
    return (
      <div className="stack stages-board stages-board--page">
        {openBar}
        <div className="stages-board-hero">
          <div>
            <p className="muted" style={{ margin: "0 0 0.35rem", fontSize: "0.9rem" }}>
              {labels.stagesHint}
            </p>
            <p className="muted" style={{ margin: "0 0 0.5rem", fontSize: "0.82rem" }}>
              {gLabels.toggleHint}
            </p>
            <div className="progress-bar" title={`${completionPercent}%`}>
              <span style={{ width: `${completionPercent}%` }} />
            </div>
            <p className="muted" style={{ margin: "0.4rem 0 0", fontSize: "0.85rem" }}>
              {labels.progress}: {completionPercent}%
            </p>
          </div>
        </div>
        <div className="stages-grid">
          {stages.map((s) => {
            const status = stageStatus.get(s.key) || "not_started";
            const active = currentStage === s.key;
            const expanded = openKey === s.key;
            return (
              <article
                key={s.key}
                className={`stages-card issue${active ? " stages-card--active" : ""}${
                  expanded ? " stages-card--open" : ""
                }`}
              >
                <div className="stages-card-top">
                  <span className="stages-card-num">{s.order}</span>
                  <span className={`badge ${statusClass(status)}`}>{statusLabel(status)}</span>
                  {active && <span className="badge ok">{labels.current}</span>}
                </div>
                <button
                  type="button"
                  className="stages-card-title-btn"
                  onClick={() => toggleGuide(s.key)}
                  aria-expanded={expanded}
                >
                  <h3 className="stages-card-title">{stageTitle(s)}</h3>
                  <span className="stage-chevron" aria-hidden>
                    {expanded ? "▾" : "▸"}
                  </span>
                </button>
                <p className="muted stages-card-key">{s.key}</p>
                {expanded && <GuidePanel stageKey={s.key} />}
                <div className="suggestion-actions stages-card-actions">
                  {projectCtx && (
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={() => setDiagramKey(s.key)}
                    >
                      {labels.showDiagram}
                    </button>
                  )}
                  <button
                    type="button"
                    className="btn"
                    onClick={() => onSetStage(s.key)}
                    disabled={active}
                  >
                    {labels.setCurrent}
                  </button>
                  {status !== "completed" && (
                    <button
                      type="button"
                      className="btn"
                      onClick={() => onCompleteStage(s.key)}
                    >
                      {labels.markComplete}
                    </button>
                  )}
                </div>
              </article>
            );
          })}
        </div>
        {projectCtx && diagramStage && (
          <StageFlowDiagram
            stage={diagramStage}
            stages={stages}
            status={diagramStatus}
            ctx={projectCtx}
            labels={diagramLabels}
            statusLabel={statusLabel}
            onClose={() => setDiagramKey(null)}
            onSelectStage={(key) => setDiagramKey(key)}
          />
        )}
      </div>
    );
  }

  // Sidebar compact list with expandable guide under each label
  return (
    <div className="stack stages-board stages-board--sidebar">
      {openBar}
      <p className="muted" style={{ margin: 0, fontSize: "0.75rem" }}>
        {gLabels.toggleHint}
      </p>
      <div className="progress-bar">
        <span style={{ width: `${completionPercent}%` }} />
      </div>
      {stages.map((s) => {
        const status = stageStatus.get(s.key) || "not_started";
        const active = currentStage === s.key;
        const expanded = openKey === s.key;
        return (
          <div key={s.key} className={`stage-item-wrap${expanded ? " stage-item-wrap--open" : ""}`}>
            <div className={`stage-item-row${active ? " active" : ""}`}>
              <button
                type="button"
                className={`stage-item stage-item--label${active ? " active" : ""}`}
                onClick={() => toggleGuide(s.key)}
                aria-expanded={expanded}
                title={gLabels.toggleHint}
              >
                <span className="num">{s.order}.</span>
                <span className="stage-item-text">
                  <div className="stage-item-title-line">
                    <span>{stageTitle(s)}</span>
                    <span className="stage-chevron" aria-hidden>
                      {expanded ? "▾" : "▸"}
                    </span>
                  </div>
                  <div className="muted" style={{ fontSize: "0.75rem" }}>
                    {statusLabel(status)}
                  </div>
                </span>
              </button>
              <button
                type="button"
                className="btn stage-set-btn"
                onClick={() => onSetStage(s.key)}
                disabled={active}
                title={labels.setCurrent}
              >
                →
              </button>
            </div>
            {/* Always-visible diagram button (no need to expand first) */}
            {projectCtx && (
              <button
                type="button"
                className="btn btn-primary stage-diagram-btn"
                onClick={() => setDiagramKey(s.key)}
              >
                {labels.showDiagram}
              </button>
            )}
            {expanded && (
              <div className="stage-guide stage-guide--sidebar">
                <GuidePanel stageKey={s.key} />
                <div className="suggestion-actions" style={{ marginTop: 8 }}>
                  {!active && (
                    <button
                      type="button"
                      className="btn"
                      style={{ fontSize: "0.8rem" }}
                      onClick={() => onSetStage(s.key)}
                    >
                      {labels.setCurrent}
                    </button>
                  )}
                  {status !== "completed" && (
                    <button
                      type="button"
                      className="btn"
                      style={{ fontSize: "0.8rem" }}
                      onClick={() => onCompleteStage(s.key)}
                    >
                      {labels.markComplete}
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
      {projectCtx && diagramStage && (
        <StageFlowDiagram
          stage={diagramStage}
          stages={stages}
          status={diagramStatus}
          ctx={projectCtx}
          labels={diagramLabels}
          statusLabel={statusLabel}
          onClose={() => setDiagramKey(null)}
          onSelectStage={(key) => setDiagramKey(key)}
        />
      )}
    </div>
  );
}
