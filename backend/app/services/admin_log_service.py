"""管理员操作日志服务"""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_log import AdminLog


class AdminLogService:
    """管理员日志业务逻辑层"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log_action(
        self,
        admin_id: int,
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None
    ) -> AdminLog:
        """
        记录管理员操作
        
        Args:
            admin_id: 管理员 ID
            action: 操作类型 (如：DELETE_USER, UPDATE_TRAINING, UPLOAD_VIDEO)
            target_type: 目标类型 (如：user, training_record)
            target_id: 目标 ID
            details: 操作详情（字典）
            ip_address: IP 地址
            
        Returns:
            创建的日志记录
        """
        log_entry = AdminLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=ip_address
        )
        
        self.session.add(log_entry)
        await self.session.commit()
        await self.session.refresh(log_entry)
        
        return log_entry
    
    async def get_logs_by_admin(
        self, 
        admin_id: int, 
        page: int = 1, 
        page_size: int = 20
    ) -> tuple[list[AdminLog], int]:
        """
        获取指定管理员的操作日志
        
        Args:
            admin_id: 管理员 ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            (日志列表，总数)
        """
        from sqlalchemy import select, func
        
        # 查询总数
        total_query = select(func.count(AdminLog.id)).where(AdminLog.admin_id == admin_id)
        total_result = await self.session.execute(total_query)
        total = total_result.scalar()
        
        # 分页查询
        query = (
            select(AdminLog)
            .where(AdminLog.admin_id == admin_id)
            .order_by(AdminLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        
        result = await self.session.execute(query)
        logs = result.scalars().all()
        
        return logs, total
    
    async def get_all_logs(
        self,
        page: int = 1,
        page_size: int = 20,
        action_filter: Optional[str] = None
    ) -> tuple[list[AdminLog], int]:
        """
        获取所有操作日志（支持筛选）
        
        Args:
            page: 页码
            page_size: 每页数量
            action_filter: 操作类型筛选
            
        Returns:
            (日志列表，总数)
        """
        from sqlalchemy import select, func
        
        # 构建查询
        query = select(AdminLog)
        count_query = select(func.count(AdminLog.id))
        
        if action_filter:
            query = query.where(AdminLog.action == action_filter)
            count_query = count_query.where(AdminLog.action == action_filter)
        
        # 查询总数
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        query = (
            query.order_by(AdminLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        
        result = await self.session.execute(query)
        logs = result.scalars().all()
        
        return logs, total
