import { Sun, Moon } from 'lucide-react';
import { useAppearance } from '../hooks/useAppearance';
import { useState, useEffect } from 'react';

export default function ThemeToggle() {
  const { appearance, updateAppearance } = useAppearance();
  const [mounted, setMounted] = useState(false);

  // Avoid hydration mismatch by waiting for mount
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className="w-9 h-9" aria-hidden="true" />;
  }

  // Determine effective theme
  let isDark = appearance.theme === 'dark';
  if (appearance.theme === 'system') {
    isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  const toggleTheme = () => {
    updateAppearance({ theme: isDark ? 'light' : 'dark' });
  };

  return (
    <button
      onClick={toggleTheme}
      className="border border-border rounded-lg p-2
                 text-muted hover:text-foreground hover:bg-muted/10 transition-all duration-200 shadow-sm ml-1 flex items-center justify-center
                 active:scale-95"
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
    >
      {isDark ? <Moon size={20} /> : <Sun size={20} />}
    </button>
  );
}
