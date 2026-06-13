from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
import types
import sys

import pytest

from app.services.training_service import TrainingService


@pytest.fixture
def training_repo():
    async def update(training, update_data):
        for field, value in update_data.items():
            setattr(training, field, value)
        return training

    return SimpleNamespace(
        create=AsyncMock(),
        get_by_id=AsyncMock(),
        update=AsyncMock(side_effect=update),
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
    assert training.training_type == "fire_extinguisher"
    assert training.status == "pending"
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
    training_repo.update.assert_awaited_once_with(
        training,
        {
            "video_path": "/tmp/video.mp4",
            "status": "processing",
        },
    )


@pytest.mark.asyncio
async def test_complete_training_rejects_missing_video_file(
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

    monkeypatch.setattr("app.services.training_service.os.path.exists", lambda path: False)

    with pytest.raises(ValueError, match="视频文件不存在"):
        await service.complete_training_with_ai_analysis(training_id=1, use_ai_scoring=True)

    training_repo.update.assert_not_called()


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
        status="processing",
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
    close_called = {"value": False}

    fake_inference = SimpleNamespace(
        analyze_video=lambda **kwargs: {
            "analysis_summary": {
                "supports_extinguisher_detection": True,
                "completed_steps_count": 3,
                "video_duration": 120.0,
                "validity_checks": {
                    "has_extinguisher": True,
                    "has_pose": True,
                    "has_step_signal": True,
                },
                "step_feature_summary": {
                    "step1": {"completed": True, "confidence": 90, "pose_quality_score": 80},
                },
                "pose_stats_summary": {
                    "body": {"stability": 25.0},
                },
            },
            "total_detections": 8,
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

        @staticmethod
        def generate_real_suggestions(summary, step_scores):
            return ["保持稳定", "继续练习"]

    monkeypatch.setitem(
        sys.modules,
        "app.ai.training_inference_service",
        types.SimpleNamespace(TrainingInferenceService=FakeTrainingInferenceService),
    )
    monkeypatch.setattr(
        "app.services.training_service.LLMScoringService.from_settings",
        lambda: None,
    )

    result = await service.complete_training_with_ai_analysis(training_id=7, use_ai_scoring=True)

    assert result["used_ai_scoring"] is True
    assert result["total_score"] > 0
    assert result["scoring_result"]["score_source"] == "rule"
    assert training.status == "done"
    assert close_called["value"] is True
    training_repo.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_complete_training_returns_zero_score_when_ai_analysis_raises(
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
    assert result["total_score"] == 0.0
    assert "视频分析失败" in result["feedback"]
    assert result["scoring_result"]["score_source"] == "zero"


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


def test_validate_detection_rejects_when_no_pose_and_no_extinguisher(service):
    """当模型支持灭火器检测但两者都缺失时，无有效证据，拒绝评分。"""
    result = service._validate_detection_result(
        {
            "supports_extinguisher_detection": True,
            "completed_steps_count": 0,
            "video_duration": 30,
            "validity_checks": {
                "has_extinguisher": False,
                "has_pose": False,
                "has_step_signal": False,
            },
        }
    )

    assert result == {"is_valid": False, "reason": "视频中未检测到人体姿态和灭火器，无有效证据"}


def test_validate_detection_allows_pose_fallback_when_model_has_no_extinguisher(service):
    result = service._validate_detection_result(
        {
            "supports_extinguisher_detection": False,
            "completed_steps_count": 2,
            "video_duration": 30,
            "validity_checks": {
                "has_extinguisher": False,
                "has_pose": True,
                "has_step_signal": True,
            },
        }
    )

    assert result == {"is_valid": True, "reason": ""}


def test_validate_detection_rejects_when_video_too_short(service):
    """视频时长 < 8s 无法形成有效时序。"""
    result = service._validate_detection_result(
        {
            "supports_extinguisher_detection": True,
            "completed_steps_count": 0,
            "video_duration": 5,
            "validity_checks": {
                "has_extinguisher": True,
                "has_pose": True,
                "has_step_signal": True,
            },
        }
    )

    assert result == {"is_valid": False, "reason": "视频时长过短（不足 8 秒），无法完成评估"}


def test_validate_detection_passes_with_partial_step_signal(service):
    """只要有任一证据（姿态/灭火器），即使步骤未完整识别也放行，由规则+LLM 评分。"""
    result = service._validate_detection_result(
        {
            "supports_extinguisher_detection": True,
            "completed_steps_count": 0,
            "video_duration": 30,
            "validity_checks": {
                "has_extinguisher": False,
                "has_pose": True,
                "has_step_signal": False,
            },
        }
    )

    assert result == {"is_valid": True, "reason": ""}


@pytest.mark.asyncio
async def test_generate_zero_score_result_returns_standard_structure(service):
    result = await service._generate_zero_score_result(
        training_type="fire_extinguisher",
        reason="未识别到有效步骤特征",
        analysis_result={"analysis_summary": {"completed_steps_count": 0}},
    )

    assert result["total_score"] == 0.0
    assert result["performance_level"] == "fail"
    assert result["score_source"] == "zero"
    assert result["analysis_summary"]["completed_steps_count"] == 0
    assert result["suggestions"]


@pytest.mark.asyncio
async def test_score_with_llm_or_fallback_uses_llm_result(service, monkeypatch):
    baseline_rule_result = {
        "total_score": 78.0,
        "performance_level": "pass",
        "dimension_scores": {"action_completeness": {"score": 80.0}},
        "step_scores": {"step1": {"score": 80.0}},
        "feedback": "规则评分反馈",
    }

    class FakeRuleEngine:
        async def evaluate(self, summary):
            return dict(baseline_rule_result)

    class FakeTrainingInferenceService:
        @staticmethod
        def generate_real_suggestions(summary, step_scores):
            return ["规则建议"]

    fake_llm_service = SimpleNamespace(
        score_training=AsyncMock(
            return_value={
                "total_score": 92.0,
                "performance_level": "excellent",
                "step_scores": {"step1": {"score": 95.0}},
                "feedback": "LLM 评分反馈",
            }
        )
    )

    monkeypatch.setitem(
        sys.modules,
        "app.ai.rule_engine",
        types.SimpleNamespace(RuleEngine=FakeRuleEngine),
    )
    monkeypatch.setitem(
        sys.modules,
        "app.ai.training_inference_service",
        types.SimpleNamespace(TrainingInferenceService=FakeTrainingInferenceService),
    )
    monkeypatch.setattr(
        "app.services.training_service.LLMScoringService.from_settings",
        lambda: fake_llm_service,
    )

    result = await service._score_with_llm_or_fallback(
        {
            "analysis_summary": {
                "step_feature_summary": {"step1": {"completed": True}},
                "completed_steps_count": 3,
            }
        },
        allow_llm=True,
    )

    assert result["score_source"] == "llm"
    assert result["total_score"] == 92.0
    assert result["performance_level"] == "excellent"
    assert result["suggestions"] == ["规则建议"]
    assert result["dimension_scores"] == baseline_rule_result["dimension_scores"]


@pytest.mark.asyncio
async def test_score_with_llm_or_fallback_falls_back_to_rule_when_llm_fails(service, monkeypatch):
    baseline_rule_result = {
        "total_score": 74.0,
        "performance_level": "pass",
        "dimension_scores": {"action_completeness": {"score": 76.0}},
        "step_scores": {"step1": {"score": 72.0}},
        "feedback": "规则评分反馈",
    }

    class FakeRuleEngine:
        async def evaluate(self, summary):
            return dict(baseline_rule_result)

    class FakeTrainingInferenceService:
        @staticmethod
        def generate_real_suggestions(summary, step_scores):
            return ["规则建议"]

    fake_llm_service = SimpleNamespace(
        score_training=AsyncMock(side_effect=RuntimeError("llm boom"))
    )

    monkeypatch.setitem(
        sys.modules,
        "app.ai.rule_engine",
        types.SimpleNamespace(RuleEngine=FakeRuleEngine),
    )
    monkeypatch.setitem(
        sys.modules,
        "app.ai.training_inference_service",
        types.SimpleNamespace(TrainingInferenceService=FakeTrainingInferenceService),
    )
    monkeypatch.setattr(
        "app.services.training_service.LLMScoringService.from_settings",
        lambda: fake_llm_service,
    )

    result = await service._score_with_llm_or_fallback(
        {
            "analysis_summary": {
                "step_feature_summary": {"step1": {"completed": True}},
                "completed_steps_count": 3,
            }
        },
        allow_llm=True,
    )

    assert result["score_source"] == "rule"
    assert result["total_score"] == 74.0
    assert result["feedback"] == "规则评分反馈"
    assert result["suggestions"] == ["规则建议"]


@pytest.mark.asyncio
async def test_complete_training_returns_zero_score_when_detection_has_no_pose(
    service, training_repo, monkeypatch
):
    training = SimpleNamespace(
        id=11,
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

    class FakeTrainingInferenceService:
        def __init__(self, **kwargs):
            pass

        def analyze_video(self, **kwargs):
            return {
                "analysis_summary": {
                    "supports_extinguisher_detection": True,
                    "completed_steps_count": 0,
                    "video_duration": 28,
                    "validity_checks": {
                        "has_extinguisher": False,
                        "has_pose": False,
                        "has_step_signal": True,
                    },
                }
            }

        def close(self):
            return None

        @staticmethod
        def generate_real_suggestions(summary, step_scores):
            return []

    monkeypatch.setitem(
        sys.modules,
        "app.ai.training_inference_service",
        types.SimpleNamespace(TrainingInferenceService=FakeTrainingInferenceService),
    )

    result = await service.complete_training_with_ai_analysis(training_id=11, use_ai_scoring=True)

    assert result["total_score"] == 0.0
    assert result["used_ai_scoring"] is False
    assert "无有效证据" in result["feedback"]
    assert result["scoring_result"]["score_source"] == "zero"
