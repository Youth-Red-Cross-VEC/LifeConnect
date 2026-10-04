import { request } from "./client.js";

export const bloodRequestApi = {
  // ── Blood Requests ──
  generateBloodRequest: (data) =>
    request("/api/v1/blood-requests/", {
      method: "POST",
      body: data,
    }),

  getBloodRequests: (status) =>
    request(`/api/v1/blood-requests/${status}`, {
      method: "GET",
    }, "/admin/login"),

  getPendingRequests: () =>
    request("/api/v1/blood-requests/pending", {
      method: "GET",
    }, "/admin/login"),

  getOngoingRequests: () =>
    request("/api/v1/blood-requests/ongoing", {
      method: "GET",
    }, "/admin/login"),

  getClosedRequests: () =>
    request("/api/v1/blood-requests/closed", {
      method: "GET",
    }, "/admin/login"),

  getExpiredRequests: () =>
    request("/api/v1/blood-requests/expired", {
      method: "GET",
    }, "/admin/login"),

  getDeclinedRequests: () =>
    request("/api/v1/blood-requests/declined", {
      method: "GET",
    }, "/admin/login"),

  approveRequest: (requestId) =>
    request(`/api/v1/blood-requests/${requestId}/approve`, {
      method: "POST",
    }, "/admin/login"),

  declineRequest: (requestId, reason) =>
    request(`/api/v1/blood-requests/${requestId}/decline${reason ? `?reason=${encodeURIComponent(reason)}` : ""}`, {
      method: "POST",
    }, "/admin/login"),

  closeRequest: (requestId, data) =>
    request(`/api/v1/blood-requests/${requestId}/close`, {
      method: "POST",
      body: data,
    }, "/admin/login"),

  getRequestStats: () =>
    request("/api/v1/blood-requests/stats/summary", {
      method: "GET",
    }, "/admin/login"),
};
