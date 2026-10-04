import { request } from "./client.js";

export const certificateApi = {
  // ── Certificates ──
  generateCertificate: (data) =>
    request("/api/v1/certificates/generate", {
      method: "POST",
      body: data,
    }, "/admin/login"),

  listCertificates: () =>
    request("/api/v1/certificates/", {
      method: "GET",
    }, "/admin/login"),

  // Binary download (needs the bearer token, so it cannot be a plain <a href>).
  // Resolves to a Blob; hand it to saveBlob() from ../download to prompt a save.
  downloadCertificate: (filename) =>
    request(`/api/v1/certificates/download/${encodeURIComponent(filename)}`, {
      method: "GET",
      responseType: "blob",
    }, "/admin/login"),
};
