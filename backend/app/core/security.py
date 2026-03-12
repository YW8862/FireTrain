"""安全相关的工具函数"""
import time
from typing import Optional, Set


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
