# ResearchGuide AI

A full-stack **scientific research assistant** that guides researchers from initial idea to methodologically aligned manuscript—without inventing references, data, or results.

This is a **structured research-development platform**, not a plain chatbot:

- Scientific guidance (18 research stages)
- Research project management & profile
- AI assistance with approval workflow
- Literature search (OpenAlex / Crossref) & reference manager
- Methodological alignment checker
- Document upload & export
- Integrity protection (approved decisions cannot be silently changed)

## Stack

| Layer | Technology |
|--------|------------|
| Backend | Python, FastAPI, SQLAlchemy, Pydantic, Alembic-ready |
| Database | SQLite (portable; SQLAlchemy allows future PostgreSQL) |
| Frontend | React, TypeScript, Vite |
| AI | SpaceXAI / xAI (`XAI_API_KEY`, model `grok-4.5`) |

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv

# Windows
.\.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # or: cp .env.example .env
```

Edit `.env` and set:

```env
XAI_API_KEY=your_key_from_console.x.ai
SECRET_KEY=long-random-string
```

Without `XAI_API_KEY`, chat runs in **offline guidance mode** (welcome + profile/structure help; no LLM drafts).

Start the API:

```bash
cd backend
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

- Health: http://127.0.0.1:8000/api/health  
- OpenAPI: http://127.0.0.1:8000/docs  

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:3000 (Vite proxies `/api` to the backend).

### 3. Tests

```bash
cd backend
.\.venv\Scripts\pytest -q
```

## Research desk

Open **Research desk** from the dashboard or a project. Its tabs connect original-text search, grounded questions, an evidence notebook, related-study discovery, comparisons, supported writing and a project research brief.

- **Sources:** paper reviews, exact library sections and document-upload chunks are indexed per project. New paper reviews retain the original upload and its page-level text. Older reviews retain their existing extracted text and section ranges; re-upload to enable original-file viewing. Draft edits are never indexed as source findings.
- **Retrieval:** BM25 keyword matching supports normalized Arabic and English. With the configured AI, bounded/cached query expansion adds translations and synonyms. Optional `EMBEDDING_MODEL`, `EMBEDDING_BASE_URL`, and `EMBEDDING_API_KEY` enable cached vector search and reciprocal-rank fusion. Without them, the UI reports keyword or expanded-keyword mode accurately. At most 128 new passage vectors are generated per task; partial semantic coverage is reported.
- **Grounding:** answers and comparisons use retrieved excerpts, not every page of every document. Server validation rejects unknown citation IDs and nonmatching quotation text, and omits generated statements with no valid quotation. Matching quotations are anchors, not proof that the interpretation is correct. Inspect context before accepting a conclusion.
- **Evidence:** saved claims include exact quotes, source locations, immutable source snapshots, researcher-assigned relationships and notes. Link a source to a saved reference before capturing evidence to retain its bibliographic record in the snapshot.
- **Discovery:** OpenAlex, Crossref and Semantic Scholar run concurrently. DOI/title duplicates are merged; metadata-only and abstract coverage are labeled. Provider failures/rate limits are visible. Successful full discovery runs can be reused for six hours. Search queries are sent to these services only for discovery; source text is sent to the configured AI/embedding services for their requested tasks.
- **References:** save discovered records, check Crossref DOI metadata and available post-publication notices, and export RIS for Zotero's File → Import workflow. Checks are timestamped and stored; identical checks can be reused for 24 hours. Metadata checks never mark a source as full-text-reviewed or a claim as proven. Unconfirmed author strings are exported as notes rather than guessed person names.
- **Writing:** select evidence, generate a proposal, explicitly keep it as a separate draft, edit/save versions, and export Word or Markdown with an evidence appendix. Evidence markers are not a finished citation-style bibliography. Your manual edits are not automatically fact-checked. RIS supports reference-manager transfer; live Zotero synchronization is not provided.
- **Memory:** the saved research brief supplies researcher decisions, scope and open questions to grounded tasks; it is not treated as published evidence.
- **Jobs:** task inputs/results/status are stored; the UI polls and can reopen or cancel tasks. Cancellation prevents saving a late response but may not abort an upstream request already in flight. Restarted unfinished jobs are marked failed with a retry action, rather than silently lost. The runner is intended for a single local API process; a multi-worker deployment needs a dedicated shared job queue.

