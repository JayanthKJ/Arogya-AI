import { APP_NAME } from "../constants";

function HeartIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="w-5 h-5"
      fill="none"
      stroke="#5eead4" /* teal-300 */
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

export default function Header({ onMenuClick, onLogout }) {
  return (
    <header className="flex items-center justify-between px-4 md:px-6 py-3.5 bg-white border-b border-gray-100 flex-shrink-0 shadow-sm z-10 relative">
      
      {/* ── Left: menu toggle + identity ── */}
      <div className="flex items-center gap-3">
        <button
          className="md:hidden p-1.5 text-teal-800 rounded-lg hover:bg-teal-50 transition-colors"
          onClick={onMenuClick}
          aria-label="Open sidebar menu"
        >
          <MenuIcon />
        </button>

        {/* Avatar */}
        <div
          className="w-10 h-10 rounded-xl bg-teal-800 flex items-center justify-center flex-shrink-0 shadow-sm"
          aria-hidden="true"
        >
          <HeartIcon />
        </div>

        {/* Name + status */}
        <div>
          <h1
            className="font-bold text-gray-800 leading-tight tracking-wide"
            style={{ fontSize: "18px" }}
          >
            {APP_NAME}
          </h1>

          <p
            className="text-teal-600 font-medium flex items-center gap-1.5"
            style={{ fontSize: "12px" }}
          >
            <span
              className="inline-block w-2 h-2 rounded-full bg-teal-500 shadow-[0_0_8px_rgba(20,184,166,0.8)]"
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
          className="hidden sm:block border border-gray-200 rounded-xl px-4 py-2
                     text-gray-600 font-semibold hover:bg-gray-50 hover:border-gray-300 transition-all shadow-sm"
          style={{ fontSize: "14px" }}
          aria-label="Switch language to Hindi"
        >
          हिंदी
        </button>

        {/* Emergency */}
        <button
          className="border border-red-100 bg-red-50/50 rounded-xl px-3 sm:px-4 py-2
                     text-red-600 font-semibold hover:bg-red-50 hover:border-red-200 transition-all shadow-sm"
          style={{ fontSize: "14px" }}
          aria-label="Emergency contact"
        >
          📞 <span className="hidden sm:inline ml-1">Emergency</span>
        </button>

        {/* Logout */}
        {onLogout && (
          <button
            onClick={onLogout}
            className="border border-gray-200 rounded-xl px-3 sm:px-4 py-2
                       text-gray-600 font-semibold hover:bg-gray-50 hover:border-gray-300 transition-all shadow-sm"
            style={{ fontSize: "14px" }}
            aria-label="Logout"
          >
            Logout
          </button>
        )}
      </div>
    </header>
  );
}