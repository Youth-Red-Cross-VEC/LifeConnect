import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AdminBase from "./AdminBase";
import { api } from "../services/api";

export default function AddNewHospital() {
    const [formData, setFormData] = useState({
        hospital_name: "",
        hospital_address: "",
        city: "",
        state: "",
        country: "",
        pincode: "",
        branch: "",
        landmark: "",
    });

    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const navigate = useNavigate();

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setSuccess("");
        setSubmitting(true);
        try {
            const res = await api.addHospital(formData);
            if (res && (res.success || res.hospital_id)) {
                setSuccess("Hospital added successfully!");
                setTimeout(() => navigate("/admin/hospitals/all"), 1500);
            } else {
                setError(res?.message || "Failed to add hospital. Please try again.");
            }
        } catch {
            setError("Server error. Please try again.");
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <AdminBase active="hospitals">
        <div className="page">
            <div className="center">
                <div className="card" style={{ maxWidth: "600px", width: "100%" }}>
                    <h2 className="title">Hospital Details</h2>

                    <form onSubmit={handleSubmit}>
                        {error && <div className="error" style={{ marginBottom: "12px" }}>{error}</div>}
                        {success && <div style={{ background: "#d4edda", color: "#155724", padding: "10px", borderRadius: "6px", marginBottom: "12px" }}>{success}</div>}
                        <div className="stack">
                            <label className="field">
                                <span>Hospital Name:</span>
                                <input
                                    type="text"
                                    name="hospital_name"
                                    value={formData.hospital_name}
                                    onChange={handleChange}
                                    required
                                />
                            </label>

                            <label className="field">
                                <span>Hospital Address:</span>
                                <input
                                    type="text"
                                    name="hospital_address"
                                    value={formData.hospital_address}
                                    onChange={handleChange}
                                    required
                                />
                            </label>

                            <label className="field">
                                <span>City:</span>
                                <input
                                    type="text"
                                    name="city"
                                    value={formData.city}
                                    onChange={handleChange}
                                    required
                                />
                            </label>

                            <label className="field">
                                <span>State:</span>
                                <input
                                    type="text"
                                    name="state"
                                    value={formData.state}
                                    onChange={handleChange}
                                    required
                                />
                            </label>

                            <label className="field">
                                <span>Country:</span>
                                <input
                                    type="text"
                                    name="country"
                                    value={formData.country}
                                    onChange={handleChange}
                                    required
                                />
                            </label>

                            <label className="field">
                                <span>Pincode:</span>
                                <input
                                    type="text"
                                    name="pincode"
                                    value={formData.pincode}
                                    onChange={handleChange}
                                    required
                                />
                            </label>

                            <label className="field">
                                <span>Branch:</span>
                                <input
                                    type="text"
                                    name="branch"
                                    value={formData.branch}
                                    onChange={handleChange}
                                />
                            </label>

                            <label className="field">
                                <span>Landmark:</span>
                                <input
                                    type="text"
                                    name="landmark"
                                    value={formData.landmark}
                                    onChange={handleChange}
                                />
                            </label>

                            <button type="submit" className="primary full" disabled={submitting}>
                                {submitting ? "Adding Hospital..." : "Add Hospital"}
                            </button>
                        </div>
                    </form>

                    <div className="actions" style={{ marginTop: "20px", justifyContent: "center", gap: "15px" }}>
                        <a
                            href="/admin/dashboard"
                            className="secondary"
                            style={{
                                textDecoration: "none",
                                padding: "10px 20px",
                                borderRadius: "5px",
                                display: "inline-block"
                            }}
                        >
                            Back To Dashboard
                        </a>
                        <a
                            href="/admin/hospitals"
                            className="secondary"
                            style={{
                                textDecoration: "none",
                                padding: "10px 20px",
                                borderRadius: "5px",
                                display: "inline-block"
                            }}
                        >
                            Back To Hospital List
                        </a>
                    </div>
                </div>
            </div>

            {/*
        ======================================================
        BACKEND CALL STRUCTURE — Add New Hospital
        ======================================================

        ENDPOINT
        --------
        POST /api/hospitals/add

        AUTH
        ----
        Admin session / JWT required

        REQUEST BODY
        ------------
        {
          hospital_name: string,
          hospital_address: string,
          city: string,
          state: string,
          country: string,
          pincode: string,
          branch: string (optional),
          landmark: string (optional)
        }

        RESPONSE (example)
        ------------------
        {
          success: true,
          message: "Hospital added successfully",
          hospital_id: string
        }

        ERROR CASES
        -----------
        - 400 → validation error
        - 401 → redirect to /admin/login
        - 409 → hospital already exists
        - 500 → server error
      */}
        </div>
        </AdminBase>
    );
}
