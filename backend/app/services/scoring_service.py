"""评分相关的 Service 层"""
from decimal import Decimal
from typing import Any, Dict, List, Optional
import random
from app.ai.pose_analyzer import PoseAnalyzer
from app.ai.pose_scoring_service import PoseScoringService


class ScoringService:
    """
    评分业务逻辑层
    
    第一版使用规则 + 固定阈值的模拟评分
    后续可扩展为真实的 AI 模型评分
    """
    
    # 评分阈值配置
    SCORE_THRESHOLDS = {
        "excellent": 90,  # 优秀分数线
        "good": 80,       # 良好分数线
        "pass": 60,       # 合格分数线
    }
    
    # 步骤权重配置（灭火器操作）
    STEP_WEIGHTS = {
        "准备阶段": 0.2,      # 准备工作占 20%
        "提灭火器": 0.15,     # 提灭火器占 15%
        "拔保险销": 0.2,      # 拔保险销占 20%
        "握喷管": 0.1,        # 握喷管占 10%
        "瞄准火源": 0.2,      # 瞄准火源占 20%
        "压把手": 0.15,       # 压把手占 15%
    }
    
    # 标准操作时间（秒）
    STANDARD_DURATION = {
        "fire_extinguisher": 120,  # 灭火器操作标准时间 2 分钟
    }
    
    def __init__(self):
        """初始化评分服务"""
        pass
    
    async def score_training(
        self,
        training_type: str,
        video_path: Optional[str] = None,
        frame_data: Optional[List[Dict[str, Any]]] = None,
        duration_seconds: Optional[Decimal] = None,
        use_pose_analysis: bool = False
    ) -> Dict[str, Any]:
        """
        对训练进行评分
        
        Args:
            training_type: 训练类型（如 fire_extinguisher）
            video_path: 视频文件路径（可选）
            frame_data: 帧数据索引（可选）
            duration_seconds: 实际用时（秒）
            use_pose_analysis: 是否使用姿态分析（默认 False，使用模拟评分）
            
        Returns:
            评分结果字典，包含：
            - total_score: 总分（0-100）
            - step_scores: 各步骤分数
            - feedback: 总体反馈
            - suggestions: 改进建议列表
            - action_logs: 动作日志（可选）
        """
        # 如果启用姿态分析且有帧数据
        if use_pose_analysis and frame_data:
            return await self._score_with_pose_analysis(
                training_type=training_type,
                frame_data=frame_data,
                duration_seconds=duration_seconds
            )
        
        # 第一版：使用模拟评分（基于规则和随机性）
        # 后续版本会分析视频或帧数据
        
        if training_type == "fire_extinguisher":
            return await self._score_fire_extinguisher(duration_seconds)
        else:
            return await self._score_generic(training_type, duration_seconds)
    
    async def _score_with_pose_analysis(
        self,
        training_type: str,
        frame_data: List[Dict[str, Any]],
        duration_seconds: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        使用 MediaPipe 姿态分析进行评分
        
        Args:
            training_type: 训练类型
            frame_data: 帧数据列表（每帧包含图像或关键点数据）
            duration_seconds: 实际用时
            
        Returns:
            评分结果
        """
        pose_analyzer = PoseAnalyzer()
        pose_scorer = PoseScoringService()
        
        try:
            # 提取所有帧的姿态关键点
            pose_results = []
            for frame_info in frame_data:
                # 如果 frame_data 已经是关键点数据，直接使用
                if "keypoints" in frame_info:
                    pose_results.append(frame_info)
                else:
                    # 否则需要从图像中提取
                    frame_image = frame_info.get("image")
                    if frame_image is not None:
                        result = pose_analyzer.analyze_pose(frame_image, training_type)
                        if result:
                            pose_results.append(result)
            
            # 使用姿态评分服务计算分数
            pose_score_result = await pose_scorer.score_pose_analysis(
                pose_results=pose_results,
                training_type=training_type
            )
            
            # 如果需要结合时间评分
            total_score = Decimal(str(pose_score_result["total_score"]))
            time_bonus = Decimal("0")
            
            if duration_seconds and training_type == "fire_extinguisher":
                standard_time = Decimal(str(self.STANDARD_DURATION.get("fire_extinguisher", 120)))
                time_ratio = duration_seconds / standard_time
                
                # 在合理时间内完成（0.8-1.2 倍）给予奖励
                if Decimal("0.8") <= time_ratio <= Decimal("1.2"):
                    time_bonus = Decimal("5")  # 奖励 5 分
                elif time_ratio > Decimal("1.5"):
                    time_bonus = Decimal("-5")  # 超时扣 5 分
                
                total_score += time_bonus
                total_score = max(Decimal("0"), min(Decimal("100"), total_score))
            
            # 生成动作日志
            action_logs = self._generate_pose_action_logs(pose_results, pose_score_result)
            
            return {
                "total_score": float(total_score),
                "step_scores": pose_score_result["step_scores"],
                "feedback": pose_score_result["feedback"],
                "suggestions": pose_score_result["suggestions"],
                "action_logs": action_logs,
                "duration_seconds": float(duration_seconds) if duration_seconds else None,
                "time_bonus": float(time_bonus) if time_bonus != 0 else None,
                "pose_analysis": True,
                "frame_count": len(pose_results)
            }
        finally:
            pose_analyzer.close()
    
    def _generate_pose_action_logs(
        self,
        pose_results: List[Dict[str, Any]],
        score_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        根据姿态分析结果生成动作日志
        
        Args:
            pose_results: 姿态分析结果列表
            score_result: 评分结果字典
            
        Returns:
            动作日志列表
        """
        action_logs = []
        base_time = 0
        
        step_names = list(self.STEP_ANGLE_STANDARDS.keys()) if hasattr(self, 'STEP_ANGLE_STANDARDS') else [
            "准备阶段", "提灭火器", "拔保险销", "握喷管", "瞄准火源", "压把手"
        ]
        
        for i, step_name in enumerate(step_names):
            step_data = score_result["step_scores"].get(f"step{i+1}", {})
            
            if step_data:
                log = {
                    "step_index": i + 1,
                    "step_name": step_name,
                    "start_time": base_time,
                    "end_time": base_time + 10,  # 假设每个步骤 10 秒
                    "score": step_data.get("score", 0),
                    "is_correct": step_data.get("is_correct", False),
                    "description": step_data.get("feedback", ""),
                    "key_points": self._get_step_key_points(step_name),
                    "pose_details": step_data.get("details", {})
                }
                action_logs.append(log)
                base_time = log["end_time"]
        
        return action_logs
    
    async def _score_fire_extinguisher(
        self, 
        duration_seconds: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        灭火器操作评分
        
        Args:
            duration_seconds: 实际用时
            
        Returns:
            评分结果
        """
        # 定义标准步骤
        standard_steps = [
            "准备阶段",
            "提灭火器",
            "拔保险销",
            "握喷管",
            "瞄准火源",
            "压把手"
        ]
        
        step_scores = {}
        total_weighted_score = Decimal("0")
        
        # 模拟每个步骤的评分
        for i, step_name in enumerate(standard_steps):
            # 基础分（60-100 之间）
            base_score = self._generate_step_score(step_name)
            
            # 判断是否正确
            is_correct = base_score >= 60
            
            # 生成步骤反馈
            step_feedback = self._generate_step_feedback(step_name, base_score)
            
            # 计算加权分数
            weight = Decimal(str(self.STEP_WEIGHTS.get(step_name, 0.1)))
            weighted_score = Decimal(str(base_score)) * weight
            total_weighted_score += weighted_score
            
            step_scores[f"step{i+1}"] = {
                "step_name": step_name,
                "score": base_score,
                "is_correct": is_correct,
                "feedback": step_feedback,
                "weight": float(weight)
            }
        
        # 计算总分（四舍五入保留 2 位小数）
        total_score = total_weighted_score.quantize(Decimal("0.01"))
        
        # 时间评分（可选）
        time_bonus = Decimal("0")
        if duration_seconds:
            standard_time = Decimal(str(self.STANDARD_DURATION.get("fire_extinguisher", 120)))
            time_ratio = duration_seconds / standard_time
            
            # 在合理时间内完成（0.8-1.2 倍）给予奖励
            if Decimal("0.8") <= time_ratio <= Decimal("1.2"):
                time_bonus = Decimal("5")  # 奖励 5 分
            elif time_ratio > Decimal("1.5"):
                time_bonus = Decimal("-5")  # 超时扣 5 分
            
            total_score += time_bonus
            total_score = max(Decimal("0"), min(Decimal("100"), total_score))
        
        # 生成总体反馈
        feedback = self._generate_overall_feedback(float(total_score))
        
        # 生成改进建议
        suggestions = self._generate_suggestions(step_scores, float(total_score))
        
        # 生成模拟的动作日志（用于后续分析）
        action_logs = self._generate_mock_action_logs(standard_steps, step_scores)
        
        return {
            "total_score": float(total_score),
            "step_scores": step_scores,
            "feedback": feedback,
            "suggestions": suggestions,
            "action_logs": action_logs,
            "duration_seconds": float(duration_seconds) if duration_seconds else None,
            "time_bonus": float(time_bonus) if time_bonus != 0 else None
        }
    
    async def _score_generic(
        self,
        training_type: str,
        duration_seconds: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        通用评分（其他训练类型）
        
        Args:
            training_type: 训练类型
            duration_seconds: 实际用时
            
        Returns:
            评分结果
        """
        # 简化的通用评分逻辑
        base_score = random.uniform(70, 95)
        
        step_scores = {
            "step1": {
                "step_name": "操作准备",
                "score": round(base_score + random.uniform(-5, 5), 2),
                "is_correct": True,
                "feedback": "准备工作基本到位"
            },
            "step2": {
                "step_name": "核心操作",
                "score": round(base_score + random.uniform(-10, 10), 2),
                "is_correct": True,
                "feedback": "操作流程基本正确"
            },
            "step3": {
                "step_name": "收尾工作",
                "score": round(base_score + random.uniform(-5, 5), 2),
                "is_correct": True,
                "feedback": "收尾工作完成良好"
            }
        }
        
        total_score = sum(step["score"] for step in step_scores.values()) / len(step_scores)
        feedback = self._generate_overall_feedback(total_score)
        suggestions = self._generate_suggestions(step_scores, total_score)
        
        return {
            "total_score": round(total_score, 2),
            "step_scores": step_scores,
            "feedback": feedback,
            "suggestions": suggestions,
            "action_logs": [],
            "duration_seconds": float(duration_seconds) if duration_seconds else None
        }
    
    def _generate_step_score(self, step_name: str) -> Decimal:
        """
        生成步骤分数（基于规则）
        
        Args:
            step_name: 步骤名称
            
        Returns:
            步骤分数（0-100）
        """
        # 根据步骤名称设置不同的难度系数
        difficulty_map = {
            "准备阶段": 0.9,      # 准备阶段通常较简单
            "提灭火器": 0.85,     # 体力要求
            "拔保险销": 0.8,      # 技巧性操作
            "握喷管": 0.9,        # 相对简单
            "瞄准火源": 0.75,     # 关键步骤，难度较高
            "压把手": 0.8         # 需要持续用力
        }
        
        difficulty = difficulty_map.get(step_name, 0.85)
        
        # 基础分（考虑难度）
        base = 70 + (1 - difficulty) * 30  # 难度越高，基础分越低
        variance = random.uniform(-10, 15)  # 随机波动
        
        score = base + variance
        score = max(0, min(100, score))  # 限制在 0-100 范围
        
        return Decimal(str(round(score, 2)))
    
    def _generate_step_feedback(self, step_name: str, score: Decimal) -> str:
        """
        生成步骤反馈
        
        Args:
            step_name: 步骤名称
            score: 步骤分数
            
        Returns:
            反馈文本
        """
        if score >= 90:
            return f"{step_name}：动作标准，非常规范"
        elif score >= 80:
            return f"{step_name}：基本正确，注意细节"
        elif score >= 60:
            return f"{step_name}：需要改进，加强练习"
        else:
            return f"{step_name}：操作不规范，需重新学习"
    
    def _generate_overall_feedback(self, total_score: float) -> str:
        """
        生成总体反馈
        
        Args:
            total_score: 总分
            
        Returns:
            总体反馈文本
        """
        if total_score >= 90:
            return "优秀！动作规范，流程熟练，继续保持"
        elif total_score >= 80:
            return "良好！基本掌握操作要领，注意细节改进"
        elif total_score >= 60:
            return "合格！但还有提升空间，建议多加练习"
        else:
            return "不合格！操作存在较大问题，请重新学习标准流程"
    
    def _generate_suggestions(
        self, 
        step_scores: Dict[str, Any],
        total_score: float
    ) -> List[str]:
        """
        生成改进建议
        
        Args:
            step_scores: 步骤分数
            total_score: 总分
            
        Returns:
            建议列表
        """
        suggestions = []
        
        # 找出得分最低的步骤
        weak_steps = []
        for step_key, step_data in step_scores.items():
            if isinstance(step_data, dict) and "score" in step_data:
                weak_steps.append({
                    "step_name": step_data.get("step_name", step_key),
                    "score": step_data["score"]
                })
        
        # 按分数排序，找出最弱的 3 个步骤
        weak_steps.sort(key=lambda x: x["score"])
        
        # 为最弱的步骤生成建议
        for step_info in weak_steps[:3]:
            step_name = step_info["step_name"]
            score = step_info["score"]
            
            if score < 60:
                suggestions.append(f"重点练习【{step_name}】，该步骤需要加强")
            elif score < 80:
                suggestions.append(f"改进【{step_name}】的动作规范性")
        
        # 如果整体表现好，给出进阶建议
        if total_score >= 80 and len(suggestions) > 0:
            suggestions.append("可以尝试提高操作速度")
        elif total_score >= 90:
            suggestions.append("表现优异，可以协助指导他人")
        
        # 默认建议（如果没有具体建议）
        if not suggestions:
            suggestions = [
                "保持现有水平，定期复习操作流程",
                "注意安全防护，确保操作规范"
            ]
        
        return suggestions
    
    def _generate_mock_action_logs(
        self,
        standard_steps: List[str],
        step_scores: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        生成模拟的动作日志（用于测试和演示）
        
        Args:
            standard_steps: 标准步骤列表
            step_scores: 步骤分数
            
        Returns:
            动作日志列表
        """
        action_logs = []
        base_time = 0
        
        for i, step_name in enumerate(standard_steps):
            # 找到对应的步骤分数
            step_data = None
            for key, value in step_scores.items():
                if isinstance(value, dict) and value.get("step_name") == step_name:
                    step_data = value
                    break
            
            if step_data:
                # 生成动作日志
                log = {
                    "step_index": i + 1,
                    "step_name": step_name,
                    "start_time": base_time,
                    "end_time": base_time + random.randint(5, 20),
                    "score": step_data["score"],
                    "is_correct": step_data["is_correct"],
                    "description": step_data["feedback"],
                    "key_points": self._get_step_key_points(step_name)
                }
                action_logs.append(log)
                base_time = log["end_time"]
        
        return action_logs
    
    def _get_step_key_points(self, step_name: str) -> List[str]:
        """
        获取步骤的关键要点
        
        Args:
            step_name: 步骤名称
            
        Returns:
            关键要点列表
        """
        key_points_map = {
            "准备阶段": [
                "做好个人防护",
                "确认逃生路线",
                "检查灭火器状态"
            ],
            "提灭火器": [
                "背部挺直",
                "屈膝下蹲",
                "用腿部力量提起"
            ],
            "拔保险销": [
                "握住保险销拉环",
                "用力向外拔出",
                "确认完全拔出"
            ],
            "握喷管": [
                "双手稳固握持",
                "保持喷管稳定",
                "对准火焰方向"
            ],
            "瞄准火源": [
                "对准火焰根部",
                "保持安全距离 2-3 米",
                "保持稳定姿势"
            ],
            "压把手": [
                "均匀用力下压",
                "保持连续喷射",
                "左右扫射覆盖"
            ]
        }
        
        return key_points_map.get(step_name, ["按标准流程操作"])
