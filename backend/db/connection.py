"""Database connection management"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os


class DatabaseConnection:
    """数据库连接管理器"""

    def __init__(self, database_url: str = None):
        """
        初始化数据库连接

        Args:
            database_url: 数据库连接 URL，如未提供则从环境变量获取
        """
        if database_url is None:
            database_url = os.getenv(
                "DATABASE_URL", "postgresql://user:password@localhost:5432/rag_db"
            )

        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            pool_pre_ping=True,
            echo=False,
            # SQLite 内存模式配置（用于测试）
            connect_args={"check_same_thread": False}
            if database_url.startswith("sqlite")
            else {},
            poolclass=StaticPool if database_url.startswith("sqlite") else None,
        )
        self.SessionLocal = sessionmaker(
            bind=self.engine, autocommit=False, autoflush=False
        )

    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()

    def close(self):
        """关闭数据库连接"""
        self.engine.dispose()

    def create_tables(self, base):
        """创建所有表"""
        base.metadata.create_all(bind=self.engine)

    def drop_tables(self, base):
        """删除所有表"""
        base.metadata.drop_all(bind=self.engine)


# 全局数据库连接实例
_db_connection = None


def get_db_connection() -> DatabaseConnection:
    """获取全局数据库连接实例"""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection


def get_db():
    """获取数据库会话（用于 FastAPI 依赖注入）"""
    db = get_db_connection().get_session()
    try:
        yield db
    finally:
        db.close()
