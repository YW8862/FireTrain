"""用户相关的 API 路由"""
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.schemas.user import (
    LoginResponse,
    MessageResponse,
    RegisterResponse,
    UserInfoResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserUpdateRequest,
)

router = APIRouter(prefix="/api/user", tags=["用户管理"])

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/user/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    """获取当前登录用户（简化版，实际应该解析 JWT token）"""
    # TODO: 解析 JWT token 获取 user_id
    # 这里为了演示，临时返回一个模拟用户
    return {"id": 1, "username": "demo_user"}


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
async def get_profile(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    获取当前用户信息
    
    需要 Bearer Token 认证
    """
    # TODO: 解析 token 获取用户 ID
    user_id = 1  # 临时硬编码
    
    user = await get_user_from_db(f"user_{user_id}")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserInfoResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        phone=user.get("phone"),
        role=user.get("role", "student"),
        is_active=user.get("is_active", True),
        last_login_at=user.get("last_login_at"),
        created_at=user.get("created_at", datetime.utcnow())
    )


@router.put("/profile", response_model=UserInfoResponse)
async def update_profile(
    user_data: UserUpdateRequest,
    token: Annotated[str, Depends(oauth2_scheme)]
):
    """
    更新当前用户信息
    
    - **nickname**: 昵称（可选）
    - **phone**: 手机号（可选）
    - **avatar_url**: 头像 URL（可选）
    """
    # TODO: 解析 token 获取用户 ID
    user_id = 1  # 临时硬编码
    
    updated_user = await update_user_in_db(user_id, user_data)
    
    return UserInfoResponse(
        id=user_id,
        username=f"user_{user_id}",
        email="user@example.com",
        phone=updated_user.get("phone"),
        role="student",
        is_active=True,
        last_login_at=datetime.utcnow(),
        created_at=datetime.utcnow()
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    退出登录
    
    清理 Token（如果需要可以实现黑名单机制）
    """
    # TODO: 将 token 加入黑名单
    return MessageResponse(message="退出登录成功")
