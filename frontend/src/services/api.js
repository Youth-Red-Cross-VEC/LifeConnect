// Central API service for LifeConnect
// All backend routes are under /api/v1 (FastAPI on port 8000).
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ─── Token Utilities ─────────────────────────────────────────────────────────

export const getToken = () => localStorage.getItem("lc_token");

export const setToken = (token) => localStorage.setItem("lc_token", token);

export const removeToken = () => localStorage.removeItem("lc_token");

export const isLoggedIn = () => Boolean(getToken());

// ─── Private Request Helper ───────────────────────────────────────────────────

async function request(endpoint, options = {}, redirectOn401 = "/donor/login") {
  const token = getToken();

  const headers = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  let body = options.body;
  if (body && typeof body === "object" && !(body instanceof FormData)) {
    // FastAPI expects JSON bodies — never send URL-encoded form data
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(body);
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
    body,
  });

  // Handle 401 — clear token and redirect to the appropriate login page
  if (response.status === 401) {
    removeToken();
    window.location.href = redirectOn401;
    return;
  }

  return response.json();
}

// ─── API Object ───────────────────────────────────────────────────────────────

export const api = {
  // Admin Auth
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

  // Donor Auth
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

  // Donors
  getDonors: (params) => {
    const query = new URLSearchParams(params).toString();
    return request(`/api/v1/donors/${query ? `?${query}` : ""}`, {
      method: "GET",
    });
  },

  // TODO: No FastAPI equivalent for /get_blood_banks.
  // The blood banks feature was in the old Flask backend but has no
  // corresponding endpoint in the new FastAPI backend (/app/api/v1/).
  // Either implement GET /api/v1/hospitals/ as a replacement (hospitals serve
  // as blood banks), or add a dedicated /api/v1/blood-banks/ endpoint.
  // For now this call will fail — do NOT replace with a guessed route.
  getBloodBanks: () => {
    console.warn(
      "[api.getBloodBanks] No backend endpoint exists for blood banks in the FastAPI backend. " +
      "This call will fail until a /api/v1/blood-banks/ endpoint is implemented."
    );
    return Promise.resolve({ error: "No blood banks endpoint available", items: [] });
  },

  // Blood Requests
  generateBloodRequest: (data) =>
    request("/api/v1/blood-requests/", {
      method: "POST",
      body: data,
    }),

  // Queries
  submitQuery: (data) =>
    request("/api/v1/queries/", {
      method: "POST",
      body: data,
    }),

  // Donor profile
  modifyDonorDetails: (donorId, data) =>
    request(`/api/v1/donors/${donorId}`, {
      method: "PATCH",
      body: data,
    }),

  // Admin profile
  updateAdminDetails: (adminId, data) =>
    request(`/api/v1/admins/${adminId}`, {
      method: "PUT",
      body: data,
    }, "/admin/login"),

  // Admin dashboard / analytics
  getAdminDashboardData: () =>
    request("/api/v1/analytics/dashboard", {
      method: "GET",
    }, "/admin/login"),

  getAdminAnalytics: () =>
    request("/api/v1/analytics/dashboard", {
      method: "GET",
    }, "/admin/login"),

  // Hospitals
  addHospital: (data) =>
    request("/api/v1/hospitals/", {
      method: "POST",
      body: data,
    }, "/admin/login"),
};
