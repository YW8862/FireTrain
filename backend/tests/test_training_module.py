"""训练模块 API 接口测试。"""

import asyncio
import sys
import types
import uuid
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

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
    """创建测试用户并返回 token 与用户信息。"""
    unique_id = str(uuid.uuid4())[:8]
    username = f"training_{role}_{unique_id}"
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
    token = login_response.json()["token"]
    return token, {"username": username, "email": email}


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_training_endpoints_require_authentication():
    """训练接口应要求 Bearer Token 认证。"""
    start_response = client.post(
        "/api/training/start",
        json={"training_type": "extinguisher", "duration_seconds": 120},
    )
    assert start_response.status_code == 401

    history_response = client.get("/api/training/history")
    assert history_response.status_code == 401


def test_user_can_cancel_unfinished_training_and_remove_record():
    """普通用户取消未完成训练后，不应保留未开始记录。"""
    token, _ = create_test_user()
    headers = auth_headers(token)

    start_response = client.post(
        "/api/training/start",
        headers=headers,
        json={"training_type": "fire_extinguisher", "duration_seconds": 120},
    )
    assert start_response.status_code == 200
    training_id = start_response.json()["training_id"]

    delete_response = client.delete(f"/api/training/{training_id}", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["training_id"] == training_id

    history_response = client.get("/api/training/history", headers=headers)
    assert history_response.status_code == 200
    assert history_response.json()["records"] == []


def test_authenticated_training_workflow_with_file_upload_precheck_complete_and_detail(
    monkeypatch,
    tmp_path,
):
    """带认证覆盖：登录 -> 开始 -> 上传文件 -> 预检测 -> 完成 -> 查看详情。"""
    token, _ = create_test_user()
    headers = auth_headers(token)
    saved_video_path = tmp_path / "workflow-training.webm"

    start_response = client.post(
        "/api/training/start",
        headers=headers,
        json={"training_type": "extinguisher", "duration_seconds": 180},
    )
    assert start_response.status_code == 200
    training_id = start_response.json()["training_id"]

    async def fake_save_upload_file(file, target_dir, filename=None):
        saved_video_path.write_bytes(b"fake-video-content")
        return SimpleNamespace(
            file_path=str(saved_video_path),
            file_size=saved_video_path.stat().st_size,
            save_duration_ms=8,
        )

    async def fake_run_in_threadpool(func):
        return {
            "analysis_summary": {
                "supports_extinguisher_detection": True,
                "completed_steps_count": 3,
                "video_duration": 22,
                "validity_checks": {
                    "has_extinguisher": True,
                    "has_pose": True,
                    "has_step_signal": True,
                },
            }
        }

    class FakeTrainingInferenceService:
        def __init__(self, **kwargs):
            pass

        def analyze_video(self, **kwargs):
            return {
                "analysis_summary": {
                    "supports_extinguisher_detection": True,
                    "completed_steps_count": 3,
                    "video_duration": 22,
                    "validity_checks": {
                        "has_extinguisher": True,
                        "has_pose": True,
                        "has_step_signal": True,
                    },
                }
            }

        def close(self):
            return None

    async def fake_complete_training(self, training_id: int, use_ai_scoring: bool = True):
        assert use_ai_scoring is True
        training = await self.training_repo.get_by_id(training_id)
        completed_at = datetime.utcnow()
        persisted_step_scores = {
            "step1": {
                "step_name": "准备阶段",
                "score": 90.0,
                "is_correct": True,
                "feedback": "准备动作完整",
                "weight": 0.15,
            },
            "_suggestions": ["继续保持压把动作稳定"],
            "_dimension_scores": {
                "action_completeness": {"score": 91.0, "weight": 0.4, "comment": "步骤完成较好"},
                "pose_standardization": {"score": 87.0, "weight": 0.4, "comment": "姿态基本规范"},
                "timeliness": {"score": 82.0, "weight": 0.2, "comment": "时序稳定"},
            },
            "_performance_level": "good",
            "_analysis_summary": {"completed_steps_count": 3},
        }
        await self.training_repo.update(
            training,
            {
                "status": "done",
                "total_score": Decimal("88.50"),
                "step_scores": persisted_step_scores,
                "feedback": "整体动作较规范，可继续优化瞄准稳定性。",
                "completed_at": completed_at,
            },
        )
        return {
            "status": "done",
            "total_score": 88.5,
            "feedback": "整体动作较规范，可继续优化瞄准稳定性。",
            "used_ai_scoring": True,
            "scoring_result": {
                "total_score": 88.5,
                "performance_level": "good",
                "dimension_scores": persisted_step_scores["_dimension_scores"],
                "step_scores": {"step1": persisted_step_scores["step1"]},
                "feedback": "整体动作较规范，可继续优化瞄准稳定性。",
                "suggestions": ["继续保持压把动作稳定"],
            },
        }

    monkeypatch.setattr("app.api.training.save_upload_file", fake_save_upload_file)
    monkeypatch.setattr("app.api.training.run_in_threadpool", fake_run_in_threadpool)
    monkeypatch.setitem(
        sys.modules,
        "app.ai.training_inference_service",
        types.SimpleNamespace(TrainingInferenceService=FakeTrainingInferenceService),
    )
    monkeypatch.setattr(TrainingService, "complete_training_with_ai_analysis", fake_complete_training)

    upload_response = client.post(
        f"/api/training/upload-file/{training_id}",
        headers=headers,
        files={"file": ("training.webm", b"binary-video", "video/webm")},
    )
    assert upload_response.status_code == 200
    assert upload_response.json()["status"] == "processing"
    assert upload_response.json()["video_path"] == str(saved_video_path)

    precheck_response = client.post(f"/api/training/precheck/{training_id}", headers=headers)
    assert precheck_response.status_code == 200
    assert precheck_response.json() == {"is_valid": True, "reason": ""}

    complete_response = client.post(f"/api/training/complete/{training_id}", headers=headers)
    assert complete_response.status_code == 200
    complete_data = complete_response.json()
    assert complete_data["status"] == "done"
    assert complete_data["used_ai_scoring"] is True
    assert complete_data["scoring_details"]["performance_level"] == "good"

    detail_response = client.get(f"/api/training/{training_id}", headers=headers)
    assert detail_response.status_code == 200
    detail_data = detail_response.json()
    assert detail_data["id"] == training_id
    assert detail_data["status"] == "done"
    assert detail_data["performance_level"] == "good"
    assert detail_data["suggestions"] == ["继续保持压把动作稳定"]
    assert detail_data["dimension_scores"]["action_completeness"]["score"] == 91.0
    assert detail_data["analysis_summary"]["completed_steps_count"] == 3

    history_response = client.get("/api/training/history", headers=headers)
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert history_data["total"] >= 1
    assert any(record["id"] == training_id for record in history_data["records"])


def test_training_invalid_record_returns_404_with_authentication():
    """带认证访问不存在的训练记录时返回 404。"""
    token, _ = create_test_user()
    headers = auth_headers(token)

    complete_response = client.post("/api/training/complete/99999", headers=headers)
    assert complete_response.status_code == 404

    detail_response = client.get("/api/training/99999", headers=headers)
    assert detail_response.status_code == 404


def test_precheck_returns_invalid_when_analysis_fails(monkeypatch):
    """预检测异常时不应静默放行。"""
    token, _ = create_test_user()
    headers = auth_headers(token)

    start_response = client.post(
        "/api/training/start",
        headers=headers,
        json={"training_type": "extinguisher", "duration_seconds": 120},
    )
    training_id = start_response.json()["training_id"]

    upload_response = client.post(
        "/api/training/upload",
        headers=headers,
        json={
            "training_id": training_id,
            "video_path": "/tmp/nonexistent.webm",
        },
    )
    assert upload_response.status_code == 200

    async def fake_run_in_threadpool(func):
        raise RuntimeError("mock precheck failure")

    monkeypatch.setattr("app.api.training.run_in_threadpool", fake_run_in_threadpool)
    monkeypatch.setitem(
        sys.modules,
        "app.ai.training_inference_service",
        types.SimpleNamespace(TrainingInferenceService=type(
            "FakeTrainingInferenceService",
            (),
            {
                "__init__": lambda self, **kwargs: None,
                "analyze_video": lambda self, **kwargs: {"analysis_summary": {}},
                "close": lambda self: None,
            },
        )),
    )

    precheck_response = client.post(f"/api/training/precheck/{training_id}", headers=headers)
    assert precheck_response.status_code == 200
    assert precheck_response.json() == {
        "is_valid": False,
        "reason": "预检测失败：mock precheck failure",
    }
