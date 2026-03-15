/**
 * App.jsx — Root component
 * Composes layout: Sidebar | Header + ChatWindow + ChatInput
 * Wires everything through the useChat hook.
 */

import { useState } from "react";
import Sidebar    from "./components/Sidebar";
import Header     from "./components/Header";
import ChatWindow from "./components/ChatWindow";
import ChatInput  from "./components/ChatInput";
import { useChat } from "./hooks/useChat";

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { messages, isLoading, error, send, clearError } = useChat();

  return (
    <div className="flex h-screen max-h-screen overflow-hidden bg-gray-50">

      {/* ── Sidebar ── */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* ── Main column ── */}
      <div className="flex flex-col flex-1 overflow-hidden">

        <Header onMenuClick={() => setSidebarOpen(true)} />

        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          error={error}
          onClearError={clearError}
          onChipClick={send}
        />

        <ChatInput
          onSend={send}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
