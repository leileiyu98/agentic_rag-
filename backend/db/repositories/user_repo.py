"""User Repository - 用户数据访问"""

from typing import Optional
from backend.db.repositories.base import BaseRepository
from backend.db.models.user import User


class UserRepository(BaseRepository[User]):
    """用户仓库"""

    def __init__(self, session):
        super().__init__(session, User)

    def get_by_user_id(self, user_id: str) -> Optional[User]:
        """根据用户ID获取"""
        return self.session.query(User).filter(User.user_id == user_id).first()

    def get_by_invite_code(self, invite_code: str) -> Optional[User]:
        """根据邀请码获取"""
        return self.session.query(User).filter(User.invite_code == invite_code).first()

    def create_user(
        self,
        user_id: str,
        username: str = None,
        email: str = None,
        is_admin: bool = False,
    ) -> User:
        """创建新用户"""
        return self.create(
            user_id=user_id, username=username, email=email, is_admin=is_admin
        )
