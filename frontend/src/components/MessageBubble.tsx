import { cn } from '../utils';
import { Bot, User } from 'lucide-react';
import { formatDate } from '../utils';
import type { Message } from '../types';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={cn(
        'flex gap-3 mb-4',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
          isUser ? 'bg-apple-blue' : 'bg-apple-gray'
        )}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-apple-text" />
        )}
      </div>

      {/* Message Content */}
      <div className={cn('flex flex-col max-w-[80%]', isUser ? 'items-end' : 'items-start')}>
        <div
          className={cn(
            'px-4 py-3 rounded-apple-lg',
            isUser
              ? 'bg-apple-blue text-white rounded-tr-sm'
              : 'bg-apple-gray text-apple-text rounded-tl-sm'
          )}
        >
          <p className="text-[15px] leading-relaxed whitespace-pre-wrap">
            {message.content}
          </p>
        </div>
        {message.created_at && (
          <span className="text-xs text-apple-text-secondary mt-1 px-1">
            {formatDate(message.created_at)}
          </span>
        )}
      </div>
    </div>
  );
}
