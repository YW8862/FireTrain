"""灭火器训练规则评分引擎。"""

from __future__ import annotations

from typing import Any, Dict, List

from app.ai.fire_extinguisher_standard import (
    DIMENSION_WEIGHTS,
    STANDARD_TIME_RANGES,
    STEP_DEFINITIONS,
    get_performance_level,
)


class RuleEngine:
    """基于统一摘要结构进行规则评分。"""

    async def evaluate(
        self,
        analysis_summary: Dict[str, Any],
        training_type: str | None = None,
    ) -> Dict[str, Any]:
        training_type = training_type or analysis_summary.get("training_type", "fire_extinguisher")
        step_feature_summary = analysis_summary.get("step_feature_summary", {})
        step_scores = self._build_step_scores(step_feature_summary, training_type)
        completeness_score = self._calculate_action_completeness(step_scores)
        standardization_score = self._calculate_pose_standardization(
            step_feature_summary,
            analysis_summary.get("pose_stats_summary", {}),
        )
        timeliness_score = self._calculate_timeliness(
            float(analysis_summary.get("video_duration", 0)),
            training_type,
        )

        total_score = round(
            completeness_score * DIMENSION_WEIGHTS["action_completeness"]
            + standardization_score * DIMENSION_WEIGHTS["pose_standardization"]
            + timeliness_score * DIMENSION_WEIGHTS["timeliness"],
            1,
        )
        performance = get_performance_level(total_score)
        details = self._build_details(analysis_summary, step_scores, training_type)

        return {
            "total_score": total_score,
            "performance_level": performance["code"],
            "performance_label": performance["label"],
            "dimension_scores": {
                "action_completeness": {
                    "score": round(completeness_score, 1),
                    "weight": DIMENSION_WEIGHTS["action_completeness"],
                    "comment": self._dimension_comment("动作完整性", completeness_score),
                },
                "pose_standardization": {
                    "score": round(standardization_score, 1),
                    "weight": DIMENSION_WEIGHTS["pose_standardization"],
                    "comment": self._dimension_comment("姿态规范性", standardization_score),
                },
                "timeliness": {
                    "score": round(timeliness_score, 1),
                    "weight": DIMENSION_WEIGHTS["timeliness"],
                    "comment": self._dimension_comment("操作时效性", timeliness_score),
                },
            },
            "step_scores": step_scores,
            "feedback": self._build_feedback(total_score, performance["label"], step_scores, analysis_summary),
            "details": details,
        }

    def _build_step_scores(
        self,
        step_feature_summary: Dict[str, Dict[str, Any]],
        training_type: str,
    ) -> Dict[str, Dict[str, Any]]:
        step_scores: Dict[str, Dict[str, Any]] = {}
        time_ranges = STANDARD_TIME_RANGES.get(training_type, {})

        for step_definition in STEP_DEFINITIONS:
            step_key = step_definition["key"]
            summary = step_feature_summary.get(step_key, {})
            completed = bool(summary.get("completed"))
            confidence_ratio = float(summary.get("confidence", 0.0)) / 100.0
            pose_ratio = float(summary.get("pose_quality_score", 0.0)) / 100.0
            extinguisher_ratio = float(summary.get("extinguisher_presence_ratio", 0.0))
            duration = float(summary.get("duration", 0.0))
            duration_ratio = self._step_duration_score(duration, time_ranges.get(step_key, step_definition["duration_range"]))
            issues = summary.get("issues", [])

            if not completed:
                score = 0.0
                feedback = "未稳定识别到该步骤"
            else:
                score = (
                    40
                    + confidence_ratio * 25
                    + pose_ratio * 20
                    + extinguisher_ratio * 10
                    + duration_ratio * 5
                )
                score -= min(len(issues) * 5, 15)
                score = max(0.0, min(100.0, score))
                feedback = issues[0] if issues else "动作基本达标"

            step_scores[step_key] = {
                "step_name": step_definition["name"],
                "score": round(score, 1),
                "is_correct": score >= 60,
                "feedback": feedback,
                "weight": step_definition["weight"],
                "completed": completed,
                "confidence": round(float(summary.get("confidence", 0.0)), 1),
                "duration": duration,
                "key_points": step_definition["key_points"],
            }

        return step_scores

    def _calculate_action_completeness(self, step_scores: Dict[str, Dict[str, Any]]) -> float:
        weighted_sum = 0.0
        total_weight = 0.0
        for step_data in step_scores.values():
            weight = float(step_data.get("weight", 0.0))
            weighted_sum += float(step_data.get("score", 0.0)) * weight
            total_weight += weight
        if total_weight == 0:
            return 0.0
        return weighted_sum / total_weight

    def _calculate_pose_standardization(
        self,
        step_feature_summary: Dict[str, Dict[str, Any]],
        pose_stats_summary: Dict[str, Dict[str, Any]],
    ) -> float:
        pose_scores = [
            float(summary.get("pose_quality_score", 0.0))
            for summary in step_feature_summary.values()
            if summary.get("completed")
        ]
        avg_pose_score = sum(pose_scores) / len(pose_scores) if pose_scores else 0.0
        body_stability = 70.0
        body_stats = pose_stats_summary.get("body")
        if body_stats:
            stability = float(body_stats.get("stability", 30.0))
            body_stability = max(0.0, min(100.0, 100.0 - stability * 1.2))
        return round(avg_pose_score * 0.7 + body_stability * 0.3, 1)

    def _calculate_timeliness(self, duration_seconds: float, training_type: str) -> float:
        total_range = STANDARD_TIME_RANGES.get(training_type, {}).get("total", (60, 150))
        min_time, max_time = total_range
        if duration_seconds <= 0:
            return 0.0
        if min_time <= duration_seconds <= max_time:
            return 100.0
        if duration_seconds < min_time:
            deviation = min_time - duration_seconds
        else:
            deviation = duration_seconds - max_time
        penalty = min(100.0, deviation * 0.8)
        return round(max(0.0, 100.0 - penalty), 1)

    def _step_duration_score(self, duration: float, duration_range: tuple[int, int]) -> float:
        min_time, max_time = duration_range
        if duration <= 0:
            return 0.0
        if min_time <= duration <= max_time:
            return 1.0
        if duration < min_time:
            deviation = min_time - duration
        else:
            deviation = duration - max_time
        width = max(max_time - min_time, 1)
        return max(0.0, 1.0 - deviation / (width * 2))

    def _dimension_comment(self, dimension_name: str, score: float) -> str:
        if score >= 90:
            return f"{dimension_name}表现优秀"
        if score >= 80:
            return f"{dimension_name}较稳定"
        if score >= 60:
            return f"{dimension_name}基本达标"
        return f"{dimension_name}需重点改进"

    def _build_feedback(
        self,
        total_score: float,
        performance_label: str,
        step_scores: Dict[str, Dict[str, Any]],
        analysis_summary: Dict[str, Any],
    ) -> str:
        completed_count = analysis_summary.get("completed_steps_count", 0)
        missing_steps = analysis_summary.get("missing_steps", [])
        weak_steps = [
            step["step_name"]
            for step in step_scores.values()
            if float(step.get("score", 0.0)) < 75
        ]

        parts = [f"本次训练综合评价为{performance_label}，已识别 {completed_count}/6 个关键步骤。"]
        if missing_steps:
            parts.append(f"仍有步骤未稳定识别：{'、'.join(missing_steps[:3])}。")
        if weak_steps:
            parts.append(f"相对薄弱的环节主要集中在{'、'.join(weak_steps[:3])}。")
        if total_score >= 85:
            parts.append("整体动作较连贯，具备较好的操作基础。")
        elif total_score >= 60:
            parts.append("建议继续强化步骤衔接和稳定性。")
        else:
            parts.append("建议先按标准流程分步练习后再进行完整训练。")
        return "".join(parts)

    def _build_details(
        self,
        analysis_summary: Dict[str, Any],
        step_scores: Dict[str, Dict[str, Any]],
        training_type: str,
    ) -> Dict[str, Any]:
        total_range = STANDARD_TIME_RANGES.get(training_type, {}).get("total", (60, 150))
        return {
            "completed_steps": analysis_summary.get("completed_steps", []),
            "missing_steps": analysis_summary.get("missing_steps", []),
            "pose_stats_summary": analysis_summary.get("pose_stats_summary", {}),
            "detection_stats": analysis_summary.get("detection_stats", {}),
            "step_times": analysis_summary.get("step_times", {}),
            "standard_total_duration_range": list(total_range),
            "step_score_breakdown": step_scores,
        }
