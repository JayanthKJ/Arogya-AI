import { useState, useCallback, useRef, useEffect } from "react";
import { chatAPI, authAPI } from "../services/api";

function formatTime() {
  return new Date().toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function createMessage(role, text) {
  return {
    id: `msg-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    role, // "user" | "ai"
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

  // Persist messages to localStorage on every change
  useEffect(() => {
    localStorage.setItem("messages", JSON.stringify(messages));
  }, [messages]);

  // On mount: sync from backend history (source of truth)
  useEffect(() => {
    const syncHistory = async () => {
      try {
        const history = await chatAPI.getHistory(sessionId.current);

        if (Array.isArray(history) && history.length > 0) {
          const normalized = history.map((m) => {
            const msgDate = m.created_at ? new Date(m.created_at) : new Date();
            return {
              id: crypto.randomUUID(),
              role: m.role === "assistant" ? "ai" : "user",
              text: m.content,
              time: msgDate.toLocaleTimeString("en-IN", {
                hour: "2-digit",
                minute: "2-digit",
              }),
            };
          });
          setMessages(normalized);
        }
      } catch (err) {
        console.error("[useChat] syncHistory error:", err);
        // Error on sync (e.g., network failure or 401) – do not clear messages
      }
    };

    syncHistory();
  }, []);

  // Send a new message
  const sendMessage = useCallback(
    async (text) => {
      const trimmed = text?.trim();
      if (!trimmed || isLoading) return;

      const userMessage = createMessage("user", trimmed);

      // Use functional state update to prevent race conditions
      let updatedMessages;
      setMessages((prev) => {
        updatedMessages = [...prev, userMessage];
        return updatedMessages;
      });

      setIsLoading(true);
      setError(null);

      try {
        // Send directly as the latest message
        const response = await chatAPI.sendMessage(trimmed, sessionId.current);
        const reply = response.reply || response.message || response.content || "No response"
        const aiMessage = createMessage("ai", reply);
        setMessages((prev) => [...prev, aiMessage]);
      } catch (err) {
        console.error("[useChat] send error:", err);
        if(err.message.includes("Session expired")){
          window.location.reload();
        }
        // Do not clear chat on failure
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading]
  );

  // Clear or reset the conversation
  const clearChat = useCallback(() => {
    setMessages([WELCOME_MESSAGE]);
    localStorage.removeItem("messages");
    const newId = crypto.randomUUID();
    sessionId.current = newId;
    localStorage.setItem("sessionId", newId);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return { messages, isLoading, error, sendMessage, clearError, clearChat };
}