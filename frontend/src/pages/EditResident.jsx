import { useState, useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { getResident, getVillages, getQualifications, updateResident } from "../api/residents";
import EducationSection from "../components/EducationSection";
import ExperienceSection from "../components/ExperienceSection";
import SkillsSection from "../components/SkillsSection";
import Toast from "../components/Toast";
import { useToast } from "../hooks/useToast";

const GENDERS = ["Male", "Female", "Other"];

export default function EditResident() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast, showToast, clearToast } = useToast();

  const [villages, setVillages] = useState([]);
  const [qualificationData, setQualificationData] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  const [form, setForm] = useState({
    first_name: "", last_name: "", dob: "", gender: "",
    village: "", cellphone_no: "", cellphone_no2: "", email: "",
  });
  const [education, setEducation] = useState([]);
  const [experience, setExperience] = useState([]);
  const [skills, setSkills] = useState([]);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    Promise.all([getResident(id), getVillages(), getQualifications()])
      .then(([resident, v, q]) => {
        setForm({
          first_name: resident.first_name,
          last_name: resident.last_name,
          dob: resident.dob,
          gender: resident.gender,
          village: resident.village,
          cellphone_no: resident.cellphone_no,
          cellphone_no2: resident.cellphone_no2 || "",
          email: resident.email || "",
        });
        setEducation(resident.qualifications.map(({ institution, name, type, level, year }) => ({ institution, name, type, level, year })));
        setExperience(resident.experiences.map(({ company, position, years }) => ({ company, position, years })));
        setSkills(resident.skills.map(({ name }) => ({ name })));
        setVillages(v);
        setQualificationData(q);
      })
      .catch(() => showToast("Failed to load resident data.", "error"))
      .finally(() => setLoading(false));
  }, [id]);

  const set = (field) => (e) => {
    setForm((p) => ({ ...p, [field]: e.target.value }));
    setErrors((p) => ({ ...p, [field]: undefined }));
  };

  const validate = () => {
    const e = {};
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
      await updateResident(id, { ...form, qualifications: education, experiences: experience, skills });
      navigate("/", { state: { success: "Resident updated successfully." } });
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to update resident.", "error");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="container mt-5 text-center"><div className="spinner-border" /></div>;

  return (
    <div className="container mt-5 mb-5">
      {toast && <Toast message={toast.message} type={toast.type} onClose={clearToast} />}

      <div className="d-flex justify-content-between align-items-center mb-4">
        <h3>Edit Resident: {form.first_name} {form.last_name}</h3>
        <Link to="/" className="btn btn-outline-primary">Home</Link>
      </div>

      <form onSubmit={handleSubmit} noValidate>
        <div className="card mb-4">
          <div className="card-header">Personal Details</div>
          <div className="card-body">
            <div className="row g-2 mb-3">
              <div className="col-md-3">
                <label className="form-label">First Name</label>
                <input className="form-control" value={form.first_name} readOnly />
              </div>
              <div className="col-md-3">
                <label className="form-label">Last Name</label>
                <input className="form-control" value={form.last_name} readOnly />
              </div>
              <div className="col-md-3">
                <label className="form-label">Date of Birth</label>
                <input className="form-control" value={form.dob} readOnly />
              </div>
              <div className="col-md-3">
                <label className="form-label">Gender</label>
                <input className="form-control" value={form.gender} readOnly />
              </div>
            </div>
            <div className="row g-2 mb-3">
              <div className="col-md-4">
                <label className="form-label">Village</label>
                <input className="form-control" value={form.village} readOnly />
              </div>
              <div className="col-md-4">
                <label className="form-label">Cellphone No *</label>
                <input
                  type="tel"
                  className={`form-control ${errors.cellphone_no ? "is-invalid" : ""}`}
                  value={form.cellphone_no}
                  onChange={set("cellphone_no")}
                />
                {errors.cellphone_no && <div className="invalid-feedback">{errors.cellphone_no}</div>}
              </div>
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
          {submitting ? "Saving…" : "Update Resident"}
        </button>
      </form>
    </div>
  );
}
