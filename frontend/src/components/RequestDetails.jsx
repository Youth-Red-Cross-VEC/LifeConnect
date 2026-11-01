import { useCallback } from "react";
import AsyncState from "./AsyncState";
import { useApiData } from "../hooks/useApiData";
import { api } from "../services/api";
import { detailRows } from "../services/requests";
import { unwrapData } from "../services/unwrap";

// Details panel for one blood request, loaded from GET /api/v1/blood-requests/{id} when it
// is first opened (the list endpoints only return a summary).
export default function RequestDetails({ requestId }) {
  const load = useCallback(
    async () => unwrapData(await api.getBloodRequest(requestId), "Failed to load request details."),
    [requestId],
  );
  const { data, isLoading, error } = useApiData(load, {
    errorMessage: "Server error. Could not load request details.",
  });

  return (
    <AsyncState isLoading={isLoading} error={error} loadingText="Loading details...">
      <table className="details-inner-table">
        <tbody>
          {detailRows(data).map(([label, value]) => (
            <tr key={label}>
              <td><strong>{label}:</strong></td>
              <td>{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </AsyncState>
  );
}
