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
    
    async def create(self, user: User) -> User:
        """创建新用户"""
        self.session.add(user)
        await self.session.flush()
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
    
    async def delete(self, user: User) -> None:
        """删除用户"""
        await self.session.delete(user)
        await self.session.commit()
    
    async def count_by_role(self, role: str) -> int:
        """统计指定角色的用户数量"""
        from sqlalchemy import select, func

        count_query = select(func.count(User.id)).where(User.role == role)
        result = await self.session.execute(count_query)
        return result.scalar()
    
    async def count_all(self) -> int:
        """统计所有用户数量"""
        from sqlalchemy import select, func
        
        count_query = select(func.count(User.id))
        result = await self.session.execute(count_query)
        return result.scalar()
    
    async def count_by_date_range(self, start_date: datetime, end_date: datetime) -> int:
        """统计指定日期范围内的用户数量"""
        from sqlalchemy import select, func
        
        count_query = select(func.count(User.id)).where(
            User.created_at >= start_date,
            User.created_at < end_date
        )
        result = await self.session.execute(count_query)
        return result.scalar()

    async def query_with_filters(
        self,
        page: int = 1,
        page_size: int = 20,
        role_filter: Optional[str | list[str]] = None,
        keyword: Optional[str] = None
    ) -> tuple[list[dict], int]:
        """
        带过滤条件的用户查询
        
        Returns:
            (用户列表, 总数)
        """
        from sqlalchemy import select, func, or_
        
        # 构建查询
        query = select(User)
        count_query = select(func.count(User.id))
        
        # 角色过滤
        if role_filter:
            if isinstance(role_filter, list):
                query = query.where(User.role.in_(role_filter))
                count_query = count_query.where(User.role.in_(role_filter))
            else:
                query = query.where(User.role == role_filter)
                count_query = count_query.where(User.role == role_filter)
        
        # 关键词搜索（用户名或邮箱）
        if keyword:
            search_pattern = f"%{keyword}%"
            query = query.where(
                or_(
                    User.username.like(search_pattern),
                    User.email.like(search_pattern)
                )
            )
            count_query = count_query.where(
                or_(
                    User.username.like(search_pattern),
                    User.email.like(search_pattern)
                )
            )
        
        # 查询总数
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        query = (
            query.order_by(User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        
        result = await self.session.execute(query)
        users = result.scalars().all()
        
        # 转换为字典（不包含密码）
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
                "is_active": user.is_active,
                "last_login_at": user.last_login_at,
                "created_at": user.created_at,
                "can_switch_role": user.can_switch_role
            })
        
        return user_list, total
