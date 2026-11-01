import { useState } from "react";
import AdminBase from "./AdminBase";
import RequestsTable from "../components/RequestsTable";
import CloseRequestForm from "../components/CloseRequestForm";
import { useApiData } from "../hooks/useApiData";
import { api } from "../services/api";
import { removeRequestById } from "../services/requests";
import { unwrapList } from "../services/unwrap";

const loadExpired = async () =>
  unwrapList(await api.getExpiredRequests(), "Failed to load expired requests.");

export default function ExpiredRequestsAdmin() {
  const { data: requests, setData: setRequests, isLoading, error } = useApiData(loadExpired, {
    initial: [],
    errorMessage: "Server error. Could not load expired requests.",
  });
  const [message, setMessage] = useState("");

  const handleClosed = (requestId, text) => {
    setMessage(`✅ ${text}`);
    setRequests((prev) => removeRequestById(prev, requestId));
  };

  return (
    <AdminBase active="expired-requests">
      <style>{`
        .expired-requests-main {
          padding: 20px;
        }

        .expired-requests-main h1 {
          text-align: center;
          color: #c82333;
          margin-bottom: 20px;
          font-size: 2.2rem;
        }

        .expired-requests-table {
          width: 100%;
          border-collapse: collapse;
          background-color: #fff;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .expired-requests-table thead { background-color: #c82333; color: #fff; }

        .expired-requests-table th,
        .expired-requests-table td {
          padding: 12px 15px;
          text-align: left;
          font-size: 14px;
        }

        .expired-requests-table tbody tr:nth-child(even) { background-color: #f2f2f2; }
        .expired-requests-table tbody tr:hover { background-color: #fde8ea; }

        .expired-requests-table th {
          font-weight: bold;
          text-transform: uppercase;
        }

        .view-btn {
          cursor: pointer;
          padding: 6px 12px;
          background-color: #c82333;
          color: white;
          border: none;
          border-radius: 4px;
          margin-right: 4px;
          font-size: 13px;
          transition: background-color 0.3s ease;
        }

        .view-btn:hover { background-color: #a71d2a; }

        .details-row { display: none; }
        .details-row.open { display: table-row; }

        .details-inner-table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
        .details-inner-table td { padding: 6px 8px; border: 1px solid #eee; font-size: 14px; }

        .action-buttons { margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap; }
        
        .approve-btn {
          cursor: pointer;
          padding: 6px 12px;
          background-color: #c82333;
          color: white;
          border: none;
          border-radius: 4px;
          margin-right: 4px;
          font-size: 13px;
          transition: background-color 0.3s ease;
        }
        .approve-btn:hover { background-color: #a71d2a; }

        .field { margin-bottom: 15px; display: block; font-size: 14px; }
        .field span { display: block; font-weight: bold; margin-bottom: 5px; }
        .field input[type="text"], .field input[type="number"], .field input[type="date"] {
          width: 100%;
          padding: 8px;
          border: 1px solid #ccc;
          border-radius: 4px;
        }

        .input-field { width: 100%; padding: 5px; margin: 5px 0; box-sizing: border-box; }
        .form-actions { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
        .close-btn { padding: 8px 14px; background: #c82333; color: #fff; border: none; border-radius: 5px; cursor: pointer; }
        .close-btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .details-inner-table { width: 100%; border-collapse: collapse; }
        .details-inner-table td { padding: 6px 8px; border: 1px solid #eee; font-size: 14px; }
      `}</style>

      <main className="expired-requests-main">
        <h1>Expired Blood Requests</h1>
        {message && (
          <p style={{ textAlign: "center", color: "#28a745", marginBottom: "12px" }}>{message}</p>
        )}
        <RequestsTable
          requests={requests}
          isLoading={isLoading}
          error={error}
          tableClass="expired-requests-table"
          emptyText="No expired requests."
          renderExtra={(request) => (
            <CloseRequestForm requestId={request.id} onClosed={handleClosed} />
          )}
        />
      </main>
    </AdminBase>
  );
}
