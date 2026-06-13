"""测试当前项目中的评分生成逻辑。"""
from types import SimpleNamespace

import pytest

from app.services.training_service import TrainingService


@pytest.fixture
def scoring_service():
    return TrainingService(SimpleNamespace())


def _patch_random(monkeypatch, *, total_score):
    values = iter(
        [
            total_score,
            91.0,
            82.0,
            76.0,
            88.0,
            79.0,
            84.0,
        ]
    )
    monkeypatch.setattr("app.services.training_service.random.uniform", lambda a, b: next(values))
    monkeypatch.setattr(
        "app.services.training_service.random.choice",
        lambda items: items[0],
    )
    monkeypatch.setattr("app.services.training_service.random.randint", lambda a, b: 2)
    monkeypatch.setattr(
        "app.services.training_service.random.sample",
        lambda items, k: items[:k],
    )


def test_generate_mock_scoring_returns_expected_structure(scoring_service, monkeypatch):
    _patch_random(monkeypatch, total_score=81.5)

    result = scoring_service._generate_mock_scoring()

    assert result["total_score"] == 81.5
    assert result["performance_level"] == "good"
    assert set(result["step_scores"]) == {"step1", "step2", "step3", "step4", "step5", "step6"}
    assert len(result["suggestions"]) == 2
    assert result["feedback"] == "未获取到有效视频分析结果，系统已使用降级评分。"
    assert set(result["dimension_scores"]) == {
        "action_completeness",
        "pose_standardization",
        "timeliness",
    }


@pytest.mark.parametrize(
    ("total_score", "expected_level"),
    [
        (92.0, "excellent"),
        (75.0, "pass"),
        (65.0, "pass"),
    ],
)
def test_generate_mock_scoring_assigns_level_by_total_score(
    scoring_service, monkeypatch, total_score, expected_level
):
    _patch_random(monkeypatch, total_score=total_score)

    result = scoring_service._generate_mock_scoring()

    assert result["performance_level"] == expected_level


def test_generate_mock_scoring_keeps_scores_within_bounds(scoring_service):
    for _ in range(10):
        result = scoring_service._generate_mock_scoring()

        assert 60 <= result["total_score"] <= 85
        assert 1 <= len(result["suggestions"]) <= 3
        for step_data in result["step_scores"].values():
            assert 60 <= step_data["score"] <= 85
