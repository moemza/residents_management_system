import { useState, useEffect, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import { getVillages, getQualifications, createResident } from "../api/residents";
import { getApiErrorMessage, getApiFieldErrors, formatApiFieldLabel } from "../api/errors";
import EducationSection from "../components/EducationSection";
import ExperienceSection from "../components/ExperienceSection";
import SkillsSection from "../components/SkillsSection";
import Toast from "../components/Toast";
import { useToast } from "../hooks/useToast";
import { useDocumentTitle } from "../hooks/useDocumentTitle";

export default function AddResident() {
  useDocumentTitle("Add Resident");
  const navigate = useNavigate();
  const { toast, showToast, clearToast } = useToast();
  const formRef = useRef(null);

  const [villages, setVillages] = useState([]);
  const [qualificationData, setQualificationData] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [referenceError, setReferenceError] = useState("");
  const [submissionError, setSubmissionError] = useState("");

  const [form, setForm] = useState({
    first_name: "", last_name: "", dob: "", gender: "",
    village: "", cellphone_no: "", cellphone_no2: "", email: "",
  });
  const [education, setEducation] = useState([]);
  const [experience, setExperience] = useState([]);
  const [skills, setSkills] = useState([]);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    getVillages()
      .then(setVillages)
      .catch(() => {
        setReferenceError("Could not load villages. Refresh the page before adding a resident.");
        showToast("Failed to load villages", "error");
      });
    getQualifications()
      .then(setQualificationData)
      .catch(() => {
        setReferenceError("Could not load qualifications. Refresh the page before adding a resident.");
        showToast("Failed to load qualifications", "error");
      });
  }, [showToast]);

  const set = (field) => (e) => {
    setForm((p) => ({ ...p, [field]: e.target.value }));
    setErrors((p) => ({ ...p, [field]: undefined }));
    setSubmissionError("");
  };

  const validate = () => {
    const e = {};
    if (!form.first_name.trim()) e.first_name = "Required";
    if (!form.last_name.trim()) e.last_name = "Required";
    if (!form.dob) e.dob = "Required";
    if (!form.gender.trim()) e.gender = "Required";
    if (!form.village.trim()) e.village = "Required";
    if (!form.cellphone_no.trim()) e.cellphone_no = "Required";
    if (form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = "Invalid email";
    if (form.dob && form.dob > new Date().toISOString().slice(0, 10)) {
      e.dob = "Date of birth cannot be in the future";
    }
    const requiredChildFields = {
      qualifications: ["institution", "name", "type", "level", "year"],
      experiences: ["company", "position", "years"],
      skills: ["name"],
    };
    for (const [collection, fields] of Object.entries(requiredChildFields)) {
      const rows = collection === "qualifications" ? education : collection === "experiences" ? experience : skills;
      rows.forEach((row, index) => {
        fields.forEach((key) => {
          if (!String(row[key] ?? "").trim()) {
            e[`${collection}.${index}.${key}`] = "Required";
          }
        });
      });
    }
    return e;
  };

  const focusFirstInvalid = () => {
    window.requestAnimationFrame(() => {
      formRef.current?.querySelector(".is-invalid")?.focus();
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) {
      setErrors(errs);
      setSubmissionError("Please correct the highlighted fields before saving.");
      focusFirstInvalid();
      return;
    }

    setSubmitting(true);
    setSubmissionError("");
    setErrors({});
    try {
      await createResident({
        ...form,
        qualifications: education,
        experiences: experience,
        skills,
      });
      navigate("/residents", { state: { success: "Resident added successfully." } });
    } catch (err) {
      const fieldErrors = getApiFieldErrors(err);
      if (Object.keys(fieldErrors).length) {
        setErrors(fieldErrors);
        setSubmissionError("The resident could not be saved. Correct the highlighted fields and try again.");
        focusFirstInvalid();
      } else {
        setSubmissionError(getApiErrorMessage(err, "Failed to save resident."));
      }
    } finally {
      setSubmitting(false);
    }
  };

  const clearFieldError = (key) => {
    setErrors((current) => key.includes(".")
      ? { ...current, [key]: undefined }
      : Object.fromEntries(Object.entries(current).filter(([field]) => !field.startsWith(`${key}.`))));
    setSubmissionError("");
  };

  const field = (label, key, type = "text", required = false) => {
    const errorId = `${key}-error`;
    return (
      <div className="col-md-3">
        <label className="form-label" htmlFor={key}>{label}{required && " *"}</label>
        <input
          id={key}
          type={type}
          list={key === "gender" ? "gender-options" : undefined}
          required={required}
          maxLength={key.startsWith("cellphone") ? 30 : 100}
          className={`form-control ${errors[key] ? "is-invalid" : ""}`}
          aria-invalid={Boolean(errors[key])}
          aria-describedby={errors[key] ? errorId : undefined}
          value={form[key]}
          onChange={set(key)}
        />
        {errors[key] && <div id={errorId} className="invalid-feedback">{errors[key]}</div>}
      </div>
    );
  };

  return (
    <div className="container mt-5 mb-5">
      {toast && <Toast message={toast.message} type={toast.type} onClose={clearToast} />}

      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">
        <h1 className="h3 mb-0">Add New Resident</h1>
        <Link to="/" className="btn btn-outline-primary">Home</Link>
      </div>

      {referenceError && (
        <div className="alert alert-danger" role="alert">{referenceError}</div>
      )}
      {submissionError && (
        <div className="alert alert-danger" role="alert" aria-live="assertive">
          <p className="mb-1">{submissionError}</p>
          {Object.entries(errors).filter(([, message]) => message).length > 0 && (
            <ul className="mb-0">
              {Object.entries(errors).filter(([, message]) => message).map(([key, message]) => (
                <li key={key}>{formatApiFieldLabel(key)}: {message}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate ref={formRef}>
        <div className="card mb-4">
          <div className="card-header">Personal Details</div>
          <div className="card-body">
            <div className="row g-2 mb-3">
              {field("First Name", "first_name", "text", true)}
              {field("Last Name", "last_name", "text", true)}
              <div className="col-md-3">
                <label className="form-label" htmlFor="dob">Date of Birth *</label>
                <input
                  id="dob"
                  type="date"
                  required
                  max={new Date().toISOString().slice(0, 10)}
                  className={`form-control ${errors.dob ? "is-invalid" : ""}`}
                  aria-invalid={Boolean(errors.dob)}
                  aria-describedby={errors.dob ? "dob-error" : undefined}
                  value={form.dob}
                  onChange={set("dob")}
                />
                {errors.dob && <div id="dob-error" className="invalid-feedback">{errors.dob}</div>}
              </div>
              {field("Gender", "gender", "text", true)}
            </div>
            <datalist id="gender-options">
              <option value="Male" />
              <option value="Female" />
              <option value="Other" />
            </datalist>
            <div className="row g-2 mb-3">
              <div className="col-md-4">
                <label className="form-label" htmlFor="village">Village *</label>
                <input
                  id="village"
                  list="village-options"
                  required
                  maxLength={100}
                  className={`form-control ${errors.village ? "is-invalid" : ""}`}
                  aria-invalid={Boolean(errors.village)}
                  aria-describedby={errors.village ? "village-error" : undefined}
                  value={form.village}
                  onChange={set("village")}
                />
                <datalist id="village-options">
                  {villages.map((v) => <option key={v} value={v} />)}
                </datalist>
                {errors.village && <div id="village-error" className="invalid-feedback">{errors.village}</div>}
              </div>
              {field("Cellphone No", "cellphone_no", "tel", true)}
              <div className="col-md-4">
                <label className="form-label" htmlFor="cellphone_no2">Cellphone No 2</label>
                <input
                  id="cellphone_no2"
                  type="tel"
                  maxLength={30}
                  className="form-control"
                  value={form.cellphone_no2}
                  onChange={set("cellphone_no2")}
                />
              </div>
            </div>
            <div className="row g-2">
              <div className="col-md-4">
                <label className="form-label" htmlFor="email">Email</label>
                <input
                  id="email"
                  type="email"
                  maxLength={254}
                  className={`form-control ${errors.email ? "is-invalid" : ""}`}
                  aria-invalid={Boolean(errors.email)}
                  aria-describedby={errors.email ? "email-error" : undefined}
                  value={form.email}
                  onChange={set("email")}
                />
                {errors.email && <div id="email-error" className="invalid-feedback">{errors.email}</div>}
              </div>
            </div>
          </div>
        </div>

        <EducationSection qualifications={qualificationData} rows={education} setRows={setEducation} errors={errors} onFieldChange={clearFieldError} />
        <ExperienceSection rows={experience} setRows={setExperience} errors={errors} onFieldChange={clearFieldError} />
        <SkillsSection rows={skills} setRows={setSkills} errors={errors} onFieldChange={clearFieldError} />

        <button type="submit" className="btn btn-primary w-100" disabled={submitting}>
          {submitting ? "Saving…" : "Save Resident"}
        </button>
      </form>
    </div>
  );
}
