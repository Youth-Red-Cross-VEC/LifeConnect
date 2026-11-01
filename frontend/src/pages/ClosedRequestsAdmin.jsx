import AdminBase from "./AdminBase";
import RequestsTable from "../components/RequestsTable";
import { useApiData } from "../hooks/useApiData";
import { api } from "../services/api";
import { unwrapList } from "../services/unwrap";

const loadClosed = async () =>
  unwrapList(await api.getClosedRequests(), "Failed to load closed requests.");

export default function ClosedRequestsAdmin() {
  const { data: requests, isLoading, error } = useApiData(loadClosed, {
    initial: [],
    errorMessage: "Server error. Could not load closed requests.",
  });

  return (
    <AdminBase active="closed-requests">
      <style>{`
        .closed-requests-main {
          padding: 20px;
        }

        .closed-requests-main h1 {
          text-align: center;
          color: #c82333;
          margin-bottom: 20px;
          font-size: 2.2rem;
        }

        .closed-requests-table {
          width: 100%;
          border-collapse: collapse;
          background-color: #fff;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .closed-requests-table thead { background-color: #c82333; color: #fff; }

        .closed-requests-table th,
        .closed-requests-table td {
          padding: 12px 15px;
          text-align: left;
          font-size: 14px;
        }

        .closed-requests-table tbody tr:nth-child(even) { background-color: #f2f2f2; }
        .closed-requests-table tbody tr:hover { background-color: #fde8ea; }

        .closed-requests-table th {
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
          font-size: 13px;
          transition: background-color 0.3s ease;
        }

        .view-btn:hover { background-color: #a71d2a; }

        .details-row { display: none; }
        .details-row.open { display: table-row; }

        .details-inner-table { width: 100%; border-collapse: collapse; }
        .details-inner-table td { padding: 6px 8px; border: 1px solid #eee; font-size: 14px; }
      `}</style>

      <main className="closed-requests-main">
        <h1>Closed Blood Requests</h1>
        <RequestsTable
          requests={requests}
          isLoading={isLoading}
          error={error}
          tableClass="closed-requests-table"
          emptyText="No closed requests."
        />
      </main>
    </AdminBase>
  );
}
