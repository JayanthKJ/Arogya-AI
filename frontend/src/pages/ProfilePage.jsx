import { Outlet, Link, useParams } from 'react-router-dom';
import { X } from 'lucide-react';

export default function ProfilePage() {
  const { sessionId } = useParams();
  const closeTo = sessionId ? `/chat/${sessionId}` : "/chat";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 sm:p-6 animate-fade-in-up" style={{ animationDuration: '200ms' }}>
      <div className="w-full max-w-2xl max-h-full bg-background rounded-2xl shadow-floating flex flex-col relative overflow-hidden border border-border">
        
        {/* Profile Layout Header */}
        <div className="flex items-center justify-between p-6 border-b border-border bg-surface z-10 flex-shrink-0">
          <h1 className="text-2xl font-bold text-foreground">Profile</h1>
          <Link
            to={closeTo}
            className="p-2 -mr-2 rounded-lg text-muted hover:text-foreground hover:bg-muted/10 transition-colors"
            aria-label="Close Profile and return to Chat"
            title="Return to Chat"
          >
            <X size={24} />
          </Link>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6 bg-background">
          <Outlet />
        </div>
        
      </div>
    </div>
  );
}
