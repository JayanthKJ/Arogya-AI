/**
 * ChatWindow.jsx
 * Scrollable message area. Renders:
 *   1. Welcome banner with quick-action chips
 *   2. All chat messages via MessageBubble
 *   3. Typing / loading indicator
 *   4. Error toast
 *
 * Props:
 *   messages   — Message[]
 *   isLoading  — boolean
 *   error      — string | null
 *   onClearError — () => void
 *   onChipClick  — (queryText: string) => void
 */

import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";
import { QUICK_CHIPS } from "../constants";

function TypingIndicator() {
  return (
    <div className="flex items-end gap-3" aria-live="polite" aria-label="Arogya AI is typing">
      {/* AI avatar */}
      <div className="w-10 h-10 rounded-full bg-green-900 flex items-center justify-center
                      text-green-300 font-bold flex-shrink-0 select-none"
           style={{ fontSize: "15px" }} aria-hidden="true">
        A
      </div>

      {/* Animated dots */}
      <div className="bg-white border-2 border-green-100 rounded-2xl rounded-bl-md px-5 py-4
                      flex gap-2 items-center">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="block w-3 h-3 rounded-full bg-green-400"
            style={{
              animation: "bounce 1.2s infinite",
              animationDelay: `${i * 0.2}s`,
            }}
            aria-hidden="true"
          />
        ))}
      </div>

      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); }
          40% { transform: translateY(-8px); }
        }
      `}</style>
    </div>
  );
}

function ErrorToast({ message, onDismiss }) {
  return (
    <div
      role="alert"
      className="flex items-start justify-between gap-3 bg-red-50
                 border-2 border-red-200 rounded-2xl px-5 py-4 mx-2"
      style={{ fontSize: "17px" }}
    >
      <p className="text-red-700 font-semibold leading-snug flex-1">
        ⚠️ {message}
      </p>
      <button
        onClick={onDismiss}
        className="text-red-400 hover:text-red-600 font-bold flex-shrink-0 leading-none"
        aria-label="Dismiss error"
        style={{ fontSize: "20px" }}
      >
        ×
      </button>
    </div>
  );
}

function WelcomeBanner({ onChipClick }) {
  return (
    <div className="bg-green-900 rounded-3xl p-7 mb-2">
      <h2 className="font-bold text-white mb-2 leading-snug" style={{ fontSize: "26px" }}>
        Namaste! How can I help you today?
      </h2>
      <p className="text-green-200 leading-relaxed" style={{ fontSize: "18px" }}>
        Ask me anything about your health, medications, diet, or general wellness.
        I am here to guide you in simple language.
      </p>

      {/* Quick-action chips */}
      <div className="flex flex-wrap gap-3 mt-5" role="list" aria-label="Quick questions">
        {QUICK_CHIPS.map((chip) => (
          <button
            key={chip.label}
            role="listitem"
            onClick={() => onChipClick(chip.query)}
            className="bg-white/10 hover:bg-white/20 border border-white/25
                       rounded-full px-5 py-2 text-white font-semibold transition-colors"
            style={{ fontSize: "16px" }}
          >
            {chip.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function ChatWindow({ messages, isLoading, error, onClearError, onChipClick }) {
  const bottomRef = useRef(null);

  // Scroll to bottom on new message or while typing
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <main
      className="flex-1 overflow-y-auto px-4 py-6 flex flex-col gap-5 bg-gray-50"
      aria-label="Chat messages"
      role="log"
    >
      <WelcomeBanner onChipClick={onChipClick} />

      {/* Messages */}
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {/* Typing indicator */}
      {isLoading && <TypingIndicator />}

      {/* Error toast */}
      {error && <ErrorToast message={error} onDismiss={onClearError} />}

      {/* Scroll anchor */}
      <div ref={bottomRef} aria-hidden="true" />
    </main>
  );
}
