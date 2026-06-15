import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";

export default function DonorNewPassword({ email = "" }) {
  const [form, setForm] = useState({ password: "", confirm_password: "" });
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

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
    setIsLoading(true);
    try {
      const res = await api.donorNewPassword({ email, ...form });
      if (res && res.success === true) {
        navigate("/donor/login");
      } else {
        setError(res?.message || "Failed to reset password. Please try again.");
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
        {/* <p className="muted">Create a strong and unique password.</p> */}

        {error ? <div className="error">{error}</div> : null}

        <form className="stack" onSubmit={onSubmit}>
          {email && (
            <label className="field">
              <span>Email</span>
              <input value={email} readOnly />
            </label>
          )}

          <label className="field">
            <span>New Password</span>
            <input
              type="password"
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
      </div>
    </main>
  );
}
