import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import users_router, training_router, statistics_router
from app.middleware import setup_request_logging, setup_exception_handlers
from app.core.security import get_current_user_id
from app.services.cleanup_service import setup_cleanup_task

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FireTrain Backend",
    description="智能消防技能训练评测系统单体后端",
    version="0.1.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
)

# 添加异常处理器
setup_exception_handlers(app)

# CORS 配置（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://localhost:5173",  # 本地 HTTPS
        "https://117.72.44.96:5173",  # 公网 IP (HTTPS)
        "http://117.72.44.96:5173",  # 公网 IP (HTTP)
        "*",  # 开发环境允许所有来源（生产环境请移除）
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加请求日志中间件
setup_request_logging(app)

# 设置定时清理任务
setup_cleanup_task(app)

# 注册路由
app.include_router(users_router)
app.include_router(training_router)
app.include_router(statistics_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """健康检查接口"""
    return {"status": "ok"}


@app.get("/")
def root():
    """根路径欢迎信息"""
    return {
        "message": "欢迎使用 FireTrain 智能消防技能训练评测系统",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
