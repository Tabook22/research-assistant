import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import BenchmarkPanel from "../components/BenchmarkPanel";
import LanguageSwitcher from "../components/LanguageSwitcher";
import PanelOpenBar from "../components/PanelOpenBar";
import ResearchLibrary from "../components/ResearchLibrary";
import StagesBoard from "../components/StagesBoard";
import StructurePanel from "../components/StructurePanel";
import SuggestionCards from "../components/SuggestionCards";
import SynthesisDashboard from "../components/SynthesisDashboard";
import TranslateButton from "../components/TranslateButton";
import VoiceTextField from "../components/VoiceTextField";
import { useI18n } from "../i18n/I18nContext";
import {
  COMMAND_KEYS,
  documentTypeLabel,
  type TranslationKey,
} from "../i18n/translations";
import { buildLibraryLabels } from "../lib/libraryLabels";
import {
  isPanelTab,
  isStandaloneSection,
  panelUrl,
  type PanelTab,
  type StandaloneSection,
} from "../lib/panelRoutes";
import type {
  AISuggestion,
  AlignmentReport,
  DocumentItem,
  LiteratureResult,
  Message,
  Objective,
  Profile,
  Project,
  Question,
  Reference,
  SourceDocumentSummary,
  StageDefinition,
} from "../types";
import {panelPermission} from '../access';

const PROFILE_FIELDS = [
  "refined_idea",
  "research_problem",
  "research_gap",
  "overall_aim",
  "existing_evidence",
  "key_concepts",
  "initial_search_terms",
  "expected_contribution",
  "ethics_requirements",
] as const;

const QUESTION_TYPES = [
  "descriptive",
  "comparative",
  "correlational",
  "predictive",
  "explanatory",
  "experimental_or_causal",
  "exploratory_qualitative",
  "mixed_methods",
] as const;

