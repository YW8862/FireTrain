"""训练推理服务。

整合 YOLOv8 检测和 MediaPipe 姿态分析，对灭火器训练视频进行分析、步骤识别与摘要生成。
"""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
from typing import Any, Dict, List

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
    ) -> Dict[str, Any]:
        """分析训练视频并输出统一摘要。"""
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

        cap.release()

        step_sequence = self._recognize_action_sequence(frame_results)
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
            if body_mean is not None and not 75 <= body_mean <= 105:
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
        stable_body = body is not None and 75 <= body <= 105
        arm_bent = any(65 <= angle <= 130 for angle in arm_angles)
        arm_extended = any(angle >= 145 for angle in arm_angles)
        nozzle_control_posture = bool(
            extinguisher_detections
            and len(arm_angles) >= 2
            and max_arm is not None
            and min_arm is not None
            and max_arm >= 110
            and 60 <= min_arm <= 130
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

    def _recognize_action_sequence(self, frame_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """使用顺序状态机识别 6 个标准步骤。"""
        if not frame_results:
            return []

        expected_step_index = 1
        current_segment: Dict[str, Any] | None = None
        step_sequence: List[Dict[str, Any]] = []

        for idx, frame_data in enumerate(frame_results):
            timestamp = frame_data["timestamp"]
            features = frame_data["frame_features"]
            recent_features = [
                item["frame_features"]
                for item in frame_results[max(0, idx - 5): idx + 1]
            ]
            candidate_scores = self._score_step_candidates(timestamp, features, recent_features)
            allowed_steps = {expected_step_index}
            if expected_step_index < len(STEP_DEFINITIONS):
                allowed_steps.add(expected_step_index + 1)
            filtered_scores = {
                step_idx: score for step_idx, score in candidate_scores.items() if step_idx in allowed_steps
            }
            dominant_step, dominant_score = max(
                filtered_scores.items(),
                key=lambda item: item[1],
            )
            if dominant_score < 0.42:
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

            if dominant_step == current_segment["step_index"] + 1:
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
    ) -> Dict[int, float]:
        """计算当前帧属于各步骤的证据分数。"""
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
        early_stage_score = 1.0 if timestamp <= 8 else 0.4

        return {
            1: min(1.0, 0.45 * pose_score + 0.35 * stable_body_score + 0.20 * early_stage_score),
            2: min(1.0, 0.45 * extinguisher_score + 0.25 * arm_bent_score + 0.20 * stable_body_score + 0.10 * both_arms_score),
            3: min(1.0, 0.35 * extinguisher_score + 0.25 * asymmetry_score + 0.20 * arm_bent_score + 0.10 * stable_body_score + 0.10 * continuity_score),
            4: min(1.0, 0.35 * extinguisher_score + 0.20 * both_arms_score + 0.20 * nozzle_control_score + 0.15 * stable_body_score + 0.10 * continuity_score),
            5: min(1.0, 0.35 * extinguisher_score + 0.25 * aiming_score + 0.20 * arm_extended_score + 0.10 * stable_body_score + 0.10 * continuity_score),
            6: min(1.0, 0.30 * extinguisher_score + 0.20 * aiming_score + 0.20 * arm_extended_score + 0.20 * motion_score + 0.10 * continuity_score),
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
        min_seconds = STEP_BY_KEY[segment["step_key"]]["duration_range"][0] * 0.3
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
