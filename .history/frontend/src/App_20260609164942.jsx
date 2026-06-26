/**
 * App.jsx — Root component
 * Composes layout: Sidebar | Header + ChatWindow + ChatInput
 * Wires everything through the useChat hook.
 */

import { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import Auth from "./components/Auth";

import { useChat } from "./hooks/useChat";
import { authAPI } from "./services/api";

function App() {
  // ─────────────────────────────────────────────
  // Auth state
  // ─────────────────────────────────────────────
  const [isAuthenticated, setIsAuthenticated] = useState(
    authAPI.isAuthenticated()
  );

  // ─────────────────────────────────────────────
  // Sidebar mobile state
  // ─────────────────────────────────────────────
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // ─────────────────────────────────────────────
  // Session state
  // ─────────────────────────────────────────────
  const [sessionId, setSessionId] = useState(
    localStorage.getItem("activeSessionId") || null
  );

  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    const loadSessions = async () => {
      try {
      const backendSessions = await chatAPI.getSessions();

        const normalized = backendSessions.map((session) => ({
          id: session.session_id,
          title: session.title,
          createdAt: session.last_updated,
        }));

        setSessions(normalized);

        // Restore last active session if possible
        if (!sessionId && normalized.length > 0) {
          setSessionId(normalized[0].id);

          localStorage.setItem(
            "activeSessionId",
            normalized[0].id
          );
        }
      } catch (err) {
        console.error("[App] Failed to load sessions:", err);
      }

    };

    if (isAuthenticated) {
      loadSessions();
    }
  }, [isAuthenticated]);


  // ─────────────────────────────────────────────
  // Chat hook
  // ─────────────────────────────────────────────
  const {
    messages,
    isLoading,
    error,
    sendMessage,
    clearError,
    clearChat,
  } = useChat(sessionId);

  // ─────────────────────────────────────────────
  // Auth handlers
  // ─────────────────────────────────────────────
  const handleAuth = async (email, password, isLogin) => {
    if (isLogin) {
      await authAPI.login(email, password);
    } else {
      await authAPI.signup(email, password);
      await authAPI.login(email, password);
    }

    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    authAPI.logout();

    localStorage.removeItem("activeSessionId");

    setIsAuthenticated(false);

    const freshSessionId = crypto.randomUUID();

    localStorage.setItem("sessionId", freshSessionId);

    const freshSessions = [
      {
        id: freshSessionId,
        title: "New Conversation",
        createdAt: new Date().toISOString(),
      },
    ];

    setSessionId(freshSessionId);
    setSessions(freshSessions);
  };

  // ─────────────────────────────────────────────
  // Session handlers
  // ─────────────────────────────────────────────
  const handleNewChat = () => {
    const newSessionId = crypto.randomUUID();

    const newSession = {
      id: newSessionId,
      title: "New Conversation",
      createdAt: new Date().toISOString(),
    };

    setSessions((prev) => [newSession, ...prev]);

    setSessionId(newSessionId);

    localStorage.setItem(
      "activeSessionId",
      newSessionId
    );

    clearChat();
  };


  const handleSessionClick = (id) => {
    setSessionId(id);

    localStorage.setItem(
      "activeSessionId",
      id
    );

    // Close sidebar on mobile after selection
    setSidebarOpen(false);
  };

  // ─────────────────────────────────────────────
  // Auto-update session title from first user msg
  // ─────────────────────────────────────────────
  useEffect(() => {
    if (messages.length === 0) return;

    const firstUserMessage = messages.find(
      (msg) => msg.role === "user"
    );

    if (!firstUserMessage) return;

    setSessions((prev) =>
      prev.map((session) =>
        session.id === sessionId &&
        session.title === "New Conversation"
          ? {
              ...session,
              title:
                firstUserMessage.text.length > 30
                  ? firstUserMessage.text.slice(0, 30) + "..."
                  : firstUserMessage.text,
            }
          : session
      )
    );
  }, [messages, sessionId]);

  // ─────────────────────────────────────────────
  // Auth gate
  // ─────────────────────────────────────────────
  if (!isAuthenticated) {
    return <Auth onLogin={handleAuth} />;
  }

  // ─────────────────────────────────────────────
  // Main layout
  // ─────────────────────────────────────────────
  return (
    <div className="flex h-screen max-h-screen overflow-hidden bg-gray-50">
      {/* ── Sidebar ───────────────────────── */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        sessions={sessions}
        activeSessionId={sessionId}
        onNewChat={handleNewChat}
        onSessionClick={handleSessionClick}
      />

      {/* ── Main column ───────────────────── */}
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header
          onMenuClick={() => setSidebarOpen(true)}
          onLogout={handleLogout}
        />

        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          error={error}
          onClearError={clearError}
          onChipClick={sendMessage}
        />

        <ChatInput
          onSend={sendMessage}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}

export default App;