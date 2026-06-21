import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";
import { QUICK_CHIPS } from "../constants";

function TypingIndicator() {
  return (
    <div className="flex items-end gap-3 w-full animate-fade-in-up" aria-live="polite" aria-label="Arogya AI is typing">
      {/* AI avatar */}
      <div className="w-9 h-9 rounded-xl bg-teal-800 flex items-center justify-center
                 text-teal-50 font-bold flex-shrink-0 select-none shadow-sm"
           style={{ fontSize: "14px" }} aria-hidden="true">
        A
      </div>

      {/* Animated dots */}
      <div className="bg-white border border-gray-100 shadow-sm rounded-2xl rounded-bl-[4px] px-4 py-3.5
                      flex gap-1.5 items-center">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="block w-2 h-2 rounded-full bg-teal-500"
            style={{
              animation: "bounce 1.4s infinite ease-in-out both",
              animationDelay: `${i * 0.16}s`,
            }}
            aria-hidden="true"
          />
        ))}
      </div>

      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); opacity: 0.3; }
          40% { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </div>
  );
}

function ErrorToast({ message, onDismiss }) {
  return (
    <div
      role="alert"
      className="flex items-start justify-between gap-3 bg-red-50/80
                 border border-red-100 rounded-2xl px-5 py-3.5 mx-2 shadow-sm animate-fade-in-up"
      style={{ fontSize: "15px" }}
    >
      <p className="text-red-700 font-medium leading-snug flex-1">
        ⚠️ {message}
      </p>
      <button
        onClick={onDismiss}
        className="text-red-400 hover:text-red-600 font-bold flex-shrink-0 leading-none transition-colors"
        aria-label="Dismiss error"
        style={{ fontSize: "18px" }}
      >
        ×
      </button>
    </div>
  );
}

function WelcomeBanner({ onChipClick }) {
  return (
    <div className="bg-gradient-to-br from-teal-800 to-teal-900 rounded-[24px] p-8 mb-2 shadow-md animate-fade-in-up border border-teal-700">
      <h2 className="font-bold text-white mb-3 leading-snug tracking-wide" style={{ fontSize: "24px" }}>
        Namaste! How can I help you today?
      </h2>
      <p className="text-teal-100/90 leading-relaxed font-medium max-w-2xl" style={{ fontSize: "15px" }}>
        Ask me anything about your health, medications, diet, or general wellness.
        I am here to guide you in simple language.
      </p>

      {/* Quick-action chips */}
      <div className="flex flex-wrap gap-2.5 mt-6" role="list" aria-label="Quick questions">
        {QUICK_CHIPS.map((chip) => (
          <button
            key={chip.label}
            role="listitem"
            onClick={() => onChipClick(chip.query)}
            className="bg-white/10 hover:bg-white/20 border border-white/20
                       rounded-full px-5 py-2.5 text-white font-medium transition-all shadow-sm
                       active:scale-95 text-sm tracking-wide"
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
      className="flex-1 overflow-y-auto px-4 py-6 md:px-8 md:py-8 flex flex-col gap-6 bg-[#FAFAFA]"
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
      <div ref={bottomRef} aria-hidden="true" className="h-4" />
    </main>
  );
}
