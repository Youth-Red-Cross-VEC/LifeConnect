import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    port: 5173,
    proxy: {
      // Every request from the frontend that starts with these paths
      // is forwarded to the Flask backend — no CORS issues in development.
      '/validate_admin': 'http://localhost:5000',
      '/register_new_admin': 'http://localhost:5000',
      '/manage_forget_password_admin': 'http://localhost:5000',
      '/otp_validation_admin': 'http://localhost:5000',
      '/new_password_admin': 'http://localhost:5000',
      '/donor_login_validation': 'http://localhost:5000',
      '/register_new_donors': 'http://localhost:5000',
      '/verify_otp_and_data_injection': 'http://localhost:5000',
      '/manage_forget_password_donor': 'http://localhost:5000',
      '/new_password_donor': 'http://localhost:5000',
      '/get_donors': 'http://localhost:5000',
      '/generate_bloodRequest': 'http://localhost:5000',
      '/get_user_query': 'http://localhost:5000',
      '/modify_donor_details': 'http://localhost:5000',
      '/update_admin_details': 'http://localhost:5000',
      '/generate_and_send_certificate': 'http://localhost:5000',
      '/get_hospitals': 'http://localhost:5000',
      '/delete_hospital_details': 'http://localhost:5000',
      '/upload_donor_csv': 'http://localhost:5000',
      '/upload_hospital_csv': 'http://localhost:5000',
      '/captcha.gif': 'http://localhost:5000',
      '/get_blood_banks': 'http://localhost:5000',
      '/admin/dashboard_data': 'http://localhost:5000',
      '/admin/render_analytics_page': 'http://localhost:5000',
    },
  },
})
