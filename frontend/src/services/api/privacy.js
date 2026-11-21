import { request } from "./client.js";

const path = "/api/v1/privacy/erasure-requests";

export const privacyApi = {
  myErasure: () => request(`${path}/mine`),
  submitErasure: (currentPassword) => request(path, {
    method: "POST", body: { current_password: currentPassword },
  }),
  pendingErasures: () => request(path, {}, "/admin/login"),
  reviewErasure: (id, decision) => request(`${path}/${encodeURIComponent(id)}`, {
    method: "PATCH", body: { decision },
  }, "/admin/login"),
};
