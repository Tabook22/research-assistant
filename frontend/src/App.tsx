import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
const ResearchDeskPage = lazy(() => import("./pages/ResearchDeskPage"));
const PaperReviewPage = lazy(() => import("./pages/PaperReviewPage"));
const AuthPage = lazy(() => import("./pages/AuthPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const LibraryPage = lazy(() => import("./pages/LibraryPage"));
const NewProjectPage = lazy(() => import("./pages/NewProjectPage"));
const WorkspacePage = lazy(() => import("./pages/WorkspacePage"));

function Protected({ children }: { children: React.ReactNode }) {
  const { token, loading } = useAuth();
  if (loading) return <div className="container muted">Loading…</div>;
  if (!token) return <Navigate to="/auth" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Suspense fallback={<div className="container muted" role="status">Loading workspace…</div>}>
    <Routes>
      <Route path="/desk" element={<Protected><ResearchDeskPage /></Protected>} />
      <Route path="/projects/:id/desk" element={<Protected><ResearchDeskPage /></Protected>} />
      <Route path="/review" element={<Protected><PaperReviewPage /></Protected>} />
      <Route path="/projects/:id/review" element={<Protected><PaperReviewPage /></Protected>} />
      <Route path="/auth" element={<AuthPage />} />
      <Route
        path="/"
        element={
          <Protected>
            <DashboardPage />
          </Protected>
        }
      />
      <Route
        path="/projects/new"
        element={
          <Protected>
            <NewProjectPage />
          </Protected>
        }
      />
      <Route
        path="/projects/:id"
        element={
          <Protected>
            <WorkspacePage />
          </Protected>
        }
      />
      {/* Full-page / new-tab views of each workspace section */}
      <Route
        path="/projects/:id/panel/:panel"
        element={
          <Protected>
            <WorkspacePage />
          </Protected>
        }
      />
      <Route
        path="/projects/:id/library"
        element={
          <Protected>
            <LibraryPage />
          </Protected>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
    </Suspense>
  );
}
