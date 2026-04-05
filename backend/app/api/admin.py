"""后台管理相关的 API 路由"""
from datetime import datetime
from typing import Optional, Annotated
import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.users import get_current_user
from app.middleware.permission import require_role
from app.repositories.user_repository import UserRepository
from app.repositories.training_repository import TrainingRepository
from app.services.user_service import UserService, get_password_hash
from app.services.admin_log_service import AdminLogService
from app.services.statistics_service import StatisticsService

router = APIRouter(prefix="/api/admin", tags=["后台管理"])

# 创建类型别名以便使用
CurrentUser = Annotated[dict, Depends(get_current_user)]


# ============ 用户管理接口 ============

@router.get("/users")
@require_role("admin", "root")
async def get_all_users(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    role: Optional[str] = Query(None, description="角色过滤"),
    keyword: Optional[str] = Query(None, description="搜索关键词（用户名/邮箱）")
):
    """
    获取所有用户列表（支持分页、搜索、过滤）
    
    - 管理员只能查看普通用户
    - Root 用户可以查看所有用户
    """
    user_repo = UserRepository(db)
    
    # 根据角色限制查询范围
    if current_user["role"] == "admin":
        # 管理员只能查看普通用户
        users, total = await user_repo.query_with_filters(
            page=page,
            page_size=page_size,
            role_filter="user",
            keyword=keyword
        )
    else:
        # Root 用户可以查看所有用户
        users, total = await user_repo.query_with_filters(
            page=page,
            page_size=page_size,
            role_filter=role,
            keyword=keyword
        )
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.delete("/users/{user_id}")
@require_role("admin", "root")
async def delete_user(
    user_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    删除用户
    
    - 禁止删除 Root 用户
    - 禁止删除自己
    - 会级联删除该用户的所有训练记录和统计数据
    """
    # 安全检查
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # Root 用户保护
    if user.role == "root":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="禁止删除 Root 用户"
        )
    
    # 管理员权限检查
    if current_user["role"] == "admin" and user.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员只能删除普通用户"
        )
    
    # 执行删除
    await user_repo.delete(user)
    
    # 记录操作日志
    log_service = AdminLogService(db)
    await log_service.log_action(
        admin_id=current_user["id"],
        action="DELETE_USER",
        target_type="user",
        target_id=user_id,
        details={"username": user.username, "email": user.email}
    )
    
    return {"message": "用户删除成功"}


@router.put("/users/{user_id}/reset-password")
@require_role("admin", "root")
async def reset_user_password(
    user_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    重置用户密码为随机密码
    
    返回临时密码，管理员需通过其他方式告知用户
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 生成随机密码（8位字母数字组合）
    characters = string.ascii_letters + string.digits
    temp_password = ''.join(secrets.choice(characters) for _ in range(8))
    
    # 更新密码
    user.password_hash = get_password_hash(temp_password)
    await user_repo.update(user, {})
    
    # 记录操作日志
    log_service = AdminLogService(db)
    await log_service.log_action(
        admin_id=current_user["id"],
        action="RESET_USER_PASSWORD",
        target_type="user",
        target_id=user_id,
        details={"username": user.username}
    )
    
    return {
        "message": "密码重置成功",
        "temp_password": temp_password,
        "warning": "请立即将此密码告知用户，并要求其首次登录后修改"
    }


# ============ 训练数据管理接口 ============

@router.get("/trainings")
@require_role("admin", "root")
async def get_all_trainings(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    training_type: Optional[str] = Query(None, description="训练类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD")
):
    """获取所有训练记录（支持多维度过滤）"""
    training_repo = TrainingRepository(db)
    
    trainings, total = await training_repo.query_with_filters(
        page=page,
        page_size=page_size,
        user_id=user_id,
        training_type=training_type,
        status=status,
        start_date=start_date,
        end_date=end_date
    )
    
    return {
        "trainings": trainings,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.delete("/trainings/{training_id}")
@require_role("admin", "root")
async def delete_training(
    training_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """删除训练记录"""
    training_repo = TrainingRepository(db)
    training = await training_repo.get_by_id(training_id)
    
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="训练记录不存在"
        )
    
    await training_repo.delete(training)
    
    # 记录操作日志
    log_service = AdminLogService(db)
    await log_service.log_action(
        admin_id=current_user["id"],
        action="DELETE_TRAINING",
        target_type="training",
        target_id=training_id
    )
    
    return {"message": "训练记录删除成功"}


# ============ 系统统计接口 ============

@router.get("/statistics/dashboard")
@require_role("admin", "root")
async def get_dashboard_statistics(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    获取仪表盘统计数据
    
    包括：
    - 用户统计（总数、今日新增、活跃用户）
    - 训练统计（总次数、今日次数、平均分）
    - 视频检测统计
    - 系统运行状态
    """
    stats_service = StatisticsService(db)
    
    # 获取各项统计数据
    user_stats = await stats_service.get_system_user_stats()
    training_stats = await stats_service.get_system_training_stats()
    video_stats = await stats_service.get_video_detection_stats()
    
    return {
        "user_statistics": user_stats,
        "training_statistics": training_stats,
        "video_statistics": video_stats,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============ 操作日志查询接口 ============

@router.get("/logs")
@require_role("admin", "root")
async def get_admin_logs(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin_id: Optional[int] = Query(None, description="管理员ID过滤"),
    action: Optional[str] = Query(None, description="操作类型过滤")
):
    """获取管理员操作日志"""
    log_service = AdminLogService(db)
    
    # Root 用户可以查看所有日志，管理员只能查看自己的日志
    if current_user["role"] == "admin":
        admin_id = current_user["id"]
    
    logs, total = await log_service.get_all_logs(
        page=page,
        page_size=page_size,
        action_filter=action
    )
    
    # 转换为字典
    log_list = []
    for log in logs:
        log_list.append({
            "id": log.id,
            "admin_id": log.admin_id,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at
        })
    
    return {
        "logs": log_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }
