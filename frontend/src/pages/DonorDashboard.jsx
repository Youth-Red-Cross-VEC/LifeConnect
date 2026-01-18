"use client";

import { useMemo, useState } from "react";

const sampleDetails = {
  id: "DON-001",
  name: "Priya S",
  email: "priya@example.com",
  blood_group: "B+",
  last_donated_date: "2024-11-15",
  active_status: "Active",
  number_of_times_donated: 3,
  last_login_date: "2025-12-28 09:15",
  first_name: "Priya",
  last_name: "Srinivasan",
  age: 27,
  contact_number: "+91 98765 43210",
  date_of_birth: "1998-10-02",
  marital_status: "Single",
  secondary_contact_number: "+91 90123 45678",
  aadhar_number: "1234-5678-9012",
  address: "21, Lake View Road",
  city: "Chennai",
  state: "Tamil Nadu",
  country: "India",
  pincode: "600028",
  disease_name: "None",
  disease_description: "NA",
};

function Section({ title, children }) {
  return (
    <section className="section">
      <h3>{title}</h3>
      <div className="stack">{children}</div>
    </section>
  );
}

function Field({ label, value, onChange, readOnly }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input value={value ?? ""} onChange={(e) => onChange?.(e.target.value)} readOnly={readOnly} />
    </label>
  );
}

export default function DonorDashboard({ details = sampleDetails }) {
  const [form, setForm] = useState(details);
  const [saving, setSaving] = useState(false);
  const payload = useMemo(() => ({ ...form }), [form]);

  const update = (key) => (value) => setForm((prev) => ({ ...prev, [key]: value }));

  const onSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    // eslint-disable-next-line no-console
    console.log("Donor update payload", payload);
    await new Promise((res) => setTimeout(res, 250));
    setSaving(false);
  };

  return (
    <div className="page">
      <header className="header">
        <div className="title">LifeConnect Dashboard</div>
        <button className="ghost-btn" onClick={() => (window.location.href = "/")}>
          Home
        </button>
      </header>

      <h2 className="title">Donor Dashboard</h2>

      <form className="card" onSubmit={onSubmit}>
        <Section title="Donor Details">
          <Field label="Donor ID" value={form.id} readOnly />
          <Field label="Name" value={form.name} onChange={update("name")} />
          <Field label="Email" value={form.email} readOnly />
          <Field label="Blood Group" value={form.blood_group} onChange={update("blood_group")} />
          <Field label="Last Donated Date" value={form.last_donated_date} readOnly />
          <Field label="Active Status" value={form.active_status} readOnly />
          <Field label="Times Donated" value={form.number_of_times_donated} readOnly />
          <Field label="Last Login Date" value={form.last_login_date} readOnly />
        </Section>

        <Section title="Personal Details">
          <Field label="First Name" value={form.first_name} onChange={update("first_name")} />
          <Field label="Last Name" value={form.last_name} onChange={update("last_name")} />
          <Field label="Age" value={form.age} onChange={update("age")} />
          <Field
            label="Contact Number"
            value={form.contact_number}
            onChange={update("contact_number")}
          />
          <Field
            label="Date of Birth"
            value={form.date_of_birth}
            onChange={update("date_of_birth")}
          />
          <Field
            label="Marital Status"
            value={form.marital_status}
            onChange={update("marital_status")}
          />
          <Field
            label="Secondary Contact Number"
            value={form.secondary_contact_number}
            onChange={update("secondary_contact_number")}
          />
          <Field
            label="Aadhar Number"
            value={form.aadhar_number}
            onChange={update("aadhar_number")}
          />
        </Section>

        <Section title="Address Details">
          <Field label="Address" value={form.address} onChange={update("address")} />
          <Field label="City" value={form.city} onChange={update("city")} />
          <Field label="State" value={form.state} onChange={update("state")} />
          <Field label="Country" value={form.country} onChange={update("country")} />
          <Field label="Pincode" value={form.pincode} onChange={update("pincode")} />
        </Section>

        <Section title="Disease Details">
          <Field
            label="Disease Name"
            value={form.disease_name}
            onChange={update("disease_name")}
          />
          <Field
            label="Disease Description"
            value={form.disease_description}
            onChange={update("disease_description")}
          />
        </Section>

        <button className="primary full" type="submit" disabled={saving}>
          {saving ? "Saving..." : "Update Details"}
        </button>

        <div className="json-block">
          <div className="small muted">Payload for backend</div>
          <pre>{JSON.stringify(payload, null, 2)}</pre>
        </div>
      </form>

      <div className="footer-links">
        <a href="/forgot-password">Forgot Password?</a>
      </div>
    </div>
  );
}
