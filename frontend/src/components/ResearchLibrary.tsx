import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type {
  PaperComparison,
  SourceDocumentDetail,
  SourceDocumentSummary,
  StageDefinition,
  WriteSectionGuide,
} from "../types";

type Props = {
  token: string;
  projectId: number;
  stages: StageDefinition[];
  labels: Record<string, string>;
  uiLang: "en" | "ar";
  /** Full dedicated page uses more width/height than the workspace side panel. */
  variant?: "embedded" | "page";
};

const DOC_TYPES = [
  "research_proposal",
  "research_protocol",
  "journal_article",
  "masters_thesis",
  "doctoral_dissertation",
  "conference_paper",
  "systematic_review",
  "scoping_review",
  "meta_analysis",
  "bachelors_research_project",
  "case_study",
  "other",
];

export default function ResearchLibrary({
  token,
  projectId,
  stages,
  labels,
  uiLang,
  variant = "embedded",
}: Props) {
  const [docs, setDocs] = useState<SourceDocumentSummary[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<SourceDocumentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [filterType, setFilterType] = useState("");
  const [search, setSearch] = useState("");
  const [selectedStage, setSelectedStage] = useState<string | null>(null);
  const [compareIds, setCompareIds] = useState<number[]>([]);
  const [comparison, setComparison] = useState<PaperComparison | null>(null);
  const [view, setView] = useState<"list" | "detail" | "compare">("list");
  const [confirmType, setConfirmType] = useState("");
  const [notes, setNotes] = useState("");
  const [showViewer, setShowViewer] = useState(false);
  const [viewerSectionId, setViewerSectionId] = useState<number | null>(null);
  const [writeGuide, setWriteGuide] = useState<WriteSectionGuide | null>(null);
  const [writeAnswers, setWriteAnswers] = useState<Record<string, string>>({});
  const [writeDraft, setWriteDraft] = useState<string | null>(null);
  const [writeBusy, setWriteBusy] = useState(false);
  const [translateBusy, setTranslateBusy] = useState(false);
  const [translateNote, setTranslateNote] = useState<string | null>(null);

  const loadList = useCallback(async () => {
    setError(null);
    try {
      const rows = await api.listLibrary(token, projectId);
      setDocs(rows);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Load failed");
    }
  }, [token, projectId]);

  useEffect(() => {
    loadList();
  }, [loadList]);

  // When UI language switches EN ↔ AR, re-load open analysis so lessons/summaries match.
  useEffect(() => {
    if (!selectedId) return;
    let cancelled = false;
    (async () => {
      try {
        const d = await api.getLibraryDoc(token, projectId, selectedId, uiLang);
        if (!cancelled) {
          setDetail(d);
          setConfirmType(d.document_type || "");
          setNotes(d.researcher_notes || "");
        }
      } catch {
        /* keep previous detail */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [uiLang, selectedId, token, projectId]);

  async function openDoc(id: number) {
    setBusy(true);
    setError(null);
    setTranslateNote(null);
    try {
      const d = await api.getLibraryDoc(token, projectId, id, uiLang);
      setDetail(d);
      setSelectedId(id);
      setConfirmType(d.document_type || "");
      setNotes(d.researcher_notes || "");
      setSelectedStage(null);
      setView("detail");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Load failed");
    } finally {
      setBusy(false);
    }
  }

  async function onUploadMany(fileList: FileList | File[] | null) {
    if (!fileList) return;
    const files = Array.from(fileList).filter(Boolean);
    if (!files.length) return;
    setBusy(true);
    setError(null);
    try {
      if (files.length === 1) {
        const d = await api.uploadLibraryDoc(token, projectId, files[0], uiLang);
        await loadList();
        setDetail(d);
        setSelectedId(d.id);
        setConfirmType(d.document_type || "");
        setNotes(d.researcher_notes || "");
        setCompareIds((prev) => Array.from(new Set([...prev, d.id])));
        setView("detail");
      } else {
        const result = await api.uploadLibraryMany(token, projectId, files, uiLang);
        await loadList();
        if (result.failed?.length) {
          setError(
            `${result.message} — ${result.failed.map((f) => `${f.filename}: ${f.error}`).join("; ")}`
          );
        }
        if (result.uploaded?.length) {
          const first = result.uploaded[0];
          setDetail(first);
          setSelectedId(first.id);
          setConfirmType(first.document_type || "");
          setNotes(first.researcher_notes || "");
          setCompareIds(result.uploaded.map((u) => u.id));
          setView(result.uploaded.length > 1 ? "list" : "detail");
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function reprocess() {
    if (!selectedId) return;
    setBusy(true);
    try {
      const d = await api.reprocessLibraryDoc(token, projectId, selectedId, uiLang);
      setDetail(d);
      await loadList();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Reprocess failed");
    } finally {
      setBusy(false);
    }
  }

  async function confirmClassification() {
    if (!selectedId) return;
    setBusy(true);
    try {
      const d = await api.confirmLibraryClassification(
        token,
        projectId,
        selectedId,
        { document_type: confirmType || undefined },
        uiLang
      );
      setDetail(d);
      await loadList();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Confirm failed");
    } finally {
      setBusy(false);
    }
  }

  async function saveNotes() {
    if (!selectedId) return;
    setBusy(true);
    try {
      const d = await api.updateLibraryNotes(token, projectId, selectedId, notes, uiLang);
      setDetail(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save notes failed");
    } finally {
      setBusy(false);
    }
  }

  async function verifyStage(mappingId: number, status: string) {
    if (!selectedId) return;
    try {
      await api.verifyLibraryStage(token, projectId, selectedId, mappingId, { status });
      await openDoc(selectedId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Verify failed");
    }
  }

  async function startWriteSection(stageKey: string) {
    if (!selectedId) return;
    setWriteBusy(true);
    setError(null);
    setWriteDraft(null);
    try {
      const res = await api.writeSectionGuide(token, projectId, selectedId, stageKey, uiLang);
      setWriteGuide(res.guide);
      const initial: Record<string, string> = {};
      for (const q of res.guide.questions_for_you || []) {
        initial[q.id] = q.hint || "";
      }
      setWriteAnswers(initial);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Guide failed");
    } finally {
      setWriteBusy(false);
    }
  }

  async function generateDraft() {
    if (!selectedId || !writeGuide) return;
    setWriteBusy(true);
    setError(null);
    try {
      const res = await api.writeSectionDraft(token, projectId, selectedId, {
        stage_key: writeGuide.stage_key,
        answers: writeAnswers,
        save_as_learning_note: true,
        language: uiLang,
      });
      setWriteDraft(res.draft);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Draft failed");
    } finally {
      setWriteBusy(false);
    }
  }

  // Authenticated file fetch for viewer (token via header, blob URL)
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  useEffect(() => {
    if (!selectedId || !showViewer || detail?.file_type !== "pdf") {
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
        setBlobUrl(null);
      }
      return;
    }
    let revoked = false;
    let url: string | null = null;
    (async () => {
      try {
        const res = await fetch(api.libraryFileUrl(projectId, selectedId), {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;
        const blob = await res.blob();
        url = URL.createObjectURL(blob);
        if (!revoked) setBlobUrl(url);
      } catch {
        /* ignore */
      }
    })();
    return () => {
      revoked = true;
      if (url) URL.revokeObjectURL(url);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId, showViewer, detail?.file_type, projectId, token]);

  function toggleCompare(id: number) {
    setCompareIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id].slice(0, 5)
    );
  }

  async function translateAnalysis(scope: "full" | "stage", stageKey?: string) {
    if (!selectedId) return;
    setTranslateBusy(true);
    setError(null);
    setTranslateNote(null);
    try {
      const res = await api.translateLibraryAnalysis(token, projectId, selectedId, {
        target_language: "ar",
        scope,
        stage_key: stageKey,
      });
      setDetail(res.document);
      setTranslateNote(
        res.message ||
          labels.translatedNote ||
          "Arabic translation applied for reading."
      );
      // Keep user on detail / current stage after translate
      if (scope === "stage" && stageKey) {
        setSelectedStage(stageKey);
      }
      setView("detail");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Translate failed");
    } finally {
      setTranslateBusy(false);
    }
  }

  async function runCompare() {
    if (compareIds.length < 2) {
      setError(labels.compareNeedTwo || "Select at least two papers");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const c = await api.compareLibraryDocs(
        token,
        projectId,
        {
          document_ids: compareIds,
          title: labels.comparison || "Paper comparison",
        },
        uiLang
      );
      setComparison(c);
      setView("compare");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Compare failed");
    } finally {
      setBusy(false);
    }
  }

  const filtered = useMemo(() => {
    return docs.filter((d) => {
      if (filterType && d.document_type !== filterType) return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          d.original_filename.toLowerCase().includes(q) ||
          (d.title_detected || "").toLowerCase().includes(q) ||
          (d.discipline || "").toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [docs, filterType, search]);

  const stageLabel = (key: string) => {
    const s = stages.find((x) => x.key === key);
    if (!s) return key;
    return uiLang === "ar" ? s.label_ar : s.label_en;
  };

  const statusClass = (status: string) => {
    if (status === "detected") return "ok";
    if (status === "partially_detected" || status === "requires_manual_review") return "warn";
    if (status === "not_applicable") return "";
    return "danger";
  };

  const statusLabel = (status: string) => {
    const map: Record<string, string | undefined> = {
      detected: labels.statusDetected,
      partially_detected: labels.statusPartial,
      not_detected: labels.statusNotDetected,
      not_applicable: labels.statusNotApplicable,
      requires_manual_review: labels.statusReview,
      completed: labels.statusCompleted,
      completed_with_warnings: labels.statusCompletedWarn,
      processing_failed: labels.statusFailed,
      waiting_for_processing: labels.statusWaiting,
      extracting_text: labels.statusExtracting,
      applying_ocr: labels.statusOcr,
      pending: labels.statusWaiting,
      failed: labels.statusFailed,
      not_needed: labels.statusNotApplicable,
      needed_but_unavailable: labels.statusOcr,
      success: labels.statusCompleted,
    };
    return map[status] || status.replaceAll("_", " ");
  };

  const selectedMapping = detail?.stage_mappings.find((m) => m.stage_key === selectedStage);

  return (
    <div className={`stack library-panel${variant === "page" ? " library-panel--page" : ""}`}>
      <div className="integrity-banner">
        {labels.integrityBanner}
      </div>

      <div className="tabs">
        <button
          type="button"
          className={`tab ${view === "list" ? "active" : ""}`}
          onClick={() => setView("list")}
        >
          {labels.library}
        </button>
        <button
          type="button"
          className={`tab ${view === "detail" ? "active" : ""}`}
          onClick={() => selectedId && setView("detail")}
          disabled={!selectedId}
        >
          {labels.paperDetail}
        </button>
        <button
          type="button"
          className={`tab ${view === "compare" ? "active" : ""}`}
          onClick={() => setView("compare")}
        >
          {labels.compare}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {view === "list" && (
        <div className="stack">
          <div className="issue" style={{ marginBottom: 0 }}>
            <h4 style={{ marginTop: 0 }}>{labels.studyTitle || "Study papers (learning library)"}</h4>
            <p className="muted" style={{ fontSize: "0.85rem", marginBottom: 0 }}>
              {labels.studyIntro ||
                "Upload research papers to read, summarize, and learn structure. This is not your project manuscript — it is a study reference shelf."}
            </p>
          </div>
          <div
            className="upload-drop"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              if (e.dataTransfer.files?.length) onUploadMany(e.dataTransfer.files);
            }}
          >
            <p>
              <strong>{labels.dropUploadMulti || labels.dropUpload}</strong>
            </p>
            <p className="muted" style={{ fontSize: "0.85rem" }}>
              PDF, DOCX, TXT, RTF — {labels.learningOnly}
            </p>
            <p className="muted" style={{ fontSize: "0.8rem" }}>
              {labels.multiHint || "You can select several files at once (up to 15)."}
            </p>
            <input
              type="file"
              accept=".pdf,.docx,.txt,.rtf"
              multiple
              disabled={busy}
              onChange={(e) => onUploadMany(e.target.files)}
            />
            {busy && (
              <p className="muted" style={{ marginTop: 8 }}>
                {labels.analyzing || "Analyzing document(s)… please wait."}
              </p>
            )}
          </div>

          <div className="grid-2">
            <div className="field">
              <label>{labels.search}</label>
              <input value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
            <div className="field">
              <label>{labels.filterType}</label>
              <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
                <option value="">{labels.allTypes}</option>
                {DOC_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t.replaceAll("_", " ")}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="suggestion-actions">
            <button
              type="button"
              className="btn btn-primary"
              disabled={busy || compareIds.length < 2}
              onClick={runCompare}
            >
              {labels.runCompare} ({compareIds.length})
            </button>
          </div>

          {filtered.length === 0 && <div className="empty">{labels.emptyLibrary}</div>}

          {filtered.map((d) => (
            <div key={d.id} className="issue library-card">
              <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                <input
                  type="checkbox"
                  checked={compareIds.includes(d.id)}
                  onChange={() => toggleCompare(d.id)}
                  title={labels.selectCompare}
                />
                <div style={{ flex: 1 }}>
                  <strong>{d.title_detected || d.original_filename}</strong>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 4 }}>
                    <span className="badge">{statusLabel(d.processing_status)}</span>
                    {d.document_type && (
                      <span className={`badge ${d.document_type_confirmed ? "ok" : "warn"}`}>
                        {d.document_type.replaceAll("_", " ")}
                        {d.document_type_confidence != null
                          ? ` (${Math.round(d.document_type_confidence * 100)}%)`
                          : ""}
                        {!d.document_type_confirmed ? ` — ${labels.unconfirmed}` : ""}
                      </span>
                    )}
                    {d.academic_level && <span className="badge">{d.academic_level}</span>}
                    {d.research_design && <span className="badge">{d.research_design}</span>}
                  </div>
                  <p className="muted" style={{ fontSize: "0.8rem", marginTop: 4 }}>
                    {d.original_filename} · {Math.round(d.file_size / 1024)} KB
                  </p>
                  <button type="button" className="btn" onClick={() => openDoc(d.id)} disabled={busy}>
                    {labels.openAnalysis}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {view === "detail" && detail && (
        <div className="stack">
          <button type="button" className="btn btn-ghost" onClick={() => setView("list")}>
            ← {labels.backToList}
          </button>

          <div className="issue">
            <h3 style={{ marginTop: 0 }}>{detail.title_detected || detail.original_filename}</h3>
            <p className="muted" style={{ fontSize: "0.85rem" }}>
              {detail.integrity_notice}
            </p>
            {detail.study_summary && (
              <div className="study-summary">
                <h4>{labels.studySummary || "What this paper is about (study view)"}</h4>
                <p className="muted" style={{ fontSize: "0.85rem" }}>
                  {detail.study_summary.purpose}
                </p>
                <div className="study-block">
                  <strong>{labels.mainIdeas || "Main ideas"}</strong>
                  <p>{detail.study_summary.main_ideas}</p>
                </div>
                <div className="study-block">
                  <strong>{labels.methods || "Methods"}</strong>
                  <p>{detail.study_summary.methods}</p>
                </div>
                <div className="study-block">
                  <strong>{labels.findings || "Findings / results"}</strong>
                  <p>{detail.study_summary.findings}</p>
                </div>
                <div className="study-block">
                  <strong>{labels.conclusions || "Conclusions"}</strong>
                  <p>{detail.study_summary.conclusions}</p>
                </div>
                {!!detail.study_summary.writing_style?.length && (
                  <div className="study-block">
                    <strong>{labels.writingStyle || "Writing style & voice"}</strong>
                    <ul>
                      {detail.study_summary.writing_style.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {!!detail.study_summary.structure_explanation?.length && (
                  <div className="study-block">
                    <strong>{labels.structureExplain || "How the paper is structured"}</strong>
                    <ul>
                      {detail.study_summary.structure_explanation.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {!!detail.study_summary.how_to_study?.length && (
                  <div className="study-block">
                    <strong>{labels.howToStudy || "How to study this paper"}</strong>
                    <ol>
                      {detail.study_summary.how_to_study.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ol>
                  </div>
                )}
                {detail.study_summary.integrity_note && (
                  <p className="muted" style={{ fontSize: "0.8rem" }}>
                    {detail.study_summary.integrity_note}
                  </p>
                )}
              </div>
            )}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
              <span className="badge">{statusLabel(detail.processing_status)}</span>
              <span className="badge">{statusLabel(detail.extraction_status)}</span>
              <span className="badge">{statusLabel(detail.ocr_status)}</span>
              {detail.detected_language && (
                <span className="badge">{detail.detected_language.toUpperCase()}</span>
              )}
              {(detail.learning_report as { ai_enrichment?: { ai_enriched?: boolean } } | null)
                ?.ai_enrichment?.ai_enriched && (
                <span className="badge ok">{labels.aiEnriched || "AI enriched"}</span>
              )}
            </div>
            <div className="suggestion-actions" style={{ marginTop: 8 }}>
              <button
                type="button"
                className="btn"
                onClick={() => setShowViewer((v) => !v)}
              >
                {showViewer
                  ? labels.hideViewer || "Hide source viewer"
                  : labels.showViewer || "Source viewer"}
              </button>
              <button
                type="button"
                className="btn btn-primary"
                disabled={busy || translateBusy}
                onClick={() => translateAnalysis("full")}
                title={labels.translatedNote}
              >
                {translateBusy
                  ? labels.translating || "Translating…"
                  : labels.translateToAr || "Translate analysis to Arabic"}
              </button>
            </div>
            {translateNote && (
              <p className="muted" style={{ fontSize: "0.82rem", marginTop: 8 }}>
                {translateNote}
              </p>
            )}
          </div>

          {showViewer && (
            <div className="issue source-viewer">
              <h4>{labels.sourceViewer || "Source viewer"}</h4>
              {detail.file_type === "pdf" && blobUrl ? (
                <iframe title="PDF" src={blobUrl} className="pdf-frame" />
              ) : (
                <div className="text-viewer">
                  <div className="tabs" style={{ marginBottom: 8 }}>
                    {(detail.sections || []).slice(0, 30).map((s) => (
                      <button
                        key={s.id}
                        type="button"
                        className={`tab ${viewerSectionId === s.id ? "active" : ""}`}
                        onClick={() => setViewerSectionId(s.id)}
                      >
                        {s.heading.slice(0, 28)}
                      </button>
                    ))}
                  </div>
                  <pre className="viewer-body">
                    {viewerSectionId
                      ? detail.sections.find((s) => s.id === viewerSectionId)?.content ||
                        labels.noSection ||
                        "—"
                      : detail.sections[0]?.content ||
                        detail.abstract_excerpt ||
                        labels.noText ||
                        "No extracted text"}
                  </pre>
                  <p className="muted" style={{ fontSize: "0.75rem" }}>
                    {labels.exactSourceNote ||
                      "Exact extracted text (not AI rewrite). Verify against the original file."}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Classification */}
          <div className="issue">
            <h4>{labels.classification}</h4>
            <p>
              <strong>{labels.detectedType}:</strong>{" "}
              {(detail.document_type || "—").replaceAll("_", " ")}
              {detail.document_type_confidence != null && (
                <span className="muted">
                  {" "}
                  · {labels.confidence}: {Math.round(detail.document_type_confidence * 100)}%
                </span>
              )}
            </p>
            {detail.document_type_evidence && (
              <p className="muted" style={{ fontSize: "0.85rem" }}>
                {labels.evidence}: {detail.document_type_evidence}
              </p>
            )}
            {!detail.document_type_confirmed && (
              <p className="muted" style={{ fontSize: "0.85rem" }}>
                {labels.confirmHint}
              </p>
            )}
            <div className="field">
              <label>{labels.confirmType}</label>
              <select value={confirmType} onChange={(e) => setConfirmType(e.target.value)}>
                <option value="">—</option>
                {DOC_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t.replaceAll("_", " ")}
                  </option>
                ))}
              </select>
            </div>
            <div className="suggestion-actions">
              <button type="button" className="btn btn-primary" onClick={confirmClassification} disabled={busy}>
                {labels.confirmClassification}
              </button>
              <button type="button" className="btn" onClick={reprocess} disabled={busy}>
                {labels.reprocess}
              </button>
            </div>
            <p>
              <strong>{labels.level}:</strong> {detail.academic_level || "—"} ·{" "}
              <strong>{labels.design}:</strong> {detail.research_design || "—"} ·{" "}
              <strong>{labels.paradigm}:</strong> {detail.methodology_paradigm || "—"}
            </p>
            {detail.abstract_excerpt && (
              <p style={{ fontSize: "0.9rem" }}>
                <strong>{labels.abstract}:</strong> {detail.abstract_excerpt}
              </p>
            )}
          </div>

          {detail.analysis_warnings?.length > 0 && (
            <div className="error">
              <strong>{labels.warnings}</strong>
              <ul>
                {detail.analysis_warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Structure map */}
          <div className="issue">
            <h4>{labels.structureMap}</h4>
            <p className="muted" style={{ fontSize: "0.8rem" }}>
              {labels.structureMapNote}
            </p>
            <div className="stage-map">
              {(detail.stage_mappings || []).map((m) => (
                <button
                  key={m.id}
                  type="button"
                  className={`stage-map-item ${selectedStage === m.stage_key ? "active" : ""}`}
                  onClick={() => setSelectedStage(m.stage_key)}
                >
                  <span className={`badge ${statusClass(m.status)}`}>
                    {statusLabel(m.status)}
                  </span>
                  <span>{stageLabel(m.stage_key)}</span>
                </button>
              ))}
            </div>
          </div>

          {selectedMapping && (
            <div className="issue">
              <h4>
                {stageLabel(selectedMapping.stage_key)} · {statusLabel(selectedMapping.status)}
              </h4>
              {selectedMapping.original_heading && (
                <p>
                  <strong>{labels.originalHeading}:</strong> {selectedMapping.original_heading}
                </p>
              )}
              {selectedMapping.extracted_excerpt && (
                <div>
                  <strong>{labels.exactSource}:</strong>
                  <pre className="suggestion-payload">{selectedMapping.extracted_excerpt}</pre>
                </div>
              )}
              {selectedMapping.ai_summary && (
                <p>
                  <strong>{labels.aiSummary}:</strong> {selectedMapping.ai_summary}
                </p>
              )}
              {selectedMapping.lessons_for_user && (
                <p>
                  <strong>{labels.lessons}:</strong> {selectedMapping.lessons_for_user}
                </p>
              )}
              {selectedMapping.writing_strategy && (
                <p className="muted" style={{ fontSize: "0.85rem" }}>
                  <strong>{labels.writingStrategy}:</strong> {selectedMapping.writing_strategy}
                </p>
              )}
              <p className="muted" style={{ fontSize: "0.8rem" }}>
                {labels.confidence}:{" "}
                {selectedMapping.confidence != null
                  ? `${Math.round(selectedMapping.confidence * 100)}%`
                  : "—"}{" "}
                · {labels.completeness}: {selectedMapping.completeness || "—"}
              </p>
              <div className="suggestion-actions">
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={busy || translateBusy}
                  onClick={() =>
                    translateAnalysis("stage", selectedMapping.stage_key)
                  }
                  title={labels.translatedNote}
                >
                  {translateBusy
                    ? labels.translating || "Translating…"
                    : labels.translateStageToAr || "Translate this stage to Arabic"}
                </button>
                <button
                  type="button"
                  className="btn"
                  onClick={() => verifyStage(selectedMapping.id, "detected")}
                >
                  {labels.markVerified}
                </button>
                <button
                  type="button"
                  className="btn"
                  onClick={() => verifyStage(selectedMapping.id, "requires_manual_review")}
                >
                  {labels.needsReview}
                </button>
                <button
                  type="button"
                  className="btn"
                  onClick={() => verifyStage(selectedMapping.id, "not_applicable")}
                >
                  {labels.notApplicable}
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={writeBusy}
                  onClick={() => startWriteSection(selectedMapping.stage_key)}
                >
                  {labels.writeMySection || "Write my section"}
                </button>
              </div>
            </div>
          )}

          {writeGuide && (
            <div className="issue write-wizard">
              <h4>
                {labels.writeMySection || "Write my section"}: {writeGuide.stage_label}
              </h4>
              <p className="muted" style={{ fontSize: "0.85rem" }}>
                {writeGuide.purpose}
              </p>
              <div className="integrity-banner" style={{ marginBottom: 8 }}>
                {(writeGuide.integrity_rules || []).join(" · ")}
              </div>
              <p>
                <strong>{labels.refApproach || "How the reference paper approached it"}:</strong>{" "}
                {writeGuide.reference?.summary}
              </p>
              {writeGuide.reference?.short_excerpt_for_illustration_only && (
                <div>
                  <strong>{labels.illustrationOnly || "Short excerpt (illustration only)"}:</strong>
                  <pre className="suggestion-payload">
                    {writeGuide.reference.short_excerpt_for_illustration_only}
                  </pre>
                </div>
              )}
              <h4 style={{ fontSize: "0.95rem" }}>{labels.outline || "Outline template"}</h4>
              <ol style={{ fontSize: "0.9rem" }}>
                {(writeGuide.outline_template || []).map((b, i) => (
                  <li key={i}>{b}</li>
                ))}
              </ol>
              <h4 style={{ fontSize: "0.95rem" }}>
                {labels.yourAnswers || "Your answers (required for an original draft)"}
              </h4>
              {(writeGuide.questions_for_you || []).map((q) => (
                <div className="field" key={q.id}>
                  <label>{q.prompt}</label>
                  <textarea
                    value={writeAnswers[q.id] || ""}
                    onChange={(e) =>
                      setWriteAnswers((a) => ({ ...a, [q.id]: e.target.value }))
                    }
                    rows={2}
                    placeholder={q.hint || ""}
                  />
                </div>
              ))}
              <div className="suggestion-actions">
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={writeBusy}
                  onClick={generateDraft}
                >
                  {writeBusy
                    ? labels.generating || "Generating…"
                    : labels.generateDraft || "Generate original draft"}
                </button>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => {
                    setWriteGuide(null);
                    setWriteDraft(null);
                  }}
                >
                  {labels.close || "Close"}
                </button>
              </div>
              {writeDraft && (
                <div style={{ marginTop: 10 }}>
                  <strong>{labels.draft || "Draft"}</strong>
                  <textarea
                    readOnly
                    value={writeDraft}
                    rows={14}
                    style={{ width: "100%", marginTop: 6, font: "inherit" }}
                  />
                  <p className="muted" style={{ fontSize: "0.8rem" }}>
                    {labels.draftSaved ||
                      "Saved as a learning note on your project (not auto-inserted into approved structure). Review, revise, and cite."}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Learning report snapshot */}
          {detail.learning_report && (
            <div className="issue">
              <h4>{labels.learningReport}</h4>
              <p className="muted" style={{ fontSize: "0.85rem" }}>
                {(detail.learning_report as { integrity_preamble?: string }).integrity_preamble}
              </p>
              {(detail.learning_report as { writing_patterns?: Record<string, string> })
                .writing_patterns && (
                <ul style={{ fontSize: "0.9rem" }}>
                  {Object.entries(
                    (detail.learning_report as { writing_patterns: Record<string, string> })
                      .writing_patterns
                  ).map(([k, v]) => (
                    <li key={k}>
                      <strong>{k}:</strong> {v}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {detail.quality_analysis && (
            <div className="issue">
              <h4>{labels.qualityAnalysis}</h4>
              <p className="muted" style={{ fontSize: "0.85rem" }}>
                {(detail.quality_analysis as { educational_note?: string }).educational_note}
              </p>
              {((detail.quality_analysis as { issues?: Array<{ issue: string; lesson: string }> })
                .issues || []
              ).map((iss, i) => (
                <div key={i} className="issue warning" style={{ marginTop: 6 }}>
                  <strong>{iss.issue}</strong>
                  <p className="muted">{iss.lesson}</p>
                </div>
              ))}
            </div>
          )}

          {/* Sections */}
          <div className="issue">
            <h4>{labels.sections} ({detail.sections?.length || 0})</h4>
            <div style={{ maxHeight: 220, overflow: "auto" }}>
              {(detail.sections || []).slice(0, 20).map((s) => (
                <div key={s.id} style={{ marginBottom: 8 }}>
                  <strong>{s.heading}</strong>
                  <p className="muted" style={{ fontSize: "0.8rem" }}>
                    {s.summary || s.content.slice(0, 200)}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div className="field">
            <label>{labels.yourNotes}</label>
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} />
            <button type="button" className="btn" onClick={saveNotes} disabled={busy}>
              {labels.saveNotes}
            </button>
          </div>
        </div>
      )}

      {view === "compare" && (
        <div className="stack">
          {!comparison && (
            <p className="muted">{labels.compareHint}</p>
          )}
          {comparison && (
            <>
              <h3>{comparison.title}</h3>
              {comparison.summary && (
                <div className="issue">
                  <p className="muted" style={{ fontSize: "0.85rem" }}>
                    {(comparison.summary as { integrity_note?: string }).integrity_note}
                  </p>
                  <ul>
                    {((comparison.summary as { common_patterns?: string[] }).common_patterns ||
                      []
                    ).map((p, i) => (
                      <li key={i}>{p}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div style={{ overflowX: "auto" }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>{labels.element}</th>
                      {comparison.document_ids.map((id) => {
                        const d = docs.find((x) => x.id === id);
                        return (
                          <th key={id}>{d?.title_detected || d?.original_filename || id}</th>
                        );
                      })}
                      <th>{labels.lessons}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparison.items.map((item) => (
                      <tr key={item.id}>
                        <td>{item.element_key.replaceAll("_", " ")}</td>
                        {comparison.document_ids.map((id) => (
                          <td key={id} style={{ fontSize: "0.8rem", maxWidth: 160 }}>
                            {(item.values[String(id)] || "—").slice(0, 180)}
                          </td>
                        ))}
                        <td style={{ fontSize: "0.8rem" }}>{item.lessons}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
