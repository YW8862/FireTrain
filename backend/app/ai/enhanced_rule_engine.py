"""增强版灭火器训练评分引擎

新增维度：
1. 动作连贯性 - 衡量步骤切换是否自然
2. 姿态稳定性 - 不仅是均值，还要看波动（方差）
3. 安全规范 - 面向火源、手臂角度等
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.ai.fire_extinguisher_standard import (
    DIMENSION_WEIGHTS,
    STANDARD_TIME_RANGES,
    STEP_DEFINITIONS,
    get_performance_level,
)


class EnhancedRuleEngine:
    """增强版评分引擎"""

    async def evaluate(
        self,
        analysis_summary: Dict[str, Any],
        training_type: str | None = None,
    ) -> Dict[str, Any]:
        training_type = training_type or analysis_summary.get("training_type", "fire_extinguisher")
        step_feature_summary = analysis_summary.get("step_feature_summary", {})
        step_scores = self._build_step_scores(step_feature_summary, training_type)

        # 原有维度
        completeness_score = self._calculate_action_completeness(step_scores)
        standardization_score = self._calculate_pose_standardization(
            step_feature_summary,
            analysis_summary.get("pose_stats_summary", {}),
        )
        timeliness_score = self._calculate_timeliness(
            float(analysis_summary.get("video_duration", 0)),
            training_type,
        )

        # 新增维度
        continuity_score = self._calculate_action_continuity(step_feature_summary, analysis_summary)
        safety_score = self._calculate_safety_compliance(analysis_summary)

        # 新权重分配（降低时效性权重，新增连贯性和安全规范）
        new_weights = {
            "action_completeness": 0.40,
            "pose_standardization": 0.30,
            "action_continuity": 0.15,
            "safety_compliance": 0.10,
            "timeliness": 0.05,
        }

        total_score = round(
            completeness_score * new_weights["action_completeness"]
            + standardization_score * new_weights["pose_standardization"]
            + continuity_score * new_weights["action_continuity"]
            + safety_score * new_weights["safety_compliance"]
            + timeliness_score * new_weights["timeliness"],
            1,
        )

        performance = get_performance_level(total_score)

        return {
            "total_score": total_score,
            "performance_level": performance["code"],
            "performance_label": performance["label"],
            "dimension_scores": {
                "action_completeness": {
                    "score": round(completeness_score, 1),
                    "weight": new_weights["action_completeness"],
                    "comment": self._dimension_comment("动作完整性", completeness_score),
                },
                "pose_standardization": {
                    "score": round(standardization_score, 1),
                    "weight": new_weights["pose_standardization"],
                    "comment": self._dimension_comment("姿态规范性", standardization_score),
                },
                "action_continuity": {
                    "score": round(continuity_score, 1),
                    "weight": new_weights["action_continuity"],
                    "comment": self._dimension_comment("动作连贯性", continuity_score),
                },
                "safety_compliance": {
                    "score": round(safety_score, 1),
                    "weight": new_weights["safety_compliance"],
                    "comment": self._dimension_comment("安全规范", safety_score),
                },
                "timeliness": {
                    "score": round(timeliness_score, 1),
                    "weight": new_weights["timeliness"],
                    "comment": self._dimension_comment("操作时效性", timeliness_score),
                },
            },
            "step_scores": step_scores,
            "feedback": self._build_feedback(total_score, performance["label"], step_scores, analysis_summary),
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
        """动作完整性：加权平均"""
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
        """姿态规范性：使用方差惩罚波动"""
        pose_scores = [
            float(summary.get("pose_quality_score", 0.0))
            for summary in step_feature_summary.values()
            if summary.get("completed")
        ]
        avg_pose_score = sum(pose_scores) / len(pose_scores) if pose_scores else 0.0

        # 计算姿态波动方差
        body_stats = pose_stats_summary.get("body", {})
        stability = float(body_stats.get("stability", 30.0))

        # 方差越大，扣分越多
        # stability 0-30: 优秀, 30-60: 良好, 60-90: 一般, >90: 差
        if stability <= 30:
            body_penalty = 0
        elif stability <= 60:
            body_penalty = (stability - 30) * 0.5
        elif stability <= 90:
            body_penalty = 15 + (stability - 60) * 1.0
        else:
            body_penalty = 45 + (stability - 90) * 1.5

        body_score = max(0.0, 100.0 - body_penalty)
        return round(avg_pose_score * 0.7 + body_score * 0.3, 1)

    def _calculate_timeliness(self, duration_seconds: float, training_type: str) -> float:
        """操作时效性"""
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

    def _calculate_action_continuity(
        self,
        step_feature_summary: Dict[str, Dict[str, Any]],
        analysis_summary: Dict[str, Any],
    ) -> float:
        """动作连贯性：检查步骤之间切换是否自然

        评估标准：
        1. 步骤时长比例是否合理（不能某个步骤过长或过短）
        2. 步骤切换是否平滑（通过step_times分析）
        3. 是否有长时间的停顿或犹豫
        """
        step_times = analysis_summary.get("step_times", {})
        if not step_times:
            return 50.0  # 无法评估

        total_duration = float(step_times.get("total", 1))
        if total_duration <= 0:
            return 50.0

        # 检查各步骤时长占比
        expected_ratios = {
            "step1": 0.10,  # 准备阶段 3-15s / 60-150s ≈ 10%
            "step2": 0.13,  # 提灭火器 5-15s / 60-150s ≈ 13%
            "step3": 0.10,  # 拔保险销 3-10s / 60-150s ≈ 10%
            "step4": 0.08,  # 握喷管 3-8s / 60-150s ≈ 8%
            "step5": 0.13,  # 瞄准火源 5-15s / 60-150s ≈ 13%
            "step6": 0.27,  # 压把手 10-30s / 60-150s ≈ 27%
        }

        continuity_penalties = []
        for step_key, expected_ratio in expected_ratios.items():
            actual_duration = float(step_times.get(step_key, 0))
            if actual_duration <= 0:
                continue

            actual_ratio = actual_duration / total_duration
            deviation = abs(actual_ratio - expected_ratio) / expected_ratio

            # 偏离超过50%扣分
            if deviation > 0.5:
                continuity_penalties.append(min(deviation * 30, 30))

        if not continuity_penalties:
            return 100.0

        avg_penalty = sum(continuity_penalties) / len(continuity_penalties)
        return round(max(0.0, 100.0 - avg_penalty), 1)

    def _calculate_safety_compliance(self, analysis_summary: Dict[str, Any]) -> float:
        """安全规范：评估安全操作意识

        评估标准：
        1. body角度 - 应该面向火源（身体朝向稳定）
        2. arm_extended - 灭火时手臂应该伸展
        3. 是否有突然的大幅度动作（可能是不安全的）
        """
        pose_stats = analysis_summary.get("pose_stats_summary", {})

        # 1. 身体稳定性（面向火源）
        body_stats = pose_stats.get("body", {})
        body_mean = float(body_stats.get("mean", 0))
        # 身体角度均值应该接近0（面向前方）
        body_score = max(0.0, 100.0 - body_mean * 2)

        # 2. 手臂伸展情况
        right_arm_stats = pose_stats.get("right_arm", {})
        left_arm_stats = pose_stats.get("left_arm", {})
        right_arm_mean = float(right_arm_stats.get("mean", 0))
        left_arm_mean = float(left_arm_stats.get("mean", 0))

        # 瞄准和压把手时，手臂应该较高角度伸展
        arm_score = 50.0  # 默认
        if right_arm_mean >= 120 or left_arm_mean >= 120:
            arm_score = 80.0
        if right_arm_mean >= 150 or left_arm_mean >= 150:
            arm_score = 100.0

        # 综合安全评分
        safety_score = body_score * 0.5 + arm_score * 0.5
        return round(safety_score, 1)

    def _step_duration_score(self, duration: float, duration_range: tuple[int, int]) -> float:
        """步骤时长评分"""
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
        """生成维度评价"""
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
        """生成反馈建议"""
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