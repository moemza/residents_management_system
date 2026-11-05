import { useState, useEffect, useRef } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { getResident, deleteResident } from "../api/residents";
import { getApiErrorMessage } from "../api/errors";
import { useDocumentTitle } from "../hooks/useDocumentTitle";

export default function ViewResident() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [resident, setResident] = useState(null);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const cancelDeleteRef = useRef(null);
  const deleteButtonRef = useRef(null);
  const errorRef = useRef(null);
  const actionErrorRef = useRef(null);
  const wasConfirmingRef = useRef(false);

  useDocumentTitle(
    resident ? `${resident.first_name} ${resident.last_name}` : "Resident Details"
  );

  useEffect(() => {
    getResident(id)
      .then(setResident)
      .catch((err) => setError(getApiErrorMessage(err, "Resident not found.")));
  }, [id]);

  useEffect(() => {
    if (confirmingDelete) {
      wasConfirmingRef.current = true;
      cancelDeleteRef.current?.focus();
    } else if (wasConfirmingRef.current) {
      wasConfirmingRef.current = false;
      deleteButtonRef.current?.focus();
    }
  }, [confirmingDelete]);

  useEffect(() => {
    if (error) errorRef.current?.focus();
  }, [error]);

  useEffect(() => {
    if (actionError) actionErrorRef.current?.focus();
  }, [actionError]);

  const handleDelete = async () => {
    setDeleting(true);
    setActionError("");
    try {
      await deleteResident(id);
      navigate("/residents", { state: { success: "Resident deleted successfully." } });
    } catch (err) {
      setActionError(getApiErrorMessage(err, "Failed to delete resident. Please try again."));
    } finally {
      setDeleting(false);
    }
  };

  if (error) {
    return (
      <div className="container mt-5">
        <div className="alert alert-danger" role="alert" tabIndex={-1} ref={errorRef}>
          {error}
        </div>
        <Link to="/residents" className="btn btn-secondary">Back to residents</Link>
      </div>
    );
  }

  if (!resident) {
    return (
      <div className="container mt-5 text-center" role="status">
        <div className="spinner-border" aria-hidden="true" />
        <span className="visually-hidden">Loading resident…</span>
      </div>
    );
  }

  return (
    <div className="container mt-5 mb-5">
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">
        <h1 className="h3 mb-0">Resident Details</h1>
        <Link to="/residents" className="btn btn-outline-primary">Back to residents</Link>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="h4 mb-0">{resident.first_name} {resident.last_name}</h2>
        </div>
        <div className="card-body">
          <div className="row">
            <div className="col-md-6">
              <p><strong>Date of Birth:</strong> {resident.dob}</p>
              <p><strong>Gender:</strong> {resident.gender}</p>
              <p><strong>Village:</strong> {resident.village}</p>
            </div>
            <div className="col-md-6">
              <p><strong>Primary Phone:</strong> {resident.cellphone_no}</p>
              <p><strong>Secondary Phone:</strong> {resident.cellphone_no2 || "N/A"}</p>
              <p><strong>Email:</strong> {resident.email || "N/A"}</p>
            </div>
          </div>

          <hr />
          <h2 className="h5">Qualifications</h2>
          {resident.qualifications.length ? (
            <ul className="list-group mb-3">
              {resident.qualifications.map((q) => (
                <li key={q.id} className="list-group-item">
                  {q.name} ({q.type}) — {q.institution} — {q.year}
                </li>
              ))}
            </ul>
          ) : <p className="text-muted">No qualifications recorded</p>}

          <hr />
          <h2 className="h5">Experience</h2>
          {resident.experiences.length ? (
            <ul className="list-group mb-3">
              {resident.experiences.map((e) => (
                <li key={e.id} className="list-group-item">
                  {e.position} at {e.company} — {e.years} years
                </li>
              ))}
            </ul>
          ) : <p className="text-muted">No experience recorded</p>}

          <hr />
          <h2 className="h5">Skills</h2>
          {resident.skills.length ? (
            <ul className="list-group">
              {resident.skills.map((s) => <li key={s.id} className="list-group-item">{s.name}</li>)}
            </ul>
          ) : <p className="text-muted">No skills recorded</p>}
        </div>
        <div className="card-footer">
          {actionError && (
            <div className="alert alert-danger" role="alert" tabIndex={-1} ref={actionErrorRef}>
              {actionError}
            </div>
          )}

          {confirmingDelete ? (
            <div
              className="alert alert-danger mb-0"
              role="alertdialog"
              aria-labelledby="delete-confirm-title"
              aria-describedby="delete-confirm-detail"
            >
              <p id="delete-confirm-title" className="fw-bold mb-1">Delete this resident?</p>
              <p id="delete-confirm-detail" className="mb-3">
                This permanently deletes the resident and all qualifications, experience, and
                skills. This cannot be undone.
              </p>
              <button
                type="button"
                className="btn btn-danger me-2"
                onClick={handleDelete}
                disabled={deleting}
              >
                {deleting ? "Deleting…" : "Yes, delete permanently"}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setConfirmingDelete(false)}
                disabled={deleting}
                ref={cancelDeleteRef}
              >
                Cancel
              </button>
            </div>
          ) : (
            <>
              <Link to={`/edit-resident/${resident.id}`} className="btn btn-warning me-2">Edit</Link>
              <button
                type="button"
                className="btn btn-danger me-2"
                onClick={() => setConfirmingDelete(true)}
                disabled={deleting}
                ref={deleteButtonRef}
              >
                Delete
              </button>
              <Link to="/residents" className="btn btn-secondary">Back to residents</Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
