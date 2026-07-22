import { useState, useMemo } from "react";
import AdminBase from "./AdminBase";

export default function OngoingRequestsAdmin({
    requests = [],
    onCloseRequest,
    onCloseRequestAndSendCertificate,
}) {
    const [openId, setOpenId] = useState(null);
    const [forms, setForms] = useState(() => new Map());

    const defaultForm = useMemo(
        () => ({
            response_status: "",
            report: "None",
            units_donated: 0,
            certificate_status: "NOTSENT",
            donation_date: "",
            response_donor_ids: "None",
        }),
        [],
    );

    const getForm = (id) => forms.get(id) ?? defaultForm;

    const setFormField = (id, key, value) => {
        setForms((prev) => {
            const copy = new Map(prev);
            const current = copy.get(id) ?? defaultForm;
            copy.set(id, { ...current, [key]: value });
            return copy;
        });
    };

    const toggleDetails = (id) =>
        setOpenId((prev) => (prev === id ? null : id));

    const handleSubmit = (e, requestId, variant) => {
        e.preventDefault();
        const payload = { request_id: requestId, ...getForm(requestId) };
        if (variant === "close_and_send") onCloseRequestAndSendCertificate?.(payload);
        else onCloseRequest?.(payload);
    };

    return (
        <AdminBase active="ongoing-requests">
            <style>{`
        .ongoing-requests-main {
          padding: 20px;
        }

        .ongoing-requests-main h1 {
          text-align: center;
          color: #c82333;
          margin-bottom: 20px;
          font-size: 2.2rem;
        }

        .ongoing-requests-table {
          width: 100%;
          border-collapse: collapse;
          background-color: #fff;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .ongoing-requests-table thead { background-color: #c82333; color: #fff; }

        .ongoing-requests-table th,
        .ongoing-requests-table td {
          padding: 12px 15px;
          text-align: left;
          font-size: 14px;
        }

        .ongoing-requests-table tbody tr:nth-child(even) { background-color: #f2f2f2; }
        .ongoing-requests-table tbody tr:hover { background-color: #fde8ea; }

        .ongoing-requests-table th {
          font-weight: bold;
          text-transform: uppercase;
        }

        .view-btn, .close-btn {
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

        .view-btn:hover, .close-btn:hover { background-color: #a71d2a; }

        .details-row { display: none; }
        .details-row.open { display: table-row; }

        .details-inner-table { width: 100%; border-collapse: collapse; }
        .details-inner-table td { padding: 6px 8px; border: 1px solid #eee; font-size: 14px; }

        .input-field { width: 100%; padding: 5px; margin: 5px 0; box-sizing: border-box; }

        .radio-group { display: flex; gap: 12px; margin: 6px 0; }

        .form-actions { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
      `}</style>

            <main className="ongoing-requests-main">
                <h1>Ongoing Blood Requests</h1>
                <table className="ongoing-requests-table">
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
                            const form = getForm(request.id);
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
                                                        ["Hospital ID", request.hospital_id],
                                                        ["Hospital Name", request.hospital_name],
                                                        ["Hospital Address", request.hospital_address],
                                                        ["Response ID", request.response_id],
                                                        ["Approved AdminID", request.approved_admin_id],
                                                    ].map(([label, value]) => (
                                                        <tr key={label}>
                                                            <td><strong>{label}:</strong></td>
                                                            <td>{value}</td>
                                                        </tr>
                                                    ))}

                                                    {/* Close Request Form */}
                                                    <tr>
                                                        <td colSpan={2}>
                                                            <form onSubmit={(e) => handleSubmit(e, request.id, "close")}>
                                                                <input type="hidden" name="request_id" value={request.id} />

                                                                <strong>Response Status</strong>
                                                                <div className="radio-group">
                                                                    {["Success", "Partial Success", "Failure"].map((val) => (
                                                                        <label key={val}>
                                                                            <input
                                                                                type="radio"
                                                                                name={`response_status_${request.id}`}
                                                                                value={val}
                                                                                checked={form.response_status === val}
                                                                                onChange={(e) => setFormField(request.id, "response_status", e.target.value)}
                                                                                required
                                                                            />{" "}
                                                                            {val}
                                                                        </label>
                                                                    ))}
                                                                </div>

                                                                <label><strong>Report</strong></label>
                                                                <input className="input-field" type="text" name="report" value={form.report} onChange={(e) => setFormField(request.id, "report", e.target.value)} />

                                                                <label><strong>Units Donated</strong></label>
                                                                <input className="input-field" type="number" name="units_donated" value={form.units_donated} onChange={(e) => setFormField(request.id, "units_donated", Number(e.target.value))} required />

                                                                <label><strong>Certificate Status</strong></label>
                                                                <input className="input-field" type="text" name="certificate_status" value={form.certificate_status} onChange={(e) => setFormField(request.id, "certificate_status", e.target.value)} required />

                                                                <label><strong>Responded Donor IDs</strong></label>
                                                                <input className="input-field" type="text" name="response_donor_ids" value={form.response_donor_ids} onChange={(e) => setFormField(request.id, "response_donor_ids", e.target.value)} />

                                                                <label><strong>Donation Date:</strong></label>
                                                                <input className="input-field" type="date" name="donation_date" value={form.donation_date} onChange={(e) => setFormField(request.id, "donation_date", e.target.value)} />

                                                                <div className="form-actions">
                                                                    <button type="submit" className="close-btn">Close Request</button>
                                                                    <button
                                                                        type="button"
                                                                        className="close-btn"
                                                                        onClick={(e) => handleSubmit(e, request.id, "close_and_send")}
                                                                    >
                                                                        Close Request and Send Certificate
                                                                    </button>
                                                                </div>
                                                            </form>
                                                        </td>
                                                    </tr>
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
        BACKEND CALL STRUCTURE — Ongoing Requests Admin
        ======================================================

        ENDPOINTS
        ---------
        GET  /admin/requests/ongoing                          → list ongoing requests
        POST /close_request/close_ongoing_requests            → close request
        POST /close_request/close_ongoing_requests_and_send  → close + send certificate

        AUTH
        ----
        Admin session / JWT required

        REQUEST BODY (both POST endpoints)
        -----------------------------------
        {
          request_id: string,
          response_status: "Success" | "Partial Success" | "Failure",
          report: string,
          units_donated: number,
          certificate_status: string,
          response_donor_ids: string,
          donation_date: string (YYYY-MM-DD)
        }

        FRONTEND RESPONSIBILITY
        -----------------------
        - Toggle expandable rows per request
        - Maintain per-request form state
        - Two submit actions: close only vs close + send certificate

        ERROR CASES
        -----------
        - 401 → redirect to /admin/login
        - 400 → missing/invalid fields
        - 500 → server error
      */}
        </AdminBase>
    );
}

function FragmentRow({ children }) {
    return <>{children}</>;
}
