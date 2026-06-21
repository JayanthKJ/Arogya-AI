import { Navigate, Outlet } from 'react-router-dom';
import { authAPI } from '../services/api';

export default function ProtectedRoute() {
  const isAuthenticated = authAPI.isAuthenticated();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
