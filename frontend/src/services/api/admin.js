import { request } from "./client.js";

export const adminApi = {
  // ── Admin Profile ──
  updateAdminDetails: (adminId, data) =>
    request(`/api/v1/admins/${adminId}`, {
      method: "PUT",
      body: data,
    }, "/admin/login"),

  getAdminProfile: () =>
    request("/api/v1/admins/me/profile", {
      method: "GET",
    }, "/admin/login"),

  // ── Admin Dashboard / Analytics ──
  getAdminDashboardData: () =>
    request("/api/v1/analytics/dashboard", {
      method: "GET",
    }, "/admin/login"),

  getAdminAnalytics: () =>
    request("/api/v1/analytics/dashboard", {
      method: "GET",
    }, "/admin/login"),
};
