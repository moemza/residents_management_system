import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { getQualifications, getResidentsPage, getVillages } from "../api/residents";
import { getApiErrorMessage } from "../api/errors";
import { PAGE_SIZE, clampPage, formatPageRange } from "../api/pagination";
import { useDocumentTitle } from "../hooks/useDocumentTitle";

const EMPTY_FILTERS = {
  name: "",
  village: "",
  qualification: "",
  skill: "",
};

function readFilters(params) {
  const filters = { ...EMPTY_FILTERS };
  for (const key of Object.keys(filters)) {
    filters[key] = params.get(key) || "";
  }
  const legacyQuery = params.get("query");
  const legacyType = params.get("type");
  if (legacyQuery && !Object.values(filters).some(Boolean)) {
    const key = legacyType === "name" ? "name" : legacyType;
    if (Object.hasOwn(filters, key)) filters[key] = legacyQuery;
  }
  return filters;
}

function queryValue(value) {
  return value.trim();
}

export default function ResidentBrowser() {
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const paramsKey = searchParams.toString();
  const params = new URLSearchParams(paramsKey);
  const filters = readFilters(params);
  const sortBy = params.get("sort_by") || "id";
  const sortOrder = params.get("sort_order") || "asc";
  const pageValue = Number.parseInt(params.get("page") || "0", 10);
  const page = Number.isSafeInteger(pageValue) && pageValue >= 0 ? pageValue : 0;
  const [draft, setDraft] = useState(filters);
  const [residents, setResidents] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [referenceError, setReferenceError] = useState("");
  const [villages, setVillages] = useState([]);
  const [qualificationFields, setQualificationFields] = useState([]);
  const [reloadVersion, setReloadVersion] = useState(0);
  const requestId = useRef(0);
  const isSearchPage = location.pathname === "/search";

  useDocumentTitle(isSearchPage ? "Search Residents" : "Residents");

  useEffect(() => {
    setDraft(readFilters(new URLSearchParams(paramsKey)));
  }, [paramsKey]);

  useEffect(() => {
    Promise.all([getVillages(), getQualifications()])
      .then(([villageList, qualificationData]) => {
        setVillages(villageList);
        setQualificationFields(qualificationData.fields || []);
      })
      .catch(() => setReferenceError("Some filter suggestions could not be loaded."));
  }, []);

  const load = useCallback(async () => {
    const currentRequest = ++requestId.current;
    const currentParams = new URLSearchParams(paramsKey);
    const currentFilters = readFilters(currentParams);
    const currentSortBy = currentParams.get("sort_by") || "id";
    const currentSortOrder = currentParams.get("sort_order") || "asc";
    const rawPage = Number.parseInt(currentParams.get("page") || "0", 10);
    const currentPage = Number.isSafeInteger(rawPage) && rawPage >= 0 ? rawPage : 0;
    const activeFilters = Object.fromEntries(
      Object.entries(currentFilters)
        .map(([key, value]) => [key, queryValue(value)])
        .filter(([, value]) => value)
    );

    setLoading(true);
    setError("");
    try {
      const data = await getResidentsPage({
        ...activeFilters,
        sort_by: currentSortBy,
        sort_order: currentSortOrder,
        limit: PAGE_SIZE,
        offset: currentPage * PAGE_SIZE,
      });
      if (currentRequest !== requestId.current) return;
      const safePage = clampPage(currentPage, PAGE_SIZE, data.total);
      setResidents(data.items);
      setTotal(data.total);
      if (safePage !== currentPage) {
        currentParams.set("page", String(safePage));
        setSearchParams(currentParams, { replace: true });
      }
    } catch (err) {
      if (currentRequest !== requestId.current) return;
      setError(getApiErrorMessage(err, "Failed to load residents."));
      setResidents([]);
      setTotal(0);
    } finally {
      if (currentRequest === requestId.current) setLoading(false);
    }
  }, [paramsKey, setSearchParams]);

  useEffect(() => {
    load();
    return () => {
      requestId.current += 1;
    };
  }, [load, reloadVersion]);

  const updateParams = (updates, resetPage = true) => {
    const next = new URLSearchParams(paramsKey);
    for (const [key, value] of Object.entries(updates)) {
      if (value) next.set(key, value);
      else next.delete(key);
    }
    if (resetPage) next.delete("page");
    next.delete("type");
    next.delete("query");
    setSearchParams(next);
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    const updates = Object.fromEntries(
      Object.entries(draft).map(([key, value]) => [key, queryValue(value)])
    );
    updateParams(updates);
  };

  const reset = () => {
    setDraft(EMPTY_FILTERS);
    setSearchParams({});
  };

  const activeLabels = Object.entries(filters)
    .filter(([, value]) => queryValue(value))
    .map(([key, value]) => `${key === "name" ? "name" : key}: ${queryValue(value)}`);
  const lastPage = Math.max(0, Math.ceil(total / PAGE_SIZE) - 1);
  const setDraftField = (field) => (event) =>
    setDraft((current) => ({ ...current, [field]: event.target.value }));

  const pageLink = (target) => {
    const next = new URLSearchParams(paramsKey);
    if (target > 0) next.set("page", String(target));
    else next.delete("page");
    setSearchParams(next);
  };

  return (
    <div className="container mt-5 mb-5">
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">
        <h1 className="h3 mb-0">{isSearchPage ? "Search Residents" : "Residents"}</h1>
        <div className="d-flex flex-wrap gap-2">
          {isSearchPage ? (
            <Link to="/residents" className="btn btn-outline-secondary">Browse residents</Link>
          ) : (
            <Link to="/search" className="btn btn-outline-secondary">Search residents</Link>
          )}
          <Link to="/add-resident" className="btn btn-primary">Add Resident</Link>
          <Link to="/" className="btn btn-outline-primary">Home</Link>
        </div>
      </div>

      <form className="card mb-4" onSubmit={handleSubmit} aria-busy={loading}>
        <div className="card-header">Filter residents</div>
        <div className="card-body">
          <div className="row g-3">
            <div className="col-12 col-md-6 col-lg-3">
              <label className="form-label" htmlFor="filter-name">Name or surname</label>
              <input
                id="filter-name"
                className="form-control"
                type="search"
                maxLength={200}
                value={draft.name}
                onChange={setDraftField("name")}
              />
            </div>
            <div className="col-12 col-md-6 col-lg-3">
              <label className="form-label" htmlFor="filter-village">Village</label>
              <input
                id="filter-village"
                className="form-control"
                list="resident-villages"
                maxLength={200}
                value={draft.village}
                onChange={setDraftField("village")}
              />
              <datalist id="resident-villages">
                {villages.map((village) => <option key={village} value={village} />)}
              </datalist>
            </div>
            <div className="col-12 col-md-6 col-lg-3">
              <label className="form-label" htmlFor="filter-qualification">Qualification</label>
              <input
                id="filter-qualification"
                className="form-control"
                list="qualification-fields"
                maxLength={200}
                value={draft.qualification}
                onChange={setDraftField("qualification")}
              />
              <datalist id="qualification-fields">
                {qualificationFields.map((field) => <option key={field} value={field} />)}
              </datalist>
            </div>
            <div className="col-12 col-md-6 col-lg-3">
              <label className="form-label" htmlFor="filter-skill">Skill</label>
              <input
                id="filter-skill"
                className="form-control"
                type="search"
                maxLength={200}
                value={draft.skill}
                onChange={setDraftField("skill")}
              />
            </div>
          </div>
          <div className="row g-3 align-items-end mt-1">
            <div className="col-12 col-sm-6 col-md-4">
              <label className="form-label" htmlFor="sort-by">Sort by</label>
              <select
                id="sort-by"
                className="form-select"
                value={sortBy}
                onChange={(event) => updateParams({ sort_by: event.target.value })}
              >
                <option value="id">Resident ID</option>
                <option value="first_name">First name</option>
                <option value="last_name">Last name</option>
                <option value="village">Village</option>
                <option value="dob">Date of birth</option>
              </select>
            </div>
            <div className="col-12 col-sm-6 col-md-4">
              <label className="form-label" htmlFor="sort-order">Sort direction</label>
              <select
                id="sort-order"
                className="form-select"
                value={sortOrder}
                onChange={(event) => updateParams({ sort_order: event.target.value })}
              >
                <option value="asc">Ascending</option>
                <option value="desc">Descending</option>
              </select>
            </div>
            <div className="col-12 col-md-4 d-flex flex-wrap gap-2">
              <button type="submit" className="btn btn-primary" disabled={loading}>
                Apply filters
              </button>
              <button type="button" className="btn btn-outline-secondary" onClick={reset}>
                Reset filters
              </button>
            </div>
          </div>
        </div>
      </form>

      {referenceError && <p className="alert alert-warning" role="status">{referenceError}</p>}
      {activeLabels.length > 0 && (
        <p className="text-muted" aria-live="polite">
          Active filters: {activeLabels.join(" · ")}
        </p>
      )}
      {error && (
        <div className="alert alert-danger" role="alert">
          <p className="mb-2">{error}</p>
          <button type="button" className="btn btn-sm btn-outline-danger" onClick={() => setReloadVersion((v) => v + 1)}>
            Try again
          </button>
        </div>
      )}

      {loading ? (
        <div className="text-center" role="status" aria-live="polite">
          <div className="spinner-border" aria-hidden="true" />
          <span className="visually-hidden">Loading residents…</span>
        </div>
      ) : !error && (
        <>
          <p className="text-muted" aria-live="polite">{formatPageRange(page, PAGE_SIZE, total)}</p>
          {total === 0 ? (
            <div className="alert alert-info" role="status">
              {activeLabels.length ? "No residents match these filters." : "No residents have been added yet."}{" "}
              {!activeLabels.length && <Link to="/add-resident">Add the first resident</Link>}
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-striped align-middle">
                <caption className="visually-hidden">Resident list</caption>
                <thead>
                  <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Village</th>
                    <th scope="col">Primary phone</th>
                    <th scope="col" className="text-end">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {residents.map((resident) => (
                    <tr key={resident.id}>
                      <th scope="row">{resident.first_name} {resident.last_name}</th>
                      <td>{resident.village}</td>
                      <td>{resident.cellphone_no}</td>
                      <td className="text-end">
                        <Link to={`/view-resident/${resident.id}`} className="btn btn-info btn-sm me-1">View</Link>
                        <Link to={`/edit-resident/${resident.id}`} className="btn btn-warning btn-sm">Edit</Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {total > PAGE_SIZE && (
            <nav aria-label="Residents pagination" className="d-flex justify-content-between align-items-center">
              <button type="button" className="btn btn-outline-secondary" disabled={page === 0} onClick={() => pageLink(page - 1)}>
                Previous
              </button>
              <span className="text-muted">Page {page + 1} of {lastPage + 1}</span>
              <button type="button" className="btn btn-outline-secondary" disabled={page >= lastPage} onClick={() => pageLink(page + 1)}>
                Next
              </button>
            </nav>
          )}
        </>
      )}
    </div>
  );
}
