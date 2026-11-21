import { useState } from "react";
import { Link, Navigate, useNavigate, useOutletContext } from "react-router-dom";
import { api, clearSession, getUserType } from "../services/api";

export default function DonorNewPassword() {
  const [form, setForm] = useState({ password: "", confirm_password: "" });
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { reset, setReset } = useOutletContext();

  if (!reset?.email || !reset.otp) {
    return <Navigate to="/donor/forgot-password" replace state={{ restartReset: true }} />;
  }

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!form.password || !form.confirm_password) {
      setError("Both fields are required");
      return;
    }
    if (form.password !== form.confirm_password) {
      setError("Passwords do not match");
      return;
    }
    if (new TextEncoder().encode(form.password).length > 72) {
      setError("Password must be at most 72 bytes.");
      return;
    }
    setIsLoading(true);
    try {
      const res = await api.donorNewPassword({ email: reset.email, otp: reset.otp, new_password: form.password });
      if (res?.message) {
        if (getUserType() === "donor") clearSession();
        // Leaving the reset routes unmounts their in-memory state.
        navigate("/donor/login", { replace: true, state: { passwordReset: true } });
      } else {
        const detail = Array.isArray(res?.detail) ? res.detail[0]?.msg : res?.detail ?? res?.error;
        setError(typeof detail === "string" ? detail : "Failed to reset password. Please try again.");
      }
    } catch {
      setError("Server error. Try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const update = (key) => (value) => setForm((prev) => ({ ...prev, [key]: value }));

  return (
    <main className="center">
      <div className="card narrow">
        <h2 className="accent">Set Your New Password</h2>
        <p className="muted">Use at least 8 characters, including an uppercase letter and a digit.</p>

        {error ? <div role="alert" className="error">{error}</div> : null}

        <form className="stack" onSubmit={onSubmit}>
          <label className="field">
            <span>Email</span>
            <input value={reset.email} readOnly />
          </label>

          <label className="field">
            <span>New Password</span>
            <input
              type="password"
              autoComplete="new-password"
              value={form.password}
              onChange={(e) => update("password")(e.target.value)}
              required
              disabled={isLoading}
            />
          </label>

          <label className="field">
            <span>Confirm Password</span>
            <input
              type="password"
              autoComplete="new-password"
              value={form.confirm_password}
              onChange={(e) => update("confirm_password")(e.target.value)}
              required
              disabled={isLoading}
            />
          </label>

          <button className="primary full" type="submit" disabled={isLoading}>
            {isLoading ? "Resetting..." : "Reset Password"}
          </button>
        </form>
        {!isLoading && (
          <div className="footer-links">
            <Link to="/donor/otp-validation">Enter a different code</Link>
            {" · "}
            <Link to="/donor/forgot-password" onClick={() => setReset(null)}>Request a new code</Link>
          </div>
        )}
      </div>
    </main>
  );
}
