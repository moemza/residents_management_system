export default function ExperienceSection({ rows, setRows }) {
  const empty = { company: "", position: "", years: "" };

  const update = (i, field, value) =>
    setRows((prev) => prev.map((r, idx) => (idx === i ? { ...r, [field]: value } : r)));

  return (
    <div className="card mb-4">
      <div className="card-header d-flex justify-content-between align-items-center">
        <span>Work Experience</span>
        <button type="button" className="btn btn-sm btn-secondary" onClick={() => setRows((p) => [...p, { ...empty }])}>
          + Add
        </button>
      </div>
      <div className="card-body">
        {rows.length === 0 && <p className="text-muted mb-0">No experience records. Click + Add to begin.</p>}
        {rows.map((row, i) => (
          <div key={i} className="row g-2 mb-3 align-items-center">
            <div className="col-md-4">
              <input className="form-control" placeholder="Company" value={row.company} onChange={(e) => update(i, "company", e.target.value)} />
            </div>
            <div className="col-md-4">
              <input className="form-control" placeholder="Position" value={row.position} onChange={(e) => update(i, "position", e.target.value)} />
            </div>
            <div className="col-md-3">
              <input className="form-control" placeholder="Years" value={row.years} onChange={(e) => update(i, "years", e.target.value)} />
            </div>
            <div className="col-md-1">
              <button type="button" className="btn btn-danger btn-sm w-100" onClick={() => setRows((p) => p.filter((_, idx) => idx !== i))}>✖</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
