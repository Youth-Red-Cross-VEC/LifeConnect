import { request } from "./client.js";

export const authApi = {
  // ── Admin Auth ──
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

  // ── Donor Auth ──
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
};
