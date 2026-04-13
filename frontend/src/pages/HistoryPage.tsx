import { useState } from 'react';
import { History, Search, MessageSquare, ArrowRight, X } from 'lucide-react';
import { apiClient } from '../api';
import { Button, Input, Card } from '../components';
import type { ConversationSummary, Message } from '../types';
import { formatDate, truncateText } from '../utils';

interface HistoryPageProps {
  userId: string;
  conversations: ConversationSummary[];
  onSessionSelect: (sessionId: string) => void;
  onPageChange: (page: string) => void;
}

export function HistoryPage({
  userId,
  conversations,
  onSessionSelect,
  onPageChange,
}: HistoryPageProps) {
  const [searchKeyword, setSearchKeyword] = useState('');
  const [searchResults, setSearchResults] = useState<Message[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchResults, setShowSearchResults] = useState(false);

  const handleSearch = async () => {
    if (!searchKeyword.trim()) return;

    setIsSearching(true);
    setShowSearchResults(true);

    try {
      const response = await apiClient.searchConversations({
        keyword: searchKeyword,
        user_id: userId,
        limit: 20,
      });

      if (response.success) {
        setSearchResults(response.results);
      }
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleOpenConversation = (sessionId: string) => {
    onSessionSelect(sessionId);
    onPageChange('chat');
  };

  const clearSearch = () => {
    setSearchKeyword('');
    setSearchResults([]);
    setShowSearchResults(false);
  };

  return (
    <div className="h-full overflow-y-auto">
      {/* Header */}
      <div className="px-6 py-5 border-b border-apple-border bg-apple-surface">
        <h1 className="text-2xl font-bold text-apple-text flex items-center gap-2">
          <History className="w-6 h-6" />
          对话历史
        </h1>
        <p className="text-sm text-apple-text-secondary mt-1">
          查看和管理您的所有对话记录
        </p>
      </div>

      <div className="p-6 max-w-4xl mx-auto space-y-6">
        {/* Search Bar */}
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Input
              placeholder="输入关键词搜索历史对话..."
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="pr-10"
            />
            {searchKeyword && (
              <button
                onClick={clearSearch}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-apple-text-secondary hover:text-apple-text"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          <Button
            onClick={handleSearch}
            isLoading={isSearching}
            disabled={!searchKeyword.trim()}
          >
            <Search className="w-4 h-4" />
            搜索
          </Button>
        </div>

        {/* Search Results */}
        {showSearchResults ? (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-apple-text">
                搜索结果
              </h2>
              <Button variant="ghost" size="sm" onClick={clearSearch}>
                ← 返回全部会话
              </Button>
            </div>

            {searchResults.length > 0 ? (
              <div className="space-y-3">
                {searchResults.map((msg, index) => (
                  <Card key={index} className="hover:shadow-apple-lg transition-shadow">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs font-medium px-2 py-0.5 bg-apple-blue-light text-apple-blue rounded-full">
                            {msg.role === 'user' ? '用户' : '助手'}
                          </span>
                          {msg.created_at && (
                            <span className="text-xs text-apple-text-secondary">
                              {formatDate(msg.created_at)}
                            </span>
                          )}
                        </div>
                        <p className="text-apple-text">
                          {truncateText(msg.content, 200)}
                        </p>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <Card className="text-center py-12">
                <p className="text-apple-text-secondary">未找到匹配的对话</p>
              </Card>
            )}
          </div>
        ) : (
          /* All Conversations */
          <div>
            <h2 className="text-lg font-semibold text-apple-text mb-4">
              全部会话 ({conversations.length})
            </h2>

            {conversations.length > 0 ? (
              <div className="space-y-3">
                {conversations.map((conv) => (
                  <Card
                    key={conv.session_id}
                    className="flex items-center justify-between hover:shadow-apple-lg transition-shadow"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-full bg-apple-blue-light flex items-center justify-center">
                        <MessageSquare className="w-5 h-5 text-apple-blue" />
                      </div>
                      <div>
                        <p className="font-medium text-apple-text">
                          {truncateText(conv.last_message || '新会话', 50)}
                        </p>
                        <div className="flex items-center gap-3 text-sm text-apple-text-secondary mt-1">
                          <span>{conv.message_count} 条消息</span>
                          <span>·</span>
                          <span>最后更新: {formatDate(conv.updated_at)}</span>
                        </div>
                      </div>
                    </div>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleOpenConversation(conv.session_id)}
                    >
                      打开
                      <ArrowRight className="w-4 h-4" />
                    </Button>
                  </Card>
                ))}
              </div>
            ) : (
              <Card className="text-center py-12">
                <div className="w-16 h-16 rounded-full bg-apple-gray flex items-center justify-center mx-auto mb-4">
                  <History className="w-8 h-8 text-apple-text-secondary" />
                </div>
                <h3 className="text-lg font-medium text-apple-text mb-2">
                  暂无对话历史
                </h3>
                <p className="text-sm text-apple-text-secondary mb-4">
                  开始您的第一次对话吧
                </p>
                <Button onClick={() => onPageChange('chat')}>
                  开始对话
                </Button>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
