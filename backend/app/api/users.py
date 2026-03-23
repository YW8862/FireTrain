"""用户相关的 API 路由"""
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import token_blacklist
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService, decode_access_token
from app.schemas.user import (
    LoginResponse,
    MessageResponse,
    RegisterResponse,
    UserInfoResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserUpdateRequest,
    RoleSwitchRequest,
    RoleSwitchResponse,
)

router = APIRouter(prefix="/api/user", tags=["用户管理"])

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/user/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    """
    获取当前登录用户（解析 JWT token）
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        Current user data
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    # 检查 token 是否在黑名单中
    if token_blacklist.is_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已失效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 解码 JWT token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    # 从 token 中获取用户 ID
    user_id: Optional[int] = payload.get("user_id")
    if user_id is None:
        raise credentials_exception
    
    # 从数据库获取用户
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if user is None:
        raise credentials_exception
    
    # 返回用户信息
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


# ============ 认证接口 ============

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    用户注册
    
    - **username**: 用户名（3-50 字符）
    - **email**: 邮箱地址
    - **password**: 密码（至少 6 字符）
    - **phone**: 手机号（可选）
    """
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)
    
    try:
        new_user = await user_service.register(user_data)
        return RegisterResponse(
            message="注册成功",
            user_id=new_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
    
    - **username**: 用户名或邮箱
    - **password**: 密码
    
    返回 JWT Token 和用户信息
    """
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)
    
    try:
        access_token, user = await user_service.login(form_data.username, form_data.password)
        
        return LoginResponse(
            token=access_token,
            token_type="bearer",
            user_info=UserInfoResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                phone=user.phone,
                role=user.role,
                is_active=user.is_active,
                last_login_at=user.last_login_at,
                created_at=user.created_at
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============ 用户信息接口 ============

@router.get("/profile", response_model=UserInfoResponse)
async def get_profile(current_user: Annotated[dict, Depends(get_current_user)]):
    """
    获取当前用户信息
    
    需要 Bearer Token 认证
    """
    return UserInfoResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        phone=current_user.get("phone"),
        role=current_user.get("role", "student"),
        is_active=current_user.get("is_active", True),
        last_login_at=current_user.get("last_login_at"),
        created_at=current_user.get("created_at", datetime.utcnow())
    )


@router.put("/profile", response_model=UserInfoResponse)
async def update_profile(
    user_data: UserUpdateRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    更新当前用户信息
    
    - **nickname**: 昵称（可选）
    - **phone**: 手机号（可选）
    - **avatar_url**: 头像 URL（可选）
    """
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)
    
    # 从数据库获取用户对象
    user = await user_repo.get_by_id(current_user["id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新用户信息
    try:
        updated_user = await user_service.update_user(user, user_data)
        
        return UserInfoResponse(
            id=updated_user.id,
            username=updated_user.username,
            email=updated_user.email,
            phone=updated_user.phone,
            role=updated_user.role,
            is_active=updated_user.is_active,
            last_login_at=updated_user.last_login_at,
            created_at=updated_user.created_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    退出登录
    
    将 token 加入黑名单，使其立即失效
    """
    # 解码 token 获取过期时间
    payload = decode_access_token(token)
    if payload:
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            # 将 token 加入黑名单
            token_blacklist.add(token, exp_timestamp)
    
    return MessageResponse(message="退出登录成功")


@router.post("/switch-role", response_model=RoleSwitchResponse)
async def switch_role(
    role_data: RoleSwitchRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    切换用户角色（仅管理员可临时切换为普通用户）
    
    - **target_role**: 目标角色 ("user" 或 "admin")
    """
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)
    
    try:
        result = await user_service.switch_role(
            current_user["id"], 
            role_data.target_role
        )
        return RoleSwitchResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
