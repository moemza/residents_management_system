import axios from "axios";
import { clearCsrfToken, getCsrfToken, setCsrfToken } from "../auth";

// Same-origin by default. Vite proxies /api during development, and the
// backend serves the built SPA in production. VITE_API_BASE_URL can override
// this for split deployments.
const baseURL = import.meta.env.VITE_API_BASE_URL || "/api";
const api = axios.create({ baseURL, withCredentials: true });

api.interceptors.request.use((config) => {
  const csrfToken = getCsrfToken();
  if (csrfToken && !["get", "head", "options"].includes(config.method?.toLowerCase())) {
    config.headers["X-CSRF-Token"] = csrfToken;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const failedLogin = error?.config?.url?.endsWith("/auth/login");
    if (error?.response?.status === 401 && !failedLogin) {
      clearCsrfToken();
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event("residents:unauthorized"));
      }
    }
    return Promise.reject(error);
  }
);

export const getAuthStatus = () =>
  api.get("/auth/status").then((response) => {
    setCsrfToken(response.data.csrf_token);
    return response.data;
  });
export const loginAdmin = (credentials) =>
  api.post("/auth/login", credentials).then((response) => {
    setCsrfToken(response.data.csrf_token);
    if (typeof window !== "undefined") {
      window.dispatchEvent(new Event("residents:authenticated"));
    }
    return response.data;
  });
export const logoutAdmin = () => api.post("/auth/logout");

export const getVillages = () => api.get("/villages").then((r) => r.data);
export const getQualifications = () => api.get("/qualifications").then((r) => r.data);

export const getResidents = (params = {}) =>
  api.get("/residents", { params }).then((r) => r.data);
export const getResidentsPage = (params = {}) =>
  api.get("/residents", { params }).then((r) => ({
    items: r.data,
    total: Number(r.headers["x-total-count"] ?? r.data.length),
  }));
export const getResident = (id) => api.get(`/residents/${id}`).then((r) => r.data);
export const createResident = (data) => api.post("/residents", data).then((r) => r.data);
export const updateResident = (id, data) => api.put(`/residents/${id}`, data).then((r) => r.data);
export const deleteResident = (id) => api.delete(`/residents/${id}`);

export const searchResidents = (query, searchType, params = {}) =>
  api
    .get("/search", { params: { query, search_type: searchType, ...params } })
    .then((r) => r.data);

export const searchResidentsPage = (query, searchType, params = {}) =>
  api
    .get("/search", { params: { query, search_type: searchType, ...params } })
    .then((r) => ({
      items: r.data,
      total: Number(r.headers["x-total-count"] ?? r.data.length),
    }));
