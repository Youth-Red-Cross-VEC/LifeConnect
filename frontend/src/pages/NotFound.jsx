import { useNavigate } from "react-router-dom";

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        background: "#f4f6f9",
        fontFamily: "Arial, sans-serif",
        textAlign: "center",
        padding: "20px",
      }}
    >
      <h1 style={{ fontSize: "6rem", fontWeight: "900", color: "#bf0001", margin: 0 }}>404</h1>
      <h2 style={{ fontSize: "1.6rem", color: "#333", margin: "10px 0" }}>Page Not Found</h2>
      <p style={{ color: "#6b7280", marginBottom: "30px", maxWidth: "400px" }}>
        The page you are looking for does not exist or has been moved.
      </p>
      <button
        onClick={() => navigate("/")}
        style={{
          padding: "12px 28px",
          background: "#bf0001",
          color: "white",
          border: "none",
          borderRadius: "8px",
          fontSize: "1rem",
          fontWeight: "bold",
          cursor: "pointer",
        }}
      >
        Return to Home
      </button>
    </div>
  );
}
