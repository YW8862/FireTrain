"""权限控制中间件"""
from functools import wraps
from typing import Callable

from fastapi import HTTPException, status


def require_role(*allowed_roles: str):
    """
    权限装饰器：验证用户角色是否有权限访问
    
    用法：
        @router.get("/admin")
        @require_role("admin", "root")
        async def admin_endpoint(current_user: dict):
            pass
    
    Args:
        *allowed_roles: 允许访问的角色列表
        
    Returns:
        装饰器函数
        
    Raises:
        HTTPException: 当用户角色不在允许列表中时抛出 403 错误
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, current_user: dict, **kwargs):
            # 获取用户角色
            user_role = current_user.get("role")
            
            # 检查角色是否在允许列表中
            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要以下角色之一：{', '.join(allowed_roles)}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # 执行原函数
            return await func(*args, current_user=current_user, **kwargs)
        
        return wrapper
    return decorator


def require_admin_or_root(func: Callable) -> Callable:
    """快捷装饰器：要求管理员或 Root 权限"""
    return require_role("admin", "root")(func)


def require_root_only(func: Callable) -> Callable:
    """快捷装饰器：仅 Root 用户可访问"""
    return require_role("root")(func)
