import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import type { StageDefinition } from "../types";
import {
  buildStageSnapshot,
  type StageProjectContext,
  type StageDataItem,
} from "../lib/stageSnapshot";
import { getStageGuide } from "../i18n/stageGuides";
import TranslateButton from "./TranslateButton";

type Props = {
  stage: StageDefinition;
  stages: StageDefinition[];
  status: string;
  ctx: StageProjectContext;
  labels: {
    title: string;
    inputs: string;
    process: string;
    outputs: string;
    next: string;
    status: string;
    completed: string;
    notCompleted: string;
    inProgress: string;
    notStarted: string;
    realData: string;
    empty: string;
    readiness: string;
    current: string;
    close: string;
    why: string;
    journey?: string;
    guideShort?: string;
  };
  statusLabel: (s: string) => string;
  onClose: () => void;
  onSelectStage?: (key: string) => void;
};

function DataCards({ items, empty }: { items: StageDataItem[]; empty: string }) {
  if (!items.length) {
    return <div className="sfd-empty">{empty}</div>;
  }
  return (
    <div className="sfd-data-grid">
      {items.map((it, i) => (
        <div key={i} className={`sfd-data-card${it.filled ? " is-filled" : " is-empty"}`}>
          <div className="sfd-data-card-top">
            <span className={`sfd-dot${it.filled ? " ok" : ""}`} />
            <span className="sfd-data-card-label">{it.label}</span>
          </div>
          <div className="sfd-data-card-value">{it.value}</div>
        </div>
      ))}
    </div>
  );
}

