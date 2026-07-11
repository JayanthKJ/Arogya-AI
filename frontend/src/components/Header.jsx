import { APP_NAME } from "../constants";
import { Menu, Heart, User, Phone } from "lucide-react";
import ThemeToggle from "./ThemeToggle";

export default function Header({ onMenuClick, onLogout }) {
  return (
    <header className="flex items-center justify-between px-4 md:px-6 py-3.5 bg-surface border-b border-border flex-shrink-0 z-10 relative">
      
      {/* ── Left: menu toggle + identity ── */}
      <div className="flex items-center gap-3">
        <button
          className="md:hidden p-1.5 text-foreground rounded-lg hover:bg-background transition-colors"
          onClick={onMenuClick}
          aria-label="Open sidebar menu"
        >
          <Menu size={24} />
        </button>

        {/* Avatar */}
        <div
          className="w-10 h-10 rounded-xl bg-primary text-primary-foreground flex items-center justify-center flex-shrink-0 shadow-sm"
          aria-hidden="true"
        >
          <Heart size={20} />
        </div>

        {/* Name + status */}
        <div>
          <h1
            className="font-bold text-foreground leading-tight tracking-wide"
            style={{ fontSize: "18px" }}
          >
            {APP_NAME}
          </h1>

          <p
            className="text-primary font-medium flex items-center gap-1.5"
            style={{ fontSize: "12px" }}
          >
            <span
              className="inline-block w-2 h-2 rounded-full bg-success shadow-[0_0_8px_rgba(16,185,129,0.8)]"
              aria-hidden="true"
            />
            Online · Ready to Help
          </p>
        </div>
      </div>

      {/* ── Right: actions ── */}
      <div className="flex items-center gap-2.5">
        
        {/* Hindi toggle */}
        <button
          className="hidden sm:block border border-border rounded-lg px-4 py-2
                     text-foreground font-semibold hover:bg-muted/10 transition-colors duration-200 shadow-sm"
          style={{ fontSize: "14px" }}
          aria-label="Switch language to Hindi"
        >
          हिंदी
        </button>

        {/* Emergency */}
        <button
          className="border border-danger/20 bg-danger/10 rounded-lg px-3 sm:px-4 py-2 flex items-center gap-2
                     text-danger font-semibold hover:bg-danger/20 transition-colors shadow-sm"
          style={{ fontSize: "14px" }}
          aria-label="Emergency contact"
        >
          <Phone size={16} />
          <span className="hidden sm:inline">Emergency</span>
        </button>

        {/* Logout */}
        {onLogout && (
          <button
            onClick={onLogout}
            className="border border-border rounded-lg px-3 sm:px-4 py-2
                       text-foreground font-semibold hover:bg-muted/10 transition-colors duration-200 shadow-sm"
            style={{ fontSize: "14px" }}
            aria-label="Logout"
          >
            Logout
          </button>
        )}

        {/* Theme Toggle */}
        <ThemeToggle />

        {/* Placeholder Profile Button */}
        <button
          className="border border-border rounded-lg p-2
                     text-muted hover:text-foreground hover:bg-muted/10 transition-all duration-200 shadow-sm ml-1"
          aria-label="Profile"
          title="Profile (Coming Soon)"
        >
          <User size={20} />
        </button>
      </div>
    </header>
  );
}