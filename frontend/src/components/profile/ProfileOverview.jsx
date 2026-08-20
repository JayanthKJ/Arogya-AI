import { Link, useNavigate } from 'react-router-dom';
import { User, Settings, ChevronRight, LogOut } from 'lucide-react';
import { authAPI } from '../../services/api';
import { MOCK_USER } from '../../constants/user';

export default function ProfileOverview() {
  const navigate = useNavigate();

  const handleLogout = () => {
    authAPI.logout();
    localStorage.removeItem("lastSessionId");
    navigate('/login', { replace: true });
  };

  return (
    <div className="space-y-6">
      <div className="bg-surface rounded-xl shadow-card border border-border p-6 flex items-center gap-5">
        <div className="w-16 h-16 rounded-2xl bg-primary/10 text-primary flex items-center justify-center flex-shrink-0">
          <User size={32} />
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="text-xl font-bold text-foreground truncate">{MOCK_USER.name}</h2>
          <p className="text-muted font-medium text-sm truncate">{MOCK_USER.username}</p>
          <p className="text-muted text-sm truncate">{MOCK_USER.email}</p>
        </div>
      </div>

      <div className="bg-surface rounded-xl shadow-card border border-border overflow-hidden">
        <Link 
          to="personal-info" 
          className="flex items-center justify-between p-4 hover:bg-muted/5 transition-colors border-b border-border"
        >
          <div className="flex items-center gap-3 text-foreground font-semibold">
            <User size={20} className="text-primary" />
            Personal Information
          </div>
          <ChevronRight size={20} className="text-muted" />
        </Link>
        <Link 
          to="preferences" 
          className="flex items-center justify-between p-4 hover:bg-muted/5 transition-colors"
        >
          <div className="flex items-center gap-3 text-foreground font-semibold">
            <Settings size={20} className="text-primary" />
            Preferences
          </div>
          <ChevronRight size={20} className="text-muted" />
        </Link>
      </div>

      <button
        onClick={handleLogout}
        className="w-full bg-surface border border-danger/20 rounded-xl p-4 flex items-center justify-center gap-2 text-danger font-semibold hover:bg-danger/5 transition-colors shadow-sm"
      >
        <LogOut size={20} />
        Log out
      </button>
    </div>
  );
}
