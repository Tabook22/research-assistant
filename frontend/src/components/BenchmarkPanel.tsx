import { useState } from "react";
import { api } from "../api";
import type { BenchmarkResult, SourceDocumentSummary } from "../types";

type Props = {
  token: string;
  projectId: number;
  language: "en" | "ar";
  libraryDocs: SourceDocumentSummary[];
  labels: Record<string, string>;
  onOpenLibrary?: () => void;
};

export default function BenchmarkPanel({
  token,
  projectId,
  language,
  libraryDocs,
  labels,
  onOpenLibrary,
}: Props) {
  const [result, setResult] = useState<BenchmarkResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<number[]>([]);
  const [useAll, setUseAll] = useState(true);

  function toggle(id: number) {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
    setUseAll(false);
  }

  async function run() {
    setBusy(true);
    setError(null);
    try {
      const ids = useAll || selected.length === 0 ? null : selected;
      const res = await api.runBenchmark(token, projectId, {
        document_ids: ids,
        language,
      });
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Benchmark failed");
    } finally {
      setBusy(false);
    }
  }

  const verdictClass = (v: string) => {
    if (v === "aligned") return "ok";
    if (v === "behind") return "danger";
    if (v === "ahead_or_unique") return "ok";
    if (v === "optional") return "";
    return "warn";
  };

  return (
    <div className="stack benchmark-panel">
      <div className="issue">
        <h3 style={{ marginTop: 0 }}>{labels.title}</h3>
        <p className="muted" style={{ fontSize: "0.9rem" }}>
          {labels.intro}
        </p>
        <div className="integrity-banner">{labels.integrity}</div>
      </div>

      {libraryDocs.length === 0 ? (
        <div className="empty">
          <p>{labels.needPapers}</p>
          {onOpenLibrary && (
            <button type="button" className="btn btn-primary" onClick={onOpenLibrary}>
              {labels.goLibrary}
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="issue">
            <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <input
                type="checkbox"
                checked={useAll}
                onChange={(e) => {
                  setUseAll(e.target.checked);
                  if (e.target.checked) setSelected([]);
                }}
              />
              {labels.useAll} ({libraryDocs.length})
            </label>
            {!useAll && (
              <div className="stack" style={{ marginTop: 8 }}>
                {libraryDocs.map((d) => (
                  <label
                    key={d.id}
                    style={{ display: "flex", gap: 8, alignItems: "flex-start", fontSize: "0.9rem" }}
                  >
                    <input
                      type="checkbox"
                      checked={selected.includes(d.id)}
                      onChange={() => toggle(d.id)}
                    />
                    <span>
                      {d.title_detected || d.original_filename}
                      <span className="muted"> · {d.document_type || "—"}</span>
                    </span>
                  </label>
                ))}
              </div>
            )}
            <button
              type="button"
              className="btn btn-primary"
              style={{ marginTop: 10 }}
              disabled={busy}
              onClick={run}
            >
              {busy ? labels.running : labels.run}
            </button>
          </div>
        </>
      )}

      {error && <div className="error">{error}</div>}

      {result && (
        <div className="stack">
          <div className="issue">
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
              <strong>{result.message}</strong>
              {result.overall_score != null && (
                <span className="badge ok">
                  {labels.score}: {result.overall_score}%
                </span>
              )}
              {result.ai_enriched && <span className="badge ok">{labels.aiEnriched}</span>}
            </div>
            {result.score_explanation && (
              <p className="muted" style={{ fontSize: "0.85rem" }}>
                {result.score_explanation}
              </p>
            )}
            <p className="muted" style={{ fontSize: "0.8rem" }}>
              {result.integrity_notice}
            </p>
          </div>

          {typeof result.ai_narrative?.executive_summary === "string" && (
            <div className="issue">
              <h4>{labels.aiSummary}</h4>
              <p style={{ fontSize: "0.95rem", lineHeight: 1.5 }}>
                {result.ai_narrative.executive_summary}
              </p>
            </div>
          )}

          {!!result.gaps?.length && (
            <div className="issue">
              <h4>{labels.gaps}</h4>
              <ul>
                {result.gaps.map((g, i) => (
                  <li key={i}>{g}</li>
                ))}
              </ul>
            </div>
          )}

          {!!result.strengths?.length && (
            <div className="issue">
              <h4>{labels.strengths}</h4>
              <ul>
                {result.strengths.map((g, i) => (
                  <li key={i}>{g}</li>
                ))}
              </ul>
            </div>
          )}

          {!!result.recommendations?.length && (
            <div className="issue">
              <h4>{labels.recommendations}</h4>
              <ol>
                {result.recommendations.map((g, i) => (
                  <li key={i}>{g}</li>
                ))}
              </ol>
            </div>
          )}

          {result.design_comparison?.notes?.length ? (
            <div className="issue">
              <h4>{labels.design}</h4>
              <ul>
                {result.design_comparison.notes.map((n, i) => (
                  <li key={i}>{n}</li>
                ))}
              </ul>
            </div>
          ) : null}

          <div className="issue">
            <h4>{labels.stageTable}</h4>
            <div style={{ overflowX: "auto" }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>{labels.stage}</th>
                    <th>{labels.yourProject}</th>
                    <th>{labels.inPapers}</th>
                    <th>{labels.verdict}</th>
                    <th>{labels.action}</th>
                  </tr>
                </thead>
                <tbody>
                  {(result.stage_benchmarks || []).map((row) => (
                    <tr key={row.stage_key}>
                      <td>
                        <strong>{row.label}</strong>
                        <div className="muted" style={{ fontSize: "0.75rem" }}>
                          {row.purpose}
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${row.user_status === "missing" ? "warn" : "ok"}`}>
                          {row.user_status}
                        </span>
                      </td>
                      <td>
                        {row.papers_detected}/{row.papers_total}
                      </td>
                      <td>
                        <span className={`badge ${verdictClass(row.verdict)}`}>
                          {row.verdict_label}
                        </span>
                      </td>
                      <td style={{ fontSize: "0.85rem", maxWidth: 220 }}>
                        {row.recommendation}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Expandable reference examples for behind stages */}
          {(result.stage_benchmarks || [])
            .filter((r) => r.verdict === "behind" && r.reference_examples?.length)
            .slice(0, 4)
            .map((row) => (
              <div key={`ex-${row.stage_key}`} className="issue">
                <h4>
                  {labels.examples}: {row.label}
                </h4>
                {row.reference_examples.map((ex, i) => (
                  <div key={i} style={{ marginBottom: 8, fontSize: "0.9rem" }}>
                    <strong>{ex.title}</strong>
                    {ex.heading && <span className="muted"> · {ex.heading}</span>}
                    {ex.summary && <p className="muted">{ex.summary}</p>}
                  </div>
                ))}
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
