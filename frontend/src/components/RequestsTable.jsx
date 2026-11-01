import { Fragment, useState } from "react";
import AsyncState from "./AsyncState";
import RequestDetails from "./RequestDetails";

// Summary table for a list of blood requests (the list endpoints' fields) with an expandable
// details panel. The page owns the CSS: `tableClass` picks its table style, and `renderExtra`
// can add controls (e.g. a close form) under the details of an open row.
export default function RequestsTable({
  requests,
  isLoading,
  error,
  tableClass,
  emptyText,
  renderExtra,
}) {
  const [openId, setOpenId] = useState(null);

  return (
    <AsyncState
      isLoading={isLoading}
      error={error}
      isEmpty={requests.length === 0}
      loadingText="Loading requests..."
      emptyText={emptyText}
    >
      <table className={tableClass}>
        <thead>
          <tr>
            <th>Patient Name</th>
            <th>Blood Group</th>
            <th>Hospital Name</th>
            <th>Due Date</th>
            <th>Units</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {requests.map((request) => {
            const isOpen = openId === request.id;
            return (
              <Fragment key={request.id}>
                <tr>
                  <td>{request.patient_name}</td>
                  <td>{request.blood_group}</td>
                  <td>{request.hospital_name}</td>
                  <td>{request.due_date ? String(request.due_date).slice(0, 10) : "—"}</td>
                  <td>{request.units_required}</td>
                  <td>{request.status}</td>
                  <td>
                    <button
                      className="view-btn"
                      type="button"
                      onClick={() => setOpenId(isOpen ? null : request.id)}
                    >
                      {isOpen ? "Hide Details" : "View Details"}
                    </button>
                  </td>
                </tr>
                {isOpen && (
                  <tr className="details-row open">
                    <td colSpan={7}>
                      <RequestDetails requestId={request.id} />
                      {renderExtra?.(request)}
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </AsyncState>
  );
}
