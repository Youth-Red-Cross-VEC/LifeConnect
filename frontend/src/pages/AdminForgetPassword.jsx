import React from "react";

const AdminForgetPassword = ({ actionUrl }) => {
  return (
    <div className="fp-wrapper">
      <div className="container">
        <h2>Forget Password</h2>
        <p>
          Please enter your email address to receive a One-Time Password (OTP)
          for resetting your password.
        </p>

        <form action={actionUrl} method="POST">
          <label htmlFor="email">Email Address:</label>
          <input type="email" id="email" name="email" required />
          <button type="submit">Send OTP</button>
        </form>

        <p className="info-text">
          We will send the OTP to the email you provide. Please check your inbox.
        </p>

        <style jsx>{`
          .fp-wrapper {
            font-family: "Poppins", sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
          }

          .container {
            background-color: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            max-width: 400px;
            width: 100%;
            text-align: center;
          }

          h2 {
            color: #bf0001;
            font-size: 2em;
            margin-bottom: 20px;
          }

          p {
            color: #555;
            font-size: 1em;
            margin-bottom: 20px;
          }

          label {
            display: block;
            margin-bottom: 10px;
            font-weight: bold;
            text-align: left;
          }

          input {
            width: calc(100% - 20px);
            padding: 10px;
            margin-bottom: 15px;
            border: 1px solid #ccc;
            border-radius: 5px;
            font-size: 1em;
            box-sizing: border-box;
          }

          button {
            background-color: #bf0001;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: background-color 0.3s ease;
          }

          button:hover {
            background-color: #a30001;
          }

          .info-text {
            margin-top: 15px;
            font-size: 0.95em;
          }
        `}</style>
      </div>
    </div>
  );
};

export default AdminForgetPassword;