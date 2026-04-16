from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
import types
import sys

import pytest

from app.services.training_service import TrainingService


@pytest.fixture
def training_repo():
    return SimpleNamespace(
        create=AsyncMock(),
        get_by_id=AsyncMock(),
        update=AsyncMock(),
        get_user_history=AsyncMock(),
    )


@pytest.fixture
def service(training_repo):
    return TrainingService(training_repo)


@pytest.mark.asyncio
async def test_start_training_creates_training_record(service, training_repo):
    request = SimpleNamespace(training_type="extinguisher", duration_seconds=120)

    training = await service.start_training(user_id=12, request=request)

    assert training.user_id == 12
    assert training.training_type == "extinguisher"
    assert training.status == "created"
    assert training.duration_seconds == 120
    training_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_training_without_duration_field(service):
    request = SimpleNamespace(training_type="extinguisher")

    training = await service.start_training(user_id=5, request=request)

    assert training.duration_seconds is None


@pytest.mark.asyncio
async def test_upload_video_returns_none_when_training_missing(service, training_repo):
    training_repo.get_by_id.return_value = None

    result = await service.upload_video(training_id=99, video_path="/tmp/none.mp4")

    assert result is None
    training_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_upload_video_updates_status_and_path(service, training_repo):
    training = SimpleNamespace(video_path=None, status="created")
    training_repo.get_by_id.return_value = training

    result = await service.upload_video(training_id=1, video_path="/tmp/video.mp4")

    assert result is training
    assert training.video_path == "/tmp/video.mp4"
    assert training.status == "processing"
    training_repo.update.assert_awaited_once_with(training)


@pytest.mark.asyncio
async def test_complete_training_uses_mock_scoring_when_ai_not_available(
    service, training_repo, monkeypatch
):
    training = SimpleNamespace(
        id=1,
        user_id=9,
        training_type="extinguisher",
        status="processing",
        video_path="/tmp/demo.mp4",
        started_at=datetime.utcnow() - timedelta(seconds=95),
        total_score=None,
        step_scores=None,
        feedback=None,
        completed_at=None,
        duration_seconds=None,
    )
    training_repo.get_by_id.return_value = training
    training_repo.update = AsyncMock()

    monkeypatch.setattr("app.services.training_service.os.path.exists", lambda path: False)
    monkeypatch.setattr(
        service,
        "_generate_mock_scoring",
        lambda: {
            "total_score": 81.5,
            "step_scores": {"step_1": 80.0},
            "feedback": "模拟评分完成",
            "suggestions": ["继续练习"],
            "performance_level": "良好",
            "dimension_scores": {"accuracy": 80.0},
        },
    )

    result = await service.complete_training_with_ai_analysis(training_id=1, use_ai_scoring=True)

    assert result["status"] == "done"
    assert result["used_ai_scoring"] is False
    assert result["total_score"] == 81.5
    assert training.status == "done"
    assert training.feedback == "模拟评分完成"
    assert training.duration_seconds is not None
    training_repo.update.assert_awaited_once_with(training)


@pytest.mark.asyncio
async def test_complete_training_returns_none_when_training_missing(service, training_repo):
    training_repo.get_by_id.return_value = None

    result = await service.complete_training_with_ai_analysis(training_id=404)

    assert result is None
    training_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_complete_training_rejects_invalid_status(service, training_repo):
    training_repo.get_by_id.return_value = SimpleNamespace(
        status="done",
        video_path="/tmp/demo.mp4",
    )

    with pytest.raises(ValueError, match="当前状态不能完成训练"):
        await service.complete_training_with_ai_analysis(training_id=2)

    training_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_complete_training_requires_video_path(service, training_repo):
    training_repo.get_by_id.return_value = SimpleNamespace(
        status="created",
        video_path=None,
    )

    with pytest.raises(ValueError, match="视频路径为空"):
        await service.complete_training_with_ai_analysis(training_id=3)


@pytest.mark.asyncio
async def test_complete_training_uses_ai_scoring_when_video_exists(
    service, training_repo, monkeypatch
):
    training = SimpleNamespace(
        id=7,
        user_id=9,
        training_type="extinguisher",
        status="created",
        video_path="/tmp/demo.mp4",
        started_at=None,
        total_score=None,
        step_scores=None,
        feedback=None,
        completed_at=None,
        duration_seconds=None,
    )
    training_repo.get_by_id.return_value = training
    monkeypatch.setattr("app.services.training_service.os.path.exists", lambda path: True)
    close_called = {"value": False}

    fake_inference = SimpleNamespace(
        analyze_video=lambda **kwargs: {
            "total_detections": 8,
            "step_scores": {"step1": {"score": 80}},
            "suggestions": ["保持稳定"],
            "dimension_scores": {"accuracy": 88},
        },
        close=lambda: close_called.__setitem__("value", True),
    )

    class FakeTrainingInferenceService:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def analyze_video(self, **kwargs):
            return fake_inference.analyze_video(**kwargs)

        def close(self):
            return fake_inference.close()

    monkeypatch.setitem(
        sys.modules,
        "app.ai.training_inference_service",
        types.SimpleNamespace(TrainingInferenceService=FakeTrainingInferenceService),
    )

    result = await service.complete_training_with_ai_analysis(training_id=7, use_ai_scoring=True)

    assert result["used_ai_scoring"] is True
    assert result["total_score"] == 80
    assert result["scoring_result"]["performance_level"] == "良好"
    assert training.status == "done"
    assert close_called["value"] is True
    training_repo.update.assert_awaited_once_with(training)


@pytest.mark.asyncio
async def test_complete_training_falls_back_to_mock_when_ai_raises(
    service, training_repo, monkeypatch
):
    training = SimpleNamespace(
        id=8,
        user_id=9,
        training_type="extinguisher",
        status="processing",
        video_path="/tmp/demo.mp4",
        started_at=None,
        total_score=None,
        step_scores=None,
        feedback=None,
        completed_at=None,
        duration_seconds=None,
    )
    training_repo.get_by_id.return_value = training
    monkeypatch.setattr("app.services.training_service.os.path.exists", lambda path: True)
    monkeypatch.setattr(
        service,
        "_generate_mock_scoring",
        lambda: {
            "total_score": 70.0,
            "step_scores": {"step_1": 70.0},
            "feedback": "降级评分",
            "suggestions": ["继续练习"],
            "performance_level": "良好",
            "dimension_scores": {"accuracy": 70.0},
        },
    )

    class FakeTrainingInferenceService:
        def __init__(self, **kwargs):
            pass

        def analyze_video(self, **kwargs):
            raise RuntimeError("boom")

        def close(self):
            return None

    monkeypatch.setitem(
        sys.modules,
        "app.ai.training_inference_service",
        types.SimpleNamespace(TrainingInferenceService=FakeTrainingInferenceService),
    )

    result = await service.complete_training_with_ai_analysis(training_id=8, use_ai_scoring=True)

    assert result["used_ai_scoring"] is False
    assert result["feedback"] == "降级评分"


@pytest.mark.asyncio
async def test_get_user_training_history_caps_page_size(service, training_repo):
    training_repo.get_user_history.return_value = (["record"], 1)

    records, total = await service.get_user_training_history(
        user_id=3,
        page=2,
        page_size=999,
        status="done",
    )

    assert records == ["record"]
    assert total == 1
    training_repo.get_user_history.assert_awaited_once_with(
        user_id=3,
        page=2,
        page_size=50,
        status="done",
        start_date=None,
        end_date=None,
    )
