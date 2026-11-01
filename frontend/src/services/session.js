// Access tokens live only in this module's memory. Refresh credentials are held in an
// HttpOnly cookie and are intentionally never readable from JavaScript.
const KEYS = {
  userType: "lc_user_type",
  userId: "lc_user_id",
  username: "lc_username",
};

function memoryStorage() {
  const data = new Map();
  return {
    getItem: (key) => (data.has(key) ? data.get(key) : null),
    setItem: (key, value) => data.set(key, String(value)),
    removeItem: (key) => data.delete(key),
  };
}

export function createSession(storage = memoryStorage()) {
  let token = null;
  let store = storage;
  const safe = (fn) => {
    try {
      return fn(store);
    } catch {
      store = memoryStorage();
      return fn(store);
    }
  };
  const get = (key) => safe((s) => s.getItem(key));
  const set = (key, value) => safe((s) => s.setItem(key, value));

  return {
    getToken: () => token,
    setToken: (value) => { token = value || null; },
    getUserType: () => get(KEYS.userType),
    setUserType: (value) => set(KEYS.userType, value),
    getUserId: () => get(KEYS.userId),
    setUserId: (value) => set(KEYS.userId, value),
    getUsername: () => get(KEYS.username),
    setUsername: (value) => set(KEYS.username, value),
    isLoggedIn: () => Boolean(token),
    isAdminLoggedIn: () => Boolean(token) && get(KEYS.userType) === "admin",
    isDonorLoggedIn: () => Boolean(token) && get(KEYS.userType) === "donor",
    saveLogin: (response, userType) => {
      token = response.access_token || null;
      set(KEYS.userType, userType);
      set(KEYS.userId, response.user_id || "");
      set(KEYS.username, response.username || "");
    },
    clear: () => {
      token = null;
      Object.values(KEYS).forEach((key) => safe((s) => s.removeItem(key)));
    },
  };
}

const defaultStorage = typeof sessionStorage !== "undefined" ? sessionStorage : memoryStorage();
export const session = createSession(defaultStorage);
