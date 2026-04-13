import axios, { AxiosError, AxiosInstance } from 'axios';
import {
  ChatRequest,
  ChatResponse,
  ChatHistoryRequest,
  ChatHistoryResponse,
  UserConversationsResponse,
  ClearConversationRequest,
  ClearConversationResponse,
  SearchConversationRequest,
  SearchConversationResponse,
  RAGQueryRequest,
  RAGQueryResponse,
  DocumentIngestRequest,
  DocumentIngestResponse,
  DocumentStatsResponse,
  DeleteDocumentRequest,
  DeleteDocumentResponse,
  CollectionsResponse,
  HealthStatus,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 120000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 响应拦截器
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.code === 'ECONNABORTED') {
          return Promise.reject(new Error('请求超时，请稍后重试'));
        }
        if (!error.response) {
          return Promise.reject(new Error('无法连接到后端服务，请确保服务已启动'));
        }
        return Promise.reject(error);
      }
    );
  }

  // ==================== 对话相关 API ====================

  async chat(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.client.post<ChatResponse>('/chat/', request);
    return response.data;
  }

  async getConversationHistory(request: ChatHistoryRequest): Promise<ChatHistoryResponse> {
    const response = await this.client.post<ChatHistoryResponse>('/chat/history', request);
    return response.data;
  }

  async listConversations(userId: string, limit = 50, offset = 0): Promise<UserConversationsResponse> {
    const response = await this.client.get<UserConversationsResponse>(
      `/chat/conversations/${userId}`,
      { params: { limit, offset } }
    );
    return response.data;
  }

  async clearConversation(request: ClearConversationRequest): Promise<ClearConversationResponse> {
    const response = await this.client.post<ClearConversationResponse>('/chat/clear', request);
    return response.data;
  }

  async searchConversations(request: SearchConversationRequest): Promise<SearchConversationResponse> {
    const response = await this.client.post<SearchConversationResponse>('/chat/search', request);
    return response.data;
  }

  async ragQuery(request: RAGQueryRequest): Promise<RAGQueryResponse> {
    const response = await this.client.post<RAGQueryResponse>('/chat/rag', request);
    return response.data;
  }

  // ==================== 文档管理 API ====================

  async ingestDocument(request: DocumentIngestRequest): Promise<DocumentIngestResponse> {
    const response = await this.client.post<DocumentIngestResponse>('/documents/ingest', request);
    return response.data;
  }

  async uploadDocument(file: File, chunkSize: number = 1000, chunkOverlap: number = 200): Promise<DocumentIngestResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('chunk_size', chunkSize.toString());
    formData.append('chunk_overlap', chunkOverlap.toString());

    const response = await this.client.post<DocumentIngestResponse>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async getDocumentStats(): Promise<DocumentStatsResponse> {
    const response = await this.client.get<DocumentStatsResponse>('/documents/stats');
    return response.data;
  }

  async deleteDocument(request: DeleteDocumentRequest): Promise<DeleteDocumentResponse> {
    const response = await this.client.post<DeleteDocumentResponse>('/documents/delete', request);
    return response.data;
  }

  async clearCollection(collectionName: string): Promise<{ success: boolean; deleted_count: number; message: string }> {
    const response = await this.client.post<{ success: boolean; deleted_count: number; message: string }>(`/documents/clear/${collectionName}`);
    return response.data;
  }

  async getCollectionSources(collectionName: string): Promise<{ success: boolean; collection: string; sources: string[]; total: number }> {
    const response = await this.client.get<{ success: boolean; collection: string; sources: string[]; total: number }>(`/documents/sources/${collectionName}`);
    return response.data;
  }

  async listCollections(): Promise<CollectionsResponse> {
    const response = await this.client.get<CollectionsResponse>('/documents/collections');
    return response.data;
  }

  // ==================== 系统健康检查 ====================

  async healthCheck(): Promise<HealthStatus> {
    try {
      const response = await this.client.get<HealthStatus>('/health', { timeout: 5000 });
      return response.data;
    } catch {
      return { status: 'unhealthy', services: {} };
    }
  }
}

export const apiClient = new APIClient();
export default apiClient;
