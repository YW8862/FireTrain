"""训练模块 API 接口测试"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.session import engine
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """测试前创建数据库表"""
    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    asyncio.run(_setup())
    yield
    # 测试后清理数据库
    asyncio.run(engine.dispose())


def test_start_training():
    """测试开始训练"""
    response = client.post(
        "/api/training/start",
        json={
            "training_type": "extinguisher",
            "duration_seconds": 120.5
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "training_id" in data
    assert data["status"] == "created"
    assert "message" in data


def test_upload_video():
    """测试上传视频（路径方式）"""
    # 先创建训练
    start_response = client.post(
        "/api/training/start",
        json={"training_type": "extinguisher"}
    )
    training_id = start_response.json()["training_id"]
    
    # 上传视频
    upload_response = client.post(
        "/api/training/upload",
        json={
            "training_id": training_id,
            "video_path": "/path/to/video.mp4"
        }
    )
    assert upload_response.status_code == 200
    data = upload_response.json()
    assert data["status"] == "processing"
    assert data["video_path"] == "/path/to/video.mp4"


def test_complete_training_with_mock_score():
    """测试完成训练并获取模拟分数"""
    # 创建训练
    start_response = client.post(
        "/api/training/start",
        json={"training_type": "extinguisher"}
    )
    training_id = start_response.json()["training_id"]
    
    # 完成训练
    complete_response = client.post(f"/api/training/complete/{training_id}")
    assert complete_response.status_code == 200
    data = complete_response.json()
    
    assert data["status"] == "done"
    assert "total_score" in data
    assert 0 <= data["total_score"] <= 100
    assert "feedback" in data
    assert "scoring_details" in data
    
    # 验证评分详情
    scoring = data["scoring_details"]
    assert "total_score" in scoring
    assert "step_scores" in scoring
    assert "feedback" in scoring


def test_get_training_detail():
    """测试获取训练详情"""
    # 创建并完成训练
    start_response = client.post(
        "/api/training/start",
        json={"training_type": "extinguisher"}
    )
    training_id = start_response.json()["training_id"]
    
    client.post(f"/api/training/complete/{training_id}")
    
    # 获取详情
    detail_response = client.get(f"/api/training/{training_id}")
    assert detail_response.status_code == 200
    data = detail_response.json()
    
    assert data["id"] == training_id
    assert data["status"] == "done"
    assert "training_type" in data
    assert "total_score" in data
    assert "feedback" in data


def test_get_training_history():
    """测试获取训练历史"""
    # 创建多个训练记录
    for i in range(3):
        client.post(
            "/api/training/start",
            json={"training_type": "extinguisher"}
        )
    
    # 获取历史记录
    history_response = client.get("/api/training/history")
    assert history_response.status_code == 200
    data = history_response.json()
    
    assert "total" in data
    assert data["total"] >= 3
    assert "records" in data
    assert len(data["records"]) >= 3
    
    # 验证分页
    assert "page" in data
    assert "page_size" in data


def test_get_training_history_with_filter():
    """测试带筛选的训练历史查询"""
    # 创建训练并完成
    start_response = client.post(
        "/api/training/start",
        json={"training_type": "extinguisher"}
    )
    training_id = start_response.json()["training_id"]
    client.post(f"/api/training/complete/{training_id}")
    
    # 按状态筛选
    history_response = client.get(
        "/api/training/history",
        params={"status": "done"}
    )
    assert history_response.status_code == 200
    data = history_response.json()
    
    assert data["total"] >= 1
    # 所有记录都应该是 done 状态
    for record in data["records"]:
        assert record["status"] == "done"


def test_upload_video_invalid_training():
    """测试上传视频到不存在的训练"""
    upload_response = client.post(
        "/api/training/upload",
        json={
            "training_id": 99999,
            "video_path": "/path/to/video.mp4"
        }
    )
    assert upload_response.status_code == 404


def test_complete_invalid_training():
    """测试完成不存在的训练"""
    complete_response = client.post("/api/training/complete/99999")
    assert complete_response.status_code == 404


def test_training_workflow():
    """测试完整的训练流程"""
    # 1. 开始训练
    start_response = client.post(
        "/api/training/start",
        json={
            "training_type": "extinguisher",
            "duration_seconds": 180
        }
    )
    assert start_response.status_code == 200
    training_id = start_response.json()["training_id"]
    
    # 2. 上传视频
    upload_response = client.post(
        "/api/training/upload",
        json={
            "training_id": training_id,
            "video_path": "/videos/test.mp4"
        }
    )
    assert upload_response.status_code == 200
    
    # 3. 完成训练
    complete_response = client.post(f"/api/training/complete/{training_id}")
    assert complete_response.status_code == 200
    
    # 4. 查看详情
    detail_response = client.get(f"/api/training/{training_id}")
    assert detail_response.status_code == 200
    data = detail_response.json()
    
    # 验证完整流程
    assert data["status"] == "done"
    assert data["video_path"] == "/videos/test.mp4"
    assert float(data["total_score"]) > 0
    assert data["feedback"] is not None
    assert data["completed_at"] is not None
