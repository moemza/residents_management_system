export default function EducationSection({ qualifications, rows, setRows }) {
  const empty = { institution: "", name: "", type: "", level: "", year: "" };

  const update = (i, field, value) =>
    setRows((prev) => prev.map((r, idx) => (idx === i ? { ...r, [field]: value } : r)));

  const remove = (i) => setRows((p) => p.filter((_, idx) => idx !== i));

  return (
    <section className="card mb-4" aria-labelledby="education-heading">
      <div className="card-header d-flex justify-content-between align-items-center">
        <h2 className="h6 mb-0" id="education-heading">Education</h2>
        <button
          type="button"
          className="btn btn-sm btn-secondary"
          aria-label="Add education record"
          onClick={() => setRows((p) => [...p, { ...empty }])}
        >
          + Add
        </button>
      </div>
      <div className="card-body">
        {rows.length === 0 && <p className="text-muted mb-0">No education records. Click + Add to begin.</p>}
        {rows.map((row, i) => (
          <div key={i} className="row g-2 mb-3 align-items-center">
            <div className="col-md-3">
              <input
                className="form-control"
                aria-label={`Institution for education record ${i + 1}`}
                maxLength={200}
                placeholder="Institution"
                value={row.institution}
                onChange={(e) => update(i, "institution", e.target.value)}
              />
            </div>
            <div className="col-md-3">
              <select
                className="form-select"
                aria-label={`Qualification name for education record ${i + 1}`}
                required
                value={row.name}
                onChange={(e) => update(i, "name", e.target.value)}
              >
                <option value="">Name</option>
                {Object.entries(qualifications.names || {}).map(([field, names]) => (
                  <optgroup key={field} label={field}>
                    {names.map((n) => <option key={n} value={n}>{n}</option>)}
                  </optgroup>
                ))}
              </select>
            </div>
            <div className="col-md-2">
              <select
                className="form-select"
                aria-label={`Qualification type for education record ${i + 1}`}
                required
                value={row.type}
                onChange={(e) => update(i, "type", e.target.value)}
              >
                <option value="">Type</option>
                {(qualifications.types || []).map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div className="col-md-2">
              <select
                className="form-select"
                aria-label={`Qualification level for education record ${i + 1}`}
                required
                value={row.level}
                onChange={(e) => update(i, "level", e.target.value)}
              >
                <option value="">Level</option>
                {(qualifications.levels || []).map((l) => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>
            <div className="col-md-1">
              <input
                className="form-control"
                aria-label={`Year completed for education record ${i + 1}`}
                maxLength={20}
                placeholder="Year"
                value={row.year}
                onChange={(e) => update(i, "year", e.target.value)}
              />
            </div>
            <div className="col-md-1">
              <button
                type="button"
                className="btn btn-danger btn-sm w-100"
                aria-label={`Remove education record ${i + 1}`}
                onClick={() => remove(i)}
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
