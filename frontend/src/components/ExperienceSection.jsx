export default function ExperienceSection({ rows, setRows, errors = {}, onFieldChange }) {
  const empty = { company: "", position: "", years: "" };

  const update = (i, field, value) =>
    setRows((prev) => prev.map((r, idx) => (idx === i ? { ...r, [field]: value } : r)));
  const fieldProps = (i, field, label) => {
    const key = `experiences.${i}.${field}`;
    const errorId = `experience-${i}-${field}-error`;
    return {
      "aria-label": `${label} for experience record ${i + 1}`,
      "aria-invalid": Boolean(errors[key]),
      "aria-describedby": errors[key] ? errorId : undefined,
      className: `form-control ${errors[key] ? "is-invalid" : ""}`,
      onChange: (event) => {
        update(i, field, event.target.value);
        onFieldChange?.(key);
      },
    };
  };

  return (
    <section className="card mb-4" aria-labelledby="experience-heading">
      <div className="card-header d-flex justify-content-between align-items-center">
        <h2 className="h6 mb-0" id="experience-heading">Work Experience</h2>
        <button
          type="button"
          className="btn btn-sm btn-secondary"
          aria-label="Add work experience record"
          onClick={() => setRows((p) => [...p, { ...empty }])}
        >
          + Add
        </button>
      </div>
      <div className="card-body">
        {rows.length === 0 && <p className="text-muted mb-0">No experience records. Click + Add to begin.</p>}
        {rows.map((row, i) => (
          <div key={i} className="row g-2 mb-3 align-items-center">
            <div className="col-md-4">
              <input
                {...fieldProps(i, "company", "Company")}
                maxLength={200}
                placeholder="Company"
                value={row.company ?? ""}
              />
              {errors[`experiences.${i}.company`] && <div id={`experience-${i}-company-error`} className="invalid-feedback">{errors[`experiences.${i}.company`]}</div>}
            </div>
            <div className="col-md-4">
              <input
                {...fieldProps(i, "position", "Position")}
                maxLength={200}
                placeholder="Position"
                value={row.position ?? ""}
              />
              {errors[`experiences.${i}.position`] && <div id={`experience-${i}-position-error`} className="invalid-feedback">{errors[`experiences.${i}.position`]}</div>}
            </div>
            <div className="col-md-3">
              <input
                {...fieldProps(i, "years", "Years")}
                maxLength={20}
                placeholder="Years"
                value={row.years ?? ""}
              />
              {errors[`experiences.${i}.years`] && <div id={`experience-${i}-years-error`} className="invalid-feedback">{errors[`experiences.${i}.years`]}</div>}
            </div>
            <div className="col-md-1">
              <button
                type="button"
                className="btn btn-danger btn-sm w-100"
                aria-label={`Remove experience record ${i + 1}`}
                onClick={() => {
                  setRows((p) => p.filter((_, idx) => idx !== i));
                  onFieldChange?.("experiences");
                }}
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
