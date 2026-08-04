import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { getVillages, getQualifications, createResident } from "../api/residents";
import EducationSection from "../components/EducationSection";
import ExperienceSection from "../components/ExperienceSection";
import SkillsSection from "../components/SkillsSection";
import Toast from "../components/Toast";
import { useToast } from "../hooks/useToast";

const GENDERS = ["Male", "Female", "Other"];

export default function AddResident() {
  const navigate = useNavigate();
  const { toast, showToast, clearToast } = useToast();

  const [villages, setVillages] = useState([]);
  const [qualificationData, setQualificationData] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    first_name: "", last_name: "", dob: "", gender: "",
    village: "", cellphone_no: "", cellphone_no2: "", email: "",
  });
  const [education, setEducation] = useState([]);
  const [experience, setExperience] = useState([]);
  const [skills, setSkills] = useState([]);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    getVillages().then(setVillages).catch(() => showToast("Failed to load villages", "error"));
    getQualifications().then(setQualificationData).catch(() => showToast("Failed to load qualifications", "error"));
  }, []);

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }

    setSubmitting(true);
    try {
      await createResident({
        ...form,
        qualifications: education,
        experiences: experience,
        skills,
      });
      navigate("/", { state: { success: "Resident added successfully." } });
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to save resident.", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const field = (label, key, type = "text", required = false) => (
    <div className="col-md-3">
      <label className="form-label">{label}{required && " *"}</label>
      <input
        type={type}
        className={`form-control ${errors[key] ? "is-invalid" : ""}`}
        value={form[key]}
        onChange={set(key)}
      />
      {errors[key] && <div className="invalid-feedback">{errors[key]}</div>}
    </div>
  );

  return (
    <div className="container mt-5 mb-5">
      {toast && <Toast message={toast.message} type={toast.type} onClose={clearToast} />}

      <div className="d-flex justify-content-between align-items-center mb-4">
        <h3>Add New Resident</h3>
        <Link to="/" className="btn btn-outline-primary">Home</Link>
      </div>

      <form onSubmit={handleSubmit} noValidate>
        <div className="card mb-4">
          <div className="card-header">Personal Details</div>
          <div className="card-body">
            <div className="row g-2 mb-3">
              {field("First Name", "first_name", "text", true)}
              {field("Last Name", "last_name", "text", true)}
              <div className="col-md-3">
                <label className="form-label">Date of Birth *</label>
                <input
                  type="date"
                  className={`form-control ${errors.dob ? "is-invalid" : ""}`}
                  value={form.dob}
                  max={new Date().toISOString().split("T")[0]}
                  onChange={set("dob")}
                />
                {errors.dob && <div className="invalid-feedback">{errors.dob}</div>}
              </div>
              <div className="col-md-3">
                <label className="form-label">Gender *</label>
                <select className={`form-select ${errors.gender ? "is-invalid" : ""}`} value={form.gender} onChange={set("gender")}>
                  <option value="">Select Gender</option>
                  {GENDERS.map((g) => <option key={g} value={g}>{g}</option>)}
                </select>
                {errors.gender && <div className="invalid-feedback">{errors.gender}</div>}
              </div>
            </div>
            <div className="row g-2 mb-3">
              <div className="col-md-4">
                <label className="form-label">Village *</label>
                <select className={`form-select ${errors.village ? "is-invalid" : ""}`} value={form.village} onChange={set("village")}>
                  <option value="">Select Village</option>
                  {villages.map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
                {errors.village && <div className="invalid-feedback">{errors.village}</div>}
              </div>
              {field("Cellphone No", "cellphone_no", "tel", true)}
              <div className="col-md-4">
                <label className="form-label">Cellphone No 2</label>
                <input type="tel" className="form-control" value={form.cellphone_no2} onChange={set("cellphone_no2")} />
              </div>
            </div>
            <div className="row g-2">
              <div className="col-md-4">
                <label className="form-label">Email</label>
                <input
                  type="email"
                  className={`form-control ${errors.email ? "is-invalid" : ""}`}
                  value={form.email}
                  onChange={set("email")}
                />
                {errors.email && <div className="invalid-feedback">{errors.email}</div>}
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
