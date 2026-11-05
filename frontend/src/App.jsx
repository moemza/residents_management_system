import { Routes, Route, useLocation, useNavigate, Link, Navigate } from "react-router-dom";
import { useCallback, useEffect, useRef, useState } from "react";
import Home from "./pages/Home";
import AddResident from "./pages/AddResident";
import EditResident from "./pages/EditResident";
import ViewResident from "./pages/ViewResident";
import SearchResident from "./pages/SearchResident";
import Residents from "./pages/Residents";
import Login from "./pages/Login";
import Toast from "./components/Toast";
import ErrorBoundary from "./components/ErrorBoundary";
import AppNavigation from "./components/AppNavigation";
import { useToast } from "./hooks/useToast";
import { getAuthStatus } from "./api/residents";
import { clearCsrfToken } from "./auth";

export default function App() {
  const location = useLocation();
  const navigate = useNavigate();
  const mainRef = useRef(null);
  const firstRender = useRef(true);
  const { toast, showToast, clearToast } = useToast();
  const [authRequired, setAuthRequired] = useState(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [authProblem, setAuthProblem] = useState("");

  const refreshAuth = useCallback(async () => {
    try {
      const data = await getAuthStatus();
      setAuthRequired(true);
      setAuthenticated(Boolean(data.authenticated));
      setAuthProblem("");
    } catch {
      clearCsrfToken();
      setAuthRequired(true);
      setAuthenticated(false);
      setAuthProblem("Could not verify your session. Check the connection and sign in again.");
    }
  }, []);

  useEffect(() => {
    refreshAuth();
  }, [refreshAuth]);

  useEffect(() => {
    const handleUnauthorized = () => {
      clearCsrfToken();
      setAuthenticated(false);
      setAuthProblem("Your session expired. Sign in again to continue.");
    };
    const handleAuthenticated = () => {
      setAuthenticated(true);
      setAuthProblem("");
    };
    window.addEventListener("residents:unauthorized", handleUnauthorized);
    window.addEventListener("residents:authenticated", handleAuthenticated);
    return () => {
      window.removeEventListener("residents:unauthorized", handleUnauthorized);
      window.removeEventListener("residents:authenticated", handleAuthenticated);
    };
  }, []);

  useEffect(() => {
    if (location.state?.success) {
      showToast(location.state.success, "success");
      navigate(`${location.pathname}${location.search}`, { replace: true, state: {} });
    }
  }, [location, showToast, navigate]);

  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false;
      return;
    }
    mainRef.current?.focus();
  }, [location.pathname]);

  const requireAuth = (element) => {
    if (authRequired === null) {
      return (
        <div className="container mt-5 text-center" role="status" aria-live="polite">
          <div className="spinner-border" aria-hidden="true" />
          <span className="visually-hidden">Checking administrator session…</span>
        </div>
      );
    }
    if (!authenticated) {
      return (
        <Navigate
          to="/login"
          replace
          state={{ from: `${location.pathname}${location.search}` }}
        />
      );
    }
    return element;
  };

  const handleSignOut = () => {
    setAuthenticated(false);
    setAuthProblem("");
  };

  return (
    <>
      <a className="visually-hidden-focusable" href="#main-content">
        Skip to main content
      </a>
      {authenticated && (
        <AppNavigation
          onSignedOut={handleSignOut}
          onError={(message) => showToast(message, "danger")}
        />
      )}
      {toast && <Toast message={toast.message} type={toast.type} onClose={clearToast} />}
      <main id="main-content" className="page-shell" ref={mainRef} tabIndex={-1}>
        {authProblem && location.pathname === "/login" && (
          <div className="container pt-3">
            <div className="alert alert-warning" role="status">{authProblem}</div>
            <button type="button" className="btn btn-outline-secondary btn-sm" onClick={refreshAuth}>
              Retry session check
            </button>
          </div>
        )}
        <ErrorBoundary>
          <Routes>
            <Route
              path="/login"
              element={<Login authenticated={authenticated} />}
            />
            <Route path="/" element={requireAuth(<Home />)} />
            <Route path="/residents" element={requireAuth(<Residents />)} />
            <Route path="/add-resident" element={requireAuth(<AddResident />)} />
            <Route path="/edit-resident/:id" element={requireAuth(<EditResident />)} />
            <Route path="/view-resident/:id" element={requireAuth(<ViewResident />)} />
            <Route path="/search" element={requireAuth(<SearchResident />)} />
            <Route
              path="*"
              element={
                <div className="container mt-5 text-center">
                  <h1 className="h3">Page not found</h1>
                  <p>The address you entered does not match a page in this application.</p>
                  <Link to="/" className="btn btn-primary mt-3">Go Home</Link>
                </div>
              }
            />
          </Routes>
        </ErrorBoundary>
      </main>
    </>
  );
}
