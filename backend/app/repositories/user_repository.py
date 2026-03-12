"""用户相关的 Repository 层"""
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """用户数据访问层"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """根据 ID 获取用户"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, user_data: dict) -> User:
        """创建新用户"""
        user = User(**user_data)
        self.session.add(user)
        await self.session.flush()  # 获取生成的 ID
        await self.session.refresh(user)
        return user
    
    async def update(self, user: User, update_data: dict) -> User:
        """更新用户信息"""
        for field, value in update_data.items():
            setattr(user, field, value)
        user.updated_at = datetime.utcnow()
        await self.session.flush()
        await self.session.refresh(user)
        return user
    
    async def update_last_login(self, user: User) -> None:
        """更新最后登录时间"""
        user.last_login_at = datetime.utcnow()
        await self.session.flush()
