// Public surface of the API layer: `import { api, setToken, ... } from "../services/api"`.
// One module per domain; `api` merges them so call sites stay `api.someCall()`.
import { adminApi } from "./admin.js";
import { authApi } from "./auth.js";
import { bloodRequestApi } from "./bloodRequests.js";
import { certificateApi } from "./certificates.js";
import { donorApi } from "./donors.js";
import { hospitalApi } from "./hospitals.js";
import { queryApi } from "./queries.js";
import { privacyApi } from "./privacy.js";

export * from "./client.js";
export { saveBlob } from "../download.js";

export const api = {
  ...authApi,
  ...donorApi,
  ...bloodRequestApi,
  ...hospitalApi,
  ...queryApi,
  ...adminApi,
  ...certificateApi,
  ...privacyApi,
};
