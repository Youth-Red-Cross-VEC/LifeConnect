import { request } from "./client.js";

export const donorApi = {
  // ── Donors ──
  getDonors: (params) => {
    const query = new URLSearchParams(params).toString();
    return request(`/api/v1/donors/${query ? `?${query}` : ""}`, {
      method: "GET",
    }, "/admin/login");
  },

  getDonorById: (donorId) =>
    request(`/api/v1/donors/${donorId}`, { method: "GET" }),

  modifyDonorDetails: (donorId, data) =>
    request(`/api/v1/donors/${donorId}`, {
      method: "PATCH",
      body: data,
    }),

  deactivateDonor: (donorId) =>
    request(`/api/v1/donors/${donorId}/deactivate`, {
      method: "POST",
    }, "/admin/login"),

  activateDonor: (donorId) =>
    request(`/api/v1/donors/${donorId}/activate`, {
      method: "POST",
    }, "/admin/login"),
};
