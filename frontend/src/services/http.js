// Shared HTTP client: auth header, JSON bodies, safe response parsing, one-shot token
// refresh and a single, central 401 policy. Everything is injectable so it can be tested.

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// Turn any response into something callers can use. Never assumes JSON:
//  - 204/205 or an empty body           -> null
//  - JSON                                -> the parsed value
//  - anything else (HTML error pages...) -> the text; failures become { detail }
async function parseBody(response) {
  if (response.status === 204 || response.status === 205) return null;
  const type = response.headers?.get?.("content-type") || "";
  let body = null;
  try {
    if (type.includes("json")) {
      body = await response.json();
    } else {
      const text = await response.text();
      body = text === "" ? null : text;
    }
  } catch {
    body = null;
  }
  if (!response.ok && (body === null || typeof body !== "object")) {
    return { detail: response.statusText || `Request failed (${response.status})` };
  }
  return body;
}

export function createHttpClient({
  baseUrl,
  session,
  fetchImpl = (...args) => fetch(...args),
  redirect = (path) => {
    window.location.href = path;
  },
}) {
  let refreshInFlight = null;

  // Exchange the stored refresh token for a new pair. Concurrent callers share one request:
  // the server rotates tokens, so a second parallel call would look like token reuse.
  function refreshSession() {
    const refreshToken = session.getRefreshToken();
    if (!refreshToken) return Promise.resolve(false);
    if (!refreshInFlight) {
      refreshInFlight = fetchImpl(`${baseUrl}/api/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })
        .then(async (res) => {
          if (!res.ok) return false;
          const data = await res.json();
          session.setToken(data.access_token);
          session.setRefreshToken(data.refresh_token);
          return true;
        })
        .catch(() => false)
        .finally(() => {
          refreshInFlight = null;
        });
    }
    return refreshInFlight;
  }

  // options.responseType: "blob" returns a Blob for downloads (throws ApiError on failure).
  async function request(endpoint, options = {}, redirectOn401 = "/donor/login") {
    const { responseType, _retried, ...fetchOptions } = options;
    const token = session.getToken();

    const headers = {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(fetchOptions.headers || {}),
    };

    let body = fetchOptions.body;
    if (body && typeof body === "object" && !(body instanceof FormData)) {
      // FastAPI expects JSON bodies, never URL-encoded form data
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(body);
    }

    const response = await fetchImpl(`${baseUrl}${endpoint}`, { ...fetchOptions, headers, body });

    // An authenticated call was rejected: the access token expired. Refresh once and replay.
    // A 401 with NO token is just an answer (e.g. a wrong password at login), not an expired
    // session, so it must not clear anything or redirect.
    if (response.status === 401 && token) {
      if (!_retried && (await refreshSession())) {
        return request(endpoint, { ...options, _retried: true }, redirectOn401);
      }
      session.clear();
      redirect(redirectOn401);
      return undefined;
    }

    if (responseType === "blob") {
      if (!response.ok) {
        const err = await parseBody(response);
        throw new ApiError(err?.detail || `Request failed (${response.status})`, response.status);
      }
      return response.blob();
    }

    return parseBody(response);
  }

  // Revoke the refresh token on the server, then clear the local session.
  async function logout() {
    const refreshToken = session.getRefreshToken();
    try {
      if (refreshToken) {
        await fetchImpl(`${baseUrl}/api/v1/auth/logout`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      }
    } finally {
      session.clear();
    }
  }

  return { request, logout };
}
