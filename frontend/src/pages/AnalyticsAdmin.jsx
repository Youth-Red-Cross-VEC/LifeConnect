import React from "react";
import AdminBase from "./AdminBase";

export default function AnalyticsAdmin({
    hospitalCount = 0,
    recentDonorCount = 0,
    recentRequestCount = 0,
}) {
    return (
        <AdminBase active="analytics">
            <style>{`
        .analytics-container {
          max-width: 1200px;
          margin: auto;
        }

        .analytics-container h1 {
          text-align: center;
          color: #333;
          margin-bottom: 30px;
          font-size: 2rem;
        }

        .summary-stats {
          display: flex;
          justify-content: space-around;
          margin-bottom: 40px;
          gap: 20px;
          flex-wrap: wrap;
        }

        .stat {
          background-color: #fff;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
          text-align: center;
          flex: 1;
          min-width: 200px;
        }

        .stat h3 {
          font-size: 18px;
          color: #bf0001;
          margin-bottom: 10px;
        }

        .stat p {
          font-size: 32px;
          color: #333;
          font-weight: bold;
          margin: 0;
        }

        .analytics-charts {
          display: flex;
          justify-content: space-between;
          margin-top: 40px;
          gap: 20px;
          flex-wrap: wrap;
        }

        .chart {
          flex: 1;
          min-width: 300px;
          text-align: center;
          background-color: #fff;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .chart h3 {
          color: #bf0001;
          margin-bottom: 15px;
          font-size: 1.2rem;
        }

        .chart img {
          width: 100%;
          height: auto;
          border-radius: 8px;
          box-sizing: border-box;
        }

        .chart-placeholder {
          width: 100%;
          height: 300px;
          background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%);
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #666;
          font-size: 14px;
        }

        @media (max-width: 768px) {
          .summary-stats {
            flex-direction: column;
          }

          .analytics-charts {
            flex-direction: column;
          }

          .chart {
            width: 100%;
          }
        }
      `}</style>

            <div className="analytics-container">
                <h1>Admin Analytics</h1>

                <div className="summary-stats">
                    <div className="stat">
                        <h3>Total Hospitals</h3>
                        <p>{hospitalCount}</p>
                    </div>
                    <div className="stat">
                        <h3>New Donors (Last 30 Days)</h3>
                        <p>{recentDonorCount}</p>
                    </div>
                    <div className="stat">
                        <h3>Blood Requests (Last 30 Days)</h3>
                        <p>{recentRequestCount}</p>
                    </div>
                </div>

                <div className="analytics-charts">
                    <div className="chart">
                        <h3>Donor Analytics by Blood Group</h3>
                        <div className="chart-placeholder">
                            Donor Analytics Chart
                            <br />
                            (Chart visualization will be rendered here)
                        </div>
                        {/* 
            <img
              src="/static/images/admin_analytics/donor_analytics_chart.png"
              alt="Donor Analytics Chart"
            />
            */}
                    </div>

                    <div className="chart">
                        <h3>Blood Request Status Distribution</h3>
                        <div className="chart-placeholder">
                            Blood Request Status Chart
                            <br />
                            (Chart visualization will be rendered here)
                        </div>
                        {/*
            <img
              src="/static/images/admin_analytics/blood_request_status.png"
              alt="Blood Request Status Chart"
            />
            */}
                    </div>

                    <div className="chart">
                        <h3>Response Status Distribution</h3>
                        <div className="chart-placeholder">
                            Response Status Chart
                            <br />
                            (Chart visualization will be rendered here)
                        </div>
                        {/*
            <img
              src="/static/images/admin_analytics/response_status_distribution.png"
              alt="Response Status Distribution Chart"
            />
            */}
                    </div>
                </div>
            </div>

            {/*
        ======================================================
        BACKEND CALL STRUCTURE — Admin Analytics
        ======================================================

        ENDPOINT
        --------
        GET /api/admin/analytics

        AUTH
        ----
        Admin session / JWT required

        RESPONSE (example)
        ------------------
        {
          hospital_count: number,
          recent_donor_count: number,
          recent_request_count: number,
          charts: {
            donor_analytics_chart: string (URL or base64),
            blood_request_status: string (URL or base64),
            response_status_distribution: string (URL or base64)
          }
        }

        FRONTEND RESPONSIBILITY
        -----------------------
        - Display summary statistics
        - Render chart images or integrate with chart library (e.g., Chart.js, Recharts)
        - Handle loading states

        ERROR CASES
        -----------
        - 401 → redirect to /admin/login
        - 403 → access denied
        - 500 → analytics error page
      */}
        </AdminBase>
    );
}
