"""Agent Memory Model - 对话历史记录"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from backend.db.models.base import Base, TimestampMixin
from datetime import datetime


class AgentMemory(Base, TimestampMixin):
    """Agent 对话历史记录表"""

    __tablename__ = "agent_memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    msg_metadata = Column(Text)  # JSON 格式存储额外信息

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "metadata": self.msg_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
