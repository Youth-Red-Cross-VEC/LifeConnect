import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";

const AdminNewPassword = () => {
  const [form, setForm] = useState({ password: "", confirmpassword: "" });
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

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
    setIsLoading(true);
    try {
      const res = await api.adminNewPassword({ password: form.password, confirmpassword: form.confirmpassword });
      if (res && (res.success || res.message)) {
        navigate("/admin/login");
      } else {
        setError(res?.message || "Failed to reset password. Please try again.");
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

        {error ? <div className="error">{error}</div> : null}

        <form className="stack" onSubmit={handleSubmit}>
          <div className="field">
            <span>Enter Your New Password</span>
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              required
              disabled={isLoading}
            />
          </div>

          <div className="field">
            <span>Confirm Your New Password</span>
            <input
              type="password"
              name="confirmpassword"
              value={form.confirmpassword}
              onChange={handleChange}
              required
              disabled={isLoading}
            />
          </div>

          <button type="submit" className="primary full" disabled={isLoading}>
            {isLoading ? "Resetting..." : "Reset Password"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AdminNewPassword;