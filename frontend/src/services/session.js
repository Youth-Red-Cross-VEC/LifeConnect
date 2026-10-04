// Single owner of the browser-side auth state (token, refresh token, who is logged in).
// Pages and components must go through this module instead of touching localStorage.

const KEYS = {
  token: "lc_token",
  refreshToken: "lc_refresh_token",
  userType: "lc_user_type",
  userId: "lc_user_id",
  username: "lc_username",
};

function memoryStorage() {
  const data = new Map();
  return {
    getItem: (k) => (data.has(k) ? data.get(k) : null),
    setItem: (k, v) => data.set(k, String(v)),
    removeItem: (k) => data.delete(k),
  };
}

// `storage` is injectable so the logic can be tested without a browser.
export function createSession(storage) {
  // Storage can throw (private mode, blocked cookies): degrade to an in-memory session.
  let store = storage;
  const safe = (fn, fallback) => {
    try {
      return fn(store);
    } catch {
      store = memoryStorage();
      return fn(store) ?? fallback;
    }
  };

  const get = (key) => safe((s) => s.getItem(key), null);
  const set = (key, value) => safe((s) => s.setItem(key, value));

  return {
    getToken: () => get(KEYS.token),
    setToken: (v) => set(KEYS.token, v),
    getRefreshToken: () => get(KEYS.refreshToken),
    setRefreshToken: (v) => set(KEYS.refreshToken, v),
    getUserType: () => get(KEYS.userType),
    setUserType: (v) => set(KEYS.userType, v),
    getUserId: () => get(KEYS.userId),
    setUserId: (v) => set(KEYS.userId, v),
    getUsername: () => get(KEYS.username),
    setUsername: (v) => set(KEYS.username, v),
    isLoggedIn: () => Boolean(get(KEYS.token)),
    isAdminLoggedIn: () => Boolean(get(KEYS.token)) && get(KEYS.userType) === "admin",
    isDonorLoggedIn: () => Boolean(get(KEYS.token)) && get(KEYS.userType) === "donor",
    // Store everything a successful login response carries, in one place.
    saveLogin: (res, userType) => {
      set(KEYS.token, res.access_token);
      set(KEYS.refreshToken, res.refresh_token);
      set(KEYS.userType, userType);
      set(KEYS.userId, res.user_id || "");
      set(KEYS.username, res.username || "");
    },
    clear: () => {
      Object.values(KEYS).forEach((key) => safe((s) => s.removeItem(key)));
    },
  };
}

const defaultStorage = typeof localStorage !== "undefined" ? localStorage : memoryStorage();
export const session = createSession(defaultStorage);
