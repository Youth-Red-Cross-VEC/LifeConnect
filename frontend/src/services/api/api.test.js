import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

import { api } from "./index.js";

const dir = path.dirname(fileURLToPath(import.meta.url));
const SKIP = new Set(["client.js", "index.js"]);

test("P2-33: domain modules do not define the same call twice (the merge would hide one)", async () => {
  const seen = new Map();
  for (const file of readdirSync(dir).filter((f) => f.endsWith(".js") && !f.endsWith(".test.js") && !SKIP.has(f))) {
    const mod = await import(`./${file}`);
    for (const [exportName, group] of Object.entries(mod)) {
      for (const key of Object.keys(group)) {
        assert.ok(!seen.has(key), `${key} is in both ${seen.get(key)} and ${file}:${exportName}`);
        seen.set(key, `${file}:${exportName}`);
      }
    }
  }
  assert.deepEqual(Object.keys(api).sort(), [...seen.keys()].sort());
});

test("api exposes the calls the pages rely on", () => {
  for (const name of [
    "donorLogin", "adminLogin", "getDonors", "approveRequest", "closeRequest", "getHospitals",
    "updateHospital", "deleteHospital", "generateCertificate", "downloadCertificate", "getQueries",
  ]) {
    assert.equal(typeof api[name], "function", name);
  }
});
