import React, { useState, useRef, useEffect } from 'react';
import { Send, Trash2, Download, Loader2, MessageSquare } from 'lucide-react';
import { apiClient } from '../api';
import { Button, MessageBubble } from '../components';
import type { Message } from '../types';
import { exportConversation, downloadFile, cn } from '../utils';

interface ChatPageProps {
  userId: string;
  sessionId: string | undefined;
  messages: Message[];
  setSessionId: (id: string | undefined) => void;
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  onRefreshConversations: () => void;
}

export function ChatPage({
  userId,
  sessionId,
  messages,
  setSessionId,
  setMessages,
  onRefreshConversations,
}: ChatPageProps) {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Debug: log messages when they change
  useEffect(() => {
    console.log('ChatPage received messages:', messages.length, 'sessionId:', sessionId);
  }, [messages, sessionId]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      created_at: new Date().toISOString(),
    };

    setMessages([...messages, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await apiClient.chat({
        query: userMessage.content,
        user_id: userId,
        session_id: sessionId,
      });

      if (response.success) {
        setSessionId(response.session_id);
        const assistantMessage: Message = {
          role: 'assistant',
          content: response.answer,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
        onRefreshConversations();
      } else {
        const errorMessage: Message = {
          role: 'assistant',
          content: `抱歉，发生了错误：${response.error || '未知错误'}`,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } catch (error) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `抱歉，发生了错误：${error instanceof Error ? error.message : '未知错误'}`,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = async () => {
    if (!sessionId) {
      setMessages([]);
      return;
    }

    try {
      await apiClient.clearConversation({
        user_id: userId,
        session_id: sessionId,
      });
      setSessionId(undefined);
      setMessages([]);
      onRefreshConversations();
    } catch (error) {
      console.error('Failed to clear conversation:', error);
    }
  };

  const handleExport = () => {
    const content = exportConversation(messages, sessionId);
    const filename = `conversation_${sessionId || 'new'}.md`;
    downloadFile(content, filename);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-6 py-5 border-b border-apple-border bg-apple-surface">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-apple-text flex items-center gap-2">
              <MessageSquare className="w-6 h-6" />
              对话
            </h1>
            <p className="text-sm text-apple-text-secondary mt-1">
              与 AI 助手进行对话，获取基于知识库的智能回答
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={handleExport}
              disabled={messages.length === 0}
            >
              <Download className="w-4 h-4" />
              导出
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleClear}
              disabled={messages.length === 0}
            >
              <Trash2 className="w-4 h-4" />
              清除
            </Button>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-20">
              <div className="w-16 h-16 rounded-full bg-apple-blue-light flex items-center justify-center mb-4">
                <MessageSquare className="w-8 h-8 text-apple-blue" />
              </div>
              <h3 className="text-lg font-medium text-apple-text mb-2">
                开始新对话
              </h3>
              <p className="text-sm text-apple-text-secondary max-w-sm">
                输入您的问题，AI 助手将基于知识库为您提供智能回答
              </p>
            </div>
          ) : (
            <>
              {messages.map((message, index) => (
                <MessageBubble key={index} message={message} />
              ))}
              {isLoading && (
                <div className="flex items-center gap-2 text-apple-text-secondary py-4">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">AI 正在思考...</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-apple-border bg-apple-surface">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end gap-2">
            <div className="flex-1">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入您的问题..."
                rows={1}
                className={cn(
                  'w-full px-4 py-3 bg-apple-bg border border-apple-border rounded-apple-xl',
                  'focus:outline-none focus:ring-2 focus:ring-apple-blue focus:border-transparent',
                  'placeholder:text-apple-text-secondary resize-none',
                  'transition-all duration-200',
                  'min-h-[48px] max-h-[200px]'
                )}
                style={{ height: 'auto' }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = 'auto';
                  target.style.height = target.scrollHeight + 'px';
                }}
              />
            </div>
            <Button
              onClick={handleSend}
              isLoading={isLoading}
              disabled={!input.trim()}
              className="h-12 px-6"
            >
              <Send className="w-5 h-5" />
            </Button>
          </div>
          <p className="text-xs text-apple-text-secondary mt-2 text-center">
            按 Enter 发送，Shift + Enter 换行
          </p>
        </div>
      </div>
    </div>
  );
}
