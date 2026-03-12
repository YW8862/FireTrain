"""应用配置"""
import os
from typing import List


class Settings:
    """应用配置类"""
    
    # JWT 配置
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-not-for-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./fire_training.db")
    
    # CORS 配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    # 调试模式
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # 应用信息
    APP_NAME: str = "FireTrain Backend"
    APP_VERSION: str = "0.1.0"


# 全局配置实例
settings = Settings()
