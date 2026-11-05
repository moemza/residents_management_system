export default function EducationSection({ qualifications, rows, setRows, errors = {}, onFieldChange }) {
  const empty = { institution: "", name: "", type: "", level: "", year: "" };

  const update = (i, field, value) =>
    setRows((prev) => prev.map((r, idx) => (idx === i ? { ...r, [field]: value } : r)));

  const fieldProps = (i, field, label) => {
    const key = `qualifications.${i}.${field}`;
    const errorId = `qualification-${i}-${field}-error`;
    return {
      "aria-label": `${label} for education record ${i + 1}`,
      "aria-invalid": Boolean(errors[key]),
      "aria-describedby": errors[key] ? errorId : undefined,
      className: `form-control ${errors[key] ? "is-invalid" : ""}`,
      onChange: (event) => {
        update(i, field, event.target.value);
        onFieldChange?.(key);
      },
    };
  };

  const remove = (i) => {
    setRows((p) => p.filter((_, idx) => idx !== i));
    onFieldChange?.("qualifications");
  };

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
                {...fieldProps(i, "institution", "Institution")}
                maxLength={200}
                placeholder="Institution"
                value={row.institution ?? ""}
              />
              {errors[`qualifications.${i}.institution`] && <div id={`qualification-${i}-institution-error`} className="invalid-feedback">{errors[`qualifications.${i}.institution`]}</div>}
            </div>
            <div className="col-md-3">
              <input
                {...fieldProps(i, "name", "Qualification name")}
                list="qualification-names"
                required
                value={row.name ?? ""}
              />
              <datalist id="qualification-names">
                {Object.values(qualifications.names || {}).flat().map((name) => <option key={name} value={name} />)}
              </datalist>
              {errors[`qualifications.${i}.name`] && <div id={`qualification-${i}-name-error`} className="invalid-feedback">{errors[`qualifications.${i}.name`]}</div>}
            </div>
            <div className="col-md-2">
              <input
                {...fieldProps(i, "type", "Qualification type")}
                list="qualification-types"
                required
                value={row.type ?? ""}
              />
              <datalist id="qualification-types">
                {(qualifications.types || []).map((type) => <option key={type} value={type} />)}
              </datalist>
              {errors[`qualifications.${i}.type`] && <div id={`qualification-${i}-type-error`} className="invalid-feedback">{errors[`qualifications.${i}.type`]}</div>}
            </div>
            <div className="col-md-2">
              <input
                {...fieldProps(i, "level", "Qualification level")}
                list="qualification-levels"
                required
                value={row.level ?? ""}
              />
              <datalist id="qualification-levels">
                {(qualifications.levels || []).map((level) => <option key={level} value={level} />)}
              </datalist>
              {errors[`qualifications.${i}.level`] && <div id={`qualification-${i}-level-error`} className="invalid-feedback">{errors[`qualifications.${i}.level`]}</div>}
            </div>
            <div className="col-md-1">
              <input
                {...fieldProps(i, "year", "Year completed")}
                maxLength={20}
                placeholder="Year"
                value={row.year ?? ""}
              />
              {errors[`qualifications.${i}.year`] && <div id={`qualification-${i}-year-error`} className="invalid-feedback">{errors[`qualifications.${i}.year`]}</div>}
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
