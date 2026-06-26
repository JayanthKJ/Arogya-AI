/**
 * Header.jsx
 * Top bar: mobile menu toggle, app identity, status indicator,
 * language toggle, and an emergency shortcut button.
 *
 * Props:
 *   onMenuClick — () => void  (toggles mobile sidebar)
 */

import { APP_NAME } from "../constants";

function HeartIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="w-5 h-5"
      fill="none"
      stroke="#86efac"
      strokeWidth={2}
      aria-hidden="true"
    >
      <path d="M12 21C12 21 3 14.5 3 8.5C3 5.42 5.42 3 8.5 3C10.24 3 11.8 3.93 12 5C12.2 3.93 13.76 3 15.5 3C18.58 3 21 5.42 21 8.5C21 14.5 12 21 12 21Z" />
    </svg>
  );
}

function MenuIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="w-6 h-6"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      aria-hidden="true"
    >
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  );
}

export default function Header({ onMenuClick }) {
  return (
    <header className="flex items-center justify-between px-5 py-4 bg-white border-b-2 border-green-100 flex-shrink-0">

      {/* ── Left: menu toggle + identity ── */}
      <div className="flex items-center gap-3">
        <button
          className="md:hidden p-1 text-green-800 rounded-lg hover:bg-green-50 transition-colors"
          onClick={onMenuClick}
          aria-label="Open sidebar menu"
        >
          <MenuIcon />
        </button>

        {/* Avatar */}
        <div
          className="w-11 h-11 rounded-full bg-green-900 flex items-center justify-center flex-shrink-0"
          aria-hidden="true"
        >
          <HeartIcon />
        </div>

        {/* Name + status */}
        <div>
          <h1 className="font-bold text-green-900 leading-tight" style={{ fontSize: "22px" }}>
            {APP_NAME}
          </h1>
          <p className="text-green-600 font-semibold flex items-center gap-1" style={{ fontSize: "14px" }}>
            <span className="inline-block w-2 h-2 rounded-full bg-green-500" aria-hidden="true" />
            Online · Ready to Help
          </p>
        </div>
      </div>

      {/* ── Right: actions ── */}
      <div className="flex items-center gap-2">
        <button
          className="hidden sm:block border-2 border-green-200 rounded-xl px-4 py-2
                     text-green-700 font-semibold hover:bg-green-50 transition-colors"
          style={{ fontSize: "16px" }}
          aria-label="Switch language to Hindi"
        >
          हिंदी
        </button>

        <button
          className="border-2 border-red-200 rounded-xl px-4 py-2
                     text-red-600 font-semibold hover:bg-red-50 transition-colors"
          style={{ fontSize: "16px" }}
          aria-label="Emergency contact"
        >
          📞 Emergency
        </button>
      </div>
    </header>
  );
}
