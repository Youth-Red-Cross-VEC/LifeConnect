// Central API service for LifeConnect
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

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
    if (options.isForm) {
      headers["Content-Type"] = "application/x-www-form-urlencoded";
      const params = new URLSearchParams();
      for (const [key, val] of Object.entries(body)) {
        params.append(key, val !== null && val !== undefined ? val : "");
      }
      body = params.toString();
    } else {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(body);
    }
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
    request("/validate_admin", {
      method: "POST",
      body: data,
      isForm: true,
    }, "/admin/login"),

  adminSignup: (data) =>
    request("/register_new_admin", {
      method: "POST",
      body: data,
      isForm: true,
    }, "/admin/login"),

  adminForgotPassword: (data) =>
    request("/manage_forget_password_admin", {
      method: "POST",
      body: data,
      isForm: true,
    }, "/admin/login"),

  adminOTPValidation: (data) =>
    request("/otp_validation_admin", {
      method: "POST",
      body: data,
      isForm: true,
    }, "/admin/login"),

  adminNewPassword: (data) =>
    request("/new_password_admin", {
      method: "POST",
      body: data,
      isForm: true,
    }, "/admin/login"),

  // Donor Auth
  donorLogin: (data) =>
    request("/donor_login_validation", {
      method: "POST",
      body: data,
      isForm: true,
    }),

  donorRegister: (data) =>
    request("/register_new_donors", {
      method: "POST",
      body: data,
      isForm: true,
    }),

  donorOTPValidation: (data) =>
    request("/verify_otp_and_data_injection", {
      method: "POST",
      body: data,
      isForm: true,
    }),

  donorForgotPassword: (data) =>
    request("/manage_forget_password_donor", {
      method: "POST",
      body: data,
      isForm: true,
    }),

  donorNewPassword: (data) =>
    request("/new_password_donor", {
      method: "POST",
      body: data,
      isForm: true,
    }),

  // Donors
  getDonors: (params) => {
    const query = new URLSearchParams(params).toString();
    return request(`/get_donors${query ? `?${query}` : ""}`, {
      method: "GET",
    });
  },

  getBloodBanks: () =>
    request("/get_blood_banks", {
      method: "GET",
    }),

  // Requests & Queries
  generateBloodRequest: (data) =>
    request("/generate_bloodRequest", {
      method: "POST",
      body: data,
      isForm: true,
    }),

  submitQuery: (data) =>
    request("/get_user_query", {
      method: "POST",
      body: data,
      isForm: true,
    }),

  // Profile
  modifyDonorDetails: (data) =>
    request("/modify_donor_details", {
      method: "POST",
      body: data,
      isForm: true,
    }),

  updateAdminDetails: (data) =>
    request("/update_admin_details", {
      method: "POST",
      body: data,
      isForm: true,
    }, "/admin/login"),

  getAdminDashboardData: async () => {
    if (!getToken()) {
      return {
        admin_name: "Guest Admin",
        active_donors_count: 120,
        total_requests: 45,
        notifications: { Pending: 3, Expired: 1, Not_Approved: 2 },
      };
    }
    return request("/admin/dashboard_data", {
      method: "GET",
    }, "/admin/login");
  },

  getAdminAnalytics: () =>
    request("/admin/render_analytics_page", {
      method: "GET",
    }, "/admin/login"),

  addHospital: (data) =>
    request("/add_hospital", {
      method: "POST",
      body: data,
      isForm: true,
    }, "/admin/login"),
};
