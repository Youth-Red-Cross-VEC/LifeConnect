import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./App.css";
import ProtectedRoute from "./components/ProtectedRoute";

// Import all pages
import Landing from "./pages/Landing";
import BloodBanks from "./pages/BloodBanks";
import BloodRequestConfirmation from "./pages/BloodRequestConfirmation";
import DonorDashboard from "./pages/DonorDashboard";
import DonorDetailsUpdateConfirmation from "./pages/DonorDetailsUpdateConfirmation";
import DonorLogin from "./pages/DonorLogin";
import DonorNewPassword from "./pages/DonorNewPassword";
import DonorForgetPassword from "./pages/DonorForgetPassword";
import DonorOTPValidationPage from "./pages/DonorOTPValidationPage";
import ExpiredRequestsAdmin from "./pages/ExpiredRequestsAdmin";
import ExpiredRequestsUpdationConfirmation from "./pages/ExpiredRequestsUpdationConfirmation";
import FetchDonors from "./pages/FetchDonors";
import AddNewHospital from "./pages/AddNewHospital";
import AdminHelp from "./pages/AdminHelp";
import AnalyticsAdmin from "./pages/AnalyticsAdmin";
import AvailableDonors from "./pages/AvailableDonors";
import AdminSignup from "./pages/AdminSignup";
import AdminLogin from "./pages/AdminLogin";
import AdminProfile from "./pages/AdminProfile";
import AdminForgetPassword from "./pages/AdminForgetPassword";
import AdminOTPVerificationPage from "./pages/AdminOTPVerificationPage";
import AdminNewPassword from "./pages/AdminNewPassword";
import ClosedRequestsAdmin from "./pages/ClosedRequestsAdmin";
import NewRequestsAdmin from "./pages/NewRequestsAdmin";
import OngoingRequestsAdmin from "./pages/OngoingRequestsAdmin";
import RequestApprovalConfirmation from "./pages/RequestApprovalConfirmation";
import ManageDonorsAdmin from "./pages/ManageDonorsAdmin";
import ManageEachDonorAdmin from "./pages/ManageEachDonorAdmin";
import ManageEachHospitalAdmin from "./pages/ManageEachHospitalAdmin";
import QueryPageAdmin from "./pages/QueryPageAdmin";
import RegisterDonor from "./pages/RegisterDonor";
import GenerateRequests from "./pages/GenerateRequests";
import NewDonorRegistrationConfirmation from "./pages/NewDonorRegistrationConfirmation";
import QueryPageDonor from "./pages/QueryPageDonor";
import DeclinedRequestsAdmin from "./pages/DeclinedRequestsAdmin";
import GenerateCertificate from "./pages/GenerateCertificate";
import ManageHospitalDetails from "./pages/ManageHospitalDetails";
import OngoingRequestsUpdationConfirmation from "./pages/OngoingRequestsUpdationConfirmation";
import UploadCsvFile from "./pages/UploadCsvFile";
import AdminDashboard from "./pages/AdminDashboard";
import AboutUs from "./pages/AboutUs";
import NotFound from "./pages/NotFound";

