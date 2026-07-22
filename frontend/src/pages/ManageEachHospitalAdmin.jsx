import AdminBase from "./AdminBase";

export default function ManageEachHospitalAdmin({ details = {}, onUpdate }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target));
    onUpdate?.(data);
  };

  return (
    <AdminBase active="hospitals">
      <style>{`
        .manage-hospital-page {
          font-family: Arial, sans-serif;
          background-color: #f4f9ff;
        }

        .manage-hospital-page h2 {
          text-align: center;
          color: #003366;
          margin-top: 20px;
          font-size: 2rem;
        }

        .manage-hospital-form {
          max-width: 800px;
          margin: 20px auto;
          background: #fff;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        .manage-hospital-form label {
          display: block;
          font-weight: bold;
          margin-bottom: 5px;
          color: #003366;
        }

        .manage-hospital-form input,
        .manage-hospital-form textarea {
          width: 100%;
          padding: 8px;
          margin-bottom: 15px;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-size: 14px;
          background: #f9f9f9;
          box-sizing: border-box;
        }

        .manage-hospital-form input[readonly] {
          background: #e9e9e9;
          cursor: not-allowed;
        }

        .manage-hospital-form .form-actions {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          margin-top: 10px;
        }

        .manage-hospital-form button[type="submit"] {
          background-color: #003366;
          color: white;
          border: none;
          padding: 10px 15px;
          font-size: 16px;
          border-radius: 4px;
          cursor: pointer;
          transition: background-color 0.3s;
        }

        .manage-hospital-form button[type="submit"]:hover { background-color: #00509e; }

        .manage-hospital-form .back-link {
          display: inline-block;
          background-color: #6c757d;
          color: white;
          padding: 10px 15px;
          font-size: 16px;
          border-radius: 4px;
          text-decoration: none;
          transition: background-color 0.3s;
        }

        .manage-hospital-form .back-link:hover { background-color: #5a6268; }
      `}</style>

      <div className="manage-hospital-page">
        <h2>Hospital Details</h2>
        <form className="manage-hospital-form" onSubmit={handleSubmit}>
          <label htmlFor="id">Hospital ID:</label>
          <input type="text" id="id" name="id" defaultValue={details.id} readOnly />

          <label htmlFor="hospital_name">Hospital Name:</label>
          <input type="text" id="hospital_name" name="hospital_name" defaultValue={details.hospital_name} required />

          <label htmlFor="hospital_address">Hospital Address:</label>
          <textarea id="hospital_address" name="hospital_address" rows={3} required defaultValue={details.hospital_address} />

          <label htmlFor="city">City:</label>
          <input type="text" id="city" name="city" defaultValue={details.city} required />

          <label htmlFor="state">State:</label>
          <input type="text" id="state" name="state" defaultValue={details.state} required />

          <label htmlFor="country">Country:</label>
          <input type="text" id="country" name="country" defaultValue={details.country} required />

          <label htmlFor="pincode">Pincode:</label>
          <input type="text" id="pincode" name="pincode" defaultValue={details.pincode} required />

          <label htmlFor="branch">Branch:</label>
          <input type="text" id="branch" name="branch" defaultValue={details.branch} />

          <label htmlFor="landmark">Landmark:</label>
          <input type="text" id="landmark" name="landmark" defaultValue={details.landmark} />

          <div className="form-actions">
            <button type="submit">Update Details</button>
            <a href="/admin/hospitals" className="back-link">Back To Hospital List</a>
            <a href="/admin/dashboard" className="back-link">Back To Dashboard</a>
          </div>
        </form>
      </div>

      {/*
        ======================================================
        BACKEND CALL STRUCTURE — Manage Each Hospital Admin
        ======================================================

        ENDPOINTS
        ---------
        POST /admin/hospital/details → fetch hospital details by hospital_id
        POST /admin/hospital/update  → update hospital details

        AUTH
        ----
        Admin session / JWT required

        RESPONSE (example)
        ------------------
        {
          details: {
            id, hospital_name, hospital_address,
            city, state, country, pincode,
            branch, landmark
          }
        }

        FRONTEND RESPONSIBILITY
        -----------------------
        - Pre-fill all fields with existing data
        - Read-only: id
        - Navigation back to hospital list or dashboard

        ERROR CASES
        -----------
        - 401 → redirect to /admin/login
        - 404 → hospital not found
        - 500 → server error
      */}
    </AdminBase>
  );
}
