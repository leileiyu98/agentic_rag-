"""API Data Models - Pydantic 请求和响应模型"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ==================== 通用响应模型 ====================


class BaseResponse(BaseModel):
    """基础响应模型"""

    success: bool = Field(..., description="操作是否成功")
    message: Optional[str] = Field(None, description="提示信息")


class ErrorResponse(BaseModel):
    """错误响应模型"""

    success: bool = False
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细错误信息")


# ==================== 聊天相关模型 ====================


class ChatRequest(BaseModel):
    """聊天请求"""

    query: str = Field(..., description="用户输入的问题", min_length=1, max_length=4000)
    user_id: str = Field(default="anonymous", description="用户ID")
    session_id: Optional[str] = Field(default="default", description="会话ID")


class ChatResponse(BaseModel):
    """聊天响应"""

    success: bool
    answer: str = Field(..., description="助手的回答")
    user_id: str
    session_id: str


class ChatHistoryRequest(BaseModel):
    """获取聊天历史请求"""

    user_id: str = Field(..., description="用户ID")
    session_id: str = Field(..., description="会话ID")
    limit: int = Field(default=50, ge=1, le=200, description="返回消息数量")
    detail: bool = Field(default=False, description="是否返回完整详情")


class Message(BaseModel):
    """消息模型"""

    model_config = {"populate_by_name": True}

    role: str = Field(..., description="角色 (user/assistant/system)")
    content: str = Field(..., description="消息内容")
    created_at: Optional[str] = Field(None, description="创建时间")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class ConversationStats(BaseModel):
    """会话统计"""

    session_id: str
    total_messages: int
    user_messages: int
    assistant_messages: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ChatHistoryResponse(BaseModel):
    """聊天历史响应"""

    success: bool
    user_id: str
    session_id: str
    messages: List[Message]
    stats: Optional[ConversationStats] = None


class ConversationSummary(BaseModel):
    """会话摘要"""

    session_id: str
    last_message: str
    last_role: str
    updated_at: Optional[str] = None
    message_count: int


class UserConversationsResponse(BaseModel):
    """用户会话列表响应"""

    success: bool
    user_id: str
    conversations: List[ConversationSummary]
    total: int


class ClearConversationRequest(BaseModel):
    """清除对话历史请求"""

    user_id: str = Field(..., description="用户ID")
    session_id: str = Field(..., description="会话ID")


class ClearConversationResponse(BaseModel):
    """清除对话历史响应"""

    success: bool
    message: str


class SearchConversationRequest(BaseModel):
    """搜索对话请求"""

    keyword: str = Field(..., description="搜索关键词", min_length=1)
    user_id: Optional[str] = Field(None, description="限定用户ID")
    session_id: Optional[str] = Field(None, description="限定会话ID")
    limit: int = Field(default=50, ge=1, le=100, description="返回数量限制")


class SearchConversationResponse(BaseModel):
    """搜索对话响应"""

    success: bool
    keyword: str
    results: List[Message]
    total: int


# ==================== RAG 直接查询模型 ====================


class RAGQueryRequest(BaseModel):
    """RAG 直接查询请求"""

    question: str = Field(..., description="问题", min_length=1, max_length=4000)


class DocumentInfo(BaseModel):
    """文档信息"""

    id: str
    content: str
    score: float
    source: str
    doc_type: str


class RAGTrace(BaseModel):
    """RAG 执行轨迹"""

    step: str
    query: Optional[str] = None
    route: Optional[str] = None
    expansion_type: Optional[str] = None
    docs_count: Optional[int] = None


class RAGQueryResponse(BaseModel):
    """RAG 直接查询响应"""

    success: bool
    question: str
    answer: str
    docs: List[DocumentInfo]
    trace: Optional[Dict[str, Any]] = None


# ==================== 文档管理模型 ====================


class DocumentIngestRequest(BaseModel):
    """文档导入请求"""

    file_path: Optional[str] = Field(None, description="单个文件路径")
    directory: Optional[str] = Field(None, description="目录路径")
    chunk_size: int = Field(default=1000, ge=100, le=5000, description="分块大小")
    chunk_overlap: int = Field(default=200, ge=0, le=1000, description="重叠大小")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="自定义元数据")


class DocumentIngestResponse(BaseModel):
    """文档导入响应"""

    success: bool
    processed_chunks: int
    stored_count: int
    errors: List[str]


class CollectionStats(BaseModel):
    """集合统计"""

    exists: bool
    name: Optional[str] = None
    count: Optional[int] = None


class DocumentStatsResponse(BaseModel):
    """文档统计响应"""

    success: bool
    collections: List[CollectionStats]


class DeleteDocumentRequest(BaseModel):
    """删除文档请求"""

    source: str = Field(..., description="文档来源路径")


class DeleteDocumentResponse(BaseModel):
    """删除文档响应"""

    success: bool
    deleted_count: int
    message: str
