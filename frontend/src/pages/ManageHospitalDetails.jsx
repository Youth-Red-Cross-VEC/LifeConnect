import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AdminBase from "./AdminBase";
import AsyncState from "../components/AsyncState";
import { useApiData } from "../hooks/useApiData";
import { api } from "../services/api";
import { unwrapList } from "../services/unwrap";

// The list endpoint is paginated ({ items, total, ... }); 100 is its maximum page size.
const loadHospitals = async () => {
  const res = await api.getHospitals({ page_size: 100 });
  return unwrapList(res?.items, res?.detail || "Failed to load hospitals.");
};

export default function ManageHospitalDetails() {
  const {
    data: hospitals,
    setData: setHospitals,
    isLoading: isLoadingList,
    error: loadError,
  } = useApiData(loadHospitals, {
    initial: [],
    errorMessage: "Server error. Could not load hospitals.",
  });
  const [error, setError] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const navigate = useNavigate();

  const handleModify = (hospitalId) => {
    navigate(`/admin/hospitals/manage?id=${hospitalId}`);
  };

  const handleDelete = async (hospitalId) => {
    if (deleteConfirm !== hospitalId) {
      setDeleteConfirm(hospitalId);
      return;
    }
    setIsDeleting(true);
    setError("");
    try {
      const res = await api.deleteHospital(hospitalId);
      if (res && res.message && !res.detail) {
        setHospitals((prev) => prev.filter((h) => h.id !== hospitalId));
      } else {
        setError(res?.detail || res?.message || "Failed to delete hospital.");
      }
    } catch {
      setError("Server error. Try again.");
    } finally {
      setIsDeleting(false);
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

        <AsyncState
          isLoading={isLoadingList}
          error={loadError}
          isEmpty={hospitals.length === 0}
          loadingText="Loading hospitals..."
          emptyText="No hospitals found."
        >
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
                {hospitals.map((hospital) => (
                    <tr key={hospital.id}>
                      <td>{hospital.id}</td>
                      <td>{hospital.hospital_name}</td>
                      <td>{hospital.city}</td>
                      <td>{hospital.state}</td>
                      <td>
                        <button
                          className="modify-btn"
                          onClick={() => handleModify(hospital.id)}
                          disabled={isDeleting}
                        >
                          Modify
                        </button>
                        <button
                          className="delete-btn"
                          onClick={() => handleDelete(hospital.id)}
                          disabled={isDeleting}
                        >
                          {deleteConfirm === hospital.id ? "Confirm?" : "Delete"}
                          {deleteConfirm === hospital.id && (
                            <span className="confirm-badge">Click again</span>
                          )}
                        </button>
                      </td>
                    </tr>
                ))}
              </tbody>
            </table>
          </div>
        </AsyncState>
      </div>
    </AdminBase>
  );
}
