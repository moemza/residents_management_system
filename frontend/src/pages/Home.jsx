import { Link } from "react-router-dom";
import { useDocumentTitle } from "../hooks/useDocumentTitle";

const actions = [
  {
    to: "/residents",
    title: "Browse residents",
    detail: "Review and update resident records.",
    className: "primary",
  },
  {
    to: "/add-resident",
    title: "Add a resident",
    detail: "Create a resident record and add their details.",
    className: "success",
  },
  {
    to: "/search?type=name",
    title: "Search residents",
    detail: "Find records by name, village, qualification, or skill.",
    className: "outline-primary",
  },
];

export default function Home() {
  useDocumentTitle("Home");

  return (
    <div className="container py-4 py-md-5">
      <header className="mb-4 mb-md-5">
        <p className="text-uppercase text-secondary small fw-semibold mb-2">
          Administration workspace
        </p>
        <h1 className="display-6 fw-semibold">Residents Management System</h1>
        <p className="lead text-secondary mb-0">
          Manage resident records, qualifications, work experience, and skills.
        </p>
      </header>

      <section aria-labelledby="quick-actions-heading">
        <h2 id="quick-actions-heading" className="h4 mb-3">Quick actions</h2>
        <div className="row g-3">
          {actions.map((action) => (
            <div className="col-12 col-md-6 col-xl-4" key={action.to}>
              <article className="card h-100 shadow-sm">
                <div className="card-body d-flex flex-column align-items-start">
                  <h3 className="h5 card-title">{action.title}</h3>
                  <p className="card-text text-secondary flex-grow-1">{action.detail}</p>
                  <Link to={action.to} className={`btn btn-${action.className}`}>
                    Open
                    <span className="visually-hidden"> {action.title.toLowerCase()}</span>
                  </Link>
                </div>
              </article>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
