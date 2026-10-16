import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import LanguageSwitcher from "../components/LanguageSwitcher";
import ResearchLibrary from "../components/ResearchLibrary";
import { useI18n } from "../i18n/I18nContext";
import { documentTypeLabel, type TranslationKey } from "../i18n/translations";
import { buildLibraryLabels } from "../lib/libraryLabels";
import type { Project, StageDefinition } from "../types";

export default function LibraryPage() {
  const { id } = useParams();
  const projectId = Number(id);
  const { token, logout, user } = useAuth();
  const { t, lang } = useI18n();
  const [project, setProject] = useState<Project | null>(null);
  const [stages, setStages] = useState<StageDefinition[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const labels = useMemo(() => buildLibraryLabels((k) => t(k as TranslationKey)), [t]);

  const load = useCallback(async () => {
    if (!token || !projectId) return;
    setLoading(true);
    setError(null);
    try {
      const [p, st] = await Promise.all([
        api.getProject(token, projectId),
        api.stages(token),
      ]);
      setProject(p);
      setStages(st);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("ws.loadFailed"));
    } finally {
      setLoading(false);
    }
  }, [token, projectId, t]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading && !project) {
    return (
      <div className="container">
        <p className="muted">{t("common.loading")}</p>
      </div>
    );
  }

  if (!project || !token) {
    return (
      <div className="container">
        {error && <div className="error">{error}</div>}
        <p className="muted">{t("ws.loadFailed")}</p>
        <Link className="btn" to="/">
          {t("common.dashboard")}
        </Link>
      </div>
    );
  }

  return (
    <div className="app-shell library-page">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">RG</div>
          <div>
            <div style={{ fontSize: "0.95rem" }}>{labels.pageTitle}</div>
            <div className="muted" style={{ fontSize: "0.75rem", fontWeight: 400 }}>
              {project.working_title} · {documentTypeLabel(lang, project.document_type)}
            </div>
          </div>
        </div>
        <div className="topbar-actions">
          <LanguageSwitcher />
          <Link className="btn btn-primary" to={`/projects/${projectId}`}>
            {labels.backToWorkspace}
          </Link>
          <Link className="btn btn-ghost" to="/">
            {t("common.dashboard")}
          </Link>
          <button className="btn btn-ghost" type="button" onClick={logout}>
            {user?.full_name?.split(" ")[0] || t("common.signOut")}
          </button>
        </div>
      </header>

      <main className="library-page-main">
        {error && <div className="error">{error}</div>}
        <div className="library-page-intro">
          <div>
            <h1 style={{ margin: "0 0 0.35rem", fontSize: "1.35rem" }}>{labels.pageTitle}</h1>
            <p className="muted" style={{ margin: 0, maxWidth: 720 }}>
              {labels.pageSubtitle}
            </p>
          </div>
          <Link className="btn" to={`/projects/${projectId}`}>
            {labels.backToWorkspace}
          </Link>
        </div>
        <div className="library-page-body card">
          <ResearchLibrary
            token={token}
            projectId={projectId}
            stages={stages}
            labels={labels}
            uiLang={lang}
            variant="page"
          />
        </div>
      </main>
    </div>
  );
}
