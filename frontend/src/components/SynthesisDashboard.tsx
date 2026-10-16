import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { SynthesisDashboard as SynthesisData } from "../types";

type Props = {
  token: string;
  projectId: number;
  language: "en" | "ar";
  labels: Record<string, string>;
  onOpenLibrary?: () => void;
  onOpenBenchmark?: () => void;
};

export default function SynthesisDashboard({
  token,
  projectId,
  language,
  labels,
  onOpenLibrary,
  onOpenBenchmark,
}: Props) {
  const [data, setData] = useState<SynthesisData | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await api.runSynthesis(token, projectId, { language });
      setData(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  }, [token, projectId, language]);

  // Auto-load and re-run when UI language switches so analysis text matches EN/AR.
  useEffect(() => {
    load();
  }, [load]);

  const heatColor = (intensity: string) => {
    if (intensity === "high") return "heat-high";
    if (intensity === "medium") return "heat-mid";
    return "heat-low";
  };

  const story =
    data?.ai_synthesis &&
    typeof data.ai_synthesis.story_of_the_literature === "string"
      ? data.ai_synthesis.story_of_the_literature
      : null;

  return (
    <div className="stack synthesis-dash">
      <div className="syn-hero">
        <div>
          <div className="syn-kicker">{labels.kicker}</div>
          <h2 className="syn-title">{data?.headline || labels.title}</h2>
          <p className="muted syn-sub">{data?.message || labels.subtitle}</p>
        </div>
        <div className="syn-hero-actions">
          <button type="button" className="btn btn-primary" disabled={busy} onClick={load}>
            {busy ? labels.refreshing : labels.refresh}
          </button>
          {onOpenLibrary && (
            <button type="button" className="btn" onClick={onOpenLibrary}>
              {labels.uploadPapers}
            </button>
          )}
        </div>
      </div>

      <div className="integrity-banner">{data?.integrity_notice || labels.integrity}</div>

      {error && <div className="error">{error}</div>}

      {data?.status === "empty" && (
        <div className="syn-empty">
          <div className="syn-empty-icon">📚</div>
          <h3>{data.headline}</h3>
          <p className="muted">{data.message}</p>
          {onOpenLibrary && (
            <button type="button" className="btn btn-primary" onClick={onOpenLibrary}>
              {labels.uploadPapers}
            </button>
          )}
        </div>
      )}

      {data && data.status === "ok" && (
        <>
          {/* Quick stats */}
          <div className="syn-stats">
            <div className="syn-stat">
              <div className="syn-stat-n">{data.paper_count}</div>
              <div className="syn-stat-l">{labels.papers}</div>
            </div>
            <div className="syn-stat">
              <div className="syn-stat-n">{data.stats?.with_methods ?? "—"}</div>
              <div className="syn-stat-l">{labels.withMethods}</div>
            </div>
            <div className="syn-stat">
              <div className="syn-stat-n">{data.stats?.with_results ?? "—"}</div>
              <div className="syn-stat-l">{labels.withResults}</div>
            </div>
            {data.ai_enriched && (
              <div className="syn-stat syn-stat-ai">
                <div className="syn-stat-n">AI</div>
                <div className="syn-stat-l">{labels.aiOn}</div>
              </div>
            )}
          </div>

          {/* Insight cards */}
          <section>
            <h3 className="syn-section-title">{labels.insights}</h3>
            <div className="syn-cards">
              {(data.insight_cards || []).map((c) => (
                <div key={c.id} className={`syn-card priority-${c.priority || "medium"} kind-${c.kind || "default"}`}>
                  <div className="syn-card-kind">{c.kind}</div>
                  <h4>{c.title}</h4>
                  <p>{c.body}</p>
                </div>
              ))}
            </div>
          </section>

          {/* AI story */}
          {story && (
            <section className="syn-story">
              <h3 className="syn-section-title">{labels.story}</h3>
              <p>{story}</p>
            </section>
          )}

          {/* Theme cloud + methods */}
          <div className="syn-two-col">
            <section>
              <h3 className="syn-section-title">{labels.themes}</h3>
              <div className="theme-cloud">
                {(data.theme_cloud || []).map((th) => (
                  <span
                    key={th.term}
                    className="theme-chip"
                    style={{
                      fontSize: `${0.75 + (th.weight || 0.3) * 0.55}rem`,
                      opacity: 0.55 + (th.weight || 0.3) * 0.45,
                    }}
                    title={`${th.term}: ${th.count ?? ""}`}
                  >
                    {th.term}
                  </span>
                ))}
              </div>
            </section>
            <section>
              <h3 className="syn-section-title">{labels.methods}</h3>
              <div className="stack">
                {(data.method_patterns || []).slice(0, 6).map((m, i) => (
                  <div key={i} className="method-bar-row">
                    <div className="method-bar-label">
                      <span className="badge">{m.kind}</span> {m.name}
                    </div>
                    <div className="method-bar-track">
                      <span style={{ width: `${Math.round((m.share || 0) * 100)}%` }} />
                    </div>
                    <div className="muted" style={{ fontSize: "0.8rem" }}>
                      {m.count}/{data.paper_count}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>

          {/* Writing moves */}
          <section>
            <h3 className="syn-section-title">{labels.writingMoves}</h3>
            <div className="syn-moves">
              {(data.writing_moves || []).map((mv, i) => (
                <div key={i} className="syn-move">
                  <div className="syn-move-top">
                    <strong>{mv.move}</strong>
                    <span className="badge">
                      {mv.frequency}/{data.paper_count}
                    </span>
                  </div>
                  <p className="muted">{mv.tip}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Gap signals */}
          {!!data.gap_signals?.length && (
            <section>
              <h3 className="syn-section-title">{labels.gaps}</h3>
              <div className="syn-cards">
                {data.gap_signals.map((g, i) => (
                  <div key={i} className="syn-card kind-gap">
                    <h4>{g.title}</h4>
                    <p>{g.body}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Stage heatmap */}
          <section>
            <h3 className="syn-section-title">{labels.heatmap}</h3>
            <p className="muted" style={{ fontSize: "0.85rem" }}>
              {labels.heatmapHint}
            </p>
            <div className="heat-grid">
              {(data.stage_heatmap || []).map((h) => (
                <div
                  key={h.stage_key}
                  className={`heat-cell ${heatColor(h.intensity)}`}
                  title={h.lesson}
                >
                  <div className="heat-label">{h.label}</div>
                  <div className="heat-pct">{Math.round((h.coverage || 0) * 100)}%</div>
                </div>
              ))}
            </div>
          </section>

          {/* Comparison matrix */}
          <section>
            <h3 className="syn-section-title">{labels.matrix}</h3>
            <div style={{ overflowX: "auto" }}>
              <table className="table syn-matrix">
                <thead>
                  <tr>
                    <th>{labels.colPaper}</th>
                    <th>{labels.colType}</th>
                    <th>{labels.colDesign}</th>
                    <th>{labels.colIdeas}</th>
                    <th>{labels.colMethods}</th>
                    <th>{labels.colFindings}</th>
                    <th>{labels.colStages}</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.comparison_matrix || []).map((row) => (
                    <tr key={row.document_id}>
                      <td>
                        <strong>{row.title}</strong>
                      </td>
                      <td>{row.type}</td>
                      <td>{row.design}</td>
                      <td className="syn-clip">{row.main_ideas}</td>
                      <td className="syn-clip">{row.methods}</td>
                      <td className="syn-clip">{row.findings}</td>
                      <td>{row.stages_covered}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Learning path */}
          <section className="syn-path">
            <h3 className="syn-section-title">{labels.path}</h3>
            <ol>
              {(data.learning_path || []).map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ol>
            <div className="suggestion-actions">
              {onOpenLibrary && (
                <button type="button" className="btn" onClick={onOpenLibrary}>
                  {labels.openLibrary}
                </button>
              )}
              {onOpenBenchmark && (
                <button type="button" className="btn btn-primary" onClick={onOpenBenchmark}>
                  {labels.openBenchmark}
                </button>
              )}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
