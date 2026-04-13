import { cn } from '../../utils';
import { MessageSquare, FileText, History, Plus, Bot } from 'lucide-react';
import type { ConversationSummary } from '../../types';
import { SessionItem } from '../SessionItem';

interface SidebarProps {
  currentPage: string;
  onPageChange: (page: string) => void;
  conversations: ConversationSummary[];
  currentSessionId?: string;
  onSessionSelect: (sessionId: string) => void;
  onNewChat: () => void;
  userId: string;
}

const navItems = [
  { id: 'chat', label: '对话', icon: MessageSquare },
  { id: 'documents', label: '文档', icon: FileText },
  { id: 'history', label: '历史', icon: History },
];

export function Sidebar({
  currentPage,
  onPageChange,
  conversations,
  currentSessionId,
  onSessionSelect,
  onNewChat,
  userId,
}: SidebarProps) {
  return (
    <aside className="w-64 h-full bg-apple-surface border-r border-apple-border flex flex-col">
      {/* Logo */}
      <div className="p-4 border-b border-apple-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-apple-blue flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-apple-text">RAG Agent</h1>
            <p className="text-xs text-apple-text-secondary">智能知识库助手</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="p-3">
        <p className="text-xs font-semibold text-apple-text-secondary uppercase tracking-wider mb-2 px-3">
          导航
        </p>
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onPageChange(item.id)}
                className={cn(
                  'w-full flex items-center gap-3 px-3 py-2.5 rounded-apple transition-all duration-200',
                  isActive
                    ? 'bg-apple-blue-light text-apple-blue font-medium'
                    : 'text-apple-text hover:bg-apple-gray'
                )}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Recent Conversations - Only show in chat page */}
      {currentPage === 'chat' && (
        <>
          <div className="px-4 py-2 border-t border-apple-border">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold text-apple-text-secondary uppercase tracking-wider">
                最近会话
              </p>
              <button
                onClick={onNewChat}
                className="flex items-center gap-1 text-xs text-apple-blue hover:text-blue-600 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                新建
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-1">
            {conversations.slice(0, 5).map((conv) => (
              <SessionItem
                key={conv.session_id}
                conversation={conv}
                isActive={currentSessionId === conv.session_id}
                onClick={() => onSessionSelect(conv.session_id)}
              />
            ))}
            {conversations.length === 0 && (
              <p className="text-xs text-apple-text-secondary text-center py-4">
                暂无会话记录
              </p>
            )}
          </div>
        </>
      )}

      {/* User Info */}
      <div className="p-4 border-t border-apple-border">
        <div className="bg-apple-gray rounded-apple p-3">
          <p className="text-xs text-apple-text-secondary">当前用户</p>
          <p className="text-sm font-medium text-apple-text truncate">{userId}</p>
        </div>
      </div>
    </aside>
  );
}
