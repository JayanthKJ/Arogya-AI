import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, Globe, Palette, Loader2, Check } from 'lucide-react';
import { useAppearance } from '../../hooks/useAppearance';
import { profileAPI } from '../../services/api';

export default function Preferences() {
  const { appearance, updateAppearance } = useAppearance();
  const [language, setLanguage] = useState('en');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await profileAPI.getProfile();
        if (data.language) {
          setLanguage(data.language);
        }
      } catch (err) {
        setError("Failed to load preferences.");
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const handleLanguageChange = async (e) => {
    const newLang = e.target.value;
    setLanguage(newLang);
    setSaving(true);
    setError(null);
    setSaved(false);

    try {
      await profileAPI.updateProfile({ language: newLang });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      setError("Failed to save language preference.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
        <p className="text-muted text-sm font-medium">Loading preferences...</p>
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
        <h2 className="text-xl font-bold text-foreground">Preferences</h2>
      </div>

      <div className="bg-surface rounded-xl shadow-card border border-border p-6 space-y-8">
        
        {error && (
          <div className="p-4 bg-danger/10 text-danger rounded-xl text-sm font-medium border border-danger/20">
            {error}
          </div>
        )}

        {/* Appearance Section */}
        <section>
          <div className="flex items-center gap-2 mb-4 text-foreground font-semibold">
            <Palette size={18} className="text-primary" />
            <h3>Appearance</h3>
          </div>
          
          <div className="grid grid-cols-3 gap-3">
            {['light', 'dark', 'system'].map((themeOption) => (
              <button
                key={themeOption}
                onClick={() => updateAppearance({ theme: themeOption })}
                className={`px-4 py-3 border rounded-lg text-sm font-semibold capitalize transition-all duration-200 ${
                  appearance.theme === themeOption
                    ? 'bg-primary text-primary-foreground border-primary shadow-sm'
                    : 'bg-background text-foreground border-border hover:bg-muted/10'
                }`}
              >
                {themeOption}
              </button>
            ))}
          </div>
        </section>

        <hr className="border-border" />

        {/* Language Section */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2 text-foreground font-semibold">
              <Globe size={18} className="text-primary" />
              <h3>Language</h3>
            </div>
            {saving && <Loader2 size={16} className="text-primary animate-spin" />}
            {saved && !saving && <Check size={16} className="text-primary" />}
          </div>
          
          <div className="max-w-xs">
            <select
              className="w-full px-4 py-3 border border-border bg-background text-foreground rounded-lg focus:bg-surface focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all duration-200 appearance-none cursor-pointer"
              value={language}
              onChange={handleLanguageChange}
              disabled={saving}
            >
              <option value="en">English</option>
              <option value="hi">हिंदी (Hindi)</option>
            </select>
          </div>
          <p className="text-sm text-muted mt-2">
            Choose your preferred language for the interface and responses.
          </p>
        </section>

      </div>
    </div>
  );
}
