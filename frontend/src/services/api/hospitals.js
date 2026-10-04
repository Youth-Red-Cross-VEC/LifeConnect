import { request } from "./client.js";

export const hospitalApi = {
  // ── Blood Banks (uses hospitals endpoint) ──
  getBloodBanks: (params) => {
    const query = new URLSearchParams(params || {}).toString();
    return request(`/api/v1/hospitals/blood-banks${query ? `?${query}` : ""}`, {
      method: "GET",
    });
  },

  // ── Hospitals ──
  addHospital: (data) =>
    request("/api/v1/hospitals/", {
      method: "POST",
      body: data,
    }, "/admin/login"),

  getHospitals: (params) => {
    const query = new URLSearchParams(params || {}).toString();
    return request(`/api/v1/hospitals/${query ? `?${query}` : ""}`, {
      method: "GET",
    }, "/admin/login");
  },

  updateHospital: (hospitalId, data) =>
    request(`/api/v1/hospitals/${hospitalId}`, {
      method: "PATCH",
      body: data,
    }, "/admin/login"),

  deleteHospital: (hospitalId) =>
    request(`/api/v1/hospitals/${hospitalId}`, {
      method: "DELETE",
    }, "/admin/login"),

  getHospitalAutofill: (q) =>
    request(`/api/v1/hospitals/autofill?q=${encodeURIComponent(q)}`, {
      method: "GET",
    }),
};
