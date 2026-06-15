import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";

export default function GenerateRequests() {
  const [form, setForm] = useState({
    patient_name: "",
    attendant_name: "",
    blood_group: "",
    hospital_name: "",
    hospital_id: "",
    hospital_address: "",
    contact_number: "",
    patient_age: "",
    pincode: "",
    landmark: "",
    due_date: "",
    request_reason: "",
    units_required: "",
  });

  const [hospitals, setHospitals] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const suggestionsRef = useRef(null);

  // Fetch hospital list on mount
  useEffect(() => {
    api.getBloodBanks().then((res) => {
      if (Array.isArray(res)) setHospitals(res);
      else if (res && Array.isArray(res.hospitals)) setHospitals(res.hospitals);
    }).catch(() => { });
  }, []);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClick = (e) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(e.target)) {
        setSuggestions([]);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));

    if (name === "hospital_name") {
      const q = value.toLowerCase();
      if (q.length > 0) {
        setSuggestions(hospitals.filter((h) => h.name.toLowerCase().includes(q)));
      } else {
        setSuggestions([]);
      }
    }
  };

  const selectHospital = (hospital) => {
    setForm((prev) => ({
      ...prev,
      hospital_name: hospital.name,
      hospital_id: hospital.id ?? "",
      hospital_address: hospital.address ?? prev.hospital_address,
    }));
    setSuggestions([]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      const res = await api.generateBloodRequest(form);
      if (res && res.success === true) {
        navigate("/blood-request/confirmation");
      } else {
        setError(res?.message || "Failed to submit request. Please try again.");
      }
    } catch {
      setError("Server error. Try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="generate-req-wrapper">
      <style>{`
        .generate-req-wrapper {
          margin: 0;
          padding: 0;
          font-family: 'Poppins', sans-serif;
          background-color: #f8f8f8;
          min-height: 100vh;
          width: 100vw;
          box-sizing: border-box;
          color: #333;
        }

        .generate-req-wrapper .header {
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

        .generate-req-wrapper .header h1 {
          margin: 0;
          font-family: "Georgia", serif;
          font-size: 2rem;
          font-weight: bold;
          color: whitesmoke;
        }

        .generate-req-wrapper .header a {
          text-decoration: none;
          color: #f4f4f4;
        }

        .generate-req-wrapper .header button {
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
        }

        .generate-req-wrapper .header button:hover {
          background-color: #f2f2f2;
        }

        .generate-req-wrapper h1.page-title {
          text-align: center;
          color: #b30001;
          margin-top: 20px;
          font-size: 2.5rem;
          font-weight: bold;
        }

        .generate-req-wrapper form {
          max-width: 1000px;
          margin: 20px auto;
          padding: 20px;
          background-color: #ffffff;
          border-radius: 20px;
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        }

        .generate-req-wrapper fieldset {
          margin-bottom: 20px;
          border: 1px solid #b30001;
          padding: 15px;
          border-radius: 20px;
          text-align: left;
        }

        .generate-req-wrapper legend {
          font-weight: bold;
          color: #b30001;
          padding: 0 10px;
          font-size: 1.1rem;
        }

        .generate-req-wrapper label {
          display: block;
          font-weight: 600;
          margin-bottom: 5px;
          margin-top: 10px;
        }

        .generate-req-wrapper input[type="text"],
        .generate-req-wrapper input[type="tel"],
        .generate-req-wrapper input[type="number"],
        .generate-req-wrapper input[type="date"],
        .generate-req-wrapper select,
        .generate-req-wrapper textarea {
          width: 100%;
          box-sizing: border-box;
          padding: 8px;
          margin: 8px 0;
          font-size: 14px;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-family: 'Poppins', sans-serif;
        }

        .generate-req-wrapper textarea {
          height: 100px;
          resize: vertical;
        }

        /* Autocomplete */
        .generate-req-wrapper .autocomplete-wrapper {
          position: relative;
        }

        .generate-req-wrapper .autocomplete-suggestions {
          position: absolute;
          top: 100%;
          left: 0;
          width: 100%;
          max-height: 200px;
          overflow-y: auto;
          background-color: #fff;
          border: 1px solid #ccc;
          z-index: 999;
          border-radius: 8px;
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        .generate-req-wrapper .autocomplete-suggestions div {
          padding: 10px 12px;
          cursor: pointer;
          font-size: 14px;
          transition: background-color 0.2s;
        }

        .generate-req-wrapper .autocomplete-suggestions div:hover {
          background-color: #fff5f5;
        }

        .generate-req-wrapper .submit-btn {
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

        .generate-req-wrapper .submit-btn:hover:not(:disabled) {
          background-color: #9f2c2c;
        }

        .generate-req-wrapper .submit-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .generate-req-wrapper .alert-error {
          background-color: #f8d7da;
          color: #721c24;
          padding: 12px;
          border-radius: 8px;
          margin-bottom: 20px;
          border: 1px solid #f5c6cb;
          font-weight: bold;
          text-align: center;
        }

        .generate-req-wrapper a.return-link {
          text-align: center;
          display: block;
          margin-top: 15px;
          margin-bottom: 30px;
          color: #b30001;
          text-decoration: none;
          font-weight: bold;
        }

        .generate-req-wrapper a.return-link:hover {
          text-decoration: underline;
        }

        @media (max-width: 768px) {
          .generate-req-wrapper .header {
            flex-direction: column;
            height: auto;
            padding: 10px;
          }

          .generate-req-wrapper .header button {
            margin-top: 10px;
            width: 100%;
          }

          .generate-req-wrapper h1.page-title {
            font-size: 2rem;
          }

          .generate-req-wrapper form {
            margin: 10px;
            padding: 15px;
          }

          .generate-req-wrapper fieldset {
            padding: 10px;
            border-radius: 10px;
          }

          .generate-req-wrapper label {
            font-size: 14px;
          }

          .generate-req-wrapper .submit-btn {
            width: 100%;
          }
        }
      `}</style>

      {/* Header */}
      <div className="header">
        <a href="/"><h1>LifeConnect</h1></a>
        <button onClick={() => navigate("/")}>Back to Home</button>
      </div>

      <h1 className="page-title">Generate Blood Request</h1>

      <form onSubmit={handleSubmit}>
        {error && <div className="alert-error">{error}</div>}

        {/* Patient Details */}
        <fieldset>
          <legend>Patient Details</legend>

          <label htmlFor="patient_name">Patient Name</label>
          <input
            type="text"
            id="patient_name"
            name="patient_name"
            value={form.patient_name}
            onChange={handleChange}
            required
            disabled={isLoading}
          />

          <label htmlFor="attendant_name">Attendant Name</label>
          <input
            type="text"
            id="attendant_name"
            name="attendant_name"
            value={form.attendant_name}
            onChange={handleChange}
            required
            disabled={isLoading}
          />

          <label htmlFor="patient_age">Patient Age</label>
          <input
            type="number"
            id="patient_age"
            name="patient_age"
            value={form.patient_age}
            onChange={handleChange}
            required
            min="1"
            disabled={isLoading}
          />

          <label htmlFor="contact_number">Contact Number</label>
          <input
            type="tel"
            id="contact_number"
            name="contact_number"
            value={form.contact_number}
            onChange={handleChange}
            required
            disabled={isLoading}
          />
        </fieldset>

        {/* Blood Requirement */}
        <fieldset>
          <legend>Blood Requirement</legend>

          <label htmlFor="blood_group">Blood Group</label>
          <select
            id="blood_group"
            name="blood_group"
            value={form.blood_group}
            onChange={handleChange}
            required
            disabled={isLoading}
          >
            <option value="">Select Blood Group</option>
            <option value="A+">A+</option>
            <option value="A-">A-</option>
            <option value="B+">B+</option>
            <option value="B-">B-</option>
            <option value="AB+">AB+</option>
            <option value="AB-">AB-</option>
            <option value="O+">O+</option>
            <option value="O-">O-</option>
          </select>

          <label htmlFor="units_required">Units Required</label>
          <input
            type="number"
            id="units_required"
            name="units_required"
            value={form.units_required}
            onChange={handleChange}
            min="1"
            disabled={isLoading}
          />

          <label htmlFor="due_date">Due Date</label>
          <input
            type="date"
            id="due_date"
            name="due_date"
            value={form.due_date}
            onChange={handleChange}
            required
            disabled={isLoading}
          />

          <label htmlFor="request_reason">Request Reason</label>
          <textarea
            id="request_reason"
            name="request_reason"
            value={form.request_reason}
            onChange={handleChange}
            required
            disabled={isLoading}
          />
        </fieldset>

        {/* Hospital Details */}
        <fieldset>
          <legend>Hospital Details</legend>

          <label htmlFor="hospital_name">Hospital Name</label>
          <div className="autocomplete-wrapper" ref={suggestionsRef}>
            <input
              type="text"
              id="hospital_name"
              name="hospital_name"
              value={form.hospital_name}
              onChange={handleChange}
              autoComplete="off"
              required
              disabled={isLoading}
            />
            <input type="hidden" id="hospital_id" name="hospital_id" value={form.hospital_id} />
            {suggestions.length > 0 && (
              <div className="autocomplete-suggestions">
                {suggestions.map((h) => (
                  <div key={h.id ?? h.name} onMouseDown={() => selectHospital(h)}>
                    {h.name}
                  </div>
                ))}
              </div>
            )}
          </div>

          <label htmlFor="hospital_address">Hospital Address</label>
          <input
            type="text"
            id="hospital_address"
            name="hospital_address"
            value={form.hospital_address}
            onChange={handleChange}
            required
            disabled={isLoading}
          />

          <label htmlFor="pincode">Pincode</label>
          <input
            type="text"
            id="pincode"
            name="pincode"
            value={form.pincode}
            onChange={handleChange}
            required
            disabled={isLoading}
          />

          <label htmlFor="landmark">Landmark (Optional)</label>
          <input
            type="text"
            id="landmark"
            name="landmark"
            value={form.landmark}
            onChange={handleChange}
            disabled={isLoading}
          />
        </fieldset>

        <button type="submit" className="submit-btn" disabled={isLoading}>
          {isLoading ? "Submitting..." : "Submit Request"}
        </button>
      </form>

      <a href="/" className="return-link">Return to Home Page</a>
    </div>
  );
}
