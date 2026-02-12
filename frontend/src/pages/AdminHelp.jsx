import React from "react";

export default function AdminHelp() {
    return (
        <>
            <style>{`
        .help-page {
          font-family: Arial, sans-serif;
          background-color: #f9f9f9;
          margin: 0;
          padding: 0;
        }

        .help-header {
          background-color: #bf0001;
          color: white;
          padding: 10px 20px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .help-header .sitename {
          font-size: 20px;
          font-weight: bold;
        }

        .help-header .back-to-dashboard {
          text-decoration: none;
          background-color: white;
          color: #bf0001;
          padding: 5px 15px;
          border-radius: 5px;
          font-weight: bold;
        }

        .help-header .back-to-dashboard:hover {
          background-color: #f0f0f0;
        }

        .help-page h1 {
          text-align: center;
          margin-top: 20px;
          color: #333;
        }

        .help-section {
          margin: 20px;
          padding: 20px;
          background-color: white;
          border-radius: 10px;
          box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }

        .help-section h2 {
          color: #bf0001;
          margin-bottom: 10px;
        }

        .help-section h3 {
          color: #333;
          margin-top: 15px;
          margin-bottom: 8px;
        }

        .help-section p {
          margin: 10px 0;
          line-height: 1.6;
        }

        .help-section ul {
          margin-left: 20px;
        }

        .help-section li {
          margin: 8px 0;
          line-height: 1.6;
        }

        .image-placeholder {
          margin: 10px 0;
          padding: 20px;
          background-color: #ececec;
          text-align: center;
          border: 1px dashed gray;
          color: gray;
          border-radius: 5px;
        }

        .faq-list {
          margin-left: 20px;
        }

        .contact-info {
          margin-top: 20px;
        }

        .contact-info p {
          margin: 5px 0;
        }
      `}</style>

            <div className="help-page">
                <header className="help-header">
                    <div className="sitename">LifeConnect</div>
                    <a href="/admin/dashboard" className="back-to-dashboard">
                        Back to Dashboard
                    </a>
                </header>

                <h1>LifeConnect Guide/Help Book</h1>

                <section className="help-section">
                    <h2>LifeConnect Work Section</h2>
                    <p>The user can:</p>
                    <ul>
                        <li>
                            Request for blood and add an image field for uploading relevant images.
                        </li>
                        <div className="image-placeholder">Image Placeholder for Blood Request</div>

                        <li>Find donors by mentioning hospitals for locating nearby donors.</li>
                        <div className="image-placeholder">Image Placeholder for Finding Donors</div>

                        <li>Join as a donor to contribute to the community.</li>
                        <div className="image-placeholder">Image Placeholder for Joining as Donor</div>

                        <li>View available blood banks for donations or requests.</li>
                        <div className="image-placeholder">Image Placeholder for Viewing Blood Banks</div>
                    </ul>
                </section>

                <section className="help-section">
                    <h2>Admin Operations</h2>
                    <p>The admin needs to log in, creating a session valid for one day.</p>
                    <div className="image-placeholder">Image Placeholder for Admin Login</div>

                    <p>Once logged in, the admin can access the dashboard:</p>
                    <div className="image-placeholder">Image Placeholder for Dashboard Overview</div>

                    <h3>Dashboard Features:</h3>
                    <ul>
                        <li>
                            Manage Blood Requests:
                            <ul>
                                <li>
                                    New Requests: Approve or decline after verifying with the attendant. Check donor
                                    availability.
                                </li>
                                <li>Ongoing Requests: Admin manually closes them after completion.</li>
                                <li>Closed Requests: Contains finalized requests.</li>
                                <li>Expired Requests: Clone requests with existing details.</li>
                                <li>Declined Requests: Contains declined requests.</li>
                            </ul>
                        </li>
                        <div className="image-placeholder">Image Placeholder for Blood Request Management</div>

                        <li>Manage Donors and Hospitals for seamless operations.</li>
                        <div className="image-placeholder">
                            Image Placeholder for Managing Donors and Hospitals
                        </div>

                        <li>Generate Certificates for donors acknowledging their contributions.</li>
                        <div className="image-placeholder">Image Placeholder for Generating Certificates</div>

                        <li>Extract CSV Data to retrieve and manage donor or hospital data efficiently.</li>
                        <div className="image-placeholder">Image Placeholder for CSV Data Management</div>

                        <li>View Admin Analytics for insights into system performance.</li>
                        <div className="image-placeholder">Image Placeholder for Admin Analytics</div>

                        <li>Manage Admin Profile for personal settings and updates.</li>
                        <div className="image-placeholder">Image Placeholder for Admin Profile Management</div>
                    </ul>
                </section>

                <section className="help-section">
                    <h2>Frequently Asked Questions (FAQ)</h2>
                    <ul className="faq-list">
                        <li>How do I request blood?</li>
                        <li>How can I find a donor near my location?</li>
                        <li>What is the process to join as a donor?</li>
                        <li>How can I view blood bank details?</li>
                        <li>What steps should I take to approve a blood request?</li>
                        <li>How do I generate certificates for donors?</li>
                        <li>Can I extract data from the system?</li>
                        <li>How to handle expired requests?</li>
                        <li>What analytics are available in the admin dashboard?</li>
                        <li>How can I update my admin profile?</li>
                    </ul>
                </section>

                <section className="help-section">
                    <h2>Help & Support</h2>
                    <div className="contact-info">
                        <p>Developer 1: +1234567890, dev1@example.com</p>
                        <p>Developer 2: +0987654321, dev2@example.com</p>
                        <p>Developer 3: +1122334455, dev3@example.com</p>
                    </div>
                </section>
            </div>
        </>
    );
}
