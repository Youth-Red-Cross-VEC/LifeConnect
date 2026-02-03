import React from "react";
import AdminBase from "./AdminBase";

export default function AdminDashboard({
  adminName,
  activeDonorsCount,
  totalRequests,
  notifications = {},
}) {
  return (
    <AdminBase active="dashboard">
      <main className="dashboard">
        {/* ================= GREETING ================= */}
        <div className="greeting">
          <h1>Welcome, {adminName} 👋</h1>
          <p>LifeConnect Dashboard</p>
        </div>

        {/* ================= STATS ================= */}
        <div className="card-container">
          <div className="card">
            <h2>Total Active Donors</h2>
            <div className="card-data">
              <span className="card-number">{activeDonorsCount}</span>
            </div>
          </div>

          <div className="card">
            <h2>Total Requests Received</h2>
            <div className="card-data">
              <span className="card-number">{totalRequests}</span>
            </div>
          </div>
        </div>

        {/* ================= BLOOD REQUEST MANAGEMENT ================= */}
        <section className="category">
          <h2>Manage Blood Request</h2>

          <div className="tiles">
            <a href="/admin/requests/new" className="tile-link">
              <div className="tile">
                {notifications.Not_Approved > 0 && (
                  <span className="badge">
                    {notifications.Not_Approved}
                  </span>
                )}
                <h3>New Requests</h3>
                <p>Manage all incoming blood requests.</p>
              </div>
            </a>

            <a href="/admin/requests/ongoing" className="tile-link">
              <div className="tile">
                {notifications.Pending > 0 && (
                  <span className="badge">
                    {notifications.Pending}
                  </span>
                )}
                <h3>Ongoing Requests</h3>
                <p>Track ongoing blood donation requests.</p>
              </div>
            </a>

            <a href="/admin/requests/closed" className="tile-link">
              <div className="tile">
                <h3>Closed Requests</h3>
                <p>View completed requests.</p>
              </div>
            </a>

            <a href="/admin/requests/expired" className="tile-link">
              <div className="tile">
                {notifications.Expired > 0 && (
                  <span className="badge">
                    {notifications.Expired}
                  </span>
                )}
                <h3>Expired Requests</h3>
                <p>View expired blood requests.</p>
              </div>
            </a>

            <a href="/admin/requests/declined" className="tile-link">
              <div className="tile">
                <h3>Declined Requests</h3>
                <p>View declined blood requests.</p>
              </div>
            </a>
          </div>
        </section>

        {/* ================= ADMIN ACTIVITIES ================= */}
        <section className="category manage-activities">
          <h2>Manage Activities</h2>

          <div className="tiles">
            <a href="/admin/analytics" className="tile-link">
              <div className="tile">
                <h3>Analytics</h3>
                <p>View Analytics for Donors</p>
              </div>
            </a>

            <a href="/admin/donors" className="tile-link">
              <div className="tile">
                <h3>Manage Donors</h3>
                <p>Manage Donor Details</p>
              </div>
            </a>

            <a href="/admin/hospitals" className="tile-link">
              <div className="tile">
                <h3>Manage Hospitals</h3>
                <p>Manage Hospital Details</p>
              </div>
            </a>

            <a href="/admin/certificates" className="tile-link">
              <div className="tile">
                <h3>Generate Certificates</h3>
                <p>Generate Certificates for Donors</p>
              </div>
            </a>

            <a href="/admin/upload-csv" className="tile-link">
              <div className="tile">
                <h3>Extract CSV Data</h3>
                <p>Extract Donor Details from CSV</p>
              </div>
            </a>
          </div>
        </section>
      </main>

      {/*
        ======================================================
        BACKEND CALL STRUCTURE — Admin Dashboard
        ======================================================

        ENDPOINT
        --------
        GET /admin/dashboard

        AUTH
        ----
        Admin session / JWT required

        RESPONSE (example)
        ------------------
        {
          admin_name: string,
          active_donors_count: number,
          total_requests: number,
          notifications: {
            Not_Approved: number,
            Pending: number,
            Expired: number
          }
        }

        FRONTEND RESPONSIBILITY
        -----------------------
        - Render dashboard metrics
        - Highlight active sidebar via `active="dashboard"`
        - Navigation only (no writes)

        ERROR CASES
        -----------
        - 401 → redirect to /admin/login
        - 403 → access denied
        - 500 → dashboard error page
      */}
    </AdminBase>
  );
}
