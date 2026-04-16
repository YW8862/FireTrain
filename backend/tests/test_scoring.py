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
    _patch_random(monkeypatch, total_score=88.5)

    result = scoring_service._generate_mock_scoring()

    assert result["total_score"] == 88.5
    assert result["performance_level"] == "良好"
    assert set(result["step_scores"]) == {"step_1", "step_2", "step_3"}
    assert len(result["suggestions"]) == 2
    assert result["feedback"] == "操作规范，流程熟练，继续保持！"
    assert set(result["dimension_scores"]) == {"accuracy", "speed", "safety"}


@pytest.mark.parametrize(
    ("total_score", "expected_level"),
    [
        (92.0, "优秀"),
        (75.0, "良好"),
        (65.0, "一般"),
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

        assert 60 <= result["total_score"] <= 95
        assert 1 <= len(result["suggestions"]) <= 3
        for step_score in result["step_scores"].values():
            assert 60 <= step_score <= 100
