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

    # ===========================================
    # AI 模型和数据路径配置
    # ===========================================
    MODEL_DIR: str = os.getenv("MODEL_DIR", "../data/models")
    VIDEO_DIR: str = os.getenv("VIDEO_DIR", "../data/videos")
    MATPLOTLIB_CACHE_DIR: str = os.getenv("MATPLOTLIB_CACHE_DIR", "../data/matplotlib_cache")
    
    # YOLO 模型文件路径
    YOLO_MODEL_PATH: str = os.path.join(MODEL_DIR, "yolov8.onnx")

    # ===========================================
    # 大模型（LLM）评分配置
    # 支持任何兼容 OpenAI Chat Completions 接口的服务：
    #   - OpenAI:   base_url=https://api.openai.com/v1, model=gpt-4o-mini
    #   - DeepSeek: base_url=https://api.deepseek.com/v1, model=deepseek-chat
    #   - Qwen:     base_url=https://dashscope.aliyuncs.com/compatible-mode/v1, model=qwen-turbo
    #   - Zhipu:    base_url=https://open.bigmodel.cn/api/paas/v4, model=glm-4-flash
    # ===========================================
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-chat")
    LLM_TIMEOUT: float = float(os.getenv("LLM_TIMEOUT", "60"))


# 全局配置实例
settings = Settings()
