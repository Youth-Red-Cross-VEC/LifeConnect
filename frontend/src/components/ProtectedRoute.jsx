/**
 * ProtectedRoute — Guards routes that require authentication.
 *
 * Usage:
 *   <ProtectedRoute type="admin">   — only allows logged-in admins
 *   <ProtectedRoute type="donor">   — only allows logged-in donors
 *   <ProtectedRoute>                — allows any authenticated user
 *
 * Reads session from localStorage keys set by api.js on login:
 *   lc_token      — JWT access token
 *   lc_user_type  — "admin" | "donor"
 */
import { Navigate, useLocation } from "react-router-dom";
import { getToken, getUserType } from "../services/api";

export default function ProtectedRoute({ children, type }) {
  const token = getToken();
  const userType = getUserType();
  const location = useLocation();

  // Not authenticated at all — redirect to appropriate login
  if (!token) {
    const loginPath = type === "admin" ? "/admin/login" : "/donor/login";
    return <Navigate to={loginPath} state={{ from: location }} replace />;
  }

  // Authenticated but wrong user type
  if (type === "admin" && userType !== "admin") {
    return <Navigate to="/admin/login" replace />;
  }

  if (type === "donor" && userType !== "donor") {
    return <Navigate to="/donor/login" replace />;
  }

  return children;
}
