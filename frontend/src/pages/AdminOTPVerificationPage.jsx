import { useState } from "react";
import { Link, Navigate, useNavigate, useOutletContext } from "react-router-dom";

const AdminOTPVerificationPage = () => {
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { reset, setReset } = useOutletContext();

  if (!reset?.email) {
    return <Navigate to="/admin/forgot-password" replace state={{ restartReset: true }} />;
  }

  const handleSubmit = (e) => {
    e.preventDefault();
    setError("");
    const code = otp.trim();
    if (!/^[0-9]{6}$/.test(code)) {
      setError("Enter the six-digit code from your email.");
      return;
    }
    setReset({ email: reset.email, otp: code });
    navigate("/admin/new-password");
  };

  return (
    <div className="center">
      <div className="card narrow">
        <h2 className="title">OTP Verification</h2>
        <p className="muted center-text">
          Enter the OTP that has been sent to the email address you provided
          earlier. We’ll verify it when you submit your new password.
        </p>

        {error ? <div role="alert" className="error">{error}</div> : null}

        <form className="stack" onSubmit={handleSubmit}>
          <label className="field">
            <span>Enter OTP</span>
            <input
              type="text"
              name="otp"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              required
              inputMode="numeric"
              autoComplete="one-time-code"
              placeholder="Enter the OTP sent to your email"
            />
          </label>

          <button type="submit" className="primary full">
            Continue
          </button>
        </form>
        <div className="footer-links">
          <Link to="/admin/forgot-password" onClick={() => setReset(null)}>Request a new code</Link>
        </div>
      </div>
    </div>
  );
};

export default AdminOTPVerificationPage;
