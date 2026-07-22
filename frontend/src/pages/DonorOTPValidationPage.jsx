import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";

export default function DonorOTPValidationPage() {
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!otp.trim()) {
      setError("Please enter the OTP");
      return;
    }
    setIsLoading(true);
    try {
      const res = await api.donorOTPValidation({ otp });
      if (res && (res.success || res.token)) {
        navigate("/donor/new-password");
      } else {
        setError(res?.message || "Invalid OTP. Please try again.");
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
          OTP Verification
        </h2>
        <p className="muted" style={{ textAlign: "center", marginBottom: "20px" }}>
          Enter the OTP that has been sent to your registered email address.
          Ensure the OTP is entered correctly to proceed with verification.
        </p>

        {error ? (
          <div className="error" style={{ marginBottom: "16px" }}>{error}</div>
        ) : null}

        <form className="stack" onSubmit={handleSubmit}>
          <label className="field">
            <span>Enter OTP</span>
            <input
              type="text"
              id="otp"
              name="otp"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              required
              disabled={isLoading}
              placeholder="Enter the OTP sent to your email"
              style={{ letterSpacing: "4px", textAlign: "center", fontSize: "1.2rem" }}
            />
          </label>

          <button className="primary full" type="submit" disabled={isLoading}>
            {isLoading ? "Verifying..." : "Verify OTP"}
          </button>
        </form>

        <div className="footer-links" style={{ textAlign: "center", marginTop: "12px" }}>
          <a href="/donor/forgot-password">Resend OTP</a>
        </div>
      </div>
    </div>
  );
}
