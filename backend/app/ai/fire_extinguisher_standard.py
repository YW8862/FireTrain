"""灭火器训练识别与评分的统一标准定义。"""

from __future__ import annotations

from typing import Any, Dict, List


TRAINING_TYPE_FIRE_EXTINGUISHER = "fire_extinguisher"

DIMENSION_WEIGHTS: Dict[str, float] = {
    "action_completeness": 0.4,
    "pose_standardization": 0.4,
    "timeliness": 0.2,
}

STEP_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "key": "step1",
        "index": 1,
        "name": "准备阶段",
        "weight": 0.15,
        "duration_range": (3, 15),
        "key_points": [
            "面向火源并确认逃生路线",
            "身体站稳，保持警觉",
            "准备进入操作状态",
        ],
    },
    {
        "key": "step2",
        "index": 2,
        "name": "提灭火器",
        "weight": 0.20,
        "duration_range": (5, 15),
        "key_points": [
            "正确抓握灭火器",
            "提起时筒体保持稳定",
            "动作连贯不过分摇晃",
        ],
    },
    {
        "key": "step3",
        "index": 3,
        "name": "拔保险销",
        "weight": 0.15,
        "duration_range": (3, 10),
        "key_points": [
            "一手稳持灭火器",
            "另一手完成拔销动作",
            "动作清晰、不反复犹豫",
        ],
    },
    {
        "key": "step4",
        "index": 4,
        "name": "握喷管",
        "weight": 0.15,
        "duration_range": (3, 8),
        "key_points": [
            "手部握持位置正确",
            "喷管朝向火源方向",
            "握持动作稳定",
        ],
    },
    {
        "key": "step5",
        "index": 5,
        "name": "瞄准火源",
        "weight": 0.20,
        "duration_range": (5, 15),
        "key_points": [
            "保持稳定站姿与重心",
            "喷管对准火焰根部",
            "手臂自然伸展，方向明确",
        ],
    },
    {
        "key": "step6",
        "index": 6,
        "name": "压把手",
        "weight": 0.15,
        "duration_range": (10, 30),
        "key_points": [
            "压把动作连续有效",
            "保持对准火焰根部",
            "动作具有一定持续性和连贯性",
        ],
    },
]

STEP_BY_KEY = {step["key"]: step for step in STEP_DEFINITIONS}
STEP_BY_NAME = {step["name"]: step for step in STEP_DEFINITIONS}
STEP_NAMES = [step["name"] for step in STEP_DEFINITIONS]

STANDARD_TIME_RANGES: Dict[str, Dict[str, tuple[int, int]]] = {
    TRAINING_TYPE_FIRE_EXTINGUISHER: {
        "total": (60, 150),
        **{step["key"]: step["duration_range"] for step in STEP_DEFINITIONS},
    }
}

PERFORMANCE_LEVELS = [
    ("excellent", "优秀", 90),
    ("good", "良好", 80),
    ("pass", "合格", 60),
    ("fail", "待改进", 0),
]


def get_performance_level(total_score: float) -> Dict[str, Any]:
    """根据分数返回统一的等级表示。"""
    for code, label, threshold in PERFORMANCE_LEVELS:
        if total_score >= threshold:
            return {"code": code, "label": label}
    return {"code": "fail", "label": "待改进"}


def get_step_definition(step_key: str) -> Dict[str, Any]:
    """按步骤键获取定义。"""
    return STEP_BY_KEY[step_key]
