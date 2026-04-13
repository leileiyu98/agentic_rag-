"""Memory Service - 对话历史业务服务"""

import json
from typing import List, Dict, Optional
from backend.db.repositories.memory_repo import MemoryRepository
from backend.db.models.memory import AgentMemory


class MemoryService:
    """对话历史业务服务"""

    def __init__(self, session):
        self.repo = MemoryRepository(session)

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        user_id: str = None,
        metadata: dict = None,
    ) -> Dict:
        """添加消息记录"""
        # 构建元数据
        meta = metadata or {}
        if user_id:
            meta["user_id"] = user_id

        # 创建记录
        memory = self.repo.create(
            session_id=session_id,
            role=role,
            content=content,
            msg_metadata=json.dumps(meta, ensure_ascii=False) if meta else None,
        )

        return memory.to_dict()

    def get_conversation_history(
        self, session_id: str, limit: int = 100, include_system: bool = True
    ) -> List[Dict]:
        """获取对话历史

        Args:
            session_id: 会话ID
            limit: 返回的最大消息数
            include_system: 是否包含系统消息，默认为True

        Returns:
            消息列表
        """
        memories = self.repo.get_by_session(session_id, limit)
        result = [m.to_dict() for m in memories]

        # 如果不包含系统消息，过滤掉role为system的记录
        if not include_system:
            result = [m for m in result if m.get("role") != "system"]

        return result

    def get_user_sessions(self, user_id: str, limit: int = 50) -> List[str]:
        """获取用户的所有会话ID"""
        return self.repo.get_user_sessions(user_id, limit)

    def get_user_conversations(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """获取用户的所有会话列表"""
        sessions = self.repo.get_user_sessions(user_id, limit + offset)
        conversations = []

        for session_id in sessions[offset : offset + limit]:
            stats = self.repo.get_session_stats(session_id)
            # 获取最后一条消息（最新的）
            from sqlalchemy import desc
            from backend.db.models.memory import AgentMemory

            last_message = (
                self.repo.session.query(AgentMemory)
                .filter(AgentMemory.session_id == session_id)
                .order_by(desc(AgentMemory.created_at))
                .first()
            )

            conversations.append(
                {
                    "session_id": session_id,
                    "message_count": stats["message_count"],
                    "last_message": last_message.content[:100] if last_message else "",
                    "last_role": last_message.role if last_message else "",
                    "updated_at": last_message.created_at.isoformat() if last_message else None,
                }
            )

        return conversations

    def clear_conversation(self, session_id: str) -> int:
        """清空对话历史"""
        return self.repo.clear_session(session_id)

    def search_conversations(self, query: str, user_id: str = None, limit: int = 20) -> List[Dict]:
        """搜索对话内容"""
        results = self.repo.search_by_content(query, user_id, limit)
        return [r.to_dict() for r in results]

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """清理旧的会话记录（暂不支持，需要添加时间字段）"""
        # TODO: 实现基于时间的清理
        return 0
