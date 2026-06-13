"""应用配置"""
import os
from pathlib import Path
from typing import List


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent if BACKEND_DIR.name == "backend" else BACKEND_DIR


def _resolve_default_path(env_name: str, default_path: Path) -> str:
    """读取路径配置，并将相对路径解析为绝对路径。"""
    configured_path = os.getenv(env_name)
    raw_path = Path(configured_path) if configured_path else default_path
    if not raw_path.is_absolute():
        raw_path = (PROJECT_DIR / raw_path).resolve()
    return str(raw_path)


class Settings:
    """应用配置类"""

    # JWT 配置
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-not-for-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # 数据库配置
    # Why: 相对路径 ./fire_training.db 会跟随 CWD 飘移，从 backend/ 启动写一个库，
    # 从根目录启动又写另一个；测试套件曾因此 drop_all 误清生产 DB。
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{BACKEND_DIR / 'fire_training.db'}",
    )

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
    DATA_ROOT: str = _resolve_default_path("DATA_ROOT", PROJECT_DIR / "data")
    MODEL_DIR: str = _resolve_default_path("MODEL_DIR", Path(DATA_ROOT) / "models")
    VIDEO_DIR: str = _resolve_default_path("VIDEO_DIR", Path(DATA_ROOT) / "videos")
    ADMIN_VIDEO_DIR: str = _resolve_default_path("ADMIN_VIDEO_DIR", Path(VIDEO_DIR) / "admin_uploads")
    MATPLOTLIB_CACHE_DIR: str = _resolve_default_path(
        "MATPLOTLIB_CACHE_DIR",
        Path(DATA_ROOT) / "matplotlib_cache",
    )

    # YOLO 模型文件路径
    YOLO_MODEL_PATH: str = _resolve_default_path(
        "YOLO_MODEL_PATH",
        Path(MODEL_DIR) / "yolov8.onnx",
    )

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
