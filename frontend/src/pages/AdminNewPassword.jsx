import { useState } from "react";
import { Link, Navigate, useNavigate, useOutletContext } from "react-router-dom";
import { api, clearSession, getUserType } from "../services/api";

const AdminNewPassword = () => {
  const [form, setForm] = useState({ password: "", confirmpassword: "" });
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { reset, setReset } = useOutletContext();

  if (!reset?.email || !reset.otp) {
    return <Navigate to="/admin/forgot-password" replace state={{ restartReset: true }} />;
  }

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!form.password || !form.confirmpassword) {
      setError("Both fields are required");
      return;
    }
    if (form.password !== form.confirmpassword) {
      setError("Passwords do not match");
      return;
    }
    if (new TextEncoder().encode(form.password).length > 72) {
      setError("Password must be at most 72 bytes.");
      return;
    }
    setIsLoading(true);
    try {
      const res = await api.adminNewPassword({ email: reset.email, otp: reset.otp, new_password: form.password });
      if (res?.message) {
        if (getUserType() === "admin") clearSession();
        navigate("/admin/login", { replace: true, state: { passwordReset: true } });
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

  return (
    <div className="center">
      <div className="card narrow">
        <h2 className="title">Set Your New Password</h2>
        <p className="muted">Use at least 8 characters, including an uppercase letter and a digit.</p>

        {error ? <div role="alert" className="error">{error}</div> : null}

        <form className="stack" onSubmit={handleSubmit}>
          <label className="field">
            <span>Email</span>
            <input value={reset.email} readOnly />
          </label>

          <label className="field">
            <span>Enter Your New Password</span>
            <input
              type="password"
              autoComplete="new-password"
              name="password"
              value={form.password}
              onChange={handleChange}
              required
              disabled={isLoading}
            />
          </label>

          <label className="field">
            <span>Confirm Your New Password</span>
            <input
              type="password"
              autoComplete="new-password"
              name="confirmpassword"
              value={form.confirmpassword}
              onChange={handleChange}
              required
              disabled={isLoading}
            />
          </label>

          <button type="submit" className="primary full" disabled={isLoading}>
            {isLoading ? "Resetting..." : "Reset Password"}
          </button>
        </form>
        {!isLoading && (
          <div className="footer-links">
            <Link to="/admin/otp-verification">Enter a different code</Link>
            {" · "}
            <Link to="/admin/forgot-password" onClick={() => setReset(null)}>Request a new code</Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminNewPassword;
