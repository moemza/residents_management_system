import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getResidentsPage } from "../api/residents";
import { getApiErrorMessage } from "../api/errors";
import { PAGE_SIZE, clampPage, formatPageRange } from "../api/pagination";
import { useDocumentTitle } from "../hooks/useDocumentTitle";

export default function Residents() {
  useDocumentTitle("Residents");

  const [residents, setResidents] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async (targetPage) => {
    setLoading(true);
    setError("");
    try {
      let safePage = Math.max(0, targetPage);
      let data = await getResidentsPage({
        limit: PAGE_SIZE,
        offset: safePage * PAGE_SIZE,
      });

      const clamped = clampPage(safePage, PAGE_SIZE, data.total);
      if (clamped !== safePage) {
        safePage = clamped;
        data = await getResidentsPage({
          limit: PAGE_SIZE,
          offset: safePage * PAGE_SIZE,
        });
      }

      setResidents(data.items);
      setTotal(data.total);
      setPage(safePage);
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to load residents."));
      setResidents([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(0);
  }, [load]);

  const lastPage = Math.max(0, Math.ceil(total / PAGE_SIZE) - 1);

  return (
    <div className="container mt-5 mb-5">
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">
        <h1 className="h3 mb-0">Residents</h1>
        <div className="d-flex gap-2">
          <Link to="/search?type=name" className="btn btn-outline-secondary">Search</Link>
          <Link to="/add-resident" className="btn btn-primary">Add Resident</Link>
          <Link to="/" className="btn btn-outline-primary">Home</Link>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger" role="alert">
          <p className="mb-2">{error}</p>
          <button type="button" className="btn btn-sm btn-outline-danger" onClick={() => load(page)}>
            Try again
          </button>
        </div>
      )}

      {loading ? (
        <div className="text-center" role="status">
          <div className="spinner-border" aria-hidden="true" />
          <span className="visually-hidden">Loading residents…</span>
        </div>
      ) : (
        <>
          <p className="text-muted" aria-live="polite">
            {formatPageRange(page, PAGE_SIZE, total)}
          </p>

          {total === 0 ? (
            <div className="alert alert-info" role="status">
              No residents have been added yet.{" "}
              <Link to="/add-resident">Add the first resident</Link>.
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
                        <Link
                          to={`/view-resident/${resident.id}`}
                          className="btn btn-info btn-sm me-1"
                        >
                          View
                        </Link>
                        <Link
                          to={`/edit-resident/${resident.id}`}
                          className="btn btn-warning btn-sm"
                        >
                          Edit
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {total > PAGE_SIZE && (
            <nav aria-label="Residents pagination" className="d-flex justify-content-between align-items-center">
              <button
                type="button"
                className="btn btn-outline-secondary"
                disabled={page === 0 || loading}
                onClick={() => load(page - 1)}
              >
                Previous
              </button>
              <span className="text-muted">
                Page {page + 1} of {lastPage + 1}
              </span>
              <button
                type="button"
                className="btn btn-outline-secondary"
                disabled={page >= lastPage || loading}
                onClick={() => load(page + 1)}
              >
                Next
              </button>
            </nav>
          )}
        </>
      )}
    </div>
  );
}
