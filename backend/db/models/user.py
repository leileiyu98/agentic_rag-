"""User Model - 用户管理"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from backend.db.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """用户表"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100))
    email = Column(String(255))
    is_admin = Column(Boolean, default=False)
    invite_code = Column(String(100))

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