export default function WorkspacePage() {
  const { id, panel: panelParam } = useParams();
  const projectId = Number(id);
  const navigate = useNavigate();
  const { token, logout, user, can } = useAuth();
  const { t, lang, isRtl } = useI18n();
  const standaloneSection: StandaloneSection | null = isStandaloneSection(panelParam)
    ? panelParam
    : null;
  const isStandalone = Boolean(standaloneSection);
  const [project, setProject] = useState<Project | null>(null);
  const [stages, setStages] = useState<StageDefinition[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [tab, setTab] = useState<PanelTab>(() =>
    isPanelTab(panelParam) ? panelParam : "profile"
  );
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [chatBusy, setChatBusy] = useState(false);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [objectives, setObjectives] = useState<Objective[]>([]);
  const [alignment, setAlignment] = useState<AlignmentReport | null>(null);
  const [refs, setRefs] = useState<Reference[]>([]);
  const [searchQ, setSearchQ] = useState("");
  const [searchResults, setSearchResults] = useState<LiteratureResult[]>([]);
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [exportText, setExportText] = useState("");
  const [profileDraft, setProfileDraft] = useState<Partial<Profile>>({});
  const [newQ, setNewQ] = useState({ text: "", question_type: "descriptive", proposed_analysis: "" });
  const [newObj, setNewObj] = useState({ text: "", question_id: "", verb: "Examine" });
  const [suggestions, setSuggestions] = useState<AISuggestion[]>([]);
  const [busySuggestionId, setBusySuggestionId] = useState<number | null>(null);
  const [flash, setFlash] = useState<string | null>(null);
  const [libraryDocs, setLibraryDocs] = useState<SourceDocumentSummary[]>([]);
  /** Display-only Arabic translations for AI texts (message id / issue id → Arabic). */
  const [translatedTexts, setTranslatedTexts] = useState<Record<string, string>>({});
  const [showOriginal, setShowOriginal] = useState<Record<string, boolean>>({});
  const chatEnd = useRef<HTMLDivElement>(null);

  function displayText(key: string, original: string) {
    const tr = translatedTexts[key];
    if (tr && !showOriginal[key]) return tr;
    return original;
  }

  function setTranslation(key: string, translated: string) {
    setTranslatedTexts((prev) => ({ ...prev, [key]: translated }));
    setShowOriginal((prev) => ({ ...prev, [key]: false }));
  }

  const loadSuggestions = useCallback(async () => {
    if (!token || !projectId) return;
    try {
      setSuggestions(await api.listSuggestions(token, projectId));
    } catch {
      /* ignore */
    }
  }, [token, projectId]);

  const loadLibraryDocs = useCallback(async () => {
    if (!token || !projectId) return;
    try {
      setLibraryDocs(await api.listLibrary(token, projectId));
    } catch {
      /* ignore */
    }
  }, [token, projectId]);

  const loadCore = useCallback(async () => {
    if (!token || !projectId) return;
    const [p, st, conv] = await Promise.all([
      api.getProject(token, projectId),
      api.stages(token),
      can('workspace')?api.getConversation(token, projectId, lang):Promise.resolve({messages:[]}),
    ]);
    setProject(p);
    setStages(st);
    setMessages(conv.messages || []);
    setProfileDraft(p.profile || {});
    await loadSuggestions();
    await loadLibraryDocs();
  }, [token, projectId, loadSuggestions, loadLibraryDocs, lang, can]);

  useEffect(() => {
    loadCore().catch((e) => setError(e.message));
  }, [loadCore]);

  useEffect(() => {
    const log = chatEnd.current?.parentElement;
    if (log) log.scrollTop = messages.length > 1 ? log.scrollHeight : 0;
  }, [messages]);

  function statusLabel(status: string): string {
    const key = `status.${status}` as TranslationKey;
    try {
      return t(key);
    } catch {
      return status;
    }
  }

  function approvalLabel(status: string): string {
    const key = `approval.${status}` as TranslationKey;
    const translated = t(key);
    return translated === key ? status : translated;
  }

  function chainLabel(status: string): string {
    if (status === "present") return t("chain.present");
    if (status === "missing") return t("chain.missing");
    if (status === "partial") return t("chain.partial");
    if (status.startsWith("optional")) return t("chain.optional_missing");
    return status;
  }

  function severityLabel(sev: string): string {
    const key = `severity.${sev}` as TranslationKey;
    const translated = t(key);
    return translated === key ? sev : translated;
  }

  function qTypeLabel(type: string): string {
    const key = `qtype.${type}` as TranslationKey;
    const translated = t(key);
    return translated === key ? type : translated;
  }

  function cmdLabel(cmd: string): string {
    const key = `cmd.${cmd}` as TranslationKey;
    const translated = t(key);
    return translated === key ? cmd : translated;
  }

  async function refreshTab(next: PanelTab = tab) {
    if (!token) return;
    if (next === "questions" || next === "structure") {
      const [qs, os] = await Promise.all([
        api.listQuestions(token, projectId),
        api.listObjectives(token, projectId),
      ]);
      setQuestions(qs);
      setObjectives(os);
    }
    if (next === "suggestions") {
      await loadSuggestions();
    } else if (next === "benchmark" || next === "library") {
      await loadLibraryDocs();
    } else if (next === "literature") {
      setRefs(await api.listReferences(token, projectId));
    } else if (next === "documents") {
      setDocs(await api.listDocuments(token, projectId));
    }
  }

  // Load related project data so stage diagrams show real inputs/outputs
  useEffect(() => {
    if (!token || !projectId) return;
    void (async () => {
      try {
        const [qs, os, rfs, libs] = await Promise.all([
          api.listQuestions(token, projectId),
          api.listObjectives(token, projectId),
          api.listReferences(token, projectId),
          can('library')?api.listLibrary(token, projectId):Promise.resolve([]),
        ]);
        setQuestions(qs);
        setObjectives(os);
        setRefs(rfs);
        setLibraryDocs(libs);
      } catch {
        /* ignore — diagrams still work with profile-only data */
      }
    })();
  }, [token, projectId]);

  async function handleApplySuggestion(
    id: number,
    editedPayload?: Record<string, unknown>,
    markApproved = false
  ) {
    if (!token) return;
    setBusySuggestionId(id);
    setError(null);
    try {
      const res = await api.actOnSuggestion(token, projectId, id, {
        action: "apply",
        edited_payload: editedPayload ?? null,
        mark_approved: markApproved,
      });
      setFlash(res.message || t("sug.applied"));
      await loadSuggestions();
      await refreshTab("questions");
      await loadCore();
    } catch (e) {
      setError(e instanceof Error ? e.message : t("ws.saveFailed"));
    } finally {
      setBusySuggestionId(null);
    }
  }

  async function handleRejectSuggestion(id: number) {
    if (!token) return;
    setBusySuggestionId(id);
    try {
      await api.actOnSuggestion(token, projectId, id, { action: "reject" });
      setFlash(t("sug.rejected"));
      await loadSuggestions();
    } catch (e) {
      setError(e instanceof Error ? e.message : t("ws.saveFailed"));
    } finally {
      setBusySuggestionId(null);
    }
  }

  async function selectTab(next: PanelTab) {
    // In full-page mode, switch by navigating so the URL/tab stay in sync
    if (isStandalone) {
      navigate(panelUrl(projectId, next));
      return;
    }
    setTab(next);
    try {
      await refreshTab(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("ws.loadFailed"));
    }
  }

  // When opened as /panel/:panel, lock tab to that section and load its data
  useEffect(() => {
    if (!standaloneSection || !isPanelTab(standaloneSection)) return;
    setTab(standaloneSection);
    refreshTab(standaloneSection).catch((e) =>
      setError(e instanceof Error ? e.message : t("ws.loadFailed"))
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [standaloneSection, token, projectId]);

  async function sendChat(content: string, special?: string) {
    if (!token || !content.trim()) return;
    setChatBusy(true);
    setError(null);
    try {
      const res = await api.sendMessage(
        token,
        projectId,
        content.trim(),
        project?.current_stage,
        special,
        lang
      );
      setMessages((m) => [...m, res.user_message, res.assistant_message]);
      setInput("");
      if (res.suggestions?.length) {
        setSuggestions((prev) => {
          const ids = new Set(prev.map((s) => s.id));
          const merged = [...res.suggestions.filter((s) => !ids.has(s.id)), ...prev];
          return merged;
        });
        setTab("suggestions");
      } else {
        await loadSuggestions();
      }
      if (res.integrity_warnings?.length) {
        setError(res.integrity_warnings.join(" · "));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : t("ws.chatFailed"));
    } finally {
      setChatBusy(false);
    }
  }

  async function onChatSubmit(e: FormEvent) {
    e.preventDefault();
    await sendChat(input);
  }

  async function saveProfile() {
    if (!token) return;
    setBusy(true);
    try {
      const updated = await api.updateProfile(token, projectId, {
        research_problem: profileDraft.research_problem,
        research_gap: profileDraft.research_gap,
        overall_aim: profileDraft.overall_aim,
        existing_evidence: profileDraft.existing_evidence,
        refined_idea: profileDraft.refined_idea,
        proposed_scope: profileDraft.proposed_scope,
        key_concepts: profileDraft.key_concepts,
        initial_search_terms: profileDraft.initial_search_terms,
        expected_contribution: profileDraft.expected_contribution,
        ethics_requirements: profileDraft.ethics_requirements,
        scientific_significance: profileDraft.scientific_significance,
        practical_significance: profileDraft.practical_significance,
      });
      setProfileDraft(updated);
      await loadCore();
    } catch (e) {
      setError(e instanceof Error ? e.message : t("ws.saveFailed"));
    } finally {
      setBusy(false);
    }
  }

  async function setStage(stageKey: string) {
    if (!token) return;
    await api.updateProject(token, projectId, { current_stage: stageKey });
    await api.updateStage(token, projectId, stageKey, { status: "in_progress" });
    await loadCore();
  }

  async function completeStage(stageKey: string) {
    if (!token) return;
    await api.updateStage(token, projectId, stageKey, { status: "completed" });
    await loadCore();
  }

  async function addQuestion(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    await api.createQuestion(token, projectId, newQ);
    setNewQ({ text: "", question_type: "descriptive", proposed_analysis: "" });
    await refreshTab("questions");
  }

  async function addObjective(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    await api.createObjective(token, projectId, {
      text: newObj.text,
      verb: newObj.verb,
      question_id: newObj.question_id ? Number(newObj.question_id) : null,
    });
    setNewObj({ text: "", question_id: "", verb: "Examine" });
    await refreshTab("questions");
  }

  async function approveQuestion(qid: number) {
    if (!token) return;
    await api.updateQuestion(token, projectId, qid, { approval_status: "approved" });
    await refreshTab("questions");
  }

  async function runAlignment() {
    if (!token) return;
    setBusy(true);
    try {
      setAlignment(await api.checkAlignment(token, projectId, lang));
      setTab("alignment");
    } catch (e) {
      setError(e instanceof Error ? e.message : t("ws.alignFailed"));
    } finally {
      setBusy(false);
    }
  }

  async function searchLit(e: FormEvent) {
    e.preventDefault();
    if (!token || !searchQ.trim()) return;
    setBusy(true);
    try {
      const res = await api.searchLiterature(token, projectId, {
        query: searchQ,
        database_name: "openalex",
        max_results: 15,
      });
      setSearchResults(res.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("ws.searchFailed"));
    } finally {
      setBusy(false);
    }
  }

  async function saveRef(item: LiteratureResult) {
    if (!token) return;
    await api.createReference(token, projectId, {
      title: item.title,
      authors: item.authors,
      year: item.year,
      journal: item.journal,
      doi: item.doi,
      url: item.url,
      verification_status: item.verification_status,
      relevance_category: "potential",
    });
    setRefs(await api.listReferences(token, projectId));
  }

  async function onUpload(file: File | null) {
    if (!token || !file) return;
    setBusy(true);
    try {
      await api.uploadDocument(token, projectId, file, "reference_material");
      setDocs(await api.listDocuments(token, projectId));
    } catch (e) {
      setError(e instanceof Error ? e.message : t("ws.uploadFailed"));
    } finally {
      setBusy(false);
    }
  }

  async function doExport() {
    if (!token) return;
    setBusy(true);
    try {
      const res = await api.exportProject(token, projectId, {
        export_type: "project_summary",
        format: "markdown",
      });
      setExportText(res.content);
      setTab("export");
    } catch (e) {
      setError(e instanceof Error ? e.message : t("ws.exportFailed"));
    } finally {
      setBusy(false);
    }
  }

  const stageStatus = useMemo(() => {
    const map = new Map(project?.stage_progress?.map((s) => [s.stage_key, s.status]));
    return map;
  }, [project]);

  const tabs: [PanelTab, TranslationKey][] = [
    ["profile", "tab.profile"],
    ["questions", "tab.questions"],
    ["structure", "tab.structure"],
    ["suggestions", "tab.suggestions"],
    ["library", "tab.library"],
    ["synthesis", "tab.synthesis"],
    ["benchmark", "tab.benchmark"],
    ["alignment", "tab.alignment"],
    ["literature", "tab.literature"],
    ["documents", "tab.documents"],
    ["export", "tab.export"],
  ];

  const openBarLabels = {
    openFullPage: t("ws.openFullPage"),
    openNewTab: t("ws.openNewTab"),
    hint: t("ws.fullPageHint"),
  };

  function SectionOpenBar({ section }: { section: StandaloneSection }) {
    if (isStandalone) return null;
    return (
      <PanelOpenBar
        fullPageHref={panelUrl(projectId, section)}
        openFullPageLabel={openBarLabels.openFullPage}
        openNewTabLabel={openBarLabels.openNewTab}
        hint={openBarLabels.hint}
      />
    );
  }

  const suggestionLabels = {
    title: t("sug.title"),
    apply: t("sug.apply"),
    applyApproved: t("sug.applyApproved"),
    reject: t("sug.reject"),
    edit: t("sug.edit"),
    hideEdit: t("sug.hideEdit"),
    empty: t("sug.empty"),
    pending: t("sug.pending"),
    rationale: t("sug.rationale"),
  };

  const libraryLabels = buildLibraryLabels((k) => t(k as TranslationKey));

  const synthesisLabels: Record<string, string> = {
    kicker: t("syn.kicker"),
    title: t("syn.title"),
    subtitle: t("syn.subtitle"),
    integrity: t("syn.integrity"),
    refresh: t("syn.refresh"),
    refreshing: t("syn.refreshing"),
    uploadPapers: t("syn.uploadPapers"),
    papers: t("syn.papers"),
    withMethods: t("syn.withMethods"),
    withResults: t("syn.withResults"),
    aiOn: t("syn.aiOn"),
    insights: t("syn.insights"),
    story: t("syn.story"),
    themes: t("syn.themes"),
    methods: t("syn.methods"),
    writingMoves: t("syn.writingMoves"),
    gaps: t("syn.gaps"),
    heatmap: t("syn.heatmap"),
    heatmapHint: t("syn.heatmapHint"),
    matrix: t("syn.matrix"),
    colPaper: t("syn.colPaper"),
    colType: t("syn.colType"),
    colDesign: t("syn.colDesign"),
    colIdeas: t("syn.colIdeas"),
    colMethods: t("syn.colMethods"),
    colFindings: t("syn.colFindings"),
    colStages: t("syn.colStages"),
    path: t("syn.path"),
    openLibrary: t("syn.openLibrary"),
    openBenchmark: t("syn.openBenchmark"),
  };

  const benchmarkLabels: Record<string, string> = {
    title: t("bench.title"),
    intro: t("bench.intro"),
    integrity: t("bench.integrity"),
    needPapers: t("bench.needPapers"),
    goLibrary: t("bench.goLibrary"),
    useAll: t("bench.useAll"),
    run: t("bench.run"),
    running: t("bench.running"),
    score: t("bench.score"),
    aiEnriched: t("lib.aiEnriched"),
    aiSummary: t("bench.aiSummary"),
    gaps: t("bench.gaps"),
    strengths: t("bench.strengths"),
    recommendations: t("bench.recommendations"),
    design: t("bench.design"),
    stageTable: t("bench.stageTable"),
    stage: t("bench.stage"),
    yourProject: t("bench.yourProject"),
    inPapers: t("bench.inPapers"),
    verdict: t("bench.verdict"),
    action: t("bench.action"),
    examples: t("bench.examples"),
  };

  const structureLabels: Record<string, string> = {
    structureHint: t("struct.hint"),
    hypotheses: t("struct.hypotheses"),
    variables: t("struct.variables"),
    design: t("struct.design"),
    population: t("struct.population"),
    sampling: t("struct.sampling"),
    instruments: t("struct.instruments"),
    analysis: t("struct.analysis"),
    h0: t("struct.h0"),
    h1: t("struct.h1"),
    direction: t("struct.direction"),
    nonDirectional: t("struct.nonDirectional"),
    directional: t("struct.directional"),
    theoreticalBasis: t("struct.theoreticalBasis"),
    proposedTest: t("struct.proposedTest"),
    addHypothesis: t("struct.addHypothesis"),
    varName: t("struct.varName"),
    varRole: t("struct.varRole"),
    scale: t("struct.scale"),
    operationalDef: t("struct.operationalDef"),
    measurementMethod: t("struct.measurementMethod"),
    addVariable: t("struct.addVariable"),
    designType: t("struct.designType"),
    paradigm: t("struct.paradigm"),
    rationale: t("struct.rationale"),
    strengths: t("struct.strengths"),
    limitations: t("struct.limitations"),
    biasRisks: t("struct.biasRisks"),
    addDesign: t("struct.addDesign"),
    targetPop: t("struct.targetPop"),
    inclusion: t("struct.inclusion"),
    exclusion: t("struct.exclusion"),
    samplingMethod: t("struct.samplingMethod"),
    sampleSize: t("struct.sampleSize"),
    sampleRationale: t("struct.sampleRationale"),
    sampleRationaleHint: t("struct.sampleRationaleHint"),
    assumptions: t("struct.assumptions"),
    savePopSampling: t("struct.savePopSampling"),
    instrumentName: t("struct.instrumentName"),
    itemText: t("struct.itemText"),
    construct: t("struct.construct"),
    variable: t("struct.variable"),
    addItem: t("struct.addItem"),
    test: t("struct.test"),
    descriptive: t("struct.descriptive"),
    addAnalysis: t("struct.addAnalysis"),
    linkQuestion: t("struct.linkQuestion"),
  };

  if (!project) {
    return (
      <div className="container">
        {!error && <p className="muted" role="status">{t("ws.loading")}</p>}
        {error && <div className="error" role="alert">{error}</div>}
        <Link className="btn btn-ghost" to="/">{t("common.dashboard")}</Link>
        {error && <button className="btn" type="button" onClick={() => { setError(null); void loadCore().catch((e) => setError(e.message)); }}>{lang === "ar" ? "حاول مرة أخرى" : "Try again"}</button>}
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">RG</div>
          <div>
            <div style={{ fontSize: "0.95rem" }}>{project.working_title}</div>
            <div className="muted" style={{ fontSize: "0.75rem", fontWeight: 400 }}>
              {documentTypeLabel(lang, project.document_type)} · {t("common.stage")}:{" "}
              {project.current_stage}
            </div>
          </div>
        </div>
        <div className="topbar-actions">
          <LanguageSwitcher />
          {can('research_desk')&&<Link className="btn" to={`/projects/${projectId}/desk`}>{lang === "ar" ? "مكتب البحث" : "Research desk"}</Link>}
          {can('paper_review')&&<Link className="btn" to={`/projects/${projectId}/review`}>{lang === "ar" ? "تحليل ورقة" : "Paper review"}</Link>}
          {isStandalone && (
            <Link className="btn btn-primary" to={`/projects/${projectId}`}>
              {t("ws.backToWorkspace")}
            </Link>
          )}
          <button className="btn" type="button" onClick={runAlignment} disabled={busy}>
            {t("ws.checkAlignment")}
          </button>
          <button className="btn" type="button" onClick={doExport} disabled={busy}>
            {t("ws.export")}
          </button>
          <Link className="btn btn-ghost" to="/">
            {t("common.dashboard")}
          </Link>
          <button className="btn btn-ghost" type="button" onClick={logout}>
            {user?.full_name?.split(" ")[0] || t("common.signOut")}
          </button>
        </div>
      </header>

      {error && (
        <div className="container">
          <div className="error">{error}</div>
        </div>
      )}
      {flash && (
        <div className="container">
          <div className="success-box" onClick={() => setFlash(null)}>
            {flash}
          </div>
        </div>
      )}

      <div className={`workspace${isStandalone ? " workspace--standalone" : ""}`}>
        {(!isStandalone || standaloneSection === "stages") && (
        <aside className={`panel${standaloneSection === "stages" ? " panel--full" : ""}`}>
          <div className="panel-header">
            <span>
              {standaloneSection === "stages" ? t("ws.standaloneStages") : t("ws.stages")}
            </span>
            <div className="panel-header-actions">
              <span className="badge">{project.completion_percent}%</span>

            </div>
          </div>
          <div className="panel-body stack">
            <StagesBoard
              stages={stages}
              stageStatus={stageStatus}
              currentStage={project.current_stage}
              completionPercent={project.completion_percent}
              lang={lang}
              variant={standaloneSection === "stages" ? "page" : "sidebar"}
              projectCtx={{
                project,
                questions,
                objectives,
                references: refs,
                libraryDocs,
                lang,
              }}
              labels={{
                markComplete: t("ws.markComplete"),
                current: t("ws.stageCurrent"),
                progress: t("ws.stagesProgress"),
                stagesHint: t("ws.stagesHint"),
                setCurrent: t("ws.setCurrentStage"),
                showDiagram: t("ws.showDiagram"),
                hideDiagram: t("ws.hideDiagram"),
                diagramTitle: t("ws.diagramTitle"),
                flowInputs: t("ws.flowInputs"),
                flowProcess: t("ws.flowProcess"),
                flowOutputs: t("ws.flowOutputs"),
                flowNext: t("ws.flowNext"),
                flowStatus: t("ws.flowStatus"),
                flowCompleted: t("ws.flowCompleted"),
                flowNotCompleted: t("ws.flowNotCompleted"),
                flowInProgress: t("ws.flowInProgress"),
                flowNotStarted: t("ws.flowNotStarted"),
                flowRealData: t("ws.flowRealData"),
                flowEmpty: t("ws.flowEmpty"),
                flowReadiness: t("ws.flowReadiness"),
                flowWhy: t("ws.flowWhy"),
                close: t("ws.close"),
              }}
              statusLabel={statusLabel}
              onSetStage={(key) => {
                void setStage(key);
              }}
              onCompleteStage={(key) => {
                void completeStage(key);
              }}
              openBar={
                standaloneSection === "stages" ? undefined : (
                  <SectionOpenBar section="stages" />
                )
              }
            />
          </div>
        </aside>
        )}

        {(!isStandalone || standaloneSection === "chat") && (
        <section className={`panel${standaloneSection === "chat" ? " panel--full" : ""}`}>
          <div className="panel-header">
            {standaloneSection === "chat" ? t("ws.standaloneChat") : t("app.name")}
            <span className="badge">{t("ws.integrityFirst")}</span>
          </div>
          <div className="panel-body">
            <SectionOpenBar section="chat" />
            <details className="research-shortcuts"><summary>{lang === "ar" ? "اختصارات البحث" : "Research shortcuts"}</summary><div className="command-row">
              {COMMAND_KEYS.map((c) => (
                <button
                  key={c}
                  type="button"
                  className="btn"
                  disabled={chatBusy}
                  onClick={() => sendChat(c, c)}
                >
                  {cmdLabel(c)}
                </button>
              ))}
            </div></details>
            <div className="chat-log" role="log" aria-label={lang === "ar" ? "محادثة البحث" : "Research conversation"}>
              {messages.map((m) => {
                const key = `msg-${m.id}`;
                const hasTr = Boolean(translatedTexts[key]);
                return (
                  <div key={m.id} className={`msg ${m.role}`}>
                    <div className="msg-body">{displayText(key, m.content)}</div>
                    {m.role === "assistant" && (
                      <div className="msg-translate-row">
                        <TranslateButton
                          text={m.content}
                          compact
                          onTranslated={(tr) => {
                            if (tr && tr.trim() && tr.trim() !== m.content.trim()) {
                              setTranslation(key, tr);
                            } else if (tr && /[\u0600-\u06FF]/.test(tr)) {
                              setTranslation(key, tr);
                            }
                          }}
                        />
                        {hasTr && (
                          <button
                            type="button"
                            className="btn translate-btn translate-btn--compact"
                            onClick={() =>
                              setShowOriginal((p) => ({ ...p, [key]: !p[key] }))
                            }
                          >
                            {showOriginal[key]
                              ? t("ws.showTranslation")
                              : t("ws.showOriginal")}
                          </button>
                        )}
                        {hasTr && !showOriginal[key] && (
                          <span className="badge ok translated-badge">
                            {t("ws.translatedBadge")}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
              <div ref={chatEnd} />
            </div>
            {suggestions.length > 0 && (
              <div className="chat-suggestions">
                <SuggestionCards
                  suggestions={suggestions.slice(0, 5)}
                  busyId={busySuggestionId}
                  onApply={handleApplySuggestion}
                  onReject={handleRejectSuggestion}
                  labels={suggestionLabels}
                />
              </div>
            )}
            <form className="chat-input" onSubmit={onChatSubmit}>
              <VoiceTextField
                value={input}
                onChange={setInput}
                language={project.writing_language}
                placeholder={t("ws.chatPlaceholder")}
                disabled={chatBusy}
                rows={3}
              />
              <button className="btn btn-primary" type="submit" disabled={chatBusy || !input.trim()}>
                {chatBusy ? "…" : t("common.send")}
              </button>
            </form>
          </div>
        </section>
        )}

        {(!isStandalone || isPanelTab(standaloneSection)) && (
        <aside className={`panel${isStandalone && isPanelTab(standaloneSection) ? " panel--full" : ""}`}>
          <div className="panel-header">
            {isStandalone && isPanelTab(standaloneSection)
              ? t(tabs.find(([k]) => k === standaloneSection)?.[1] || "ws.workspace")
              : t("ws.workspace")}
          </div>
          <div className="panel-body">
            <div className="tabs">
              {tabs.filter(([k])=>can(panelPermission(k))).map(([k, labelKey]) => (
                <button
                  key={k}
                  type="button"
                  className={`tab ${tab === k ? "active" : ""}`}
                  onClick={() => selectTab(k)}
                >
                  {t(labelKey)}
                </button>
              ))}
            </div>

            {tab === "profile" && (
              <div className="stack">
                <SectionOpenBar section="profile" />
                <p className="muted" style={{ fontSize: "0.85rem" }}>
                  {t("ws.profileHint")}
                </p>
                {PROFILE_FIELDS.map((key) => (
                  <div className="field" key={key}>
                    <VoiceTextField
                      compact
                      label={t(`profile.${key}` as TranslationKey)}
                      language={project.writing_language}
                      value={
                        (profileDraft as Record<string, string | null | undefined>)[key] || ""
                      }
                      onChange={(text) => setProfileDraft((d) => ({ ...d, [key]: text }))}
                    />
                  </div>
                ))}
                <button className="btn btn-primary" type="button" onClick={saveProfile} disabled={busy}>
                  {t("ws.saveProfile")}
                </button>
              </div>
            )}

            {tab === "structure" && token && (
              <div className="stack">
                <SectionOpenBar section="structure" />
                <StructurePanel
                  token={token}
                  projectId={projectId}
                  questions={questions}
                  labels={structureLabels}
                />
              </div>
            )}

            {tab === "library" && token && (
              <div className="stack">
                <SectionOpenBar section="library" />
                <ResearchLibrary
                  token={token}
                  projectId={projectId}
                  stages={stages}
                  labels={libraryLabels}
                  uiLang={lang}
                  variant={isStandalone ? "page" : "embedded"}
                />
              </div>
            )}

            {tab === "synthesis" && token && (
              <div className="stack">
                <SectionOpenBar section="synthesis" />
                <SynthesisDashboard
                  token={token}
                  projectId={projectId}
                  language={lang}
                  labels={synthesisLabels}
                  onOpenLibrary={() => navigate(`/projects/${projectId}/library`)}
                  onOpenBenchmark={() => selectTab("benchmark")}
                />
              </div>
            )}

            {tab === "benchmark" && token && (
              <div className="stack">
                <SectionOpenBar section="benchmark" />
                <BenchmarkPanel
                  token={token}
                  projectId={projectId}
                  language={lang}
                  libraryDocs={libraryDocs}
                  labels={benchmarkLabels}
                  onOpenLibrary={() => navigate(`/projects/${projectId}/library`)}
                />
              </div>
            )}

            {tab === "suggestions" && (
              <div className="stack">
                <SectionOpenBar section="suggestions" />
                <SuggestionCards
                  suggestions={suggestions}
                  busyId={busySuggestionId}
                  onApply={handleApplySuggestion}
                  onReject={handleRejectSuggestion}
                  labels={suggestionLabels}
                />
              </div>
            )}

            {tab === "questions" && (
              <div className="stack">
                <SectionOpenBar section="questions" />
                <h3>{t("ws.researchQuestions")}</h3>
                {questions.map((q) => (
                  <div key={q.id} className="issue">
                    <div className="badge">{qTypeLabel(q.question_type)}</div>{" "}
                    <div className="badge">{approvalLabel(q.approval_status)}</div>
                    <p>{q.text}</p>
                    {q.proposed_analysis && (
                      <p className="muted" style={{ fontSize: "0.85rem" }}>
                        {t("ws.analysis")}: {q.proposed_analysis}
                      </p>
                    )}
                    {q.approval_status !== "approved" && (
                      <button className="btn" type="button" onClick={() => approveQuestion(q.id)}>
                        {t("common.approve")}
                      </button>
                    )}
                  </div>
                ))}
                <form className="stack" onSubmit={addQuestion}>
                  <div className="field">
                    <VoiceTextField
                      compact
                      label={t("ws.newQuestion")}
                      language={project.writing_language}
                      required
                      value={newQ.text}
                      onChange={(text) => setNewQ({ ...newQ, text })}
                      placeholder={t("ws.questionPlaceholder")}
                    />
                  </div>
                  <div className="field">
                    <label>{t("common.type")}</label>
                    <select
                      value={newQ.question_type}
                      onChange={(e) => setNewQ({ ...newQ, question_type: e.target.value })}
                    >
                      {QUESTION_TYPES.map((qt) => (
                        <option key={qt} value={qt}>
                          {qTypeLabel(qt)}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="field">
                    <label>{t("ws.proposedAnalysis")}</label>
                    <input
                      value={newQ.proposed_analysis}
                      onChange={(e) => setNewQ({ ...newQ, proposed_analysis: e.target.value })}
                    />
                  </div>
                  <button className="btn btn-primary" type="submit">
                    {t("ws.addQuestion")}
                  </button>
                </form>

                <h3>{t("ws.objectives")}</h3>
                {objectives.map((o) => (
                  <div key={o.id} className="issue">
                    <span className="badge">{approvalLabel(o.approval_status)}</span>
                    <p>
                      {o.verb ? `${o.verb}: ` : ""}
                      {o.text}
                    </p>
                    <p className="muted" style={{ fontSize: "0.8rem" }}>
                      {t("ws.linkedQ")}: {o.question_id ?? t("common.none")}
                    </p>
                  </div>
                ))}
                <form className="stack" onSubmit={addObjective}>
                  <div className="field">
                    <VoiceTextField
                      compact
                      label={t("ws.objectiveText")}
                      language={project.writing_language}
                      required
                      value={newObj.text}
                      onChange={(text) => setNewObj({ ...newObj, text })}
                      placeholder={t("ws.objectivePlaceholder")}
                    />
                  </div>
                  <div className="field">
                    <label>{t("ws.linkQuestion")}</label>
                    <select
                      value={newObj.question_id}
                      onChange={(e) => setNewObj({ ...newObj, question_id: e.target.value })}
                    >
                      <option value="">—</option>
                      {questions.map((q) => (
                        <option key={q.id} value={q.id}>
                          #{q.id}: {q.text.slice(0, 60)}
                        </option>
                      ))}
                    </select>
                  </div>
                  <button className="btn" type="submit">
                    {t("ws.addObjective")}
                  </button>
                </form>
              </div>
            )}

            {tab === "alignment" && (
              <div className="stack">
                <SectionOpenBar section="alignment" />
                <button className="btn btn-primary" type="button" onClick={runAlignment} disabled={busy}>
                  {t("ws.runAlignment")}
                </button>
                {alignment && (
                  <>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      {Object.entries(alignment.summary).map(([k, v]) => (
                        <span
                          key={k}
                          className={`badge ${k === "critical" || k === "major" ? "danger" : k === "warning" ? "warn" : ""}`}
                        >
                          {severityLabel(k)}: {v}
                        </span>
                      ))}
                    </div>
                    <h3>{t("ws.chainStatus")}</h3>
                    <table className="table">
                      <tbody>
                        {Object.entries(alignment.chain_status).map(([k, v]) => (
                          <tr key={k}>
                            <td>{k}</td>
                            <td>
                              <span className={`badge ${v === "present" ? "ok" : "warn"}`}>
                                {chainLabel(v)}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    <h3>{t("ws.issues")}</h3>
                    {alignment.issues.length === 0 && (
                      <div className="success-box">{t("ws.noIssues")}</div>
                    )}
                    {alignment.issues.map((issue) => {
                      const ek = `align-e-${issue.id}`;
                      const rk = `align-r-${issue.id}`;
                      return (
                      <div key={issue.id} className={`issue ${issue.severity}`}>
                        <strong>
                          [{severityLabel(issue.severity)}] {issue.issue_type}
                        </strong>
                        <p>{displayText(ek, issue.explanation)}</p>
                        <TranslateButton
                          text={issue.explanation}
                          compact
                          onTranslated={(tr) => setTranslation(ek, tr)}
                        />
                        {issue.recommended_correction && (
                          <>
                            <p className="muted">
                              {displayText(rk, issue.recommended_correction)}
                            </p>
                            <TranslateButton
                              text={issue.recommended_correction}
                              compact
                              onTranslated={(tr) => setTranslation(rk, tr)}
                            />
                          </>
                        )}
                      </div>
                      );
                    })}
                  </>
                )}
              </div>
            )}

            {tab === "literature" && (
              <div className="stack">
                <SectionOpenBar section="literature" />
                <form className="stack" onSubmit={searchLit}>
                  <div className="field">
                    <label>{t("ws.searchOpenAlex")}</label>
                    <input
                      value={searchQ}
                      onChange={(e) => setSearchQ(e.target.value)}
                      placeholder={t("ws.searchPlaceholder")}
                    />
                  </div>
                  <button className="btn btn-primary" type="submit" disabled={busy}>
                    {t("common.search")}
                  </button>
                </form>
                <p className="muted" style={{ fontSize: "0.8rem" }}>
                  {t("ws.litHint")}
                </p>
                {searchResults.map((r, i) => (
                  <div key={i} className="issue">
                    <strong>{r.title}</strong>
                    <p className="muted" style={{ fontSize: "0.85rem" }}>
                      {r.authors} ({r.year || "n.d."}) · {r.journal || "—"}
                    </p>
                    {r.doi && <p className="muted">DOI: {r.doi}</p>}
                    <button className="btn" type="button" onClick={() => saveRef(r)}>
                      {t("ws.saveReference")}
                    </button>
                  </div>
                ))}
                <h3>{t("ws.savedReferences")}</h3>
                {refs.map((r) => (
                  <div key={r.id} className="issue">
                    <span className="badge">{r.verification_status}</span>
                    <p>
                      {r.authors} ({r.year}). {r.title}
                    </p>
                  </div>
                ))}
              </div>
            )}

            {tab === "documents" && (
              <div className="stack">
                <SectionOpenBar section="documents" />
                <div className="field">
                  <label>{t("ws.uploadLabel")}</label>
                  <input
                    type="file"
                    accept=".pdf,.docx,.txt,.csv,.xlsx"
                    onChange={(e) => onUpload(e.target.files?.[0] || null)}
                  />
                </div>
                {docs.map((d) => (
                  <div key={d.id} className="issue">
                    <strong>{d.original_filename}</strong>
                    <p className="muted">
                      {d.file_type} · {Math.round(d.file_size / 1024)} KB · {t("ws.extract")}:{" "}
                      {d.extracted_text_status}
                    </p>
                  </div>
                ))}
                {docs.length === 0 && <div className="empty">{t("ws.noDocs")}</div>}
              </div>
            )}

            {tab === "export" && (
              <div className="stack">
                <SectionOpenBar section="export" />
                <button className="btn btn-primary" type="button" onClick={doExport} disabled={busy}>
                  {t("ws.generateSummary")}
                </button>
                {exportText && (
                  <textarea readOnly value={exportText} style={{ minHeight: 320 }} />
                )}
              </div>
            )}
          </div>
        </aside>
        )}
      </div>
    </div>
  );
}
