import { useState } from "react";

export default function FetchDonors({
  onBackToHome,
  onSubmitFindDonor,
  defaultBloodType = "",
  defaultHospitalAddress = "",
}) {
  const [bloodType, setBloodType] = useState(defaultBloodType);
  const [hospitalAddress, setHospitalAddress] = useState(defaultHospitalAddress);

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = { bloodType, hospitalAddress };
    // eslint-disable-next-line no-console
    console.log("FetchDonors payload:", payload);
    onSubmitFindDonor?.(payload);
  };

  return (
    <div className="page" style={{ marginTop: 0, maxWidth: "100%", padding: 0 }}>
      <div className="header" style={{ borderRadius: 0 }}>
        <a href="/" style={{ textDecoration: "none", color: "white" }}>
          <h1>LifeConnect</h1>
        </a>
        <button
          type="button"
          className="ghost-btn"
          onClick={() => (onBackToHome ? onBackToHome() : (window.location.href = "/"))}
        >
          Back to Home
        </button>
      </div>

      <div className="center" style={{ minHeight: "calc(100vh - 80px)" }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "20px", justifyContent: "center" }}>
          <img
            src="/images/index/blood-donation.png"
            alt="Decorative Image"
            style={{ width: "350px", height: "auto", borderRadius: "8px", objectFit: "cover" }}
          />

          <div className="card narrow" style={{ maxWidth: "400px" }}>
            <h2 className="title" style={{ textAlign: "center" }}>
              Find Donors
            </h2>
            <form onSubmit={handleSubmit} className="stack">
              <label className="field">
                <span>Blood Type:</span>
                <select
                  id="bloodType"
                  name="bloodType"
                  required
                  value={bloodType}
                  onChange={(e) => setBloodType(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px",
                    borderRadius: "8px",
                    border: "1px solid #ddd",
                  }}
                >
                  <option value="">Select Blood Type</option>
                  <option value="A+">A+</option>
                  <option value="B+">B+</option>
                  <option value="O+">O+</option>
                  <option value="AB+">AB+</option>
                  <option value="A-">A-</option>
                  <option value="B-">B-</option>
                  <option value="O-">O-</option>
                  <option value="AB-">AB-</option>
                </select>
              </label>

              <label className="field">
                <span>Hospital Address (Optional):</span>
                <input
                  type="text"
                  id="hospital_address"
                  name="hospital_address"
                  placeholder="Enter Hospital Address"
                  value={hospitalAddress}
                  onChange={(e) => setHospitalAddress(e.target.value)}
                />
              </label>

              <button className="primary full" type="submit">
                Find Donor
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

