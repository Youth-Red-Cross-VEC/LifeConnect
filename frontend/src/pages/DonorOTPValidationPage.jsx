import { useState } from "react";
import { Link, Navigate, useNavigate, useOutletContext } from "react-router-dom";

export default function DonorOTPValidationPage() {
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { reset, setReset } = useOutletContext();

  if (!reset?.email) {
    return <Navigate to="/donor/forgot-password" replace state={{ restartReset: true }} />;
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
    navigate("/donor/new-password");
  };

  return (
    <div className="center" style={{ minHeight: "100vh" }}>
      <div className="card narrow" style={{ maxWidth: "420px", width: "100%" }}>
        <h2 className="title" style={{ color: "#bf0001", textAlign: "center" }}>
          OTP Verification
        </h2>
        <p className="muted" style={{ textAlign: "center", marginBottom: "20px" }}>
          Enter the OTP that has been sent to your registered email address.
          We’ll verify it when you submit your new password.
        </p>

        {error ? (
          <div role="alert" className="error" style={{ marginBottom: "16px" }}>{error}</div>
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
              inputMode="numeric"
              autoComplete="one-time-code"
              placeholder="Enter the OTP sent to your email"
              style={{ letterSpacing: "4px", textAlign: "center", fontSize: "1.2rem" }}
            />
          </label>

          <button className="primary full" type="submit">
            Continue
          </button>
        </form>

        <div className="footer-links" style={{ textAlign: "center", marginTop: "12px" }}>
          <Link to="/donor/forgot-password" onClick={() => setReset(null)}>Request a new code</Link>
        </div>
      </div>
    </div>
  );
}
