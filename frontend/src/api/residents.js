import axios from "axios";

const api = axios.create({ baseURL: "http://localhost:8000/api" });

export const getVillages = () => api.get("/villages").then((r) => r.data);
export const getQualifications = () => api.get("/qualifications").then((r) => r.data);

export const getResidents = () => api.get("/residents").then((r) => r.data);
export const getResident = (id) => api.get(`/residents/${id}`).then((r) => r.data);
export const createResident = (data) => api.post("/residents", data).then((r) => r.data);
export const updateResident = (id, data) => api.put(`/residents/${id}`, data).then((r) => r.data);
export const deleteResident = (id) => api.delete(`/residents/${id}`);

export const searchResidents = (query, searchType) =>
  api.get("/search", { params: { query, search_type: searchType } }).then((r) => r.data);
