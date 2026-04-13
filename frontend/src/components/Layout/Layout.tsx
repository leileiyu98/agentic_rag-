import type { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import type { ConversationSummary } from '../../types';

interface LayoutProps {
  children: ReactNode;
  currentPage: string;
  onPageChange: (page: string) => void;
  conversations: ConversationSummary[];
  currentSessionId?: string;
  onSessionSelect: (sessionId: string) => void;
  onNewChat: () => void;
  userId: string;
}

export function Layout({
  children,
  currentPage,
  onPageChange,
  conversations,
  currentSessionId,
  onSessionSelect,
  onNewChat,
  userId,
}: LayoutProps) {
  return (
    <div className="flex h-screen bg-apple-bg">
      <Sidebar
        currentPage={currentPage}
        onPageChange={onPageChange}
        conversations={conversations}
        currentSessionId={currentSessionId}
        onSessionSelect={onSessionSelect}
        onNewChat={onNewChat}
        userId={userId}
      />
      <main className="flex-1 overflow-hidden">
        {children}
      </main>
    </div>
  );
}
