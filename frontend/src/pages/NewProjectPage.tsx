import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {projectHome} from "../access";
import { api } from "../api";
import { useAuth } from "../auth";
import LanguageSwitcher from "../components/LanguageSwitcher";
import VoiceTextField from "../components/VoiceTextField";
import { useI18n } from "../i18n/I18nContext";
import {
  MATERIAL_VALUES,
  documentTypeLabel,
  materialKeyFromEn,
  type TranslationKey,
} from "../i18n/translations";

export default function NewProjectPage() {
  const { token, can } = useAuth();
  const { t, lang } = useI18n();
  const navigate = useNavigate();
  const [docTypes, setDocTypes] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    working_title: "",
    research_field: "",
    document_type: "research_proposal",
    writing_language: lang as string,
    study_context: "",
    population_summary: "",
    target_institution: "",
    target_journal: "",
    citation_style: "APA 7",
    research_idea: "",
    available_materials: [] as string[],
  });

  useEffect(() => {
    if (!token) return;
    let active = true;
    api.documentTypes(token).then((data) => { if (active) setDocTypes(data); }).catch(() => { if (active) setDocTypes([]); });
    return () => { active = false; };
  }, [token]);

  function toggleMaterial(m: string) {
    setForm((f) => ({
      ...f,
      available_materials: f.available_materials.includes(m)
        ? f.available_materials.filter((x) => x !== m)
        : [...f.available_materials, m],
    }));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      const project = await api.createProject(token, { ...form, working_title: form.working_title.trim() });
      navigate(projectHome(project.id,can));
    } catch (err) {
      setError(err instanceof Error ? err.message : t("new.failed"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">RG</div>
          <span>{t("new.title")}</span>
        </div>
        <div className="topbar-actions">
          <LanguageSwitcher />
          <Link className="btn btn-ghost" to="/">
            {t("common.back")}
          </Link>
        </div>
      </header>
      <main className="container">
        <div className="card stack project-wizard">
          <div className="wizard-step"><span>1</span>{lang === "ar" ? "ابدأ بفكرتك" : "START WITH YOUR IDEA"}</div>
          <h1>{t("new.wizard")}</h1>
          <p className="muted">{t("new.intro")}</p>
          <form className="stack" onSubmit={onSubmit}>
            <div className="field">
              <label htmlFor="new-workingTitle">{t("new.workingTitle")}</label>
                <input id="new-workingTitle"
                required
                value={form.working_title}
                onChange={(e) => setForm({ ...form, working_title: e.target.value })}
              />
            </div>
            <div className="field">
              <VoiceTextField
                label={t("new.expandIdea")}
                language={form.writing_language}
                value={form.research_idea}
                onChange={(text) => setForm({ ...form, research_idea: text })}
                placeholder={t("new.expandPlaceholder")}
              />
            </div>
            <div className="grid-2">
              <div className="field">
                <label htmlFor="new-academicField">{t("new.academicField")}</label>
                <input id="new-academicField"
                  value={form.research_field}
                  onChange={(e) => setForm({ ...form, research_field: e.target.value })}
                />
              </div>
              <div className="field">
                <label htmlFor="new-documentType">{t("new.documentType")}</label>
                <select id="new-documentType"
                  value={form.document_type}
                  onChange={(e) => setForm({ ...form, document_type: e.target.value })}
                >
                  {(docTypes.length ? docTypes : ["research_proposal"]).map((dt) => (
                    <option key={dt} value={dt}>
                      {documentTypeLabel(lang, dt)}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="new-writingLanguage">{t("new.writingLanguage")}</label>
                <select id="new-writingLanguage"
                  value={form.writing_language}
                  onChange={(e) => setForm({ ...form, writing_language: e.target.value })}
                >
                  <option value="en">{t("common.english")}</option>
                  <option value="ar">{t("common.arabic")}</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="new-citationStyle">{t("new.citationStyle")}</label>
                <select id="new-citationStyle"
                  value={form.citation_style}
                  onChange={(e) => setForm({ ...form, citation_style: e.target.value })}
                >
                  <option>APA 7</option>
                  <option>Vancouver</option>
                  <option>Harvard</option>
                  <option>IEEE</option>
                  <option>Chicago</option>
                </select>
              </div>
            </div>
            <details><summary>{lang === "ar" ? "تفاصيل إضافية (اختياري)" : "Add study details (optional)"}</summary>
            <div className="grid-2">
              <div className="field">
                <label htmlFor="new-population">{t("new.population")}</label>
                <input id="new-population"
                  value={form.population_summary}
                  onChange={(e) => setForm({ ...form, population_summary: e.target.value })}
                />
              </div>
              <div className="field">
                <label htmlFor="new-context">{t("new.context")}</label>
                <input id="new-context"
                  value={form.study_context}
                  onChange={(e) => setForm({ ...form, study_context: e.target.value })}
                />
              </div>
              <div className="field">
                <label htmlFor="new-institution">{t("new.institution")}</label>
                <input id="new-institution"
                  value={form.target_institution}
                  onChange={(e) => setForm({ ...form, target_institution: e.target.value })}
                />
              </div>
              <div className="field">
                <label htmlFor="new-journal">{t("new.journal")}</label>
                <input id="new-journal"
                  value={form.target_journal}
                  onChange={(e) => setForm({ ...form, target_journal: e.target.value })}
                />
              </div>
            </div>
            </details>
            <div>
              <div className="muted" style={{ marginBottom: "0.5rem" }}>
                {t("new.materials")}
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                {MATERIAL_VALUES.map((m) => {
                  const mk = materialKeyFromEn(m);
                  return (
                    <button
                      key={m}
                      type="button"
                      aria-pressed={form.available_materials.includes(m)}
                      className={`tab ${form.available_materials.includes(m) ? "active" : ""}`}
                      onClick={() => toggleMaterial(m)}
                    >
                      {mk ? t(mk as TranslationKey) : m}
                    </button>
                  );
                })}
              </div>
            </div>
            {error && <div role="alert" className="error">{error}</div>}
            <button className="btn btn-primary" disabled={busy} type="submit">
              {busy ? t("new.creating") : t("new.create")}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
