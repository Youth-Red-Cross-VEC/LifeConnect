export default function RequestApprovalConfirmation() {
  return (
    <>
      <style>{`
        .approval-page {
          font-family: "Poppins", sans-serif;
          background-color: #f4f4f4;
          color: #333;
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100vh;
          margin: 0;
          text-align: center;
        }

        .approval-container {
          background-color: white;
          border-radius: 8px;
          padding: 30px;
          box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
          max-width: 600px;
          width: 100%;
          text-align: center;
        }

        .approval-container h2 {
          color: #bf0001;
          font-size: 2.2rem;
          margin-bottom: 20px;
        }

        .approval-container p {
          font-size: 1.2em;
          margin-bottom: 20px;
          color: #555;
        }

        .approval-container a {
          display: inline-block;
          background-color: #bf0001;
          color: white;
          padding: 12px 20px;
          border-radius: 5px;
          font-weight: bold;
          text-decoration: none;
          margin-top: 10px;
          transition: background-color 0.3s ease;
          font-size: 1.1em;
        }

        .approval-container a:hover { background-color: #a30001; }

        .button-container { margin-top: 20px; display: flex; flex-direction: column; gap: 10px; align-items: center; }
      `}</style>

      <div className="approval-page">
        <div className="approval-container">
          <h2>Success</h2>
          <p>Email has been successfully sent to the available donors.</p>
          <div className="button-container">
            <a href="/admin/requests/new">Back to New Requests</a>
            <a href="/admin/dashboard">Back to Dashboard</a>
          </div>
        </div>
      </div>

      {/*
        ======================================================
        BACKEND CALL STRUCTURE — Request Approval Confirmation
        ======================================================

        NOTES
        -----
        This is a static confirmation page shown after emails
        are successfully sent to donors from NewRequestsAdmin.

        TRIGGERED BY
        ------------
        Successful POST to /SendEmailToDonors

        NAVIGATION
        ----------
        - Back to New Requests → /admin/requests/new
        - Back to Dashboard    → /admin/dashboard

        FRONTEND RESPONSIBILITY
        -----------------------
        - Display a success confirmation message
        - Provide navigation links back

        NO BACKEND CALL NEEDED FOR THIS PAGE
      */}
    </>
  );
}
