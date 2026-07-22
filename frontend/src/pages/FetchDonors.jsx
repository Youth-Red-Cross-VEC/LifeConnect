import { useState } from "react";
import { api } from "../services/api";

export default function FetchDonors() {
  const [bloodType, setBloodType] = useState("");
  const [hospitalAddress, setHospitalAddress] = useState("");
  const [donors, setDonors] = useState([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  // Table sorting, pagination, search query
  const [tableSearch, setTableSearch] = useState("");
  const [sortField, setSortField] = useState("Name");
  const [sortOrder, setSortOrder] = useState("asc");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setDonors([]);
    setIsLoading(true);
    setSearched(true);
    setCurrentPage(1);

    try {
      const params = { blood_type: bloodType };
      if (hospitalAddress) params.hospital_address = hospitalAddress;
      const res = await api.getDonors(params);

      if (res && !res.error) {
        setDonors(res);
      } else {
        setError(res?.error || "No donors found.");
      }
    } catch {
      setError("Server error. Try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortOrder("asc");
    }
  };

  // Filter local results
  const filteredDonors = donors.filter((d) => {
    const query = tableSearch.toLowerCase();
    return (
      (d.Name || "").toLowerCase().includes(query) ||
      (d.blood_grp || "").toLowerCase().includes(query) ||
      (d.city || "").toLowerCase().includes(query) ||
      (d.status || "").toLowerCase().includes(query)
    );
  });

  // Sort local results
  const sortedDonors = [...filteredDonors].sort((a, b) => {
    let aVal = a[sortField] || "";
    let bVal = b[sortField] || "";

    if (typeof aVal === "string") aVal = aVal.toLowerCase();
    if (typeof bVal === "string") bVal = bVal.toLowerCase();

    if (aVal < bVal) return sortOrder === "asc" ? -1 : 1;
    if (aVal > bVal) return sortOrder === "asc" ? 1 : -1;
    return 0;
  });

  // Paginated sorted results
  const totalPages = Math.ceil(sortedDonors.length / itemsPerPage);
  const paginatedDonors = sortedDonors.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  return (
    <div className="fetch-donors-wrapper">
      <style>{`
        .fetch-donors-wrapper {
          font-family: "Roboto", sans-serif;
          background-color: #f4f4f4;
          margin: 0;
          padding: 0;
          min-height: 100vh;
          width: 100vw;
          box-sizing: border-box;
          color: #333;
        }

        /* Header Styles */
        .fetch-donors-wrapper .header {
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

        .fetch-donors-wrapper .header h1 {
          margin: 0;
          font-family: "Georgia", serif;
          font-size: 2rem;
          font-weight: bold;
        }

        .fetch-donors-wrapper .header a {
          text-decoration: none;
          color: #f4f4f4;
        }

        .fetch-donors-wrapper .header .button-container {
          display: flex;
          justify-content: flex-end;
          gap: 10px;
        }

        .fetch-donors-wrapper .header button {
          background-color: #fff;
          color: #8b0000;
          font-weight: bold;
          border: none;
          padding: 8px 16px;
          font-size: 1rem;
          border-radius: 4px;
          cursor: pointer;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }

        .fetch-donors-wrapper .header button:hover {
          background-color: #f2f2f2;
        }

        /* Form and Container */
        .fetch-donors-wrapper .form-container {
          display: flex;
          justify-content: center;
          align-items: center;
          flex-wrap: wrap;
          gap: 20px;
          margin-top: 30px;
          padding: 20px;
        }

        .fetch-donors-wrapper .form-container img {
          width: 350px;
          height: auto;
          border-radius: 8px;
          box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        .fetch-donors-wrapper .form-content {
          background-color: white;
          padding: 25px;
          border-radius: 8px;
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
          max-width: 600px;
          width: 100%;
          box-sizing: border-box;
          text-align: left;
        }

        .fetch-donors-wrapper .form-content h2 {
          text-align: center;
          margin-bottom: 20px;
          color: #8b0000;
          font-weight: bold;
        }

        .fetch-donors-wrapper label {
          font-weight: bold;
          color: #8b0000;
          margin-bottom: 10px;
          display: block;
        }

        .fetch-donors-wrapper select,
        .fetch-donors-wrapper input[type="text"] {
          width: 100%;
          padding: 12px;
          margin-bottom: 15px;
          border-radius: 10px;
          border: 2px solid #8b0000;
          font-size: 14px;
          box-sizing: border-box;
        }

        .fetch-donors-wrapper .submit-btn {
          width: 150px;
          padding: 12px;
          background-color: #8b0000;
          color: white;
          border: none;
          border-radius: 10px;
          cursor: pointer;
          font-size: 16px;
          font-weight: bold;
          margin: 0 auto;
          display: block;
          transition: background-color 0.2s;
        }

        .fetch-donors-wrapper .submit-btn:hover:not(:disabled) {
          background-color: #9c0001;
        }

        /* Results table styling */
        .fetch-donors-wrapper .page-title {
          text-align: center;
          margin: 40px 0 20px 0;
          font-family: "Georgia", serif;
          color: #8b0000;
          font-size: 2.5rem;
          font-weight: bold;
          text-transform: uppercase;
        }

        .fetch-donors-wrapper .table-container {
          margin: 0 auto 50px auto;
          width: 85%;
          background-color: #fff;
          border-radius: 8px;
          padding: 20px;
          box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        }

        .fetch-donors-wrapper .controls-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 15px;
          flex-wrap: wrap;
          gap: 10px;
        }

        .fetch-donors-wrapper .search-input {
          padding: 8px 12px;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-size: 14px;
          width: 250px;
        }

        .fetch-donors-wrapper table {
          width: 100%;
          border-collapse: collapse;
        }

        .fetch-donors-wrapper th {
          background-color: #8b0000;
          color: #fff;
          padding: 12px 10px;
          font-size: 1rem;
          text-align: left;
          cursor: pointer;
          user-select: none;
        }

        .fetch-donors-wrapper th:hover {
          background-color: #a30001;
        }

        .fetch-donors-wrapper td {
          padding: 12px 10px;
          border-bottom: 1px solid #ddd;
          text-align: left;
        }

        .fetch-donors-wrapper tr:hover td {
          background-color: #f8d7da;
          color: #8b0000;
        }

        .fetch-donors-wrapper .pagination {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 10px;
          margin-top: 20px;
        }

        .fetch-donors-wrapper .page-btn {
          background-color: #8b0000;
          color: white;
          border: none;
          padding: 6px 12px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        }

        .fetch-donors-wrapper .page-btn:disabled {
          background-color: #ccc;
          cursor: not-allowed;
        }

        .fetch-donors-wrapper .alert-error {
          background-color: #f8d7da;
          color: #721c24;
          padding: 12px;
          border-radius: 8px;
          margin-bottom: 20px;
          border: 1px solid #f5c6cb;
          font-weight: bold;
          text-align: center;
        }

        /* Mobile View */
        @media (max-width: 768px) {
          .fetch-donors-wrapper .form-container {
            flex-direction: column;
            align-items: center;
          }

          .fetch-donors-wrapper .header h1 {
            font-size: 1.5rem;
          }

          .fetch-donors-wrapper .header button {
            font-size: 0.9rem;
            padding: 6px 12px;
          }

          .fetch-donors-wrapper .form-container img {
            display: none;
          }

          .fetch-donors-wrapper .form-content {
            width: 100%;
            max-width: 400px;
            padding: 15px;
          }

          .fetch-donors-wrapper .form-content h2 {
            font-size: 1.5rem;
            margin-bottom: 15px;
          }

          .fetch-donors-wrapper label,
          .fetch-donors-wrapper select,
          .fetch-donors-wrapper input[type="text"],
          .fetch-donors-wrapper .submit-btn {
            font-size: 14px;
          }

          .fetch-donors-wrapper .submit-btn {
            padding: 10px;
          }

          .fetch-donors-wrapper .table-container {
            width: 95%;
            padding: 10px;
            overflow-x: auto;
          }

          .fetch-donors-wrapper table {
            font-size: 0.8rem;
          }

          .fetch-donors-wrapper th,
          .fetch-donors-wrapper td {
            padding: 8px 6px;
            white-space: nowrap;
          }

          .fetch-donors-wrapper .search-input {
            width: 100%;
          }
        }
      `}</style>

      {/* Header Section */}
      <div className="header">
        <a href="/">
          <h1>LifeConnect</h1>
        </a>
        <div className="button-container">
          <a href="/donor/generate-request">
            <button>Generate Blood Request</button>
          </a>
          <button onClick={() => (window.location.href = "/")}>Back to Home</button>
        </div>
      </div>

      {/* Form Section */}
      <div className="form-container">
        {/* Image Section */}
        <img src="/images/fetch_donors/imgs.png" alt="Decorative Image" />

        {/* Form Content Section */}
        <div className="form-content">
          <h2>Find Donors</h2>
          <form onSubmit={handleSubmit}>
            <label htmlFor="bloodType">Blood Type:</label>
            <select
              id="bloodType"
              name="bloodType"
              required
              value={bloodType}
              onChange={(e) => setBloodType(e.target.value)}
              disabled={isLoading}
            >
              <option value="">Select Blood Type</option>
              <option value="A+">A+</option>
              <option value="B+">B+</option>
              <option value="O+">O+</option>
              <option value="AB+">AB+</option>
              <option value="A-">A-</option>
              <option value="B-">B-</option>
              <option value="O-">O-</option>
              <option value="AB-">AB-</option>
            </select>

            <label htmlFor="hospital_address">Hospital Address (Optional):</label>
            <input
              type="text"
              id="hospital_address"
              name="hospital_address"
              placeholder="Enter Hospital Address"
              value={hospitalAddress}
              onChange={(e) => setHospitalAddress(e.target.value)}
              disabled={isLoading}
            />

            <button className="submit-btn" type="submit" disabled={isLoading}>
              {isLoading ? "Searching..." : "Find Donor"}
            </button>
          </form>
        </div>
      </div>

      {/* Results Section */}
      {searched && (
        <div>
          <div className="page-title">Available Blood Donors</div>

          {error && (
            <div className="table-container">
              <div className="alert-error">{error}</div>
            </div>
          )}

          {!error && (
            <div className="table-container">
              <div className="controls-row">
                <div>
                  Showing {paginatedDonors.length} of {filteredDonors.length} donors
                </div>
                <input
                  type="text"
                  className="search-input"
                  placeholder="Search donors..."
                  value={tableSearch}
                  onChange={(e) => {
                    setTableSearch(e.target.value);
                    setCurrentPage(1);
                  }}
                />
              </div>

              <div style={{ overflowX: "auto" }}>
                <table>
                  <thead>
                    <tr>
                      <th onClick={() => handleSort("Name")}>
                        Name {sortField === "Name" && (sortOrder === "asc" ? "▲" : "▼")}
                      </th>
                      <th onClick={() => handleSort("blood_grp")}>
                        Blood Group {sortField === "blood_grp" && (sortOrder === "asc" ? "▲" : "▼")}
                      </th>
                      <th onClick={() => handleSort("city")}>
                        City {sortField === "city" && (sortOrder === "asc" ? "▲" : "▼")}
                      </th>
                      <th onClick={() => handleSort("status")}>
                        Status {sortField === "status" && (sortOrder === "asc" ? "▲" : "▼")}
                      </th>
                      <th onClick={() => handleSort("distance")}>
                        Distance {sortField === "distance" && (sortOrder === "asc" ? "▲" : "▼")}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedDonors.length > 0 ? (
                      paginatedDonors.map((donor, idx) => (
                        <tr key={idx}>
                          <td>{donor.Name}</td>
                          <td>{donor.blood_grp}</td>
                          <td>{donor.city}</td>
                          <td>{donor.status}</td>
                          <td>{donor.distance !== null && donor.distance !== undefined ? donor.distance : "N/A"}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="5" style={{ textAlign: "center", color: "#666" }}>
                          No donors found for this query.
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
      )}
    </div>
  );
}
