import { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { getResident, deleteResident } from "../api/residents";

export default function ViewResident() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [resident, setResident] = useState(null);
  const [error, setError] = useState(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    getResident(id).then(setResident).catch(() => setError("Resident not found."));
  }, [id]);

  const handleDelete = async () => {
    if (!window.confirm) return; // guard — should never be called directly
    setDeleting(true);
    try {
      await deleteResident(id);
      navigate("/", { state: { success: "Resident deleted successfully." } });
    } catch {
      setError("Failed to delete resident. Please try again.");
    } finally {
      setDeleting(false);
    }
  };

  if (error) return <div className="container mt-5"><div className="alert alert-danger">{error}</div><Link to="/" className="btn btn-secondary">Home</Link></div>;
  if (!resident) return <div className="container mt-5 text-center"><div className="spinner-border" /></div>;

  return (
    <div className="container mt-5">
      <Link to="/" className="btn btn-secondary mb-3">Home</Link>
      <h2 className="mb-4 text-center">Resident Details</h2>

      <div className="card">
        <div className="card-header">
          <h4>{resident.first_name} {resident.last_name}</h4>
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
          <h5>Qualifications</h5>
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
          <h5>Experience</h5>
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
          <h5>Skills</h5>
          {resident.skills.length ? (
            <ul className="list-group">
              {resident.skills.map((s) => <li key={s.id} className="list-group-item">{s.name}</li>)}
            </ul>
          ) : <p className="text-muted">No skills recorded</p>}
        </div>
        <div className="card-footer">
          <Link to={`/edit-resident/${resident.id}`} className="btn btn-warning me-2">Edit</Link>
          <button
            className="btn btn-danger me-2"
            onClick={handleDelete}
            disabled={deleting}
          >
            {deleting ? "Deleting…" : "Delete"}
          </button>
          <Link to="/" className="btn btn-secondary">Back to Home</Link>
        </div>
      </div>
    </div>
  );
}
