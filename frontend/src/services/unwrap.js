// Turn the API client's "body or { detail }" answers into data-or-throw, so pages and
// hooks have one way to handle failures instead of re-checking `res.detail` everywhere.

// Thrown with a message that is safe to show to the user.
export class LoadError extends Error {
  constructor(message) {
    super(message);
    this.name = "LoadError";
  }
}

const failure = (res, fallback) =>
  new LoadError((res && typeof res === "object" && (res.detail || res.error)) || fallback);

export function unwrapList(res, fallback = "Failed to load data.") {
  if (Array.isArray(res)) return res;
  throw failure(res, fallback);
}

export function unwrapData(res, fallback = "Failed to load data.") {
  if (res && typeof res === "object" && !Array.isArray(res) && !res.detail && !res.error) return res;
  throw failure(res, fallback);
}

// The message to show for whatever a loader threw: our own LoadError text, otherwise the
// generic message (network failures and bugs must not leak raw error text to users).
export function messageFor(err, fallback) {
  return err instanceof LoadError ? err.message : fallback;
}
