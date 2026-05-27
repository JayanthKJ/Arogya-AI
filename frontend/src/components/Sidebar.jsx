import { useState } from 'react';
import { Menu, X, Plus } from 'lucide-react';

export default function Sidebar({ sessions, activeSessionId, onNewChat, onSessionClick }) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <>
      {/* Sidebar */}
      <div
        className={`${
          isCollapsed ? 'w-0' : 'w-64'
        } bg-gradient-to-b from-green-800 to-green-900 text-white transition-all duration-300 flex flex-col overflow-hidden`}
      >
        <div className="p-4 flex items-center justify-between border-b border-green-700">
          {!isCollapsed && (
            <>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center">
                  <span className="text-xl">🌿</span>
                </div>
                <div>
                  <h1 className="font-semibold">Arogya AI</h1>
                  <p className="text-xs text-green-300">YOUR HEALTH COMPANION</p>
                </div>
              </div>
            </>
          )}
        </div>

        {!isCollapsed && (
          <>
            <button
              onClick={onNewChat}
              className="m-4 bg-green-700 hover:bg-green-600 rounded-lg p-3 flex items-center justify-center gap-2 transition-colors"
            >
              <Plus size={20} />
              <span>New Conversation</span>
            </button>

            <div className="flex-1 overflow-y-auto px-2">
              <div className="text-xs text-green-400 px-3 mb-2 font-semibold">RECENT CHATS</div>
              {sessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => onSessionClick(session.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg mb-1 transition-colors ${
                    activeSessionId === session.id
                      ? 'bg-green-700'
                      : 'hover:bg-green-800'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                    <span className="text-sm truncate">{session.title}</span>
                  </div>
                </button>
              ))}
            </div>

            <div className="p-4 border-t border-green-700 text-xs text-green-300">
              ⚠️ Arogya AI provides general health guidance. This is not medical diagnosis. Consult a doctor for serious concerns.
            </div>
          </>
        )}
      </div>

      {/* Toggle Button */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute top-4 left-4 z-50 bg-green-700 hover:bg-green-600 text-white p-2 rounded-lg transition-colors shadow-lg"
        style={{ left: isCollapsed ? '16px' : '272px' }}
      >
        {isCollapsed ? <Menu size={20} /> : <X size={20} />}
      </button>
    </>
  );
}