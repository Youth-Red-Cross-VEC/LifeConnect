import { useState } from "react";
import AdminBase from "./AdminBase";
import { api } from "../services/api";

export default function GenerateCertificate() {
  const [form, setForm] = useState({
    donor_name: "",
    donor_email: "",
    donation_date: "",
    blood_group: "",
    location: "",
  });
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMsg("");
    setIsLoading(true);
    try {
      // Uses correct endpoint: POST /api/v1/certificates/generate on port 8000
      const res = await api.generateCertificate(form);
      if (res && (res.success || res.message || res.filename)) {
        setSuccessMsg(res.message || "Certificate sent successfully to the donor.");
        setForm({ donor_name: "", donor_email: "", donation_date: "", blood_group: "", location: "" });
      } else {
        setError(res?.detail || res?.message || "Failed to send certificate. Please try again.");
      }
    } catch {
      setError("Server error. Try again.");
    } finally {
      setIsLoading(false);
    }
  };
  return (
    <AdminBase active="certificates">
      <style>{`
        .cert-form-container {
          margin: 40px auto;
          max-width: 580px;
          background-color: #f8f9fa;
          padding: 36px 32px;
          border-radius: 12px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .cert-form-container h2 {
          text-align: center;
          margin-bottom: 24px;
          font-size: 1.6rem;
          color: #343a40;
        }

        .cert-form-group {
          margin-bottom: 20px;
        }

        .cert-form-group label {
          font-weight: 600;
          margin-bottom: 6px;
          display: block;
          color: #495057;
          font-size: 14px;
        }

        .cert-form-group input {
          width: 100%;
          padding: 11px 14px;
          border: 1.5px solid #ced4da;
          border-radius: 6px;
          font-size: 14px;
          box-sizing: border-box;
          transition: border-color 0.2s;
        }

        .cert-form-group input:focus {
          border-color: #bf0001;
          outline: none;
        }

        .cert-submit-btn {
          width: 100%;
          padding: 13px;
          background-color: #bf0001;
          color: white;
          border: none;
          border-radius: 6px;
          font-size: 16px;
          cursor: pointer;
          transition: background-color 0.3s;
          font-weight: 600;
        }

        .cert-submit-btn:hover:not(:disabled) { background-color: #a30001; }
        .cert-submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }

        .cert-back-link {
          display: block;
          text-align: center;
          margin-top: 16px;
          color: #bf0001;
          text-decoration: none;
          font-size: 14px;
          cursor: pointer;
        }

        .cert-back-link:hover { text-decoration: underline; }

        .cert-success {
          background: #d4edda;
          color: #155724;
          border: 1px solid #c3e6cb;
          border-radius: 6px;
          padding: 12px 16px;
          margin-bottom: 18px;
          font-size: 14px;
          text-align: center;
        }

        .cert-error {
          background: #f8d7da;
          color: #721c24;
          border: 1px solid #f5c6cb;
          border-radius: 6px;
          padding: 12px 16px;
          margin-bottom: 18px;
          font-size: 14px;
        }

        @media (max-width: 768px) {
          .cert-form-container {
            margin: 20px;
            padding: 20px;
          }
          .cert-form-container h2 { font-size: 1.3rem; }
        }
      `}</style>

      <div className="cert-form-container">
        <h2>Generate Manual Certificates</h2>

        {successMsg && <div className="cert-success">✅ {successMsg}</div>}
        {error && <div className="cert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="cert-form-group">
            <label htmlFor="donor_name">Donor Name</label>
            <input
              type="text"
              name="donor_name"
              id="donor_name"
              placeholder="Enter donor's name"
              value={form.donor_name}
              onChange={handleChange}
              required
              disabled={isLoading}
            />
          </div>

          <div className="cert-form-group">
            <label htmlFor="donor_email">Donor Email</label>
            <input
              type="email"
              name="donor_email"
              id="donor_email"
              placeholder="Enter donor's email"
              value={form.donor_email}
              onChange={handleChange}
              required
              disabled={isLoading}
            />
          </div>

          <div className="cert-form-group">
            <label htmlFor="donation_date">Donation Date</label>
            <input
              type="date"
              name="donation_date"
              id="donation_date"
              value={form.donation_date}
              onChange={handleChange}
              required
              disabled={isLoading}
            />
          </div>

          <div className="cert-form-group">
            <label htmlFor="blood_group">Blood Group</label>
            <input
              type="text"
              name="blood_group"
              id="blood_group"
              placeholder="Enter blood group (e.g. A+)"
              value={form.blood_group}
              onChange={handleChange}
              required
              disabled={isLoading}
            />
          </div>

          <div className="cert-form-group">
            <label htmlFor="location">Location (Optional)</label>
            <input
              type="text"
              name="location"
              id="location"
              placeholder="Enter location"
              value={form.location}
              onChange={handleChange}
              disabled={isLoading}
            />
          </div>

          <button type="submit" className="cert-submit-btn" disabled={isLoading}>
            {isLoading ? "Sending Certificate..." : "Send Certificate"}
          </button>
        </form>

        <span
          className="cert-back-link"
          onClick={() => navigate("/admin/dashboard")}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === "Enter" && navigate("/admin/dashboard")}
        >
          ← Back to Dashboard
        </span>
      </div>
    </AdminBase>
  );
}
