import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useGoogleReCaptcha } from "react-google-recaptcha-v3";
import { api, setToken, setUserType, setUserId, setUsername } from "../services/api";

export default function DonorLogin() {
  const [form, setForm] = useState({
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { executeRecaptcha } = useGoogleReCaptcha();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    setError("");
    if (!executeRecaptcha) {
      setError("reCAPTCHA not ready. Please wait and try again.");
      return;
    }
    setIsLoading(true);
    try {
      const token = await executeRecaptcha("donor_login");
      const res = await api.donorLogin({
        email: form.email,
        password: form.password,
        recaptcha_token: token,
      });
      if (res && res.access_token) {
        setToken(res.access_token);
        setUserType("donor");
        setUserId(res.user_id || "");
        setUsername(res.username || "");
        navigate("/donor/dashboard");
      } else {
        setError(res?.detail || res?.message || "Invalid credentials");
      }
    } catch {
      setError("Server error. Try again.");
    } finally {
      setIsLoading(false);
    }
  }, [executeRecaptcha, form, navigate]);

  return (
    <div className="donor-login-wrapper">
      <style>{`
        .donor-login-wrapper {
          font-family: Arial, Helvetica, sans-serif;
          height: 100vh;
          width: 100vw;
          justify-content: flex-end;
          align-items: center;
          display: flex;
          background-color: #f8f8f8;
          color: #333;
          position: relative;
          overflow: hidden;
          margin: 0;
          padding: 0;
        }

        /* Navbar styling for smaller screens */
        .donor-login-wrapper .navbar {
          display: none;
          width: 100%;
          background-color: #b30001;
          padding: 10px;
          position: fixed;
          top: 0;
          left: 0;
          z-index: 1000;
          justify-content: space-between;
          align-items: center;
        }

        .donor-login-wrapper .navbar-logo {
          color: white;
          font-size: 1.5rem;
          font-weight: bold;
        }

        .donor-login-wrapper .navbar-buttons {
          display: flex;
          gap: 10px;
        }

        .donor-login-wrapper .navbar-btn {
          color: #b30001;
          background-color: white;
          padding: 10px 15px;
          border-radius: 15px;
          text-decoration: none;
          font-weight: bold;
        }

        .donor-login-wrapper .navbar-btn:hover {
          background-color: #bf0001;
          color: white;
        }

        /* Styling the container for the login form */
        .donor-login-wrapper .container {
          width: 350px;
          padding: 20px;
          border-radius: 10px;
          background-color: #fff;
          box-shadow: 0 0 10px rgba(163, 131, 131, 0.733);
          text-align: center;
          position: absolute;
          top: 20%;
          right: 250px;
          z-index: 2;
        }

        /* Styling the form layout */
        .donor-login-wrapper form {
          display: flex;
          flex-direction: column;
        }

        .donor-login-wrapper form button {
          margin-bottom: 20px;
        }

        .donor-login-wrapper form a {
          display: block;
          margin-top: 25px;
          text-align: center;
        }

        /* Styling for labels and input fields */
        .donor-login-wrapper label,
        .donor-login-wrapper input {
          text-align: left;
          margin-bottom: 8px;
          font-weight: bolder;
        }

        /* Input field styles */
        .donor-login-wrapper input {
          width: 100%;
          padding: 8px;
          margin-bottom: 5px;
          border: 2px solid #b30001;
          border-radius: 10px;
          margin-top: 3px;
          box-sizing: border-box;
        }

        /* Heading styles */
        .donor-login-wrapper h2 {
          padding: 10px;
          margin-bottom: 10px;
          color: #b30001;
          font-weight: bolder;
        }

        /* Button styles */
        .donor-login-wrapper button {
          padding: 10px;
          border: none;
          border-radius: 10px;
          cursor: pointer;
          background-color: #b30001;
          color: white;
          font-size: medium;
          font-weight: bold;
        }

        /* Styling anchor links */
        .donor-login-wrapper a {
          color: #b30001;
          text-decoration: none;
          margin: 0 5px;
          display: inline-block;
          font-size: medium;
          font-weight: bold;
        }

        /* Hover effect for anchor links */
        .donor-login-wrapper a:hover {
          text-decoration: underline;
        }

        /* Styling the background red circular effect */
        .donor-login-wrapper .container::before {
          content: "";
          position: absolute;
          height: 1500px;
          width: 1500px;
          top: -10%;
          right: 48%;
          background-image: linear-gradient(-40deg, #b30001, #b30001);
          transform: translate(-20%, -60%);
          border-radius: 50%;
          z-index: -1;
        }

        /* Styling for the button in the top-right corner */
        .donor-login-wrapper .top-right-btn {
          position: absolute;
          top: 20px;
          right: 20px;
          padding: 10px;
          background-color: #b30001;
          border: none;
          border-radius: 10px;
          cursor: pointer;
          z-index: 5;
        }

        .donor-login-wrapper .top-right-btn a {
          color: white;
          text-decoration: none;
        }

        /* Hover effect for the top-right button */
        .donor-login-wrapper .top-right-btn:hover {
          background-color: #8c0001;
        }

        /* Content section inside the red-shape (text and image) */
        .donor-login-wrapper .red-shape-content {
          position: absolute;
          top: 10%;
          left: 5%;
          color: white;
          text-align: left;
          z-index: 10;
          width: 480px;
          padding: 10px;
        }

        /* Styling for the heading inside the red-shape */
        .donor-login-wrapper .red-shape-content h3 {
          font-weight: 600;
          line-height: 1.2;
          font-size: 1.8rem;
          margin-bottom: 10px;
          text-align: left;
        }

        /* Paragraph styling inside the red-shape */
        .donor-login-wrapper .red-shape-content p {
          font-size: 1rem;
          line-height: 1.5;
          text-align: left;
          margin-bottom: 5px;
          color: #ffe9e9;
        }

        /* Signup button styling inside the red-shape */
        .donor-login-wrapper .red-shape-content .signup-btn {
          display: inline-block;
          margin-top: 10px;
          padding: 10px 20px;
          background-color: white;
          color: #b30001;
          font-weight: bold;
          font-size: 1rem;
          border-radius: 15px;
          cursor: pointer;
          transition: 0.3s;
          text-decoration: none;
        }

        /* Hover effect for the signup button */
        .donor-login-wrapper .red-shape-content .signup-btn:hover {
          background-color: #0a0909;
          color: white;
        }

        /* Image styling inside the red-shape */
        .donor-login-wrapper .red-shape-content .image {
          width: 100%;
          max-width: 280px;
          margin: 20px auto 0 auto;
          display: block;
          border-radius: 10px;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
        }

        .donor-login-wrapper .error-alert {
          background-color: #f8d7da;
          color: #721c24;
          padding: 10px;
          border-radius: 5px;
          margin-bottom: 15px;
          font-weight: bold;
          text-align: center;
        }

        /* reCAPTCHA v3 badge is injected by Google automatically */

        /* Responsive Design */
        @media (max-width: 768px) {
          .donor-login-wrapper {
            flex-direction: column;
            justify-content: flex-start;
            align-items: center;
            overflow-x: hidden;
            overflow-y: auto;
            padding: 80px 20px 20px 20px;
          }

          .donor-login-wrapper .navbar {
            display: flex;
          }

          .donor-login-wrapper .container {
            width: 100%;
            max-width: 400px;
            margin: 20px auto;
            z-index: 2;
            position: relative;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            left: 0;
            right: 0;
            top: auto;
          }

          .donor-login-wrapper .container::before {
            content: none;
          }

          .donor-login-wrapper .red-shape-content {
            position: relative;
            top: auto;
            left: auto;
            width: 100%;
            max-width: 400px;
            color: #333;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 20px;
          }

          .donor-login-wrapper .red-shape-content h3 {
            color: #b30001;
          }

          .donor-login-wrapper .red-shape-content p {
            color: #555;
            text-align: center;
          }

          .donor-login-wrapper .red-shape-content .signup-btn {
            background-color: #b30001;
            color: white;
            margin-bottom: 10px;
          }

          .donor-login-wrapper .red-shape-content .image {
            max-width: 250px;
          }

          .donor-login-wrapper .top-right-btn {
            display: none;
          }
        }

        @media (min-width: 769px) and (max-width: 1024px) {
          .donor-login-wrapper .navbar {
            display: none;
          }

          .donor-login-wrapper .container {
            width: 350px;
            bottom: auto;
            top: 20%;
            right: 10%;
          }

          .donor-login-wrapper .container::before {
            height: 1200px;
            width: 1200px;
            top: -10%;
            right: 25%;
            transform: translate(-20%, -60%);
          }

          .donor-login-wrapper .red-shape-content {
            width: 90%;
            left: 50%;
            top: 10%;
            text-align: center;
            transform: translateX(-50%);
          }

          .donor-login-wrapper .red-shape-content h3,
          .donor-login-wrapper .red-shape-content p {
            text-align: center;
            margin: 0 auto;
          }

          .donor-login-wrapper .red-shape-content .image {
            max-width: 300px;
            margin: 20px auto 0 auto;
          }
        }

        @media (min-width: 1025px) {
          .donor-login-wrapper .navbar {
            display: none;
          }

          .donor-login-wrapper .container {
            width: 350px;
            bottom: auto;
            top: 20%;
            right: 250px;
          }

          .donor-login-wrapper .container::before {
            height: 1500px;
            width: 1500px;
            top: -10%;
            right: 48%;
            transform: translate(-20%, -60%);
          }

          .donor-login-wrapper .red-shape-content {
            width: 430px;
            left: 5%;
            top: 10%;
            text-align: center;
            transform: none;
          }

          .donor-login-wrapper .red-shape-content h3,
          .donor-login-wrapper .red-shape-content p {
            text-align: center;
            margin: 0 auto;
          }

          .donor-login-wrapper .red-shape-content .image {
            margin: 20px auto 0 auto;
          }
        }
      `}</style>

      {/* Navbar for smaller screens */}
      <nav className="navbar">
        <div className="navbar-logo">Life Connect</div>
        <div className="navbar-buttons">
          <a href="/donor/register" className="navbar-btn">Sign Up</a>
          <a href="/" className="navbar-btn">Home</a>
        </div>
      </nav>

      {/* Button linking back to the home page */}
      <button className="top-right-btn">
        <a href="/">Return to Home Page</a>
      </button>

      {/* Section for signup information and image */}
      <div className="red-shape-content">
        <h3>New here?</h3>
        <p>
          &quot;Give the gift of life with every drop you share. Become a hero—donate
          blood and inspire hope!&quot;
          <br />
          <br />
          <b>Click here to sign up and start making a difference.</b>
        </p>
        <a href="/donor/register" className="signup-btn">Sign Up</a>
        <img
          src="/images/donor_login/images1.png"
          className="image"
          alt="Blood donation illustration"
        />
      </div>

      {/* Login form container */}
      <div className="container">
        {error && <div className="error-alert">{error}</div>}

        <h2>Donor Login</h2>
        <form onSubmit={handleSubmit}>
          <label htmlFor="donor-email">Email:</label>
          <input
            type="email"
            id="donor-email"
            name="email"
            value={form.email}
            onChange={handleChange}
            placeholder="Enter your email"
            required
            disabled={isLoading}
          />

          <label htmlFor="donor-password">Password:</label>
          <input
            type="password"
            id="donor-password"
            name="password"
            value={form.password}
            onChange={handleChange}
            placeholder="Enter your password"
            required
            disabled={isLoading}
          />

          <button type="submit" disabled={isLoading}>
            {isLoading ? "Logging in…" : "Login"}
          </button>
        </form>
        <br />
        <a href="/donor/forgot-password" id="donor-fp">Forget Password</a>
      </div>
    </div>
  );
}
