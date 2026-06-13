import os
import sys
import asyncio
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# 强制把 DATABASE_URL 指向独立的 test.db，必须在任何 app.* import 之前完成。
# Why: 此前 reset_database fixture 直接对 settings.DATABASE_URL drop_all + create_all，
# 而 settings 默认指到生产 DB，导致 `make test` / pytest 每跑一次就把后端真实数据清空。
# How: app.core.config.Settings 在 import 时读取 env，app.db.session.engine 在 import
# 时基于该 settings 创建，所以 env 必须在这两步之前被覆盖。
TEST_DB_PATH = BACKEND_ROOT / "test.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH}"

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base

# 防御性断言：保护这层 override 在未来重构中不被悄悄删掉。
# 注意上一行 os.environ 是无条件覆盖，会盖过 shell export 和 .env 的值，
# 所以正常情况下 assert 永远通过；它的作用仅是在 override 失效时立刻 fail。
assert settings.DATABASE_URL.endswith("test.db"), (
    f"测试拒绝在非 test.db 上跑：当前 DATABASE_URL={settings.DATABASE_URL}。"
    f" 期望以 test.db 结尾——检查上面的 os.environ override 是否被改坏。"
)


@pytest.fixture(autouse=True)
def reset_database():
    """
    每个测试前 drop_all + create_all，确保表结构与数据完全隔离。

    注意：被测模型与 SQLite dev DB 已通过 migrate_add_role_fields.py 对齐，
    真实环境请通过 alembic/SQL 迁移推进 schema。
    """
    test_engine = create_async_engine(settings.DATABASE_URL, echo=False)
    TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

    async def _reset():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_reset())
    yield
    asyncio.run(test_engine.dispose())


@pytest.fixture
def yolo_onnx_path():
    """真实 ONNX 模型绝对路径，所有 AI 推理测试统一使用。"""
    return str(PROJECT_ROOT / "data" / "models" / "yolov8.onnx")
