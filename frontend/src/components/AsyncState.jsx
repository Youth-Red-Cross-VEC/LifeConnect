// One place for the loading / error / empty states every data page needs.
//   <AsyncState isLoading={isLoading} error={error} isEmpty={rows.length === 0}
//               loadingText="Loading requests..." emptyText="No pending requests.">
//     ...table...
//   </AsyncState>
const base = { textAlign: "center", padding: "40px" };

export default function AsyncState({
  isLoading,
  error,
  isEmpty = false,
  loadingText = "Loading...",
  emptyText = "Nothing to show.",
  onRetry,
  children,
}) {
  if (isLoading) {
    return (
      <p role="status" style={base}>
        {loadingText}
      </p>
    );
  }
  if (error) {
    return (
      <div role="alert" style={{ ...base, color: "#c82333" }}>
        <p style={{ margin: 0 }}>{error}</p>
        {onRetry && (
          <button type="button" onClick={onRetry} style={{ marginTop: "12px", cursor: "pointer" }}>
            Try again
          </button>
        )}
      </div>
    );
  }
  if (isEmpty) return <p style={base}>{emptyText}</p>;
  return children;
}
