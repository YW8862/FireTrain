"""管理员操作日志工具函数"""
from typing import Optional, TYPE_CHECKING

from fastapi import Request

if TYPE_CHECKING:
    from app.services.admin_log_service import AdminLogService


async def log_admin_action(
    service: "AdminLogService",
    admin_id: int,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    details: Optional[dict] = None,
    request: Optional[Request] = None
):
    """
    便捷函数：记录管理员操作
    
    用法:
        await log_admin_action(
            log_service,
            current_user["id"],
            "DELETE_USER",
            target_type="user",
            target_id=user_id,
            request=request
        )
    
    Args:
        service: AdminLogService 实例
        admin_id: 管理员 ID
        action: 操作类型
        target_type: 目标类型
        target_id: 目标 ID
        details: 操作详情
        request: FastAPI 请求对象（用于获取 IP）
    """
    # 从请求中获取 IP 地址
    ip_address = None
    if request:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()
        else:
            if request.client:
                ip_address = request.client.host
    
    # 记录日志
    await service.log_action(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address
    )


# 常用操作类型常量
class AdminActionTypes:
    """管理员操作类型常量"""
    # 用户管理
    DELETE_USER = "DELETE_USER"
    UPDATE_USER = "UPDATE_USER"
    RESET_USER_PASSWORD = "RESET_USER_PASSWORD"
    
    # 训练数据管理
    DELETE_TRAINING = "DELETE_TRAINING"
    UPDATE_TRAINING = "UPDATE_TRAINING"
    
    # 视频管理
    UPLOAD_VIDEO = "UPLOAD_VIDEO"
    DELETE_VIDEO = "DELETE_VIDEO"
    
    # 管理员管理（仅 Root）
    CREATE_ADMIN = "CREATE_ADMIN"
    DELETE_ADMIN = "DELETE_ADMIN"
    
    # 角色切换
    SWITCH_TO_USER = "SWITCH_TO_USER"
    SWITCH_TO_ADMIN = "SWITCH_TO_ADMIN"
