import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, setToken } from "../services/api";

const AdminLogin = () => {
  const [form, setForm] = useState({
    email: "",
    password: "",
    captcha: "",
  });
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [captchaUrl, setCaptchaUrl] = useState(`/captcha.gif?t=${Date.now()}`);
  const navigate = useNavigate();

  const refreshCaptcha = () => {
    setCaptchaUrl(`/captcha.gif?t=${Date.now()}`);
  };

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      const res = await api.adminLogin(form);
      // If backend returns redirect/success
      if (res && (res.success || res.token || !res.error)) {
        if (res.token) setToken(res.token);
        navigate("/admin/dashboard");
      } else {
        setError(res?.message || "Invalid credentials or CAPTCHA");
        refreshCaptcha();
      }
    } catch {
      setError("Server error. Try again.");
      refreshCaptcha();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="admin-login-wrapper">
      <style>{`
        .admin-login-wrapper {
          font-family: Arial, Helvetica, sans-serif;
          height: 100vh;
          width: 100vw;
          justify-content: flex-end;
          align-items: flex-end;
          display: flex;
          background-color: #f8f8f8;
          color: #333;
          position: relative;
          overflow: hidden;
          margin: 0;
          padding: 0;
        }

        /* Navbar styling for smaller screens */
        .admin-login-wrapper .navbar {
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

        .admin-login-wrapper .navbar-logo {
          color: white;
          font-size: 1.5rem;
          font-weight: bold;
        }

        .admin-login-wrapper .navbar-buttons {
          display: flex;
          gap: 10px;
        }

        .admin-login-wrapper .navbar-btn {
          color: #b30001;
          background-color: white;
          padding: 10px 15px;
          border-radius: 15px;
          text-decoration: none;
          font-weight: bold;
        }

        .admin-login-wrapper .navbar-btn:hover {
          background-color: #BF0001;
          color: white;
        }

        /* Styling for the login form container */
        .admin-login-wrapper .container {
          width: 350px;
          padding: 20px;
          border-radius: 10px;
          background-color: #fff;
          box-shadow: 0 0 10px rgba(163, 131, 131, 0.733);
          text-align: center;
          position: absolute;
          bottom: 60px;
          right: 250px;
          z-index: 2;
        }

        /* Form styling */
        .admin-login-wrapper form {
          display: flex;
          flex-direction: column;
        }

        /* Label and input styling */
        .admin-login-wrapper label,
        .admin-login-wrapper input {
          text-align: left;
          margin-bottom: 8px;
          font-weight: bolder;
        }

        .admin-login-wrapper input {
          width: 100%;
          padding: 8px;
          margin-bottom: 5px;
          border: 2px solid #b30001;
          border-radius: 10px;
          margin-top: 3px;
        }

        /* Header styling */
        .admin-login-wrapper h2 {
          padding: 10px;
          margin-bottom: 10px;
          color: #b30001;
          font-weight: bolder;
        }

        /* Button styling */
        .admin-login-wrapper button {
          padding: 10px;
          border: none;
          border-radius: 10px;
          cursor: pointer;
          background-color: #b30001;
          color: white;
          font-size: medium;
          font-weight: bold;
        }

        /* Link styling */
        .admin-login-wrapper a {
          color: #b30001;
          text-decoration: none;
          margin: 0 5px;
          display: inline-block;
          font-size: medium;
          font-weight: bold;
        }

        .admin-login-wrapper a:hover {
          text-decoration: underline;
        }

        /* Styling for return button */
        .admin-login-wrapper .top-right-btn {
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

        .admin-login-wrapper .top-right-btn a {
          color: white;
        }

        /* Styling for the background circular shape */
        .admin-login-wrapper .container::before {
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

        /* Styling for the red-shape content section */
        .admin-login-wrapper .red-shape-content {
          position: absolute;
          top: 10%;
          left: 5%;
          color: white;
          text-align: left;
          z-index: 10;
          width: 480px;
          padding: 10px;
        }

        .admin-login-wrapper .red-shape-content h3 {
          font-weight: 600;
          line-height: 1.2;
          font-size: 1.8rem;
          margin-bottom: 10px;
          text-align: left;
        }

        .admin-login-wrapper .red-shape-content p {
          font-size: 1rem;
          line-height: 1.5;
          text-align: left;
          margin-bottom: 15px;
          color: #ffe9e9;
        }

        .admin-login-wrapper .red-shape-content .signup-btn {
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

        .admin-login-wrapper .red-shape-content .signup-btn:hover {
          background-color: #0a0909;
          color: white;
        }

        .admin-login-wrapper .red-shape-content .image {
          width: 100%;
          max-width: 250px;
          margin: 20px 0 0 0;
          display: block;
          border-radius: 10px;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
        }

        .admin-login-wrapper .error-alert {
          background-color: #f8d7da;
          color: #721c24;
          padding: 10px;
          border-radius: 5px;
          margin-bottom: 15px;
          font-weight: bold;
          text-align: center;
        }

        .admin-login-wrapper .captcha-img-element {
          height: 60px;
          width: 150px;
          border: 2px solid #b30001;
          border-radius: 10px;
          margin-bottom: 10px;
          cursor: pointer;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
          .admin-login-wrapper {
            flex-direction: column;
            justify-content: center;
            align-items: center;
            overflow-x: hidden;
            overflow-y: auto;
            padding: 80px 20px 20px 20px;
          }

          .admin-login-wrapper .navbar {
            display: flex;
          }

          .admin-login-wrapper .container {
            width: 90%;
            bottom: auto;
            margin: 20px auto;
            z-index: 2;
            position: relative;
            padding: 20px;
            box-shadow: none;
            left: 0;
            right: 0;
          }

          .admin-login-wrapper .container::before {
            content: none;
          }

          .admin-login-wrapper .red-shape-content {
            display: none;
          }

          .admin-login-wrapper .top-right-btn {
            display: none;
          }
        }

        @media (min-width: 769px) and (max-width: 1024px) {
          .admin-login-wrapper .navbar {
            display: none;
          }

          .admin-login-wrapper .container {
            width: 350px;
            bottom: auto;
            top: 20%;
            right: 10%;
          }

          .admin-login-wrapper .container::before {
            height: 1200px;
            width: 1200px;
            top: -10%;
            right: 25%;
            transform: translate(-20%, -60%);
          }

          .admin-login-wrapper .red-shape-content {
            width: 90%;
            left: 50%;
            top: 10%;
            text-align: center;
            transform: translateX(-50%);
          }

          .admin-login-wrapper .red-shape-content h3,
          .admin-login-wrapper .red-shape-content p {
            text-align: center;
            margin: 0 auto;
          }

          .admin-login-wrapper .red-shape-content .image {
            max-width: 300px;
            margin: 20px auto 0 auto;
          }
        }

        @media (min-width: 1025px) {
          .admin-login-wrapper .navbar {
            display: none;
          }

          .admin-login-wrapper .container {
            width: 350px;
            bottom: auto;
            top: 20%;
            right: 250px;
          }

          .admin-login-wrapper .container::before {
            height: 1500px;
            width: 1500px;
            top: -10%;
            right: 48%;
            transform: translate(-20%, -60%);
          }

          .admin-login-wrapper .red-shape-content {
            width: 430px;
            left: 5%;
            top: 10%;
            text-align: center;
            transform: none;
          }

          .admin-login-wrapper .red-shape-content h3,
          .admin-login-wrapper .red-shape-content p {
            text-align: center;
            margin: 0 auto;
          }

          .admin-login-wrapper .red-shape-content .image {
            margin: 20px auto 0 auto;
          }
        }
      `}</style>

      {/* Navbar for smaller screens */}
      <nav className="navbar">
        <div className="navbar-logo">Life Connect</div>
        <div className="navbar-buttons">
          <a href="/admin/signup" className="navbar-btn">Sign Up</a>
          <a href="/" className="navbar-btn">Home</a>
        </div>
      </nav>

      {/* Section for new user introduction and sign-up information */}
      <div className="red-shape-content">
        <h3>New here?</h3>
        <p>
          &quot;Join our esteemed community of lifesavers and make a significant
          impact. By signing up as an admin, you become the backbone of a
          life-saving mission, ensuring every donation reaches those who need it
          most&quot;.
          <br />
          <br />
          <b>Click here to sign up and start making a difference.</b>
        </p>
        <a href="/admin/signup" className="signup-btn">Sign Up</a>
        <img
          src="/images/adminLogin/img5.png"
          className="image"
          alt="Illustration for new users"
        />
      </div>

      {/* Form Container */}
      <div className="container">
        {error && <div className="error-alert">{error}</div>}

        <h2>Admin Login</h2>
        <form onSubmit={handleSubmit}>
          <label htmlFor="email">Email:</label>
          <input
            type="email"
            id="email"
            name="email"
            value={form.email}
            onChange={handleChange}
            required
            disabled={isLoading}
          />

          <label htmlFor="password">Password:</label>
          <input
            type="password"
            id="password"
            name="password"
            value={form.password}
            onChange={handleChange}
            required
            disabled={isLoading}
          />

          <label htmlFor="captcha">Captcha:</label>
          <input
            type="text"
            id="captcha"
            name="captcha"
            value={form.captcha}
            onChange={handleChange}
            required
            disabled={isLoading}
          />

          <img
            src={captchaUrl}
            className="captcha-img-element"
            alt="Captcha Image"
            onClick={refreshCaptcha}
            title="Click to refresh Captcha"
          />

          <button type="submit" disabled={isLoading}>
            {isLoading ? "Logging in..." : "Login"}
          </button>
        </form>
        <br />
        <a href="/admin/forgot-password" id="fp">Forget Password</a>
      </div>

      <button className="top-right-btn">
        <a href="/">Return to Home Page</a>
      </button>
    </div>
  );
};

export default AdminLogin;