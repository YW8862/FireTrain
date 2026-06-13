from unittest.mock import AsyncMock

import httpx
import pytest

from app.ai.llm_scoring_service import LLMScoringService


@pytest.fixture
def service():
    return LLMScoringService(
        api_key="test-key",
        base_url="https://example.com/v1",
        model="demo-model",
        timeout=5.0,
    )


def test_build_user_prompt_includes_baseline_and_evidence(service):
    prompt = service._build_user_prompt(
        {
            "analysis_summary": {
                "video_duration": 120,
                "processed_frames": 100,
                "pose_frame_count": 30,
                "completed_steps_count": 3,
                "completed_steps": ["step1", "step2", "step3"],
                "missing_steps": ["step4"],
                "detection_stats": {
                    "fire_extinguisher": {
                        "frame_count": 60,
                        "detection_count": 80,
                        "average_confidence": 0.85,
                    }
                },
                "pose_stats_summary": {
                    "right_arm": {"mean": 120.0, "min": 90.0, "max": 150.0, "stability": 25.0}
                },
                "step_feature_summary": {
                    "step1": {"completed": True, "confidence": 90, "duration": 8.0, "pose_quality_score": 88.0},
                    "step2": {"completed": True, "confidence": 85, "duration": 6.0, "pose_quality_score": 80.0},
                },
            }
        },
        baseline_score={
            "total_score": 78.0,
            "performance_level": "good",
            "dimension_scores": {"action_completeness": {"score": 80.0}},
            "step_scores": {"step1": {"score": 80.0}},
        },
    )

    assert "video_duration=120" in prompt
    assert "right_arm: mean=120.0" in prompt
    assert "准备阶段: completed=True" in prompt
    assert "【规则引擎基线分】" in prompt
    assert "78.0" in prompt
    assert "【重要】规则引擎基线分仅供参考" in prompt


def test_build_user_prompt_omits_evidence_hint_when_data_is_sparse(service):
    prompt = service._build_user_prompt(
        {
            "analysis_summary": {
                "video_duration": 30,
                "processed_frames": 0,
                "pose_frame_count": 0,
                "completed_steps_count": 0,
                "detection_stats": {},
                "pose_stats_summary": {},
                "step_feature_summary": {},
            }
        }
    )

    assert "视频中几乎没有有效证据" in prompt


def test_build_user_prompt_uses_all_six_step_definitions(service):
    prompt = service._build_user_prompt(
        {
            "analysis_summary": {
                "video_duration": 90,
                "processed_frames": 60,
                "pose_frame_count": 30,
                "completed_steps_count": 0,
                "detection_stats": {},
                "pose_stats_summary": {},
                "step_feature_summary": {},
            }
        }
    )

    for step_name in ["准备阶段", "提灭火器", "拔保险销", "握喷管", "瞄准火源", "压把手"]:
        assert step_name in prompt


def test_build_user_prompt_includes_evidence_hint_for_partial_steps(service):
    prompt = service._build_user_prompt(
        {
            "analysis_summary": {
                "video_duration": 90,
                "processed_frames": 100,
                "pose_frame_count": 60,
                "completed_steps_count": 2,
                "detection_stats": {
                    "fire_extinguisher": {"frame_count": 40, "detection_count": 50, "average_confidence": 0.9}
                },
                "pose_stats_summary": {},
                "step_feature_summary": {},
            }
        }
    )

    assert "【证据强度提示】" in prompt
    assert "状态机仅识别出 2/6 个完整步骤" in prompt


def test_parse_llm_response_handles_markdown_and_normalizes_defaults(service):
    result = service._parse_llm_response(
        """```json
{
  "total_score": "88.5",
  "performance_level": "good",
  "step_scores": {
    "step1": {
      "step_name": "准备阶段",
      "score": "59",
      "feedback": "反应稍慢"
    },
    "step2": {
      "step_name": "提灭火器",
      "score": 92,
      "is_correct": true,
      "feedback": "动作到位"
    }
  },
  "feedback": "整体良好",
  "suggestions": "继续加强瞄准练习"
}
```"""
    )

    assert result["total_score"] == 88.5
    assert result["step_scores"]["step1"]["score"] == 59.0
    assert result["step_scores"]["step1"]["is_correct"] is False
    assert result["step_scores"]["step2"]["is_correct"] is True
    assert result["suggestions"] == ["继续加强瞄准练习"]


