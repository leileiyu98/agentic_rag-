import { useState, useEffect, useCallback } from 'react';
import { Layout } from './components/Layout';
import { ChatPage, DocumentsPage, HistoryPage } from './pages';
import { apiClient } from './api';
import type { Message, ConversationSummary } from './types';
import { generateUserId, generateSessionId } from './utils';

function App() {
  const [currentPage, setCurrentPage] = useState('chat');
  const [userId] = useState(() => {
    const stored = localStorage.getItem('rag_user_id');
    if (stored) return stored;
    const newId = generateUserId();
    localStorage.setItem('rag_user_id', newId);
    return newId;
  });
  const [sessionId, setSessionId] = useState<string | undefined>(() => generateSessionId());
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, [userId]);

  const loadConversations = useCallback(async () => {
    try {
      console.log('Loading conversations for user:', userId);
      const response = await apiClient.listConversations(userId, 50);
      console.log('Conversations response:', response);
      if (response.success) {
        setConversations(response.conversations);
        console.log('Set conversations:', response.conversations.length);
      } else {
        console.error('Failed to load conversations:', response);
      }
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  }, [userId]);

  const handleSessionSelect = useCallback(async (selectedSessionId: string) => {
    console.log('=== Selecting session:', selectedSessionId);
    setSessionId(selectedSessionId);
    setCurrentPage('chat'); // 切换到聊天页面
    try {
      console.log('Fetching history for user:', userId, 'session:', selectedSessionId);
      const response = await apiClient.getConversationHistory({
        user_id: userId,
        session_id: selectedSessionId,
        limit: 50,
      });
      console.log('History response:', response);
      if (response.success) {
        console.log('Setting messages:', response.messages);
        setMessages(response.messages);
      } else {
        console.error('Failed to get history:', response);
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to load conversation history:', error);
      setMessages([]);
    }
  }, [userId]);

  const handleNewChat = useCallback(() => {
    // 生成新的 session_id 以确保对话隔离
    setSessionId(generateSessionId());
    setMessages([]);
  }, []);

  const renderPage = () => {
    switch (currentPage) {
      case 'chat':
        return (
          <ChatPage
            userId={userId}
            sessionId={sessionId}
            messages={messages}
            setSessionId={setSessionId}
            setMessages={setMessages}
            onRefreshConversations={loadConversations}
          />
        );
      case 'documents':
        return <DocumentsPage />;
      case 'history':
        return (
          <HistoryPage
            userId={userId}
            conversations={conversations}
            onSessionSelect={handleSessionSelect}
            onPageChange={setCurrentPage}
          />
        );
      default:
        return (
          <ChatPage
            userId={userId}
            sessionId={sessionId}
            messages={messages}
            setSessionId={setSessionId}
            setMessages={setMessages}
            onRefreshConversations={loadConversations}
          />
        );
    }
  };

  return (
    <Layout
      currentPage={currentPage}
      onPageChange={setCurrentPage}
      conversations={conversations}
      currentSessionId={sessionId}
      onSessionSelect={handleSessionSelect}
      onNewChat={handleNewChat}
      userId={userId}
    >
      {renderPage()}
    </Layout>
  );
}

export default App;
