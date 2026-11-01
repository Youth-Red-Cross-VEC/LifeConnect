import { useState } from "react";
import { api } from "../services/api";
import { buildClosePayload, errorText } from "../services/requests";

const EMPTY = { report: "", units_donated: 0, donation_date: "", donor_ids: "" };

// Closes a request through POST /api/v1/blood-requests/{id}/close.
// onClosed(requestId, message) is called after the server accepts it.
export default function CloseRequestForm({ requestId, onClosed }) {
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const setField = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

  const submit = async (event, sendCertificates) => {
    event.preventDefault();
    setError("");
    setIsSaving(true);
    try {
      const res = await api.closeRequest(requestId, buildClosePayload(requestId, form, sendCertificates));
      if (res && res.message && !res.detail) {
        onClosed(requestId, res.message);
      } else {
        setError(errorText(res, "Failed to close the request."));
      }
    } catch {
      setError("Server error. Try again.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <form onSubmit={(e) => submit(e, false)}>
      <label><strong>Report</strong></label>
      <input className="input-field" type="text" value={form.report} maxLength={255}
        onChange={(e) => setField("report", e.target.value)} />

      <label><strong>Units Donated</strong></label>
      <input className="input-field" type="number" min={0} value={form.units_donated} required
        onChange={(e) => setField("units_donated", e.target.value)} />

      <label><strong>Responded Donor IDs</strong> (comma separated)</label>
      <input className="input-field" type="text" value={form.donor_ids}
        onChange={(e) => setField("donor_ids", e.target.value)} />

      <label><strong>Donation Date</strong></label>
      <input className="input-field" type="date" value={form.donation_date} required
        onChange={(e) => setField("donation_date", e.target.value)} />

      {error && <p role="alert" style={{ color: "#c82333" }}>{error}</p>}

      <div className="form-actions">
        <button type="submit" className="close-btn" disabled={isSaving}>Close Request</button>
        <button type="button" className="close-btn" disabled={isSaving}
          onClick={(e) => submit(e, true)}>
          Close Request and Send Certificate
        </button>
      </div>
    </form>
  );
}
