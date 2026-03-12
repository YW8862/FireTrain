"""规则引擎模块

实现动作完整性、姿态规范性、时效性三类评分的合成。
"""
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


class PerformanceLevel(Enum):
    """表现等级"""
    EXCELLENT = "优秀"      # 90-100 分
    GOOD = "良好"          # 80-89 分
    PASS = "合格"          # 60-79 分
    FAIL = "不合格"        # 0-59 分


class RuleEngine:
    """规则引擎
    
    综合评估动作完整性、姿态规范性、时效性三个维度的得分。
    """
    
    # 三个维度的权重配置
    DIMENSION_WEIGHTS = {
        "action_completeness": Decimal("0.4"),   # 动作完整性占 40%
        "pose_standardization": Decimal("0.4"),  # 姿态规范性占 40%
        "timeliness": Decimal("0.2"),            # 时效性占 20%
    }
    
    # 各维度内部步骤的权重（灭火器操作）
    ACTION_STEP_WEIGHTS = {
        "准备阶段": Decimal("0.15"),
        "提灭火器": Decimal("0.20"),
        "拔保险销": Decimal("0.25"),
        "握喷管": Decimal("0.15"),
        "瞄准火源": Decimal("0.15"),
        "压把手": Decimal("0.10"),
    }
    
    # 标准时间范围（秒）
    STANDARD_TIME_RANGES = {
        "fire_extinguisher": {
            "total": (90, 150),      # 总时间 1.5-2.5 分钟
            "step1": (5, 15),        # 准备阶段
            "step2": (5, 15),        # 提灭火器
            "step3": (5, 10),        # 拔保险销
            "step4": (3, 8),         # 握喷管
            "step5": (5, 15),        # 瞄准火源
            "step6": (10, 30),       # 压把手
        }
    }
    
    def __init__(self):
        """初始化规则引擎"""
        pass
    
    async def evaluate(
        self,
        action_scores: Dict[str, Any],
        pose_scores: Dict[str, Any],
        duration_seconds: Optional[Decimal] = None,
        step_times: Optional[Dict[str, Decimal]] = None,
        training_type: str = "fire_extinguisher"
    ) -> Dict[str, Any]:
        """
        综合评估训练表现
        
        Args:
            action_scores: 动作完整性分数（来自 YOLO 检测）
            pose_scores: 姿态规范性分数（来自 MediaPipe）
            duration_seconds: 总用时
            step_times: 各步骤用时
            training_type: 训练类型
            
        Returns:
            评估结果字典
        """
        # 1. 计算动作完整性得分
        completeness_score = self._calculate_action_completeness(action_scores)
        
        # 2. 计算姿态规范性得分
        standardization_score = self._calculate_pose_standardization(pose_scores)
        
        # 3. 计算时效性得分
        timeliness_score = self._calculate_timeliness(
            duration_seconds=duration_seconds,
            step_times=step_times,
            training_type=training_type
        )
        
        # 4. 综合三个维度的得分
        total_score = (
            completeness_score * self.DIMENSION_WEIGHTS["action_completeness"] +
            standardization_score * self.DIMENSION_WEIGHTS["pose_standardization"] +
            timeliness_score * self.DIMENSION_WEIGHTS["timeliness"]
        )
        
        # 四舍五入保留 2 位小数
        total_score = total_score.quantize(Decimal("0.01"))
        
        # 5. 确定表现等级
        performance_level = self._get_performance_level(float(total_score))
        
        # 6. 生成详细评估报告
        evaluation_report = {
            "total_score": float(total_score),
            "performance_level": performance_level.value,
            "dimension_scores": {
                "action_completeness": {
                    "score": float(completeness_score),
                    "weight": float(self.DIMENSION_WEIGHTS["action_completeness"]),
                    "weighted_score": float(completeness_score * self.DIMENSION_WEIGHTS["action_completeness"])
                },
                "pose_standardization": {
                    "score": float(standardization_score),
                    "weight": float(self.DIMENSION_WEIGHTS["pose_standardization"]),
                    "weighted_score": float(standardization_score * self.DIMENSION_WEIGHTS["pose_standardization"])
                },
                "timeliness": {
                    "score": float(timeliness_score),
                    "weight": float(self.DIMENSION_WEIGHTS["timeliness"]),
                    "weighted_score": float(timeliness_score * self.DIMENSION_WEIGHTS["timeliness"])
                }
            },
            "details": {
                "completeness_details": self._get_completeness_details(action_scores),
                "standardization_details": self._get_standardization_details(pose_scores),
                "timeliness_details": self._get_timeliness_details(duration_seconds, training_type)
            }
        }
        
        return evaluation_report
    
    def _calculate_action_completeness(
        self,
        action_scores: Dict[str, Any]
    ) -> Decimal:
        """
        计算动作完整性得分
        
        Args:
            action_scores: 动作检测分数
            
        Returns:
            动作完整性得分（0-100）
        """
        if not action_scores or "step_scores" not in action_scores:
            return Decimal("0")
        
        step_scores = action_scores["step_scores"]
        weighted_sum = Decimal("0")
        
        for step_key, step_data in step_scores.items():
            if isinstance(step_data, dict) and "score" in step_data:
                step_name = step_data.get("step_name", step_key)
                weight = self.ACTION_STEP_WEIGHTS.get(step_name, Decimal("0.1"))
                score = Decimal(str(step_data["score"]))
                weighted_sum += score * weight
        
        return weighted_sum
    
    def _calculate_pose_standardization(
        self,
        pose_scores: Dict[str, Any]
    ) -> Decimal:
        """
        计算姿态规范性得分
        
        Args:
            pose_scores: 姿态分析分数
            
        Returns:
            姿态规范性得分（0-100）
        """
        if not pose_scores or "step_scores" not in pose_scores:
            return Decimal("0")
        
        step_scores = pose_scores["step_scores"]
        weighted_sum = Decimal("0")
        total_weight = Decimal("0")
        
        for step_key, step_data in step_scores.items():
            if isinstance(step_data, dict) and "score" in step_data:
                weight = Decimal(str(step_data.get("weight", 0.1)))
                score = Decimal(str(step_data["score"]))
                weighted_sum += score * weight
                total_weight += weight
        
        if total_weight > 0:
            return weighted_sum / total_weight
        return Decimal("0")
    
    def _calculate_timeliness(
        self,
        duration_seconds: Optional[Decimal] = None,
        step_times: Optional[Dict[str, Decimal]] = None,
        training_type: str = "fire_extinguisher"
    ) -> Decimal:
        """
        计算时效性得分
        
        Args:
            duration_seconds: 总用时
            step_times: 各步骤用时
            training_type: 训练类型
            
        Returns:
            时效性得分（0-100）
        """
        if not duration_seconds:
            return Decimal("50")  # 默认中等分数
        
        time_ranges = self.STANDARD_TIME_RANGES.get(training_type, {})
        total_range = time_ranges.get("total", (90, 150))
        
        min_time, max_time = total_range
        
        # 在标准时间范围内：满分 100 分
        if min_time <= duration_seconds <= max_time:
            return Decimal("100")
        
        # 超出范围：根据偏差扣分
        if duration_seconds < min_time:
            deviation = min_time - duration_seconds
        else:
            deviation = duration_seconds - max_time
        
        # 每超 10 秒扣 5 分
        penalty = Decimal(str(int(deviation / 10) * 5))
        score = Decimal("100") - penalty
        
        return max(Decimal("0"), min(Decimal("100"), score))
    
    def _get_performance_level(self, total_score: float) -> PerformanceLevel:
        """
        根据总分获取表现等级
        
        Args:
            total_score: 总分
            
        Returns:
            表现等级
        """
        if total_score >= 90:
            return PerformanceLevel.EXCELLENT
        elif total_score >= 80:
            return PerformanceLevel.GOOD
        elif total_score >= 60:
            return PerformanceLevel.PASS
        else:
            return PerformanceLevel.FAIL
    
    def _get_completeness_details(
        self,
        action_scores: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取动作完整性详情"""
        if not action_scores:
            return {"message": "无动作检测数据"}
        
        return {
            "detected_steps": len(action_scores.get("step_scores", {})),
            "average_detection_rate": action_scores.get("average_detection_rate", 0)
        }
    
    def _get_standardization_details(
        self,
        pose_scores: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取姿态规范性详情"""
        if not pose_scores:
            return {"message": "无姿态分析数据"}
        
        return {
            "analyzed_frames": pose_scores.get("frame_count", 0),
            "average_angles": pose_scores.get("average_angles", {})
        }
    
    def _get_timeliness_details(
        self,
        duration_seconds: Optional[Decimal],
        training_type: str
    ) -> Dict[str, Any]:
        """获取时效性详情"""
        time_ranges = self.STANDARD_TIME_RANGES.get(training_type, {})
        total_range = time_ranges.get("total", (90, 150))
        
        return {
            "actual_duration": float(duration_seconds) if duration_seconds else None,
            "standard_range": list(total_range),
            "is_within_range": total_range[0] <= (duration_seconds or 0) <= total_range[1]
        }
