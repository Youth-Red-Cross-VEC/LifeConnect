import { useNavigate } from "react-router-dom";

export default function NewDonorRegistrationConfirmation() {
  const navigate = useNavigate();

  return (
    <div className="center" style={{ minHeight: "100vh", flexDirection: "column", gap: "16px" }}>
      <div className="card" style={{ maxWidth: "480px", textAlign: "center", padding: "40px 32px" }}>
        <div style={{ fontSize: "4rem", marginBottom: "12px" }}>🎉</div>
        <h2 style={{ color: "#b30001", marginBottom: "12px" }}>Registration Successful!</h2>
        <p style={{ color: "#555", marginBottom: "8px" }}>
          Welcome to LifeConnect! Your donor registration has been submitted successfully.
        </p>
        <p style={{ color: "#777", fontSize: "0.9rem", marginBottom: "24px" }}>
          You can now log in to your donor dashboard and start making a difference.
        </p>
        <button
          className="primary"
          style={{ padding: "12px 32px", borderRadius: "10px" }}
          onClick={() => navigate("/donor/login")}
        >
          Go to Login
        </button>
      </div>
    </div>
  );
}
