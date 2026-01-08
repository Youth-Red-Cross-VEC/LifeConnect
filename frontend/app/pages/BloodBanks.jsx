"use client";

const sampleHospitals = [
  {
    NAME: "Apollo Hospital",
    ADDRESS: "21 Greams Lane, Chennai",
    "Contact Number": "+91-44-4040-1066",
    Website: "https://www.apollohospitals.com/",
  },
  {
    NAME: "Fortis Malar",
    ADDRESS: "52, 1st Main Rd, Gandhi Nagar, Adyar, Chennai",
    "Contact Number": "+91-44-4289-2222",
    Website: "https://www.fortishealthcare.com/",
  },
];

export default function BloodBanks({ hospitals = sampleHospitals }) {
  return (
    <div className="page">
      <header className="header">
        <h1>LifeConnect</h1>
        <button className="ghost-btn" onClick={() => (window.location.href = "/")}>
          Back to Home
        </button>
      </header>

      <h2 className="title">Blood Banks</h2>

      <div className="card scroll-x">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Address</th>
              <th>Contact</th>
              <th>Website</th>
            </tr>
          </thead>
          <tbody>
            {hospitals.map((h, idx) => (
              <tr key={`${h.NAME}-${idx}`}>
                <td>{h.NAME}</td>
                <td>{h.ADDRESS}</td>
                <td>{h["Contact Number"]}</td>
                <td>
                  {h.Website ? (
                    <a href={h.Website} target="_blank" rel="noreferrer">
                      Visit Website
                    </a>
                  ) : (
                    "None"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

