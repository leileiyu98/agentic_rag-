"""Base Repository - 数据访问层基类"""

from typing import TypeVar, Generic, List, Optional, Type
from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """基础仓库类"""

    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def get_by_id(self, id: int) -> Optional[T]:
        """根据ID获取"""
        return self.session.query(self.model).filter(self.model.id == id).first()

    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """获取所有记录"""
        return self.session.query(self.model).offset(offset).limit(limit).all()

    def create(self, **kwargs) -> T:
        """创建记录"""
        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def update(self, instance: T, **kwargs) -> T:
        """更新记录"""
        for key, value in kwargs.items():
            setattr(instance, key, value)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def delete(self, instance: T) -> None:
        """删除记录"""
        self.session.delete(instance)
        self.session.commit()

    def delete_by_id(self, id: int) -> bool:
        """根据ID删除"""
        instance = self.get_by_id(id)
        if instance:
            self.delete(instance)
            return True
        return False
