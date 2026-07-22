import { useState } from "react";
import AdminBase from "./AdminBase";

export default function QueryPageAdmin({ queries = [], onSubmitResponse }) {
  const [responses, setResponses] = useState({});

  const handleChange = (queryId, value) => {
    setResponses((prev) => ({ ...prev, [queryId]: value }));
  };

  const handleSubmit = (e, queryId) => {
    e.preventDefault();
    onSubmitResponse?.({ query_id: queryId, admin_response: responses[queryId] ?? "" });
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
