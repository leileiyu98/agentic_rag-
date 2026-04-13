"""User Service - 用户业务服务"""

from typing import Optional, Dict
from backend.db.repositories.user_repo import UserRepository


class UserService:
    """用户业务服务"""

    def __init__(self, session):
        self.repo = UserRepository(session)

    def get_or_create_user(self, user_id: str, username: str = None) -> Dict:
        """获取或创建用户"""
        user = self.repo.get_by_user_id(user_id)
        if not user:
            user = self.repo.create_user(user_id=user_id, username=username)
        return user.to_dict()

    def get_user(self, user_id: str) -> Optional[Dict]:
        """获取用户信息"""
        user = self.repo.get_by_user_id(user_id)
        return user.to_dict() if user else None

    def validate_invite_code(self, invite_code: str) -> bool:
        """验证邀请码"""
        # 简单实现：检查是否已存在
        user = self.repo.get_by_invite_code(invite_code)
        return user is None

    def set_user_admin(self, user_id: str, is_admin: bool) -> bool:
        """设置用户管理员权限"""
        user = self.repo.get_by_user_id(user_id)
        if user:
            self.repo.update(user, is_admin=is_admin)
            return True
        return False
