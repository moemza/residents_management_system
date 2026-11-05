import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { loginAdmin } from "../api/residents";
import { getApiErrorMessage } from "../api/errors";
import { useDocumentTitle } from "../hooks/useDocumentTitle";

export default function Login({ authenticated }) {
  useDocumentTitle("Administrator sign in");
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (authenticated) return <Navigate to="/" replace />;

  const destination = location.state?.from;
  const safeDestination =
    typeof destination === "string" && destination.startsWith("/") && !destination.startsWith("//")
      ? destination
      : "/";

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await loginAdmin({ username: username.trim(), password });
      navigate(safeDestination, { replace: true });
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
          "Unable to sign in. Check your credentials or try again later."
        )
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container min-vh-100 d-flex align-items-center justify-content-center py-4">
      <section className="card shadow-sm w-100 login-card" aria-labelledby="login-title">
        <div className="card-body p-4 p-md-5">
          <h1 id="login-title" className="h3 mb-2">Administrator sign in</h1>
          <p className="text-secondary mb-4">
            Sign in with an administrator account provisioned by your system operator.
          </p>

          {error && <div className="alert alert-danger" role="alert">{error}</div>}

          <form onSubmit={handleSubmit} aria-busy={submitting}>
            <div className="mb-3">
              <label className="form-label" htmlFor="username">Username</label>
              <input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                autoFocus
                required
                maxLength={100}
                className="form-control"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                disabled={submitting}
              />
            </div>
            <div className="mb-4">
              <label className="form-label" htmlFor="password">Password</label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="form-control"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                disabled={submitting}
              />
            </div>
            <button type="submit" className="btn btn-primary w-100" disabled={submitting}>
              {submitting ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" aria-hidden="true" />
                  Signing in…
                </>
              ) : "Sign in"}
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}
