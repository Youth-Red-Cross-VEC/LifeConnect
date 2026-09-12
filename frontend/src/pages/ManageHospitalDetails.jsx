import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import AdminBase from "./AdminBase";

// Use the same base URL as the central api.js service
const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const sampleHospitals = [
  { id: "HOSP-01", hospital_name: "Apollo Hospital", city: "Chennai", state: "Tamil Nadu" },
  { id: "HOSP-02", hospital_name: "Fortis Malar", city: "Chennai", state: "Tamil Nadu" },
];

export default function ManageHospitalDetails() {
  const [hospitals, setHospitals] = useState(sampleHospitals);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchHospitals = async () => {
      setIsLoading(true);
      try {
        const token = localStorage.getItem("lc_token");
        const res = await fetch(`${BASE_URL}/api/v1/hospitals/`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        const data = await res.json();
        if (data && (Array.isArray(data.hospitals) || Array.isArray(data))) {
          setHospitals(Array.isArray(data) ? data : data.hospitals);
        }
      } catch {
        // Keep sample data on error
      } finally {
        setIsLoading(false);
      }
    };
    fetchHospitals();
  }, []);

  const handleModify = (hospitalId) => {
    navigate(`/admin/hospitals/manage?id=${hospitalId}`);
  };

  const handleDelete = async (hospitalId) => {
    if (deleteConfirm !== hospitalId) {
      setDeleteConfirm(hospitalId);
      return;
    }
    setIsLoading(true);
    setError("");
    try {
      const token = localStorage.getItem("lc_token");
      const res = await fetch(`${BASE_URL}/api/v1/hospitals/${hospitalId}`, {
        method: "DELETE",
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });
      const data = await res.json();
      if (res.ok && data && (data.success || data.message)) {
        setHospitals((prev) => prev.filter((h) => h.id !== hospitalId));
      } else {
        setError(data?.message || "Failed to delete hospital.");
      }
    } catch {
      setError("Server error. Try again.");
    } finally {
      setIsLoading(false);
      setDeleteConfirm(null);
    }
  };

  return (
    <AdminBase active="hospitals">
      <style>{`
        .mh-page {
          padding: 20px;
          font-family: Arial, sans-serif;
        }

        .mh-page h1 {
          color: #003f88;
          text-align: center;
          margin-bottom: 24px;
          font-size: 2rem;
        }

        .mh-error {
          background: #f8d7da;
          color: #721c24;
          border: 1px solid #f5c6cb;
          border-radius: 6px;
          padding: 10px 16px;
          margin-bottom: 16px;
          font-size: 14px;
        }

        .mh-add-btn {
          display: inline-block;
          margin-bottom: 20px;
          color: white;
          background-color: #003f88;
          text-decoration: none;
          padding: 10px 18px;
          border-radius: 6px;
          border: none;
          cursor: pointer;
          font-size: 14px;
          font-weight: 600;
          transition: background-color 0.3s;
        }
        .mh-add-btn:hover { background-color: #0056b3; }

        .mh-table-container {
          overflow-x: auto;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .mh-table {
          width: 100%;
          border-collapse: collapse;
          background: white;
          border: 1px solid #dee2e6;
        }

        .mh-table th {
          background-color: #003f88;
          color: white;
          text-transform: uppercase;
          padding: 12px 15px;
          text-align: left;
          font-size: 13px;
        }

        .mh-table td {
          padding: 12px 15px;
          border-bottom: 1px solid #dee2e6;
          color: #333;
          font-size: 14px;
        }

        .mh-table tbody tr:hover { background-color: #f0f7ff; }

        .modify-btn {
          background-color: #003f88;
          color: white;
          border: none;
          padding: 7px 14px;
          border-radius: 5px;
          cursor: pointer;
          font-size: 13px;
          margin-right: 8px;
          transition: background-color 0.2s;
        }
        .modify-btn:hover { background-color: #218838; }

        .delete-btn {
          background-color: #dc3545;
          color: white;
          border: none;
          padding: 7px 14px;
          border-radius: 5px;
          cursor: pointer;
          font-size: 13px;
          transition: background-color 0.2s;
        }
        .delete-btn:hover { background-color: #c82333; }
        .delete-btn:disabled { opacity: 0.6; cursor: not-allowed; }

        .confirm-badge {
          font-size: 11px;
          background: #fff3cd;
          color: #856404;
          border: 1px solid #ffeeba;
          border-radius: 4px;
          padding: 2px 8px;
          margin-left: 6px;
        }
      `}</style>

      <div className="mh-page">
        <h1>Manage Hospitals</h1>

        {error && <div className="mh-error">{error}</div>}

        <button
          className="mh-add-btn"
          onClick={() => navigate("/admin/hospitals/add")}
        >
          + Add New Hospital
        </button>

        {isLoading && hospitals.length === 0 ? (
          <div style={{ textAlign: "center", color: "#888", padding: "30px" }}>Loading hospitals...</div>
        ) : (
          <div className="mh-table-container">
            <table className="mh-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>City</th>
                  <th>State</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {hospitals.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: "center", color: "#888", padding: "24px" }}>
                      No hospitals found.
                    </td>
                  </tr>
                ) : (
                  hospitals.map((hospital) => (
                    <tr key={hospital.id}>
                      <td>{hospital.id}</td>
                      <td>{hospital.hospital_name}</td>
                      <td>{hospital.city}</td>
                      <td>{hospital.state}</td>
                      <td>
                        <button
                          className="modify-btn"
                          onClick={() => handleModify(hospital.id)}
                          disabled={isLoading}
                        >
                          Modify
                        </button>
                        <button
                          className="delete-btn"
                          onClick={() => handleDelete(hospital.id)}
                          disabled={isLoading}
                        >
                          {deleteConfirm === hospital.id ? "Confirm?" : "Delete"}
                          {deleteConfirm === hospital.id && (
                            <span className="confirm-badge">Click again</span>
                          )}
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AdminBase>
  );
}
