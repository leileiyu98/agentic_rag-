"""Chat Routes - 对话相关 API 接口"""

from fastapi import APIRouter, HTTPException, status
from typing import List
import traceback

from backend.api.models import (
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
    Message,
    ConversationSummary,
    ConversationStats,
    DocumentInfo,
)
from backend.src.agent import (
    chat_with_agent,
    clear_conversation,
    get_conversation_history,
    list_user_conversations,
    search_conversations,
    direct_rag_query,
)

router = APIRouter(prefix="/chat", tags=["对话"])


@router.post("/", response_model=ChatResponse, summary="与 Agent 对话")
async def chat(request: ChatRequest):
    """
    与 RAG Agent 进行对话

    - 支持多轮对话（自动使用数据库持久化历史）
    - 可以指定 user_id 和 session_id 来区分不同用户和会话
    """
    try:
        result = chat_with_agent(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
        )

        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "对话失败"),
            )

        return ChatResponse(
            success=True,
            answer=result["answer"],
            user_id=result["user_id"],
            session_id=result["session_id"],
        )

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误: {str(e)}",
        )


@router.post("/history", response_model=ChatHistoryResponse, summary="获取对话历史")
async def get_chat_history(request: ChatHistoryRequest):
    """
    获取指定会话的对话历史

    - 可以获取简要格式或详细格式（含元数据）
    - 支持限制返回消息数量
    """
    try:
        result = get_conversation_history(
            user_id=request.user_id,
            session_id=request.session_id,
            limit=request.limit,
        )

        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "获取历史失败"),
            )

        # 转换消息格式
        import json

        messages = []
        for msg in result.get("messages", []):
            # metadata 是 JSON 字符串，需要解析为字典
            metadata = msg.get("metadata")
            if metadata and isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    metadata = None

            messages.append(
                Message(
                    role=msg.get("role", ""),
                    content=msg.get("content", ""),
                    created_at=msg.get("created_at"),
                    metadata=metadata,
                )
            )

        return ChatHistoryResponse(
            success=True,
            user_id=request.user_id,
            session_id=request.session_id,
            messages=messages,
        )

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误: {str(e)}",
        )


@router.get(
    "/conversations/{user_id}",
    response_model=UserConversationsResponse,
    summary="获取用户会话列表",
)
async def get_user_conversations(user_id: str, limit: int = 50, offset: int = 0):
    """
    获取指定用户的所有会话列表

    - 返回每个会话的最后一条消息和消息数量
    - 支持分页
    """
    try:
        result = list_user_conversations(user_id=user_id, limit=limit, offset=offset)

        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "获取会话列表失败"),
            )

        conversations = []
        for conv in result.get("conversations", []):
            conversations.append(
                ConversationSummary(
                    session_id=conv.get("session_id", ""),
                    last_message=conv.get("last_message", ""),
                    last_role=conv.get("last_role", ""),
                    updated_at=conv.get("updated_at"),
                    message_count=conv.get("message_count", 0),
                )
            )

        return UserConversationsResponse(
            success=True,
            user_id=user_id,
            conversations=conversations,
            total=len(conversations),
        )

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误: {str(e)}",
        )


@router.post("/clear", response_model=ClearConversationResponse, summary="清除对话历史")
async def clear_chat_history(request: ClearConversationRequest):
    """
    清除指定会话的对话历史

    - 永久删除数据库中的记录
    - 请谨慎使用
    """
    try:
        result = clear_conversation(
            user_id=request.user_id,
            session_id=request.session_id,
        )

        return ClearConversationResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误: {str(e)}",
        )


@router.post(
    "/search", response_model=SearchConversationResponse, summary="搜索对话内容"
)
async def search_chat_content(request: SearchConversationRequest):
    """
    搜索对话内容

    - 支持关键词搜索
    - 可以限定用户或会话
    """
    try:
        result = search_conversations(
            keyword=request.keyword,
            user_id=request.user_id,
            session_id=request.session_id,
            limit=request.limit,
        )

        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "搜索失败"),
            )

        messages = []
        for msg in result.get("results", []):
            messages.append(
                Message(
                    role=msg.get("role", ""),
                    content=msg.get("content", ""),
                    created_at=msg.get("created_at"),
                    metadata=msg.get("metadata"),
                )
            )

        return SearchConversationResponse(
            success=True,
            keyword=request.keyword,
            results=messages,
            total=len(messages),
        )

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误: {str(e)}",
        )


# ==================== RAG 直接查询接口 ====================


@router.post("/rag", response_model=RAGQueryResponse, summary="RAG 直接查询")
async def rag_query(request: RAGQueryRequest):
    """
    直接使用 RAG 查询（不经过 Agent 决策）

    - 直接检索知识库并生成答案
    - 返回检索到的文档和执行轨迹
    """
    try:
        result = direct_rag_query(question=request.question)

        # 转换文档格式
        docs = []
        for doc in result.get("docs", []):
            docs.append(
                DocumentInfo(
                    id=doc.get("id", ""),
                    content=doc.get("content", ""),
                    score=doc.get("score", 0.0),
                    source=doc.get("source", ""),
                    doc_type=doc.get("doc_type", ""),
                )
            )

        return RAGQueryResponse(
            success=True,
            question=result.get("question", request.question),
            answer=result.get("answer", ""),
            docs=docs,
            trace=result.get("trace"),
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误: {str(e)}",
        )
