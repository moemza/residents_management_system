import { useState, useEffect } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { searchResidents, getVillages, getQualifications } from "../api/residents";

const SEARCH_TYPES = [
  { value: "name", label: "Name or Surname" },
  { value: "village", label: "Village" },
  { value: "qualification", label: "Qualification" },
  { value: "skill", label: "Skill" },
];

export default function SearchResident() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchType, setSearchType] = useState(searchParams.get("type") || "name");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [villages, setVillages] = useState([]);
  const [qualificationFields, setQualificationFields] = useState([]);

  useEffect(() => {
    getVillages().then(setVillages).catch(() => setMessage("Failed to load villages."));
    getQualifications()
      .then((q) => setQualificationFields(q.fields || []))
      .catch(() => setMessage("Failed to load qualifications."));
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) { setMessage("Please enter a search term."); setResults(null); return; }
    setLoading(true);
    setMessage("");
    try {
      const data = await searchResidents(query, searchType);
      setResults(data);
      if (data.length === 0) setMessage("No residents found matching your search criteria.");
    } catch {
      setMessage("Search failed. Please try again.");
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const handleTypeChange = (type) => {
    setSearchType(type);
    setQuery("");
    setResults(null);
    setMessage("");
    setSearchParams({ type });
  };

  return (
    <div className="container mt-5">
      <Link to="/" className="btn btn-secondary mb-3">Home</Link>
      <h2 className="mb-4 text-center">Search Residents</h2>

      <form onSubmit={handleSearch}>
        <div className="mb-3">
          <label className="form-label">Search By</label>
          <select className="form-select" value={searchType} onChange={(e) => handleTypeChange(e.target.value)}>
            {SEARCH_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </div>

        <div className="mb-3">
          <label className="form-label">Search Term</label>
          {searchType === "village" ? (
            <select className="form-select" value={query} onChange={(e) => setQuery(e.target.value)}>
              <option value="">Select Village</option>
              {villages.map((v) => <option key={v} value={v}>{v}</option>)}
            </select>
          ) : searchType === "qualification" ? (
            <select className="form-select" value={query} onChange={(e) => setQuery(e.target.value)}>
              <option value="">Select Qualification Field</option>
              {qualificationFields.map((f) => <option key={f} value={f}>{f}</option>)}
            </select>
          ) : (
            <input
              type="text"
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

      {message && <div className="alert alert-warning mt-4">{message}</div>}

      {results && results.length > 0 && (
        <div className="mt-4">
          <h4>Results ({results.length})</h4>
          <ul className="list-group">
            {results.map((r) => (
              <li key={r.id} className="list-group-item d-flex justify-content-between align-items-center">
                <span>{r.first_name} {r.last_name} — {r.village}</span>
                <div>
                  <Link to={`/view-resident/${r.id}`} className="btn btn-info btn-sm me-1">View</Link>
                  <Link to={`/edit-resident/${r.id}`} className="btn btn-warning btn-sm">Edit</Link>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
