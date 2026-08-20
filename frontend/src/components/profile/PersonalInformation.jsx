import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, Save } from 'lucide-react';
import { MOCK_USER } from '../../constants/user';
import AdditionalInformation from './AdditionalInformation';

export default function PersonalInformation() {
  const [name, setName] = useState(MOCK_USER.name);
  const [age, setAge] = useState(MOCK_USER.age);
  const [isSaved, setIsSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    // Simulate save (frontend-only)
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2000);
  };

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
        <form onSubmit={handleSave} className="space-y-5">
          <div>
            <label className="block text-sm font-semibold text-foreground mb-1.5 tracking-wide">Full Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 border border-border bg-background rounded-lg focus:bg-surface focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all duration-200"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-foreground mb-1.5 tracking-wide">Age</label>
            <input
              type="number"
              value={age}
              onChange={(e) => setAge(e.target.value)}
              className="w-full px-4 py-3 border border-border bg-background rounded-lg focus:bg-surface focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all duration-200"
              min="0"
              required
            />
          </div>

          <AdditionalInformation />

          <div className="pt-4 flex justify-end">
            <button
              type="submit"
              className="bg-primary hover:bg-primary-hover text-primary-foreground font-semibold px-6 py-2.5 rounded-lg transition-all duration-200 shadow-sm flex items-center gap-2"
            >
              <Save size={18} />
              {isSaved ? "Saved!" : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
