import { useState, useEffect } from "react";
import { api } from "../services/api";

export default function BloodBanks() {
  const [hospitals, setHospitals] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState("NAME");
  const [sortOrder, setSortOrder] = useState("asc");
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const itemsPerPage = 10;

  useEffect(() => {
    const fetchHospitals = async () => {
      try {
        const data = await api.getBloodBanks();
        if (data && !data.error) {
          setHospitals(data);
        } else {
          setError("Failed to load blood bank data.");
        }
      } catch {
        setError("Error connecting to server.");
      } finally {
        setIsLoading(false);
      }
    };
    fetchHospitals();
  }, []);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortOrder("asc");
    }
  };

  // Filter hospitals based on search query
  const filteredHospitals = hospitals.filter((h) => {
    const query = searchQuery.toLowerCase();
    return (
      (h.NAME || "").toLowerCase().includes(query) ||
      (h.ADDRESS || "").toLowerCase().includes(query) ||
      (h["Contact Number"] || "").toString().toLowerCase().includes(query)
    );
  });

  // Sort filtered hospitals
  const sortedHospitals = [...filteredHospitals].sort((a, b) => {
    let aVal = a[sortField] || "";
    let bVal = b[sortField] || "";

    if (typeof aVal === "string") aVal = aVal.toLowerCase();
    if (typeof bVal === "string") bVal = bVal.toLowerCase();

    if (aVal < bVal) return sortOrder === "asc" ? -1 : 1;
    if (aVal > bVal) return sortOrder === "asc" ? 1 : -1;
    return 0;
  });

  // Paginated sorted list
  const totalPages = Math.ceil(sortedHospitals.length / itemsPerPage);
  const paginatedHospitals = sortedHospitals.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  return (
    <div className="blood-banks-wrapper">
      <style>{`
        .blood-banks-wrapper {
          font-family: Arial, sans-serif;
          margin: 0;
          padding: 0;
          background-color: #f8f8f8;
          color: #333;
          min-height: 100vh;
          width: 100vw;
        }

        /* Header Styling */
        .blood-banks-wrapper .header {
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

        .blood-banks-wrapper .header h1 {
          margin: 0;
          font-family: "Georgia", serif;
          font-size: 2rem;
          font-weight: bold;
        }

        .blood-banks-wrapper .header button {
          background-color: #fff;
          color: #8b0000;
          border: none;
          padding: 8px 16px;
          font-size: 1rem;
          border-radius: 4px;
          cursor: pointer;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
          font-weight: bold;
        }

        .blood-banks-wrapper .header button:hover {
          background-color: #f2f2f2;
        }

        /* Page Title Styling */
        .blood-banks-wrapper .page-title {
          text-align: center;
          margin: 20px 0;
          font-family: "Georgia", serif;
          color: #8b0000;
          font-size: 2.5rem;
          text-transform: uppercase;
          font-weight: bold;
        }

        /* Table Container Styling */
        .blood-banks-wrapper .table-container {
          margin: 0 auto 40px auto;
          width: 85%;
          background-color: #fff;
          border-radius: 8px;
          padding: 20px;
          box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        }

        .blood-banks-wrapper .controls-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 15px;
          flex-wrap: wrap;
          gap: 10px;
        }

        .blood-banks-wrapper .search-input {
          padding: 8px 12px;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-size: 14px;
          width: 250px;
        }

        /* Table Styling */
        .blood-banks-wrapper table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 10px;
        }

        .blood-banks-wrapper th {
          background-color: #8b0000;
          color: #fff;
          padding: 12px 10px;
          font-size: 1rem;
          text-align: left;
          cursor: pointer;
          user-select: none;
        }

        .blood-banks-wrapper th:hover {
          background-color: #a30001;
        }

        .blood-banks-wrapper td {
          padding: 12px 10px;
          border-bottom: 1px solid #ddd;
          text-align: left;
        }

        .blood-banks-wrapper tr:hover td {
          background-color: #f8d7da;
          color: #8b0000;
        }

        .blood-banks-wrapper tr:hover a {
          color: #6a0000;
        }

        .blood-banks-wrapper a {
          text-decoration: none;
          color: #8b0000;
          font-weight: bold;
        }

        .blood-banks-wrapper a:hover {
          text-decoration: underline;
        }

        .blood-banks-wrapper .pagination {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 10px;
          margin-top: 20px;
        }

        .blood-banks-wrapper .page-btn {
          background-color: #8b0000;
          color: white;
          border: none;
          padding: 6px 12px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        }

        .blood-banks-wrapper .page-btn:disabled {
          background-color: #ccc;
          cursor: not-allowed;
        }

        .blood-banks-wrapper .alert-error {
          background-color: #f8d7da;
          color: #721c24;
          padding: 12px;
          border-radius: 8px;
          margin: 20px auto;
          width: 85%;
          text-align: center;
          font-weight: bold;
        }

        .blood-banks-wrapper .loading-spinner {
          text-align: center;
          font-size: 1.2rem;
          margin-top: 50px;
          color: #8b0000;
          font-weight: bold;
        }

        /* MEDIA QUERIES */
        @media (max-width: 768px) {
          .blood-banks-wrapper .header h1 {
            font-size: 1.5rem;
          }

          .blood-banks-wrapper .header button {
            font-size: 0.9rem;
            padding: 6px 12px;
          }

          .blood-banks-wrapper .page-title {
            font-size: 1.8rem;
          }

          .blood-banks-wrapper .table-container {
            width: 95%;
            padding: 10px;
            overflow-x: auto;
          }

          .blood-banks-wrapper table {
            font-size: 0.8rem;
          }

          .blood-banks-wrapper th,
          .blood-banks-wrapper td {
            padding: 8px 6px;
            white-space: nowrap;
          }

          .blood-banks-wrapper .search-input {
            width: 100%;
          }
        }
      `}</style>

      {/* Header */}
      <div className="header">
        <h1>LifeConnect</h1>
        <button onClick={() => (window.location.href = "/")}>Back to Home</button>
      </div>

      {/* Page Title */}
      <div className="page-title">BloodBanks</div>

      {error && <div className="alert-error">{error}</div>}

      {isLoading ? (
        <div className="loading-spinner">Loading Blood Bank Details...</div>
      ) : (
        <div className="table-container">
          <div className="controls-row">
            <div>
              Showing {paginatedHospitals.length} of {filteredHospitals.length} banks
            </div>
            <input
              type="text"
              className="search-input"
              placeholder="Search blood banks..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
            />
          </div>

          <div style={{ overflowX: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th onClick={() => handleSort("NAME")}>
                    Name {sortField === "NAME" && (sortOrder === "asc" ? "▲" : "▼")}
                  </th>
                  <th onClick={() => handleSort("ADDRESS")}>
                    Address {sortField === "ADDRESS" && (sortOrder === "asc" ? "▲" : "▼")}
                  </th>
                  <th onClick={() => handleSort("Contact Number")}>
                    Contact Number {sortField === "Contact Number" && (sortOrder === "asc" ? "▲" : "▼")}
                  </th>
                  <th>Website</th>
                </tr>
              </thead>
              <tbody>
                {paginatedHospitals.length > 0 ? (
                  paginatedHospitals.map((hospital, idx) => (
                    <tr key={idx}>
                      <td>{hospital.NAME}</td>
                      <td>{hospital.ADDRESS}</td>
                      <td>{hospital["Contact Number"]}</td>
                      <td>
                        {hospital.Website ? (
                          <a href={hospital.Website} target="_blank" rel="noreferrer">
                            Visit Website
                          </a>
                        ) : (
                          "None"
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="4" style={{ textAlign: "center", color: "#666" }}>
                      No blood banks found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="page-btn"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              >
                Previous
              </button>
              <span>
                Page {currentPage} of {totalPages}
              </span>
              <button
                className="page-btn"
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
