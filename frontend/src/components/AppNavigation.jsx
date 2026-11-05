import { useEffect, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { logoutAdmin } from "../api/residents";
import { clearCsrfToken } from "../auth";

const links = [
  { to: "/", label: "Home", end: true },
  { to: "/residents", label: "Residents" },
  { to: "/add-resident", label: "Add resident" },
  { to: "/search", label: "Search" },
];

export default function AppNavigation({ onSignedOut, onError }) {
  const [expanded, setExpanded] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => setExpanded(false), [location.pathname]);

  const handleSignOut = async () => {
    setSigningOut(true);
    try {
      await logoutAdmin();
      clearCsrfToken();
      onSignedOut();
      navigate("/login", { replace: true });
    } catch (error) {
      onError("Sign out failed. Please retry.", error);
    } finally {
      setSigningOut(false);
    }
  };

  return (
    <header className="app-header">
      <nav className="navbar navbar-expand-md navbar-dark bg-primary" aria-label="Main navigation">
        <div className="container">
          <NavLink className="navbar-brand fw-semibold" to="/">
            Residents Management
          </NavLink>
          <button
            className="navbar-toggler"
            type="button"
            aria-controls="primary-navigation"
            aria-expanded={expanded}
            aria-label={expanded ? "Close navigation menu" : "Open navigation menu"}
            onClick={() => setExpanded((open) => !open)}
          >
            <span className="navbar-toggler-icon" />
          </button>
          <div
            id="primary-navigation"
            className={`collapse navbar-collapse${expanded ? " show" : ""}`}
          >
            <ul className="navbar-nav me-auto mb-2 mb-md-0">
              {links.map(({ to, label, end }) => (
                <li className="nav-item" key={to}>
                  <NavLink
                    to={to}
                    end={end}
                    className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
                  >
                    {label}
                  </NavLink>
                </li>
              ))}
            </ul>
            <button
              type="button"
              className="btn btn-outline-light btn-sm"
              onClick={handleSignOut}
              disabled={signingOut}
            >
              {signingOut ? "Signing out…" : "Sign out"}
            </button>
          </div>
        </div>
      </nav>
    </header>
  );
}
