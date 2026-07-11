import { useState, useEffect } from 'react';
import { Menu, X, Plus, MessageSquare, ChevronLeft, ChevronRight, Leaf } from 'lucide-react';

export default function Sidebar({ isOpen, onClose, sessions, activeSessionId, onNewChat, onSessionClick }) {
  const [isDesktopCollapsed, setIsDesktopCollapsed] = useState(() => {
    return localStorage.getItem("sidebar_collapsed") === "true";
  });

  const toggleDesktopCollapse = () => {
    const newState = !isDesktopCollapsed;
    setIsDesktopCollapsed(newState);
    localStorage.setItem("sidebar_collapsed", String(newState));
  };

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
          bg-sidebar-bg text-sidebar-fg transition-all duration-300 ease-in-out
          flex flex-col overflow-hidden shadow-xl md:shadow-none border-r border-sidebar-border
          ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
          w-[260px] ${desktopWidth}
        `}
      >
        {/* Header */}
        <div className={`p-5 flex items-center border-b border-sidebar-border min-h-[84px] ${isDesktopCollapsed ? 'justify-center' : 'justify-start'}`}>
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 bg-[#0f766e] text-white rounded-xl flex items-center justify-center flex-shrink-0 shadow-md border border-[rgba(255,255,255,0.15)] relative overflow-hidden">
              {/* Subtle inner glow effect */}
              <div className="absolute inset-0 bg-gradient-to-tr from-transparent to-[rgba(255,255,255,0.1)] pointer-events-none" />
              <Leaf size={22} strokeWidth={2.5} className="relative z-10" />
            </div>
            {!isDesktopCollapsed && (
              <div className="md:block transition-opacity duration-300">
                <h1 className="font-bold text-[19px] tracking-wide leading-tight text-sidebar-fg">Arogya AI</h1>
                <p className="text-[10px] text-sidebar-muted font-bold tracking-[0.15em] mt-0.5">HEALTH COMPANION</p>
              </div>
            )}
          </div>
          
          {/* Mobile close button */}
          {!isDesktopCollapsed && (
            <button onClick={onClose} className="md:hidden ml-auto p-1.5 text-sidebar-muted hover:text-sidebar-fg bg-sidebar-hover/50 hover:bg-sidebar-hover rounded-lg transition-colors">
              <X size={20} />
            </button>
          )}
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <button
            onClick={handleNewChatClick}
            className={`
              w-full bg-primary hover:bg-primary-hover text-primary-foreground rounded-lg p-3 
              flex items-center justify-center gap-2 transition-all shadow-sm active:scale-95
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
            <div className="text-[11px] text-sidebar-muted px-2 mb-3 mt-2 font-bold uppercase tracking-wider">
              Recent Chats
            </div>
          )}
          
          {/* Empty State */}
          {!isDesktopCollapsed && sessions.length === 0 && (
            <div className="text-center text-sidebar-muted font-medium mt-10 px-4 text-sm">
              <p>No past conversations.</p>
              <p className="mt-1">Start a new chat above!</p>
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
                  w-full flex items-center rounded-lg p-3 transition-colors duration-200
                  ${isDesktopCollapsed ? 'justify-center' : 'justify-start gap-3'}
                  ${isActive 
                    ? 'bg-sidebar-accent/50 text-sidebar-accent-fg border-l-[3px] border-l-primary rounded-l-sm' 
                    : 'text-sidebar-fg hover:bg-sidebar-hover'}
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
        <div className="p-3 border-t border-sidebar-border">
          <button
            onClick={toggleDesktopCollapse}
            className="hidden md:flex w-full items-center justify-center p-2 text-sidebar-muted hover:text-sidebar-fg hover:bg-sidebar-hover rounded-lg transition-colors"
            title={isDesktopCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isDesktopCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
          </button>
          
          {/* Mobile warning */}
          <div className="md:hidden mt-2 text-[10px] text-sidebar-muted text-center leading-tight px-2 pb-2">
            ⚠️ Arogya AI provides general guidance, not medical diagnosis.
          </div>
        </div>
      </div>
    </>
  );
}