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


def test_compute_pose_stats_filters_non_numeric_values(service):
    stats = service._compute_pose_stats(
        [
            {"angles": {"right_arm": 100, "body": 90}},
            {"angles": {"right_arm": 140.5, "body": "skip", "left_arm": 80}},
            {"angles": {"left_arm": None}},
        ]
    )

    assert stats["right_arm"] == {
        "mean": 120.25,
        "min": 100.0,
        "max": 140.5,
        "count": 2,
    }
    assert stats["body"]["mean"] == 90.0
    assert stats["left_arm"]["mean"] == 80.0


def test_build_user_prompt_deduplicates_steps_and_formats_pose_summary(service):
    prompt = service._build_user_prompt(
        {
            "video_duration": 45,
            "total_detections": 8,
            "pose_frame_count": 12,
            "processed_frames": 18,
            "step_sequence": [
                {"step_index": 1, "step_name": "准备阶段", "is_completed": True},
                {"step_index": 1, "step_name": "准备阶段", "is_completed": True},
                {"step_index": 2, "step_name": "提灭火器", "is_completed": False},
            ],
            "step_times": {"step1": 8.3, "step2": 12},
            "all_pose_results": [
                {"angles": {"right_arm": 95, "body": 92}},
                {"angles": {"right_arm": 155, "body": 88}},
            ],
        }
    )

    assert prompt.count("准备阶段") == 1
    assert "提灭火器：未完成" in prompt
    assert "右臂角度：平均 125.0°" in prompt
    assert "身体姿态角度：平均 90.0°" in prompt
    assert "操作过快，可能遗漏步骤" in prompt


def test_build_user_prompt_handles_missing_steps_and_torso_stats(service):
    prompt = service._build_user_prompt(
        {
            "video_duration": 180,
            "step_sequence": [],
            "all_pose_results": [
                {"angles": {"torso": 99, "right_knee": 110}},
                {"angles": {"torso": 101, "right_knee": 130}},
            ],
        }
    )

    assert "未检测到有效步骤" in prompt
    assert "身体姿态角度：平均 100.0°" in prompt
    assert "右膝角度：平均 120.0°" in prompt
    assert "操作时间过长，需加强熟练度" in prompt


def test_build_user_prompt_includes_left_arm_range(service):
    prompt = service._build_user_prompt(
        {
            "video_duration": 100,
            "step_sequence": [],
            "all_pose_results": [
                {"angles": {"left_arm": 70}},
                {"angles": {"left_arm": 90}},
            ],
        }
    )

    assert "左臂角度：平均 80.0°，范围 70.0°-90.0°" in prompt
    assert "操作时间合理" in prompt


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


def test_compute_pose_stats_returns_empty_for_no_pose_results(service):
    assert service._compute_pose_stats([]) == {}


@pytest.mark.asyncio
async def test_score_training_orchestrates_internal_steps(service, monkeypatch):
    built_prompt = "built prompt"
    parsed_result = {"total_score": 90.0}
    call_llm = AsyncMock(return_value="raw")

    monkeypatch.setattr(service, "_build_user_prompt", lambda payload: built_prompt)
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
