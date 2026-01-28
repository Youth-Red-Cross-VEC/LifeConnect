import React from "react";

const AdminLogin = () => {
  return (
    <div className="center">
      <div className="page auth">
        {/* Left CTA / Intro */}
        <div className="cta-card">
          <div className="topbar">
            <div className="logo" style={{ color: "#fff" }}>Life Connect</div>
            <div className="nav-actions">
              <a href="/admin/signup" className="ghost-btn">Sign Up</a>
              <a href="/" className="ghost-btn">Home</a>
            </div>
          </div>

          <h3 className="title" style={{ color: "#fff" }}>New here?</h3>
          <p>
            Join our esteemed community of lifesavers and make a significant
            impact. By signing up as an admin, you become the backbone of a
            life-saving mission, ensuring every donation reaches those who need
            it most.
          </p>
          <a href="/admin/signup" className="primary">Sign Up</a>

          <img
            src="/images/adminLogin/img5.png"
            alt="Admin illustration"
            className="cta-image"
          />
        </div>

        {/* Login Card */}
        <div className="card auth-card narrow">
          <h2 className="title">Admin Login</h2>

          <form method="POST" action="/admin/login" className="stack">
            <div className="field">
              <span>Email</span>
              <input type="email" name="email" required />
            </div>

            <div className="field">
              <span>Password</span>
              <input type="password" name="password" required />
            </div>

            <div className="field">
              <span>Captcha</span>
              <div className="captcha-row">
                <input type="text" name="captcha" required />
                <div className="captcha-img" />
              </div>
            </div>

            <button type="submit" className="primary full">Login</button>
          </form>

          <div className="footer-links">
            <a href="/admin/forgot-password">Forget Password</a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminLogin;