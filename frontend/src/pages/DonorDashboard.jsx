import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function DonorDashboard({ details = {} }) {
  const [form, setForm] = useState({
    id: details.id ?? "",
    name: details.name ?? "",
    email: details.email ?? "",
    blood_group: details.blood_group ?? "",
    last_donated_date: details.last_donated_date ?? "",
    active_status: details.active_status ?? "",
    number_of_times_donated: details.number_of_times_donated ?? "",
    last_login_date: details.last_login_date ?? "",
    first_name: details.first_name ?? "",
    last_name: details.last_name ?? "",
    age: details.age ?? "",
    contact_number: details.contact_number ?? "",
    date_of_birth: details.date_of_birth ?? "",
    marital_status: details.marital_status ?? "",
    secondary_contact_number: details.secondary_contact_number ?? "",
    aadhar_number: details.aadhar_number ?? "",
    address: details.address ?? "",
    city: details.city ?? "",
    state: details.state ?? "",
    country: details.country ?? "",
    pincode: details.pincode ?? "",
    disease_name: details.disease_name ?? "",
    disease_description: details.disease_description ?? "",
  });

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSaving(true);

    try {
      // TODO: wire up real API call, e.g. await api.updateDonor(form);
      await new Promise((res) => setTimeout(res, 400));
      setSuccess("Details updated successfully!");
    } catch {
      setError("Failed to save changes. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="donor-dashboard-wrapper">
      <style>{`
        .donor-dashboard-wrapper {
          margin: 0;
          padding: 0;
          font-family: 'Poppins', sans-serif;
          background-color: #f8f8f8;
          min-height: 100vh;
          width: 100vw;
          box-sizing: border-box;
          color: #333;
        }

        /* Header Styles */
        .donor-dashboard-wrapper .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          background-color: #8b0000;
          color: #fff;
          padding: 10px 20px;
          box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
          width: 100%;
          box-sizing: border-box;
          border-radius: 0px;
        }

        .donor-dashboard-wrapper .header h1 {
          margin: 0;
          font-family: "Georgia", serif;
          font-size: 2rem;
          font-weight: bold;
          color: whitesmoke;
        }

        .donor-dashboard-wrapper .header a {
          text-decoration: none;
          color: #f4f4f4;
        }

        .donor-dashboard-wrapper .header button {
          background-color: #fff;
          color: #8b0000;
          font-weight: bold;
          border: none;
          padding: 8px 16px;
          font-size: 1rem;
          border-radius: 4px;
          cursor: pointer;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
          width: 150px;
          margin: 0;
        }

        .donor-dashboard-wrapper .header button:hover {
          background-color: #f2f2f2;
        }

        .donor-dashboard-wrapper h1.page-title {
          text-align: center;
          color: #b30001;
          margin-top: 20px;
          font-size: 2.5rem;
          font-weight: bold;
        }

        /* Form Container */
        .donor-dashboard-wrapper form {
          max-width: 1000px;
          margin: 20px auto;
          padding: 20px;
          background-color: #ffffff;
          border-radius: 20px;
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        }

        /* Fieldsets */
        .donor-dashboard-wrapper fieldset {
          margin-bottom: 20px;
          border: 1px solid #b30001;
          padding: 15px;
          border-radius: 20px;
          text-align: left;
        }

        .donor-dashboard-wrapper legend {
          font-weight: bold;
          color: #b30001;
          padding: 0 10px;
          font-size: 1.1rem;
        }

        /* Labels and Inputs */
        .donor-dashboard-wrapper label {
          display: block;
          font-weight: 600;
          margin-bottom: 5px;
          margin-top: 10px;
        }

        .donor-dashboard-wrapper input[type="text"],
        .donor-dashboard-wrapper input[type="email"],
        .donor-dashboard-wrapper input[type="tel"],
        .donor-dashboard-wrapper input[type="number"],
        .donor-dashboard-wrapper input[type="date"],
        .donor-dashboard-wrapper select {
          width: 100%;
          box-sizing: border-box;
          padding: 8px;
          margin: 8px 0;
          font-size: 14px;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-family: 'Poppins', sans-serif;
        }

        .donor-dashboard-wrapper input[readonly] {
          background-color: #f0f0f0;
          cursor: not-allowed;
          color: #555;
        }

        /* Submit Button */
        .donor-dashboard-wrapper .submit-btn {
          width: 50%;
          padding: 10px 15px;
          margin: 20px auto;
          background-color: #b30001;
          color: whitesmoke;
          border: none;
          border-radius: 4px;
          font-size: 1rem;
          cursor: pointer;
          transition: background-color 0.3s ease;
          display: block;
          font-weight: bold;
        }

        .donor-dashboard-wrapper .submit-btn:hover:not(:disabled) {
          background-color: #9f2c2c;
        }

        .donor-dashboard-wrapper .submit-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .donor-dashboard-wrapper a.return-link {
          text-align: center;
          display: block;
          margin-top: 15px;
          margin-bottom: 30px;
          color: #b30001;
          text-decoration: none;
          font-weight: bold;
        }

        .donor-dashboard-wrapper a.return-link:hover {
          text-decoration: underline;
        }

        .donor-dashboard-wrapper .alert-error {
          background-color: #f8d7da;
          color: #721c24;
          padding: 12px;
          border-radius: 8px;
          margin-bottom: 20px;
          border: 1px solid #f5c6cb;
          font-weight: bold;
          text-align: center;
        }

        .donor-dashboard-wrapper .alert-success {
          background-color: #d4edda;
          color: #155724;
          padding: 12px;
          border-radius: 8px;
          margin-bottom: 20px;
          border: 1px solid #c3e6cb;
          font-weight: bold;
          text-align: center;
        }

        .donor-dashboard-wrapper .readonly-note {
          color: #555;
          font-size: 13px;
          font-style: italic;
          margin-top: -4px;
          margin-bottom: 6px;
          font-weight: normal;
        }

        @media (max-width: 768px) {
          .donor-dashboard-wrapper .header {
            flex-direction: column;
            height: auto;
            padding: 10px;
          }

          .donor-dashboard-wrapper .header button {
            text-align: center;
            margin-top: 10px;
            font-size: 12px;
            padding: 8px 16px;
            width: 100%;
          }

          .donor-dashboard-wrapper .header h1 {
            font-size: 24px;
          }

          .donor-dashboard-wrapper h1.page-title {
            font-size: 2rem;
          }

          .donor-dashboard-wrapper form {
            margin: 10px;
            padding: 15px;
          }

          .donor-dashboard-wrapper fieldset {
            padding: 10px;
            border-radius: 10px;
          }

          .donor-dashboard-wrapper label {
            font-size: 14px;
          }

          .donor-dashboard-wrapper .submit-btn {
            width: 100%;
          }
        }
      `}</style>

      {/* Header Section */}
      <div className="header">
        <a href="/">
          <h1>LifeConnect</h1>
        </a>
        <button onClick={() => navigate("/")}>Back to Home</button>
      </div>

      <h1 className="page-title">Donor Dashboard</h1>

      <form onSubmit={handleSubmit}>
        {error && <div className="alert-error">{error}</div>}
        {success && <div className="alert-success">{success}</div>}

        {/* Section 1: Donor Details */}
        <fieldset>
          <legend>Donor Details</legend>

          <label htmlFor="id">Donor ID:</label>
          <p className="readonly-note">Read-only — assigned by the system</p>
          <input type="text" id="id" name="id" value={form.id} readOnly />

          <label htmlFor="email">Email:</label>
          <p className="readonly-note">Read-only — contact support to change</p>
          <input type="email" id="email" name="email" value={form.email} readOnly />

          <label htmlFor="blood_group">Blood Group:</label>
          <input
            type="text"
            id="blood_group"
            name="blood_group"
            value={form.blood_group}
            onChange={handleChange}
            disabled={saving}
          />

          <label htmlFor="last_donated_date">Last Donated Date:</label>
          <input
            type="text"
            id="last_donated_date"
            name="last_donated_date"
            value={form.last_donated_date}
            readOnly
          />

          <label htmlFor="active_status">Active Status:</label>
          <input
            type="text"
            id="active_status"
            name="active_status"
            value={form.active_status}
            readOnly
          />

          <label htmlFor="number_of_times_donated">Times Donated:</label>
          <input
            type="text"
            id="number_of_times_donated"
            name="number_of_times_donated"
            value={form.number_of_times_donated}
            readOnly
          />

          <label htmlFor="last_login_date">Last Login Date:</label>
          <input
            type="text"
            id="last_login_date"
            name="last_login_date"
            value={form.last_login_date}
            readOnly
          />
        </fieldset>

        {/* Section 2: Personal Details */}
        <fieldset>
          <legend>Personal Details</legend>

          <label htmlFor="first_name">First Name:</label>
          <input
            type="text"
            id="first_name"
            name="first_name"
            value={form.first_name}
            onChange={handleChange}
            disabled={saving}
          />

          <label htmlFor="last_name">Last Name:</label>
          <input
            type="text"
            id="last_name"
            name="last_name"
            value={form.last_name}
            onChange={handleChange}
            disabled={saving}
          />

          <label htmlFor="age">Age:</label>
          <input
            type="number"
            id="age"
            name="age"
            value={form.age}
            onChange={handleChange}
            disabled={saving}
          />

          <label htmlFor="contact_number">Contact Number:</label>
          <input
            type="tel"
            id="contact_number"
            name="contact_number"
            value={form.contact_number}
            onChange={handleChange}
            disabled={saving}
          />

          <label htmlFor="date_of_birth">Date of Birth:</label>
          <input
            type="date"
            id="date_of_birth"
            name="date_of_birth"
            value={form.date_of_birth}
            onChange={handleChange}
            disabled={saving}
          />

          <label htmlFor="marital_status">Marital Status:</label>
          <select
            id="marital_status"
            name="marital_status"
            value={form.marital_status}
            onChange={handleChange}
            disabled={saving}
          >
            <option value="">-- Select --</option>
            <option value="single">Single</option>
            <option value="married">Married</option>
          </select>

          <label htmlFor="secondary_contact_number">Secondary Contact Number:</label>
          <input
            type="tel"
            id="secondary_contact_number"
            name="secondary_contact_number"
            value={form.secondary_contact_number}
            onChange={handleChange}
            disabled={saving}
          />

          <label htmlFor="aadhar_number">Aadhar Number:</label>
          <input
            type="text"
            id="aadhar_number"
            name="aadhar_number"
            value={form.aadhar_number}
            onChange={handleChange}
            disabled={saving}
          />
        </fieldset>

        {/* Section 3: Address Details */}
        <fieldset>
          <legend>Address Details</legend>

          <label htmlFor="address">Address:</label>
          <input
            type="text"
            id="address"
            name="address"
            value={form.address}
            onChange={handleChange}
            disabled={saving}
          />

          <label htmlFor="city">City:</label>
          <input
            type="text"
            id="city"
            name="city"
            value={form.city}
            onChange={handleChange}
            disabled={saving}
          />

          <label htmlFor="state">State:</label>
          <input
            type="text"
            id="state"
            name="state"
            value={form.state}
            onChange={handleChange}
            disabled={saving}
          />

          <label htmlFor="country">Country:</label>
          <input
            type="text"
            id="country"
            name="country"
            value={form.country}
            onChange={handleChange}
            disabled={saving}
          />

          <label htmlFor="pincode">Pincode:</label>
          <input
            type="number"
            id="pincode"
            name="pincode"
            value={form.pincode}
            onChange={handleChange}
            disabled={saving}
          />
        </fieldset>

        {/* Section 4: Disease Details */}
        <fieldset>
          <legend>Disease Details</legend>

          <label htmlFor="disease_name">Disease Name:</label>
          <input
            type="text"
            id="disease_name"
            name="disease_name"
            value={form.disease_name}
            onChange={handleChange}
            disabled={saving}
          />

          <label htmlFor="disease_description">Disease Description:</label>
          <input
            type="text"
            id="disease_description"
            name="disease_description"
            value={form.disease_description}
            onChange={handleChange}
            disabled={saving}
          />
        </fieldset>

        <button type="submit" className="submit-btn" disabled={saving}>
          {saving ? "Saving..." : "Update Details"}
        </button>
      </form>

      <a href="/" className="return-link">
        Return to Home Page
      </a>
    </div>
  );
}
