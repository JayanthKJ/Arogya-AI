import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, Save, Loader2 } from 'lucide-react';
import { profileAPI } from '../../services/api';
import AdditionalInformation from './AdditionalInformation';

export default function PersonalInformation() {
  const [name, setName] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await profileAPI.getProfile();
        setName(data.name || '');
        setDateOfBirth(data.date_of_birth || '');
      } catch (err) {
        setError("Failed to load profile.");
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setIsSaved(false);

    try {
      const updateData = {};
      if (name.trim()) updateData.name = name.trim();
      if (dateOfBirth) updateData.date_of_birth = dateOfBirth;

      await profileAPI.updateProfile(updateData);
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 2000);
    } catch (err) {
      setError(err.message || "Failed to save profile.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
        <p className="text-muted text-sm font-medium">Loading personal info...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <Link 
          to=".."
          relative="path"
          className="p-2 -ml-2 rounded-lg text-muted hover:text-foreground hover:bg-muted/10 transition-colors"
          aria-label="Back to Profile"
        >
          <ChevronLeft size={24} />
        </Link>
        <h2 className="text-xl font-bold text-foreground">Personal Information</h2>
      </div>

      <div className="bg-surface rounded-xl shadow-card border border-border p-6">
        {error && (
          <div className="p-4 mb-4 bg-danger/10 text-danger rounded-xl text-sm font-medium border border-danger/20">
            {error}
          </div>
        )}
        <form onSubmit={handleSave} className="space-y-5">
          <div>
            <label className="block text-sm font-semibold text-foreground mb-1.5 tracking-wide">Full Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 border border-border bg-background text-foreground rounded-lg focus:bg-surface focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all duration-200"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-foreground mb-1.5 tracking-wide">Date of Birth</label>
            <input
              type="date"
              value={dateOfBirth}
              onChange={(e) => setDateOfBirth(e.target.value)}
              className="w-full px-4 py-3 border border-border bg-background text-foreground rounded-lg focus:bg-surface focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all duration-200"
              max={new Date().toISOString().split("T")[0]}
              required
            />
          </div>

          <AdditionalInformation />

          <div className="pt-4 flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="bg-primary hover:bg-primary-hover text-primary-foreground font-semibold px-6 py-2.5 rounded-lg transition-all duration-200 shadow-sm flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save size={18} />
                  {isSaved ? "Saved!" : "Save Changes"}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
