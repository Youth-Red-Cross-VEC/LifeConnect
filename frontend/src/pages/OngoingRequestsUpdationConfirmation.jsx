import { useNavigate } from "react-router-dom";

const sampleDetails = [
  "REQ-001",
  "Completed",
  "All units donated successfully",
  2,
  "Issued",
  "DON-001, DON-002",
  "2025-12-28",
];

export default function OngoingRequestsUpdationConfirmation({
  details = sampleDetails,
  onBackToOngoingRequests,
  onBackToDashboard,
}) {
  const navigate = useNavigate();

  const [
    requestId,
    responseStatus,
    report,
    unitsDonated,
    certificateStatus,
    responseDonorIds,
    donationDate,
  ] = details;

  return (
    <>
      <style>{`
        .ongoing-confirm-page {
          font-family: "Poppins", sans-serif;
          background-color: #f4f4f4;
          color: #333;
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 100vh;
          margin: 0;
          padding: 20px;
        }

        .ongoing-confirm-card {
          background-color: white;
          border-radius: 10px;
          padding: 36px 32px;
          box-shadow: 0 2px 16px rgba(0, 0, 0, 0.12);
          max-width: 520px;
          width: 100%;
          text-align: center;
        }

        .ongoing-confirm-card h1 {
          color: #bf0001;
          font-size: 2rem;
          margin-bottom: 14px;
        }

        .ongoing-confirm-card > p {
          font-size: 1.1rem;
          margin-bottom: 24px;
          color: #555;
        }

        .confirm-details {
          text-align: left;
          font-size: 1rem;
          color: #333;
          margin-top: 20px;
          border-top: 2px solid #a30001;
          padding-top: 16px;
        }

        .confirm-details h3 {
          color: #bf0001;
          font-size: 1.2rem;
          margin-bottom: 12px;
        }

        .confirm-details p {
          margin: 10px 0;
          display: flex;
          justify-content: space-between;
          gap: 12px;
        }

        .detail-label {
          font-weight: bold;
          min-width: 160px;
          color: #222;
        }

        .detail-value {
          color: #444;
          flex: 1;
        }

        .confirm-actions {
          display: flex;
          gap: 12px;
          justify-content: center;
          flex-wrap: wrap;
          margin-top: 24px;
        }

        .confirm-btn {
          display: inline-block;
          background-color: #bf0001;
          color: white;
          padding: 11px 22px;
          border-radius: 6px;
          font-weight: bold;
          text-decoration: none;
          border: none;
          cursor: pointer;
          font-size: 14px;
          transition: background-color 0.3s;
        }

        .confirm-btn:hover { background-color: #a30001; }

        @media (max-width: 480px) {
          .ongoing-confirm-card { padding: 24px 16px; }
          .ongoing-confirm-card h1 { font-size: 1.5rem; }
          .confirm-details p { flex-direction: column; gap: 4px; }
        }
      `}</style>

      <div className="ongoing-confirm-page">
        <div className="ongoing-confirm-card">
          <h1>Request Updated Successfully!</h1>
          <p>
            Your ongoing request has been updated successfully. Thank you for your patience!
          </p>

          <div className="confirm-details">
            <h3>Request Details:</h3>
            <p>
              <span className="detail-label">Request ID:</span>
              <span className="detail-value">{requestId}</span>
            </p>
            <p>
              <span className="detail-label">Response Status:</span>
              <span className="detail-value">{responseStatus}</span>
            </p>
            <p>
              <span className="detail-label">Report:</span>
              <span className="detail-value">{report}</span>
            </p>
            <p>
              <span className="detail-label">Units Donated:</span>
              <span className="detail-value">{unitsDonated}</span>
            </p>
            <p>
              <span className="detail-label">Certificate Status:</span>
              <span className="detail-value">{certificateStatus}</span>
            </p>
            <p>
              <span className="detail-label">Donation Date:</span>
              <span className="detail-value">{donationDate}</span>
            </p>
            <p>
              <span className="detail-label">Response Donor IDs:</span>
              <span className="detail-value">{responseDonorIds}</span>
            </p>
          </div>

          <div className="confirm-actions">
            <button
              className="confirm-btn"
              onClick={() =>
                onBackToOngoingRequests
                  ? onBackToOngoingRequests()
                  : navigate("/admin/requests/ongoing")
              }
            >
              Back to Ongoing Requests
            </button>
            <button
              className="confirm-btn"
              onClick={() =>
                onBackToDashboard
                  ? onBackToDashboard()
                  : navigate("/admin/dashboard")
              }
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
