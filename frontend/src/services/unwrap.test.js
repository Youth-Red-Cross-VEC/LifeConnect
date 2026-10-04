import { test } from "node:test";
import assert from "node:assert/strict";

import { LoadError, messageFor, unwrapData, unwrapList } from "./unwrap.js";

test("unwrapList returns arrays and rejects { detail } bodies with the server message", () => {
  assert.deepEqual(unwrapList([1, 2]), [1, 2]);
  assert.throws(() => unwrapList({ detail: "Not authorized" }, "Failed"), { name: "LoadError", message: "Not authorized" });
});

test("unwrapList falls back to the generic message for null, undefined and strings", () => {
  for (const bad of [null, undefined, "<html>502</html>"]) {
    assert.throws(() => unwrapList(bad, "Failed to load requests."), { message: "Failed to load requests." });
  }
});

test("unwrapData accepts objects and rejects error bodies", () => {
  assert.deepEqual(unwrapData({ a: 1 }), { a: 1 });
  assert.throws(() => unwrapData({ error: "boom" }), { message: "boom" });
  assert.throws(() => unwrapData([1]), LoadError);
});

test("messageFor shows LoadError text but hides raw network/bug errors", () => {
  assert.equal(messageFor(new LoadError("Nope"), "Generic"), "Nope");
  assert.equal(messageFor(new TypeError("Failed to fetch"), "Generic"), "Generic");
});