/** Full-screen visual stage map: Inputs → Process → Outputs + live project data. */
export default function StageFlowDiagram({
  stage,
  stages,
  status,
  ctx,
  labels,
  statusLabel,
  onClose,
  onSelectStage,
}: Props) {
  const snap = useMemo(
    () => buildStageSnapshot(stage.key, status, ctx),
    [stage.key, status, ctx]
  );
  const guide = getStageGuide(ctx.lang, stage.key);
  const title = ctx.lang === "ar" ? stage.label_ar : stage.label_en;
  const nextStage = stages.find((s) => s.key === snap.nextStageKey);
  const nextTitle = nextStage
    ? ctx.lang === "ar"
      ? nextStage.label_ar
      : nextStage.label_en
    : snap.nextStageKey;

  const [trGuide, setTrGuide] = useState<{
    inputs?: string;
    process?: string;
    outputs?: string;
    why?: string;
    nextNote?: string;
  }>({});
  const [showGuideDetail, setShowGuideDetail] = useState(false);

  const modalRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const previouslyFocused = document.activeElement as HTMLElement | null;
    modalRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "Tab") {
        const controls = modalRef.current?.querySelectorAll<HTMLElement>('button:not(:disabled), a[href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex="0"]');
        if (!controls?.length) { e.preventDefault(); return; }
        const first = controls[0], last = controls[controls.length - 1];
        if (e.shiftKey && (document.activeElement === first || document.activeElement === modalRef.current)) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && (document.activeElement === last || document.activeElement === modalRef.current)) { e.preventDefault(); first.focus(); }
      }
    };
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
      previouslyFocused?.focus();
    };
  }, [onClose]);

  const statusTone = snap.isComplete
    ? "complete"
    : status === "in_progress"
      ? "progress"
      : "idle";

  const statusText = snap.isComplete
    ? labels.completed
    : status === "in_progress"
      ? labels.inProgress
      : labels.notStarted;

  const pack = [
    snap.guideInputs,
    snap.guideProcessing,
    snap.guideOutputs,
    guide?.why || "",
    guide?.nextNote || "",
  ].join("\n\n---\n\n");

  const modal = (
    <div
      className="sfd-overlay"
      role="dialog"
      aria-modal="true"
      aria-label={labels.title}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="sfd-modal" ref={modalRef} tabIndex={-1}>
        {/* Top bar */}
        <header className="sfd-top">
          <div className="sfd-top-main">
            <div className="sfd-kicker">{labels.title}</div>
            <h2 className="sfd-heading">
              <span className="sfd-num">{stage.order}</span>
              <span>{title}</span>
            </h2>
            <p className="sfd-project">{ctx.project.working_title}</p>
          </div>
          <div className="sfd-top-side">
            <div className={`sfd-status-pill sfd-status-pill--${statusTone}`}>
              <span className="sfd-status-icon">
                {snap.isComplete ? "✓" : status === "in_progress" ? "●" : "○"}
              </span>
              {statusText}
            </div>
            {snap.isCurrent && (
              <span className="sfd-status-pill sfd-status-pill--current">{labels.current}</span>
            )}
            <button type="button" className="btn btn-primary sfd-close" onClick={onClose}>
              {labels.close}
            </button>
          </div>
        </header>

        {/* Readiness + journey */}
        <section className="sfd-metrics">
          <div className="sfd-metric-card">
            <div className="sfd-metric-label">{labels.status}</div>
            <div className="sfd-metric-value">{statusLabel(status)}</div>
            {snap.completedAt && (
              <div className="sfd-metric-sub">
                {new Date(snap.completedAt).toLocaleString()}
              </div>
            )}
          </div>
          <div className="sfd-metric-card sfd-metric-card--wide">
            <div className="sfd-metric-label">
              {labels.readiness}: <strong>{snap.readinessPercent}%</strong>
            </div>
            <div className="sfd-ring-track">
              <div
                className="sfd-ring-fill"
                style={{ width: `${snap.readinessPercent}%` }}
              />
            </div>
            <div className="sfd-metric-sub">
              {ctx.lang === "ar"
                ? "نسبة امتلاء بيانات هذه المرحلة من مشروعك"
                : "How much of this stage’s project data is filled"}
            </div>
          </div>
        </section>

        {/* Journey strip */}
        <section className="sfd-journey">
          <div className="sfd-journey-label">
            {labels.journey || (ctx.lang === "ar" ? "خريطة المراحل" : "Stage journey")}
          </div>
          <div className="sfd-journey-track">
            {stages.map((s, idx) => {
              const st =
                ctx.project.stage_progress?.find((p) => p.stage_key === s.key)?.status ||
                (ctx.project.current_stage === s.key ? "in_progress" : "not_started");
              const done = st === "completed";
              const cur = s.key === stage.key;
              const active = st === "in_progress";
              return (
                <button
                  key={s.key}
                  type="button"
                  className={`sfd-journey-node${done ? " is-done" : ""}${
                    active ? " is-active" : ""
                  }${cur ? " is-focus" : ""}`}
                  title={ctx.lang === "ar" ? s.label_ar : s.label_en}
                  onClick={() => onSelectStage?.(s.key)}
                >
                  <span className="sfd-journey-ord">{s.order}</span>
                  {idx < stages.length - 1 && <span className="sfd-journey-line" />}
                </button>
              );
            })}
          </div>
        </section>

        {/* Main visual pipeline */}
        <section className="sfd-pipeline">
          <article className="sfd-col sfd-col--in">
            <div className="sfd-col-badge">1</div>
            <div className="sfd-col-icon" aria-hidden>
              📥
            </div>
            <h3 className="sfd-col-title">{labels.inputs}</h3>
            {showGuideDetail && (
              <p className="sfd-col-guide">{trGuide.inputs || snap.guideInputs}</p>
            )}
            <div className="sfd-col-section-label">{labels.realData}</div>
            <DataCards items={snap.inputData} empty={labels.empty} />
          </article>

          <div className="sfd-connector" aria-hidden>
            <div className="sfd-connector-line" />
            <div className="sfd-connector-chevron">›</div>
          </div>

          <article className="sfd-col sfd-col--proc">
            <div className="sfd-col-badge">2</div>
            <div className="sfd-col-icon" aria-hidden>
              ⚙️
            </div>
            <h3 className="sfd-col-title">{labels.process}</h3>
            <div className="sfd-process-steps">
              {(trGuide.process || snap.guideProcessing || guide?.how || "")
                .split(/[.;]\s+/)
                .filter((x) => x.trim().length > 12)
                .slice(0, 4)
                .map((step, i) => (
                  <div key={i} className="sfd-process-step">
                    <span className="sfd-process-step-n">{i + 1}</span>
                    <span>{step.trim().replace(/\.$/, "")}</span>
                  </div>
                ))}
            </div>
            {showGuideDetail && (
              <p className="sfd-col-guide">{trGuide.process || guide?.how}</p>
            )}
          </article>

          <div className="sfd-connector" aria-hidden>
            <div className="sfd-connector-line" />
            <div className="sfd-connector-chevron">›</div>
          </div>

          <article className="sfd-col sfd-col--out">
            <div className="sfd-col-badge">3</div>
            <div className="sfd-col-icon" aria-hidden>
              📤
            </div>
            <h3 className="sfd-col-title">{labels.outputs}</h3>
            {showGuideDetail && (
              <p className="sfd-col-guide">{trGuide.outputs || snap.guideOutputs}</p>
            )}
            <div className="sfd-col-section-label">{labels.realData}</div>
            <DataCards items={snap.outputData} empty={labels.empty} />
          </article>
        </section>

        {/* Footer cards */}
        <section className="sfd-footer-grid">
          {snap.nextStageKey && (
            <div className="sfd-footer-card">
              <div className="sfd-footer-card-title">{labels.next}</div>
              <div className="sfd-next-pill">{nextTitle}</div>
              <p className="sfd-footer-card-text">
                {trGuide.nextNote || guide?.nextNote}
              </p>
            </div>
          )}
          {guide?.why && (
            <div className="sfd-footer-card sfd-footer-card--why">
              <div className="sfd-footer-card-title">{labels.why}</div>
              <p className="sfd-footer-card-text">{trGuide.why || guide.why}</p>
            </div>
          )}
        </section>

        <footer className="sfd-actions">
          <button
            type="button"
            className="btn"
            onClick={() => setShowGuideDetail((v) => !v)}
          >
            {showGuideDetail
              ? ctx.lang === "ar"
                ? "إخفاء الشرح الطويل"
                : "Hide long guide"
              : ctx.lang === "ar"
                ? "عرض الشرح الكامل"
                : "Show full guide text"}
          </button>
          <TranslateButton
            text={pack}
            onTranslated={(text) => {
              const parts = text.split(/\n\n---\n\n/);
              setTrGuide({
                inputs: parts[0],
                process: parts[1],
                outputs: parts[2],
                why: parts[3],
                nextNote: parts[4],
              });
              setShowGuideDetail(true);
            }}
          />
          <button type="button" className="btn btn-primary" onClick={onClose}>
            {labels.close}
          </button>
        </footer>
      </div>
    </div>
  );

  return createPortal(modal, document.body);
}
