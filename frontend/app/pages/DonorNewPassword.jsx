"use client";

import { useMemo, useState } from "react";

export default function DonorNewPassword({ email = "donor@example.com" }) {
  const [form, setForm] = useState({ password: "", confirmpassword: "" });
  const [error, setError] = useState("");

  const payload = useMemo(
    () => ({
      email,
      ...form,
    }),
    [email, form],
  );

  const onSubmit = (e) => {
    e.preventDefault();
    setError("");
    if (!form.password || !form.confirmpassword) {
      setError("Both fields are required");
      return;
    }
    if (form.password !== form.confirmpassword) {
      setError("Passwords do not match");
      return;
    }
    // eslint-disable-next-line no-console
    console.log("Reset password payload", payload);
  };

  const update = (key) => (value) => setForm((prev) => ({ ...prev, [key]: value }));

  return (
    <main className="center">
      <div className="card narrow">
        <h2 className="accent">Set Your New Password</h2>
        <p className="muted">Create a strong and unique password.</p>

        {error ? <div className="error">{error}</div> : null}

        <form className="stack" onSubmit={onSubmit}>
          <label className="field">
            <span>Email</span>
            <input value={email} readOnly />
          </label>

          <label className="field">
            <span>New Password</span>
            <input
              type="password"
              value={form.password}
              onChange={(e) => update("password")(e.target.value)}
              required
            />
          </label>

          <label className="field">
            <span>Confirm Password</span>
            <input
              type="password"
              value={form.confirmpassword}
              onChange={(e) => update("confirmpassword")(e.target.value)}
              required
            />
          </label>

          <button className="primary full" type="submit">
            Reset Password
          </button>
        </form>

        <div className="json-block">
          <div className="small muted">Payload for backend</div>
          <pre>{JSON.stringify(payload, null, 2)}</pre>
        </div>
      </div>
    </main>
  );
}

