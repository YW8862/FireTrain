"""姿态评分服务

基于 MediaPipe 姿态分析结果进行评分。
"""
from decimal import Decimal
from typing import Any, Dict, List, Optional
import numpy as np


class PoseScoringService:
    """姿态评分服务
    
    根据 MediaPipe 姿态分析结果计算姿态规范性分数。
    """
    
    # 步骤权重配置（灭火器操作）
    STEP_WEIGHTS = {
        "准备阶段": 0.15,      # 准备姿势
        "提灭火器": 0.20,      # 提起动作的姿态
        "拔保险销": 0.25,      # 拔销动作的姿态
        "握喷管": 0.15,        # 握持姿态
        "瞄准火源": 0.15,      # 瞄准姿态
        "压把手": 0.10,        # 按压姿态
    }
    
    # 各步骤的标准角度范围
    STEP_ANGLE_STANDARDS = {
        "准备阶段": {
            "body_upright": (80, 100),      # 身体直立
            "arm_natural": (160, 180),      # 手臂自然下垂
        },
        "提灭火器": {
            "arm_lift": (120, 160),         # 手臂抬起角度
            "body_stable": (85, 95),        # 身体稳定
        },
        "拔保险销": {
            "elbow_flex": (90, 120),        # 肘关节弯曲
            "wrist_straight": (170, 180),   # 手腕平直
        },
        "握喷管": {
            "arm_extend": (150, 170),       # 手臂伸展
            "shoulder_relax": (0, 30),      # 肩部放松
        },
        "瞄准火源": {
            "aim_direction": (0, 45),       # 瞄准方向
            "body_lean": (85, 95),          # 身体前倾
        },
        "压把手": {
            "arm_press": (100, 130),        # 按压角度
            "body_support": (80, 100),      # 身体支撑
        }
    }
    
    def __init__(self):
        """初始化姿态评分服务"""
        pass
    
    async def score_pose_analysis(
        self,
        pose_results: List[Dict[str, Any]],
        training_type: str = "fire_extinguisher"
    ) -> Dict[str, Any]:
        """对姿态分析结果进行评分
        
        Args:
            pose_results: MediaPipe 姿态分析结果列表（每帧一个）
            training_type: 训练类型
            
        Returns:
            评分结果字典
        """
        if not pose_results:
            return await self._generate_empty_score()
        
        # 计算每个步骤的分数
        step_scores = {}
        total_weighted_score = Decimal("0")
        
        # 分析所有帧的平均值
        avg_angles = self._calculate_average_angles(pose_results)
        
        # 对每个步骤进行评分
        for i, (step_name, angle_standards) in enumerate(self.STEP_ANGLE_STANDARDS.items()):
            step_score_data = await self._score_single_step(step_name, angle_standards, avg_angles)
            
            weight = Decimal(str(self.STEP_WEIGHTS.get(step_name, 0.1)))
            weighted_score = Decimal(str(step_score_data["score"])) * weight
            total_weighted_score += weighted_score
            
            step_scores[f"step{i+1}"] = step_score_data
        
        # 计算总分
        total_score = total_weighted_score.quantize(Decimal("0.01"))
        
        # 生成反馈和建议
        feedback = self._generate_pose_feedback(step_scores)
        suggestions = self._generate_pose_suggestions(step_scores)
        
        return {
            "total_score": float(total_score),
            "step_scores": step_scores,
            "feedback": feedback,
            "suggestions": suggestions,
            "pose_analysis": True,
            "frame_count": len(pose_results),
            "average_angles": avg_angles
        }
    
    def _calculate_average_angles(
        self,
        pose_results: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """计算所有帧的平均角度
        
        Args:
            pose_results: 姿态分析结果列表
            
        Returns:
            平均角度字典
        """
        angle_sums = {}
        angle_counts = {}
        
        for result in pose_results:
            angles = result.get("angles", {})
            for angle_name, angle_value in angles.items():
                if angle_name not in angle_sums:
                    angle_sums[angle_name] = 0
                    angle_counts[angle_name] = 0
                angle_sums[angle_name] += angle_value
                angle_counts[angle_name] += 1
        
        avg_angles = {}
        for angle_name in angle_sums:
            avg_angles[angle_name] = round(
                angle_sums[angle_name] / angle_counts[angle_name],
                2
            )
        
        return avg_angles
    
    async def _score_single_step(
        self,
        step_name: str,
        angle_standards: Dict[str, tuple],
        avg_angles: Dict[str, float]
    ) -> Dict[str, Any]:
        """对单个步骤进行评分
        
        Args:
            step_name: 步骤名称
            angle_standards: 该步骤的角度标准
            avg_angles: 平均角度数据
            
        Returns:
            步骤评分结果
        """
        step_scores = []
        step_feedbacks = []
        
        for angle_key, (min_angle, max_angle) in angle_standards.items():
            actual_angle = avg_angles.get(angle_key, 90)
            
            # 计算偏差
            if min_angle <= actual_angle <= max_angle:
                deviation = 0
                score = 100
                level = "优秀"
                feedback = f"{angle_key}: 动作标准"
            else:
                if actual_angle < min_angle:
                    deviation = min_angle - actual_angle
                else:
                    deviation = actual_angle - max_angle
                
                # 根据偏差评分
                if deviation <= 10:
                    score = 80
                    level = "良好"
                    feedback = f"{angle_key}: 基本正确"
                elif deviation <= 20:
                    score = 60
                    level = "合格"
                    feedback = f"{angle_key}: 需要改进"
                else:
                    score = max(0, 100 - deviation * 2)
                    level = "不合格"
                    feedback = f"{angle_key}: 不规范"
            
            step_scores.append(score)
            step_feedbacks.append(feedback)
        
        # 计算步骤平均分
        avg_score = sum(step_scores) / len(step_scores) if step_scores else 0
        
        return {
            "step_name": step_name,
            "score": round(avg_score, 2),
            "is_correct": avg_score >= 60,
            "feedback": "；".join(step_feedbacks),
            "weight": self.STEP_WEIGHTS.get(step_name, 0.1),
            "level": "优秀" if avg_score >= 90 else "良好" if avg_score >= 80 else "合格" if avg_score >= 60 else "不合格",
            "details": {
                "angle_scores": step_scores,
                "angle_feedbacks": step_feedbacks
            }
        }
    
    async def _generate_empty_score(self) -> Dict[str, Any]:
        """生成空评分结果（当没有姿态数据时）"""
        return {
            "total_score": 0,
            "step_scores": {},
            "feedback": "未检测到有效姿态数据",
            "suggestions": ["请确保摄像头画面中包含完整的人体"],
            "pose_analysis": True,
            "frame_count": 0,
            "average_angles": {}
        }
    
    def _generate_pose_feedback(self, step_scores: Dict[str, Any]) -> str:
        """生成姿态反馈
        
        Args:
            step_scores: 步骤分数字典
            
        Returns:
            反馈文本
        """
        # 计算平均分
        scores = [step["score"] for step in step_scores.values()]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        if avg_score >= 90:
            return "姿态非常规范，动作标准流畅"
        elif avg_score >= 80:
            return "姿态基本正确，注意细节改进"
        elif avg_score >= 60:
            return "姿态需要改进，建议加强练习"
        else:
            return "姿态不规范，请重新学习标准动作"
    
    def _generate_pose_suggestions(
        self,
        step_scores: Dict[str, Any]
    ) -> List[str]:
        """生成姿态改进建议
        
        Args:
            step_scores: 步骤分数字典
            
        Returns:
            建议列表
        """
        suggestions = []
        
        # 找出得分最低的步骤
        weak_steps = []
        for step_key, step_data in step_scores.items():
            weak_steps.append({
                "step_name": step_data["step_name"],
                "score": step_data["score"],
                "feedback": step_data["feedback"]
            })
        
        # 按分数排序
        weak_steps.sort(key=lambda x: x["score"])
        
        # 为最弱的 3 个步骤生成建议
        for step_info in weak_steps[:3]:
            if step_info["score"] < 60:
                suggestions.append(f"重点改进【{step_info['step_name']}】的姿势")
            elif step_info["score"] < 80:
                suggestions.append(f"优化【{step_info['step_name']}】的动作规范性")
        
        # 默认建议
        if not suggestions:
            suggestions = [
                "保持现有姿态水平",
                "注意动作的连贯性和稳定性"
            ]
        
        return suggestions
