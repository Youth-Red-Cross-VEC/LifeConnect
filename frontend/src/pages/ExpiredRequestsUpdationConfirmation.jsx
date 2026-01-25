import { useEffect, useMemo } from "react";

export default function ExpiredRequestsUpdationConfirmation({
  details = ["-", "-", "-", "-", "-", "-", "-"],
  onBackToExpiredRequests,
  onBackToDashboard,
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.log("ExpiredRequestsUpdationConfirmation details:", details);
  }, [details]);

  return (
    <div className="center">
      <div className="card narrow" style={{ textAlign: "center" }}>
        <h1 className="title" style={{ textAlign: "center", fontSize: "2em" }}>
          Request Successfully Updated!
        </h1>
        <p>
          The expired request has been successfully updated. Below are the details of the request:
        </p>

        <div className="details" style={{ textAlign: "left" }}>
          <p>
            <strong>Request ID:</strong> {details[0]}
          </p>
          <p>
            <strong>Response Status:</strong> {details[1]}
          </p>
          <p>
            <strong>Report:</strong> {details[2]}
          </p>
          <p>
            <strong>Units Donated:</strong> {details[3]}
          </p>
          <p>
            <strong>Certificate Status:</strong> {details[4]}
          </p>
          <p>
            <strong>Donation Date:</strong> {details[6]}
          </p>
          <p>
            <strong>Response Donor IDs:</strong> {details[5]}
          </p>
        </div>

        <div className="actions" style={{ justifyContent: "center" }}>
          {onBackToExpiredRequests ? (
            <button type="button" className="primary" onClick={onBackToExpiredRequests}>
              Back to Expired Requests
            </button>
          ) : (
            <a href="#" className="primary" style={{ textDecoration: "none" }}>
              Back to Expired Requests
            </a>
          )}

          {onBackToDashboard ? (
            <button type="button" className="primary" onClick={onBackToDashboard}>
              Back to Dashboard
            </button>
          ) : (
            <a href="#" className="primary" style={{ textDecoration: "none" }}>
              Back to Dashboard
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

