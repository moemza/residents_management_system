/**
 * Convert FastAPI error responses into a single human-readable message.
 *
 * FastAPI returns `detail` as a string for HTTPException responses and as an
 * array of validation objects for 422 responses. Rendering that array directly
 * in React would throw, so callers must use this helper.
 */
export function getApiErrorMessage(error, fallback = "Request failed. Please try again.") {
  const detail = error?.response?.data?.detail;

  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (!item || typeof item !== "object") return null;

        const location = Array.isArray(item.loc)
          ? item.loc.filter((part) => part !== "body" && part !== "query").join(".")
          : "";
        const message = typeof item.msg === "string" ? item.msg : "Invalid value";
        return location ? `${location}: ${message}` : message;
      })
      .filter(Boolean);

    if (messages.length) return messages.join("; ");
  }

  return fallback;
}

export function getApiFieldErrors(error) {
  const detail = error?.response?.data?.detail;
  if (!Array.isArray(detail)) return {};

  return detail.reduce((errors, item) => {
    if (!item || !Array.isArray(item.loc) || typeof item.msg !== "string") return errors;
    const path = item.loc.filter((part) => part !== "body");
    if (path.length) {
      const key = path.join(".");
      errors[key] = errors[key] ? `${errors[key]}; ${item.msg}` : item.msg;
    }
    return errors;
  }, {});
}

export function formatApiFieldLabel(path) {
  const labels = {
    first_name: "First name",
    last_name: "Last name",
    dob: "Date of birth",
    gender: "Gender",
    village: "Village",
    cellphone_no: "Primary phone",
    cellphone_no2: "Secondary phone",
    email: "Email",
  };
  if (labels[path]) return labels[path];

  const nested = path.match(/^(qualifications|experiences|skills)\.(\d+)\.(.+)$/);
  if (!nested) return path;
  const [, collection, index, field] = nested;
  const collectionLabel = {
    qualifications: "Qualification",
    experiences: "Experience",
    skills: "Skill",
  }[collection];
  const fieldLabel = {
    institution: "Institution",
    name: collection === "qualifications" ? "Name" : "Skill name",
    type: "Type",
    level: "Level",
    year: "Year",
    company: "Company",
    position: "Position",
    years: "Years",
  }[field] || field;
  return `${collectionLabel} ${Number(index) + 1} — ${fieldLabel}`;
}
