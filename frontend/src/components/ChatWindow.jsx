import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";
import { QUICK_CHIPS } from "../constants";
import { HeartPulse } from "lucide-react";

function TypingIndicator() {
  return (
    <div className="flex items-end gap-3 w-full animate-fade-in-up" aria-live="polite" aria-label="Arogya AI is typing">
      {/* AI avatar */}
      <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center
                 text-primary-foreground font-bold flex-shrink-0 select-none shadow-sm"
           style={{ fontSize: "14px" }} aria-hidden="true">
        A
      </div>

      {/* Animated dots */}
      <div className="bg-card border border-border shadow-sm rounded-xl rounded-bl-[4px] px-4 py-3.5
                      flex gap-1.5 items-center">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="block w-2 h-2 rounded-full bg-primary/60"
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
      className="flex items-start justify-between gap-3 bg-danger/10
                 border border-danger/20 rounded-xl px-5 py-3.5 mx-2 shadow-sm animate-fade-in-up"
      style={{ fontSize: "15px" }}
    >
      <p className="text-danger font-medium leading-snug flex-1">
        ⚠️ {message}
      </p>
      <button
        onClick={onDismiss}
        className="text-danger/70 hover:text-danger font-bold flex-shrink-0 leading-none transition-colors"
        aria-label="Dismiss error"
        style={{ fontSize: "18px" }}
      >
        ×
      </button>
    </div>
  );
}

function WelcomeBanner({ onChipClick }) {
  const hour = new Date().getHours();
  let greeting = "Good Evening";
  if (hour < 12) greeting = "Good Morning";
  else if (hour < 18) greeting = "Good Afternoon";

  return (
    <div className="flex flex-col items-center justify-center max-w-2xl mx-auto text-center px-4 pt-[15vh] mb-4">
      <h2 className="font-bold text-foreground mb-2 leading-tight tracking-tight" style={{ fontSize: "32px" }}>
        {greeting} 👋
      </h2>
      <p className="text-muted font-medium mb-10" style={{ fontSize: "16px" }}>
        How are you feeling today?
      </p>

      {/* Quick-action chips */}
      <div className="flex flex-wrap justify-center gap-3" role="list" aria-label="Quick questions">
        {QUICK_CHIPS.map((chip) => (
          <button
            key={chip.label}
            role="listitem"
            onClick={() => onChipClick(chip.query)}
            className="bg-surface border border-border
                       rounded-full px-5 py-2.5 text-foreground font-medium transition-all duration-200 shadow-sm
                       hover:-translate-y-0.5 hover:shadow-md hover:bg-primary/5 hover:border-primary/20 
                       active:scale-95 text-sm tracking-wide cursor-pointer focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
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

  const [showWelcome, setShowWelcome] = useState(messages.length === 0 && !isLoading);
  const isExiting = messages.length > 0 || isLoading;

  useEffect(() => {
    if (isExiting) {
      const timer = setTimeout(() => setShowWelcome(false), 200);
      return () => clearTimeout(timer);
    } else {
      setShowWelcome(true);
    }
  }, [isExiting]);

  // Scroll to bottom on new message or while typing
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <main
      className="flex-1 overflow-y-auto px-4 py-6 md:px-8 md:py-8 flex flex-col gap-6 bg-background relative"
      aria-label="Chat messages"
      role="log"
    >
      {showWelcome && (
        <div className={`transition-all duration-200 ease-out ${isExiting ? 'opacity-0 -translate-y-2' : 'opacity-100 translate-y-0 animate-fade-in-up'}`}>
          <WelcomeBanner onChipClick={onChipClick} />
        </div>
      )}

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
