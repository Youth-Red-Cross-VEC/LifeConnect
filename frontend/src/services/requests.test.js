import { test } from "node:test";
import assert from "node:assert/strict";

import { buildClosePayload, detailRows, errorText, parseDonorIds, removeRequestById } from "./requests.js";

test("removeRequestById matches list items by `id` (they have no request_id)", () => {
  const list = [{ id: "REQ-1" }, { id: "REQ-2" }, { id: "REQ-3" }];
  assert.deepEqual(removeRequestById(list, "REQ-2"), [{ id: "REQ-1" }, { id: "REQ-3" }]);
  assert.equal(removeRequestById(list, "REQ-9").length, 3);
});

test("removeRequestById does not mutate its input", () => {
  const list = [{ id: "REQ-1" }];
  removeRequestById(list, "REQ-1");
  assert.equal(list.length, 1);
});

test("parseDonorIds splits on commas/whitespace and drops blanks and 'None'", () => {
  assert.deepEqual(parseDonorIds("DON-1, DON-2  DON-3"), ["DON-1", "DON-2", "DON-3"]);
  assert.deepEqual(parseDonorIds("None"), []);
  assert.deepEqual(parseDonorIds(""), []);
  assert.deepEqual(parseDonorIds(undefined), []);
});

test("buildClosePayload matches the BloodRequestClose schema", () => {
  const payload = buildClosePayload(
    "REQ-1",
    { report: " done ", units_donated: "2", donation_date: "2026-10-04", donor_ids: "DON-1, DON-2" },
    true,
  );
  assert.deepEqual(payload, {
    request_id: "REQ-1",
    report: "done",
    units_donated: 2,
    donation_date: "2026-10-04",
    donor_ids: ["DON-1", "DON-2"],
    send_certificates: true,
  });
  assert.equal(buildClosePayload("REQ-1", { report: "  ", units_donated: "", donation_date: "x", donor_ids: "" }, false).report, null);
  assert.equal(buildClosePayload("REQ-1", { units_donated: "abc" }, false).units_donated, 0);
});

test("errorText handles string, validation-array and missing details", () => {
  assert.equal(errorText({ detail: "Cannot close request with status 'Declined'" }, "x"), "Cannot close request with status 'Declined'");
  assert.equal(errorText({ detail: [{ msg: "Field required" }, { msg: "Value is not a valid date" }] }, "x"), "Field required; Value is not a valid date");
  assert.equal(errorText(undefined, "Failed"), "Failed");
  assert.equal(errorText({ detail: [] }, "Failed"), "Failed");
});

test("detailRows shows dashes for missing values and includes nested hospital data", () => {
  const rows = Object.fromEntries(
    detailRows({ id: "REQ-1", patient_name: "A", approved_admin_id: null, hospital: { id: "H-1", hospital_name: "City Care", city: "Chennai" } }),
  );
  assert.equal(rows["Request ID"], "REQ-1");
  assert.equal(rows["Approved Admin ID"], "—");
  assert.equal(rows["Hospital Name"], "City Care");
  assert.equal(rows["Hospital Address"], "—");
  assert.ok(!Object.values(rows).includes("undefined"));
});
