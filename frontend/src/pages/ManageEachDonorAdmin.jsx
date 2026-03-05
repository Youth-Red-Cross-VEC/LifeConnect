import AdminBase from "./AdminBase";

export default function ManageEachDonorAdmin({ details = {}, onUpdate }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target));
    onUpdate?.(data);
  };

  return (
    <AdminBase active="manage-donors">
      <style>{`
        .manage-donor-page {
          font-family: Arial, sans-serif;
          background-color: #f4f9ff;
        }

        .manage-donor-page h2 {
          text-align: center;
          color: #003366;
          margin-top: 20px;
          font-size: 2rem;
        }

        .manage-donor-form {
          max-width: 800px;
          margin: 20px auto;
          background: #fff;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        .manage-donor-form label {
          display: block;
          font-weight: bold;
          margin-bottom: 5px;
          color: #003366;
        }

        .manage-donor-form input,
        .manage-donor-form select {
          width: 100%;
          padding: 8px;
          margin-bottom: 15px;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-size: 14px;
          background: #f9f9f9;
          box-sizing: border-box;
        }

        .manage-donor-form input[readonly] {
          background: #e9e9e9;
          cursor: not-allowed;
        }

        .manage-donor-form h3 {
          margin-top: 20px;
          color: #003366;
          border-bottom: 2px solid #003366;
          padding-bottom: 5px;
        }

        .manage-donor-form button[type="submit"] {
          background-color: #003366;
          color: white;
          border: none;
          padding: 10px 15px;
          font-size: 16px;
          border-radius: 4px;
          cursor: pointer;
          transition: background-color 0.3s;
        }

        .manage-donor-form button[type="submit"]:hover { background-color: #00509e; }
      `}</style>

      <div className="manage-donor-page">
        <h2>Donor Details</h2>
        <form className="manage-donor-form" onSubmit={handleSubmit}>
          {/* Donor Account Fields */}
          <label htmlFor="id">Donor ID:</label>
          <input type="text" name="id" id="id" defaultValue={details.id} readOnly />

          <label htmlFor="name">Name:</label>
          <input type="text" name="name" id="name" defaultValue={details.name} />

          <label htmlFor="email">Email:</label>
          <input type="email" name="email" id="email" defaultValue={details.email} readOnly />

          <label htmlFor="password">Password:</label>
          <input type="password" name="password" id="password" defaultValue={details.password} readOnly />

          <label htmlFor="blood_group">Blood Group:</label>
          <input type="text" name="blood_group" id="blood_group" defaultValue={details.blood_group} />

          <label htmlFor="personal_details_id">Personal Details ID:</label>
          <input type="text" name="personal_details_id" id="personal_details_id" defaultValue={details.personal_details_id} readOnly />

          <label htmlFor="active_status">Active Status:</label>
          <input type="text" name="active_status" id="active_status" defaultValue={details.active_status} />

          <label htmlFor="last_donated_date">Last Donated Date:</label>
          <input type="text" name="last_donated_date" id="last_donated_date" defaultValue={details.last_donated_date} readOnly />

          <label htmlFor="number_of_times_donated">Times Donated:</label>
          <input type="number" name="number_of_times_donated" id="number_of_times_donated" defaultValue={details.number_of_times_donated} />

          <label htmlFor="last_login_date">Last Login Date:</label>
          <input type="text" name="last_login_date" id="last_login_date" defaultValue={details.last_login_date} readOnly />

          {/* Personal Details */}
          <h3>Personal Details</h3>
          <label htmlFor="first_name">First Name:</label>
          <input type="text" name="first_name" id="first_name" defaultValue={details.first_name} />

          <label htmlFor="last_name">Last Name:</label>
          <input type="text" name="last_name" id="last_name" defaultValue={details.last_name} />

          <label htmlFor="age">Age:</label>
          <input type="number" name="age" id="age" defaultValue={details.age} />

          <label htmlFor="contact_number">Contact Number:</label>
          <input type="text" name="contact_number" id="contact_number" defaultValue={details.contact_number} />

          <label htmlFor="date_of_birth">Date of Birth:</label>
          <input type="date" name="date_of_birth" id="date_of_birth" defaultValue={details.date_of_birth} />

          <label htmlFor="marital_status">Marital Status:</label>
          <input type="text" name="marital_status" id="marital_status" defaultValue={details.marital_status} />

          <label htmlFor="secondary_contact_number">Secondary Contact Number:</label>
          <input type="text" name="secondary_contact_number" id="secondary_contact_number" defaultValue={details.secondary_contact_number} />

          <label htmlFor="aadhar_number">Aadhar Number:</label>
          <input type="text" name="aadhar_number" id="aadhar_number" defaultValue={details.aadhar_number} />

          {/* Address Details */}
          <h3>Address Details</h3>
          <label htmlFor="address">Address:</label>
          <input type="text" name="address" id="address" defaultValue={details.address} />

          <label htmlFor="city">City:</label>
          <input type="text" name="city" id="city" defaultValue={details.city} />

          <label htmlFor="state">State:</label>
          <input type="text" name="state" id="state" defaultValue={details.state} />

          <label htmlFor="country">Country:</label>
          <input type="text" name="country" id="country" defaultValue={details.country} />

          <label htmlFor="pincode">Pincode:</label>
          <input type="text" name="pincode" id="pincode" defaultValue={details.pincode} />

          {/* Disease Details */}
          <h3>Disease Details</h3>
          <label htmlFor="disease_name">Disease Name:</label>
          <input type="text" name="disease_name" id="disease_name" defaultValue={details.disease_name} />

          <label htmlFor="disease_description">Disease Description:</label>
          <input type="text" name="disease_description" id="disease_description" defaultValue={details.disease_description} />

          <button type="submit">Update Details</button>
        </form>
      </div>

      {/*
        ======================================================
        BACKEND CALL STRUCTURE — Manage Each Donor Admin
        ======================================================

        ENDPOINTS
        ---------
        POST /admin/donor/details  → fetch donor details by donor_id (initial data)
        POST /admin/donor/update   → update donor details

        AUTH
        ----
        Admin session / JWT required

        REQUEST (fetch details)
        -----------------------
        { donor_id: string }

        RESPONSE (example)
        ------------------
        {
          details: {
            id, name, email, password, blood_group,
            personal_details_id, active_status,
            last_donated_date, number_of_times_donated,
            last_login_date, first_name, last_name,
            age, contact_number, date_of_birth,
            marital_status, secondary_contact_number,
            aadhar_number, address, city, state,
            country, pincode, disease_name, disease_description
          }
        }

        FRONTEND RESPONSIBILITY
        -----------------------
        - Pre-fill all fields with existing data
        - Read-only: id, email, password, personal_details_id,
          last_donated_date, last_login_date
        - Submit updates

        ERROR CASES
        -----------
        - 401 → redirect to /admin/login
        - 404 → donor not found
        - 500 → server error
      */}
    </AdminBase>
  );
}
