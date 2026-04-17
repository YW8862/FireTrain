#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI 推理手工冒烟脚本。

覆盖内容：
1. ONNX 模型加载
2. 推理服务初始化
3. 可选真实视频分析
4. 规则评分
5. 可选真实 LLM 评分

使用示例：
    cd backend
    python3 scripts/test_ai_integration.py
    python3 scripts/test_ai_integration.py --video-path ../data/videos/test_videos/mock_training.mp4
    python3 scripts/test_ai_integration.py --with-llm
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai.fire_extinguisher_detector import FireExtinguisherDetector
from app.ai.llm_scoring_service import LLMScoringService
from app.ai.training_inference_service import TrainingInferenceService
from app.core.config import settings


def print_section(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def resolve_video_path(video_path_arg: Optional[str]) -> Optional[Path]:
    if video_path_arg:
        path = Path(video_path_arg)
        return path if path.exists() else None

    candidates = [
        Path(settings.VIDEO_DIR) / "test_videos" / "mock_training.mp4",
        Path("data/videos/test_videos/mock_training.mp4"),
        Path("../data/videos/test_videos/mock_training.mp4"),
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def build_mock_analysis() -> Dict[str, Any]:
    return {
        "analysis_summary": {
            "training_type": "fire_extinguisher",
            "video_duration": 28.0,
            "processed_frames": 84,
            "pose_frame_count": 36,
            "extinguisher_detected": True,
            "person_detected": True,
            "has_pose": True,
            "completed_steps_count": 6,
            "completed_steps": ["准备阶段", "提灭火器", "拔保险销", "握喷管", "瞄准火源", "压把手"],
            "missing_steps": [],
            "detection_stats": {
                "fire_extinguisher": {
                    "frame_count": 50,
                    "detection_count": 65,
                    "average_confidence": 0.91,
                },
                "person": {
                    "frame_count": 80,
                    "detection_count": 80,
                    "average_confidence": 0.96,
                },
            },
            "pose_stats_summary": {
                "body": {"mean": 89.5, "min": 84.0, "max": 96.0, "stability": 0.88},
                "right_arm": {"mean": 148.0, "min": 123.0, "max": 170.0, "stability": 0.81},
            },
            "step_feature_summary": {
                "step1": {
                    "completed": True,
                    "confidence": 0.95,
                    "duration": 4.3,
                    "pose_quality_score": 90.0,
                    "extinguisher_presence_ratio": 0.85,
                    "detected_actions": ["prepare"],
                    "issues": [],
                },
                "step2": {
                    "completed": True,
                    "confidence": 0.92,
                    "duration": 3.8,
                    "pose_quality_score": 88.0,
                    "extinguisher_presence_ratio": 0.93,
                    "detected_actions": ["lift"],
                    "issues": [],
                },
                "step3": {
                    "completed": True,
                    "confidence": 0.9,
                    "duration": 2.4,
                    "pose_quality_score": 85.0,
                    "extinguisher_presence_ratio": 0.91,
                    "detected_actions": ["pull_pin"],
                    "issues": [],
                },
                "step4": {
                    "completed": True,
                    "confidence": 0.88,
                    "duration": 3.2,
                    "pose_quality_score": 84.0,
                    "extinguisher_presence_ratio": 0.9,
                    "detected_actions": ["hold_hose"],
                    "issues": [],
                },
                "step5": {
                    "completed": True,
                    "confidence": 0.86,
                    "duration": 5.0,
                    "pose_quality_score": 82.0,
                    "extinguisher_presence_ratio": 0.92,
                    "detected_actions": ["aim"],
                    "issues": [],
                },
                "step6": {
                    "completed": True,
                    "confidence": 0.91,
                    "duration": 4.8,
                    "pose_quality_score": 87.0,
                    "extinguisher_presence_ratio": 0.94,
                    "detected_actions": ["press_handle"],
                    "issues": [],
                },
            },
        }
    }


def test_onnx_model_loading(model_path: str) -> bool:
    print_section("测试 1: ONNX 模型加载")
    try:
        detector = FireExtinguisherDetector(
            model_path=model_path,
            conf_threshold=0.5,
            img_size=640,
        )
        print("✅ ONNX 模型加载成功")
        print(f"   模型路径：{detector.model_path}")
        print(f"   输入形状：{detector.input_shape}")
        print(f"   类别数：{len(detector.names)}")
        detector.close()
        return True
    except Exception as exc:
        print(f"❌ ONNX 模型加载失败：{exc}")
        return False


def test_service_initialization(model_path: str) -> bool:
    print_section("测试 2: 推理服务初始化")
    try:
        service = TrainingInferenceService(
            yolo_model_path=model_path,
            yolo_conf_threshold=0.5,
            use_pose_analysis=True,
        )
        print("✅ 推理服务初始化成功")
        print(f"   YOLO 检测器：{type(service.yolo_detector).__name__}")
        print(f"   姿态分析器：{type(service.pose_analyzer).__name__}")
        print(f"   启用姿态分析：{service.use_pose_analysis}")
        service.close()
        return True
    except Exception as exc:
        print(f"❌ 推理服务初始化失败：{exc}")
        return False


def test_video_analysis(model_path: str, video_path: Optional[Path]) -> tuple[bool, Optional[Dict[str, Any]]]:
    print_section("测试 3: 视频分析")
    if not video_path:
        print("⚠️  未找到测试视频，跳过真实视频分析")
        print("   可通过 --video-path 指定视频，或准备 data/videos/test_videos/mock_training.mp4")
        return True, None

    service = None
    try:
        service = TrainingInferenceService(
            yolo_model_path=model_path,
            yolo_conf_threshold=0.5,
            use_pose_analysis=True,
        )
        print(f"📹 开始分析视频：{video_path}")
        result = service.analyze_video(str(video_path), "fire_extinguisher")
        summary = result.get("analysis_summary", result)
        print("✅ 视频分析成功")
        print(f"   视频时长：{summary.get('video_duration', 0):.2f} 秒")
        print(f"   处理帧数：{summary.get('processed_frames', 0)}")
        print(f"   检测到的完整步骤数：{summary.get('completed_steps_count', 0)}")
        print(f"   completed_steps：{summary.get('completed_steps', [])}")
        print(f"   missing_steps：{summary.get('missing_steps', [])}")
        return True, result
    except Exception as exc:
        print(f"❌ 视频分析失败：{exc}")
        traceback.print_exc()
        return False, None
    finally:
        if service:
            service.close()


async def test_rule_scoring(model_path: str) -> tuple[bool, Optional[Dict[str, Any]]]:
    print_section("测试 4: 规则评分")
    service = None
    try:
        service = TrainingInferenceService(
            yolo_model_path=model_path,
            yolo_conf_threshold=0.5,
            use_pose_analysis=True,
        )
        analysis = build_mock_analysis()
        score_result = await service.generate_ai_scores(analysis)
        print("✅ 规则评分成功")
        print(f"   总分：{score_result['total_score']}")
        print(f"   等级：{score_result['performance_level']}")
        print(f"   建议：{score_result.get('suggestions', [])}")
        return True, score_result
    except Exception as exc:
        print(f"❌ 规则评分失败：{exc}")
        traceback.print_exc()
        return False, None
    finally:
        if service:
            service.close()


async def test_llm_scoring(analysis_result: Dict[str, Any], baseline_score: Optional[Dict[str, Any]]) -> bool:
    print_section("测试 5: 真实 LLM 评分")
    llm_service = LLMScoringService.from_settings()
    if not llm_service:
        print("⚠️  未配置 LLM_API_KEY，跳过真实 LLM 评分")
        return True

    try:
        llm_result = await llm_service.score_training(analysis_result, baseline_score=baseline_score)
        print("✅ 真实 LLM 评分成功")
        print(f"   模型：{llm_service.model}")
        print(f"   总分：{llm_result['total_score']}")
        print(f"   等级：{llm_result['performance_level']}")
        print(f"   建议数量：{len(llm_result.get('suggestions', []))}")
        return True
    except Exception as exc:
        print(f"❌ 真实 LLM 评分失败：{exc}")
        traceback.print_exc()
        return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FireTrain AI 手工集成冒烟脚本")
    parser.add_argument(
        "--model-path",
        default=settings.YOLO_MODEL_PATH,
        help="YOLO ONNX 模型路径，默认读取 settings.YOLO_MODEL_PATH",
    )
    parser.add_argument(
        "--video-path",
        default=None,
        help="测试视频路径；不传则自动在默认目录查找",
    )
    parser.add_argument(
        "--skip-video",
        action="store_true",
        help="跳过真实视频分析，只跑模型加载、规则评分和可选 LLM 评分",
    )
    parser.add_argument(
        "--with-llm",
        action="store_true",
        help="额外发起一次真实 LLM 评分请求（需要配置 LLM_API_KEY）",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    model_path = args.model_path
    video_path = None if args.skip_video else resolve_video_path(args.video_path)

    print_section("FireTrain AI 推理手工冒烟测试")
    print(f"模型路径：{model_path}")
    print(f"视频路径：{video_path or '未提供/未找到'}")
    print(f"LLM 开关：{'开启' if args.with_llm else '关闭'}")

    tests: list[tuple[str, bool]] = []

    tests.append(("ONNX 模型加载", test_onnx_model_loading(model_path)))
    tests.append(("推理服务初始化", test_service_initialization(model_path)))

    video_ok, video_analysis = test_video_analysis(model_path, video_path)
    tests.append(("视频分析", video_ok))

    rule_ok, rule_result = asyncio.run(test_rule_scoring(model_path))
    tests.append(("规则评分", rule_ok))

    if args.with_llm:
        llm_analysis = video_analysis or build_mock_analysis()
        llm_ok = asyncio.run(test_llm_scoring(llm_analysis, baseline_score=rule_result))
        tests.append(("真实 LLM 评分", llm_ok))

    print_section("测试总结")
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    for test_name, result in tests:
        print(f"{'✅ 通过' if result else '❌ 失败'}: {test_name}")
    print(f"\n总计：{passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 冒烟测试全部通过")
        return 0

    print(f"\n⚠️  有 {total - passed} 项失败，请根据上面的错误信息排查")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
