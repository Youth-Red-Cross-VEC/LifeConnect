import { request } from "./client.js";

export const queryApi = {
  // ── Queries ──
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
};
