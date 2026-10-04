import { useCallback, useEffect, useState } from "react";
import { messageFor } from "../services/unwrap.js";

// Load data once on mount (and on reload()) with consistent loading/error state.
//   const { data, isLoading, error, reload, setData } = useApiData(
//     async () => unwrapList(await api.getPendingRequests(), "Failed to load requests."),
//     { initial: [], errorMessage: "Server error. Could not load pending requests." },
//   );
// `load` should return the data or throw (use unwrapList/unwrapData). Pass a stable function
// (module-level or useCallback) to avoid reloading on every render.
export function useApiData(load, { initial = null, errorMessage = "Failed to load data." } = {}) {
  const [data, setData] = useState(initial);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [reloadCount, setReloadCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    load()
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setError("");
        }
      })
      .catch((err) => {
        if (!cancelled) setError(messageFor(err, errorMessage));
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [load, errorMessage, reloadCount]);

  const reload = useCallback(() => {
    setIsLoading(true);
    setReloadCount((n) => n + 1);
  }, []);

  return { data, setData, isLoading, error, reload };
}
