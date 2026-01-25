import { useMemo, useState } from "react";

export default function ExpiredRequestsAdmin({
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

  const toggleDetails = (id) => setOpenId((prev) => (prev === id ? null : id));

  const handleSubmit = (e, requestId, variant) => {
    e.preventDefault();
    const payload = { request_id: requestId, ...getForm(requestId) };
    // eslint-disable-next-line no-console
    console.log("ExpiredRequestsAdmin payload:", payload);
    if (variant === "close_and_send") onCloseRequestAndSendCertificate?.(payload);
    else onCloseRequest?.(payload);
  };

  return (
    <div className="page">
      <h1>Expired Blood Requests</h1>
      <table className="table">
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
                      className="primary btn-sm"
                      type="button"
                      onClick={() => toggleDetails(request.id)}
                    >
                      View Details
                    </button>
                  </td>
                </tr>

                <tr id={`details${request.id}`} className={isOpen ? "" : "hidden"}>
                  <td colSpan={6}>
                    <div className="card">
                      <table className="table">
                        <tbody>
                          <tr>
                            <td>
                              <strong>Request ID:</strong>
                            </td>
                            <td>{request.id}</td>
                          </tr>
                          <tr>
                            <td>
                              <strong>Patient Name:</strong>
                            </td>
                            <td>{request.patient_name}</td>
                          </tr>
                          <tr>
                            <td>
                              <strong>Patient Age:</strong>
                            </td>
                            <td>{request.patient_age}</td>
                          </tr>
                          <tr>
                            <td>
                              <strong>Blood Group:</strong>
                            </td>
                            <td>{request.blood_group}</td>
                          </tr>
                          <tr>
                            <td>
                              <strong>Contact Number</strong>
                            </td>
                            <td>{request.contact_number}</td>
                          </tr>
                          <tr>
                            <td>
                              <strong>Attendant Name</strong>
                            </td>
                            <td>{request.attendant_name}</td>
                          </tr>
                          <tr>
                            <td>
                              <strong>Units Required</strong>
                            </td>
                            <td>{request.units_required}</td>
                          </tr>
                          <tr>
                            <td>
                              <strong>Request Reason</strong>
                            </td>
                            <td>{request.request_reason}</td>
                          </tr>
                          <tr>
                            <td>
                              <strong>Due Date</strong>
                            </td>
                            <td>{request.due_date}</td>
                          </tr>
                          <tr>
                            <td>
                              <strong>Hospital ID</strong>
                            </td>
                            <td>{request.hospital_id}</td>
                          </tr>
                          <tr>
                            <td>
                              <strong>Approved AdminID</strong>
                            </td>
                            <td>{request.approved_admin_id}</td>
                          </tr>
                          <tr>
                            <td>
                              <strong>Hospital Name</strong>
                            </td>
                            <td>{request.hospital_name}</td>
                          </tr>
                          <tr>
                            <td>
                              <strong>Hospital Address</strong>
                            </td>
                            <td>{request.hospital_address}</td>
                          </tr>
                          <tr>
                            <td>
                              <strong>Response ID</strong>
                            </td>
                            <td>{request.response_id}</td>
                          </tr>

                          <tr>
                            <td colSpan={2}>
                              <form
                                className="stack"
                                onSubmit={(e) => handleSubmit(e, request.id, "close")}
                              >
                                <input type="hidden" name="request_id" value={request.id} />

                                <div className="field">
                                  <span>Response Status</span>
                                  <div style={{ display: "flex", gap: "10px" }}>
                                    <label>
                                      <input
                                        type="radio"
                                        name={`response_status_${request.id}`}
                                        value="Success"
                                        checked={form.response_status === "Success"}
                                        onChange={(e) =>
                                          setFormField(request.id, "response_status", e.target.value)
                                        }
                                      />
                                      Success
                                    </label>
                                    <label>
                                      <input
                                        type="radio"
                                        name={`response_status_${request.id}`}
                                        value="Partial Success"
                                        checked={form.response_status === "Partial Success"}
                                        onChange={(e) =>
                                          setFormField(request.id, "response_status", e.target.value)
                                        }
                                      />
                                      Partial Success
                                    </label>
                                    <label>
                                      <input
                                        type="radio"
                                        name={`response_status_${request.id}`}
                                        value="Failure"
                                        checked={form.response_status === "Failure"}
                                        onChange={(e) =>
                                          setFormField(request.id, "response_status", e.target.value)
                                        }
                                      />
                                      Failure
                                    </label>
                                  </div>
                                </div>

                                <label className="field">
                                  <span>Report</span>
                                  <input
                                    type="text"
                                    name="report"
                                    value={form.report}
                                    onChange={(e) => setFormField(request.id, "report", e.target.value)}
                                  />
                                </label>

                                <label className="field">
                                  <span>Units Donated</span>
                                  <input
                                    type="number"
                                    name="units_donated"
                                    value={form.units_donated}
                                    required
                                    onChange={(e) =>
                                      setFormField(
                                        request.id,
                                        "units_donated",
                                        Number(e.target.value),
                                      )
                                    }
                                  />
                                </label>

                                <label className="field">
                                  <span>Certificate Status</span>
                                  <input
                                    type="text"
                                    name="certificate_status"
                                    value={form.certificate_status}
                                    required
                                    onChange={(e) =>
                                      setFormField(request.id, "certificate_status", e.target.value)
                                    }
                                  />
                                </label>

                                <label className="field">
                                  <span>Donation Date</span>
                                  <input
                                    type="date"
                                    name="donation_date"
                                    value={form.donation_date}
                                    required
                                    onChange={(e) =>
                                      setFormField(request.id, "donation_date", e.target.value)
                                    }
                                  />
                                </label>

                                <label className="field">
                                  <span>Responsed Donor IDs</span>
                                  <input
                                    type="text"
                                    name="response_donor_ids"
                                    value={form.response_donor_ids}
                                    onChange={(e) =>
                                      setFormField(request.id, "response_donor_ids", e.target.value)
                                    }
                                  />
                                </label>

                                <div className="actions">
                                  <button type="submit" className="primary">
                                    Close Request
                                  </button>
                                  <button
                                    type="button"
                                    className="primary"
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
                    </div>
                  </td>
                </tr>
              </FragmentRow>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function FragmentRow({ children }) {
  return <>{children}</>;
}

