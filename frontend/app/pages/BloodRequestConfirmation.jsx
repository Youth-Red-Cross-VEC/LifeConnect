"use client";

const sampleDetails = [
  "John Doe",
  "A+",
  "City Hospital",
  "+91 90000 11111",
  "123 Main St, Chennai",
];

export default function BloodRequestConfirmation({ details = sampleDetails }) {
  const [patient, blood, hospital, phone, address] = details;
  const payload = {
    patient_name: patient,
    blood_group: blood,
    hospital_name: hospital,
    contact_number: phone,
    hospital_address: address,
  };

  return (
    <main className="center">
      <div className="card narrow">
        <h1 className="accent">Request Received!</h1>
        <p className="muted">
          Thank you for reaching out. Your blood request is being processed.
        </p>

        <section className="stack">
          <h3>Request Details</h3>
          <p>
            <b>Patient Name:</b> {patient}
          </p>
          <p>
            <b>Blood Group:</b> {blood}
          </p>
          <p>
            <b>Hospital Name:</b> {hospital}
          </p>
          <p>
            <b>Contact Number:</b> {phone}
          </p>
          <p>
            <b>Hospital Address:</b> {address}
          </p>
        </section>

        <div className="muted small">Phone: 9150450401 · Email: yrclifeconnect@gmail.com</div>

        <button className="primary full" onClick={() => (window.location.href = "/")}>
          Go back to Home
        </button>

        <div className="json-block">
          <div className="small muted">Payload for backend</div>
          <pre>{JSON.stringify(payload, null, 2)}</pre>
        </div>
      </div>
    </main>
  );
}

