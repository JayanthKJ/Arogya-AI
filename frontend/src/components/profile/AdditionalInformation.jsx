import { useState } from 'react';
import { ChevronDown, ChevronUp, Info } from 'lucide-react';

export default function AdditionalInformation() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border border-border rounded-xl bg-background overflow-hidden">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 hover:bg-muted/5 transition-colors text-left"
      >
        <div className="flex items-center gap-3 font-semibold text-foreground">
          <Info size={18} className="text-primary" />
          Additional Information
        </div>
        {isOpen ? <ChevronUp size={18} className="text-muted" /> : <ChevronDown size={18} className="text-muted" />}
      </button>

      {isOpen && (
        <div className="p-4 border-t border-border bg-surface space-y-4">
          <div className="bg-primary/10 text-primary px-4 py-3 rounded-lg text-sm font-medium flex gap-2">
            <Info size={16} className="mt-0.5 flex-shrink-0" />
            <p>
              These fields will help Arogya AI provide more personalized health responses in the future.
              (Coming soon)
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 opacity-60 pointer-events-none">
            <div>
              <label className="block text-sm font-semibold text-foreground mb-1.5 tracking-wide">Height (cm)</label>
              <input
                type="text"
                disabled
                placeholder="e.g. 175"
                className="w-full px-4 py-3 border border-border bg-background rounded-lg outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-foreground mb-1.5 tracking-wide">Weight (kg)</label>
              <input
                type="text"
                disabled
                placeholder="e.g. 70"
                className="w-full px-4 py-3 border border-border bg-background rounded-lg outline-none"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-semibold text-foreground mb-1.5 tracking-wide">Known Conditions</label>
              <input
                type="text"
                disabled
                placeholder="e.g. Hypertension"
                className="w-full px-4 py-3 border border-border bg-background rounded-lg outline-none"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
