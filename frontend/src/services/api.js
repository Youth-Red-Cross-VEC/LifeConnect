// Central API service for LifeConnect
// In Docker: VITE_API_URL is "" so requests go to same origin (nginx proxies /api/* → api:8000)
// In local dev: VITE_API_URL is "http://localhost:8000" for direct access
import { createHttpClient } from "./http";
import { session } from "./session";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// ─── Session helpers (re-exported so existing imports keep working) ───────────

export const getToken = session.getToken;
export const setToken = session.setToken;
export const getRefreshToken = session.getRefreshToken;
export const setRefreshToken = session.setRefreshToken;
export const isLoggedIn = session.isLoggedIn;
export const getUserType = session.getUserType;
export const setUserType = session.setUserType;
export const getUserId = session.getUserId;
export const setUserId = session.setUserId;
export const getUsername = session.getUsername;
export const setUsername = session.setUsername;
export const clearSession = session.clear;
export const isAdminLoggedIn = session.isAdminLoggedIn;
export const isDonorLoggedIn = session.isDonorLoggedIn;

// ─── HTTP client ──────────────────────────────────────────────────────────────

const http = createHttpClient({ baseUrl: BASE_URL, session });
const request = http.request;
export const logout = http.logout;

// ─── API Object ───────────────────────────────────────────────────────────────

export const api = {
  // ── Admin Auth ──────────────────────────────────────────────────────────────
  adminLogin: (data) =>
    request("/api/v1/auth/admin/login", {
      method: "POST",
      body: data,
    }, "/admin/login"),

  adminSignup: (data) =>
    request("/api/v1/admins/register", {
      method: "POST",
      body: data,
    }, "/admin/login"),

  adminInvite: (data) =>
    request("/api/v1/admins/invite", {
      method: "POST",
      body: data,
    }, "/admin/login"),

  adminForgotPassword: (data) =>
    request("/api/v1/auth/admin/password-reset/request", {
      method: "POST",
      body: data,
    }, "/admin/login"),

  adminOTPValidation: (data) =>
    request("/api/v1/auth/admin/password-reset/confirm", {
      method: "POST",
      body: data,
    }, "/admin/login"),

  adminNewPassword: (data) =>
    request("/api/v1/auth/admin/password-reset/confirm", {
      method: "POST",
      body: data,
    }, "/admin/login"),

  // ── Donor Auth ──────────────────────────────────────────────────────────────
  donorLogin: (data) =>
    request("/api/v1/auth/donor/login", {
      method: "POST",
      body: data,
    }),

  donorRegister: (data) =>
    request("/api/v1/donors/register", {
      method: "POST",
      body: data,
    }),

  donorOTPValidation: (data) =>
    request("/api/v1/auth/donor/password-reset/confirm", {
      method: "POST",
      body: data,
    }),

  donorForgotPassword: (data) =>
    request("/api/v1/auth/donor/password-reset/request", {
      method: "POST",
      body: data,
    }),

  donorNewPassword: (data) =>
    request("/api/v1/auth/donor/password-reset/confirm", {
      method: "POST",
      body: data,
    }),

  // ── Donors ──────────────────────────────────────────────────────────────────
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

  // ── Blood Requests ──────────────────────────────────────────────────────────
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

  // ── Blood Banks (uses hospitals endpoint) ───────────────────────────────────
  getBloodBanks: (params) => {
    const query = new URLSearchParams(params || {}).toString();
    return request(`/api/v1/hospitals/blood-banks${query ? `?${query}` : ""}`, {
      method: "GET",
    });
  },

  // ── Queries ─────────────────────────────────────────────────────────────────
  submitQuery: (data) =>
    request("/api/v1/queries/", {
      method: "POST",
      body: data,
    }),

  getQueries: (params) => {
    const query = new URLSearchParams(params || {}).toString();
    return request(`/api/v1/queries/${query ? `?${query}` : ""}`, {
      method: "GET",
    }, "/admin/login");
  },

  replyToQuery: (queryId, data) =>
    request(`/api/v1/queries/${queryId}/reply`, {
      method: "POST",
      body: data,
    }, "/admin/login"),

  deleteQuery: (queryId) =>
    request(`/api/v1/queries/${queryId}`, {
      method: "DELETE",
    }, "/admin/login"),

  // ── Admin Profile ───────────────────────────────────────────────────────────
  updateAdminDetails: (adminId, data) =>
    request(`/api/v1/admins/${adminId}`, {
      method: "PUT",
      body: data,
    }, "/admin/login"),

  getAdminProfile: () =>
    request("/api/v1/admins/me/profile", {
      method: "GET",
    }, "/admin/login"),

  // ── Admin Dashboard / Analytics ─────────────────────────────────────────────
  getAdminDashboardData: () =>
    request("/api/v1/analytics/dashboard", {
      method: "GET",
    }, "/admin/login"),

  getAdminAnalytics: () =>
    request("/api/v1/analytics/dashboard", {
      method: "GET",
    }, "/admin/login"),

  // ── Hospitals ────────────────────────────────────────────────────────────────
  addHospital: (data) =>
    request("/api/v1/hospitals/", {
      method: "POST",
      body: data,
    }, "/admin/login"),

  getHospitals: (params) => {
    const query = new URLSearchParams(params || {}).toString();
    return request(`/api/v1/hospitals/${query ? `?${query}` : ""}`, {
      method: "GET",
    });
  },

  getHospitalAutofill: (q) =>
    request(`/api/v1/hospitals/autofill?q=${encodeURIComponent(q)}`, {
      method: "GET",
    }),

  // ── Certificates ─────────────────────────────────────────────────────────────
  generateCertificate: (data) =>
    request("/api/v1/certificates/generate", {
      method: "POST",
      body: data,
    }, "/admin/login"),

  listCertificates: () =>
    request("/api/v1/certificates/", {
      method: "GET",
    }, "/admin/login"),
};
