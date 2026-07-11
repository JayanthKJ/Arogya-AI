import { useState, useEffect, useCallback } from 'react';

const DEFAULT_APPEARANCE = {
  theme: 'system', // 'light', 'dark', or 'system'
  // Future settings can go here (e.g., fontSize, compactMode)
};

export function useAppearance() {
  const [appearance, setAppearance] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('appearance_settings');
      if (saved) {
        try {
          return { ...DEFAULT_APPEARANCE, ...JSON.parse(saved) };
        } catch {
          return DEFAULT_APPEARANCE;
        }
      }
    }
    return DEFAULT_APPEARANCE;
  });

  const updateAppearance = useCallback((updates) => {
    setAppearance((prev) => {
      const next = { ...prev, ...updates };
      localStorage.setItem('appearance_settings', JSON.stringify(next));
      return next;
    });
  }, []);

  // Apply theme to document
  useEffect(() => {
    const root = window.document.documentElement;
    let isDark = false;

    if (appearance.theme === 'system') {
      isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    } else {
      isDark = appearance.theme === 'dark';
    }

    if (isDark) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [appearance.theme]);

  // Listen for system theme changes if set to 'system'
  useEffect(() => {
    if (appearance.theme !== 'system') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e) => {
      const root = window.document.documentElement;
      if (e.matches) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [appearance.theme]);

  return { appearance, updateAppearance };
}
