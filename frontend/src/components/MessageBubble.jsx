/**
 * MessageBubble.jsx
 * Renders a single chat message as a styled bubble.
 * - User messages: right-aligned, primary background
 * - AI messages: left-aligned, card background with soft shadow
 */

function UserAvatar() {
  return (
    <div
      className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center
                 text-primary font-bold flex-shrink-0 select-none border border-primary/20"
      style={{ fontSize: "14px" }}
      aria-hidden="true"
    >
      U
    </div>
  );
}

function AIAvatar() {
  return (
    <div
      className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center
                 text-primary-foreground font-bold flex-shrink-0 select-none shadow-sm"
      style={{ fontSize: "14px" }}
      aria-hidden="true"
    >
      A
    </div>
  );
}

export default function MessageBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex items-end gap-3 w-full animate-fade-in-up ${isUser ? "flex-row-reverse" : "flex-row"}`}
      role="article"
      aria-label={`${isUser ? "You" : "Arogya AI"} at ${message.time}`}
    >
      {/* Avatar */}
      {isUser ? <UserAvatar /> : <AIAvatar />}

      {/* Bubble + timestamp */}
      <div className={`flex flex-col max-w-[85%] md:max-w-[70%] ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={[
            "px-6 py-4 leading-relaxed shadow-sm transition-all duration-200",
            isUser
              ? "bg-primary text-primary-foreground rounded-2xl rounded-br-[4px]"
              : "bg-card text-foreground border border-border rounded-2xl rounded-bl-[4px]",
          ].join(" ")}
          style={{ fontSize: "15px", letterSpacing: "0.2px" }}
        >
          {message.text}
        </div>

        <p
          className="text-muted font-medium mt-1.5 px-1 tracking-wide"
          style={{ fontSize: "11px" }}
          aria-hidden="true"
        >
          {message.time}
        </p>
      </div>
    </div>
  );
}
