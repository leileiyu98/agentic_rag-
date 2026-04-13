"""Database models base module"""

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

Base = declarative_base()


class TimestampMixin:
    """时间戳混入类 - 使用北京时间 (UTC+8)"""

    @staticmethod
    def beijing_now():
        """获取当前北京时间"""
        return datetime.utcnow() + timedelta(hours=8)

    created_at = Column(DateTime, default=beijing_now)
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now)
