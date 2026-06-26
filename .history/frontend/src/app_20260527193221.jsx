import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import Auth from './components/Auth';
import { useChat } from './hooks/useChat';
import { authAPI } from './services/api';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(authAPI.isAuthenticated());
  const [sessionId, setSessionId] = useState(() => crypto.randomUUID());
  const [sessions, setSessions] = useState([
    { id: sessionId, title: 'New Conversation', createdAt: new Date().toISOString() }
  ]);

  const { messages, isLoading, error, sendMessage, clearError } = useChat(sessionId);

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
    setIsAuthenticated(false);
    setSessionId(crypto.randomUUID());
    setSessions([{ id: crypto.randomUUID(), title: 'New Conversation', createdAt: new Date().toISOString() }]);
  };

  const handleNewChat = () => {
    const newSessionId = crypto.randomUUID();
    const newSession = {
      id: newSessionId,
      title: 'New Conversation',
      createdAt: new Date().toISOString(),
    };
    setSessions((prev) => [newSession, ...prev]);
    setSessionId(newSessionId);
  };

  const handleSessionClick = (id) => {
    setSessionId(id);
  };

  // Update session title based on first message
  useEffect(() => {
    if (messages.length > 0) {
      const firstUserMessage = messages.find((msg) => msg.sender === 'user');
      if (firstUserMessage) {
        setSessions((prev) =>
          prev.map((session) =>
            session.id === sessionId && session.title === 'New Conversation'
              ? { ...session, title: firstUserMessage.text.slice(0, 30) + '...' }
              : session
          )
        );
      }
    }
  }, [messages, sessionId]);

  if (!isAuthenticated) {
    return <Auth onLogin={handleAuth} />;
  }

  return (
    <div className="flex h-screen bg-gray-50 relative">
      <Sidebar
        sessions={sessions}
        activeSessionId={sessionId}
        onNewChat={handleNewChat}
        onSessionClick={handleSessionClick}
      />
      
      <div className="flex-1 flex flex-col">
        <Header onLogout={handleLogout} />
        <ChatWindow messages={messages} loading={loading} />
        <ChatInput onSend={sendMessage} disabled={loading} />
      </div>
    </div>
  );
}

export default App;