import AdminBase from "./AdminBase";
import AsyncState from "../components/AsyncState";
import { useApiData } from "../hooks/useApiData";
import { api } from "../services/api";
import { unwrapData } from "../services/unwrap";

const loadAnalytics = async () => {
  const res = unwrapData(await api.getAdminAnalytics(), "Failed to load analytics data.");
  return {
    hospital_count: res.hospital_count || 0,
    recent_donor_count: res.recent_donor_count || 0,
    recent_request_count: res.recent_request_count || 0,
  };
};

const EMPTY_ANALYTICS = { hospital_count: 0, recent_donor_count: 0, recent_request_count: 0 };

export default function AnalyticsAdmin() {
  const { data, isLoading, error } = useApiData(loadAnalytics, {
    initial: EMPTY_ANALYTICS,
    errorMessage: "Error connecting to analytics API.",
  });

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
          font-weight: bold;
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
          font-weight: bold;
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
          font-weight: bold;
        }

        .chart img {
          width: 100%;
          max-width: 350px;
          height: auto;
          border-radius: 8px;
          box-sizing: border-box;
          margin: 0 auto;
          display: block;
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

        <AsyncState isLoading={isLoading} error={error} loadingText="Loading analytics data...">
          <>
            <div className="summary-stats">
              <div className="stat">
                <h3>Total Hospitals</h3>
                <p>{data.hospital_count}</p>
              </div>
              <div className="stat">
                <h3>New Donors (Last 30 Days)</h3>
                <p>{data.recent_donor_count}</p>
              </div>
              <div className="stat">
                <h3>Blood Requests (Last 30 Days)</h3>
                <p>{data.recent_request_count}</p>
              </div>
            </div>

            <div className="analytics-charts">
              <div className="chart">
                <h3>Donor Analytics by Blood Group</h3>
                <img
                  src="/images/admin_analytics/donor_analytics_chart.png"
                  alt="Donor Analytics Chart"
                />
              </div>

              <div className="chart">
                <h3>Blood Request Status Distribution</h3>
                <img
                  src="/images/admin_analytics/blood_request_status.png"
                  alt="Blood Request Status Chart"
                />
              </div>

              <div className="chart">
                <h3>Response Status Distribution</h3>
                <img
                  src="/images/admin_analytics/response_status_distribution.png"
                  alt="Response Status Distribution Chart"
                />
              </div>
            </div>
          </>
        </AsyncState>
      </div>
    </AdminBase>
  );
}
