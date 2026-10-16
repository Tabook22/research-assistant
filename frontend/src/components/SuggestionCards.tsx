import { useState } from "react";
import type { AISuggestion } from "../types";
import TranslateButton from "./TranslateButton";

type Props = {
  suggestions: AISuggestion[];
  busyId: number | null;
  onApply: (id: number, editedPayload?: Record<string, unknown>, markApproved?: boolean) => void;
  onReject: (id: number) => void;
  labels: {
    title: string;
    apply: string;
    applyApproved: string;
    reject: string;
    edit: string;
    hideEdit: string;
    empty: string;
    pending: string;
    rationale: string;
    translateToAr?: string;
  };
};

export default function SuggestionCards({
  suggestions,
  busyId,
  onApply,
  onReject,
  labels,
}: Props) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [translated, setTranslated] = useState<Record<number, { title?: string; body?: string }>>(
    {}
  );

  if (!suggestions.length) {
    return <p className="muted" style={{ fontSize: "0.85rem" }}>{labels.empty}</p>;
  }

  return (
    <div className="stack suggestion-list">
      <div className="suggestion-list-header">
        <strong>{labels.title}</strong>
        <span className="badge warn">{labels.pending}: {suggestions.length}</span>
      </div>
      {suggestions.map((s) => {
        const jsonText =
          drafts[s.id] ??
          JSON.stringify(s.payload ?? {}, null, 2);
        const isEditing = editingId === s.id;
        const busy = busyId === s.id;
        const body = s.rationale || s.content || "";
        const tr = translated[s.id];
        return (
          <div key={s.id} className="suggestion-card">
            <div className="suggestion-card-top">
              <span className="badge">{s.suggestion_type}</span>
              <span className="badge warn">{s.approval_status}</span>
            </div>
            <h4 className="suggestion-title">{tr?.title || s.title}</h4>
            {body && (
              <p className="muted" style={{ fontSize: "0.85rem" }}>
                <strong>{labels.rationale}:</strong> {tr?.body || body}
              </p>
            )}
            {(s.title || body) && (
              <TranslateButton
                text={[s.title, body].filter(Boolean).join("\n\n")}
                compact
                onTranslated={(text) => {
                  const parts = text.split(/\n\n+/);
                  setTranslated((prev) => ({
                    ...prev,
                    [s.id]: {
                      title: parts[0] || s.title,
                      body: parts.slice(1).join("\n\n") || parts[0] || body,
                    },
                  }));
                }}
              />
            )}
            {!isEditing && (
              <pre className="suggestion-payload">
                {JSON.stringify(s.payload ?? {}, null, 2)}
              </pre>
            )}
            {isEditing && (
              <textarea
                className="suggestion-edit"
                value={jsonText}
                onChange={(e) => setDrafts((d) => ({ ...d, [s.id]: e.target.value }))}
                rows={8}
              />
            )}
            <div className="suggestion-actions">
              <button
                type="button"
                className="btn"
                disabled={busy}
                onClick={() => setEditingId(isEditing ? null : s.id)}
              >
                {isEditing ? labels.hideEdit : labels.edit}
              </button>
              <button
                type="button"
                className="btn btn-primary"
                disabled={busy}
                onClick={() => {
                  let payload: Record<string, unknown> | undefined;
                  if (isEditing || drafts[s.id]) {
                    try {
                      payload = JSON.parse(drafts[s.id] ?? jsonText);
                    } catch {
                      alert("Invalid JSON in edited payload");
                      return;
                    }
                  }
                  onApply(s.id, payload, false);
                }}
              >
                {busy ? "…" : labels.apply}
              </button>
              <button
                type="button"
                className="btn"
                disabled={busy}
                onClick={() => {
                  let payload: Record<string, unknown> | undefined;
                  if (isEditing || drafts[s.id]) {
                    try {
                      payload = JSON.parse(drafts[s.id] ?? jsonText);
                    } catch {
                      alert("Invalid JSON in edited payload");
                      return;
                    }
                  }
                  onApply(s.id, payload, true);
                }}
              >
                {labels.applyApproved}
              </button>
              <button
                type="button"
                className="btn btn-ghost"
                disabled={busy}
                onClick={() => onReject(s.id)}
              >
                {labels.reject}
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
