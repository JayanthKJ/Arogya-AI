import { useState, useCallback, useRef, useEffect } from "react";
import { sendMessage } from "../services/api";

const API_BASE = import.meta.env.VITE_API_URL || "";

/**
 * useChat — central state manager for the chat interface
 *
 * Returns:
 *   messages     — array of { id, role, text, time }
 *   isLoading    — boolean, true while awaiting AI response
 *   error        — string | null
 *   send(text)   — triggers user message + AI response cycle
 *   clearError   — resets error state
 *   clearChat    — resets session and messages
 */

function formatTime() {
  return new Date().toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function createMessage(role, text) {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    role,   // "user" | "ai"
    text,
    time: formatTime(),
  };
}

const WELCOME_MESSAGE = createMessage(
  "ai",
  "Namaste! 🙏 I am Arogya AI, your personal health companion. I can help you understand your health, answer questions about medications, diet, and general wellness. How can I help you today?"
);

function getOrCreateSessionId() {
  const existing = localStorage.getItem("sessionId");
  if (existing) return existing;
  const fresh = crypto.randomUUID();
  localStorage.setItem("sessionId", fresh);
  return fresh;
}

function loadSavedMessages() {
  try {
    const saved = localStorage.getItem("messages");
    return saved ? JSON.parse(saved) : null;
  } catch {
    return null;
  }
}

export function useChat() {
  const sessionId = useRef(getOrCreateSessionId());

  const [messages, setMessages] = useState(() => {
    const saved = loadSavedMessages();
    return saved && saved.length > 0 ? saved : [WELCOME_MESSAGE];
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // ── Persist messages to localStorage on every change ───────────────
  useEffect(() => {
    localStorage.setItem("messages", JSON.stringify(messages));
  }, [messages]);

  // ── On mount: sync from backend history (source of truth) ──────────
  useEffect(() => {
    const syncHistory = async () => {
      try {
        const res = await fetch(
          `${API_BASE}/chat/history/${sessionId.current}`
        );
        if (!res.ok) return;
        const history = await res.json(); // [{ role, content }, ...]
        if (Array.isArray(history) && history.length > 0) {
          const normalized = history.map((m) => ({
            id: `${m.role}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
            role: m.role === "assistant" ? "ai" : m.role,
            text: m.content,
            time: formatTime(),
          }));
          setMessages(normalized);
        }
        // If backend returns empty history, keep localStorage state (welcome msg or prior session)
      } catch {
        // Backend unreachable — keep localStorage state, no-op
      }
    };

    syncHistory();
  }, []); // run once on mount

  // ── Send a new message ──────────────────────────────────────────────
  const send = useCallback(
    async (text) => {
      const trimmed = text?.trim();
      if (!trimmed || isLoading) return;

      const userMessage = createMessage("user", trimmed);

      // Build the updated list synchronously inside the setter so
      // sendMessage always receives the latest state — fixes race condition.
      let updatedMessages;
      setMessages((prev) => {
        updatedMessages = [...prev, userMessage];
        return updatedMessages;
      });

      setIsLoading(true);
      setError(null);

      try {
        const reply = await sendMessage(updatedMessages, sessionId.current);
        const aiMessage = createMessage("ai", reply);
        // Functional update ensures we append to the very latest state
        setMessages((prev) => [...prev, aiMessage]);
      } catch (err) {
        console.error("[useChat] send error:", err);
        setError(
          "Sorry, I could not reach the server. Please check your connection and try again."
        );
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading]   // removed "messages" dep — state is read via functional updater
  );

  // ── Clear conversation ──────────────────────────────────────────────
  const clearChat = useCallback(() => {
    setMessages([WELCOME_MESSAGE]);
    localStorage.removeItem("messages");
    const newId = crypto.randomUUID();
    sessionId.current = newId;
    localStorage.setItem("sessionId", newId);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return { messages, isLoading, error, send, clearError, clearChat };
}
