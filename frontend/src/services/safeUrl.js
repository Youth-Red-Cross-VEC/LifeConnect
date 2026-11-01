// Turn a server-supplied web address into something safe to put in an <a href>, or null.
//
// React escapes text, but it does not stop `href="javascript:..."` from running when clicked. Only
// absolute http(s) URLs are allowed: anything else (javascript:, data:, vbscript:, file:, scheme-relative
// "//host", a bare "example.com", control-character tricks) yields null so the caller renders no link.

export function safeHttpUrl(value) {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  if (trimmed === "") return null;
  let url;
  try {
    // No base URL: a relative or scheme-relative value must fail to parse, not resolve against our own origin.
    url = new URL(trimmed);
  } catch {
    return null;
  }
  // The parser has already stripped tabs/newlines and lower-cased the scheme, so "Java\nScript:" lands here as "javascript:".
  return url.protocol === "http:" || url.protocol === "https:" ? url.href : null;
}
