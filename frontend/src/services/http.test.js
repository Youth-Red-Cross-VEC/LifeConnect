// Run with: npm test   (Node's built-in runner; no extra dependencies)
import { test } from "node:test";
import assert from "node:assert/strict";

import { ApiError, createHttpClient } from "./http.js";
import { createSession } from "./session.js";

function memoryStore(initial = {}) {
  const data = new Map(Object.entries(initial));
  return {
    getItem: (k) => (data.has(k) ? data.get(k) : null),
    setItem: (k, v) => data.set(k, String(v)),
    removeItem: (k) => data.delete(k),
  };
}

function response(status, body, { type = "application/json", statusText = "" } = {}) {
  const text = body === undefined ? "" : typeof body === "string" ? body : JSON.stringify(body);
  return {
    status,
    ok: status >= 200 && status < 300,
    statusText,
    headers: { get: (h) => (h.toLowerCase() === "content-type" ? type : null) },
    json: async () => JSON.parse(text),
    text: async () => text,
    blob: async () => ({ size: text.length, kind: "blob" }),
  };
}

// fetch fake: `script` maps "METHOD url" to a response (or a function / array of responses)
function setup({ stored = {}, script = {} } = {}) {
  const session = createSession(memoryStore(stored));
  if (stored.lc_token) session.setToken(stored.lc_token);
  const calls = [];
  const redirects = [];
  const fetchImpl = async (url, init = {}) => {
    calls.push({ url, init });
    const key = `${init.method || "GET"} ${url.replace("http://api", "")}`;
    let next = script[key];
    if (Array.isArray(next)) next = next.shift();
    if (typeof next === "function") next = next(init);
    if (!next) throw new Error(`unscripted request: ${key}`);
    return next;
  };
  const client = createHttpClient({
    baseUrl: "http://api",
    session,
    fetchImpl,
    redirect: (path) => redirects.push(path),
  });
  return { session, calls, redirects, client };
}

test("P2-36: a wrong password at login is returned to the caller, not treated as an expired session", async () => {
  const { client, session, redirects } = setup({
    script: { "POST /api/v1/auth/donor/login": response(401, { detail: "Invalid email or password" }) },
  });
  const res = await client.request("/api/v1/auth/donor/login", { method: "POST", body: { email: "a@b.c", password: "x" } });
  assert.deepEqual(res, { detail: "Invalid email or password" });
  assert.deepEqual(redirects, []);
  assert.equal(session.getToken(), null);
});

test("P2-36: an authenticated call that is rejected and cannot be refreshed clears the session and redirects", async () => {
  const { client, session, redirects } = setup({
    stored: { lc_token: "T" },
    script: { "GET /api/v1/admins/me/profile": response(401, { detail: "expired" }) },
  });
  const res = await client.request("/api/v1/admins/me/profile", {}, "/admin/login");
  assert.equal(res, undefined);
  assert.deepEqual(redirects, ["/admin/login"]);
  assert.equal(session.getToken(), null);
});

test("expired access token: refreshes once and replays the request with the new token", async () => {
  const { client, session, calls, redirects } = setup({
    stored: { lc_token: "OLD" },
    script: {
      "GET /api/v1/donors/": [response(401, { detail: "expired" }), response(200, { items: [1] })],
      "POST /api/v1/auth/refresh": response(200, { access_token: "NEW", user_type: "donor", user_id: "DON-1", username: "Donor" }),
    },
  });
  const res = await client.request("/api/v1/donors/", {}, "/admin/login");
  assert.deepEqual(res, { items: [1] });
  assert.deepEqual(redirects, []);
  assert.equal(session.getToken(), "NEW");
  const replay = calls.filter((c) => c.url.endsWith("/api/v1/donors/")).pop();
  assert.equal(replay.init.headers.Authorization, "Bearer NEW");
});

test("concurrent 401s share a single refresh call (the server rotates tokens)", async () => {
  const { client, calls } = setup({
    stored: { lc_token: "OLD" },
    script: {
      "GET /a": [response(401, {}), response(200, { ok: "a" })],
      "GET /b": [response(401, {}), response(200, { ok: "b" })],
      "POST /api/v1/auth/refresh": response(200, { access_token: "NEW", user_type: "donor", user_id: "DON-1", username: "Donor" }),
    },
  });
  const [a, b] = await Promise.all([client.request("/a"), client.request("/b")]);
  assert.deepEqual([a, b], [{ ok: "a" }, { ok: "b" }]);
  assert.equal(calls.filter((c) => c.url.endsWith("/auth/refresh")).length, 1);
});

