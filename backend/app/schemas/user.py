"""用户相关的 Pydantic Schema"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ============ 请求 Schema ============

class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., min_length=6, max_length=50, description="密码")


class UserUpdateRequest(BaseModel):
    """用户信息更新请求"""
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    avatar_url: Optional[str] = Field(None, max_length=255, description="头像 URL")


# ============ 响应 Schema ============

class UserInfoResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 分钟，单位秒


class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    token_type: str = "bearer"
    user_info: UserInfoResponse


class RegisterResponse(BaseModel):
    """注册响应"""
    message: str
    user_id: int


# ============ 通用响应 Schema ============

class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    code: int = 200


class RoleSwitchRequest(BaseModel):
    """角色切换请求"""
    target_role: str = Field(..., description="目标角色 (user 或 admin)")


class RoleSwitchResponse(BaseModel):
    """角色切换响应"""
    role: str
    original_role: str | None = None
    can_switch_role: bool
    token: str | None = None  # 新的 Token


# ============ 管理员管理 Schema ============

class AdminCreateRequest(BaseModel):
    """创建管理员请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    role: str = Field(..., description="角色 (admin 或 root)")
    can_switch_role: bool = Field(True, description="是否允许角色切换")


class AdminUpdateRoleRequest(BaseModel):
    """修改管理员角色请求"""
    role: str = Field(..., description="目标角色 (user, admin 或 root)")


class AdminInfoResponse(BaseModel):
    """管理员信息响应"""
    id: int
    username: str
    email: str
    role: str
    can_switch_role: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
