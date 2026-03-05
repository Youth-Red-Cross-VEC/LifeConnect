import { useState } from "react";
import AdminBase from "./AdminBase";

export default function ClosedRequestsAdmin({ requests = [] }) {
    const [openId, setOpenId] = useState(null);

    const toggleDetails = (id) =>
        setOpenId((prev) => (prev === id ? null : id));

    return (
        <AdminBase active="closed-requests">
            <style>{`
        .closed-requests-main {
          padding: 20px;
        }

        .closed-requests-main h1 {
          text-align: center;
          color: #c82333;
          margin-bottom: 20px;
          font-size: 2.2rem;
        }

        .closed-requests-table {
          width: 100%;
          border-collapse: collapse;
          background-color: #fff;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .closed-requests-table thead { background-color: #c82333; color: #fff; }

        .closed-requests-table th,
        .closed-requests-table td {
          padding: 12px 15px;
          text-align: left;
          font-size: 14px;
        }

        .closed-requests-table tbody tr:nth-child(even) { background-color: #f2f2f2; }
        .closed-requests-table tbody tr:hover { background-color: #fde8ea; }

        .closed-requests-table th {
          font-weight: bold;
          text-transform: uppercase;
        }

        .view-btn {
          cursor: pointer;
          padding: 6px 12px;
          background-color: #c82333;
          color: white;
          border: none;
          border-radius: 4px;
          font-size: 13px;
          transition: background-color 0.3s ease;
        }

        .view-btn:hover { background-color: #a71d2a; }

        .details-row { display: none; }
        .details-row.open { display: table-row; }

        .details-inner-table { width: 100%; border-collapse: collapse; }
        .details-inner-table td { padding: 6px 8px; border: 1px solid #eee; font-size: 14px; }
      `}</style>

            <main className="closed-requests-main">
                <h1>Closed Blood Requests</h1>
                <table className="closed-requests-table">
                    <thead>
                        <tr>
                            <th>Patient Name</th>
                            <th>Blood Group</th>
                            <th>Hospital Name</th>
                            <th>Contact Number</th>
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {requests.map((request) => {
                            const isOpen = openId === request.id;
                            return (
                                <FragmentRow key={request.id}>
                                    <tr>
                                        <td>{request.patient_name}</td>
                                        <td>{request.blood_group}</td>
                                        <td>{request.hospital_name}</td>
                                        <td>{request.contact_number}</td>
                                        <td>{request.status}</td>
                                        <td>
                                            <button
                                                className="view-btn"
                                                type="button"
                                                onClick={() => toggleDetails(request.id)}
                                            >
                                                View Details
                                            </button>
                                        </td>
                                    </tr>
                                    <tr className={`details-row ${isOpen ? "open" : ""}`} id={`details${request.id}`}>
                                        <td colSpan={6}>
                                            <table className="details-inner-table">
                                                <tbody>
                                                    {[
                                                        ["Request ID", request.id],
                                                        ["Patient Name", request.patient_name],
                                                        ["Patient Age", request.patient_age],
                                                        ["Blood Group", request.blood_group],
                                                        ["Contact Number", request.contact_number],
                                                        ["Attendant Name", request.attendant_name],
                                                        ["Units Required", request.units_required],
                                                        ["Request Reason", request.request_reason],
                                                        ["Due Date", request.due_date],
                                                        ["Approved AdminID", request.approved_admin_id],
                                                        ["Closed AdminID", request.closed_admin_id],
                                                        ["Hospital ID", request.hospital_id],
                                                        ["Hospital Name", request.hospital_name],
                                                        ["Hospital Address", request.hospital_address],
                                                        ["Response ID", request.response_id],
                                                        ["Response Status", request.response_status],
                                                        ["Response Report", request.report],
                                                        ["Units Donated", request.units_donated],
                                                        ["Certificate Status", request.certificate_status],
                                                        ["Donation Date", request.donation_date],
                                                        ["Responded Donors ID", request.response_donor_ids],
                                                    ].map(([label, value]) => (
                                                        <tr key={label}>
                                                            <td><strong>{label}:</strong></td>
                                                            <td>{value}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </td>
                                    </tr>
                                </FragmentRow>
                            );
                        })}
                    </tbody>
                </table>
            </main>

            {/*
        ======================================================
        BACKEND CALL STRUCTURE — Closed Requests Admin
        ======================================================

        ENDPOINT
        --------
        GET /admin/requests/closed

        AUTH
        ----
        Admin session / JWT required

        RESPONSE (example)
        ------------------
        {
          requests: [
            {
              id, patient_name, patient_age, blood_group,
              contact_number, attendant_name, units_required,
              request_reason, due_date, status,
              approved_admin_id, closed_admin_id,
              hospital_id, hospital_name, hospital_address,
              response_id, response_status, report,
              units_donated, certificate_status,
              donation_date, response_donor_ids
            }
          ]
        }

        FRONTEND RESPONSIBILITY
        -----------------------
        - Display requests in a table
        - Toggle expandable detail rows on "View Details"
        - Read-only view (no actions)

        ERROR CASES
        -----------
        - 401 → redirect to /admin/login
        - 500 → server error
      */}
        </AdminBase>
    );
}

function FragmentRow({ children }) {
    return <>{children}</>;
}