def test_parse_llm_response_requires_expected_fields(service):
    with pytest.raises(RuntimeError, match="缺少必要字段"):
        service._parse_llm_response('{"total_score": 90}')


def test_parse_llm_response_raises_for_invalid_json(service):
    with pytest.raises(RuntimeError, match="无法解析评分结果"):
        service._parse_llm_response("not json")


def test_compute_pose_stats_returns_empty_for_no_pose_results():
    # _compute_pose_stats 已在重构中移除，姿态统计由调用方（rule_engine）预处理后传入
    pass


@pytest.mark.asyncio
async def test_score_training_orchestrates_internal_steps(service, monkeypatch):
    built_prompt = "built prompt"
    parsed_result = {"total_score": 90.0}
    call_llm = AsyncMock(return_value="raw")

    monkeypatch.setattr(service, "_build_user_prompt", lambda *args, **kwargs: built_prompt)
    monkeypatch.setattr(service, "_call_llm", call_llm)
    monkeypatch.setattr(service, "_parse_llm_response", lambda raw: parsed_result)

    result = await service.score_training({"video_duration": 100})

    assert result == parsed_result
    call_llm.assert_awaited_once_with(built_prompt)


@pytest.mark.asyncio
async def test_call_llm_wraps_http_status_errors(service, monkeypatch):
    request = httpx.Request("POST", "https://example.com/v1/chat/completions")
    response = httpx.Response(
        status_code=401,
        request=request,
        json={"error": {"message": "bad api key"}},
    )

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, json, headers):
            raise httpx.HTTPStatusError("boom", request=request, response=response)

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    with pytest.raises(RuntimeError, match="HTTP 401"):
        await service._call_llm("prompt")


@pytest.mark.asyncio
async def test_call_llm_wraps_http_status_without_json_error_detail(service, monkeypatch):
    request = httpx.Request("POST", "https://example.com/v1/chat/completions")
    response = httpx.Response(status_code=500, request=request, text="plain error")

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, json, headers):
            raise httpx.HTTPStatusError("boom", request=request, response=response)

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    with pytest.raises(RuntimeError, match="HTTP 500"):
        await service._call_llm("prompt")


@pytest.mark.asyncio
async def test_call_llm_returns_message_content(service, monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [{"message": {"content": '{"total_score": 90}'}}],
                "usage": {"total_tokens": 12},
            }

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, json, headers):
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    result = await service._call_llm("prompt")

    assert result == '{"total_score": 90}'


@pytest.mark.asyncio
async def test_call_llm_wraps_timeout_errors(service, monkeypatch):
    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, json, headers):
            raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    with pytest.raises(RuntimeError, match="请求超时"):
        await service._call_llm("prompt")


@pytest.mark.asyncio
async def test_call_llm_wraps_unexpected_errors(service, monkeypatch):
    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, json, headers):
            raise ValueError("unexpected")

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    with pytest.raises(RuntimeError, match="调用异常"):
        await service._call_llm("prompt")


def test_from_settings_returns_none_without_api_key(monkeypatch):
    fake_settings = type(
        "FakeSettings",
        (),
        {
            "LLM_API_KEY": "",
            "LLM_BASE_URL": "https://demo/v1",
            "LLM_MODEL": "demo-model",
            "LLM_TIMEOUT": 30.0,
        },
    )()

    monkeypatch.setattr("app.core.config.settings", fake_settings)

    assert LLMScoringService.from_settings() is None


def test_from_settings_builds_service_when_api_key_exists(monkeypatch):
    fake_settings = type(
        "FakeSettings",
        (),
        {
            "LLM_API_KEY": "configured-key",
            "LLM_BASE_URL": "https://demo/v1",
            "LLM_MODEL": "demo-model",
            "LLM_TIMEOUT": 30.0,
        },
    )()

    monkeypatch.setattr("app.core.config.settings", fake_settings)

    service = LLMScoringService.from_settings()

    assert service is not None
    assert service.api_key == "configured-key"
    assert service.base_url == "https://demo/v1"
