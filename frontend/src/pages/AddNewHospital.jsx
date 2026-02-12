import React, { useState } from "react";

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

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);

        // eslint-disable-next-line no-console
        console.log("Adding new hospital:", formData);

        // TODO: Replace with actual API call
        // await fetch('/api/hospitals/add', {
        //   method: 'POST',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: JSON.stringify(formData)
        // });

        await new Promise((res) => setTimeout(res, 500));
        setSubmitting(false);
    };

    return (
        <div className="page">
            <div className="center">
                <div className="card" style={{ maxWidth: "600px", width: "100%" }}>
                    <h2 className="title">Hospital Details</h2>

                    <form onSubmit={handleSubmit}>
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
    );
}
