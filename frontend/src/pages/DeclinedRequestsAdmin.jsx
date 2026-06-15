import { useState } from "react";
import AdminBase from "./AdminBase";

const sampleRequests = [
  {
    id: "REQ-001",
    patient_name: "John Doe",
    blood_group: "A+",
    hospital_name: "Apollo Hospital",
    contact_number: "+91 90000 11111",
    status: "Declined",
    patient_age: 45,
    attendant_name: "Jane Doe",
    units_required: 2,
    request_reason: "Surgery",
    due_date: "2025-12-30",
    hospital_id: "HOSP-01",
    approved_admin_id: "ADMIN-01",
    hospital_address: "21 Greams Lane, Chennai",
    response_id: "RESP-001",
    response_status: "Declined",
    report: "Insufficient donor availability",
    units_donated: 0,
    certificate_status: "Not Issued",
    response_donor_ids: "N/A",
  },
];

export default function DeclinedRequestsAdmin({ requests = sampleRequests }) {
  const [expandedId, setExpandedId] = useState(null);

  const toggleDetails = (id) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <AdminBase active="declined-requests">
      <style>{`
        .declined-requests-main {
          padding: 20px;
        }

        .declined-requests-main h1 {
          text-align: center;
          color: #c82333;
          margin-bottom: 20px;
          font-size: 2.2rem;
        }

        .declined-requests-table {
          width: 100%;
          border-collapse: collapse;
          background-color: #fff;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .declined-requests-table thead { background-color: #c82333; color: #fff; }

        .declined-requests-table th,
        .declined-requests-table td {
          padding: 12px 15px;
          text-align: left;
          font-size: 14px;
        }

        .declined-requests-table tbody tr:nth-child(even) { background-color: #f2f2f2; }
        .declined-requests-table tbody tr:hover { background-color: #fde8ea; }

        .declined-requests-table th {
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
          margin-right: 4px;
          font-size: 13px;
          transition: background-color 0.3s ease;
        }

        .view-btn:hover { background-color: #a71d2a; }

        .details-inner-table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
        .details-inner-table td { padding: 6px 8px; border: 1px solid #eee; font-size: 14px; }

        .status-badge {
          display: inline-block;
          padding: 3px 10px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 600;
          background: #f8d7da;
          color: #721c24;
        }
      `}</style>

      <div className="declined-requests-main">
        <h1>Declined Blood Requests</h1>

        {requests.length === 0 ? (
          <div style={{ textAlign: "center", color: "#888", padding: "40px", fontSize: "1.1rem" }}>
            No declined requests found.
          </div>
        ) : (
          <table className="declined-requests-table">
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
              {requests.map((req) => (
                <>
                  <tr key={req.id}>
                    <td>{req.patient_name}</td>
                    <td>{req.blood_group}</td>
                    <td>{req.hospital_name}</td>
                    <td>{req.contact_number}</td>
                    <td>
                      <span className="status-badge">{req.status}</span>
                    </td>
                    <td>
                      <button
                        className="view-btn"
                        onClick={() => toggleDetails(req.id)}
                      >
                        {expandedId === req.id ? "Hide Details" : "View Details"}
                      </button>
                    </td>
                  </tr>

                  {expandedId === req.id && (
                    <tr key={`details-${req.id}`} className="details-row">
                      <td colSpan={6}>
                        <table className="details-inner-table">
                          <tbody>
                            <tr><td>Request ID</td><td>{req.id}</td></tr>
                            <tr><td>Patient Name</td><td>{req.patient_name}</td></tr>
                            <tr><td>Patient Age</td><td>{req.patient_age}</td></tr>
                            <tr><td>Blood Group</td><td>{req.blood_group}</td></tr>
                            <tr><td>Contact Number</td><td>{req.contact_number}</td></tr>
                            <tr><td>Attendant Name</td><td>{req.attendant_name}</td></tr>
                            <tr><td>Units Required</td><td>{req.units_required}</td></tr>
                            <tr><td>Request Reason</td><td>{req.request_reason}</td></tr>
                            <tr><td>Due Date</td><td>{req.due_date}</td></tr>
                            <tr><td>Hospital ID</td><td>{req.hospital_id}</td></tr>
                            <tr><td>Declined Admin ID</td><td>{req.approved_admin_id}</td></tr>
                            <tr><td>Hospital Name</td><td>{req.hospital_name}</td></tr>
                            <tr><td>Hospital Address</td><td>{req.hospital_address}</td></tr>
                            <tr><td>Response ID</td><td>{req.response_id}</td></tr>
                            <tr><td>Response Status</td><td>{req.response_status}</td></tr>
                            <tr><td>Response Report</td><td>{req.report}</td></tr>
                            <tr><td>Units Donated</td><td>{req.units_donated}</td></tr>
                            <tr><td>Certificate Status</td><td>{req.certificate_status}</td></tr>
                            <tr><td>Responded Donor IDs</td><td>{req.response_donor_ids}</td></tr>
                          </tbody>
                        </table>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </AdminBase>
  );
}
