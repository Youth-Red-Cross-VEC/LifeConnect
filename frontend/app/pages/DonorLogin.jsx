"use client";

import { useMemo, useState } from "react";

const sampleCaptcha = {
  id: "captcha-123",
  imageUrl: "https://dummyimage.com/140x50/8b0000/ffffff&text=8D5K9",
};

export default function DonorLogin({ captcha = sampleCaptcha }) {
  const [form, setForm] = useState({
    email: "",
    password: "",
    captcha_value: "",
  });
  const [error, setError] = useState("");

  const payload = useMemo(
    () => ({
      ...form,
      captcha_id: captcha.id,
    }),
    [form, captcha.id],
  );

  const onSubmit = (e) => {
    e.preventDefault();
    setError("");
    if (!form.email || !form.password || !form.captcha_value) {
      setError("All fields are required");
      return;
    }
    // eslint-disable-next-line no-console
    console.log("Login payload", payload);
  };

  const update = (key) => (value) => setForm((prev) => ({ ...prev, [key]: value }));

  return (
    <div className="page auth">
      <nav className="topbar">
        <div className="logo">LifeConnect</div>
        <div className="nav-actions">
          <button className="ghost-btn" onClick={() => (window.location.href = "/signup")}>
            Sign Up
          </button>
          <button className="ghost-btn" onClick={() => (window.location.href = "/")}>
            Home
          </button>
        </div>
      </nav>

      <section className="cta-card">
        <h3>New here?</h3>
        <p>
          "Give the gift of life with every drop you share. Become a hero—donate blood and inspire
          hope!"
        </p>
        <button className="primary" onClick={() => (window.location.href = "/signup")}>
          Sign Up
        </button>
        <img
          className="cta-image"
          src="https://dummyimage.com/320x200/8b0000/ffffff&text=Donate+Blood"
          alt="Donate blood illustration"
        />
      </section>

      <form className="card auth-card" onSubmit={onSubmit}>
        <h2>Donor Login</h2>
        {error ? <div className="error">{error}</div> : null}

        <label className="field">
          <span>Email</span>
          <input
            type="email"
            value={form.email}
            onChange={(e) => update("email")(e.target.value)}
            required
          />
        </label>

        <label className="field">
          <span>Password</span>
          <input
            type="password"
            value={form.password}
            onChange={(e) => update("password")(e.target.value)}
            required
          />
        </label>

        <label className="field">
          <span>Captcha</span>
          <div className="captcha-row">
            <input
              value={form.captcha_value}
              onChange={(e) => update("captcha_value")(e.target.value)}
              required
              placeholder="Enter text from image"
            />
            {captcha.imageUrl ? (
              <img src={captcha.imageUrl} alt="captcha" className="captcha-img" />
            ) : null}
          </div>
        </label>

        <button className="primary full" type="submit">
          Login
        </button>

        <a className="link" href="/forgot-password">
          Forgot Password?
        </a>

        <div className="json-block">
          <div className="small muted">Payload for backend</div>
          <pre>{JSON.stringify(payload, null, 2)}</pre>
        </div>
      </form>
    </div>
  );
}