test("failed refresh clears the session and redirects once", async () => {
  const { client, session, redirects } = setup({
    stored: { lc_token: "OLD" },
    script: {
      "GET /x": response(401, {}),
      "POST /api/v1/auth/refresh": response(401, { detail: "reuse" }),
    },
  });
  assert.equal(await client.request("/x", {}, "/admin/login"), undefined);
  assert.deepEqual(redirects, ["/admin/login"]);
  assert.equal(session.getToken(), null);
});

test("P2-31: 204 and empty bodies resolve to null instead of throwing", async () => {
  const { client } = setup({
    script: {
      "DELETE /gone": response(204),
      "GET /empty": response(200, undefined),
    },
  });
  assert.equal(await client.request("/gone", { method: "DELETE" }), null);
  assert.equal(await client.request("/empty"), null);
});

test("P2-31: non-JSON success and error bodies are handled", async () => {
  const { client } = setup({
    script: {
      "GET /text": response(200, "plain text", { type: "text/plain" }),
      "GET /bad-gateway": response(502, "<html>nginx</html>", { type: "text/html", statusText: "Bad Gateway" }),
    },
  });
  assert.equal(await client.request("/text"), "plain text");
  assert.deepEqual(await client.request("/bad-gateway"), { detail: "Bad Gateway" });
});

test("JSON error bodies still reach the caller untouched", async () => {
  const { client } = setup({ script: { "GET /nope": response(404, { detail: "Not found" }) } });
  assert.deepEqual(await client.request("/nope"), { detail: "Not found" });
});

test("P2-32: blob downloads return a Blob and send the bearer token", async () => {
  const { client, calls } = setup({
    stored: { lc_token: "T" },
    script: { "GET /api/v1/certificates/download/cert.png": response(200, "PNGDATA", { type: "image/png" }) },
  });
  const blob = await client.request("/api/v1/certificates/download/cert.png", { responseType: "blob" });
  assert.equal(blob.kind, "blob");
  assert.equal(calls[0].init.headers.Authorization, "Bearer T");
  assert.equal(calls[0].init.responseType, undefined, "responseType is not a fetch option");
});

test("P2-32: a failed blob download throws an ApiError with the server message", async () => {
  const { client } = setup({
    stored: { lc_token: "T" },
    script: { "GET /api/v1/certificates/download/x.png": response(404, { detail: "Certificate not found" }) },
  });
  await assert.rejects(
    () => client.request("/api/v1/certificates/download/x.png", { responseType: "blob" }),
    (err) => err instanceof ApiError && err.status === 404 && err.message === "Certificate not found",
  );
});

test("object bodies are sent as JSON", async () => {
  const { client, calls } = setup({ script: { "POST /p": response(200, {}) } });
  await client.request("/p", { method: "POST", body: { a: 1 } });
  assert.equal(calls[0].init.headers["Content-Type"], "application/json");
  assert.equal(calls[0].init.body, '{"a":1}');
});

test("logout revokes the refresh token on the server and clears the session", async () => {
  const { client, session, calls } = setup({
    stored: { lc_token: "T", lc_user_type: "admin" },
    script: { "POST /api/v1/auth/logout": response(200, { message: "Logged out" }) },
  });
  await client.logout();
  assert.equal(calls[0].init.body, undefined);
  assert.equal(calls[0].init.headers["Content-Type"], "application/json");
  assert.equal(session.getToken(), null);
  assert.equal(session.getUserType(), null);
});

test("logout still clears the session when the server is unreachable", async () => {
  const session = createSession(memoryStore());
  session.setToken("T");
  const client = createHttpClient({
    baseUrl: "http://api",
    session,
    fetchImpl: async () => {
      throw new Error("offline");
    },
  });
  await assert.rejects(() => client.logout());
  assert.equal(session.getToken(), null);
});

test("session survives a storage that throws", () => {
  const broken = {
    getItem: () => {
      throw new Error("blocked");
    },
    setItem: () => {
      throw new Error("blocked");
    },
    removeItem: () => {
      throw new Error("blocked");
    },
  };
  const session = createSession(broken);
  session.setToken("T");
  assert.equal(session.getToken(), "T");
  session.clear();
  assert.equal(session.getToken(), null);
});
