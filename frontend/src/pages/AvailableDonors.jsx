import React, { useEffect, useState } from "react";

export default function AvailableDonors({ donors = [] }) {
    const [tableInitialized, setTableInitialized] = useState(false);

    useEffect(() => {
        // Initialize DataTable when component mounts
        // Note: In a real React app, you might want to use a React-based table library
        // like react-table or MUI DataGrid instead of jQuery DataTables

        if (typeof window !== "undefined" && window.jQuery && !tableInitialized) {
            const $ = window.jQuery;

            // Destroy existing table if it exists
            if ($.fn.DataTable.isDataTable("#donorTable")) {
                $("#donorTable").DataTable().destroy();
            }

            // Initialize DataTable
            $("#donorTable").DataTable({
                pageLength: 10,
                responsive: true,
            });

            setTableInitialized(true);
        }
    }, [donors, tableInitialized]);

    return (
        <>
            <style>{`
        /* General Body Styling */
        .available-donors-page {
          font-family: Arial, sans-serif;
          margin: 0;
          padding: 0;
          background-color: #f8f8f8;
          color: #333;
        }

        /* Header Styling */
        .donors-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          background-color: #8b0000;
          color: #fff;
          padding: 10px 20px;
          box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
        }

        .donors-header h1 {
          margin: 0;
          font-family: "Georgia", serif;
          font-size: 2rem;
          font-weight: bold;
        }

        .donors-header .button-container {
          display: flex;
          justify-content: flex-end;
          gap: 10px;
        }

        .donors-header button {
          background-color: #fff;
          color: #8b0000;
          border: none;
          padding: 8px 16px;
          font-size: 1rem;
          border-radius: 4px;
          cursor: pointer;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }

        .donors-header button:hover {
          background-color: #f2f2f2;
        }

        .page-title {
          text-align: center;
          margin: 20px 0;
          font-family: "Georgia", serif;
          color: #8b0000;
          font-size: 2.5rem;
          text-transform: uppercase;
        }

        .table-container {
          margin: 0 auto;
          width: 85%;
          background-color: #fff;
          border-radius: 8px;
          padding: 20px;
          box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
          overflow-x: auto;
        }

        table.dataTable {
          border: none;
          width: 100%;
        }

        table.dataTable thead {
          background-color: #8b0000;
          color: #fff;
        }

        table.dataTable thead th {
          font-size: 1rem;
          padding: 12px;
        }

        table.dataTable tbody td {
          padding: 10px;
        }

        table.dataTable tbody tr:hover {
          background-color: #f8d7da;
          color: #8b0000;
        }

        a {
          text-decoration: none;
          color: #8b0000;
        }

        a:hover {
          text-decoration: underline;
          color: #6a0000;
        }

        @media (max-width: 768px) {
          .donors-header h1 {
            font-size: 1.5rem;
          }

          .donors-header button {
            font-size: 0.9rem;
            padding: 6px 12px;
          }

          .page-title {
            font-size: 1.8rem;
          }

          .table-container {
            width: 95%;
            padding: 10px;
          }

          table.dataTable {
            font-size: 0.8rem;
          }

          table.dataTable thead th {
            font-size: 0.9rem;
          }

          table.dataTable tbody td {
            font-size: 0.8rem;
            white-space: nowrap;
          }

          div.dataTables_filter {
            text-align: center;
          }
        }

        @media (max-width: 480px) {
          .donors-header {
            flex-direction: column;
            text-align: center;
          }

          .donors-header h1 {
            font-size: 1.3rem;
            margin-bottom: 5px;
          }

          .donors-header button {
            font-size: 0.8rem;
            padding: 5px 10px;
          }

          .page-title {
            font-size: 1.5rem;
            margin: 10px 0;
          }

          table.dataTable {
            font-size: 0.7rem;
          }

          table.dataTable thead th {
            font-size: 0.8rem;
          }
        }
      `}</style>

            <div className="available-donors-page">
                {/* Header */}
                <div className="donors-header">
                    <h1>LifeConnect</h1>
                    <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                        <a href="/generate-request">
                            <button>Generate Blood Request</button>
                        </a>
                        <button onClick={() => (window.location.href = "/")}>Back to Home</button>
                    </div>
                </div>

                {/* Page Title */}
                <div className="page-title">Available Blood Donors</div>

                {/* Table */}
                <div className="table-container">
                    <table id="donorTable" className="display" style={{ width: "100%" }}>
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Blood Group</th>
                                <th>City</th>
                                <th>Status</th>
                                <th>Distance</th>
                            </tr>
                        </thead>
                        <tbody>
                            {donors.map((donor, index) => (
                                <tr key={index}>
                                    <td>{donor.Name}</td>
                                    <td>{donor.blood_grp}</td>
                                    <td>{donor.city}</td>
                                    <td>{donor.status}</td>
                                    <td>{donor.distance !== null && donor.distance !== undefined ? donor.distance : "N/A"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/*
        ======================================================
        BACKEND CALL STRUCTURE — Available Donors
        ======================================================

        ENDPOINT
        --------
        GET /api/donors/available
        
        QUERY PARAMETERS (optional)
        ---------------------------
        - blood_group: string (filter by blood group)
        - city: string (filter by city)
        - hospital_id: string (find donors near a specific hospital)

        AUTH
        ----
        Public or authenticated user

        RESPONSE (example)
        ------------------
        {
          donors: [
            {
              Name: string,
              blood_grp: string,
              city: string,
              status: string,
              distance: number | null
            }
          ]
        }

        FRONTEND RESPONSIBILITY
        -----------------------
        - Render donors in a searchable, sortable table
        - Initialize DataTable for enhanced UX
        - Handle empty state when no donors available

        DEPENDENCIES
        ------------
        - jQuery (loaded via CDN or npm)
        - DataTables (loaded via CDN or npm)
        
        NOTE: Consider migrating to a React-based table library
        like react-table or @tanstack/react-table for better
        integration with React ecosystem.

        ERROR CASES
        -----------
        - 404 → no donors found
        - 500 → server error
      */}
        </>
    );
}
