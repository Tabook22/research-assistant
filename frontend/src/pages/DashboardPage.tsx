import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import Icon from "../components/Icon";
import LanguageSwitcher from "../components/LanguageSwitcher";
import { useI18n } from "../i18n/I18nContext";
import { documentTypeLabel } from "../i18n/translations";
import type { ProjectSummary, StageDefinition } from "../types";
import {projectHome} from '../access';

export default function DashboardPage() {
 const { token, user, logout, can } = useAuth();
 const { t, lang } = useI18n();
 const ar = lang === "ar";
 const copy = (en: string, arabic: string) => ar ? arabic : en;
 const [projects, setProjects] = useState<ProjectSummary[]>([]);
 const [stages, setStages] = useState<StageDefinition[]>([]);
 const [error, setError] = useState<string | null>(null);
 const [loading, setLoading] = useState(true);
 const [query, setQuery] = useState("");
 const [filter, setFilter] = useState("all");
 const [sort, setSort] = useState("recent");
 const [attempt, setAttempt] = useState(0);
 useEffect(() => {
  if (!token) return;
  let active = true;
  setLoading(true); setError(null);
  api.listProjects(token).then((data) => { if (active) setProjects(data); })
   .catch((e) => { if (active) setError(e.message); })
   .finally(() => { if (active) setLoading(false); });
  api.stages(token).then((data) => { if (active) setStages(data); }).catch(() => {});
  return () => { active = false; };
 }, [token, attempt]);
 const progress = (p: ProjectSummary) => Math.min(100, Math.max(0, p.completion_percent || 0));
 const completed = projects.filter((p) => progress(p) === 100).length;
 const shown = projects.filter((p) => `${p.working_title} ${p.research_field || ""} ${documentTypeLabel(lang, p.document_type)}`.toLocaleLowerCase().includes(query.toLocaleLowerCase().trim()) && (filter === "all" || (filter === "complete" ? progress(p) === 100 : progress(p) < 100)))
  .sort((a,b) => sort === "title" ? a.working_title.localeCompare(b.working_title, lang) : sort === "progress" ? progress(b)-progress(a) : Date.parse(b.updated_at)-Date.parse(a.updated_at));
 const firstName = user?.full_name?.trim().split(/\s+/)[0];
 return <div className="dashboard-shell">
  <a className="skip-link" href="#main-content">{copy("Skip to content", "انتقل إلى المحتوى")}</a>
  <aside className="dashboard-sidebar">
   <Link to="/" className="brand"><span className="brand-mark"><Icon name="book" /></span><span>ResearchGuide <small>AI</small></span></Link>
   <div className="sidebar-caption">{copy("YOUR WORKSPACE", "مساحة عملك")}</div>
   <nav className="sidebar-nav" aria-label={copy("Main navigation", "التنقل الرئيسي")}>
    <Link to="/" className="sidebar-link active" aria-current="page"><Icon name="grid" />{copy("Overview", "نظرة عامة")}</Link>
    {can('create_projects')&&<Link to="/projects/new" className="sidebar-link"><Icon name="plus" />{t("dash.newProject")}</Link>}
    {can('research_desk')&&<Link to="/desk" className="sidebar-link"><Icon name="search" />{copy("Research desk", "مكتب البحث")}</Link>}
    {can('paper_review')&&<Link to="/review" className="sidebar-link"><Icon name="spark" />{copy("Paper review", "تحليل ورقة بحثية")}</Link>}
    <Link to="/papers" className="sidebar-link"><Icon name="book"/>{copy('My papers & uploads','أوراقي وملفاتي')}</Link>
    {user?.is_superuser&&<Link to="/admin" className="sidebar-link"><Icon name="shield"/>{copy('Administration','الإدارة')}</Link>}
    <Link to="/account" className="sidebar-link"><Icon name="grid"/>{copy('Account settings','إعدادات الحساب')}</Link>
    <a href="#research-guide" className="sidebar-link"><Icon name="book" />{copy("Research guide", "دليل البحث")}</a>
   </nav>
   <div className="sidebar-note"><Icon name="spark" /><h3>{copy("Small steps. Meaningful discoveries.", "فكرة صغيرة، أثر كبير.")}</h3><p>{copy("Bring your next idea to life with a little guidance along the way.", "طوّر فكرتك خطوة بخطوة مع إرشاد علمي واضح.")}</p>{can("create_projects")&&<Link to="/projects/new">{copy("Start something new", "ابدأ رحلتك")}<Icon name="arrow" size={16} /></Link>}</div>
   <div className="sidebar-user"><span className="avatar">{user?.full_name?.trim().charAt(0).toUpperCase() || "R"}</span><div><strong>{user?.full_name}</strong><small>{copy("Researcher workspace", "مساحة الباحث")}</small></div><button className="icon-button" onClick={logout} aria-label={t("common.signOut")} title={t("common.signOut")}><Icon name="logout" size={18} /></button></div>
  </aside>
  <div className="dashboard-content">
   <header className="dashboard-topbar"><span>{copy("Workspace", "مساحة العمل")}<span className="breadcrumb-separator">/</span><strong>{copy("Overview", "نظرة عامة")}</strong></span><LanguageSwitcher /></header>
   <main id="main-content" className="dashboard-main">
    <section className="dashboard-heading"><div><div className="eyebrow">{copy("A LITTLE CLARITY FOR YOUR NEXT BIG IDEA", "مساحة للأفكار الكبيرة")}</div><h1>{copy("Welcome back", "أهلاً بك")}{firstName ? `, ${firstName}` : ""}<span className="greeting-dot">.</span></h1><p className="muted">{copy("Let’s turn your curiosity into research that makes a difference.", "لنواصل تحويل أفكارك إلى بحث علمي متين.")}</p></div>{can("create_projects")&&<Link className="btn btn-primary" to="/projects/new"><Icon name="plus" size={18} />{t("dash.newProject")}</Link>}</section>
    <section className="dashboard-stats" aria-label={copy("Project statistics", "إحصائيات المشاريع")}>
     {[
      {icon: "book" as const, label: copy("Total projects", "جميع المشاريع"), value: projects.length, hint: copy("Your ideas, all in one place", "أفكارك في مكان واحد")},
      {icon: "clock" as const, label: copy("In progress", "قيد التطوير"), value: projects.length-completed, hint: copy("A step closer to your goal", "خطوة أقرب إلى هدفك")},
      {icon: "check" as const, label: copy("Completed projects", "المشاريع المكتملة"), value: completed, hint: copy("Projects at 100% progress", "مشاريع بلغت نسبة ١٠٠٪")},
     ].map((s,i) => <div className="stat-card" key={s.label}><div className={`stat-icon tone-${i}`}><Icon name={s.icon} /></div><div><span>{s.label}</span><strong>{loading || error ? "—" : s.value}</strong><small>{s.hint}</small></div></div>)}
    </section>
    <div className="dashboard-columns"><section className="projects-section" aria-labelledby="projects-heading">
     <div className="section-heading"><h2 id="projects-heading">{t("dash.title")} <span className="count-pill">{projects.length}</span></h2></div>
     <div className="project-tools"><div className="search-field"><Icon name="search" size={18} /><input aria-label={copy("Search projects", "ابحث في المشاريع")} placeholder={copy("Search projects or fields…", "ابحث عن مشروع أو مجال…")} value={query} onChange={(e) => setQuery(e.target.value)} /></div><select aria-label={copy("Sort projects", "ترتيب المشاريع")} value={sort} onChange={(e) => setSort(e.target.value)}><option value="recent">{copy("Recently updated", "الأحدث أولاً")}</option><option value="title">{copy("Project title", "العنوان")}</option><option value="progress">{copy("Most progress", "نسبة الإنجاز")}</option></select></div>
     <div className="project-filters">{[["all", copy("All projects", "جميع المشاريع")], ["active", copy("In progress", "قيد التطوير")], ["complete", copy("Completed", "مكتملة")]].map(([key,label]) => <button type="button" key={key} aria-pressed={filter === key} className={filter === key ? "active" : ""} onClick={() => setFilter(key)}>{label}</button>)}</div>
     {error && <div className="error stack" role="alert">{error}<button className="btn" onClick={() => setAttempt((n) => n+1)}>{copy("Try again", "حاول مرة أخرى")}</button></div>}
     {loading && <div className="project-grid" role="status" aria-label={t("dash.loading")}>{[1,2].map((n) => <div key={n} className="project-skeleton"><span /><span /><span /></div>)}</div>}
     {!loading && !error && shown.length === 0 && <div className="project-empty"><span className="empty-icon"><Icon name={projects.length ? "search" : "book"} size={30} /></span><h3>{projects.length ? copy("No matching projects", "لا توجد نتائج") : copy("Every discovery starts with a question", "كل بحث رائع يبدأ بسؤال")}</h3><p>{projects.length ? copy("Try another search or adjust your filters.", "جرّب كلمة بحث أو تصفية أخرى.") : t("dash.empty")}</p>{projects.length ? <button className="btn" onClick={() => { setQuery(""); setFilter("all"); }}>{copy("Clear filters", "مسح التصفية")}</button> : can("create_projects")&&<Link className="btn btn-primary" to="/projects/new"><Icon name="plus" size={17} />{copy("Create your first project", "أنشئ مشروعك الأول")}</Link>}</div>}
     {!loading && !error && <div className="project-grid">{shown.map((p) => { const stage = stages.find((s) => s.key === p.current_stage); return <Link key={p.id} to={projectHome(p.id,can)} className="card project-card"><div className="project-card-top"><span className="project-symbol"><Icon name="book" /></span><span className={`project-status ${progress(p) === 100 ? "is-complete" : ""}`}><i />{progress(p) === 100 ? copy("Completed", "مكتمل") : copy("In progress", "قيد التطوير")}</span></div><span className="project-type">{documentTypeLabel(lang,p.document_type)}</span><h3>{p.working_title}</h3><p className="project-field">{p.research_field || t("common.fieldNotSet")}</p><div className="project-progress-label"><span>{copy("Research progress", "تقدم البحث")}</span><strong>{progress(p)}%</strong></div><div className="progress-bar" role="progressbar" aria-label={copy("Research progress", "تقدم البحث")} aria-valuenow={progress(p)} aria-valuemin={0} aria-valuemax={100}><span style={{width: `${progress(p)}%`}} /></div><div className="project-stage">{stage ? (ar ? stage.label_ar : stage.label_en) : p.current_stage.replace(/_/g," ")}</div><div className="project-card-footer"><span>{Number.isNaN(Date.parse(p.updated_at)) ? "" : new Intl.DateTimeFormat(ar ? "ar-OM" : "en-GB", {day:"numeric",month:"short",year:"numeric"}).format(new Date(p.updated_at))}</span><span>{copy("Open project", "افتح المشروع")}<Icon name="arrow" size={16} /></span></div></Link>; })}</div>}
    </section><aside className="dashboard-guide" id="research-guide"><div className="guide-card"><span className="eyebrow">{copy("FROM IDEA TO IMPACT", "من الفكرة إلى الأثر")}</span><h2>{copy("Your research journey, made clearer.", "رحلتك البحثية، خطوة بخطوة.")}</h2><p>{copy("A guided path through 18 research stages, at your own pace.", "إرشاد منظم خلال ١٨ مرحلة بحثية.")}</p><ol className="journey-list">{[[copy("Shape your idea", "شكّل فكرتك"),copy("Define the problem. Find your question.", "حدد المشكلة وصغ أسئلتك.")],[copy("Build your foundation", "ابنِ أساساً متيناً"),copy("Connect evidence with a sound method.", "اربط الأدلة بالمنهج المناسب.")],[copy("Write with confidence", "اكتب بثقة"),copy("Develop your manuscript, step by step.", "طوّر مخطوطتك خطوة بخطوة.")]].map(([title,sub],i) => <li key={title}><span>{String(i+1).padStart(2,"0")}</span><div><strong>{title}</strong><p>{sub}</p></div></li>)}</ol></div><div className="integrity-note"><Icon name="shield" size={22} /><div><h3>{copy("Your research. Your decisions.", "بحثك. قراراتك.")}</h3><p>{copy("You stay the author. Review and approve AI suggestions before they become part of your research.", "أنت المؤلف وصاحب القرار. راجع اقتراحات الذكاء الاصطناعي قبل اعتمادها.")}</p></div></div></aside></div>
    <footer className="dashboard-footer">{copy("A thoughtful space for meaningful research.", "صُمم لدعم التفكير المتأني والبحث الهادف.")}<span>ResearchGuide AI</span></footer>
   </main>
  </div>
 </div>;
}
