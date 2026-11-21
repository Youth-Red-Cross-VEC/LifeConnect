import { useState } from "react";
import { useLocation, useNavigate, useOutletContext } from "react-router-dom";
import { api } from "../services/api";

const AdminForgetPassword = () => {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { state } = useLocation();
  const { setReset } = useOutletContext();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setReset(null);
    setIsLoading(true);
    try {
      const address = email.trim();
      const res = await api.adminForgotPassword({ email: address });
      if (res?.message) {
        setReset({ email: address });
        navigate("/admin/otp-verification");
      } else {
        const detail = res?.detail ?? res?.error;
        setError(typeof detail === "string" ? detail : "Unable to request a code. Check your email address and try again.");
      }
    } catch {
      setError("Server error. Try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="center" style={{ minHeight: "100vh" }}>
      <div className="card narrow" style={{ maxWidth: "420px", width: "100%" }}>
        <h2 className="title" style={{ color: "#bf0001", textAlign: "center" }}>
          Forgot Password
        </h2>
        <p className="muted" style={{ textAlign: "center", marginBottom: "20px" }}>
          Please enter your email address to receive a One-Time Password (OTP)
          for resetting your password.
        </p>

        {error || state?.restartReset ? (
          <div role="alert" className="error" style={{ marginBottom: "16px" }}>
            {error || "Request a new code to continue resetting your password."}
          </div>
        ) : null}

        <form className="stack" onSubmit={handleSubmit}>
          <label className="field">
            <span>Email Address</span>
            <input
              type="email"
              id="admin-fp-email"
              name="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={isLoading}
              placeholder="Enter your registered email"
            />
          </label>

          <button className="primary full" type="submit" disabled={isLoading}>
            {isLoading ? "Sending OTP..." : "Send OTP"}
          </button>
        </form>

        <p className="muted" style={{ textAlign: "center", marginTop: "16px", fontSize: "0.9rem" }}>
          If the address is registered, check your inbox for a code.
        </p>

        <div className="footer-links" style={{ textAlign: "center", marginTop: "12px" }}>
          <a href="/admin/login">Back to Login</a>
        </div>
      </div>
    </div>
  );
};

export default AdminForgetPassword;
