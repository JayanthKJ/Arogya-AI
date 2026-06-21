import { useState } from 'react';
import { Menu, X, Plus, MessageSquare, ChevronLeft, ChevronRight } from 'lucide-react';

export default function Sidebar({ isOpen, onClose, sessions, activeSessionId, onNewChat, onSessionClick }) {
  const [isDesktopCollapsed, setIsDesktopCollapsed] = useState(false);

  // Handle clicking a session
  const handleSessionClick = (id) => {
    onSessionClick(id);
    if (onClose) onClose();
  };

  const handleNewChatClick = () => {
    onNewChat();
    if (onClose) onClose();
  };

  const desktopWidth = isDesktopCollapsed ? 'md:w-[72px]' : 'md:w-[280px]';

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/40 z-40 md:hidden backdrop-blur-sm transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Sidebar Container */}
      <div
        className={`
          fixed md:relative top-0 left-0 h-full z-50
          bg-teal-900 text-white transition-all duration-300 ease-in-out
          flex flex-col overflow-hidden shadow-xl md:shadow-none
          ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
          w-[260px] ${desktopWidth}
        `}
      >
        {/* Header */}
        <div className={`p-4 flex items-center border-b border-teal-800 min-h-[73px] ${isDesktopCollapsed ? 'justify-center' : 'justify-between'}`}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-teal-700/80 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm border border-teal-600/50">
              <span className="text-xl">🌿</span>
            </div>
            {!isDesktopCollapsed && (
              <div className="md:block">
                <h1 className="font-bold text-lg tracking-wide leading-tight">Arogya AI</h1>
                <p className="text-[10px] text-teal-300 font-medium tracking-wider">HEALTH COMPANION</p>
              </div>
            )}
          </div>
          
          {/* Mobile close button */}
          <button onClick={onClose} className="md:hidden p-1.5 text-teal-300 hover:text-white bg-teal-800 rounded-lg">
            <X size={18} />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <button
            onClick={handleNewChatClick}
            className={`
              w-full bg-teal-700 hover:bg-teal-600 rounded-xl p-3 
              flex items-center justify-center gap-2 transition-all shadow-sm
            `}
            title={isDesktopCollapsed ? "New Conversation" : undefined}
          >
            <Plus size={20} className="flex-shrink-0" />
            {!isDesktopCollapsed && <span className="font-semibold text-sm">New Chat</span>}
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
          {!isDesktopCollapsed && sessions.length > 0 && (
            <div className="text-[11px] text-teal-400/80 px-2 mb-3 mt-2 font-bold uppercase tracking-wider">
              Recent Chats
            </div>
          )}
          {sessions.map((session) => {
            const isActive = activeSessionId === session.id;
            return (
              <button
                key={session.id}
                onClick={() => handleSessionClick(session.id)}
                title={isDesktopCollapsed ? session.title : undefined}
                className={`
                  w-full flex items-center rounded-xl p-3 transition-colors duration-200
                  ${isDesktopCollapsed ? 'justify-center' : 'justify-start gap-3'}
                  ${isActive 
                    ? 'bg-teal-800 text-white shadow-sm ring-1 ring-teal-700' 
                    : 'text-teal-100 hover:bg-teal-800/50'}
                `}
              >
                <MessageSquare size={18} className="flex-shrink-0 opacity-90" />
                {!isDesktopCollapsed && (
                  <span className="text-sm truncate font-medium text-left flex-1">{session.title}</span>
                )}
              </button>
            );
          })}
        </div>

        {/* Footer / Desktop Toggle */}
        <div className="p-3 border-t border-teal-800">
          <button
            onClick={() => setIsDesktopCollapsed(!isDesktopCollapsed)}
            className="hidden md:flex w-full items-center justify-center p-2 text-teal-300 hover:text-white hover:bg-teal-800 rounded-lg transition-colors"
            title={isDesktopCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isDesktopCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
          </button>
          
          {/* Mobile warning */}
          <div className="md:hidden mt-2 text-[10px] text-teal-400/80 text-center leading-tight px-2 pb-2">
            ⚠️ Arogya AI provides general guidance, not medical diagnosis.
          </div>
        </div>
      </div>
    </>
  );
}