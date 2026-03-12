"""用户相关的 Service 层"""
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRegisterRequest, UserUpdateRequest


# 密码加密配置
BCRYPT_ROUNDS = 12


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """生成密码 hash"""
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """生成 JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    解码 JWT Token
    
    Args:
        token: JWT token string
        
    Returns:
        解码后的 payload 字典，如果验证失败返回 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


class UserService:
    """用户业务逻辑层"""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def register(self, user_data: UserRegisterRequest) -> User:
        """用户注册"""
        # 检查用户名是否已存在
        existing_user = await self.user_repo.get_by_username(user_data.username)
        if existing_user:
            raise ValueError("用户名已被注册")
        
        # 检查邮箱是否已存在
        existing_email = await self.user_repo.get_by_email(user_data.email)
        if existing_email:
            raise ValueError("邮箱已被注册")
        
        # 创建用户（密码 hash 存储）
        user_dict = {
            "username": user_data.username,
            "email": user_data.email,
            "password_hash": get_password_hash(user_data.password),
            "phone": user_data.phone,
        }
        
        user = await self.user_repo.create(user_dict)
        return user
    
    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """用户认证"""
        user = await self.user_repo.get_by_username(username)
        if not user:
            # 尝试用邮箱登录
            user = await self.user_repo.get_by_email(username)
        
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        return user
    
    async def login(self, username: str, password: str) -> tuple[str, User]:
        """用户登录，返回 token 和用户信息"""
        user = await self.authenticate(username, password)
        if not user:
            raise ValueError("用户名或密码错误")
        
        # 更新最后登录时间
        await self.user_repo.update_last_login(user)
        
        # 生成 Token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=access_token_expires
        )
        
        return access_token, user
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """获取用户信息"""
        return await self.user_repo.get_by_id(user_id)
    
    async def update_user(self, user: User, update_data: UserUpdateRequest) -> User:
        """更新用户信息"""
        update_dict = update_data.model_dump(exclude_unset=True)
        updated_user = await self.user_repo.update(user, update_dict)
        return updated_user
