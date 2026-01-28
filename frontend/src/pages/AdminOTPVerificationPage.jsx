import React from "react";

const AdminOTPVerificationPage = ({
  email,
  password,
  username,
  vec_registration_number,
  date_of_birth,
  mobile_number,
  department,
  admin_id,
  authentication_id,
  one_time_password,
}) => {
  return (
    <div className="center">
      <div className="card narrow">
        <h2 className="title">OTP Verification</h2>
        <p className="muted center-text">
          Enter the OTP that has been sent to the email address you provided
          earlier. Ensure the OTP is entered correctly to proceed with
          verification.
        </p>

        <form
          method="POST"
          action="/admin/verify-otp"
          className="stack"
        >
          <div className="field">
            <span>Enter OTP</span>
            <input type="text" name="otp" required />
          </div>

          {/* Hidden fields preserved for backend compatibility */}
          <input type="hidden" name="email" value={email || ""} />
          <input type="hidden" name="password" value={password || ""} />
          <input type="hidden" name="username" value={username || ""} />
          <input
            type="hidden"
            name="vec_registration_number"
            value={vec_registration_number || ""}
          />
          <input
            type="hidden"
            name="date_of_birth"
            value={date_of_birth || ""}
          />
          <input
            type="hidden"
            name="mobile_number"
            value={mobile_number || ""}
          />
          <input
            type="hidden"
            name="department"
            value={department || ""}
          />
          <input type="hidden" name="admin_id" value={admin_id || ""} />
          <input
            type="hidden"
            name="authentication_id"
            value={authentication_id || ""}
          />
          <input
            type="hidden"
            name="generated_otp"
            value={one_time_password || ""}
          />

          <button type="submit" className="primary full">
            Verify OTP
          </button>
        </form>
      </div>
    </div>
  );
};

export default AdminOTPVerificationPage;