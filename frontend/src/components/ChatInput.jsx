import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";

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

  // Global keyboard listener to automatically focus input on typing
  useEffect(() => {
    function handleGlobalKeyDown(e) {
      // Ignore if using modifier keys
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      
      // Ignore if it's not a single printable character (e.g., 'Enter', 'Backspace', 'Escape')
      if (e.key.length !== 1) return;

      // Ignore if user is already focused on an input/textarea/select or contenteditable
      const activeEl = document.activeElement;
      if (
        activeEl &&
        (activeEl.tagName === "INPUT" ||
         activeEl.tagName === "TEXTAREA" ||
         activeEl.tagName === "SELECT" ||
         activeEl.isContentEditable)
      ) {
        return;
      }

      // Ignore if user is highlighting/selecting text
      const selection = window.getSelection();
      if (selection && selection.toString().trim() !== "") return;

      // Focus the textarea and append the character
      if (textareaRef.current) {
        textareaRef.current.focus();
        setText((prev) => prev + e.key);
        e.preventDefault(); // Prevent default to avoid double-typing or page scroll
      }
    }

    window.addEventListener("keydown", handleGlobalKeyDown);
    return () => window.removeEventListener("keydown", handleGlobalKeyDown);
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
    <div className="flex-shrink-0 bg-surface border-t border-border px-4 md:px-8 pt-4 pb-6 shadow-floating relative z-10">
      {/* ── Input row ── */}
      <div
        className={[
          "flex items-end gap-3 bg-surface rounded-2xl px-4 md:px-5 py-3 mx-auto max-w-4xl",
          "border transition-all duration-200 ease-in-out shadow-sm hover:shadow-md hover:-translate-y-[1px]",
          isLoading
            ? "border-border opacity-80"
            : "border-border focus-within:border-primary focus-within:ring-4 focus-within:ring-primary/10",
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
          className="flex-1 bg-transparent resize-none outline-none text-foreground
                     placeholder:text-muted font-medium leading-relaxed my-auto"
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
              ? "bg-primary hover:bg-primary-hover text-primary-foreground shadow-md hover:shadow-lg active:scale-95 cursor-pointer"
              : isLoading 
              ? "bg-muted/10 text-primary cursor-not-allowed" 
              : "bg-muted/10 text-muted/60 cursor-not-allowed",
          ].join(" ")}
        >
          {isLoading ? (
            // Spinner
            <svg
              className="w-5 h-5 animate-spin"
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
            <Send size={20} />
          )}
        </button>
      </div>

      {/* ── Hint ── */}
      <div className="hidden md:block">
        <p
          className="text-center text-muted font-medium mt-3 tracking-wide"
          style={{ fontSize: "12px" }}
          aria-hidden="true"
        >
          Press <kbd className="bg-muted/10 px-1.5 py-0.5 rounded border border-border">Enter</kbd> to send
          &nbsp;·&nbsp;
          <kbd className="bg-muted/10 px-1.5 py-0.5 rounded border border-border">Shift + Enter</kbd> for new line
        </p>
      </div>
    </div>
  );
}
