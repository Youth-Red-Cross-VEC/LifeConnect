import AdminBase from "./AdminBase";
import RequestsTable from "../components/RequestsTable";
import { useApiData } from "../hooks/useApiData";
import { api } from "../services/api";
import { unwrapList } from "../services/unwrap";

const loadDeclined = async () =>
  unwrapList(await api.getDeclinedRequests(), "Failed to load declined requests.");

export default function DeclinedRequestsAdmin() {
  const { data: requests, isLoading, error } = useApiData(loadDeclined, {
    initial: [],
    errorMessage: "Server error. Could not load declined requests.",
  });

  return (
    <AdminBase active="declined-requests">
      <style>{`
        .declined-requests-main {
          padding: 20px;
        }

        .declined-requests-main h1 {
          text-align: center;
          color: #c82333;
          margin-bottom: 20px;
          font-size: 2.2rem;
        }

        .declined-requests-table {
          width: 100%;
          border-collapse: collapse;
          background-color: #fff;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .declined-requests-table thead { background-color: #c82333; color: #fff; }

        .declined-requests-table th,
        .declined-requests-table td {
          padding: 12px 15px;
          text-align: left;
          font-size: 14px;
        }

        .declined-requests-table tbody tr:nth-child(even) { background-color: #f2f2f2; }
        .declined-requests-table tbody tr:hover { background-color: #fde8ea; }

        .declined-requests-table th {
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

        .details-inner-table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
        .details-inner-table td { padding: 6px 8px; border: 1px solid #eee; font-size: 14px; }

        .status-badge {
          display: inline-block;
          padding: 3px 10px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 600;
          background: #f8d7da;
          color: #721c24;
        }
      `}</style>

      <main className="declined-requests-main">
        <h1>Declined Blood Requests</h1>
        <RequestsTable
          requests={requests}
          isLoading={isLoading}
          error={error}
          tableClass="declined-requests-table"
          emptyText="No declined requests found."
        />
      </main>
    </AdminBase>
  );
}
