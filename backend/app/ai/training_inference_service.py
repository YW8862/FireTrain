"""训练推理服务。

整合 YOLOv8 检测和 MediaPipe 姿态分析，对灭火器训练视频进行分析、步骤识别与摘要生成。
"""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional

import cv2

from app.ai.fire_extinguisher_detector import FireExtinguisherDetector
from app.ai.fire_extinguisher_standard import STEP_BY_KEY, STEP_DEFINITIONS, STEP_NAMES
from app.ai.pose_analyzer import PoseAnalyzer
from app.core.config import settings


class TrainingInferenceService:
    """训练推理服务。"""

    STANDARD_STEPS = STEP_NAMES

    def __init__(
        self,
        yolo_model_path: str | None = None,
        yolo_conf_threshold: float = 0.5,
        use_pose_analysis: bool = True,
    ):
        if yolo_model_path is None:
            yolo_model_path = settings.YOLO_MODEL_PATH

        self.yolo_detector = FireExtinguisherDetector(
            model_path=yolo_model_path,
            conf_threshold=yolo_conf_threshold,
        )
        self.use_pose_analysis = use_pose_analysis
        self.pose_analyzer = PoseAnalyzer() if use_pose_analysis else None

    def analyze_video(
        self,
        video_path: str,
        training_type: str = "fire_extinguisher",
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        """分析训练视频并输出统一摘要。

        Args:
            progress_callback: 可选进度回调，接收 ``(processed_frames, total_frames)``。
                每处理若干帧会触发一次（节流），用于将后台分析进度上报给前端。
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频：{video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0

        frame_results: List[Dict[str, Any]] = []
        all_detections: List[Dict[str, Any]] = []
        all_pose_results: List[Dict[str, Any]] = []

        frame_idx = 0
        processed_frames = 0
        frame_skip = 1 if total_frames < 300 else 2
        # 回调节流：每 5 帧或 2% 上报一次，避免锁竞争
        report_every = max(5, total_frames // 50) if total_frames > 0 else 10

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_skip == 0:
                timestamp = frame_idx / fps if fps > 0 else 0
                detections = self.yolo_detector.detect_frame(frame)
                all_detections.extend(detections)

                pose_result = None
                if self.use_pose_analysis:
                    pose_result = self.pose_analyzer.analyze_pose(frame, training_type)
                    if pose_result:
                        all_pose_results.append(pose_result)

                frame_features = self._extract_frame_features(detections, pose_result)
                frame_results.append(
                    {
                        "frame_idx": frame_idx,
                        "timestamp": timestamp,
                        "detections": detections,
                        "pose_result": pose_result,
                        "frame_features": frame_features,
                    }
                )
                processed_frames += 1

            frame_idx += 1

            if progress_callback is not None and frame_idx % report_every == 0:
                try:
                    progress_callback(frame_idx, total_frames)
                except Exception:
                    # 进度回调异常不应影响分析主流程
                    pass

        cap.release()
        # 循环结束后再触发一次最终进度（保证 100%）
        if progress_callback is not None and total_frames > 0:
            try:
                progress_callback(total_frames, total_frames)
            except Exception:
                pass

        step_sequence = self._recognize_action_sequence(frame_results, duration)
        step_times = self._calculate_step_times(step_sequence, duration)
        detection_stats = self._summarize_detections(frame_results)
        pose_stats_summary = self._summarize_pose_stats(all_pose_results)
        step_feature_summary = self._summarize_steps(step_sequence, frame_results)
        completed_steps = [step["step_name"] for step in step_sequence if step["is_completed"]]
        missing_steps = [name for name in self.STANDARD_STEPS if name not in completed_steps]
        detector_class_names = [
            class_name
            for _, class_name in sorted(self.yolo_detector.names.items(), key=lambda item: item[0])
        ]
        supports_extinguisher_detection = "fire_extinguisher" in detector_class_names

        analysis_summary = {
            "training_type": training_type,
            "video_duration": duration,
            "fps": fps,
            "total_frames": total_frames,
            "processed_frames": processed_frames,
            "extinguisher_detected": detection_stats.get("fire_extinguisher", {}).get("frame_count", 0) > 0,
            "person_detected": len(all_pose_results) > 0,
            "has_pose": len(all_pose_results) > 0,
            "pose_frame_count": len(all_pose_results),
            "total_detections": len(all_detections),
            "detector_class_names": detector_class_names,
            "supports_extinguisher_detection": supports_extinguisher_detection,
            "detection_stats": detection_stats,
            "pose_stats_summary": pose_stats_summary,
            "step_sequence": step_sequence,
            "step_times": step_times,
            "step_feature_summary": step_feature_summary,
            "completed_steps_count": len(completed_steps),
            "completed_steps": completed_steps,
            "missing_steps": missing_steps,
            "validity_checks": {
                "has_extinguisher": detection_stats.get("fire_extinguisher", {}).get("frame_count", 0) > 0,
                "has_pose": len(all_pose_results) > 0,
                "has_step_signal": len(completed_steps) > 0,
                "duration_ok": duration >= 20,
            },
        }

        return {
            "video_duration": duration,
            "total_frames": total_frames,
            "processed_frames": processed_frames,
            "fps": fps,
            "step_sequence": step_sequence,
            "step_times": step_times,
            "total_detections": len(all_detections),
            "detector_class_names": detector_class_names,
            "supports_extinguisher_detection": supports_extinguisher_detection,
            "pose_frame_count": len(all_pose_results),
            "frame_results": frame_results,
            "all_detections": all_detections,
            "all_pose_results": all_pose_results,
            "detection_stats": detection_stats,
            "pose_stats_summary": pose_stats_summary,
            "step_feature_summary": step_feature_summary,
            "extinguisher_detected": analysis_summary["extinguisher_detected"],
            "person_detected": analysis_summary["person_detected"],
            "has_pose": analysis_summary["has_pose"],
            "completed_steps_count": analysis_summary["completed_steps_count"],
            "analysis_summary": analysis_summary,
        }

    async def generate_ai_scores(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """基于统一摘要生成规则评分。"""
        from app.ai.rule_engine import RuleEngine

        summary = analysis_result.get("analysis_summary", analysis_result)
        rule_engine = RuleEngine()
        evaluation_result = await rule_engine.evaluate(summary)
        evaluation_result["suggestions"] = self.generate_real_suggestions(
            summary,
            evaluation_result.get("step_scores", {}),
        )
        return evaluation_result

    @staticmethod
    def generate_real_suggestions(
        analysis_result: Dict[str, Any],
        step_scores: Dict[str, Any],
    ) -> List[str]:
        """基于真实 AI 分析数据生成改进建议。"""
        suggestions: List[str] = []
        detection_stats = analysis_result.get("detection_stats", {})
        extinguisher_frames = detection_stats.get("fire_extinguisher", {}).get("frame_count", 0)
        pose_summary = analysis_result.get("pose_stats_summary", {})
        missing_steps = analysis_result.get("missing_steps", [])
        step_feature_summary = analysis_result.get("step_feature_summary", {})
        duration = float(analysis_result.get("video_duration", 0))

        if extinguisher_frames == 0:
            suggestions.append("视频中未稳定识别到灭火器，请检查取景和模型可见度")
        elif extinguisher_frames < max(3, int(analysis_result.get("processed_frames", 1) * 0.2)):
            suggestions.append("灭火器出现帧占比较低，建议让器材始终处于画面关键区域")

        if not analysis_result.get("has_pose"):
            suggestions.append("未检测到稳定人体姿态，请确保操作者全身进入画面")
        else:
            body_mean = pose_summary.get("body", {}).get("mean")
            right_arm_mean = pose_summary.get("right_arm", {}).get("mean")
            if body_mean is not None and body_mean > 35:
                suggestions.append("身体姿态波动较大，建议保持站姿稳定后再执行操作")
            if right_arm_mean is not None and not 80 <= right_arm_mean <= 170:
                suggestions.append("手臂动作幅度异常，建议按标准姿态重新练习抬臂和瞄准")

        if missing_steps:
            suggestions.append(f"仍有未稳定识别的步骤：{'、'.join(missing_steps[:3])}")

        weak_steps = []
        for step_key, score_data in step_scores.items():
            if isinstance(score_data, dict) and float(score_data.get("score", 0)) < 75:
                weak_steps.append(score_data.get("step_name", step_key))
        if weak_steps:
            suggestions.append(f"优先加强步骤：{'、'.join(weak_steps[:3])}")

        for step_key, summary in step_feature_summary.items():
            if not summary.get("completed"):
                continue
            issues = summary.get("issues", [])
            if issues:
                suggestions.append(f"{summary['step_name']}需关注：{issues[0]}")
                break

        if duration < 60:
            suggestions.append("本次操作偏快，注意不要省略准备、拔销和瞄准环节")
        elif duration > 150:
            suggestions.append("本次操作偏慢，建议提升流程熟练度和动作衔接速度")

        if not suggestions:
            suggestions.append("整体动作较完整，可继续强化压把后的持续扫射稳定性")
            suggestions.append("建议多进行带场景的重复练习，提升全过程连贯性")

        unique_suggestions: List[str] = []
        for suggestion in suggestions:
            if suggestion not in unique_suggestions:
                unique_suggestions.append(suggestion)
        return unique_suggestions[:4]

    def _extract_frame_features(
        self,
        detections: List[Dict[str, Any]],
        pose_result: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        """提取单帧可用于步骤识别的特征。"""
        extinguisher_detections = [
            det for det in detections if det.get("class_name") == "fire_extinguisher"
        ]
        extinguisher_confidence = max(
            (det.get("confidence", 0.0) for det in extinguisher_detections),
            default=0.0,
        )

        angles = pose_result.get("angles", {}) if pose_result else {}
        right_arm = angles.get("right_arm")
        left_arm = angles.get("left_arm")
        body = angles.get("body")
        arm_angles = [angle for angle in (right_arm, left_arm) if angle is not None]
        max_arm = max(arm_angles) if arm_angles else None
        min_arm = min(arm_angles) if arm_angles else None
        arm_asymmetry = abs(right_arm - left_arm) if right_arm is not None and left_arm is not None else 0.0
        # body 角度是肩髋连线与垂直线的夹角，0 度 = 完全直立
        stable_body = body is not None and body <= 35
        arm_bent = any(65 <= angle <= 130 for angle in arm_angles)
        arm_extended = any(angle >= 145 for angle in arm_angles)
        nozzle_control_posture = bool(
            extinguisher_detections
            and len(arm_angles) >= 2
            and max_arm is not None
            and min_arm is not None
            and max_arm >= 90
            and 50 <= min_arm <= 140
        )
        aiming_posture = bool(
            extinguisher_detections
            and arm_extended
            and stable_body
        )
        detected_actions = []
        if extinguisher_detections:
            detected_actions.append("extinguisher_detected")
        if pose_result:
            detected_actions.append("pose_detected")
        if arm_bent:
            detected_actions.append("arm_bent")
        if arm_extended:
            detected_actions.append("arm_extended")
        if arm_asymmetry >= 35:
            detected_actions.append("arm_asymmetry")
        if nozzle_control_posture:
            detected_actions.append("nozzle_control")
        if aiming_posture:
            detected_actions.append("aiming_posture")

        pose_quality = 0.0
        if pose_result and pose_result.get("scores"):
            score_values = [
                score_item.get("score", 0)
                for score_item in pose_result["scores"].values()
                if isinstance(score_item, dict)
            ]
            if score_values:
                pose_quality = sum(score_values) / len(score_values)

        return {
            "extinguisher_detected": bool(extinguisher_detections),
            "extinguisher_count": len(extinguisher_detections),
            "extinguisher_confidence": float(extinguisher_confidence),
            "pose_available": pose_result is not None,
            "right_arm": right_arm,
            "left_arm": left_arm,
            "body": body,
            "stable_body": stable_body,
            "arm_bent": arm_bent,
            "arm_extended": arm_extended,
            "arm_asymmetry": arm_asymmetry,
            "both_arms_visible": len(arm_angles) >= 2,
            "nozzle_control_posture": nozzle_control_posture,
            "aiming_posture": aiming_posture,
            "pose_quality": float(pose_quality),
            "detected_actions": detected_actions,
        }

    _STEP_CONFIDENCE_THRESHOLD = 0.36
    # 允许前向跳跃最多几步（放宽到 3 步以避免前期步骤全部低于阈值时卡住）
    _MAX_FORWARD_JUMP = 3

    def _recognize_action_sequence(
        self,
        frame_results: List[Dict[str, Any]],
        total_duration: float,
    ) -> List[Dict[str, Any]]:
        """使用"宽松顺序 + 证据累积"状态机识别 6 个标准步骤。

        改进点：
        - 允许前向跳跃 ≤ 2 步（教学视频常有连续动作间"讲解跳跃"）
        - 用视频相对进度替代 step1 的硬编码 8 秒
        - 使用 9 帧滑窗累计证据，单帧噪声不再决定步骤切换
        - 仅要求"证据累计"达阈值才切段，避免窗口短导致步骤漏判
        """
        if not frame_results:
            return []

        expected_step_index = 1
        current_segment: Dict[str, Any] | None = None
        step_sequence: List[Dict[str, Any]] = []
        window_size = 9  # 原来是 6，这里放大

        for idx, frame_data in enumerate(frame_results):
            timestamp = frame_data["timestamp"]
            features = frame_data["frame_features"]
            recent_features = [
                item["frame_features"]
                for item in frame_results[max(0, idx - window_size + 1): idx + 1]
            ]
            candidate_scores = self._score_step_candidates(
                timestamp,
                features,
                recent_features,
                total_duration,
            )

            # 宽松的允许集合：当前步骤 + 后续 _MAX_FORWARD_JUMP 步
            allowed_steps = {
                step_idx
                for step_idx in candidate_scores
                if expected_step_index <= step_idx <= expected_step_index + self._MAX_FORWARD_JUMP
            }
            if not allowed_steps:
                allowed_steps = {expected_step_index}

            filtered_scores = {
                step_idx: score for step_idx, score in candidate_scores.items() if step_idx in allowed_steps
            }
            dominant_step, dominant_score = max(
                filtered_scores.items(),
                key=lambda item: item[1],
            )
            if dominant_score < self._STEP_CONFIDENCE_THRESHOLD:
                continue

            dominant_step_key = f"step{dominant_step}"
            dominant_step_definition = STEP_BY_KEY[dominant_step_key]

            if current_segment is None:
                current_segment = self._create_step_segment(
                    dominant_step_definition,
                    timestamp,
                    dominant_score,
                    features,
                )
                expected_step_index = dominant_step
                continue

            if dominant_step == current_segment["step_index"]:
                current_segment = self._extend_step_segment(
                    current_segment,
                    timestamp,
                    dominant_score,
                    features,
                )
                continue

            # 允许前向跳跃 >= 1（而不是只限 +1）
            if dominant_step > current_segment["step_index"]:
                if self._is_step_segment_valid(current_segment):
                    step_sequence.append(self._finalize_step_segment(current_segment))
                current_segment = self._create_step_segment(
                    dominant_step_definition,
                    timestamp,
                    dominant_score,
                    features,
                )
                expected_step_index = dominant_step

        if current_segment and self._is_step_segment_valid(current_segment):
            step_sequence.append(self._finalize_step_segment(current_segment))

        return step_sequence

    def _score_step_candidates(
        self,
        timestamp: float,
        features: Dict[str, Any],
        recent_features: List[Dict[str, Any]],
        total_duration: float = 0.0,
    ) -> Dict[int, float]:
        """计算当前帧属于各步骤的证据分数。

        用视频相对进度（timestamp / total_duration）替代硬编码 8 秒，这样
        对不同时长的视频都合理：前 25% 属于"早期"、25%-55% 属于"中期"、
        55%-100% 属于"后期"。
        """
        extinguisher_score = 1.0 if features["extinguisher_detected"] else 0.0
        pose_score = 1.0 if features["pose_available"] else 0.0
        stable_body_score = 1.0 if features["stable_body"] else 0.0
        arm_bent_score = 1.0 if features["arm_bent"] else 0.0
        arm_extended_score = 1.0 if features["arm_extended"] else 0.0
        asymmetry_score = min(features["arm_asymmetry"] / 80.0, 1.0)
        both_arms_score = 1.0 if features["both_arms_visible"] else 0.0
        nozzle_control_score = 1.0 if features["nozzle_control_posture"] else 0.0
        aiming_score = 1.0 if features["aiming_posture"] else 0.0
        continuity_score = self._recent_extinguisher_ratio(recent_features)
        motion_score = self._recent_arm_motion_score(recent_features)

        # 视频相对进度（0.0 - 1.0）
        if total_duration > 0:
            video_ratio = max(0.0, min(timestamp / total_duration, 1.0))
        else:
            # 兜底：用绝对时间近似
            video_ratio = min(timestamp / 60.0, 1.0)

        # 阶段相位分：按步骤在整段视频中的典型时间位置
        early_stage = 1.0 if video_ratio <= 0.30 else (0.6 if video_ratio <= 0.50 else 0.3)
        mid_stage = 1.0 if 0.15 <= video_ratio <= 0.70 else 0.5
        late_stage = 1.0 if video_ratio >= 0.40 else 0.5
        final_stage = 1.0 if video_ratio >= 0.55 else (0.6 if video_ratio >= 0.30 else 0.3)

        return {
            # step1 准备阶段：姿态可见 + 视频早期 + 身体稳定（低权重）
            1: min(1.0, 0.35 * pose_score + 0.15 * stable_body_score + 0.35 * early_stage + 0.15 * (1.0 - extinguisher_score)),
            # step2 提灭火器：灭火器出现 + 手臂弯曲 + 偏早期
            2: min(1.0, 0.30 * extinguisher_score + 0.25 * arm_bent_score + 0.10 * stable_body_score + 0.10 * both_arms_score + 0.15 * early_stage + 0.10 * mid_stage),
            # step3 拔保险销：双臂非对称 + 灭火器出现（移除 arm_bent_score，因为拔销时拉销手臂通常是伸展的）
            3: min(1.0, 0.25 * extinguisher_score + 0.35 * asymmetry_score + 0.15 * stable_body_score + 0.10 * continuity_score + 0.15 * mid_stage),
            # step4 握喷管：双臂可见 + 握持姿态（降低 nozzle_control 条件，放宽手臂角度要求）
            4: min(1.0, 0.25 * extinguisher_score + 0.20 * both_arms_score + 0.20 * nozzle_control_score + 0.10 * stable_body_score + 0.10 * continuity_score + 0.15 * mid_stage),
            # step5 瞄准火源：手臂伸展 + 瞄准姿态
            5: min(1.0, 0.25 * extinguisher_score + 0.30 * aiming_score + 0.15 * arm_extended_score + 0.10 * stable_body_score + 0.10 * continuity_score + 0.10 * late_stage),
            # step6 压把手：手臂运动 + 后期阶段
            6: min(1.0, 0.20 * extinguisher_score + 0.20 * aiming_score + 0.15 * arm_extended_score + 0.20 * motion_score + 0.10 * continuity_score + 0.15 * final_stage),
        }

    def _recent_extinguisher_ratio(self, recent_features: List[Dict[str, Any]]) -> float:
        if not recent_features:
            return 0.0
        detected = sum(1 for item in recent_features if item["extinguisher_detected"])
        return detected / len(recent_features)

    def _recent_arm_motion_score(self, recent_features: List[Dict[str, Any]]) -> float:
        dominant_arm_values = []
        for features in recent_features:
            arm_values = [
                value for value in (features.get("right_arm"), features.get("left_arm"))
                if value is not None
            ]
            if arm_values:
                dominant_arm_values.append(max(arm_values))
        if len(dominant_arm_values) < 2:
            return 0.0
        return min((max(dominant_arm_values) - min(dominant_arm_values)) / 35.0, 1.0)

    def _create_step_segment(
        self,
        step_definition: Dict[str, Any],
        timestamp: float,
        evidence_score: float,
        features: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "step_key": step_definition["key"],
            "step_index": step_definition["index"],
            "step_name": step_definition["name"],
            "start_timestamp": timestamp,
            "end_timestamp": timestamp,
            "evidence_scores": [round(evidence_score, 4)],
            "frame_count": 1,
            "detected_actions": set(features["detected_actions"]),
            "extinguisher_presence_count": 1 if features["extinguisher_detected"] else 0,
            "pose_quality_values": [features["pose_quality"]] if features["pose_available"] else [],
            "is_completed": True,
        }

    def _extend_step_segment(
        self,
        segment: Dict[str, Any],
        timestamp: float,
        evidence_score: float,
        features: Dict[str, Any],
    ) -> Dict[str, Any]:
        segment["end_timestamp"] = timestamp
        segment["frame_count"] += 1
        segment["evidence_scores"].append(round(evidence_score, 4))
        segment["detected_actions"].update(features["detected_actions"])
        if features["extinguisher_detected"]:
            segment["extinguisher_presence_count"] += 1
        if features["pose_available"]:
            segment["pose_quality_values"].append(features["pose_quality"])
        return segment

    def _is_step_segment_valid(self, segment: Dict[str, Any]) -> bool:
        """判断步骤片段是否视为有效。

        允许较短的"掠过式"片段被计入——教学视频中每个动作往往只停留 1-2 秒，
        再苛刻的时长要求会让整个状态机对教学视频几乎完全失效。
        """
        # 原先是 duration_range 下限 * 0.3（约 1-3 秒），这里再放宽到 * 0.15
        min_seconds = max(0.5, STEP_BY_KEY[segment["step_key"]]["duration_range"][0] * 0.15)
        duration = segment["end_timestamp"] - segment["start_timestamp"]
        return segment["frame_count"] >= 2 and duration >= min_seconds

    def _finalize_step_segment(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        pose_quality_values = segment.pop("pose_quality_values")
        avg_pose_quality = (
            sum(pose_quality_values) / len(pose_quality_values)
            if pose_quality_values else 0.0
        )
        evidence_scores = segment["evidence_scores"]
        frame_count = max(segment["frame_count"], 1)
        segment["confidence"] = round(sum(evidence_scores) / len(evidence_scores), 3)
        segment["peak_confidence"] = round(max(evidence_scores), 3)
        segment["avg_pose_quality"] = round(avg_pose_quality, 2)
        segment["extinguisher_presence_ratio"] = round(
            segment["extinguisher_presence_count"] / frame_count,
            3,
        )
        segment["detected_actions"] = sorted(segment["detected_actions"])
        segment["key_points"] = STEP_BY_KEY[segment["step_key"]]["key_points"]
        return segment

    def _calculate_step_times(
        self,
        step_sequence: List[Dict[str, Any]],
        total_duration: float,
    ) -> Dict[str, Decimal]:
        step_times = {
            step["step_key"]: Decimal(
                str(round(step["end_timestamp"] - step["start_timestamp"], 2))
            )
            for step in step_sequence
        }
        step_times["total"] = Decimal(str(round(total_duration, 2)))
        return step_times

    def _summarize_detections(self, frame_results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        detection_summary: Dict[str, Dict[str, Any]] = {}
        for frame_data in frame_results:
            seen_classes = set()
            for detection in frame_data["detections"]:
                class_name = detection.get("class_name", "unknown")
                summary = detection_summary.setdefault(
                    class_name,
                    {
                        "detection_count": 0,
                        "frame_count": 0,
                        "max_confidence": 0.0,
                        "confidence_sum": 0.0,
                    },
                )
                summary["detection_count"] += 1
                summary["confidence_sum"] += detection.get("confidence", 0.0)
                summary["max_confidence"] = max(
                    summary["max_confidence"],
                    float(detection.get("confidence", 0.0)),
                )
                if class_name not in seen_classes:
                    summary["frame_count"] += 1
                    seen_classes.add(class_name)

        for summary in detection_summary.values():
            count = max(summary["detection_count"], 1)
            summary["average_confidence"] = round(summary["confidence_sum"] / count, 3)
            summary.pop("confidence_sum", None)

        return detection_summary

    def _summarize_pose_stats(
        self,
        all_pose_results: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, float]]:
        angle_data: Dict[str, List[float]] = {}
        for pose_result in all_pose_results:
            for angle_name, angle_value in pose_result.get("angles", {}).items():
                if isinstance(angle_value, (int, float)):
                    angle_data.setdefault(angle_name, []).append(float(angle_value))

        pose_summary: Dict[str, Dict[str, float]] = {}
        for angle_name, values in angle_data.items():
            if not values:
                continue
            mean_value = sum(values) / len(values)
            pose_summary[angle_name] = {
                "mean": round(mean_value, 2),
                "min": round(min(values), 2),
                "max": round(max(values), 2),
                "count": len(values),
                "stability": round(max(values) - min(values), 2),
            }
        return pose_summary

    def _summarize_steps(
        self,
        step_sequence: List[Dict[str, Any]],
        frame_results: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        step_feature_summary: Dict[str, Dict[str, Any]] = {}
        for step_definition in STEP_DEFINITIONS:
            step_key = step_definition["key"]
            step_entry = next((step for step in step_sequence if step["step_key"] == step_key), None)
            if not step_entry:
                step_feature_summary[step_key] = {
                    "step_name": step_definition["name"],
                    "completed": False,
                    "confidence": 0.0,
                    "duration": 0.0,
                    "frame_count": 0,
                    "extinguisher_presence_ratio": 0.0,
                    "pose_quality_score": 0.0,
                    "detected_actions": [],
                    "key_points": step_definition["key_points"],
                    "issues": ["未稳定识别到该步骤"],
                }
                continue

            matching_frames = [
                frame for frame in frame_results
                if step_entry["start_timestamp"] <= frame["timestamp"] <= step_entry["end_timestamp"]
            ]
            actions = Counter()
            for frame in matching_frames:
                for action in frame["frame_features"]["detected_actions"]:
                    actions[action] += 1

            issues: List[str] = []
            if step_entry["extinguisher_presence_ratio"] < 0.5:
                issues.append("灭火器可见度偏低")
            if step_entry["avg_pose_quality"] and step_entry["avg_pose_quality"] < 70:
                issues.append("姿态稳定性不足")
            if step_entry["confidence"] < 0.55:
                issues.append("步骤识别置信度偏低")

            step_feature_summary[step_key] = {
                "step_name": step_definition["name"],
                "completed": True,
                "confidence": round(step_entry["confidence"] * 100, 1),
                "duration": round(step_entry["end_timestamp"] - step_entry["start_timestamp"], 2),
                "frame_count": step_entry["frame_count"],
                "extinguisher_presence_ratio": step_entry["extinguisher_presence_ratio"],
                "pose_quality_score": step_entry["avg_pose_quality"],
                "detected_actions": [action for action, _ in actions.most_common(4)],
                "key_points": step_definition["key_points"],
                "issues": issues,
            }

        return step_feature_summary
    
    def close(self):
        if self.pose_analyzer:
            self.pose_analyzer.close()
        self.yolo_detector.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
