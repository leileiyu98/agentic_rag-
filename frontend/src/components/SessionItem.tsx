import { cn } from '../utils';
import { MessageSquare, Clock } from 'lucide-react';
import type { ConversationSummary } from '../types';
import { formatRelativeTime, truncateText } from '../utils';

interface SessionItemProps {
  conversation: ConversationSummary;
  isActive?: boolean;
  onClick?: () => void;
}

export function SessionItem({ conversation, isActive, onClick }: SessionItemProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left p-3 rounded-apple-lg transition-all duration-200',
        'hover:bg-apple-gray',
        isActive && 'bg-apple-blue-light border border-apple-blue'
      )}
    >
      <div className="flex items-start gap-3">
        <div className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
          isActive ? 'bg-apple-blue' : 'bg-apple-gray'
        )}>
          <MessageSquare className={cn(
            'w-4 h-4',
            isActive ? 'text-white' : 'text-apple-text-secondary'
          )} />
        </div>
        <div className="flex-1 min-w-0">
          <p className={cn(
            'text-sm font-medium truncate',
            isActive ? 'text-apple-blue' : 'text-apple-text'
          )}>
            {truncateText(conversation.last_message || '新会话', 30)}
          </p>
          <div className="flex items-center gap-2 mt-1 text-xs text-apple-text-secondary">
            <Clock className="w-3 h-3" />
            <span>{formatRelativeTime(conversation.updated_at)}</span>
            <span>·</span>
            <span>{conversation.message_count} 条消息</span>
          </div>
        </div>
      </div>
    </button>
  );
}