The desk uses additive tables initialized by the existing startup workflow. Indexing updates only changed source passages, unchanged embeddings are reused, and frontend pages load on demand. Keyword retrieval requires no additional service. Scanned pages, figures and image-only tables still require separate OCR/visual review; absent text is not fabricated.

## Paper review and revision

Open **Paper review** from the dashboard, or from a project workspace. Choose a project and upload a searchable PDF, DOCX, or UTF-8 TXT paper (up to the configured upload size, 200 PDF pages, and 240,000 extracted characters).

- The original extracted text is saved separately from drafts and divided using English/Arabic headings. Check automatic section boundaries against the source.
- AI analysis explains the main ideas, research problem (explicit or inferred), strengths, concrete improvements, and claims needing verification. Analysis is stored in the language selected during upload.
- Select a section to read its source, discuss it, request a proposed revision, and edit your working draft. AI proposals require an explicit action to move them into the editor; saving creates a retrievable version.
- Export a Markdown working copy using saved drafts where available and original text elsewhere. Unsaved edits must be saved first.
- AI calls use the configured xAI-compatible provider (`XAI_API_KEY`, `XAI_BASE_URL`, `AI_MODEL`). Without it, extraction, reading, manual editing, version history and export still work. Failed AI calls do not replace saved analysis or drafts.
- This is text analysis: diagrams, scanned pages and image-based tables require separate visual review. External citations are flagged for checking, not automatically verified. Papers longer than the overview context limit receive an explicit partial-coverage notice; remaining sections can be analyzed individually.

Review records live in the additive `paper_reviews` table, created through the existing application startup table initialization. Every endpoint uses the project's existing access checks; edits use an optimistic version to prevent another tab from silently overwriting a draft.

Paper analysis saves an overview first (`POST .../analyze?overview_only=true`), then saves each section through its own versioned request. The page shows progress and supports pausing after the active step. Continue analysis skips completed steps, including after a page reload or provider failure. Keep the page open while analysis runs. Refresh retains older findings while recording which section updates remain pending. Provider failures distinguish timeout, connection, quota, access, and invalid responses; diagnostics log only exception type and HTTP status. An individual provider request has a 120-second timeout.

## Scientific criteria assessment

In **Paper review**, choose **Scientific criteria**, select the actual research design and original text or saved working copy, then assess. Eight design profiles cover general, conceptual/legal, quantitative, observational health, qualitative, systematic review, randomized trial and proposal papers. Each criterion includes a bilingual explanation, practical improvement guidance and relevant primary guidance links.

This is an application-authored reporting/reasoning rubric informed by EQUATOR, ICMJE, PRISMA 2020, STROBE, CONSORT/SPIRIT 2025, SRQR and TOP 2025. It is not their complete official checklist, a validated scientific quality scale or publication certification. Health reporting guidelines are applied only to relevant research designs.

The server computes equal-weight documented fulfilment: met = 2, partial = 1, not identified = 0; justified conditional exemptions are excluded. Unchecked and unassessable criteria earn no documented points and remain explicit uncertainties. The report displays coverage and an uncertainty range without an arbitrary pass threshold. Positive judgments require excerpts matched against saved text; this validates location, not the scientific correctness of a claim. References, statistics, novelty, ethics approvals and image-only content require independent review.

Matched excerpts open and highlight the saved passage. Original PDF page links appear only when the excerpt is also matched to that extracted page. Missing criteria link to a clearly identified suggested insertion section, where the researcher can discuss, request a proposal or edit manually. Draft changes invalidate working-copy findings; source text remains unchanged. Reports export as Markdown.

Assessments save each three-criterion batch and resume after provider failure or a pause. Whole-paper scoring is limited to 110,000 extracted characters; longer manuscripts are rejected before replacing any existing report rather than silently truncated. Existing project ownership, admin access and paper-review permissions apply to all criteria endpoints.

## Administrator AI providers and task profiles

