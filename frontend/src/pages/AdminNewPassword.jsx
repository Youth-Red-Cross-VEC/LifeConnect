import React from "react";

const AdminNewPassword = ({ email }) => {
  return (
    <div className="center">
      <div className="card narrow">
        <h2 className="title">Set Your New Password</h2>

        <form
          method="POST"
          action="/admin/new-password"
          className="stack"
        >
          <div className="field">
            <span>Enter Your New Password</span>
            <input type="password" name="password" required />
          </div>

          <div className="field">
            <span>Confirm Your New Password</span>
            <input type="password" name="confirmpassword" required />
          </div>

          {/* Email passed from backend or parent */}
          <input type="hidden" name="email" value={email || ""} />

          <button type="submit" className="primary full">
            Reset Password
          </button>
        </form>
      </div>
    </div>
  );
};

export default AdminNewPassword;