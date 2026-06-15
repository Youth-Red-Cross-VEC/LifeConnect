import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./App.css";

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

          {/* Donor Routes */}
          <Route path="/donor/login" element={<DonorLogin />} />
          <Route path="/donor/register" element={<RegisterDonor />} />
          <Route path="/donor/dashboard" element={<DonorDashboard />} />
          <Route path="/donor/new-password" element={<DonorNewPassword />} />
          <Route path="/donor/forgot-password" element={<DonorForgetPassword />} />
          <Route path="/donor/otp-validation" element={<DonorOTPValidationPage />} />
          <Route path="/donor/update-confirmation" element={<DonorDetailsUpdateConfirmation />} />
          <Route path="/donor/registration-confirmation" element={<NewDonorRegistrationConfirmation />} />
          <Route path="/donor/query" element={<QueryPageDonor />} />
          <Route path="/donor/generate-request" element={<GenerateRequests />} />

          {/* Admin Auth Routes */}
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin/signup" element={<AdminSignup />} />
          <Route path="/admin/forgot-password" element={<AdminForgetPassword />} />
          <Route path="/admin/otp-verification" element={<AdminOTPVerificationPage />} />
          <Route path="/admin/new-password" element={<AdminNewPassword />} />

          {/* Admin Dashboard Routes */}
          <Route path="/admin/dashboard" element={<AdminDashboard />} />
          <Route path="/admin/requests/expired" element={<ExpiredRequestsAdmin />} />
          <Route path="/admin/requests/expired/confirmation" element={<ExpiredRequestsUpdationConfirmation />} />
          <Route path="/admin/analytics" element={<AnalyticsAdmin />} />
          <Route path="/admin/hospitals/add" element={<AddNewHospital />} />
          <Route path="/help" element={<AdminHelp />} />
          <Route path="/admin/profile" element={<AdminProfile />} />
          <Route path="/admin/requests/closed" element={<ClosedRequestsAdmin />} />
          <Route path="/admin/requests/new" element={<NewRequestsAdmin />} />
          <Route path="/admin/requests/ongoing" element={<OngoingRequestsAdmin />} />
          <Route path="/admin/requests/approval-confirmation" element={<RequestApprovalConfirmation />} />
          <Route path="/admin/donors" element={<ManageDonorsAdmin />} />
          <Route path="/admin/donors/manage" element={<ManageEachDonorAdmin />} />
          <Route path="/admin/hospitals/manage" element={<ManageEachHospitalAdmin />} />
          <Route path="/admin/queries" element={<QueryPageAdmin />} />

          {/* Confirmation Routes */}
          <Route path="/blood-request/confirmation" element={<BloodRequestConfirmation />} />

          {/* Admin — Additional Pages */}
          <Route path="/admin/requests/declined" element={<DeclinedRequestsAdmin />} />
          <Route path="/admin/generate-certificate" element={<GenerateCertificate />} />
          <Route path="/admin/hospitals/all" element={<ManageHospitalDetails />} />
          <Route path="/admin/requests/ongoing/confirmation" element={<OngoingRequestsUpdationConfirmation />} />
          <Route path="/admin/upload-csv" element={<UploadCsvFile />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
