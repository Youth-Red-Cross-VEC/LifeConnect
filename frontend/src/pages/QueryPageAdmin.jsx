import { errorText } from "../services/requests";
import { useState } from "react";
import AdminBase from "./AdminBase";
import AsyncState from "../components/AsyncState";
import { useApiData } from "../hooks/useApiData";
import { api } from "../services/api";
import { unwrapList } from "../services/unwrap";

const loadQueries = async () => {
  const res = await api.getQueries();
  // The list endpoint answers { items: [...] }; older responses were a bare array.
  return unwrapList(res?.items ?? res, "Failed to load queries.");
};

export default function QueryPageAdmin() {
  const {
    data: queries,
    setData: setQueries,
    isLoading,
    error,
  } = useApiData(loadQueries, {
    initial: [],
    errorMessage: "Server error. Could not load queries.",
  });
  const [responses, setResponses] = useState({});
  const [actionMsg, setActionMsg] = useState("");

  const handleChange = (queryId, value) => {
    setResponses((prev) => ({ ...prev, [queryId]: value }));
  };

  const handleSubmit = async (e, queryId) => {
    e.preventDefault();
    setActionMsg("");
    const responseText = responses[queryId]?.trim();
    if (!responseText) {
      setActionMsg("❌ Please type a response before submitting.");
      return;
    }
    try {
      const res = await api.replyToQuery(queryId, {
        admin_response: responseText,
      });
      if (res && res.id) {
        setActionMsg(`✅ Response submitted for query #${queryId}.`);
        setQueries((prev) =>
          prev.map((q) => (q.id === queryId ? { ...q, admin_response: responseText } : q))
        );
        setResponses((prev) => ({ ...prev, [queryId]: "" }));
      } else {
        setActionMsg(`❌ ${errorText(res, "Failed to submit response.")}`);
      }
    } catch {
      setActionMsg("❌ Server error submitting response.");
    }
  };

  return (
    <AdminBase active="queries">
      <style>{`
        .query-admin-main { padding: 20px; }

        .query-admin-main h1 {
          text-align: center;
          color: #003f88;
          margin-bottom: 20px;
          font-size: 2.2rem;
        }

        .query-table {
          width: 100%;
          border-collapse: collapse;
          background-color: #fff;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .query-table thead { background-color: #003f88; color: #fff; }

        .query-table th,
        .query-table td {
          padding: 12px 15px;
          text-align: left;
          font-size: 14px;
        }

        .query-table tbody tr:nth-child(even) { background-color: #f2f2f2; }
        .query-table tbody tr:hover { background-color: #e6f7ff; }

        .query-table th { font-weight: bold; text-transform: uppercase; }

        .response-form {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .response-form textarea {
          padding: 8px;
          width: 100%;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-size: 14px;
          resize: vertical;
          box-sizing: border-box;
        }

        .response-form button {
          align-self: flex-start;
          background-color: #003f88;
          color: #fff;
          border: none;
          cursor: pointer;
          padding: 8px 16px;
          border-radius: 4px;
          font-size: 14px;
          transition: background-color 0.3s ease;
        }

        .response-form button:hover { background-color: #0056b3; }

        @media (max-width: 768px) {
          .query-table,
          .query-table thead,
          .query-table tbody,
          .query-table th,
          .query-table td,
          .query-table tr { display: block; }

          .query-table th { text-align: right; }
          .query-table td {
            text-align: left;
            border-bottom: 1px solid #ccc;
          }
        }
      `}</style>

      <main className="query-admin-main">
        <h1>Admin Query Management</h1>
        {actionMsg && (
          <p style={{ textAlign: "center", color: actionMsg.startsWith("❌") ? "#c82333" : "#28a745", marginBottom: "12px" }}>
            {actionMsg}
          </p>
        )}
        <AsyncState
          isLoading={isLoading}
          error={error}
          isEmpty={queries.length === 0}
          loadingText="Loading queries..."
          emptyText="No queries found."
        >
        <table className="query-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>User Name</th>
              <th>User Query</th>
              <th>Admin Response</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {queries.map((query) => (
              <tr key={query.id}>
                <td>{query.id}</td>
                <td>{query.user_name}</td>
                <td>{query.user_query}</td>
                <td>{query.admin_response || "Pending"}</td>
                <td>
                  <form
                    className="response-form"
                    onSubmit={(e) => handleSubmit(e, query.id)}
                  >
                    <input type="hidden" name="query_id" value={query.id} />
                    <textarea
                      name="admin_response"
                      rows={2}
                      placeholder="Type response"
                      value={responses[query.id] ?? ""}
                      onChange={(e) => handleChange(query.id, e.target.value)}
                    />
                    <button type="submit">Submit Response</button>
                  </form>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </AsyncState>
      </main>

      {/*
        ======================================================
        BACKEND CALL STRUCTURE — Query Page Admin
        ======================================================

        ENDPOINTS
        ---------
        GET  /admin/queries              → fetch all donor/user queries
        POST /admin/queries/reply        → submit admin response

        AUTH
        ----
        Admin session / JWT required

        REQUEST (POST, reply)
        ---------------------
        { query_id: string, admin_response: string }

        RESPONSE (GET, example)
        -----------------------
        {
          queries: [
            { id, user_name, user_query, admin_response }
          ]
        }

        FRONTEND RESPONSIBILITY
        -----------------------
        - Display all queries in a table
        - Allow inline response submission per query
        - Show "Pending" if no admin_response yet

        ERROR CASES
        -----------
        - 401 → redirect to /admin/login
        - 400 → missing response text
        - 500 → server error
      */}
    </AdminBase>
  );
}
