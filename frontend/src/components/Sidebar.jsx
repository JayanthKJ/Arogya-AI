/**
 * Sidebar.jsx
 * Left navigation panel: branding, new chat CTA, chat history list,
 * and a safety disclaimer footer.
 *
 * Props:
 *   isOpen   — boolean (controls mobile slide-in visibility)
 *   onClose  — () => void (called when overlay is tapped on mobile)
 */

import { APP_NAME, APP_TAGLINE, CHAT_HISTORY } from "../constants";

export default function Sidebar({ isOpen, onClose }) {
  return (
    <>
      {/* Mobile backdrop overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-30 md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        className={[
          "fixed md:static inset-y-0 left-0 z-40 md:z-auto",
          "w-64 flex flex-col bg-green-900 text-white",
          "transition-transform duration-300 ease-in-out md:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full",
        ].join(" ")}
        aria-label="Sidebar navigation"
      >
        {/* ── Branding ── */}
        <div className="px-5 py-6 border-b border-white/10">
          <div className="flex items-center gap-2">
            <span className="text-green-300 text-2xl">🌿</span>
            <span className="font-bold text-white" style={{ fontSize: "22px" }}>
              {APP_NAME}
            </span>
          </div>
          <p
            className="text-green-300 mt-1 tracking-widest uppercase font-semibold"
            style={{ fontSize: "11px" }}
          >
            {APP_TAGLINE}
          </p>
        </div>

        {/* ── New Chat CTA ── */}
        <div className="px-4 py-4">
          <button
            onClick={onClose}
            className="w-full flex items-center gap-3 bg-white/10 hover:bg-white/20
                       border border-white/20 rounded-xl px-4 py-3
                       font-semibold transition-colors"
            style={{ fontSize: "18px" }}
          >
            <span className="text-xl leading-none">＋</span>
            New Conversation
          </button>
        </div>

        {/* ── History label ── */}
        <p
          className="px-5 text-green-400 uppercase tracking-widest font-bold"
          style={{ fontSize: "11px" }}
        >
          Recent Chats
        </p>

        {/* ── History list ── */}
        <nav className="flex-1 overflow-y-auto py-2" aria-label="Chat history">
          {CHAT_HISTORY.map((title, i) => (
            <button
              key={i}
              className={[
                "w-full text-left flex items-start gap-3 px-4 py-3 mx-0",
                "hover:bg-white/10 transition-colors",
                i === 0 ? "bg-white/15" : "",
              ].join(" ")}
              style={{ fontSize: "17px" }}
            >
              <span className="w-2 h-2 rounded-full bg-green-400 mt-2 flex-shrink-0 opacity-80" />
              <span className="text-white/80 leading-snug">{title}</span>
            </button>
          ))}
        </nav>

        {/* ── Footer disclaimer ── */}
        <div className="px-5 py-5 border-t border-white/10">
          <p
            className="text-white/40 text-center leading-relaxed"
            style={{ fontSize: "13px" }}
          >
            ⚠ Arogya AI provides general health guidance.
            This is not medical diagnosis.
            Consult a doctor for serious concerns.
          </p>
        </div>
      </aside>
    </>
  );
}
