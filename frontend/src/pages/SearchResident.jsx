import { useState, useEffect } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { searchResidentsPage, getVillages, getQualifications } from "../api/residents";
import { getApiErrorMessage } from "../api/errors";
import { PAGE_SIZE, formatPageRange } from "../api/pagination";
import { useDocumentTitle } from "../hooks/useDocumentTitle";

const SEARCH_TYPES = [
  { value: "name", label: "Name or Surname" },
  { value: "village", label: "Village" },
  { value: "qualification", label: "Qualification" },
  { value: "skill", label: "Skill" },
];

export default function SearchResident() {
  useDocumentTitle("Search Residents");
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchType, setSearchType] = useState(searchParams.get("type") || "name");
  const [query, setQuery] = useState("");
  const [activeSearch, setActiveSearch] = useState(null);
  const [results, setResults] = useState(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(false);
  const [villages, setVillages] = useState([]);
  const [qualificationFields, setQualificationFields] = useState([]);

  useEffect(() => {
    getVillages()
      .then(setVillages)
      .catch(() => setFeedback({ type: "danger", text: "Failed to load villages." }));
    getQualifications()
      .then((q) => setQualificationFields(q.fields || []))
      .catch(() => setFeedback({ type: "danger", text: "Failed to load qualifications." }));
  }, []);

  const runSearch = async (targetPage = 0, term = query, type = searchType) => {
    const trimmed = term.trim();
    if (!trimmed) {
      setFeedback({ type: "warning", text: "Please enter a search term." });
      setResults(null);
      setTotal(0);
      return;
    }

    setLoading(true);
    setFeedback(null);
    try {
      const { items, total: matchCount } = await searchResidentsPage(trimmed, type, {
        limit: PAGE_SIZE,
        offset: targetPage * PAGE_SIZE,
      });
      setResults(items);
      setTotal(matchCount);
      setPage(targetPage);
      setActiveSearch({ query: trimmed, type });
      if (matchCount === 0) {
        setFeedback({
          type: "warning",
          text: "No residents found matching your search criteria.",
        });
      }
    } catch (err) {
      setFeedback({
        type: "danger",
        text: getApiErrorMessage(err, "Search failed. Please try again."),
      });
      setResults(null);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (event) => {
    event.preventDefault();
    runSearch(0);
  };

  const handleTypeChange = (type) => {
    setSearchType(type);
    setQuery("");
    setResults(null);
    setTotal(0);
    setPage(0);
    setFeedback(null);
    setActiveSearch(null);
    setSearchParams({ type });
  };

  return (
    <div className="container mt-5 mb-5">
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">
        <h1 className="h3 mb-0">Search Residents</h1>
        <Link to="/residents" className="btn btn-outline-secondary">Browse all residents</Link>
      </div>

      <form onSubmit={handleSearch} aria-busy={loading}>
        <div className="mb-3">
          <label className="form-label" htmlFor="search-type">Search By</label>
          <select
            id="search-type"
            className="form-select"
            value={searchType}
            onChange={(e) => handleTypeChange(e.target.value)}
          >
            {SEARCH_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </div>

        <div className="mb-3">
          <label className="form-label" htmlFor="search-term">Search Term</label>
          {searchType === "village" ? (
            <select
              id="search-term"
              className="form-select"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            >
              <option value="">Select Village</option>
              {villages.map((v) => <option key={v} value={v}>{v}</option>)}
            </select>
          ) : searchType === "qualification" ? (
            <select
              id="search-term"
              className="form-select"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            >
              <option value="">Select Qualification Field</option>
              {qualificationFields.map((f) => <option key={f} value={f}>{f}</option>)}
            </select>
          ) : (
            <input
              id="search-term"
              type="search"
              maxLength={200}
              autoComplete="off"
              className="form-control"
              placeholder={`Enter ${searchType}…`}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          )}
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? "Searching…" : "Search"}
        </button>
      </form>

      {feedback && (
        <div
          className={`alert alert-${feedback.type} mt-4`}
          role={feedback.type === "danger" ? "alert" : "status"}
          aria-live="polite"
        >
          {feedback.text}
        </div>
      )}

      {results && results.length > 0 && (
        <div className="mt-4">
          <h2 className="h4">Results ({total})</h2>
          <p className="text-muted" aria-live="polite">
            {formatPageRange(page, PAGE_SIZE, total)}
          </p>
          <ul className="list-group">
            {results.map((r) => (
              <li key={r.id} className="list-group-item d-flex flex-wrap justify-content-between align-items-center gap-2">
                <span>{r.first_name} {r.last_name} — {r.village}</span>
                <div>
                  <Link
                    to={`/view-resident/${r.id}`}
                    className="btn btn-info btn-sm me-1"
                    aria-label={`View ${r.first_name} ${r.last_name}`}
                  >
                    View
                  </Link>
                  <Link
                    to={`/edit-resident/${r.id}`}
                    className="btn btn-warning btn-sm"
                    aria-label={`Edit ${r.first_name} ${r.last_name}`}
                  >
                    Edit
                  </Link>
                </div>
              </li>
            ))}
          </ul>

          {total > PAGE_SIZE && activeSearch && (
            <nav
              aria-label="Search results pagination"
              className="d-flex justify-content-between align-items-center mt-3"
            >
              <button
                type="button"
                className="btn btn-outline-secondary btn-sm"
                disabled={page === 0 || loading}
                onClick={() => runSearch(page - 1, activeSearch.query, activeSearch.type)}
              >
                Previous
              </button>
              <span className="text-muted">
                Page {page + 1} of {Math.ceil(total / PAGE_SIZE)}
              </span>
              <button
                type="button"
                className="btn btn-outline-secondary btn-sm"
                disabled={(page + 1) * PAGE_SIZE >= total || loading}
                onClick={() => runSearch(page + 1, activeSearch.query, activeSearch.type)}
              >
                Next
              </button>
            </nav>
          )}
        </div>
      )}
    </div>
  );
}
