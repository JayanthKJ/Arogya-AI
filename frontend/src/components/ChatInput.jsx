/**
 * ChatInput.jsx
 * Large, accessible input bar at the bottom of the chat.
 * - Auto-growing textarea (up to 5 lines)
 * - Enter to send, Shift+Enter for new line
 * - Disabled while the AI is loading
 *
 * Props:
 *   onSend     — (text: string) => void
 *   isLoading  — boolean
 */

import { useState, useRef, useEffect } from "react";

function SendIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="w-6 h-6"
      fill="none"
      stroke="white"
      strokeWidth={2.2}
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
    <div className="flex-shrink-0 bg-white border-t-2 border-green-100 px-4 pt-4 pb-5">

      {/* ── Input row ── */}
      <div
        className={[
          "flex items-end gap-3 bg-gray-50 rounded-2xl px-5 py-3",
          "border-2 transition-colors",
          isLoading
            ? "border-gray-200"
            : "border-green-200 focus-within:border-green-500",
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
          className="flex-1 bg-transparent resize-none outline-none text-gray-900
                     placeholder-gray-400 font-medium leading-relaxed"
          style={{ fontSize: "19px", minHeight: "34px", maxHeight: "160px" }}
        />

        {/* ── Send button ── */}
        <button
          onClick={handleSend}
          disabled={!canSend}
          aria-label="Send message"
          className={[
            "flex-shrink-0 w-13 h-13 rounded-xl flex items-center justify-center transition-all",
            "w-14 h-14",
            canSend
              ? "bg-green-800 hover:bg-green-700 active:scale-95 cursor-pointer"
              : "bg-gray-300 cursor-not-allowed",
          ].join(" ")}
        >
          {isLoading ? (
            // Spinner
            <svg
              className="w-6 h-6 animate-spin text-white"
              viewBox="0 0 24 24"
              fill="none"
              aria-label="Sending…"
            >
              <circle
                className="opacity-25"
                cx="12" cy="12" r="10"
                stroke="white" strokeWidth="3"
              />
              <path
                className="opacity-75"
                fill="white"
                d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
              />
            </svg>
          ) : (
            <SendIcon />
          )}
        </button>
      </div>

      {/* ── Hint ── */}
      <p
        className="text-center text-gray-400 font-semibold mt-3"
        style={{ fontSize: "13px" }}
        aria-hidden="true"
      >
        Press <kbd className="bg-gray-100 px-1 rounded">Enter</kbd> to send
        &nbsp;·&nbsp;
        <kbd className="bg-gray-100 px-1 rounded">Shift + Enter</kbd> for new line
      </p>
    </div>
  );
}
