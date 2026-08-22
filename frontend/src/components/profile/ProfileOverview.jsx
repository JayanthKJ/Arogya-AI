import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, Settings, ChevronRight, LogOut, Loader2 } from 'lucide-react';
import { authAPI, profileAPI } from '../../services/api';

export default function ProfileOverview() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await profileAPI.getProfile();
        setProfile(data);
      } catch (err) {
        setError("Failed to load profile.");
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const handleLogout = () => {
    authAPI.logout();
    localStorage.removeItem("lastSessionId");
    navigate('/login', { replace: true });
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
        <p className="text-muted text-sm font-medium">Loading profile...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-4 bg-danger/10 text-danger rounded-xl text-sm font-medium border border-danger/20">
          {error}
        </div>
      )}
      <div className="bg-surface rounded-xl shadow-card border border-border p-6 flex items-center gap-5">
        <div className="w-16 h-16 rounded-2xl bg-primary/10 text-primary flex items-center justify-center flex-shrink-0">
          <User size={32} />
        </div>
        <div className="flex-1 min-w-0">
          {profile?.name ? (
            <h2 className="text-xl font-bold text-foreground truncate">{profile.name}</h2>
          ) : (
            <h2 className="text-xl font-bold text-muted truncate italic">Setup Profile</h2>
          )}
          <p className="text-muted text-sm truncate mt-1">{profile?.email}</p>
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
