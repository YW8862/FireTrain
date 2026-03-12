"""JWT 鉴权相关的工具函数和依赖注入"""
import time
from typing import Optional, Set

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.services.user_service import decode_access_token

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/user/login")


class TokenBlacklist:
    """
    Token 黑名单管理器（内存实现）
    
    注意：这是简单的内存实现，生产环境应该使用 Redis 等持久化存储
    """
    
    def __init__(self):
        self._blacklist: Set[str] = set()
        self._expiry: dict[str, float] = {}
    
    def add(self, token: str, expiry_timestamp: float) -> None:
        """
        将 token 加入黑名单
        
        Args:
            token: JWT token string
            expiry_timestamp: token 过期时间戳
        """
        self._blacklist.add(token)
        self._expiry[token] = expiry_timestamp
    
    def is_blacklisted(self, token: str) -> bool:
        """
        检查 token 是否在黑名单中
        
        Args:
            token: JWT token string
            
        Returns:
            True if token is blacklisted, False otherwise
        """
        # 清理过期的 token
        current_time = time.time()
        expired_tokens = [
            t for t, exp in self._expiry.items() 
            if exp < current_time
        ]
        
        for t in expired_tokens:
            self._blacklist.discard(t)
            del self._expiry[t]
        
        return token in self._blacklist
    
    def clear(self) -> None:
        """清空黑名单"""
        self._blacklist.clear()
        self._expiry.clear()


# 全局黑名单实例
token_blacklist = TokenBlacklist()


async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> int:
    """
    获取当前登录用户 ID
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        当前用户 ID
        
    Raises:
        HTTPException: 如果 token 无效或用户不存在
    """
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
    
    # 从数据库验证用户是否存在
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if user is None:
        raise credentials_exception
    
    return user_id


async def get_optional_user_id(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[int]:
    """
    获取当前登录用户 ID（可选，允许未认证）
    
    用于某些接口既支持匿名用户也支持登录用户的场景
    
    Returns:
        当前用户 ID，如果未认证则返回 None
    """
    try:
        return await get_current_user_id(token=token, db=db)
    except HTTPException:
        return None
