import { useState } from "react";
import AdminBase from "./AdminBase";
import RequestsTable from "../components/RequestsTable";
import CloseRequestForm from "../components/CloseRequestForm";
import { useApiData } from "../hooks/useApiData";
import { api } from "../services/api";
import { removeRequestById } from "../services/requests";
import { unwrapList } from "../services/unwrap";

const loadOngoing = async () =>
  unwrapList(await api.getOngoingRequests(), "Failed to load ongoing requests.");

export default function OngoingRequestsAdmin() {
  const { data: requests, setData: setRequests, isLoading, error } = useApiData(loadOngoing, {
    initial: [],
    errorMessage: "Server error. Could not load ongoing requests.",
  });
  const [message, setMessage] = useState("");

  const handleClosed = (requestId, text) => {
    setMessage(`✅ ${text}`);
    setRequests((prev) => removeRequestById(prev, requestId));
  };

  return (
    <AdminBase active="ongoing-requests">
      <style>{`
        .ongoing-requests-main {
          padding: 20px;
        }

        .ongoing-requests-main h1 {
          text-align: center;
          color: #c82333;
          margin-bottom: 20px;
          font-size: 2.2rem;
        }

        .ongoing-requests-table {
          width: 100%;
          border-collapse: collapse;
          background-color: #fff;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .ongoing-requests-table thead { background-color: #c82333; color: #fff; }

        .ongoing-requests-table th,
        .ongoing-requests-table td {
          padding: 12px 15px;
          text-align: left;
          font-size: 14px;
        }

        .ongoing-requests-table tbody tr:nth-child(even) { background-color: #f2f2f2; }
        .ongoing-requests-table tbody tr:hover { background-color: #fde8ea; }

        .ongoing-requests-table th {
          font-weight: bold;
          text-transform: uppercase;
        }

        .view-btn, .close-btn {
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

        .view-btn:hover, .close-btn:hover { background-color: #a71d2a; }

        .details-row { display: none; }
        .details-row.open { display: table-row; }

        .details-inner-table { width: 100%; border-collapse: collapse; }
        .details-inner-table td { padding: 6px 8px; border: 1px solid #eee; font-size: 14px; }

        .input-field { width: 100%; padding: 5px; margin: 5px 0; box-sizing: border-box; }

        .radio-group { display: flex; gap: 12px; margin: 6px 0; }

        .form-actions { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }

        .input-field { width: 100%; padding: 5px; margin: 5px 0; box-sizing: border-box; }
        .form-actions { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
        .close-btn { padding: 8px 14px; background: #c82333; color: #fff; border: none; border-radius: 5px; cursor: pointer; }
        .close-btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .details-inner-table { width: 100%; border-collapse: collapse; }
        .details-inner-table td { padding: 6px 8px; border: 1px solid #eee; font-size: 14px; }
      `}</style>

      <main className="ongoing-requests-main">
        <h1>Ongoing Blood Requests</h1>
        {message && (
          <p style={{ textAlign: "center", color: "#28a745", marginBottom: "12px" }}>{message}</p>
        )}
        <RequestsTable
          requests={requests}
          isLoading={isLoading}
          error={error}
          tableClass="ongoing-requests-table"
          emptyText="No ongoing requests."
          renderExtra={(request) => (
            <CloseRequestForm requestId={request.id} onClosed={handleClosed} />
          )}
        />
      </main>
    </AdminBase>
  );
}
