const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export class ApiError extends Error {
  constructor(message:string,public status:number){super(message);this.name='ApiError';}
}

function authHeaders(token: string | null): HeadersInit {
  const h: HeadersInit = { "Content-Type": "application/json" };
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

export async function request<T>(
  path: string,
  options: RequestInit = {},
  token: string | null = null
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        ...(options.body instanceof FormData ? (token ? { Authorization: `Bearer ${token}` } : {}) : authHeaders(token)),
        ...(options.headers || {}),
      },
    });
  } catch {
    throw new Error(
      "Cannot reach the API (Failed to fetch). " +
        "Start the backend on http://127.0.0.1:8000 and open the app via http://127.0.0.1:3000 " +
        "(not a different host). If both are running, hard-refresh the page."
    );
  }
  if (!res.ok) {
    let detail: unknown = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? body.message ?? body;
    } catch {
      /* ignore */
    }
    // FastAPI may return detail as string or list of validation errors
    if (typeof detail === "string") throw new ApiError(detail,res.status);
    if (Array.isArray(detail)) {
      throw new ApiError(
        detail
          .map((d) => (typeof d === "object" && d && "msg" in d ? String((d as { msg: string }).msg) : JSON.stringify(d)))
          .join("; "),res.status
      );
    }
    throw new ApiError(JSON.stringify(detail),res.status);
  }
  return res.json() as Promise<T>;
}

