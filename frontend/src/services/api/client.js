// Shared client instance for every API module.
// In Docker: VITE_API_URL is "" so requests go to same origin (nginx proxies /api/* → api:8000)
// In local dev: VITE_API_URL is "http://localhost:8000" for direct access
import { createHttpClient } from "../http.js";
import { session } from "../session.js";

const BASE_URL = import.meta.env?.VITE_API_URL ?? "http://localhost:8000";

const http = createHttpClient({ baseUrl: BASE_URL, session });

export const request = http.request;
export const logout = http.logout;
export const restoreSession = http.restoreSession;

// Session helpers (re-exported so pages keep importing them from "services/api")
export const getToken = session.getToken;
export const setToken = session.setToken;
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
