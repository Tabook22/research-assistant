import { lazy, Suspense } from "react";
import { Navigate, Route, Routes, useLocation, useParams, Link } from "react-router-dom";
import {panelPermission} from './access';
import {useI18n} from './i18n/I18nContext';
const AdminPage=lazy(()=>import('./pages/AdminPage'));
const AccountPage=lazy(()=>import('./pages/AccountPage'));
const PapersPage=lazy(()=>import('./pages/PapersPage'));
import { useAuth } from "./auth";
const ResearchDeskPage = lazy(() => import("./pages/ResearchDeskPage"));
const PaperReviewPage = lazy(() => import("./pages/PaperReviewPage"));
const AuthPage = lazy(() => import("./pages/AuthPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const LibraryPage = lazy(() => import("./pages/LibraryPage"));
const NewProjectPage = lazy(() => import("./pages/NewProjectPage"));
const WorkspacePage = lazy(() => import("./pages/WorkspacePage"));

function Protected({ children, grant, admin=false }: { children: React.ReactNode;grant?:string;admin?:boolean }) {
  const { token, loading, user, can, error } = useAuth();
  const location=useLocation();const params=useParams();const {lang}=useI18n();
  if (loading) return <div className="container muted">Loading…</div>;
  if (!token) return <Navigate to="/auth" replace />;
  if(error)return <main className="container account-main"><h1>{lang==='ar'?'تعذر تحميل الحساب':'Could not load your account'}</h1><p>{error}</p><button className="btn" onClick={()=>window.location.reload()}>{lang==='ar'?'إعادة المحاولة':'Retry'}</button></main>;
  if(user?.must_change_password&&location.pathname!=='/account')return <Navigate to="/account" replace/>;
  const needed=grant==='panel'?panelPermission(params.panel||''):grant;
  if((admin&&!user?.is_superuser)||(needed&&!(needed==='paper_review'?(can('paper_review')||can('paper_evaluate')):can(needed))))return <main className="container account-main"><h1>{lang==='ar'?'هذه الصفحة غير متاحة لحسابك':'This page is not enabled for your account'}</h1><p>{lang==='ar'?'تواصل مع مسؤول النظام لتغيير صلاحياتك.':'Ask your administrator to change your page permissions.'}</p><Link className="btn" to="/">{lang==='ar'?'العودة لمساحتي':'Back to my workspace'}</Link></main>;
  return <>{children}</>;
}

function Home(){const {can,user}=useAuth();return can('paper_evaluate')&&user?.permissions.every(grant=>grant==='paper_evaluate')?<Navigate to="/review" replace/>:<DashboardPage/>;}

export default function App() {
  return (
    <Suspense fallback={<div className="container muted" role="status">Loading workspace…</div>}>
    <Routes>
      <Route path="/account" element={<Protected><AccountPage/></Protected>}/>
      <Route path="/papers" element={<Protected><PapersPage/></Protected>}/>
      <Route path="/admin" element={<Protected admin><AdminPage/></Protected>}/>
      <Route path="/desk" element={<Protected grant="research_desk"><ResearchDeskPage /></Protected>} />
      <Route path="/projects/:id/desk" element={<Protected grant="research_desk"><ResearchDeskPage /></Protected>} />
      <Route path="/review" element={<Protected grant="paper_review"><PaperReviewPage /></Protected>} />
      <Route path="/projects/:id/review" element={<Protected grant="paper_review"><PaperReviewPage /></Protected>} />
      <Route path="/auth" element={<AuthPage />} />
      <Route
        path="/"
        element={
          <Protected>
            <Home />
          </Protected>
        }
      />
      <Route
        path="/projects/new"
        element={
          <Protected grant="create_projects">
            <NewProjectPage />
          </Protected>
        }
      />
      <Route
        path="/projects/:id"
        element={
          <Protected grant="workspace">
            <WorkspacePage />
          </Protected>
        }
      />
      {/* Full-page / new-tab views of each workspace section */}
      <Route
        path="/projects/:id/panel/:panel"
        element={
          <Protected grant="panel">
            <WorkspacePage />
          </Protected>
        }
      />
      <Route
        path="/projects/:id/library"
        element={
          <Protected grant="library">
            <LibraryPage />
          </Protected>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
    </Suspense>
  );
}