function App() {
  return (
    <BrowserRouter>
      <div className="w-full min-h-screen m-0 p-0 overflow-x-hidden">
        <Routes>
          {/* Main Routes */}
          <Route path="/" element={<Landing />} />
          <Route path="/blood-banks" element={<BloodBanks />} />
          <Route path="/find-donors" element={<FetchDonors />} />
          <Route path="/available-donors" element={<AvailableDonors />} />
          <Route path="/about" element={<AboutUs />} />

          {/* Donor Auth Routes (public) */}
          <Route path="/donor/login" element={<DonorLogin />} />
          <Route path="/donor/register" element={<RegisterDonor />} />
          <Route path="/donor/new-password" element={<DonorNewPassword />} />
          <Route path="/donor/forgot-password" element={<DonorForgetPassword />} />
          <Route path="/donor/otp-validation" element={<DonorOTPValidationPage />} />
          <Route path="/donor/registration-confirmation" element={<NewDonorRegistrationConfirmation />} />

          {/* Donor Protected Routes */}
          <Route path="/donor/dashboard" element={<ProtectedRoute type="donor"><DonorDashboard /></ProtectedRoute>} />
          <Route path="/donor/update-confirmation" element={<ProtectedRoute type="donor"><DonorDetailsUpdateConfirmation /></ProtectedRoute>} />
          <Route path="/donor/query" element={<ProtectedRoute type="donor"><QueryPageDonor /></ProtectedRoute>} />
          <Route path="/donor/generate-request" element={<ProtectedRoute type="donor"><GenerateRequests /></ProtectedRoute>} />

          {/* Admin Auth Routes (public) */}
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin/signup" element={<AdminSignup />} />
          <Route path="/admin/forgot-password" element={<AdminForgetPassword />} />
          <Route path="/admin/otp-verification" element={<AdminOTPVerificationPage />} />
          <Route path="/admin/new-password" element={<AdminNewPassword />} />

          {/* Admin Protected Dashboard Routes */}
          <Route path="/admin/dashboard" element={<ProtectedRoute type="admin"><AdminDashboard /></ProtectedRoute>} />
          <Route path="/admin/requests/expired" element={<ProtectedRoute type="admin"><ExpiredRequestsAdmin /></ProtectedRoute>} />
          <Route path="/admin/requests/expired/confirmation" element={<ProtectedRoute type="admin"><ExpiredRequestsUpdationConfirmation /></ProtectedRoute>} />
          <Route path="/admin/analytics" element={<ProtectedRoute type="admin"><AnalyticsAdmin /></ProtectedRoute>} />
          <Route path="/admin/hospitals/add" element={<ProtectedRoute type="admin"><AddNewHospital /></ProtectedRoute>} />
          <Route path="/help" element={<ProtectedRoute type="admin"><AdminHelp /></ProtectedRoute>} />
          <Route path="/admin/profile" element={<ProtectedRoute type="admin"><AdminProfile /></ProtectedRoute>} />
          <Route path="/admin/requests/closed" element={<ProtectedRoute type="admin"><ClosedRequestsAdmin /></ProtectedRoute>} />
          <Route path="/admin/requests/new" element={<ProtectedRoute type="admin"><NewRequestsAdmin /></ProtectedRoute>} />
          <Route path="/admin/requests/ongoing" element={<ProtectedRoute type="admin"><OngoingRequestsAdmin /></ProtectedRoute>} />
          <Route path="/admin/requests/approval-confirmation" element={<ProtectedRoute type="admin"><RequestApprovalConfirmation /></ProtectedRoute>} />
          <Route path="/admin/donors" element={<ProtectedRoute type="admin"><ManageDonorsAdmin /></ProtectedRoute>} />
          <Route path="/admin/donors/manage" element={<ProtectedRoute type="admin"><ManageEachDonorAdmin /></ProtectedRoute>} />
          <Route path="/admin/hospitals/manage" element={<ProtectedRoute type="admin"><ManageEachHospitalAdmin /></ProtectedRoute>} />
          <Route path="/admin/queries" element={<ProtectedRoute type="admin"><QueryPageAdmin /></ProtectedRoute>} />
          <Route path="/admin/requests/declined" element={<ProtectedRoute type="admin"><DeclinedRequestsAdmin /></ProtectedRoute>} />
          <Route path="/admin/generate-certificate" element={<ProtectedRoute type="admin"><GenerateCertificate /></ProtectedRoute>} />
          <Route path="/admin/hospitals/all" element={<ProtectedRoute type="admin"><ManageHospitalDetails /></ProtectedRoute>} />
          <Route path="/admin/requests/ongoing/confirmation" element={<ProtectedRoute type="admin"><OngoingRequestsUpdationConfirmation /></ProtectedRoute>} />
          <Route path="/admin/upload-csv" element={<ProtectedRoute type="admin"><UploadCsvFile /></ProtectedRoute>} />

          {/* Confirmation Routes */}
          <Route path="/blood-request/confirmation" element={<BloodRequestConfirmation />} />

          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;

