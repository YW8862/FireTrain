"""管理员视频上传与后台分析测试。"""

import asyncio
import uuid
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.admin_videos import process_admin_video_analysis
from app.db.base import Base
from app.db.session import async_session_maker, engine
from app.main import app
from app.models.user import User
from app.services.training_service import TrainingService

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """测试前创建数据库表。"""

    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_setup())
    yield
    asyncio.run(engine.dispose())


def create_test_user(role: str = "student") -> tuple[str, dict]:
    """创建测试用户并返回 token 与基本信息。"""
    unique_id = str(uuid.uuid4())[:8]
    username = f"admin_video_{role}_{unique_id}"
    email = f"{username}@example.com"
    password = "test123456"

    register_response = client.post(
        "/api/user/register",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )
    assert register_response.status_code == 201

    async def _promote_role():
        async with async_session_maker() as session:
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalar_one()
            user.role = role
            await session.commit()

    if role != "student":
        asyncio.run(_promote_role())

    login_response = client.post(
        "/api/user/login",
        data={"username": username, "password": password},
    )
    assert login_response.status_code == 200
    return login_response.json()["token"], {"username": username, "email": email}


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _patch_upload_dependencies(monkeypatch, tmp_path, scheduled_coroutines: list):
    saved_video_path = tmp_path / f"admin-upload-{uuid.uuid4().hex[:8]}.mp4"
    original_create_task = asyncio.create_task

    async def fake_save_upload_file(file, target_dir, filename=None):
        saved_video_path.write_bytes(b"admin-video-content")
        return SimpleNamespace(
            file_path=str(saved_video_path),
            file_size=saved_video_path.stat().st_size,
            save_duration_ms=11,
        )

    def fake_create_task(coro):
        if getattr(getattr(coro, "cr_code", None), "co_name", "") == "process_admin_video_analysis":
            scheduled_coroutines.append(coro)
            coro.close()
            return original_create_task(asyncio.sleep(0))
        return original_create_task(coro)

    monkeypatch.setattr("app.api.admin_videos.save_upload_file", fake_save_upload_file)
    monkeypatch.setattr("asyncio.create_task", fake_create_task)


def test_admin_upload_returns_processing_and_starts_background_task(monkeypatch, tmp_path):
    """管理员上传成功后应返回 processing，并启动后台任务。"""
    admin_token, _ = create_test_user(role="admin")
    _, target_user = create_test_user(role="student")
    scheduled_coroutines = []
    _patch_upload_dependencies(monkeypatch, tmp_path, scheduled_coroutines)

    response = client.post(
        "/api/admin/video/upload",
        headers=auth_headers(admin_token),
        data={"username": target_user["username"], "training_type": "extinguisher"},
        files={"file": ("demo.mp4", b"video-content", "video/mp4")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert data["username"] == target_user["username"]
    assert len(scheduled_coroutines) == 1

    status_response = client.get(
        f"/api/admin/video/status/{data['training_id']}",
        headers=auth_headers(admin_token),
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "processing"


def test_process_admin_video_analysis_updates_status_to_done(monkeypatch, tmp_path):
    """后台分析成功后，管理员状态接口应返回 done。"""
    admin_token, _ = create_test_user(role="admin")
    _, target_user = create_test_user(role="student")
    scheduled_coroutines = []
    _patch_upload_dependencies(monkeypatch, tmp_path, scheduled_coroutines)

    upload_response = client.post(
        "/api/admin/video/upload",
        headers=auth_headers(admin_token),
        data={"username": target_user["username"], "training_type": "extinguisher"},
        files={"file": ("demo.mp4", b"video-content", "video/mp4")},
    )
    training_id = upload_response.json()["training_id"]

    async def fake_complete_training(self, training_id: int, use_ai_scoring: bool = True):
        training = await self.training_repo.get_by_id(training_id)
        await self.training_repo.update(
            training,
            {
                "status": "done",
                "total_score": Decimal("92.50"),
                "feedback": "管理员上传视频分析完成",
                "completed_at": datetime.utcnow(),
                "step_scores": {
                    "_performance_level": "excellent",
                    "_analysis_summary": {"completed_steps_count": 6},
                },
            },
        )
        return {
            "status": "done",
            "total_score": 92.5,
            "feedback": "管理员上传视频分析完成",
        }

    monkeypatch.setattr(TrainingService, "complete_training_with_ai_analysis", fake_complete_training)

    asyncio.run(process_admin_video_analysis(training_id))

    status_response = client.get(
        f"/api/admin/video/status/{training_id}",
        headers=auth_headers(admin_token),
    )
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["status"] == "done"
    assert status_data["total_score"] == 92.5
    assert status_data["performance_level"] == "excellent"
    assert status_data["analysis_summary"]["completed_steps_count"] == 6


def test_process_admin_video_analysis_updates_status_to_failed(monkeypatch, tmp_path):
    """后台分析失败后，管理员状态接口应返回 failed。"""
    admin_token, _ = create_test_user(role="admin")
    _, target_user = create_test_user(role="student")
    scheduled_coroutines = []
    _patch_upload_dependencies(monkeypatch, tmp_path, scheduled_coroutines)

    upload_response = client.post(
        "/api/admin/video/upload",
        headers=auth_headers(admin_token),
        data={"username": target_user["username"], "training_type": "extinguisher"},
        files={"file": ("demo.mp4", b"video-content", "video/mp4")},
    )
    training_id = upload_response.json()["training_id"]

    async def fake_complete_training(self, training_id: int, use_ai_scoring: bool = True):
        raise RuntimeError("mock ai failure")

    monkeypatch.setattr(TrainingService, "complete_training_with_ai_analysis", fake_complete_training)

    asyncio.run(process_admin_video_analysis(training_id))

    status_response = client.get(
        f"/api/admin/video/status/{training_id}",
        headers=auth_headers(admin_token),
    )
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["status"] == "failed"
    assert "mock ai failure" in status_data["feedback"]
