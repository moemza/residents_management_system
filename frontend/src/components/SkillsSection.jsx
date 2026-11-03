export default function SkillsSection({ rows, setRows }) {
  return (
    <section className="card mb-4" aria-labelledby="skills-heading">
      <div className="card-header d-flex justify-content-between align-items-center">
        <h2 className="h6 mb-0" id="skills-heading">Skills</h2>
        <button
          type="button"
          className="btn btn-sm btn-secondary"
          aria-label="Add skill record"
          onClick={() => setRows((p) => [...p, { name: "" }])}
        >
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
                aria-label={`Skill ${i + 1}`}
                maxLength={100}
                placeholder="Skill"
                value={row.name}
                onChange={(e) => setRows((p) => p.map((r, idx) => (idx === i ? { name: e.target.value } : r)))}
              />
            </div>
            <div className="col-md-1">
              <button
                type="button"
                className="btn btn-danger btn-sm w-100"
                aria-label={`Remove skill ${i + 1}`}
                onClick={() => setRows((p) => p.filter((_, idx) => idx !== i))}
              >
                ✖
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
