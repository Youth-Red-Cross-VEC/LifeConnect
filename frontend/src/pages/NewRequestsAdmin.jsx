import { useState, useEffect } from "react";
import AdminBase from "./AdminBase";
import { api, getUserId, getUsername } from "../services/api";

export default function NewRequestsAdmin() {
    const [requests, setRequests] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState("");
    const [openId, setOpenId] = useState(null);
    const [actionMsg, setActionMsg] = useState("");

    useEffect(() => {
        const fetchPending = async () => {
            try {
                const res = await api.getPendingRequests();
                if (Array.isArray(res)) {
                    setRequests(res);
                } else {
                    setError(res?.detail || "Failed to load requests.");
                }
            } catch {
                setError("Server error. Could not load pending requests.");
            } finally {
                setIsLoading(false);
            }
        };
        fetchPending();
    }, []);

    const toggleDetails = (id) =>
        setOpenId((prev) => (prev === id ? null : id));

    const handleApprove = async (requestId) => {
        setActionMsg("");
        try {
            const res = await api.approveRequest(requestId);
            if (res && (res.message || !res.detail)) {
                setActionMsg(`✅ Request ${requestId} approved. Donors notified.`);
                setRequests((prev) => prev.filter((r) => r.request_id !== requestId));
            } else {
                setActionMsg(`❌ ${res?.detail || "Failed to approve request."}`);
            }
        } catch {
            setActionMsg("❌ Server error during approval.");
        }
    };

    const handleDecline = async (requestId) => {
        setActionMsg("");
        try {
            const res = await api.declineRequest(requestId);
            if (res && (res.message || !res.detail)) {
                setActionMsg(`Request ${requestId} declined.`);
                setRequests((prev) => prev.filter((r) => r.request_id !== requestId));
            } else {
                setActionMsg(`❌ ${res?.detail || "Failed to decline request."}`);
            }
        } catch {
            setActionMsg("❌ Server error during decline.");
        }
    };

    return (
        <AdminBase active="new-requests">
            <style>{`
        .new-requests-main {
          padding: 20px;
        }

        .new-requests-main h1 {
          text-align: center;
          color: #c82333;
          margin-bottom: 20px;
          font-size: 2.2rem;
        }

        .new-requests-table {
          width: 100%;
          border-collapse: collapse;
          background-color: #fff;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .new-requests-table thead { background-color: #c82333; color: #fff; }

        .new-requests-table th,
        .new-requests-table td {
          padding: 12px 15px;
          text-align: left;
          font-size: 14px;
        }

        .new-requests-table tbody tr:nth-child(even) { background-color: #f2f2f2; }
        .new-requests-table tbody tr:hover { background-color: #fde8ea; }

        .new-requests-table th {
          font-weight: bold;
          text-transform: uppercase;
        }

        .view-btn, .approve-btn {
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

        .view-btn:hover, .approve-btn:hover { background-color: #a71d2a; }

        .send-btn {
          padding: 6px 12px;
          background-color: #28a745;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          margin-right: 4px;
          font-size: 13px;
          transition: background-color 0.3s ease;
        }

        .send-btn:hover { background-color: #218838; }

        .decline-btn {
          cursor: pointer;
          padding: 6px 12px;
          background-color: #dc3545;
          color: white;
          border: none;
          border-radius: 4px;
          font-size: 13px;
          transition: background-color 0.3s ease;
        }

        .decline-btn:hover { background-color: #c82333; }

        .details-row { display: none; }
        .details-row.open { display: table-row; }

        .details-inner-table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
        .details-inner-table td { padding: 6px 8px; border: 1px solid #eee; font-size: 14px; }

        .action-buttons { margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap; }
      `}</style>

            <main className="new-requests-main">
                <h1>New Blood Requests</h1>
                {actionMsg && (
                    <p style={{ textAlign: "center", color: actionMsg.startsWith("❌") ? "#c82333" : "#28a745", marginBottom: "12px" }}>
                        {actionMsg}
                    </p>
                )}
                {isLoading ? (
                    <p style={{ textAlign: "center", padding: "40px" }}>Loading requests...</p>
                ) : error ? (
                    <p style={{ textAlign: "center", color: "#c82333", padding: "40px" }}>{error}</p>
                ) : requests.length === 0 ? (
                    <p style={{ textAlign: "center", padding: "40px" }}>No pending requests.</p>
                ) : (
                <table className="new-requests-table">
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
                            const rid = request.request_id || request.id;
                            const isOpen = openId === rid;
                            return (
                                <FragmentRow key={rid}>
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
                                                onClick={() => toggleDetails(rid)}
                                            >
                                                View Request
                                            </button>
                                        </td>
                                    </tr>

                                    <tr className={`details-row ${isOpen ? "open" : ""}`} id={`details${rid}`}>
                                        <td colSpan={6}>
                                            <table className="details-inner-table">
                                                <tbody>
                                                    {[
                                                        ["Request ID", rid],
                                                        ["Patient Name", request.patient_name],
                                                        ["Patient Age", request.patient_age],
                                                        ["Blood Group", request.blood_group],
                                                        ["Units Required", request.units_required],
                                                        ["Hospital Name", request.hospital_name],
                                                        ["Hospital Address", request.hospital_address],

                                                        ["Hospital ID", request.hospital_id],
                                                        ["Status", request.status],
                                                        ["Due Date", request.due_date],
                                                        ["Contact Number", request.contact_number],
                                                        ["Attendant Name", request.attendant_name],
                                                        ["Request Reason", request.request_reason],
                                                        ["Available Active Donors", request.active_donor_count],
                                                    ].map(([label, value]) => (
                                                        <tr key={label}>
                                                            <td><strong>{label}:</strong></td>
                                                            <td>{value}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>

                                            <div className="action-buttons">
                                                <button
                                                    className="approve-btn"
                                                    type="button"
                                                    onClick={() => handleApprove(rid)}
                                                >
                                                    Approve &amp; Notify Donors
                                                </button>
                                                <button
                                                    className="decline-btn"
                                                    type="button"
                                                    onClick={() => handleDecline(rid)}
                                                >
                                                    Decline Request
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                </FragmentRow>
                            );
                        })}
                    </tbody>
                </table>
                )}
            </main>

            {/*
        ======================================================
        BACKEND CALL STRUCTURE — New Requests Admin
        ======================================================

        ENDPOINTS
        ---------
        GET  /admin/requests/new           → list new/pending requests
        POST /SendEmailToDonors            → approve and send emails to donors
        POST /decline_request              → decline a blood request

        AUTH
        ----
        Admin session / JWT required

        REQUEST (POST /SendEmailToDonors)
        ---------------------------------
        {
          request_id, blood_group, patient_name,
          hospital_name, hospital_address, contact_number,
          due_date, attendant_name, units_required,
          request_reason, patient_age
        }

        REQUEST (POST /decline_request)
        --------------------------------
        { request_id: string }

        FRONTEND RESPONSIBILITY
        -----------------------
        - Toggle details row per request
        - Two-step approval: first "Approve Request" reveals "Send Requests" button
        - "Decline Request" calls decline endpoint directly

        ERROR CASES
        -----------
        - 401 → redirect to /admin/login
        - 400 → bad request
        - 500 → server error
      */}
        </AdminBase>
    );
}

function FragmentRow({ children }) {
    return <>{children}</>;
}
