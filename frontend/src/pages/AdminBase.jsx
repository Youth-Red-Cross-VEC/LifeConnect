import React, { useState } from "react";

export default function AdminBase({ children, active = "" }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);
  const closeSidebar = () => setSidebarOpen(false);

  return (
    <>
      {/* Inline Admin Dashboard CSS */}
      <style>{`
        /* General Reset */
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        body {
          font-family: Arial, sans-serif;
          background-color: #f4f6f8;
        }

        .dashboard-container {
          display: flex;
          height: calc(100vh - 60px);
        }

        /* Header */
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          background-color: #ffffff;
          padding: 10px 20px;
          border-bottom: 1px solid #e0e0e0;
          height: 60px;
        }

        .header-logo {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .logo-img {
          height: 45px;
        }

        .header h2 {
          font-size: 18px;
          font-weight: bolder;
          color: #bf0001;
        }

        .header-actions {
          display: flex;
          gap: 10px;
        }

        .help-btn,
        .logout-btn {
          text-decoration: none;
          padding: 8px 16px;
          border-radius: 4px;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.3s;
        }

        .help-btn {
          background-color: #f4f4f4;
          color: #555;
        }

        .logout-btn {
          background-color: #bf0001;
          color: white;
        }

        .help-btn:hover {
          background-color: #e0e0e0;
        }

        .logout-btn:hover {
          background-color: #c82f3d;
        }

        /* Sidebar */
        .sidebar {
          width: 260px;
          background-color: #ffffff;
          padding: 20px;
        }

        .sidebar nav ul {
          list-style: none;
        }

        .sidebar nav ul li {
          margin-bottom: 15px;
        }

        .sidebar nav ul li a {
          text-decoration: none;
          color: #333;
          font-size: 16px;
          font-weight: 500;
          display: block;
          padding: 10px 15px;
          border-radius: 8px;
          transition: 0.3s;
        }

        .sidebar nav ul li a.active {
          background-color: #bf0001;
          color: #ffffff;
        }

        .sidebar nav ul li a:hover {
          background-color: #f4f6f9;
        }

        .sidebar nav h4 {
          font-size: 15px;
          color: #b2b0b0;
          text-transform: uppercase;
          margin-bottom: 10px;
        }

        .separator {
          height: 2.5px;
          background-color: #f3f3f3;
          margin: 20px 0;
          border-radius: 5px;
        }

        /* Sidebar Toggle */
        .sidebar-toggle-btn {
          background: none;
          border: none;
          font-size: 20px;
          cursor: pointer;
          display: none;
        }

        /* Overlay */
        .sidebar-overlay {
          display: none;
        }

        @media (max-width: 768px) {
          .sidebar-toggle-btn {
            display: block;
          }

          .sidebar {
            position: fixed;
            left: -260px;
            top: 0;
            height: 100%;
            z-index: 1000;
            transition: left 0.3s ease;
          }

          .sidebar.visible {
            left: 0;
          }

          .sidebar-overlay {
            display: block;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.5);
            z-index: 999;
          }
        }
      `}</style>

      {/* Header */}
      <header className="header">
        <div className="header-logo">
          <button className="sidebar-toggle-btn" onClick={toggleSidebar}>
            <i className="fa-solid fa-bars"></i>
          </button>

          <a href="/">
            <img
              src="public/images/admin_dashboard/logo.png"
              alt="Logo"
              className="logo-img"
            />
          </a>

          <h2>Life Connect</h2>
        </div>

        <div className="header-actions">
          <a className="help-btn" href="/admin/queries">
            <i className="fa-solid fa-comments"></i> Queries
          </a>
          <a className="help-btn" href="/help">
            <i className="fa-solid fa-circle-question"></i> Help
          </a>
          <a className="logout-btn" href="/admin/logout">
            <i className="fa-solid fa-right-from-bracket"></i> Logout
          </a>
        </div>
      </header>

      <div className="dashboard-container">
        {/* Sidebar */}
        <aside className={`sidebar ${sidebarOpen ? "visible" : ""}`}>
          <nav>
            <h4>Manage Requests</h4>
            <ul>
              <li>
                <a href="/admin/dashboard" className={active === "dashboard" ? "active" : ""}>
                  <i className="fa-solid fa-chart-line"></i> Dashboard
                </a>
              </li>
              <li><a href="/admin/requests/new">New Requests</a></li>
              <li><a href="/admin/requests/ongoing">Ongoing Requests</a></li>
              <li><a href="/admin/requests/closed">Closed Requests</a></li>
              <li><a href="/admin/requests/expired">Expired Requests</a></li>
              <li><a href="/admin/requests/declined">Declined Requests</a></li>
            </ul>

            <div className="separator"></div>

            <h4>Admin Corner</h4>
            <ul>
              <li><a href="/admin/analytics">Analytics</a></li>
              <li><a href="/admin/profile">Admin Profile</a></li>
            </ul>
          </nav>
        </aside>

        {/* Overlay */}
        {sidebarOpen && <div className="sidebar-overlay" onClick={closeSidebar} />}

        {/* Main Content */}
        <main style={{ flex: 1, padding: "20px" }}>
          {children}
        </main>
      </div>

      {/*
        ================= BACKEND INTERACTION NOTES =================

        AUTHENTICATION
        - All routes assume admin session / JWT validation
        - Unauthorized users should be redirected to /admin/login

        HEADER LINKS
        - GET  /admin/queries        → Admin queries page
        - GET  /help                 → Help documentation
        - GET  /admin/logout         → Clears session / token

        SIDEBAR ROUTES
        - GET /admin/dashboard
        - GET /admin/requests/new
        - GET /admin/requests/ongoing
        - GET /admin/requests/closed
        - GET /admin/requests/expired
        - GET /admin/requests/declined
        - GET /admin/analytics
        - GET /admin/profile

        RESPONSE FORMAT (expected)
        - HTML/React page render OR JSON (if API-based)
        - 401 → redirect to login
        - 403 → show access denied page
      */}
    </>
  );
}
