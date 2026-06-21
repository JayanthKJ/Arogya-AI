import { useNavigate, Navigate } from 'react-router-dom';
import Auth from '../components/Auth';
import { authAPI } from '../services/api';

export default function LoginPage() {
  const navigate = useNavigate();
  const isAuthenticated = authAPI.isAuthenticated();

  // If already authenticated, redirect to chat
  if (isAuthenticated) {
    return <Navigate to="/chat" replace />;
  }

  const handleAuth = async (email, password, isLogin) => {
    localStorage.removeItem("lastSessionId"); // to remove old user session
    localStorage.removeItem("activeSessionId"); // just in case it's lingering

    if (isLogin) {
      await authAPI.login(email, password);
    } else {
      await authAPI.signup(email, password);
      await authAPI.login(email, password);
    }

    navigate('/chat');
  };

  return <Auth onLogin={handleAuth} />;
}
