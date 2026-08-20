import { useState, useEffect } from "react";
import { useParams, useNavigate, Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import ChatWindow from "../components/ChatWindow";
import ChatInput from "../components/ChatInput";
import { useChat } from "../hooks/useChat";
import { chatAPI, authAPI } from "../services/api";

export default function ChatPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [hasLoadedSessions, setHasLoadedSessions] = useState(false);

  // 1. Initial Load of Sessions
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
        setHasLoadedSessions(true);
      } catch (err) {
        console.error("[ChatPage] Failed to load sessions:", err);
        setHasLoadedSessions(true);
      }
    };
    loadSessions();
  }, []);

  // 2. Route redirection logic based on sessionId
  useEffect(() => {
    if (!hasLoadedSessions) return;

    if (!sessionId) {
      // Base /chat route
      const lastSessionId = localStorage.getItem("lastSessionId");
      if (lastSessionId && sessions.some(s => s.id === lastSessionId)) {
        navigate(`/chat/${lastSessionId}`, { replace: true });
      } else if (sessions.length > 0) {
        navigate(`/chat/${sessions[0].id}`, { replace: true });
      } else {
        const newSessionId = crypto.randomUUID();
        navigate(`/chat/${newSessionId}`, { replace: true });
      }
    } else {
      // Remember this as the last active session
      localStorage.setItem("lastSessionId", sessionId);
      
      // If the URL sessionId is not in our loaded sessions list, we add it optimistically
      // so it shows up in the sidebar. It might be a brand new session generated from a link.
      setSessions((prev) => {
        if (!prev.some(s => s.id === sessionId)) {
          return [{
            id: sessionId,
            title: "New Conversation",
            createdAt: new Date().toISOString(),
          }, ...prev];
        }
        return prev;
      });
    }
  }, [sessionId, hasLoadedSessions, sessions, navigate]);

  const activeSessionId = sessionId;

  const {
    messages,
    isLoading,
    error,
    sendMessage,
    clearError,
    clearChat,
  } = useChat(activeSessionId);

  const handleSendMessage = async (message) => {
    let currentSessionId = activeSessionId;
    if (!currentSessionId) {
      currentSessionId = crypto.randomUUID();
      navigate(`/chat/${currentSessionId}`, { replace: true });
    }

    await sendMessage(message, currentSessionId);
  };

  const handleNewChat = () => {
    const newSessionId = crypto.randomUUID();
    navigate(`/chat/${newSessionId}`);
    setSidebarOpen(false);
  };

  const handleSessionClick = (id) => {
    navigate(`/chat/${id}`);
    setSidebarOpen(false);
  };

  useEffect(() => {
    if (messages.length === 0) return;
    const firstUserMessage = messages.find((msg) => msg.role === "user");
    if (!firstUserMessage) return;

    setSessions((prev) =>
      prev.map((session) =>
        session.id === activeSessionId && session.title === "New Conversation"
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
  }, [messages, activeSessionId]);

  return (
    <div className="flex h-screen max-h-screen overflow-hidden bg-gray-50">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        sessions={sessions}
        activeSessionId={activeSessionId}
        onNewChat={handleNewChat}
        onSessionClick={handleSessionClick}
      />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header
          onMenuClick={() => setSidebarOpen(true)}
        />
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          error={error}
          onClearError={clearError}
          onChipClick={handleSendMessage}
        />
        <ChatInput
          onSend={handleSendMessage}
          isLoading={isLoading}
        />
      </div>
      
      {/* Profile Overlay */}
      <Outlet />
    </div>
  );
}
