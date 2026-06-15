import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";

export default function AdminSignup() {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({
    email: "",
    username: "",
    password: "",
    confirm_password: "",
    vec_registration_number: "",
    date_of_birth: "",
    mobile_number: "",
    department: "",
  });
  const [otp, setOtp] = useState("");
  const [signupResponseData, setSignupResponseData] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleNext = (e) => {
    e.preventDefault();
    if (form.password !== form.confirm_password) {
      setError("Passwords do not match");
      return;
    }
    setError("");
    setStep(2);
  };

  const handlePrev = () => {
    setError("");
    setStep(1);
  };

  // Submit Step 2 to register and trigger OTP email
  const handleSubmitSignup = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      const res = await api.adminSignup(form);
      if (res && res.success) {
        setSignupResponseData(res);
        setStep(3);
      } else {
        setError(res?.message || "Signup failed. Please try again.");
      }
    } catch {
      setError("Server error. Try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Submit Step 3 (OTP) to inject data into DB
  const handleSubmitOTP = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      const payload = {
        otp: otp,
        generated_otp: signupResponseData.one_time_password,
        email: signupResponseData.email,
        password: form.password,
        username: signupResponseData.username,
        vec_registration_number: signupResponseData.vec_registration_number,
        date_of_birth: signupResponseData.date_of_birth,
        mobile_number: signupResponseData.mobile_number,
        department: signupResponseData.department,
        admin_id: signupResponseData.admin_id,
        authentication_id: signupResponseData.authentication_id,
      };

      const res = await api.donorOTPValidation(payload);
      if (res && res.success) {
        navigate("/admin/login");
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
    <div className="as-page">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

        /* ── Page shell ── */
        .as-page {
          font-family: "Poppins", sans-serif;
          min-height: 100vh;
          width: 100vw;
          margin: 0;
          padding: 0;
          display: flex;
          background: #f4f4f4;
          overflow: hidden;
          position: relative;
        }

        /* ── Mobile navbar (hidden on desktop) ── */
        .as-navbar {
          display: none;
        }

        /* ══════════════════════════════
           LEFT PANEL — red background
        ══════════════════════════════ */
        .as-left {
          flex: 0 0 48%;
          background: linear-gradient(160deg, #c0000a 0%, #8b0000 100%);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 48px 44px;
          position: relative;
          overflow: hidden;
        }

        /* Decorative circle behind content */
        .as-left::before {
          content: "";
          position: absolute;
          width: 520px;
          height: 520px;
          background: rgba(255, 255, 255, 0.06);
          border-radius: 50%;
          bottom: -120px;
          right: -120px;
        }
        .as-left::after {
          content: "";
          position: absolute;
          width: 300px;
          height: 300px;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 50%;
          top: -80px;
          left: -80px;
        }

        /* Brand name — absolute top-left of the full page */
        .as-brand {
          position: absolute;
          top: 22px;
          left: 24px;
          z-index: 20;
          text-decoration: none;
          color: #fff;
          font-weight: 800;
          font-size: 1.3rem;
          font-family: "Raleway", sans-serif;
          letter-spacing: 0.5px;
        }

        /* Illustration */
        .as-illustration {
          width: 100%;
          max-width: 340px;
          border-radius: 16px;
          display: block;
          margin: 0 auto 32px;
          position: relative;
          z-index: 1;
          filter: drop-shadow(0 8px 24px rgba(0,0,0,0.25));
        }

        /* Quote */
        .as-quote {
          font-size: 0.92rem;
          line-height: 1.7;
          color: rgba(255, 233, 233, 0.92);
          text-align: center;
          font-style: italic;
          font-weight: 500;
          max-width: 360px;
          position: relative;
          z-index: 1;
        }

        /* Arrow — top-right corner of the red panel */
        .as-arrow {
          position: absolute;
          top: 20px;
          right: 20px;
          z-index: 10;
        }
        .as-arrow img {
          width: 64px;
          height: auto;
          animation: as-bounce 1.4s ease-in-out infinite;
          filter: drop-shadow(0 2px 6px rgba(0,0,0,0.35));
        }
        @keyframes as-bounce {
          0%, 100% { transform: translateY(0); }
          50%       { transform: translateY(-8px); }
        }

        /* ══════════════════════════════
           RIGHT PANEL — white form card
        ══════════════════════════════ */
        .as-right {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 48px 32px;
          background: #f4f4f4;
        }

        .as-card {
          background: #ffffff;
          border-radius: 24px;
          padding: 44px 38px;
          width: 100%;
          max-width: 420px;
          box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
        }

        /* Heading */
        .as-card h2 {
          text-align: center;
          margin: 0 0 28px;
          font-size: 1.75rem;
          font-weight: 800;
          color: #b30001;
          letter-spacing: 0.5px;
        }

        /* Step indicator */
        .as-steps {
          display: flex;
          justify-content: center;
          gap: 8px;
          margin-bottom: 28px;
        }
        .as-step-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: #e0e0e0;
          transition: background 0.3s, transform 0.3s;
        }
        .as-step-dot.active {
          background: #b30001;
          transform: scale(1.3);
        }

        /* Form group */
        .as-form-group {
          margin-bottom: 18px;
        }
        .as-form-group label {
          display: block;
          font-size: 13px;
          font-weight: 600;
          color: #333;
          margin-bottom: 6px;
        }
        .as-form-group input {
          width: 100%;
          padding: 11px 16px;
          border: 2px solid #e0e0e0;
          border-radius: 12px;
          font-size: 14px;
          font-family: "Poppins", sans-serif;
          box-sizing: border-box;
          transition: border-color 0.25s, box-shadow 0.25s;
          outline: none;
          color: #222;
          background: #fafafa;
        }
        .as-form-group input:focus {
          border-color: #b30001;
          box-shadow: 0 0 0 3px rgba(179, 0, 1, 0.12);
          background: #fff;
        }
        .as-form-group input:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        /* Buttons */
        .as-btn {
          width: 100%;
          padding: 13px;
          background: #b30001;
          color: #fff;
          font-size: 15px;
          font-weight: 700;
          font-family: "Poppins", sans-serif;
          border: none;
          border-radius: 12px;
          cursor: pointer;
          margin-top: 8px;
          transition: background 0.25s, transform 0.15s, box-shadow 0.25s;
          box-shadow: 0 4px 14px rgba(179, 0, 1, 0.3);
        }
        .as-btn:hover:not(:disabled) {
          background: #950001;
          transform: translateY(-1px);
          box-shadow: 0 6px 18px rgba(179, 0, 1, 0.4);
        }
        .as-btn:active:not(:disabled) {
          transform: translateY(0);
        }
        .as-btn:disabled {
          opacity: 0.65;
          cursor: not-allowed;
        }
        .as-btn.secondary {
          background: #f0f0f0;
          color: #555;
          box-shadow: none;
        }
        .as-btn.secondary:hover:not(:disabled) {
          background: #e2e2e2;
          transform: translateY(-1px);
        }

        .as-btn-group {
          display: flex;
          gap: 12px;
          margin-top: 8px;
        }
        .as-btn-group .as-btn {
          margin-top: 0;
          flex: 1;
        }

        /* Alerts */
        .as-error {
          background: #fff0f0;
          color: #b30001;
          border: 1px solid #f5c6c6;
          padding: 10px 14px;
          border-radius: 10px;
          font-size: 13px;
          font-weight: 600;
          text-align: center;
          margin-bottom: 18px;
        }
        .as-success-msg {
          background: #edfbf0;
          color: #1a6b35;
          border: 1px solid #b2dfbc;
          padding: 10px 14px;
          border-radius: 10px;
          font-size: 13px;
          font-weight: 600;
          text-align: center;
          margin-bottom: 18px;
        }

        /* Login link */
        .as-login-link {
          text-align: center;
          font-size: 13px;
          color: #777;
          margin-top: 20px;
        }
        .as-login-link a {
          color: #b30001;
          font-weight: 600;
          text-decoration: none;
        }
        .as-login-link a:hover {
          text-decoration: underline;
        }

        /* ══════════════════════════════
           MOBILE  ≤ 768px
        ══════════════════════════════ */
        @media (max-width: 768px) {
          .as-page {
            flex-direction: column;
            overflow-y: auto;
          }

          /* Show mobile navbar */
          .as-navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            background: #b30001;
            color: #fff;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            z-index: 1000;
            box-sizing: border-box;
          }
          .as-navbar-logo {
            font-size: 18px;
            font-weight: 800;
          }
          .as-navbar-buttons a {
            color: #b30001;
            text-decoration: none;
            margin-left: 8px;
            font-weight: 700;
            padding: 8px 16px;
            background: #fff;
            border-radius: 20px;
            font-size: 13px;
          }

          /* Hide left panel on mobile */
          .as-left {
            display: none;
          }

          .as-right {
            flex: 1;
            padding: 96px 16px 32px;
          }

          .as-card {
            padding: 32px 24px;
          }
        }
      `}</style>

      {/* ── Mobile navbar ── */}
      <nav className="as-navbar">
        <div className="as-navbar-logo">Life Connect</div>
        <div className="as-navbar-buttons">
          <a href="/admin/login">Login</a>
          <a href="/">Home</a>
        </div>
      </nav>

      {/* Brand — top-left corner of the page */}
      <a href="/" className="as-brand">Life Connect</a>

      {/* ══ LEFT PANEL ══ */}
      <div className="as-left">
        {/* Arrow — top-right corner of the red box */}
        <div className="as-arrow">
          <img
            src="/images/admin_signup/arrow.png"
            alt="Arrow pointing to the form"
          />
        </div>

        <img
          src="/images/admin_signup/img4.png"
          className="as-illustration"
          alt="Admin illustration"
        />

        <p className="as-quote">
          &ldquo;Behind every blood donor is a silent hero like you. By joining
          our dedicated admin team, you ensure every precious drop of blood
          saves a life. Together, we can connect donors to those in urgent need,
          bringing hope and second chances to families.&rdquo;
        </p>


      </div>

      {/* ══ RIGHT PANEL ══ */}
      <div className="as-right">
        <div className="as-card">
          <h2>Admin Sign Up</h2>

          {/* Step dots */}
          <div className="as-steps">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`as-step-dot${step === s ? " active" : ""}`}
              />
            ))}
          </div>

          {error && <div className="as-error">{error}</div>}

          {/* ── Step 1: Account Info ── */}
          {step === 1 && (
            <form onSubmit={handleNext}>
              <div className="as-form-group">
                <label htmlFor="email">Email</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={form.email}
                  onChange={handleChange}
                  placeholder="you@example.com"
                  required
                  disabled={isLoading}
                />
              </div>
              <div className="as-form-group">
                <label htmlFor="username">Username</label>
                <input
                  type="text"
                  id="username"
                  name="username"
                  value={form.username}
                  onChange={handleChange}
                  placeholder="Your display name"
                  required
                  disabled={isLoading}
                />
              </div>
              <div className="as-form-group">
                <label htmlFor="password">Password</label>
                <input
                  type="password"
                  id="password"
                  name="password"
                  value={form.password}
                  onChange={handleChange}
                  placeholder="Create a password"
                  required
                  disabled={isLoading}
                />
              </div>
              <div className="as-form-group">
                <label htmlFor="confirm_password">Confirm Password</label>
                <input
                  type="password"
                  id="confirm_password"
                  name="confirm_password"
                  value={form.confirm_password}
                  onChange={handleChange}
                  placeholder="Repeat your password"
                  required
                  disabled={isLoading}
                />
              </div>
              <button type="submit" className="as-btn">
                Next →
              </button>
              <div className="as-login-link">
                Already have an account? <a href="/admin/login">Log in</a>
              </div>
            </form>
          )}

          {/* ── Step 2: Personal Details ── */}
          {step === 2 && (
            <form onSubmit={handleSubmitSignup}>
              <div className="as-form-group">
                <label htmlFor="vec_registration_number">
                  VEC Registration Number
                </label>
                <input
                  type="text"
                  id="vec_registration_number"
                  name="vec_registration_number"
                  value={form.vec_registration_number}
                  onChange={handleChange}
                  placeholder="e.g. VEC-2024-001"
                  required
                  disabled={isLoading}
                />
              </div>
              <div className="as-form-group">
                <label htmlFor="date_of_birth">Date of Birth</label>
                <input
                  type="date"
                  id="date_of_birth"
                  name="date_of_birth"
                  value={form.date_of_birth}
                  onChange={handleChange}
                  required
                  disabled={isLoading}
                />
              </div>
              <div className="as-form-group">
                <label htmlFor="mobile_number">Mobile Number</label>
                <input
                  type="tel"
                  id="mobile_number"
                  name="mobile_number"
                  value={form.mobile_number}
                  onChange={handleChange}
                  placeholder="+91 XXXXX XXXXX"
                  required
                  disabled={isLoading}
                />
              </div>
              <div className="as-form-group">
                <label htmlFor="department">Department</label>
                <input
                  type="text"
                  id="department"
                  name="department"
                  value={form.department}
                  onChange={handleChange}
                  placeholder="e.g. Computer Science"
                  disabled={isLoading}
                />
              </div>
              <div className="as-btn-group">
                <button
                  type="button"
                  className="as-btn secondary"
                  onClick={handlePrev}
                  disabled={isLoading}
                >
                  ← Back
                </button>
                <button type="submit" className="as-btn" disabled={isLoading}>
                  {isLoading ? "Signing up…" : "Sign Up"}
                </button>
              </div>
            </form>
          )}

          {/* ── Step 3: OTP Verification ── */}
          {step === 3 && (
            <form onSubmit={handleSubmitOTP}>
              <div className="as-success-msg">
                ✅ An OTP has been sent to the administrator email for
                verification. Please check and enter it below.
              </div>
              <div className="as-form-group">
                <label htmlFor="otp">Enter OTP</label>
                <input
                  type="text"
                  id="otp"
                  name="otp"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  required
                  disabled={isLoading}
                  placeholder="6-digit OTP"
                  maxLength={6}
                />
              </div>
              <button type="submit" className="as-btn" disabled={isLoading}>
                {isLoading ? "Verifying…" : "Verify OTP"}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
