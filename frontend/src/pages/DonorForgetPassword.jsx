import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";

export default function DonorForgetPassword() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      const res = await api.donorForgotPassword({ email });
      if (res && (res.success || res.message)) {
        navigate("/donor/otp-validation");
      } else {
        setError(res?.message || "Failed to send OTP. Please try again.");
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

        {error ? (
          <div className="error" style={{ marginBottom: "16px" }}>{error}</div>
        ) : null}

        <form className="stack" onSubmit={handleSubmit}>
          <label className="field">
            <span>Email Address</span>
            <input
              type="email"
              id="email"
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
          We will send the OTP to the email you provide. Please check your inbox.
        </p>

        <div className="footer-links" style={{ textAlign: "center", marginTop: "12px" }}>
          <a href="/donor/login">Back to Login</a>
        </div>
      </div>
    </div>
  );
}
