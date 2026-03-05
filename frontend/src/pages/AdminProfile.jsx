import AdminBase from "./AdminBase";

export default function AdminProfile({ details = {}, onUpdate }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target));
    onUpdate?.(data);
  };

  return (
    <AdminBase active="profile">
      <style>{`
        .profile-form-container {
          max-width: 800px;
          margin: 40px auto;
          padding: 30px;
          background-color: #fff;
          border-radius: 8px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .profile-form-container h2 {
          text-align: center;
          color: #333;
          font-size: 2rem;
          margin-bottom: 30px;
        }

        .profile-form-container form {
          display: flex;
          flex-direction: column;
        }

        .profile-form-container label {
          font-size: 1rem;
          color: #333;
          margin-bottom: 8px;
          font-weight: bold;
        }

        .profile-form-container input {
          padding: 12px;
          font-size: 1rem;
          margin-bottom: 20px;
          border: 1px solid #ccc;
          border-radius: 4px;
          background-color: #f9f9f9;
          color: #333;
        }

        .profile-form-container input:focus {
          outline: none;
          border-color: #2980b9;
          box-shadow: 0 0 5px rgba(41, 128, 185, 0.6);
        }

        .profile-form-container button[type="submit"] {
          background-color: #2980b9;
          color: white;
          padding: 12px;
          border: none;
          border-radius: 4px;
          font-size: 1.1rem;
          cursor: pointer;
          transition: background-color 0.3s ease;
        }

        .profile-form-container button[type="submit"]:hover {
          background-color: #3498db;
        }
      `}</style>

      <div className="profile-form-container">
        <h2>Admin Profile</h2>
        <form onSubmit={handleSubmit}>
          <label htmlFor="id">Admin ID:</label>
          <input type="text" name="id" id="id" defaultValue={details.id} readOnly />

          <label htmlFor="name">Name:</label>
          <input type="text" name="name" id="name" defaultValue={details.username} />

          <label htmlFor="email">Email:</label>
          <input type="email" name="email" id="email" defaultValue={details.email} />

          <label htmlFor="password">Password:</label>
          <input type="password" name="password" id="password" defaultValue={details.password} readOnly />

          <label htmlFor="vec_registration_number">VEC Registration Number:</label>
          <input type="number" name="vec_registration_number" id="vec_registration_number" defaultValue={details.vec_registration_number} />

          <label htmlFor="active_status">Active Status:</label>
          <input type="text" name="active_status" id="active_status" defaultValue={details.active_status} />

          <label htmlFor="department">Department:</label>
          <input type="text" name="department" id="department" defaultValue={details.department} />

          <label htmlFor="approved_donation">Approved Donation:</label>
          <input type="number" name="approved_donation" id="approved_donation" defaultValue={details.approved_donation_count} readOnly />

          <label htmlFor="closed_requests">Closed Requests:</label>
          <input type="number" name="closed_requests" id="closed_requests" defaultValue={details.closed_requests_count} readOnly />

          <label htmlFor="contact_number">Contact Number:</label>
          <input type="text" name="contact_number" id="contact_number" defaultValue={details.mobile_number} />

          <label htmlFor="date_of_birth">Date of Birth:</label>
          <input type="date" name="date_of_birth" id="date_of_birth" defaultValue={details.date_of_birth} />

          <button type="submit">Update Details</button>
        </form>
      </div>

      {/*
        ======================================================
        BACKEND CALL STRUCTURE — Admin Profile
        ======================================================

        ENDPOINT
        --------
        GET  /admin/profile        → fetch admin details
        POST /admin/update-details → update admin details

        AUTH
        ----
        Admin session / JWT required

        RESPONSE (GET, example)
        -----------------------
        {
          details: {
            id, username, email, password,
            vec_registration_number, active_status,
            department, approved_donation_count,
            closed_requests_count, mobile_number,
            date_of_birth
          }
        }

        FRONTEND RESPONSIBILITY
        -----------------------
        - Pre-fill all fields with existing data
        - Read-only fields: id, password, approved_donation, closed_requests
        - Submit updates via POST

        ERROR CASES
        -----------
        - 401 → redirect to /admin/login
        - 400 → validation error
        - 500 → server error
      */}
    </AdminBase>
  );
}
