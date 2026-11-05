let csrfToken = "";

export function getCsrfToken() {
  return csrfToken;
}

export function setCsrfToken(token) {
  csrfToken = typeof token === "string" ? token : "";
}

export function clearCsrfToken() {
  csrfToken = "";
}
