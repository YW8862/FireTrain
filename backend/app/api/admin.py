"""后台管理相关的 API 路由"""
from datetime import datetime, timedelta
from typing import Optional, Annotated
import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.users import get_current_user
from app.middleware.permission import require_role
from app.repositories.user_repository import UserRepository
from app.repositories.training_repository import TrainingRepository
from app.services.user_service import get_password_hash
from app.services.admin_log_service import AdminLogService
from app.services.statistics_service import StatisticsService
from app.schemas.user import (
    AdminUpdateRequest,
    AdminCreateRequest,
    AdminInfoResponse,
    AdminUserCreateRequest,
    AdminUserInfoResponse,
    AdminUserUpdateRequest,
    AdminUpdateRoleRequest,
)
from app.schemas.statistics import (
    StatisticsOverviewResponse,
    StepAnalysisResponse,
    TrainingTrendResponse,
)
from app.schemas.training import TrainingHistoryResponse, TrainingRecordResponse


def _get_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


router = APIRouter(prefix="/api/admin", tags=["后台管理"])

# 创建类型别名以便使用
CurrentUser = Annotated[dict, Depends(get_current_user)]
STANDARD_USER_ROLE = "student"
LEGACY_USER_ROLE = "user"
MANAGEABLE_USER_ROLES = {STANDARD_USER_ROLE, LEGACY_USER_ROLE}


def _build_admin_info_response(user) -> AdminInfoResponse:
    if isinstance(user, dict):
        return AdminInfoResponse(**user)
    return AdminInfoResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


def _build_admin_user_info_response(user) -> AdminUserInfoResponse:
    if isinstance(user, dict):
        return AdminUserInfoResponse(**user)
    return AdminUserInfoResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


async def _get_manageable_user(
    user_repo: UserRepository,
    user_id: int,
    current_user: dict,
):
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    # Root 用户可以访问任何人（包括自己）的详情
    if current_user["role"] == "root":
        return user

    if user.role not in MANAGEABLE_USER_ROLES:
        if user.role == "admin" and current_user["role"] == "root":
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="普通用户管理入口不能操作管理员或 Root 用户",
        )

    return user


async def _validate_unique_user_fields(
    user_repo: UserRepository,
    *,
    username: str,
    email: str,
    current_user_id: Optional[int] = None,
):
    existing_user = await user_repo.get_by_username(username)
    if existing_user and existing_user.id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    existing_email = await user_repo.get_by_email(email)
    if existing_email and existing_email.id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在",
        )


async def _get_admin_target(
    user_repo: UserRepository,
    admin_id: int,
):
    user = await user_repo.get_by_id(admin_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    if user.role not in {"admin", "root"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员管理入口仅能操作 admin 或 root 用户",
        )

    return user


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
    user_repo = UserRepository(db)

    # 查询所有管理员（admin 和 root）
    users, total = await user_repo.query_with_filters(
        page=page,
        page_size=page_size,
        role_filter=["admin", "root"],
        keyword=keyword
    )

    admin_list = [_build_admin_info_response(user) for user in users]

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
    admin_data: AdminCreateRequest,
    current_user: CurrentUser,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新管理员（仅 Root 用户）

    可以创建 admin 或 root 角色的用户
    """
    from app.models.user import User

    # 只允许创建普通管理员，系统内 Root 账号仅保留一个且不可新增
    if admin_data.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅允许创建管理员（admin）账号，系统内 Root 账号唯一且不可新增"
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
        password_hash=hashed_password,
        phone=None,
        role=admin_data.role,
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
        },
        ip_address=_get_client_ip(request)
    )

    return _build_admin_info_response(new_admin)


@router.delete("/admins/{admin_id}")
@require_role("root")
async def delete_admin(
    admin_id: int,
    current_user: CurrentUser,
    request: Request,
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
        },
        ip_address=_get_client_ip(request)
    )

    return {"message": "管理员删除成功"}


@router.put("/admins/{admin_id}/role")
@require_role("root")
async def update_admin_role(
    admin_id: int,
    role_data: AdminUpdateRoleRequest,
    current_user: CurrentUser,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    修改管理员角色（仅 Root 用户）

    可以将用户角色修改为 student、admin 或 root（兼容旧值 user）
    """
    target_role = STANDARD_USER_ROLE if role_data.role == LEGACY_USER_ROLE else role_data.role

    # 只允许在普通用户与管理员之间切换，系统内 Root 账号唯一且不可新增/提升
    if target_role not in [STANDARD_USER_ROLE, "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色只能设置为普通用户或管理员，Root 账号不可新增"
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
    if old_role == "root" and target_role != "root":
        root_count = await user_repo.count_by_role("root")
        if root_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无法修改最后一个 Root 用户的角色"
            )

    # 更新角色
    user.role = target_role

    await user_repo.update(user, {})

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
            "new_role": target_role
        },
        ip_address=_get_client_ip(request)
    )

    return _build_admin_info_response(user)


