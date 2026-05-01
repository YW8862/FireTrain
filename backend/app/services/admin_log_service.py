"""管理员日志服务层 - 处理管理员日志相关的业务逻辑"""
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_log import AdminLog
from app.repositories.user_repository import UserRepository
from app.utils.logger import ACTION_LABELS


class AdminLogService:
    """管理员日志服务类"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = None  # 将在需要时初始化
    
    async def create_log(
        self,
        admin_id: int,
        action: str,
        target_type: str,
        target_id: Optional[int] = None,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None
    ) -> AdminLog:
        """
        创建管理员操作日志
        
        Args:
            admin_id: 管理员ID
            action: 操作类型
            target_type: 目标类型
            target_id: 目标ID
            details: 详细信息
            ip_address: IP地址
            
        Returns:
            创建的日志对象
        """
        log = AdminLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details or {},
            ip_address=ip_address,
            created_at=datetime.utcnow()
        )
        
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        
        return log

    async def log_action(
        self,
        admin_id: int,
        action: str,
        target_type: str,
        target_id: Optional[int] = None,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None
    ) -> AdminLog:
        """兼容旧调用方的日志写入别名。"""
        return await self.create_log(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=ip_address,
        )
    
    async def get_admin_logs(
        self,
        page: int = 1,
        page_size: int = 20,
        admin_id: Optional[int] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> tuple[List[Dict], int]:
        """
        获取管理员操作日志
        
        Args:
            page: 页码
            page_size: 每页数量
            admin_id: 管理员ID筛选
            action: 操作类型筛选
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            (日志列表, 总数) 元组
        """
        from sqlalchemy import select, func
        
        # 构建查询
        query = select(AdminLog)
        count_query = select(func.count(AdminLog.id))
        
        # 添加筛选条件
        if admin_id:
            query = query.where(AdminLog.admin_id == admin_id)
            count_query = count_query.where(AdminLog.admin_id == admin_id)
        
        if action:
            query = query.where(AdminLog.action == action)
            count_query = count_query.where(AdminLog.action == action)
        
        if start_date:
            query = query.where(AdminLog.created_at >= start_date)
            count_query = count_query.where(AdminLog.created_at >= start_date)
        
        if end_date:
            query = query.where(AdminLog.created_at <= end_date)
            count_query = count_query.where(AdminLog.created_at <= end_date)
        
        # 查询总数
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        offset = (page - 1) * page_size
        query = (
            query.order_by(AdminLog.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        
        result = await self.session.execute(query)
        logs = result.scalars().all()
        
        # 转换为字典并获取管理员用户名
        log_list = []
        for log in logs:
            # 获取管理员用户名
            if not self.user_repo:
                from app.repositories.user_repository import UserRepository
                self.user_repo = UserRepository(self.session)
            
            admin = await self.user_repo.get_by_id(log.admin_id)
            admin_username = admin.username if admin else "未知管理员"
            
            log_list.append({
                "id": log.id,
                "admin_id": log.admin_id,
                "admin_username": admin_username,
                "action": ACTION_LABELS.get(log.action, log.action),
                "action_original": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at
            })
        
        return log_list, total

    async def get_all_logs(
        self,
        page: int = 1,
        page_size: int = 20,
        action_filter: Optional[str] = None
    ) -> tuple[List[AdminLog], int]:
        """兼容旧调用方的日志查询别名。"""
        logs, total = await self.get_admin_logs(
            page=page,
            page_size=page_size,
            action=action_filter,
        )
        admin_logs = []
        for log in logs:
            admin_logs.append(AdminLog(
                id=log["id"],
                admin_id=log["admin_id"],
                action=log["action"],
                target_type=log["target_type"],
                target_id=log["target_id"],
                details=log["details"],
                ip_address=log["ip_address"],
                created_at=log["created_at"],
            ))
        return admin_logs, total