Open **Administration → AI providers & models** (`/admin?tab=ai`). Analysis and discussion have independent provider, model identifier, API key and output-token ceilings. Analysis includes paper review, scientific criteria, comparisons and proposed revisions; discussion includes section questions, research-desk answers and workspace conversations. Settings apply to all users and new requests immediately. Existing results are retained; in-flight requests keep the profile loaded at their start.

Supported providers: OpenAI (native Responses API), Anthropic/Claude (native Messages API), Google/Gemini, xAI/Grok, DeepSeek and Mistral (compatible chat APIs). Provider endpoints are fixed. The authenticated model discovery button retrieves account-visible versions from the selected provider; it does not claim every listed model supports this workflow. Exact manual model IDs are also accepted. The connection test checks a synthetic JSON response and can incur provider charges; it sends no paper text and does not save configuration. No automatic provider fallback or model upgrade occurs.

Existing deployment settings remain the fallback until an administrator saves each task profile. Deployment keys are usable only with their original provider. A blank key retains a previously saved key for that same task/provider; selecting a different provider requires its own key. Keys are encrypted in the database using a Fernet key derived from `SECRET_KEY`, never returned by the API, and never put in browser storage. Keep `SECRET_KEY` stable and back it up privately alongside the database; changing it requires re-entering saved provider keys. API permissions and account billing remain the administrator's responsibility. Embeddings use their separate existing configuration.

## Whole-paper improved proposals

In **Paper review**, open **Improved whole-paper proposal**, choose the research design and source basis, optionally describe revision priorities, then generate. The analysis model first plans an ordered manuscript and provisional research problem, then writes each planned section through a separate versioned request. Every original section must be mapped into the plan; newly proposed sections are clearly identified. No source text or saved working draft is overwritten.

The view compares source material with proposed wording and records changes, missing author input and verification needs. It supports pause/resume, Markdown export (including partial/stale notices), and export of the immediately previous proposal. Source edits invalidate unfinished proposals. Input is limited to 110,000 characters without silent truncation; total generated section text is limited to 105,000 characters so independent reassessment remains within the criteria context budget.

After generation, **Create independent copy & reassess** creates a separate private paper review with the proposed title, ordered sections, origin link, AI provenance warning and outstanding-input list. Repeated creation reopens the same copy, preserving any researcher edits. The copy opens the scientific criteria screen using the selected design; scoring is a separate researcher-triggered task, not an automatic assertion of compliance.

Rewriting cannot supply missing empirical data, real findings, verified citations or ethics approvals. Prompts require explicit inline input/verification placeholders and prohibit invented evidence, references or guarantees of publication or complete scientific compliance. Generated statements still require human verification. Failed or invalid requests retain completed checkpoints and previous proposals. The feature uses the existing project ownership and paper-review permissions.

## Core workflows

1. Register / sign in  
2. **New project** wizard (idea, field, document type, population, language)  
3. Workspace: stage navigator · AI chat · profile · questions/objectives · alignment · literature · documents · export  
4. Approve research questions before treating them as fixed  
5. **Check alignment** across problem → gap → aim → objectives → questions → … → analysis  
6. Export Markdown/JSON project summary  

## Architecture (backend)

```
backend/app/
  api/           # FastAPI routes
  core/          # security, deps
  models/        # SQLAlchemy entities
  schemas/       # Pydantic I/O
  services/      # business logic, AI, alignment, literature, docs, export
  prompts/       # master system prompt (never exposed to frontend)
```

AI flow: **suggestion → validation → researcher review → approval → DB update**. Approved questions cannot be edited without explicitly changing approval status.

## Research integrity

- No fabricated citations, DOIs, or results  
- Proposals/protocols use future tense; results only from real data  
- Unverified references flagged  
- Alignment checker surfaces causal/design mismatches, unlinked instruments, missing analysis, etc.  

## Environment variables

See `backend/.env.example` for:

- `DATABASE_URL`, `UPLOAD_DIR`, `EXPORT_DIR`
- `CORS_ORIGINS`
- `XAI_API_KEY`, `XAI_BASE_URL`, `AI_MODEL`
- `OPENALEX_MAILTO`, `CROSSREF_MAILTO`

## License

Use and adapt for academic research support. Researcher remains the author and final decision-maker.
#   r e s e a r c h - a s s i s t a n t  
 