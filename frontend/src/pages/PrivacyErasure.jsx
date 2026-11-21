import { useState } from "react";
import { Link } from "react-router-dom";
import { useApiData } from "../hooks/useApiData";
import { api } from "../services/api";
import { unwrapData, unwrapList } from "../services/unwrap";

async function loadMine() {
  const result = await api.myErasure();
  return result === null ? null : unwrapData(result, "Unable to load your request.");
}

async function loadPending() {
  return unwrapList(await api.pendingErasures(), "Unable to load erasure requests.");
}

export function DonorErasure() {
  const { data, error, isLoading, reload } = useApiData(loadMine, {
    initial: null, errorMessage: "Unable to load your request.",
  });
  const [password, setPassword] = useState("");
  const [notice, setNotice] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setSubmitting(true);
    setNotice("");
    try {
      unwrapData(await api.submitErasure(password), "Unable to request erasure.");
      setNotice("Request submitted for review.");
      reload();
    } catch (err) {
      setNotice(err.message);
    } finally {
      setPassword("");
      setSubmitting(false);
    }
  }

  return (
    <main className="center">
      <section className="card narrow">
        <h1 className="title">Request account erasure</h1>
        <p>If approved, your account and linked personal data will be removed and your sessions will end. Donation totals will be kept.</p>
        {isLoading && <p role="status">Loading request…</p>}
        {error && <p role="alert">{error}</p>}
        {notice && <p role="status">{notice}</p>}
        {data?.status === "pending" && <p>Awaiting review. Reference {data.id}</p>}
        {data?.status === "rejected" && <p>Your previous request was declined. You can submit a new one.</p>}
        {!isLoading && !error && data?.status !== "pending" && (
          <form className="stack" onSubmit={submit}>
            <label className="field">
              <span>Current password</span>
              <input type="password" autoComplete="current-password" required maxLength={72}
                value={password} onChange={(e) => setPassword(e.target.value)} disabled={submitting} />
            </label>
            <button className="primary" disabled={submitting}>{submitting ? "Submitting…" : "Request erasure"}</button>
          </form>
        )}
        <Link to="/donor/dashboard">Back to dashboard</Link>
      </section>
    </main>
  );
}

export function AdminErasure() {
  const { data, error, isLoading, reload } = useApiData(loadPending, {
    initial: [], errorMessage: "Unable to load erasure requests.",
  });
  const [decision, setDecision] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState("");

  async function review() {
    setSubmitting(true);
    setNotice("");
    try {
      unwrapData(await api.reviewErasure(decision.id, decision.action), "Unable to review the request.");
      setNotice(decision.action === "approve" ? "Account erasure approved." : "Request declined.");
      setDecision(null);
      reload();
    } catch (err) {
      setNotice(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="center">
      <section className="card">
        <h1 className="title">Account erasure requests</h1>
        {isLoading && <p role="status">Loading requests…</p>}
        {error && <p role="alert">{error}</p>}
        {notice && <p role="status">{notice}</p>}
        {!isLoading && !error && data.length === 0 && <p>There are no pending requests.</p>}
        {!isLoading && !error && data.map((item) => (
          <div key={item.id} className="stack">
            <p>Donor {item.donor_id} · Reference {item.id}</p>
            {decision?.id === item.id ? (
              <>
                <p>{decision.action === "approve" ? "Permanently erase this account?" : "Decline this request?"}</p>
                <button className="primary" disabled={submitting} onClick={review}>Confirm</button>
                <button disabled={submitting} onClick={() => setDecision(null)}>Cancel</button>
              </>
            ) : (
              <div>
                <button disabled={submitting} onClick={() => setDecision({ id: item.id, action: "approve" })}>Approve</button>
                <button disabled={submitting} onClick={() => setDecision({ id: item.id, action: "reject" })}>Decline</button>
              </div>
            )}
          </div>
        ))}
        <Link to="/admin/dashboard">Back to dashboard</Link>
      </section>
    </main>
  );
}
