import { Link } from 'react-router-dom';
import { ChevronLeft, Globe, Palette } from 'lucide-react';
import { useAppearance } from '../../hooks/useAppearance';

export default function Preferences() {
  const { appearance, updateAppearance } = useAppearance();

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
          <div className="flex items-center gap-2 mb-4 text-foreground font-semibold">
            <Globe size={18} className="text-primary" />
            <h3>Language</h3>
          </div>
          
          <div className="max-w-xs">
            <select
              className="w-full px-4 py-3 border border-border bg-background text-foreground rounded-lg focus:bg-surface focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all duration-200 appearance-none cursor-pointer"
              defaultValue="en"
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
