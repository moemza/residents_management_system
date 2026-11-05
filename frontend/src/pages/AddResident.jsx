import { useState, useEffect, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import { getVillages, getQualifications, createResident } from "../api/residents";
import { getApiErrorMessage } from "../api/errors";
import { GENDERS } from "../constants";
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
  };

  const validate = () => {
    const e = {};
    if (!form.first_name.trim()) e.first_name = "Required";
    if (!form.last_name.trim()) e.last_name = "Required";
    if (!form.dob) e.dob = "Required";
    if (!form.gender) e.gender = "Required";
    if (!form.village) e.village = "Required";
    if (!form.cellphone_no.trim()) e.cellphone_no = "Required";
    if (form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = "Invalid email";
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
      focusFirstInvalid();
      return;
    }

    setSubmitting(true);
    try {
      await createResident({
        ...form,
        qualifications: education,
        experiences: experience,
        skills,
      });
      navigate("/residents", { state: { success: "Resident added successfully." } });
    } catch (err) {
      showToast(getApiErrorMessage(err, "Failed to save resident."), "error");
    } finally {
      setSubmitting(false);
    }
  };

  const field = (label, key, type = "text", required = false) => {
    const errorId = `${key}-error`;
    return (
      <div className="col-md-3">
        <label className="form-label" htmlFor={key}>{label}{required && " *"}</label>
        <input
          id={key}
          type={type}
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
              <div className="col-md-3">
                <label className="form-label" htmlFor="gender">Gender *</label>
                <select
                  id="gender"
                  required
                  className={`form-select ${errors.gender ? "is-invalid" : ""}`}
                  aria-invalid={Boolean(errors.gender)}
                  aria-describedby={errors.gender ? "gender-error" : undefined}
                  value={form.gender}
                  onChange={set("gender")}
                >
                  <option value="">Select Gender</option>
                  {GENDERS.map((g) => <option key={g} value={g}>{g}</option>)}
                </select>
                {errors.gender && <div id="gender-error" className="invalid-feedback">{errors.gender}</div>}
              </div>
            </div>
            <div className="row g-2 mb-3">
              <div className="col-md-4">
                <label className="form-label" htmlFor="village">Village *</label>
                <select
                  id="village"
                  required
                  className={`form-select ${errors.village ? "is-invalid" : ""}`}
                  aria-invalid={Boolean(errors.village)}
                  aria-describedby={errors.village ? "village-error" : undefined}
                  value={form.village}
                  onChange={set("village")}
                >
                  <option value="">Select Village</option>
                  {villages.map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
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

        <EducationSection qualifications={qualificationData} rows={education} setRows={setEducation} />
        <ExperienceSection rows={experience} setRows={setExperience} />
        <SkillsSection rows={skills} setRows={setSkills} />

        <button type="submit" className="btn btn-primary w-100" disabled={submitting}>
          {submitting ? "Saving…" : "Save Resident"}
        </button>
      </form>
    </div>
  );
}
