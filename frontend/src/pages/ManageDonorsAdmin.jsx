import { useState } from "react";
import AdminBase from "./AdminBase";

const BLOOD_GROUPS = ["", "A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"];

export default function ManageDonorsAdmin({ donors = [], onSearch, onModifyDonor }) {
  const [searchName, setSearchName] = useState("");
  const [searchBloodGroup, setSearchBloodGroup] = useState("");

  const handleSearch = (e) => {
    e.preventDefault();
    onSearch?.({ name: searchName, blood_group: searchBloodGroup });
  };

  return (
    <AdminBase active="donors">
      <style>{`
        .manage-donors-container {
          padding: 20px;
          background-color: #f9f9f9;
        }

        .manage-donors-container h1 {
          color: #003f88;
          text-align: center;
          margin-bottom: 20px;
          font-size: 2.2rem;
        }

        .search-form {
          display: flex;
          flex-wrap: wrap;
          justify-content: center;
          gap: 10px;
          margin-bottom: 20px;
          background-color: #f1f1f1;
          padding: 15px;
          border-radius: 8px;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .search-form label { font-weight: bold; align-self: center; }

        .search-form input,
        .search-form select {
          padding: 8px 12px;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-size: 14px;
        }

        .search-form button {
          padding: 8px 12px;
          background-color: #003f88;
          color: #fff;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
          transition: background-color 0.3s ease;
        }

        .search-form button:hover { background-color: #0056b3; }

        .donors-table {
          width: 100%;
          border-collapse: collapse;
          background-color: #fff;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .donors-table thead { background-color: #003f88; color: #fff; }

        .donors-table th,
        .donors-table td { padding: 12px 15px; text-align: left; }

        .donors-table tbody tr:nth-child(even) { background-color: #f2f2f2; }
        .donors-table tbody tr:hover { background-color: #e6f7ff; }

        .donors-table th {
          font-weight: bold;
          text-transform: uppercase;
        }

        .modify-btn {
          padding: 5px 10px;
          background-color: #003f88;
          color: #fff;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          transition: background-color 0.3s ease;
        }

        .modify-btn:hover { background-color: #0056b3; }

        @media (max-width: 768px) {
          .donors-table,
          .donors-table thead,
          .donors-table tbody,
          .donors-table th,
          .donors-table td,
          .donors-table tr { display: block; }

          .donors-table th { text-align: right; }
          .donors-table td {
            text-align: left;
            border-bottom: 1px solid #ccc;
          }
        }
      `}</style>

      <div className="manage-donors-container">
        <h1>Manage Donors</h1>

        {/* Search Form */}
        <form className="search-form" onSubmit={handleSearch}>
          <label htmlFor="name">Search by Name:</label>
          <input
            type="text"
            id="name"
            name="name"
            placeholder="Enter donor name"
            value={searchName}
            onChange={(e) => setSearchName(e.target.value)}
          />

          <label htmlFor="blood_group">Search by Blood Group:</label>
          <select
            id="blood_group"
            name="blood_group"
            value={searchBloodGroup}
            onChange={(e) => setSearchBloodGroup(e.target.value)}
          >
            {BLOOD_GROUPS.map((bg) => (
              <option key={bg} value={bg}>{bg || "Select Blood Group"}</option>
            ))}
          </select>

          <button type="submit">Search</button>
        </form>

        {/* Donors Table */}
        <table className="donors-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Blood Group</th>
              <th>Active Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {donors.map((donor) => (
              <tr key={donor.id}>
                <td>{donor.id}</td>
                <td>{donor.name}</td>
                <td>{donor.email}</td>
                <td>{donor.blood_group}</td>
                <td data-label="Active Status">
                  {donor.active_status ? "Active" : "Inactive"}
                </td>
                <td data-label="Action">
                  <button
                    className="modify-btn"
                    type="button"
                    onClick={() => onModifyDonor?.(donor.id)}
                  >
                    Modify Donor
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/*
        ======================================================
        BACKEND CALL STRUCTURE — Manage Donors Admin
        ======================================================

        ENDPOINTS
        ---------
        GET /admin/donors                        → list all donors
        GET /admin/donors?name=...&blood_group=  → filtered search

        AUTH
        ----
        Admin session / JWT required

        RESPONSE (example)
        ------------------
        {
          donors: [
            { id, name, email, blood_group, active_status }
          ]
        }

        FRONTEND RESPONSIBILITY
        -----------------------
        - Search/filter by name or blood group
        - "Modify Donor" navigates to ManageEachDonorAdmin with donor_id

        ERROR CASES
        -----------
        - 401 → redirect to /admin/login
        - 500 → server error
      */}
    </AdminBase>
  );
}
