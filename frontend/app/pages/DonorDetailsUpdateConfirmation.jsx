"use client";

const labels = [
  "Name",
  "Blood Group",
  "First Name",
  "Last Name",
  "Age",
  "Contact Number",
  "Secondary Contact Number",
  "Marital Status",
  "Aadhar Number",
  "Address",
  "City",
  "State",
  "Country",
  "Pincode",
  "Disease Name",
  "Disease Description",
];

const sampleDetails = [
  "Priya S",
  "B+",
  "Priya",
  "Srinivasan",
  "27",
  "+91 98765 43210",
  "+91 90123 45678",
  "Single",
  "1234-5678-9012",
  "21, Lake View Road",
  "Chennai",
  "Tamil Nadu",
  "India",
  "600028",
  "None",
  "NA",
];

export default function DonorDetailsUpdateConfirmation({ details = sampleDetails }) {
  const summary = labels.map((label, idx) => ({
    label,
    value: details[idx],
  }));

  return (
    <main className="center">
      <div className="card narrow">
        <h1 className="success">Success!</h1>
        <h2>Your Donor Details Have Been Updated</h2>
        <p className="muted">We saved the information you provided.</p>

        <div className="details">
          {summary.map((item) => (
            <p key={item.label}>
              <b>{item.label}:</b> {item.value ?? "—"}
            </p>
          ))}
        </div>

        <div className="muted small">Phone: 9150450401 · Email: yrclifeconnect@gmail.com</div>

        <div className="actions">
          <button className="primary" onClick={() => (window.location.href = "/")}>
            Home
          </button>
          <button className="ghost-btn" onClick={() => (window.location.href = "/donor-login")}>
            Donor Login
          </button>
        </div>

        <div className="json-block">
          <div className="small muted">Payload for backend</div>
          <pre>{JSON.stringify(details, null, 2)}</pre>
        </div>
      </div>
    </main>
  );
}

