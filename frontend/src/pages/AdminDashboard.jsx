import { useState, useEffect } from "react";
import AdminBase from "./AdminBase";
import { api } from "../services/api";

export default function AdminDashboard() {
  const [data, setData] = useState({
    admin_name: "Admin",
    active_donors_count: 0,
    total_requests: 0,
    notifications: {},
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const res = await api.getAdminDashboardData();
        if (res && !res.error && !res.detail) {
          // FastAPI backend returns { requests: { total, pending, ... }, donors: { active, total }, hospitals: { total } }
          setData({
            admin_name: res.admin_name || "Admin",
            active_donors_count: res.donors?.active ?? res.donors?.total ?? res.active_donors_count ?? 0,
            total_requests: res.requests?.total ?? res.total_requests ?? 0,
            notifications: {
              Pending: res.requests?.pending || 0,
              Expired: res.requests?.expired || 0,
              Declined: res.requests?.declined || 0,
            },
          });
        } else {
          setError(res?.detail || res?.error || "Failed to load dashboard data.");
        }
      } catch {
        setError("Error connecting to dashboard API.");
      } finally {
        setIsLoading(false);
      }
    };
    fetchDashboardData();
  }, []);

  return (
    <AdminBase active="dashboard">
      <style>{`
        .dashboard {
          background-color: #f4f6f9;
          padding: 30px;
          min-height: 100%;
        }

        .dashboard .greeting {
          margin-bottom: 28px;
          border-bottom: 1px solid #e5e7eb;
          padding-bottom: 16px;
        }

        .dashboard .greeting h1 {
          font-size: 26px;
          font-weight: 700;
          color: #1a1a2e;
          margin: 0 0 4px 0;
        }

        .dashboard .greeting p {
          color: #9ca3af;
          margin: 0;
          font-size: 14px;
        }

        /* ── Stat Cards ── */
        .card-container {
          display: flex;
          gap: 20px;
          margin-bottom: 36px;
          flex-wrap: wrap;
        }

        .stat-card {
          background: #ffffff;
          border-radius: 12px;
          padding: 24px 28px;
          min-width: 200px;
          box-shadow: 0 1px 4px rgba(0,0,0,0.08);
          display: flex;
          flex-direction: column;
          gap: 8px;
          border-left: 4px solid #bf0001;
        }

        .stat-card .stat-label {
          font-size: 13px;
          color: #6b7280;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .stat-card .stat-value {
          font-size: 38px;
          font-weight: 800;
          color: #bf0001;
          line-height: 1;
        }

        /* ── Section headings ── */
        .section-heading {
          font-size: 16px;
          font-weight: 700;
          color: #374151;
          text-transform: uppercase;
          letter-spacing: 0.6px;
          margin: 0 0 16px 0;
          padding-bottom: 8px;
          border-bottom: 2px solid #f3f4f6;
        }

        /* ── Tile Grid ── */
        .tiles {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
          gap: 16px;
          margin-bottom: 36px;
        }

        .tile-link {
          text-decoration: none;
          color: inherit;
        }

        .tile {
          background: #ffffff;
          border: 1px solid #e5e7eb;
          border-radius: 12px;
          padding: 24px 16px;
          text-align: center;
          transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
          box-shadow: 0 1px 3px rgba(0,0,0,0.06);
          height: 100%;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: flex-start;
        }

        .tile:hover {
          transform: translateY(-4px);
          box-shadow: 0 6px 16px rgba(191, 0, 1, 0.12);
          border-color: #bf0001;
        }

        .tile h3 {
          font-size: 15px;
          font-weight: 700;
          color: #1f2937;
          margin: 0 0 8px 0;
        }

        .tile p {
          font-size: 12.5px;
          color: #6b7280;
          line-height: 1.5;
          margin: 0;
        }

        .tile-icon {
          font-size: 28px;
          margin-bottom: 12px;
          color: #bf0001;
        }

        @media (max-width: 768px) {
          .dashboard { padding: 16px; }
          .tiles { grid-template-columns: repeat(2, 1fr); }
          .stat-card { min-width: 140px; }
        }
      `}</style>

      <main className="dashboard">
        {/* GREETING */}
        <div className="greeting">
          <h1>Welcome, {data.admin_name}</h1>
          <p>LifeConnect Admin Dashboard</p>
        </div>

        {error && (
          <div style={{ background: "#fee2e2", color: "#991b1b", padding: "12px 16px", borderRadius: "8px", marginBottom: "24px", fontSize: "14px" }}>
            {error}
          </div>
        )}

        {isLoading ? (
          <div style={{ padding: "40px", textAlign: "center", fontWeight: "bold", color: "#bf0001" }}>
            Loading dashboard metrics...
          </div>
        ) : (
          <>
            {/* STATS */}
            <div className="card-container">
              <div className="stat-card">
                <span className="stat-label">Total Active Donors</span>
                <span className="stat-value">{data.active_donors_count}</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Total Requests Received</span>
                <span className="stat-value">{data.total_requests}</span>
              </div>
            </div>

            {/* BLOOD REQUEST MANAGEMENT */}
            <h2 className="section-heading">Manage Blood Requests</h2>
            <div className="tiles">
              <a href="/admin/requests/new" className="tile-link">
                <div className="tile">
                  <i className="fa-solid fa-hand-holding-heart tile-icon"></i>
                  <h3>New Requests</h3>
                  <p>Manage all incoming blood requests.</p>
                </div>
              </a>
              <a href="/admin/requests/ongoing" className="tile-link">
                <div className="tile">
                  <i className="fa-solid fa-spinner tile-icon"></i>
                  <h3>Ongoing Requests</h3>
                  <p>Track ongoing blood donation requests.</p>
                </div>
              </a>
              <a href="/admin/requests/closed" className="tile-link">
                <div className="tile">
                  <i className="fa-solid fa-check-circle tile-icon"></i>
                  <h3>Closed Requests</h3>
                  <p>View completed requests.</p>
                </div>
              </a>
              <a href="/admin/requests/expired" className="tile-link">
                <div className="tile">
                  <i className="fa-solid fa-clock tile-icon"></i>
                  <h3>Expired Requests</h3>
                  <p>View expired blood requests.</p>
                </div>
              </a>
              <a href="/admin/requests/declined" className="tile-link">
                <div className="tile">
                  <i className="fa-solid fa-times-circle tile-icon"></i>
                  <h3>Declined Requests</h3>
                  <p>View declined blood requests.</p>
                </div>
              </a>
            </div>

            {/* MANAGE ACTIVITIES */}
            <h2 className="section-heading">Manage Activities</h2>
            <div className="tiles">
              <a href="/admin/analytics" className="tile-link">
                <div className="tile">
                  <i className="fa-solid fa-chart-pie tile-icon"></i>
                  <h3>Analytics</h3>
                  <p>View analytics for donors.</p>
                </div>
              </a>
              <a href="/admin/donors" className="tile-link">
                <div className="tile">
                  <i className="fa-solid fa-users tile-icon"></i>
                  <h3>Manage Donors</h3>
                  <p>Manage donor details.</p>
                </div>
              </a>
              <a href="/admin/hospitals/all" className="tile-link">
                <div className="tile">
                  <i className="fa-solid fa-hospital tile-icon"></i>
                  <h3>Manage Hospitals</h3>
                  <p>Manage hospital details.</p>
                </div>
              </a>
              <a href="/admin/generate-certificate" className="tile-link">
                <div className="tile">
                  <i className="fa-solid fa-award tile-icon"></i>
                  <h3>Generate Certificates</h3>
                  <p>Generate certificates for donors.</p>
                </div>
              </a>
              <a href="/admin/upload-csv" className="tile-link">
                <div className="tile">
                  <i className="fa-solid fa-file-csv tile-icon"></i>
                  <h3>Extract CSV Data</h3>
                  <p>Upload donor/hospital CSV data.</p>
                </div>
              </a>
            </div>
          </>
        )}
      </main>
    </AdminBase>
  );
}
