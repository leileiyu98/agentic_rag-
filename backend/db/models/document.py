"""Document Model - 文档记录"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from backend.db.models.base import Base, TimestampMixin


class Document(Base, TimestampMixin):
    """文档表"""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(500), nullable=False)  # 文档来源路径
    filename = Column(String(255))
    doc_metadata = Column(Text)  # JSON 格式存储文档元数据
    chunk_count = Column(Integer, default=0)

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "source": self.source,
            "filename": self.filename,
            "metadata": self.doc_metadata,
            "chunk_count": self.chunk_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
