import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";

const AdminOTPVerificationPage = () => {
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
      const res = await api.adminOTPValidation({ otp });
      if (res && (res.success || res.token)) {
        navigate("/admin/new-password");
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
    <div className="center">
      <div className="card narrow">
        <h2 className="title">OTP Verification</h2>
        <p className="muted center-text">
          Enter the OTP that has been sent to the email address you provided
          earlier. Ensure the OTP is entered correctly to proceed with
          verification.
        </p>

        {error ? <div className="error">{error}</div> : null}

        <form className="stack" onSubmit={handleSubmit}>
          <div className="field">
            <span>Enter OTP</span>
            <input
              type="text"
              name="otp"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              required
              disabled={isLoading}
              placeholder="Enter the OTP sent to your email"
            />
          </div>

          <button type="submit" className="primary full" disabled={isLoading}>
            {isLoading ? "Verifying..." : "Verify OTP"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AdminOTPVerificationPage;