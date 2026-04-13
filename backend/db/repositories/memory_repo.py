"""Memory Repository - 对话历史数据访问"""

from typing import List, Optional
from sqlalchemy import desc
from backend.db.repositories.base import BaseRepository
from backend.db.models.memory import AgentMemory


class MemoryRepository(BaseRepository[AgentMemory]):
    """对话历史仓库"""

    def __init__(self, session):
        super().__init__(session, AgentMemory)

    def get_by_session(self, session_id: str, limit: int = 100) -> List[AgentMemory]:
        """获取指定会话的历史记录 - 按时间正序"""
        return (
            self.session.query(AgentMemory)
            .filter(AgentMemory.session_id == session_id)
            .order_by(AgentMemory.created_at)
            .limit(limit)
            .all()
        )

    def get_user_sessions(self, user_id: str, limit: int = 50) -> List[str]:
        """获取用户的所有会话ID - 按最近活动时间排序"""
        # 子查询：获取每个会话的最后一条消息时间
        from sqlalchemy import func

        subquery = (
            self.session.query(
                AgentMemory.session_id,
                func.max(AgentMemory.created_at).label("last_activity"),
            )
            .filter(AgentMemory.msg_metadata.contains(f'"user_id": "{user_id}"'))
            .group_by(AgentMemory.session_id)
            .subquery()
        )

        # 主查询：按最后活动时间倒序获取会话ID
        results = (
            self.session.query(subquery.c.session_id)
            .order_by(desc(subquery.c.last_activity))
            .limit(limit)
            .all()
        )
        return [r[0] for r in results]

    def clear_session(self, session_id: str) -> int:
        """清空指定会话的历史记录"""
        count = (
            self.session.query(AgentMemory)
            .filter(AgentMemory.session_id == session_id)
            .delete()
        )
        self.session.commit()
        return count

    def search_by_content(
        self, query: str, user_id: str = None, limit: int = 20
    ) -> List[AgentMemory]:
        """搜索对话内容"""
        q = self.session.query(AgentMemory).filter(AgentMemory.content.contains(query))
        if user_id:
            q = q.filter(AgentMemory.msg_metadata.contains(f'"user_id": "{user_id}"'))
        return q.order_by(desc(AgentMemory.created_at)).limit(limit).all()

    def get_session_stats(self, session_id: str) -> dict:
        """获取会话统计信息"""
        messages = self.get_by_session(session_id)
        return {
            "message_count": len(messages),
            "user_messages": len([m for m in messages if m.role == "user"]),
            "assistant_messages": len([m for m in messages if m.role == "assistant"]),
        }
