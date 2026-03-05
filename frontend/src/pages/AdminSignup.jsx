import { useState } from "react";

export default function AdminSignup({ onSignup }) {
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

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleNext = (e) => {
    e.preventDefault();
    setStep(2);
  };

  const handlePrev = (e) => {
    e.preventDefault();
    setStep(1);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSignup?.(form);
  };

  return (
    <>
      <style>{`
        .admin-signup-page {
          font-family: "Poppins", sans-serif;
          background-color: #f8f8f8;
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 100vh;
          padding: 20px;
          position: relative;
          overflow: hidden;
        }

        .signup-container {
          background: white;
          padding: 40px 30px;
          border-radius: 25px;
          width: 380px;
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
          position: relative;
          bottom: 5px;
          left: 300px;
        }

        .signup-container::before {
          content: "";
          position: absolute;
          height: 1500px;
          width: 1500px;
          top: -10%;
          right: 48%;
          background-image: linear-gradient(-40deg, #b30001, 0%, #b30001 100%);
          transform: translate(-20%, -50%);
          border-radius: 50%;
        }

        .signup-container h2 {
          text-align: center;
          margin-bottom: 20px;
          font-size: 2.2rem;
          font-weight: bolder;
          color: #b30001;
          position: relative;
        }

        .form-step { display: none; }
        .form-step.active { display: block; }

        .form-group { margin-bottom: 20px; }

        .form-group label {
          font-size: 15px;
          font-weight: bold;
          color: #0e0b0b;
          display: block;
          margin-bottom: 5px;
        }

        .form-group input {
          width: 100%;
          padding: 12px;
          border: 2px solid #b30001;
          border-radius: 20px;
          font-size: 14px;
          box-sizing: border-box;
        }

        .signup-btn-main {
          padding: 12px;
          background: #b30001;
          color: white;
          font-size: 16px;
          border: none;
          border-radius: 20px;
          font-weight: bold;
          cursor: pointer;
          width: 100%;
          margin-top: 10px;
        }

        .signup-btn-main:hover { background: #8a0001; }

        .button-group {
          display: flex;
          justify-content: space-between;
          gap: 10px;
        }

        .button-group .signup-btn-main { width: 48%; }

        .red-shape-content {
          position: absolute;
          top: -5px;
          left: -750px;
          color: white;
          text-align: center;
          z-index: 1;
          width: 400px;
        }

        .red-shape-content p {
          font-size: 1rem;
          padding: 0.5rem 0;
          line-height: 1.5;
          margin-top: 10px;
          text-align: center;
          font-weight: bold;
        }

        .flash-messages {
          margin-bottom: 20px;
          position: absolute;
          top: 20px;
          left: 50%;
          transform: translateX(-50%);
          width: 90%;
          max-width: 400px;
          z-index: 1000;
        }

        .flash-messages .alert {
          padding: 15px;
          border-radius: 5px;
          margin-bottom: 10px;
          font-size: 14px;
          font-weight: bold;
          text-align: center;
        }

        .alert-success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-danger  { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .alert-info    { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .alert-warning { background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; }

        @media (max-width: 768px) {
          .signup-container::before,
          .red-shape-content { display: none; }
          .signup-container { left: 0; right: 0; }
        }
      `}</style>

      <div className="admin-signup-page">
        <div className="signup-container">
          {/* Left decorative text inside the red blob */}
          <div className="red-shape-content">
            <p>
              "Behind every blood donor is a silent hero like you. By joining our
              dedicated admin team, you ensure every precious drop of blood saves a
              life. Together, we can connect donors to those in urgent need,
              bringing hope and second chances to families."
            </p>
          </div>

          <h2>Admin Sign Up</h2>

          <form onSubmit={step === 1 ? handleNext : handleSubmit}>
            {/* Step 1 */}
            <div className={`form-step ${step === 1 ? "active" : ""}`}>
              <div className="form-group">
                <label htmlFor="email">Email:</label>
                <input type="email" id="email" name="email" value={form.email} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label htmlFor="username">Username:</label>
                <input type="text" id="username" name="username" value={form.username} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label htmlFor="password">Password:</label>
                <input type="password" id="password" name="password" value={form.password} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label htmlFor="confirm_password">Confirm Password:</label>
                <input type="password" id="confirm_password" name="confirm_password" value={form.confirm_password} onChange={handleChange} required />
              </div>
              <button type="submit" className="signup-btn-main">Next</button>
            </div>

            {/* Step 2 */}
            <div className={`form-step ${step === 2 ? "active" : ""}`}>
              <div className="form-group">
                <label htmlFor="vec_registration_number">VEC Registration Number:</label>
                <input type="text" id="vec_registration_number" name="vec_registration_number" value={form.vec_registration_number} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label htmlFor="date_of_birth">Date of Birth:</label>
                <input type="date" id="date_of_birth" name="date_of_birth" value={form.date_of_birth} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label htmlFor="mobile_number">Mobile Number:</label>
                <input type="tel" id="mobile_number" name="mobile_number" value={form.mobile_number} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label htmlFor="department">Department:</label>
                <input type="text" id="department" name="department" value={form.department} onChange={handleChange} />
              </div>
              <div className="button-group">
                <button type="button" className="signup-btn-main" onClick={handlePrev}>Previous</button>
                <button type="submit" className="signup-btn-main">Sign Up</button>
              </div>
            </div>
          </form>
        </div>
      </div>

      {/*
        ======================================================
        BACKEND CALL STRUCTURE — Admin Signup
        ======================================================

        ENDPOINT
        --------
        POST /admin/register

        REQUEST BODY
        ------------
        {
          email: string,
          username: string,
          password: string,
          confirm_password: string,
          vec_registration_number: string,
          date_of_birth: string (YYYY-MM-DD),
          mobile_number: string,
          department: string
        }

        AUTH
        ----
        No auth required (public registration)

        RESPONSE (example)
        ------------------
        { success: true, message: "Admin registered successfully" }

        FRONTEND RESPONSIBILITY
        -----------------------
        - Multi-step form (step 1: credentials, step 2: personal info)
        - Show flash-style messages for success/error
        - Redirect to /admin/login on success

        ERROR CASES
        -----------
        - 400 → validation error (e.g. passwords don't match)
        - 409 → email/username already exists
        - 500 → server error
      */}
    </>
  );
}
