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
