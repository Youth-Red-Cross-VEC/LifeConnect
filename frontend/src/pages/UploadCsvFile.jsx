import { useState, useRef } from "react";
import AdminBase from "./AdminBase";

export default function UploadCsvFile() {
  const [donorFile, setDonorFile] = useState(null);
  const [hospitalFile, setHospitalFile] = useState(null);
  const [alert, setAlert] = useState({ type: "", message: "" });
  const [donorLoading, setDonorLoading] = useState(false);
  const [hospitalLoading, setHospitalLoading] = useState(false);
  const donorRef = useRef(null);
  const hospitalRef = useRef(null);

  const dismissAlert = () => setAlert({ type: "", message: "" });

  const uploadCsv = async (file, endpoint, setLoading) => {
    if (!file) return;
    setLoading(true);
    setAlert({ type: "", message: "" });
    try {
      const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const token = localStorage.getItem("lc_token");
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${BASE_URL}${endpoint}`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      const res = await response.json();
      if (res && (res.success || res.message)) {
        setAlert({
          type: "success",
          message: res.message || "Details Added Successfully",
        });
      } else {
        setAlert({
          type: "danger",
          message: res?.message || "Upload failed. Please check the file format.",
        });
      }
    } catch {
      setAlert({ type: "danger", message: "Server error. Try again." });
    } finally {
      setLoading(false);
    }
  };

  const handleDonorSubmit = async (e) => {
    e.preventDefault();
    // TODO: No FastAPI endpoint currently exists for POST /upload_donor_csv.
    // await uploadCsv(donorFile, "/upload_donor_csv", setDonorLoading);
    setAlert({
      type: "danger",
      message: "CSV upload for donors is not yet implemented on the FastAPI backend.",
    });
    setDonorFile(null);
    if (donorRef.current) donorRef.current.value = "";
  };

  const handleHospitalSubmit = async (e) => {
    e.preventDefault();
    // TODO: No FastAPI endpoint currently exists for POST /upload_hospital_csv.
    // await uploadCsv(hospitalFile, "/upload_hospital_csv", setHospitalLoading);
    setAlert({
      type: "danger",
      message: "CSV upload for hospitals is not yet implemented on the FastAPI backend.",
    });
    setHospitalFile(null);
    if (hospitalRef.current) hospitalRef.current.value = "";
  };

  return (
    <AdminBase active="upload-csv">
      <style>{`
        .csv-page {
          padding: 20px;
          font-family: "Inter", sans-serif;
        }

        .csv-page h2 {
          text-align: center;
          color: #333;
          font-size: 1.6rem;
          margin-bottom: 24px;
        }

        .csv-alert {
          position: relative;
          padding: 14px 48px 14px 18px;
          margin-bottom: 20px;
          border: 1px solid transparent;
          border-radius: 6px;
          font-size: 15px;
          font-weight: 500;
          max-width: 800px;
          margin-left: auto;
          margin-right: auto;
          animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-8px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .csv-alert-success {
          background-color: #d4edda;
          color: #155724;
          border-color: #c3e6cb;
        }

        .csv-alert-danger {
          background-color: #f8d7da;
          color: #721c24;
          border-color: #f5c6cb;
        }

        .csv-close-btn {
          position: absolute;
          top: 12px;
          right: 14px;
          background: none;
          border: none;
          font-size: 20px;
          color: inherit;
          cursor: pointer;
          line-height: 1;
        }

        .csv-forms-row {
          display: flex;
          flex-wrap: wrap;
          gap: 24px;
          justify-content: center;
        }

        .csv-form-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: flex-start;
          padding: 28px 24px;
          border-radius: 12px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          max-width: 380px;
          width: 100%;
          background: white;
        }

        .csv-form-container h3 {
          font-size: 1.2rem;
          font-weight: 700;
          color: #333;
          margin-bottom: 18px;
          text-align: center;
        }

        .csv-form-container label {
          font-size: 15px;
          font-weight: 600;
          margin-bottom: 8px;
          color: #333;
          display: block;
          width: 100%;
        }

        .csv-file-input {
          width: 100%;
          padding: 8px;
          border: 1px solid #f3f3f3;
          border-radius: 6px;
          cursor: pointer;
          margin-bottom: 16px;
          box-sizing: border-box;
        }

        input[type="file"]::file-selector-button {
          margin-right: 16px;
          border: none;
          background: #dc3545;
          padding: 8px 18px;
          border-radius: 8px;
          color: #fff;
          cursor: pointer;
          transition: background 0.2s;
        }

        input[type="file"]::file-selector-button:hover {
          background: #c82333;
        }

        .csv-submit-btn {
          background-color: #198754;
          color: #fff;
          padding: 11px 20px;
          border: none;
          border-radius: 6px;
          font-size: 15px;
          font-weight: bold;
          cursor: pointer;
          width: 100%;
          transition: background-color 0.3s, transform 0.15s;
        }

        .csv-submit-btn:hover:not(:disabled) {
          background-color: #218838;
          transform: scale(1.02);
        }

        .csv-submit-btn:active:not(:disabled) { transform: scale(0.98); }
        .csv-submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }

        .csv-format-hint {
          font-size: 12px;
          color: #888;
          margin-top: 10px;
          text-align: center;
        }
      `}</style>

      <div className="csv-page">
        <h2>Add Donor and Hospital Details</h2>

        {alert.message && (
          <div className={`csv-alert csv-alert-${alert.type}`}>
            {alert.message}
            <button className="csv-close-btn" onClick={dismissAlert}>&times;</button>
          </div>
        )}

        <div className="csv-forms-row">
          {/* Donor CSV Upload */}
          <div className="csv-form-container">
            <h3>Upload Donor CSV</h3>
            <form onSubmit={handleDonorSubmit} style={{ width: "100%" }}>
              <label htmlFor="donor-file">Select Donor CSV File</label>
              <input
                ref={donorRef}
                id="donor-file"
                type="file"
                accept=".csv"
                className="csv-file-input"
                onChange={(e) => setDonorFile(e.target.files[0] || null)}
                required
              />
              <button type="submit" className="csv-submit-btn" disabled={donorLoading || !donorFile}>
                {donorLoading ? "Uploading..." : "Upload Donors"}
              </button>
              <p className="csv-format-hint">Accepts .csv format only</p>
            </form>
          </div>

          {/* Hospital CSV Upload */}
          <div className="csv-form-container">
            <h3>Upload Hospital CSV</h3>
            <form onSubmit={handleHospitalSubmit} style={{ width: "100%" }}>
              <label htmlFor="hospital-file">Select Hospital CSV File</label>
              <input
                ref={hospitalRef}
                id="hospital-file"
                type="file"
                accept=".csv"
                className="csv-file-input"
                onChange={(e) => setHospitalFile(e.target.files[0] || null)}
                required
              />
              <button type="submit" className="csv-submit-btn" disabled={hospitalLoading || !hospitalFile}>
                {hospitalLoading ? "Uploading..." : "Upload Hospitals"}
              </button>
              <p className="csv-format-hint">Accepts .csv format only</p>
            </form>
          </div>
        </div>
      </div>
    </AdminBase>
  );
}
