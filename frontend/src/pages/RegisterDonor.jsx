import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";

export default function RegisterDonor() {
  const [form, setForm] = useState({
    Email: "",
    password: "",
    confirm_password: "",
    first_name: "",
    last_name: "",
    age: "",
    dob: "",
    contact_number: "",
    secondary_contact: "",
    marital_status: "",
    aadhar_number: "",
    blood_group: "",
    previous_blood_donation_status: "",
    last_donation: "",
    blood_donated_count: "",
    address: "",
    city: "",
    state: "TamilNadu",
    pincode: "",
    country: "India",
    disease_name: "",
    description: "",
    agree_terms: false,
  });

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (form.password !== form.confirm_password) {
      setError("Passwords do not match");
      return;
    }
    if (!form.agree_terms) {
      setError("You must agree to the terms and conditions");
      return;
    }

    setIsLoading(false);
    setIsLoading(true);

    try {
      const payload = {
        name: `${form.first_name} ${form.last_name || ""}`.trim(),
        email: form.Email,
        password: form.password,
        blood_group: form.blood_group,
        personal_details: {
          first_name: form.first_name,
          last_name: form.last_name || null,
          age: parseInt(form.age, 10),
          date_of_birth: form.dob,
          contact_number: form.contact_number,
          secondary_contact_number: form.secondary_contact || null,
          marital_status: form.marital_status || null,
          aadhar_number: form.aadhar_number || null,
        },
        address_details: {
          address: form.address,
          pincode: form.pincode,
          country: form.country || "India",
          state: form.state || "TamilNadu",
          city: form.city,
        },
        disease_details: {
          name: form.disease_name || "None",
          description: form.description || null,
        },
      };

      const res = await api.donorRegister(payload);
      if (res && (res.id || res.email || res.success || !res.error)) {
        setSuccess("Registration successful! Redirecting to confirmation...");
        setTimeout(() => {
          navigate("/donor/registration-confirmation");
        }, 1500);
      } else {
        setError(res?.detail?.[0]?.msg || res?.message || "Registration failed. Please try again.");
      }
    } catch {
      setError("Server error. Try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="register-donor-wrapper">
      <style>{`
        .register-donor-wrapper {
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
        .register-donor-wrapper .header {
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

        .register-donor-wrapper .header h1 {
          margin: 0;
          font-family: "Georgia", serif;
          font-size: 2rem;
          font-weight: bold;
          color: whitesmoke;
        }

        .register-donor-wrapper .header a {
          text-decoration: none;
          color: #f4f4f4;
        }

        .register-donor-wrapper .header button {
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

        .register-donor-wrapper .header button:hover {
          background-color: #f2f2f2;
        }

        .register-donor-wrapper h1.page-title {
          text-align: center;
          color: #b30001;
          margin-top: 20px;
          font-size: 2.5rem;
          font-weight: bold;
        }

        /* Form Container */
        .register-donor-wrapper form {
          max-width: 1000px;
          margin: 20px auto;
          padding: 20px;
          background-color: #ffffff;
          border-radius: 20px;
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        }

        /* Fieldsets */
        .register-donor-wrapper fieldset {
          margin-bottom: 20px;
          border: 1px solid #b30001;
          padding: 15px;
          border-radius: 20px;
          text-align: left;
        }

        .register-donor-wrapper legend {
          font-weight: bold;
          color: #b30001;
          padding: 0 10px;
          font-size: 1.1rem;
        }

        /* Labels and Inputs */
        .register-donor-wrapper label {
          display: block;
          font-weight: 600;
          margin-bottom: 5px;
          margin-top: 10px;
        }

        .register-donor-wrapper input[type="text"],
        .register-donor-wrapper input[type="email"],
        .register-donor-wrapper input[type="password"],
        .register-donor-wrapper input[type="tel"],
        .register-donor-wrapper input[type="number"],
        .register-donor-wrapper input[type="date"],
        .register-donor-wrapper textarea,
        .register-donor-wrapper select {
          width: 100%;
          box-sizing: border-box;
          padding: 8px;
          margin: 8px 0;
          font-size: 14px;
          border: 1px solid #ccc;
          border-radius: 4px;
        }

        .register-donor-wrapper input[type="radio"] {
          margin-right: 8px;
          display: inline;
        }

        .register-donor-wrapper textarea {
          height: 100px;
          resize: vertical;
        }

        /* Buttons */
        .register-donor-wrapper .submit-btn {
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

        .register-donor-wrapper .submit-btn:hover:not(:disabled) {
          background-color: #9f2c2c;
        }

        .register-donor-wrapper .submit-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        /* Checkbox and Password Toggle */
        .register-donor-wrapper input[type="checkbox"] {
          margin-right: 5px;
          display: inline-block;
          width: auto;
        }

        .register-donor-wrapper .show-pwd-label {
          display: inline-block;
          font-weight: normal;
          margin: 0;
          cursor: pointer;
        }

        .register-donor-wrapper a.return-link {
          text-align: center;
          display: block;
          margin-top: 15px;
          margin-bottom: 30px;
          color: #b30001;
          text-decoration: none;
          font-weight: bold;
        }

        .register-donor-wrapper a.return-link:hover {
          text-decoration: underline;
        }

        .register-donor-wrapper .radio-group {
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
          margin-top: 10px;
          margin-bottom: 15px;
        }

        .register-donor-wrapper .radio-group input[type="radio"] {
          display: none;
        }

        .register-donor-wrapper .radio-group label {
          display: inline-block;
          padding: 8px 12px;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-size: 14px;
          cursor: pointer;
          text-align: center;
          min-width: 50px;
          background-color: #f9f9f9;
          transition: background-color 0.3s, border-color 0.3s;
          margin: 0;
        }

        .register-donor-wrapper .radio-group input[type="radio"]:checked + label {
          background-color: #ce7676;
          border-color: #9f2c2c;
          color: white;
        }

        .register-donor-wrapper .yesno-group {
          display: flex;
          gap: 20px;
          margin-bottom: 15px;
          margin-top: 5px;
        }

        .register-donor-wrapper .yesno-group label {
          font-size: 1rem;
          font-weight: 500;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 5px;
          margin: 0;
        }

        .register-donor-wrapper .alert-error {
          background-color: #f8d7da;
          color: #721c24;
          padding: 12px;
          border-radius: 8px;
          margin-bottom: 20px;
          border: 1px solid #f5c6cb;
          font-weight: bold;
          text-align: center;
        }

        .register-donor-wrapper .alert-success {
          background-color: #d4edda;
          color: #155724;
          padding: 12px;
          border-radius: 8px;
          margin-bottom: 20px;
          border: 1px solid #c3e6cb;
          font-weight: bold;
          text-align: center;
        }

        @media (max-width: 768px) {
          .register-donor-wrapper .header {
            flex-direction: column;
            height: auto;
            padding: 10px;
          }

          .register-donor-wrapper .header button {
            text-align: center;
            margin-top: 10px;
            font-size: 12px;
            padding: 8px 16px;
            width: 100%;
          }

          .register-donor-wrapper .header h1 {
            font-size: 24px;
          }

          .register-donor-wrapper h1.page-title {
            font-size: 2rem;
          }

          .register-donor-wrapper form {
            margin: 10px;
            padding: 15px;
          }

          .register-donor-wrapper fieldset {
            padding: 10px;
            border-radius: 10px;
          }

          .register-donor-wrapper label {
            font-size: 14px;
          }

          .register-donor-wrapper .submit-btn {
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

      <h1 className="page-title">Become a Donor</h1>

      <form onSubmit={handleSubmit}>
        {error && <div className="alert-error">{error}</div>}
        {success && <div className="alert-success">{success}</div>}

        {/* Section 1: Login Credentials */}
        <fieldset>
          <legend>Sign-In Credentials</legend>
          <label htmlFor="Email">Email address</label>
          <input
            type="email"
            id="Email"
            name="Email"
            value={form.Email}
            onChange={handleChange}
            required
            disabled={isLoading}
          />

          <label htmlFor="password">Password</label>
          <input
            type={showPassword ? "text" : "password"}
            id="password"
            name="password"
            value={form.password}
            onChange={handleChange}
            required
            disabled={isLoading}
          />

          <label htmlFor="confirm_password">Confirm Password</label>
          <input
            type={showPassword ? "text" : "password"}
            id="confirm_password"
            name="confirm_password"
            value={form.confirm_password}
            onChange={handleChange}
            required
            disabled={isLoading}
          />

          <div style={{ marginTop: "10px" }}>
            <input
              type="checkbox"
              id="show_passwords"
              checked={showPassword}
              onChange={() => setShowPassword(!showPassword)}
              disabled={isLoading}
            />
            <label htmlFor="show_passwords" className="show-pwd-label">
              Show Passwords
            </label>
          </div>
        </fieldset>

        {/* Section 2: Personal Details */}
        <fieldset>
          <legend>Personal Details</legend>
          <label htmlFor="first_name">First Name (required):</label>
          <input
            type="text"
            id="first_name"
            name="first_name"
            value={form.first_name}
            onChange={handleChange}
            required
            disabled={isLoading}
          />

          <label htmlFor="last_name">Last Name or Initial:</label>
          <input
            type="text"
            id="last_name"
            name="last_name"
            value={form.last_name}
            onChange={handleChange}
            disabled={isLoading}
          />

          <label htmlFor="age">Age (required):</label>
          <input
            type="number"
            id="age"
            name="age"
            value={form.age}
            onChange={handleChange}
            required
            min="1"
            disabled={isLoading}
          />

          <label htmlFor="dob">Date of Birth (required):</label>
          <input
            type="date"
            id="dob"
            name="dob"
            value={form.dob}
            onChange={handleChange}
            required
            disabled={isLoading}
          />

          <label htmlFor="contact_number">Contact Number (required):</label>
          <input
            type="tel"
            id="contact_number"
            name="contact_number"
            value={form.contact_number}
            onChange={handleChange}
            required
            pattern="[0-9]{10}"
            title="Enter a 10-digit phone number"
            disabled={isLoading}
          />

          <label htmlFor="secondary_contact">Secondary Contact Number (Optional):</label>
          <input
            type="tel"
            id="secondary_contact"
            name="secondary_contact"
            value={form.secondary_contact}
            onChange={handleChange}
            pattern="[0-9]{10}"
            title="Enter a 10-digit phone number"
            disabled={isLoading}
          />

          <label htmlFor="marital_status">Marital Status (Optional):</label>
          <select
            id="marital_status"
            name="marital_status"
            value={form.marital_status}
            onChange={handleChange}
            disabled={isLoading}
          >
            <option value="">-- Select --</option>
            <option value="single">Single</option>
            <option value="married">Married</option>
          </select>

          <label htmlFor="aadhar_number">Aadhar Number (Optional):</label>
          <input
            type="text"
            id="aadhar_number"
            name="aadhar_number"
            value={form.aadhar_number}
            onChange={handleChange}
            pattern="[0-9]{12}"
            title="Enter a 12-digit Aadhar number"
            disabled={isLoading}
          />

          <label>Blood Group (required):</label>
          <div className="radio-group">
            {["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].map((bg) => (
              <span key={bg}>
                <input
                  type="radio"
                  id={`blood_group_${bg}`}
                  name="blood_group"
                  value={bg}
                  checked={form.blood_group === bg}
                  onChange={handleChange}
                  required
                  disabled={isLoading}
                />
                <label htmlFor={`blood_group_${bg}`}>{bg}</label>
              </span>
            ))}
          </div>

          <label>Have you Donated Blood Before:</label>
          <div className="yesno-group">
            <label>
              <input
                type="radio"
                name="previous_blood_donation_status"
                value="1"
                checked={form.previous_blood_donation_status === "1"}
                onChange={handleChange}
                disabled={isLoading}
              />
              Yes
            </label>
            <label>
              <input
                type="radio"
                name="previous_blood_donation_status"
                value="0"
                checked={form.previous_blood_donation_status === "0"}
                onChange={handleChange}
                disabled={isLoading}
              />
              No
            </label>
          </div>

          <label htmlFor="last_donation">Last Blood Donated Date:</label>
          <input
            type="date"
            id="last_donation"
            name="last_donation"
            value={form.last_donation}
            onChange={handleChange}
            disabled={isLoading}
          />

          <label htmlFor="blood_donated_count">No of Times Blood Donated:</label>
          <input
            type="number"
            id="blood_donated_count"
            name="blood_donated_count"
            value={form.blood_donated_count}
            onChange={handleChange}
            disabled={isLoading}
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
            required
            disabled={isLoading}
          />

          <label htmlFor="city">City:</label>
          <input
            type="text"
            id="city"
            name="city"
            value={form.city}
            onChange={handleChange}
            required
            disabled={isLoading}
          />

          <label htmlFor="state">State:</label>
          <select
            id="state"
            name="state"
            value={form.state}
            onChange={handleChange}
            required
            disabled={isLoading}
          >
            <option value="TamilNadu">Tamil Nadu</option>
            <option value="Other">Other</option>
          </select>

          <label htmlFor="pincode">Pincode:</label>
          <input
            type="number"
            id="pincode"
            name="pincode"
            value={form.pincode}
            onChange={handleChange}
            required
            pattern="[0-9]{6}"
            title="Enter a valid 6-digit pincode"
            disabled={isLoading}
          />

          <label htmlFor="country">Country:</label>
          <select
            id="country"
            name="country"
            value={form.country}
            onChange={handleChange}
            required
            disabled={isLoading}
          >
            <option value="India">India</option>
            <option value="Other">Other</option>
          </select>
        </fieldset>

        {/* Section 4: Disease Details */}
        <fieldset>
          <legend>Disease Details</legend>
          <p style={{ color: "#555", fontSize: "14px", marginBottom: "10px" }}>
            If you have any existing medical conditions or health concerns, please specify them below:
          </p>
          <label htmlFor="disease_name">Disease Name (Optional):</label>
          <input
            type="text"
            id="disease_name"
            name="disease_name"
            value={form.disease_name}
            onChange={handleChange}
            disabled={isLoading}
          />

          <label htmlFor="description">Description (Optional):</label>
          <textarea
            id="description"
            name="description"
            value={form.description}
            onChange={handleChange}
            disabled={isLoading}
          />
        </fieldset>

        {/* Section 5: Terms and Conditions */}
        <fieldset>
          <legend>Terms and Conditions</legend>
          <label htmlFor="terms">Please read the terms and conditions below:</label>
          <textarea
            id="terms"
            name="terms"
            readOnly
            style={{ width: "100%", height: "200px" }}
            value={`Terms and Conditions for Blood Donor Registration

1. Personal Information and Privacy
1.1 Data Collection: During the registration process, we collect personal details such as your name, contact information, date of birth, gender, blood group, and health information...
1.2 Data Usage: The personal information you provide will only be used for the purposes of donor management...
1.3 Data Security: All data is stored securely using industry-standard encryption...`}
          />
          <div style={{ marginTop: "10px" }}>
            <input
              type="checkbox"
              id="agree_terms"
              name="agree_terms"
              checked={form.agree_terms}
              onChange={handleChange}
              required
              disabled={isLoading}
            />
            <label htmlFor="agree_terms" className="show-pwd-label">
              I agree to the terms and conditions
            </label>
          </div>
        </fieldset>

        <button type="submit" className="submit-btn" disabled={isLoading}>
          {isLoading ? "Submitting..." : "Submit"}
        </button>
      </form>

      <a href="/" className="return-link">
        Return to Home Page
      </a>
    </div>
  );
}
