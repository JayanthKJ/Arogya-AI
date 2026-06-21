import { useState, useRef, useEffect } from "react";

function SendIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="w-5 h-5"
      fill="none"
      stroke="white"
      strokeWidth={2.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

export default function ChatInput({ onSend, isLoading }) {
  const [text, setText] = useState("");
  const textareaRef = useRef(null);

  // Auto-grow the textarea height
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [text]);

  // Focus input on mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const canSend = text.trim().length > 0 && !isLoading;

  function handleSend() {
    if (!canSend) return;
    onSend(text.trim());
    setText("");
    // Reset height after clearing
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="flex-shrink-0 bg-white border-t border-gray-100 px-4 md:px-8 pt-4 pb-6 shadow-[0_-4px_20px_-10px_rgba(0,0,0,0.05)] relative z-10">
      {/* ── Input row ── */}
      <div
        className={[
          "flex items-end gap-3 bg-gray-50/80 rounded-[20px] px-4 md:px-5 py-3 mx-auto max-w-4xl",
          "border shadow-sm transition-all duration-200 ease-in-out",
          isLoading
            ? "border-gray-200 opacity-80"
            : "border-gray-200 focus-within:border-teal-400 focus-within:ring-2 focus-within:ring-teal-100 focus-within:bg-white",
        ].join(" ")}
      >
        <textarea
          ref={textareaRef}
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          placeholder="Type your health question here…"
          aria-label="Health question input"
          className="flex-1 bg-transparent resize-none outline-none text-gray-800
                     placeholder-gray-400 font-medium leading-relaxed my-auto"
          style={{ fontSize: "16px", minHeight: "24px", maxHeight: "160px" }}
        />

        {/* ── Send button ── */}
        <button
          onClick={handleSend}
          disabled={!canSend && !isLoading}
          aria-label="Send message"
          className={[
            "flex-shrink-0 w-11 h-11 rounded-xl flex items-center justify-center transition-all duration-200",
            canSend
              ? "bg-teal-600 hover:bg-teal-500 shadow-md hover:shadow-lg active:scale-95 cursor-pointer"
              : isLoading 
              ? "bg-teal-50 cursor-not-allowed" 
              : "bg-gray-200 text-gray-400 cursor-not-allowed",
          ].join(" ")}
        >
          {isLoading ? (
            // Spinner
            <svg
              className="w-5 h-5 animate-spin text-teal-600"
              viewBox="0 0 24 24"
              fill="none"
              aria-label="Sending…"
            >
              <circle
                className="opacity-25"
                cx="12" cy="12" r="10"
                stroke="currentColor" strokeWidth="3"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
              />
            </svg>
          ) : (
            <SendIcon />
          )}
        </button>
      </div>

      {/* ── Hint ── */}
      <div className="hidden md:block">
        <p
          className="text-center text-gray-400 font-medium mt-3 tracking-wide"
          style={{ fontSize: "12px" }}
          aria-hidden="true"
        >
          Press <kbd className="bg-gray-100 px-1.5 py-0.5 rounded-md border border-gray-200">Enter</kbd> to send
          &nbsp;·&nbsp;
          <kbd className="bg-gray-100 px-1.5 py-0.5 rounded-md border border-gray-200">Shift + Enter</kbd> for new line
        </p>
      </div>
    </div>
  );
}
