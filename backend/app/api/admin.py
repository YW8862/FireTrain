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


# ============ 管理员管理接口 ============

@router.get("/admins")
@require_role("root")
async def get_admins(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词（用户名/邮箱）")
):
    """
    获取管理员列表（仅 Root 用户）

    返回所有 admin 和 root 角色的用户
    """
    from app.schemas.user import AdminInfoResponse

    user_repo = UserRepository(db)

    # 查询所有管理员（admin 和 root）
    users, total = await user_repo.query_with_filters(
        page=page,
        page_size=page_size,
        role_filter=["admin", "root"],
        keyword=keyword
    )

    admin_list = [
        AdminInfoResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            can_switch_role=user.can_switch_role,
            is_active=user.is_active,
            created_at=user.created_at
        )
        for user in users
    ]

    return {
        "admins": admin_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.post("/admins")
@require_role("root")
async def create_admin(
    admin_data: "AdminCreateRequest",
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新管理员（仅 Root 用户）

    可以创建 admin 或 root 角色的用户
    """
    from app.schemas.user import AdminCreateRequest, AdminInfoResponse
    from app.models.user import User

    # 验证角色
    if admin_data.role not in ["admin", "root"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色必须是 admin 或 root"
        )

    user_repo = UserRepository(db)

    # 检查用户名是否已存在
    existing_user = await user_repo.get_by_username(admin_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否已存在
    existing_email = await user_repo.get_by_email(admin_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )

    # 创建新管理员
    hashed_password = get_password_hash(admin_data.password)
    new_admin = User(
        username=admin_data.username,
        email=admin_data.email,
        hashed_password=hashed_password,
        role=admin_data.role,
        can_switch_role=admin_data.can_switch_role,
        is_active=True
    )

    await user_repo.create(new_admin)

    # 记录操作日志
    log_service = AdminLogService(db)
    await log_service.log_action(
        admin_id=current_user["id"],
        action="CREATE_ADMIN",
        target_type="user",
        target_id=new_admin.id,
        details={
            "username": new_admin.username,
            "email": new_admin.email,
            "role": new_admin.role
        }
    )

    return AdminInfoResponse(
        id=new_admin.id,
        username=new_admin.username,
        email=new_admin.email,
        role=new_admin.role,
        can_switch_role=new_admin.can_switch_role,
        is_active=new_admin.is_active,
        created_at=new_admin.created_at
    )


@router.delete("/admins/{admin_id}")
@require_role("root")
async def delete_admin(
    admin_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    删除管理员（仅 Root 用户）

    - 禁止删除自己
    - 禁止删除最后一个 Root 用户
    """
    # 禁止删除自己
    if admin_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(admin_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # Root 用户保护：检查是否是最后一个 Root
    if user.role == "root":
        root_count = await user_repo.count_by_role("root")
        if root_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无法删除最后一个 Root 用户"
            )

    # 执行删除
    await user_repo.delete(user)

    # 记录操作日志
    log_service = AdminLogService(db)
    await log_service.log_action(
        admin_id=current_user["id"],
        action="DELETE_ADMIN",
        target_type="user",
        target_id=admin_id,
        details={
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    )

    return {"message": "管理员删除成功"}


@router.put("/admins/{admin_id}/role")
@require_role("root")
async def update_admin_role(
    admin_id: int,
    role_data: "AdminUpdateRoleRequest",
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    修改管理员角色（仅 Root 用户）

    可以将用户角色修改为 user、admin 或 root
    """
    from app.schemas.user import AdminUpdateRoleRequest, AdminInfoResponse

    # 验证角色
    if role_data.role not in ["user", "admin", "root"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色必须是 user、admin 或 root"
        )

    # 禁止修改自己的角色
    if admin_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的角色"
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(admin_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    old_role = user.role

    # Root 保护：如果要将 Root 改为其他角色，检查是否是最后一个 Root
    if old_role == "root" and role_data.role != "root":
        root_count = await user_repo.count_by_role("root")
        if root_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无法修改最后一个 Root 用户的角色"
            )

    # 更新角色
    user.role = role_data.role

    # 如果改为 admin 或 root，自动设置 can_switch_role
    if role_data.role in ["admin", "root"]:
        user.can_switch_role = True

    await user_repo.update(user)

    # 记录操作日志
    log_service = AdminLogService(db)
    await log_service.log_action(
        admin_id=current_user["id"],
        action="UPDATE_ROLE",
        target_type="user",
        target_id=admin_id,
        details={
            "username": user.username,
            "old_role": old_role,
            "new_role": role_data.role
        }
    )

    return AdminInfoResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        can_switch_role=user.can_switch_role,
        is_active=user.is_active,
        created_at=user.created_at
    )


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
