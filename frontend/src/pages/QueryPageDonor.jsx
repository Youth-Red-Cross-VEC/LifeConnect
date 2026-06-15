import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";

export default function QueryPageDonor() {
  const [form, setForm] = useState({
    user_name: "",
    user_email: "",
    user_query: "",
  });
  const [queries, setQueries] = useState([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setIsLoading(true);
    try {
      const res = await api.submitQuery(form);
      if (res && res.success === true) {
        setSuccess(res.message || "Your query has been submitted successfully. We will get back to you soon.");
        setForm({ user_name: "", user_email: "", user_query: "" });
        // Refresh query list if backend returns updated list
        if (res.queries) setQueries(res.queries);
      } else {
        setError(res?.message || "Failed to submit query. Please try again.");
      }
    } catch {
      setError("Server error. Try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="query-donor-wrapper">
      <style>{`
        .query-donor-wrapper {
          margin: 0;
          padding: 0;
          font-family: 'Poppins', sans-serif;
          background-color: #f8f8f8;
          min-height: 100vh;
          width: 100vw;
          box-sizing: border-box;
          color: #333;
        }

        .query-donor-wrapper .header {
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

        .query-donor-wrapper .header h1 {
          margin: 0;
          font-family: "Georgia", serif;
          font-size: 2rem;
          font-weight: bold;
          color: whitesmoke;
        }

        .query-donor-wrapper .header a {
          text-decoration: none;
          color: #f4f4f4;
        }

        .query-donor-wrapper .header button {
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

        .query-donor-wrapper .header button:hover {
          background-color: #f2f2f2;
        }

        .query-donor-wrapper h1.page-title {
          text-align: center;
          color: #b30001;
          margin-top: 20px;
          font-size: 2.5rem;
          font-weight: bold;
        }

        .query-donor-wrapper form {
          max-width: 700px;
          margin: 20px auto;
          padding: 20px;
          background-color: #ffffff;
          border-radius: 20px;
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        }

        .query-donor-wrapper fieldset {
          margin-bottom: 20px;
          border: 1px solid #b30001;
          padding: 15px;
          border-radius: 20px;
          text-align: left;
        }

        .query-donor-wrapper legend {
          font-weight: bold;
          color: #b30001;
          padding: 0 10px;
          font-size: 1.1rem;
        }

        .query-donor-wrapper label {
          display: block;
          font-weight: 600;
          margin-bottom: 5px;
          margin-top: 10px;
        }

        .query-donor-wrapper input[type="text"],
        .query-donor-wrapper input[type="email"],
        .query-donor-wrapper textarea {
          width: 100%;
          box-sizing: border-box;
          padding: 8px;
          margin: 8px 0;
          font-size: 14px;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-family: 'Poppins', sans-serif;
        }

        .query-donor-wrapper textarea {
          height: 120px;
          resize: vertical;
        }

        .query-donor-wrapper .submit-btn {
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

        .query-donor-wrapper .submit-btn:hover:not(:disabled) {
          background-color: #9f2c2c;
        }

        .query-donor-wrapper .submit-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .query-donor-wrapper .alert-error {
          background-color: #f8d7da;
          color: #721c24;
          padding: 12px;
          border-radius: 8px;
          margin-bottom: 20px;
          border: 1px solid #f5c6cb;
          font-weight: bold;
          text-align: center;
        }

        .query-donor-wrapper .alert-success {
          background-color: #d4edda;
          color: #155724;
          padding: 12px;
          border-radius: 8px;
          margin-bottom: 20px;
          border: 1px solid #c3e6cb;
          font-weight: bold;
          text-align: center;
        }

        .query-donor-wrapper a.return-link {
          text-align: center;
          display: block;
          margin-top: 15px;
          margin-bottom: 30px;
          color: #b30001;
          text-decoration: none;
          font-weight: bold;
        }

        .query-donor-wrapper a.return-link:hover {
          text-decoration: underline;
        }

        /* Query History Table */
        .query-donor-wrapper .table-wrapper {
          max-width: 1000px;
          margin: 20px auto 40px;
          overflow-x: auto;
        }

        .query-donor-wrapper .table-wrapper h2 {
          color: #b30001;
          font-size: 1.4rem;
          font-weight: bold;
          margin-bottom: 12px;
          text-align: center;
        }

        .query-donor-wrapper table {
          width: 100%;
          border-collapse: collapse;
          background: #fff;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        .query-donor-wrapper th,
        .query-donor-wrapper td {
          padding: 12px 16px;
          text-align: left;
          border-bottom: 1px solid #eee;
          font-size: 14px;
        }

        .query-donor-wrapper thead {
          background-color: #8b0000;
          color: #fff;
        }

        .query-donor-wrapper tbody tr:hover {
          background-color: #fff5f5;
        }

        .query-donor-wrapper .badge-pending {
          background: #fff3cd;
          color: #856404;
          padding: 2px 10px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 600;
        }

        .query-donor-wrapper .badge-answered {
          background: #d4edda;
          color: #155724;
          padding: 2px 10px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 600;
        }

        @media (max-width: 768px) {
          .query-donor-wrapper .header {
            flex-direction: column;
            height: auto;
            padding: 10px;
          }

          .query-donor-wrapper .header button {
            margin-top: 10px;
            width: 100%;
          }

          .query-donor-wrapper h1.page-title {
            font-size: 2rem;
          }

          .query-donor-wrapper form,
          .query-donor-wrapper .table-wrapper {
            margin: 10px;
            padding: 15px;
          }

          .query-donor-wrapper .submit-btn {
            width: 100%;
          }
        }
      `}</style>

      {/* Header */}
      <div className="header">
        <a href="/"><h1>LifeConnect</h1></a>
        <button onClick={() => navigate("/")}>Back to Home</button>
      </div>

      <h1 className="page-title">User Query Page</h1>

      <form onSubmit={handleSubmit}>
        {error && <div className="alert-error">{error}</div>}
        {success && <div className="alert-success">✅ {success}</div>}

        <fieldset>
          <legend>Submit Your Query</legend>

          <label htmlFor="user_name">Your Name</label>
          <input
            type="text"
            id="user_name"
            name="user_name"
            value={form.user_name}
            onChange={handleChange}
            placeholder="Enter your name"
            required
            disabled={isLoading}
          />

          <label htmlFor="user_email">Your Email</label>
          <input
            type="email"
            id="user_email"
            name="user_email"
            value={form.user_email}
            onChange={handleChange}
            placeholder="Enter your email"
            required
            disabled={isLoading}
          />

          <label htmlFor="user_query">Your Query</label>
          <textarea
            id="user_query"
            name="user_query"
            value={form.user_query}
            onChange={handleChange}
            placeholder="Type your query here..."
            required
            disabled={isLoading}
          />
        </fieldset>

        <button type="submit" className="submit-btn" disabled={isLoading}>
          {isLoading ? "Submitting..." : "Submit Query"}
        </button>
      </form>

      <a href="/donor/dashboard" className="return-link">← Return to Dashboard</a>

      {/* Query History Table */}
      {queries.length > 0 && (
        <div className="table-wrapper">
          <h2>Your Query History</h2>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>User Name</th>
                <th>Your Query</th>
                <th>Admin Response</th>
              </tr>
            </thead>
            <tbody>
              {queries.map((q) => (
                <tr key={q.id}>
                  <td>{q.id}</td>
                  <td>{q.user_name}</td>
                  <td>{q.user_query}</td>
                  <td>
                    {q.admin_response ? (
                      <span className="badge-answered">{q.admin_response}</span>
                    ) : (
                      <span className="badge-pending">Pending</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
