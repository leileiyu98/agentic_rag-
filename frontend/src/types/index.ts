// ==================== 通用类型 ====================

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export interface ApiResponse<T = any> {
  success: boolean;
  error?: string;
  data?: T;
}

// ==================== 消息类型 ====================

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at?: string;
  metadata?: Record<string, unknown>;
}

export interface ConversationSummary {
  session_id: string;
  last_message: string;
  last_role: string;
  updated_at?: string;
  message_count: number;
}

export interface ConversationStats {
  session_id: string;
  total_messages: number;
  user_messages: number;
  assistant_messages: number;
  created_at?: string;
  updated_at?: string;
}

// ==================== 对话 API 请求/响应 ====================

export interface ChatRequest {
  query: string;
  user_id: string;
  session_id?: string;
}

export interface ChatResponse extends ApiResponse {
  answer: string;
  user_id: string;
  session_id: string;
}

export interface ChatHistoryRequest {
  user_id: string;
  session_id: string;
  limit?: number;
  detail?: boolean;
}

export interface ChatHistoryResponse extends ApiResponse {
  user_id: string;
  session_id: string;
  messages: Message[];
  stats?: ConversationStats;
}

export interface UserConversationsResponse extends ApiResponse {
  user_id: string;
  conversations: ConversationSummary[];
  total: number;
}

export interface ClearConversationRequest {
  user_id: string;
  session_id: string;
}

export interface ClearConversationResponse extends ApiResponse {
  message: string;
}

export interface SearchConversationRequest {
  keyword: string;
  user_id?: string;
  session_id?: string;
  limit?: number;
}

export interface SearchConversationResponse extends ApiResponse {
  keyword: string;
  results: Message[];
  total: number;
}

// ==================== RAG 类型 ====================

export interface DocumentInfo {
  id: string;
  content: string;
  score: number;
  source: string;
  doc_type: string;
}

export interface RAGQueryRequest {
  question: string;
}

export interface RAGQueryResponse extends ApiResponse {
  question: string;
  answer: string;
  docs: DocumentInfo[];
  trace?: unknown;
}

// ==================== 文档管理类型 ====================

export interface DocumentIngestRequest {
  file_path?: string;
  directory?: string;
  metadata?: Record<string, unknown>;
  chunk_size?: number;
  chunk_overlap?: number;
}

export interface DocumentIngestResponse extends ApiResponse {
  processed_chunks: number;
  stored_count: number;
  errors: string[];
}

export interface CollectionStats {
  exists: boolean;
  name: string;
  count?: number;
}

export interface DocumentStatsResponse extends ApiResponse {
  collections: CollectionStats[];
}

export interface DeleteDocumentRequest {
  source: string;
}

export interface DeleteDocumentResponse extends ApiResponse {
  deleted_count: number;
  message: string;
}

export interface CollectionsResponse extends ApiResponse {
  collections: string[];
  total: number;
}

// ==================== 健康检查 ====================

export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  services: {
    database?: string;
    milvus?: string;
  };
}
