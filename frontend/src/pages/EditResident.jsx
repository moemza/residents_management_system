import { useState, useEffect, useRef } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { getResident, getQualifications, updateResident } from "../api/residents";
import { getApiErrorMessage } from "../api/errors";
import EducationSection from "../components/EducationSection";
import ExperienceSection from "../components/ExperienceSection";
import SkillsSection from "../components/SkillsSection";
import Toast from "../components/Toast";
import { useToast } from "../hooks/useToast";
import { useDocumentTitle } from "../hooks/useDocumentTitle";

export default function EditResident() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast, showToast, clearToast } = useToast();
  const formRef = useRef(null);
  const loadErrorRef = useRef(null);

  const [qualificationData, setQualificationData] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [form, setForm] = useState({
    first_name: "", last_name: "", dob: "", gender: "",
    village: "", cellphone_no: "", cellphone_no2: "", email: "",
  });
  const [education, setEducation] = useState([]);
  const [experience, setExperience] = useState([]);
  const [skills, setSkills] = useState([]);
  const [errors, setErrors] = useState({});

  useDocumentTitle("Edit Resident");

  useEffect(() => {
    Promise.all([getResident(id), getQualifications()])
      .then(([resident, q]) => {
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
        setQualificationData(q);
      })
      .catch((err) => {
        setLoadError(
          getApiErrorMessage(
            err,
            "Failed to load resident data. The resident may no longer exist."
          )
        );
        showToast("Failed to load resident data.", "error");
      })
      .finally(() => setLoading(false));
  }, [id, showToast]);

  useEffect(() => {
    if (loadError) loadErrorRef.current?.focus();
  }, [loadError]);

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
      await updateResident(id, { ...form, qualifications: education, experiences: experience, skills });
      navigate("/residents", { state: { success: "Resident updated successfully." } });
    } catch (err) {
      showToast(getApiErrorMessage(err, "Failed to update resident."), "error");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="container mt-5 text-center" role="status">
        <div className="spinner-border" aria-hidden="true" />
        <span className="visually-hidden">Loading resident…</span>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="container mt-5">
        <div className="alert alert-danger" role="alert" tabIndex={-1} ref={loadErrorRef}>
          {loadError}
        </div>
        <Link to="/residents" className="btn btn-secondary">Back to residents</Link>
      </div>
    );
  }

  return (
    <div className="container mt-5 mb-5">
      {toast && <Toast message={toast.message} type={toast.type} onClose={clearToast} />}

      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">
        <h1 className="h3 mb-0">Edit Resident: {form.first_name} {form.last_name}</h1>
        <Link to="/" className="btn btn-outline-primary">Home</Link>
      </div>

      <p className="text-muted">
        Name, date of birth, gender, and village are identity fields and cannot be
        changed after creation. Contact details and records can be updated.
      </p>

      <form onSubmit={handleSubmit} noValidate ref={formRef}>
        <div className="card mb-4">
          <div className="card-header">Personal Details</div>
          <div className="card-body">
            <div className="row g-2 mb-3">
              <div className="col-md-3">
                <label className="form-label" htmlFor="edit-first_name">First Name</label>
                <input id="edit-first_name" className="form-control" value={form.first_name} readOnly />
              </div>
              <div className="col-md-3">
                <label className="form-label" htmlFor="edit-last_name">Last Name</label>
                <input id="edit-last_name" className="form-control" value={form.last_name} readOnly />
              </div>
              <div className="col-md-3">
                <label className="form-label" htmlFor="edit-dob">Date of Birth</label>
                <input id="edit-dob" className="form-control" value={form.dob} readOnly />
              </div>
              <div className="col-md-3">
                <label className="form-label" htmlFor="edit-gender">Gender</label>
                <input id="edit-gender" className="form-control" value={form.gender} readOnly />
              </div>
            </div>
            <div className="row g-2 mb-3">
              <div className="col-md-4">
                <label className="form-label" htmlFor="edit-village">Village</label>
                <input id="edit-village" className="form-control" value={form.village} readOnly />
              </div>
              <div className="col-md-4">
                <label className="form-label" htmlFor="edit-cellphone_no">Cellphone No *</label>
                <input
                  id="edit-cellphone_no"
                  type="tel"
                  required
                  maxLength={30}
                  className={`form-control ${errors.cellphone_no ? "is-invalid" : ""}`}
                  aria-invalid={Boolean(errors.cellphone_no)}
                  aria-describedby={errors.cellphone_no ? "edit-cellphone_no-error" : undefined}
                  value={form.cellphone_no}
                  onChange={set("cellphone_no")}
                />
                {errors.cellphone_no && (
                  <div id="edit-cellphone_no-error" className="invalid-feedback">
                    {errors.cellphone_no}
                  </div>
                )}
              </div>
              <div className="col-md-4">
                <label className="form-label" htmlFor="edit-cellphone_no2">Cellphone No 2</label>
                <input
                  id="edit-cellphone_no2"
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
                <label className="form-label" htmlFor="edit-email">Email</label>
                <input
                  id="edit-email"
                  type="email"
                  maxLength={254}
                  className={`form-control ${errors.email ? "is-invalid" : ""}`}
                  aria-invalid={Boolean(errors.email)}
                  aria-describedby={errors.email ? "edit-email-error" : undefined}
                  value={form.email}
                  onChange={set("email")}
                />
                {errors.email && (
                  <div id="edit-email-error" className="invalid-feedback">{errors.email}</div>
                )}
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
