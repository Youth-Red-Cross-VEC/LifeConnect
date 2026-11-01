import test from "node:test";
import assert from "node:assert/strict";

import { safeHttpUrl } from "./safeUrl.js";

test("accepts absolute http and https URLs", () => {
  assert.equal(safeHttpUrl("https://example.org"), "https://example.org/");
  assert.equal(safeHttpUrl("http://example.org/path?q=1#frag"), "http://example.org/path?q=1#frag");
  assert.equal(safeHttpUrl("  https://example.org/a b  "), "https://example.org/a%20b");
  assert.equal(safeHttpUrl("HTTPS://EXAMPLE.ORG"), "https://example.org/");
});

test("rejects script-bearing and non-web schemes in any spelling", () => {
  for (const bad of [
    "javascript:alert(1)",
    "JaVaScRiPt:alert(1)",
    "  javascript:alert(1)",
    "java\nscript:alert(1)",
    "java\tscript:alert(1)",
    "\u0001javascript:alert(1)",
    "data:text/html,<script>alert(1)</script>",
    "vbscript:msgbox(1)",
    "file:///etc/passwd",
    "blob:https://example.org/uuid",
    "ftp://example.org",
    "mailto:someone@example.org",
  ]) {
    assert.equal(safeHttpUrl(bad), null, JSON.stringify(bad));
  }
});

test("rejects relative, scheme-relative and scheme-less values instead of resolving them", () => {
  for (const bad of ["//example.org", "/admin/login", "example.org", "www.example.org", "?x=1", "#top"]) {
    assert.equal(safeHttpUrl(bad), null, JSON.stringify(bad));
  }
});

test("rejects anything that is not a non-empty string", () => {
  for (const bad of [undefined, null, 0, 42, {}, [], true, "", "   ", "\n"]) {
    assert.equal(safeHttpUrl(bad), null, JSON.stringify(bad));
  }
});

// Guard: a data-driven href is a stored-XSS sink (javascript: URLs). Every `href={...}` in the app must go
// through safeHttpUrl(), except Header's NavLink, whose href prop is only ever fed constant internal paths.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..");
const CONSTANT_HREF_ALLOWLIST = new Set(["components/Header.jsx"]);

function jsxFiles(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return jsxFiles(path);
    return path.endsWith(".jsx") ? [path] : [];
  });
}

test("no component puts an unchecked value in an href", () => {
  const offenders = [];
  for (const file of jsxFiles(SRC)) {
    const rel = relative(SRC, file).replaceAll("\\", "/");
    if (CONSTANT_HREF_ALLOWLIST.has(rel)) continue;
    const lines = readFileSync(file, "utf8").split("\n");
    lines.forEach((line, i) => {
      for (const match of line.matchAll(/href=\{([^}]*)\}/g)) {
        if (!match[1].trim().startsWith("safeHttpUrl(")) offenders.push(`${rel}:${i + 1}  href={${match[1]}}`);
      }
    });
  }
  assert.deepEqual(offenders, []);
});