export const api = {
  register: (data: object) =>
    request<{ access_token: string; user: unknown }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  login: (data: object) =>
    request<{ access_token: string; user: unknown }>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  me: (token: string) => request<import("./types").User>("/auth/me", {}, token),
  stages: (token: string) =>
    request<import("./types").StageDefinition[]>("/projects/meta/stages", {}, token),
  documentTypes: (token: string) =>
    request<string[]>("/projects/meta/document-types", {}, token),
  listProjects: (token: string) =>
    request<import("./types").ProjectSummary[]>("/projects", {}, token),
  getProject: (token: string, id: number) =>
    request<import("./types").Project>(`/projects/${id}`, {}, token),
  createProject: (token: string, data: object) =>
    request<import("./types").Project>("/projects", {
      method: "POST",
      body: JSON.stringify(data),
    }, token),
  updateProject: (token: string, id: number, data: object) =>
    request<import("./types").Project>(`/projects/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }, token),
  updateProfile: (token: string, id: number, data: object) =>
    request<import("./types").Profile>(`/projects/${id}/profile`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }, token),
  updateStage: (token: string, id: number, stageKey: string, data: object) =>
    request(`/projects/${id}/stages/${stageKey}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }, token),
  getConversation: (token: string, id: number, language?: string) =>
    request<import("./types").Conversation>(
      `/projects/${id}/chat/conversation${language ? `?language=${language}` : ""}`,
      {},
      token
    ),
  sendMessage: (
    token: string,
    id: number,
    content: string,
    stage_key?: string,
    special_command?: string,
    language?: string
  ) =>
    request<{
      conversation_id: number;
      user_message: import("./types").Message;
      assistant_message: import("./types").Message;
      integrity_warnings: string[];
      suggestions: import("./types").AISuggestion[];
    }>(
      `/projects/${id}/chat/messages`,
      {
        method: "POST",
        body: JSON.stringify({ content, stage_key, special_command, language }),
      },
      token
    ),
  listSuggestions: (token: string, id: number) =>
    request<import("./types").AISuggestion[]>(`/projects/${id}/suggestions`, {}, token),
  actOnSuggestion: (
    token: string,
    id: number,
    suggestionId: number,
    data: {
      action: string;
      edited_payload?: Record<string, unknown> | null;
      mark_approved?: boolean;
      notes?: string;
    }
  ) =>
    request<{
      suggestion_id: number;
      action: string;
      approval_status: string;
      created_element_type?: string | null;
      created_element_id?: number | null;
      message: string;
    }>(
      `/projects/${id}/suggestions/${suggestionId}/action`,
      { method: "POST", body: JSON.stringify(data) },
      token
    ),
  listQuestions: (token: string, id: number) =>
    request<import("./types").Question[]>(`/projects/${id}/questions`, {}, token),
  createQuestion: (token: string, id: number, data: object) =>
    request<import("./types").Question>(`/projects/${id}/questions`, {
      method: "POST",
      body: JSON.stringify(data),
    }, token),
  updateQuestion: (token: string, id: number, qid: number, data: object) =>
    request<import("./types").Question>(`/projects/${id}/questions/${qid}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }, token),
  listObjectives: (token: string, id: number) =>
    request<import("./types").Objective[]>(`/projects/${id}/objectives`, {}, token),
  createObjective: (token: string, id: number, data: object) =>
    request<import("./types").Objective>(`/projects/${id}/objectives`, {
      method: "POST",
      body: JSON.stringify(data),
    }, token),
  checkAlignment: (token: string, id: number, language?: string) =>
    request<import("./types").AlignmentReport>(
      `/projects/${id}/alignment/check${language ? `?language=${language}` : ""}`,
      {
      method: "POST",
    }, token),
  searchLiterature: (token: string, id: number, data: object) =>
    request<{
      id: number;
      results: import("./types").LiteratureResult[];
      result_count: number;
      query: string;
    }>(`/projects/${id}/literature/search`, {
      method: "POST",
      body: JSON.stringify(data),
    }, token),
  listReferences: (token: string, id: number) =>
    request<import("./types").Reference[]>(`/projects/${id}/references`, {}, token),
  createReference: (token: string, id: number, data: object) =>
    request<import("./types").Reference>(`/projects/${id}/references`, {
      method: "POST",
      body: JSON.stringify(data),
    }, token),
  listDocuments: (token: string, id: number) =>
    request<import("./types").DocumentItem[]>(`/projects/${id}/documents`, {}, token),
  uploadDocument: async (token: string, id: number, file: File, category: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("category", category);
    const res = await fetch(`${API_BASE}/projects/${id}/documents`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json() as Promise<import("./types").DocumentItem>;
  },
  exportProject: (token: string, id: number, data: object) =>
    request<{ content: string; export_type: string; format: string }>(
      `/projects/${id}/export`,
      { method: "POST", body: JSON.stringify(data) },
      token
    ),
  listHypotheses: (token: string, id: number) =>
    request<import("./types").Hypothesis[]>(`/projects/${id}/hypotheses`, {}, token),
  createHypothesis: (token: string, id: number, data: object) =>
    request<import("./types").Hypothesis>(
      `/projects/${id}/hypotheses`,
      { method: "POST", body: JSON.stringify(data) },
      token
    ),
  listVariables: (token: string, id: number) =>
    request<import("./types").Variable[]>(`/projects/${id}/variables`, {}, token),
  createVariable: (token: string, id: number, data: object) =>
    request<import("./types").Variable>(
      `/projects/${id}/variables`,
      { method: "POST", body: JSON.stringify(data) },
      token
    ),
  listDesigns: (token: string, id: number) =>
    request<import("./types").Design[]>(`/projects/${id}/designs`, {}, token),
  createDesign: (token: string, id: number, data: object) =>
    request<import("./types").Design>(
      `/projects/${id}/designs`,
      { method: "POST", body: JSON.stringify(data) },
      token
    ),
  listPopulations: (token: string, id: number) =>
    request<import("./types").Population[]>(`/projects/${id}/populations`, {}, token),
  createPopulation: (token: string, id: number, data: object) =>
    request<import("./types").Population>(
      `/projects/${id}/populations`,
      { method: "POST", body: JSON.stringify(data) },
      token
    ),
  listSampling: (token: string, id: number) =>
    request<import("./types").SamplingPlan[]>(`/projects/${id}/sampling-plans`, {}, token),
  createSampling: (token: string, id: number, data: object) =>
    request<import("./types").SamplingPlan>(
      `/projects/${id}/sampling-plans`,
      { method: "POST", body: JSON.stringify(data) },
      token
    ),
  listInstruments: (token: string, id: number) =>
    request<import("./types").Instrument[]>(`/projects/${id}/instruments`, {}, token),
  createInstrument: (token: string, id: number, data: object) =>
    request<import("./types").Instrument>(
      `/projects/${id}/instruments`,
      { method: "POST", body: JSON.stringify(data) },
      token
    ),
  listAnalysisPlans: (token: string, id: number) =>
    request<import("./types").AnalysisPlan[]>(`/projects/${id}/analysis-plans`, {}, token),
  createAnalysisPlan: (token: string, id: number, data: object) =>
    request<import("./types").AnalysisPlan>(
      `/projects/${id}/analysis-plans`,
      { method: "POST", body: JSON.stringify(data) },
      token
    ),

  // Previous Research Library
  listLibrary: (token: string, id: number) =>
    request<import("./types").SourceDocumentSummary[]>(`/projects/${id}/library`, {}, token),
  uploadLibraryDoc: async (token: string, id: number, file: File, language?: string) => {
    const form = new FormData();
    form.append("file", file);
    const q = language ? `?language=${encodeURIComponent(language)}` : "";
    const res = await fetch(`${API_BASE}/projects/${id}/library/upload${q}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    if (!res.ok) {
      let detail = await res.text();
      try {
        detail = JSON.parse(detail).detail || detail;
      } catch {
        /* ignore */
      }
      throw new Error(typeof detail === "string" ? detail : "Upload failed");
    }
    return res.json() as Promise<import("./types").SourceDocumentDetail>;
  },
  uploadLibraryMany: async (
    token: string,
    id: number,
    files: File[],
    language?: string
  ) => {
    const form = new FormData();
    for (const f of files) {
      form.append("files", f);
    }
    const q = language ? `?language=${encodeURIComponent(language)}` : "";
    const res = await fetch(`${API_BASE}/projects/${id}/library/upload-many${q}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    if (!res.ok) {
      let detail = await res.text();
      try {
        detail = JSON.parse(detail).detail || detail;
      } catch {
        /* ignore */
      }
      throw new Error(typeof detail === "string" ? detail : "Upload failed");
    }
    return res.json() as Promise<import("./types").MultiUploadResult>;
  },
  getLibraryDoc: (token: string, id: number, docId: number, language?: string) =>
    request<import("./types").SourceDocumentDetail>(
      `/projects/${id}/library/${docId}${language ? `?language=${language}` : ""}`,
      {},
      token
    ),
  reprocessLibraryDoc: (token: string, id: number, docId: number, language?: string) =>
    request<import("./types").SourceDocumentDetail>(
      `/projects/${id}/library/${docId}/reprocess${language ? `?language=${language}` : ""}`,
      { method: "POST" },
      token
    ),
  confirmLibraryClassification: (
    token: string,
    id: number,
    docId: number,
    data: object,
    language?: string
  ) =>
    request<import("./types").SourceDocumentDetail>(
      `/projects/${id}/library/${docId}/confirm-classification${language ? `?language=${language}` : ""}`,
      { method: "POST", body: JSON.stringify(data) },
      token
    ),
  updateLibraryNotes: (
    token: string,
    id: number,
    docId: number,
    notes: string,
    language?: string
  ) =>
    request<import("./types").SourceDocumentDetail>(
      `/projects/${id}/library/${docId}/notes${language ? `?language=${language}` : ""}`,
      { method: "PATCH", body: JSON.stringify({ researcher_notes: notes }) },
      token
    ),
  verifyLibraryStage: (
    token: string,
    id: number,
    docId: number,
    mappingId: number,
    data: object
  ) =>
    request(
      `/projects/${id}/library/${docId}/stages/${mappingId}/verify`,
      { method: "POST", body: JSON.stringify(data) },
      token
    ),
  compareLibraryDocs: (
    token: string,
    id: number,
    data: object,
    language?: string
  ) =>
    request<import("./types").PaperComparison>(
      `/projects/${id}/library/compare${language ? `?language=${language}` : ""}`,
      { method: "POST", body: JSON.stringify(data) },
      token
    ),
  translateLibraryAnalysis: (
    token: string,
    id: number,
    docId: number,
    data: {
      target_language?: string;
      scope?: "full" | "stage";
      stage_key?: string;
    }
  ) =>
    request<{
      document: import("./types").SourceDocumentDetail;
      ai_used: boolean;
      message: string;
      translated_fields: number;
      candidate_fields: number;
    }>(
      `/projects/${id}/library/${docId}/translate-analysis`,
      { method: "POST", body: JSON.stringify(data) },
      token
    ),
  /** Translate any free-text block (chat, suggestion, alignment, stage note). */
  translateText: (token: string, text: string, target_language: string = "ar") =>
    request<{
      original: string;
      translated: string;
      target_language: string;
      used_service: boolean;
      message: string;
    }>(
      `/translate/text`,
      {
        method: "POST",
        body: JSON.stringify({ text, target_language }),
      },
      token
    ),
  libraryFileUrl: (id: number, docId: number) =>
    `${API_BASE}/projects/${id}/library/${docId}/file`,
  writeSectionGuide: (
    token: string,
    id: number,
    docId: number,
    stage_key: string,
    language?: string
  ) =>
    request<{ guide: import("./types").WriteSectionGuide }>(
      `/projects/${id}/library/${docId}/write-section/guide`,
      { method: "POST", body: JSON.stringify({ stage_key, language }) },
      token
    ),
  writeSectionDraft: (
    token: string,
    id: number,
    docId: number,
    data: {
      stage_key: string;
      answers: Record<string, string>;
      save_as_learning_note?: boolean;
      language?: string;
    }
  ) =>
    request<{
      draft: string;
      source: string;
      ai_used: boolean;
      learning_note_id?: number | null;
      integrity_notice: string;
    }>(
      `/projects/${id}/library/${docId}/write-section/draft`,
      { method: "POST", body: JSON.stringify(data) },
      token
    ),
  runBenchmark: (
    token: string,
    id: number,
    data?: { document_ids?: number[] | null; language?: string }
  ) =>
    request<import("./types").BenchmarkResult>(
      `/projects/${id}/benchmark`,
      { method: "POST", body: JSON.stringify(data || {}) },
      token
    ),
  runSynthesis: (
    token: string,
    id: number,
    data?: { document_ids?: number[] | null; language?: string }
  ) =>
    request<import("./types").SynthesisDashboard>(
      `/projects/${id}/synthesis/dashboard`,
      { method: "POST", body: JSON.stringify(data || {}) },
      token
    ),
};
