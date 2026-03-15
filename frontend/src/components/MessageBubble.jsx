/**
 * MessageBubble.jsx
 * Renders a single chat message as a styled bubble.
 * - User messages: right-aligned, dark green background
 * - AI messages:   left-aligned, white/cream background with border
 *
 * Props:
 *   message — { id, role: "user"|"ai", text: string, time: string }
 */

function UserAvatar() {
  return (
    <div
      className="w-10 h-10 rounded-full bg-amber-400 flex items-center justify-center
                 text-green-900 font-bold flex-shrink-0 select-none"
      style={{ fontSize: "16px" }}
      aria-hidden="true"
    >
      U
    </div>
  );
}

function AIAvatar() {
  return (
    <div
      className="w-10 h-10 rounded-full bg-green-900 flex items-center justify-center
                 text-green-300 font-bold flex-shrink-0 select-none"
      style={{ fontSize: "15px" }}
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
      className={`flex items-end gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}
      role="article"
      aria-label={`${isUser ? "You" : "Arogya AI"} at ${message.time}`}
    >
      {/* Avatar */}
      {isUser ? <UserAvatar /> : <AIAvatar />}

      {/* Bubble + timestamp */}
      <div className={`flex flex-col max-w-[72%] ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={[
            "px-5 py-4 rounded-2xl leading-relaxed",
            isUser
              ? "bg-green-900 text-white rounded-br-md"
              : "bg-white text-gray-900 border-2 border-green-100 rounded-bl-md",
          ].join(" ")}
          style={{ fontSize: "18px" }}
        >
          {message.text}
        </div>

        <p
          className="text-gray-400 font-semibold mt-1 px-1"
          style={{ fontSize: "12px" }}
          aria-hidden="true"
        >
          {message.time}
        </p>
      </div>
    </div>
  );
}
