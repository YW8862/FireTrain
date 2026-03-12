from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import users_router, training_router, statistics_router


app = FastAPI(
    title="FireTrain Backend",
    description="智能消防技能训练评测系统单体后端",
    version="0.1.0",
)

# CORS 配置（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://117.72.44.96:5173",  # 添加公网 IP
        "*",  # 开发环境允许所有来源（生产环境应该移除）
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(users_router)
app.include_router(training_router)
app.include_router(statistics_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