@router.get("/admins/{admin_id}", response_model=AdminInfoResponse)
@require_role("root")
async def get_admin_detail(
    admin_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """获取管理员详情（仅 Root）。"""
    user_repo = UserRepository(db)
    user = await _get_admin_target(user_repo, admin_id)
    return _build_admin_info_response(user)


@router.put("/admins/{admin_id}", response_model=AdminInfoResponse)
@require_role("root")
async def update_admin(
    admin_id: int,
    admin_data: AdminUpdateRequest,
    current_user: CurrentUser,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """更新管理员基础资料（仅 Root）。"""
    user_repo = UserRepository(db)
    user = await _get_admin_target(user_repo, admin_id)

    await _validate_unique_user_fields(
        user_repo,
        username=admin_data.username,
        email=admin_data.email,
        current_user_id=user.id,
    )

    if user.role == "root" and not admin_data.is_active:
        root_count = await user_repo.count_by_role("root")
        if root_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无法禁用最后一个 Root 用户",
            )

    update_data = {
        "username": admin_data.username,
        "email": admin_data.email,
        "phone": admin_data.phone,
        "is_active": admin_data.is_active,
    }

    if admin_data.password:
        update_data["password_hash"] = get_password_hash(admin_data.password)

    updated_user = await user_repo.update(user, update_data)

    log_service = AdminLogService(db)
    await log_service.log_action(
        admin_id=current_user["id"],
        action="UPDATE_ADMIN",
        target_type="user",
        target_id=updated_user.id,
        details={
            "username": updated_user.username,
            "role": updated_user.role,
            "is_active": updated_user.is_active,
        },
        ip_address=_get_client_ip(request),
    )

    return _build_admin_info_response(updated_user)


@router.put("/admins/{admin_id}/reset-password")
@require_role("root")
async def reset_admin_password(
    admin_id: int,
    current_user: CurrentUser,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """重置管理员密码（仅 Root）。"""
    user_repo = UserRepository(db)
    user = await _get_admin_target(user_repo, admin_id)

    characters = string.ascii_letters + string.digits
    temp_password = ''.join(secrets.choice(characters) for _ in range(8))

    await user_repo.update(user, {
        "password_hash": get_password_hash(temp_password),
    })

    log_service = AdminLogService(db)
    await log_service.log_action(
        admin_id=current_user["id"],
        action="RESET_ADMIN_PASSWORD",
        target_type="user",
        target_id=admin_id,
        details={"username": user.username},
        ip_address=_get_client_ip(request)
    )

    return {
        "message": "管理员密码重置成功",
        "temp_password": temp_password,
        "warning": "请立即将此密码告知管理员，并要求其首次登录后修改",
    }


# ============ 用户管理接口 ============

@router.get("/users")
@require_role("admin", "root")
async def get_all_users(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词（用户名/邮箱）"),
    role: Optional[str] = Query(
        None,
        description="角色筛选：all/student/admin/root（仅 Root 可使用；非 Root 固定仅返回普通用户）"
    )
):
    """
    获取用户列表（支持分页、搜索、按角色过滤）

    - 普通管理员：始终只返回普通用户（student/user）
    - Root 用户：可通过 role 参数查看全部角色
        - all 或留空：返回全部用户（普通用户 + 管理员 + Root）
        - student：仅普通用户
        - admin：仅管理员
        - root：仅 Root
    """
    user_repo = UserRepository(db)

    is_root = current_user.get("role") == "root"
    standard_roles = [STANDARD_USER_ROLE, LEGACY_USER_ROLE]

    if not is_root:
        role_filter = standard_roles
    else:
        normalized_role = (role or "all").lower()
        if normalized_role in ("all", ""):
            role_filter = None
        elif normalized_role in ("student", "user"):
            role_filter = standard_roles
        elif normalized_role == "admin":
            role_filter = ["admin"]
        elif normalized_role == "root":
            role_filter = ["root"]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="role 参数必须是 all/student/admin/root 之一"
            )

    users, total = await user_repo.query_with_filters(
        page=page,
        page_size=page_size,
        role_filter=role_filter,
        keyword=keyword
    )
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.post("/users", response_model=AdminUserInfoResponse, status_code=status.HTTP_201_CREATED)
@require_role("admin", "root")
async def create_user(
    user_data: AdminUserCreateRequest,
    current_user: CurrentUser,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """管理员创建普通用户。"""
    from app.models.user import User

    user_repo = UserRepository(db)
    await _validate_unique_user_fields(
        user_repo,
        username=user_data.username,
        email=user_data.email,
    )

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        phone=user_data.phone,
        role=STANDARD_USER_ROLE,
        is_active=user_data.is_active,
    )

    await user_repo.create(new_user)

    log_service = AdminLogService(db)
    await log_service.log_action(
        admin_id=current_user["id"],
        action="CREATE_USER",
        target_type="user",
        target_id=new_user.id,
        details={
            "username": new_user.username,
            "email": new_user.email,
        },
        ip_address=_get_client_ip(request),
    )

    return _build_admin_user_info_response(new_user)


@router.get("/users/{user_id}", response_model=AdminUserInfoResponse)
@require_role("admin", "root")
async def get_user_detail(
    user_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """获取普通用户详情。"""
    user_repo = UserRepository(db)
    user = await _get_manageable_user(user_repo, user_id, current_user)
    return _build_admin_user_info_response(user)


@router.put("/users/{user_id}", response_model=AdminUserInfoResponse)
@require_role("admin", "root")
async def update_user_detail(
    user_id: int,
    user_data: AdminUserUpdateRequest,
    current_user: CurrentUser,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """管理员更新普通用户资料。"""
    user_repo = UserRepository(db)
    user = await _get_manageable_user(user_repo, user_id, current_user)

    await _validate_unique_user_fields(
        user_repo,
        username=user_data.username,
        email=user_data.email,
        current_user_id=user.id,
    )

    update_data = {
        "username": user_data.username,
        "email": user_data.email,
        "phone": user_data.phone,
        "is_active": user_data.is_active,
    }

    if user_data.password:
        update_data["password_hash"] = get_password_hash(user_data.password)

    # 只有 root 可以修改用户角色
    if user_data.role and current_user["role"] == "root":
        update_data["role"] = user_data.role

    updated_user = await user_repo.update(user, update_data)

    log_service = AdminLogService(db)
    await log_service.log_action(
        admin_id=current_user["id"],
        action="UPDATE_USER",
        target_type="user",
        target_id=user_id,
        details={
            "username": updated_user.username,
            "email": updated_user.email,
            "is_active": updated_user.is_active,
        },
        ip_address=_get_client_ip(request),
    )

    return _build_admin_user_info_response(updated_user)


@router.get("/users/{user_id}/trainings", response_model=TrainingHistoryResponse)
@require_role("admin", "root")
async def get_user_trainings(
    user_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """管理员查看普通用户训练记录。"""
    user_repo = UserRepository(db)
    await _get_manageable_user(user_repo, user_id, current_user)

    training_repo = TrainingRepository(db)
    records, total = await training_repo.get_user_history(
        user_id=user_id,
        page=page,
        page_size=page_size,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )

    return TrainingHistoryResponse(
        total=total,
        page=page,
        page_size=page_size,
        records=[
            TrainingRecordResponse(
                id=record.id,
                user_id=record.user_id,
                training_type=record.training_type,
                status=record.status,
                total_score=record.total_score,
                step_scores=record.step_scores,
                video_path=record.video_path,
                duration_seconds=record.duration_seconds,
                started_at=record.started_at,
                completed_at=record.completed_at,
                feedback=record.feedback,
                created_at=record.created_at,
            )
            for record in records
        ],
    )


@router.get("/users/{user_id}/stats/overview", response_model=StatisticsOverviewResponse)
@require_role("admin", "root")
async def get_user_statistics_overview(
    user_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    days: int = Query(7, ge=1, le=30, description="趋势天数")
):
    """管理员查看普通用户统计概览。"""
    user_repo = UserRepository(db)
    await _get_manageable_user(user_repo, user_id, current_user)

    stats_service = StatisticsService(db)
    personal_stats = await stats_service.get_personal_statistics(user_id)
    trend_data = await stats_service.get_training_trend(user_id, days=days)
    step_analysis = await stats_service.get_step_analysis(user_id)

    return StatisticsOverviewResponse(
        personal_stats=personal_stats,
        recent_trend=TrainingTrendResponse(
            trend_data=trend_data,
            total_days=len(trend_data),
        ),
        step_analysis=StepAnalysisResponse(step_analysis=step_analysis),
    )


@router.delete("/users/{user_id}")
@require_role("admin", "root")
async def delete_user(
    user_id: int,
    current_user: CurrentUser,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    删除用户
    
    - 禁止删除 Root 用户
    - 禁止删除自己
    - 会级联删除该用户的所有训练记录和统计数据
    """
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    user_repo = UserRepository(db)
    user = await _get_manageable_user(user_repo, user_id, current_user)
    
    # 执行删除
    await user_repo.delete(user)
    
    # 记录操作日志
    log_service = AdminLogService(db)
    await log_service.log_action(
        admin_id=current_user["id"],
        action="DELETE_USER",
        target_type="user",
        target_id=user_id,
        details={"username": user.username, "email": user.email},
        ip_address=_get_client_ip(request)
    )

    return {"message": "用户删除成功"}


@router.put("/users/{user_id}/reset-password")
@require_role("admin", "root")
async def reset_user_password(
    user_id: int,
    current_user: CurrentUser,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    重置用户密码为随机密码
    
    返回临时密码，管理员需通过其他方式告知用户
    """
    user_repo = UserRepository(db)
    user = await _get_manageable_user(user_repo, user_id, current_user)
    
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
        details={"username": user.username},
        ip_address=_get_client_ip(request)
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
    request: Request,
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
        target_id=training_id,
        ip_address=_get_client_ip(request)
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
    from sqlalchemy import func, select

    from app.models.training_record import TrainingRecord
    from app.models.user import User
    from app.models.video_detection_task import VideoDetectionTask

    user_repo = UserRepository(db)
    training_repo = TrainingRepository(db)

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    total_users = await user_repo.count_all()
    new_users_today = await user_repo.count_by_date_range(today_start, today_end)

    role_result = await db.execute(
        select(User.role, func.count(User.id)).group_by(User.role)
    )
    role_distribution = {role: count for role, count in role_result.all()}

    total_trainings = await training_repo.count_all()
    trainings_today = await training_repo.count_by_date_range(today_start, today_end)
    average_score = await training_repo.get_average_score()

    training_type_result = await db.execute(
        select(TrainingRecord.training_type, func.count(TrainingRecord.id))
        .group_by(TrainingRecord.training_type)
    )
    type_distribution = {training_type: count for training_type, count in training_type_result.all()}

    video_status_result = await db.execute(
        select(VideoDetectionTask.status, func.count(VideoDetectionTask.id))
        .group_by(VideoDetectionTask.status)
    )
    video_counts = {str(status): count for status, count in video_status_result.all()}

    user_stats = {
        "total_users": total_users,
        "new_users_today": new_users_today,
        "active_users": total_users,
        "role_distribution": role_distribution
    }
    training_stats = {
        "total_trainings": total_trainings,
        "trainings_today": trainings_today,
        "average_score": round(average_score, 2) if average_score else 0,
        "type_distribution": type_distribution
    }
    video_stats = {
        "pending": video_counts.get("VideoTaskStatus.PENDING", video_counts.get("pending", 0)),
        "processing": video_counts.get("VideoTaskStatus.PROCESSING", video_counts.get("processing", 0)),
        "completed": video_counts.get("VideoTaskStatus.COMPLETED", video_counts.get("completed", 0)),
        "failed": video_counts.get("VideoTaskStatus.FAILED", video_counts.get("failed", 0)),
    }
    
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
