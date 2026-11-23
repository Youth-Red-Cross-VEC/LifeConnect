// Pure helpers for blood-request pages (no React, so they can be tested with node:test).

// Remove a request from a list. List items from the API are keyed by `id`.
export function removeRequestById(requests, requestId) {
  return requests.filter((request) => request.id !== requestId);
}

// Text for an error body from the API client. FastAPI sends `detail` as a string for
// application errors and as an array of { msg, loc } objects for validation errors.
export function errorText(res, fallback) {
  const detail = res?.detail;
  if (typeof detail === "string" && detail) return detail;
  if (Array.isArray(detail) && detail.length) {
    return detail.map((item) => item?.msg).filter((msg) => typeof msg === "string" && msg).join("; ") || fallback;
  }
  return [res?.message, res?.error].find((msg) => typeof msg === "string" && msg) || fallback;
}

// "DON-1, DON-2" -> ["DON-1", "DON-2"]; blanks and the legacy placeholder "None" are dropped.
export function parseDonorIds(text) {
  return String(text ?? "")
    .split(/[,\s]+/)
    .map((id) => id.trim())
    .filter((id) => id && id.toLowerCase() !== "none");
}

// Body for POST /api/v1/blood-requests/{id}/close (schema: BloodRequestClose).
export function buildClosePayload(requestId, form, sendCertificates) {
  return {
    request_id: requestId,
    report: form.report?.trim() ? form.report.trim() : null,
    units_donated: Number(form.units_donated) || 0,
    donation_date: form.donation_date,
    donor_ids: parseDonorIds(form.donor_ids),
    send_certificates: Boolean(sendCertificates),
  };
}

const LABELS = [
  ["id", "Request ID"],
  ["patient_name", "Patient Name"],
  ["patient_age", "Patient Age"],
  ["blood_group", "Blood Group"],
  ["contact_number", "Contact Number"],
  ["attendant_name", "Attendant Name"],
  ["units_required", "Units Required"],
  ["request_reason", "Request Reason"],
  ["due_date", "Due Date"],
  ["status", "Status"],
  ["approved_admin_id", "Approved Admin ID"],
  ["closed_admin_id", "Closed Admin ID"],
];

const HOSPITAL_LABELS = [
  ["id", "Hospital ID"],
  ["hospital_name", "Hospital Name"],
  ["hospital_address", "Hospital Address"],
  ["city", "City"],
];

// [label, value] pairs for the details panel, from GET /blood-requests/{id}.
// Missing values show as an em dash so the panel never prints "undefined".
export function detailRows(request) {
  const show = (value) => (value === null || value === undefined || value === "" ? "—" : String(value));
  const rows = LABELS.map(([key, label]) => [label, show(request?.[key])]);
  const hospital = request?.hospital;
  if (hospital) {
    rows.push(...HOSPITAL_LABELS.map(([key, label]) => [label, show(hospital[key])]));
  } else {
    rows.push(["Hospital Name", show(request?.hospital_name)]);
  }
  return rows;
}
