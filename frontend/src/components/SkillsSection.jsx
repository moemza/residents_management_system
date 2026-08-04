export default function SkillsSection({ rows, setRows }) {
  return (
    <div className="card mb-4">
      <div className="card-header d-flex justify-content-between align-items-center">
        <span>Skills</span>
        <button type="button" className="btn btn-sm btn-secondary" onClick={() => setRows((p) => [...p, { name: "" }])}>
          + Add
        </button>
      </div>
      <div className="card-body">
        {rows.length === 0 && <p className="text-muted mb-0">No skills recorded. Click + Add to begin.</p>}
        {rows.map((row, i) => (
          <div key={i} className="row g-2 mb-3 align-items-center">
            <div className="col-md-11">
              <input
                className="form-control"
                placeholder="Skill"
                value={row.name}
                onChange={(e) => setRows((p) => p.map((r, idx) => (idx === i ? { name: e.target.value } : r)))}
              />
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
