import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import ChatPage from "./pages/ChatPage";
import NotFoundPage from "./pages/NotFoundPage";
import ProtectedRoute from "./routes/ProtectedRoute";
import ProfilePage from "./pages/ProfilePage";
import ProfileOverview from "./components/profile/ProfileOverview";
import PersonalInformation from "./components/profile/PersonalInformation";
import Preferences from "./components/profile/Preferences";
import { useAppearance } from "./hooks/useAppearance";

function App() {
  // Initialize appearance settings at root level
  useAppearance();

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/chat" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        
        {/* Protected Routes */}
        <Route element={<ProtectedRoute />}>
          <Route path="/chat" element={<ChatPage />}>
            <Route path="profile" element={<ProfilePage />}>
              <Route index element={<ProfileOverview />} />
              <Route path="personal-info" element={<PersonalInformation />} />
              <Route path="preferences" element={<Preferences />} />
            </Route>
          </Route>
          
          <Route path="/chat/:sessionId" element={<ChatPage />}>
            <Route path="profile" element={<ProfilePage />}>
              <Route index element={<ProfileOverview />} />
              <Route path="personal-info" element={<PersonalInformation />} />
              <Route path="preferences" element={<Preferences />} />
            </Route>
          </Route>
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;