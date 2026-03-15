import { useState, useCallback } from "react";
import { sendMessage } from "../services/api";

/**
 * useChat — central state manager for the chat interface
 *
 * Returns:
 *   messages     — array of { id, role, text, time }
 *   isLoading    — boolean, true while awaiting AI response
 *   error        — string | null
 *   send(text)   — triggers user message + AI response cycle
 *   clearError   — resets error state
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

export function useChat() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const send = useCallback(
    async (text) => {
      if (!text.trim() || isLoading) return;

      const userMessage = createMessage("user", text.trim());

      // Optimistically add user message
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      try {
        // Pass the full history (including the new user message) for context
        const historyWithNew = [...messages, userMessage];
        const reply = await sendMessage(historyWithNew);

        const aiMessage = createMessage("ai", reply);
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
    [isLoading, messages]
  );

  const clearError = useCallback(() => setError(null), []);

  return { messages, isLoading, error, send, clearError };
}
