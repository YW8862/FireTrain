"""训练相关的 Service 层"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.models.training_record import TrainingRecord
from app.repositories.training_repository import TrainingRepository
from app.schemas.training import TrainingStartRequest
from app.services.scoring_service import ScoringService
from app.ai.training_inference_service import TrainingInferenceService


class TrainingService:
    """训练业务逻辑层"""
    
    def __init__(self, training_repo: TrainingRepository):
        self.training_repo = training_repo
    
    async def start_training(
        self, 
        user_id: int, 
        request: TrainingStartRequest
    ) -> TrainingRecord:
        """
        开始训练任务
        
        Args:
            user_id: 用户 ID
            request: 开始训练请求
            
        Returns:
            创建的训练记录
        """
        training_data = {
            "user_id": user_id,
            "training_type": request.training_type,
            "status": "created",  # 初始状态
            "total_score": Decimal("0.00"),
            "duration_seconds": request.duration_seconds,
            "started_at": datetime.utcnow(),
        }
        
        training = await self.training_repo.create(training_data)
        return training
    
    async def upload_video(
        self, 
        training_id: int, 
        video_path: str
    ) -> Optional[TrainingRecord]:
        """
        上传训练视频
        
        Args:
            training_id: 训练记录 ID
            video_path: 视频文件路径
            
        Returns:
            更新后的训练记录，如果不存在则返回 None
        """
        training = await self.training_repo.get_by_id(training_id)
        if not training:
            return None
        
        # 验证状态
        if training.status != "created":
            raise ValueError(f"当前状态不能上传视频：{training.status}")
        
        update_data = {
            "video_path": video_path,
            "status": "processing",  # 进入处理状态
        }
        
        updated_training = await self.training_repo.update(training, update_data)
        return updated_training
    
    async def complete_training_with_score(
        self,
        training_id: int,
        total_score: Decimal,
        step_scores: Optional[Dict[str, Any]],
        feedback: str
    ) -> Optional[TrainingRecord]:
        """
        完成训练并保存评分结果
        
        Args:
            training_id: 训练记录 ID
            total_score: 总分
            step_scores: 步骤分数（JSON 格式）
            feedback: 反馈文本
            
        Returns:
            更新后的训练记录，如果不存在则返回 None
        """
        training = await self.training_repo.get_by_id(training_id)
        if not training:
            return None
        
        # 验证状态
        if training.status not in ["created", "processing"]:
            raise ValueError(f"当前状态不能完成训练：{training.status}")
        
        updated_training = await self.training_repo.complete_training(
            training_id=training_id,
            total_score=total_score,
            step_scores=step_scores,
            feedback=feedback
        )
        
        return updated_training
    
    async def get_training_detail(self, training_id: int) -> Optional[TrainingRecord]:
        """获取训练详情"""
        return await self.training_repo.get_by_id(training_id)
    
    async def get_user_training_history(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> tuple[List[TrainingRecord], int]:
        """
        获取用户训练历史（分页）
        
        Args:
            user_id: 用户 ID
            page: 页码
            page_size: 每页数量
            status: 状态筛选
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            tuple: (训练记录列表，总数)
        """
        return await self.training_repo.query_with_pagination(
            user_id=user_id,
            page=page,
            page_size=page_size,
            status=status,
            start_date=start_date,
            end_date=end_date
        )
    
    async def generate_mock_score(self, training_type: str) -> dict:
        """
        生成模拟分数（使用 ScoringService，后续替换为真实 AI 评分）
        
        Args:
            training_type: 训练类型
            
        Returns:
            评分结果字典
        """
        scoring_service = ScoringService()
        result = await scoring_service.score_training(training_type=training_type)
        
        # 将 Decimal 转换为 float，使其可以被 JSON 序列化
        def convert_decimal_to_float(obj):
            """递归转换对象中的 Decimal 为 float"""
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_decimal_to_float(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimal_to_float(item) for item in obj]
            else:
                return obj
        
        return {
            "total_score": float(result["total_score"]),
            "step_scores": convert_decimal_to_float(result["step_scores"]),
            "feedback": result["feedback"],
            "suggestions": result.get("suggestions", []),
            "action_logs": convert_decimal_to_float(result.get("action_logs", []))
        }
    
    async def complete_training_with_ai_analysis(
        self,
        training_id: int,
        use_ai_scoring: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        完成训练并使用 AI 分析评分
        
        Args:
            training_id: 训练记录 ID
            use_ai_scoring: 是否使用 AI 评分（否则使用模拟评分）
            
        Returns:
            评分结果字典
        """
        training = await self.training_repo.get_by_id(training_id)
        if not training:
            return None
        
        # 验证状态
        if training.status not in ["created", "processing"]:
            raise ValueError(f"当前状态不能完成训练：{training.status}")
        
        # 检查是否有视频路径（如果没有，使用模拟评分）
        has_video = bool(training.video_path)
        if not has_video and use_ai_scoring:
            print(f"⚠️  训练记录 {training_id} 没有视频路径，将使用模拟评分")
            use_ai_scoring = False  # 自动降级到模拟评分
        
        scoring_result = None
        
        if use_ai_scoring:
            try:
                # 使用 AI 推理服务分析视频
                # 注意：使用 ONNX 模型而不是 PT 模型
                inference_service = TrainingInferenceService(
                    yolo_model_path="yolov8.onnx",  # 使用 ONNX 模型
                    yolo_conf_threshold=0.5,
                    use_pose_analysis=True
                )
                
                # 分析视频
                analysis_result = inference_service.analyze_video(
                    video_path=training.video_path,
                    training_type=training.training_type
                )
                
                # 生成 AI 评分
                ai_score_result = inference_service.generate_ai_scores(analysis_result)
                
                # 转换为普通字典（处理 Decimal）
                scoring_result = self._convert_ai_score_to_dict(ai_score_result)
                
                inference_service.close()
                
            except Exception as e:
                # AI 分析失败，降级到模拟评分
                print(f"AI 分析失败：{e}，使用模拟评分")
                scoring_service = ScoringService()
                scoring_result = await scoring_service.score_training(
                    training_type=training.training_type,
                    duration_seconds=training.duration_seconds
                )
        else:
            # 使用模拟评分
            scoring_service = ScoringService()
            scoring_result = await scoring_service.score_training(
                training_type=training.training_type,
                duration_seconds=training.duration_seconds
            )
        
        # 确保 step_scores 可以 JSON 序列化（转换 Decimal 为 float）
        def convert_decimal_to_float(obj):
            """递归转换对象中的 Decimal 为 float"""
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_decimal_to_float(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimal_to_float(item) for item in obj]
            else:
                return obj
        
        # 保存评分结果
        updated_training = await self.training_repo.complete_training(
            training_id=training_id,
            total_score=scoring_result["total_score"],
            step_scores=convert_decimal_to_float(scoring_result["step_scores"]),
            feedback=scoring_result["feedback"]
        )
        
        return {
            "training_id": training_id,
            "status": updated_training.status,
            "total_score": float(updated_training.total_score),
            "feedback": updated_training.feedback,
            "scoring_result": scoring_result,
            "used_ai_scoring": use_ai_scoring
        }
    
    def _convert_ai_score_to_dict(
        self,
        ai_score_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """将 AI 评分结果转换为字典格式（处理 Decimal）
        
        根据 system.md 第 7 章评分规则详细说明，转换 AI 评分结果为标准格式。
        
        Args:
            ai_score_result: AI 评分结果，包含：
                - total_score: 总分
                - performance_level: 表现等级
                - dimension_scores: 三个维度分数
                - details: 详细信息
        
        Returns:
            标准化的评分结果字典
        """
        from decimal import Decimal
        
        def convert_decimal(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_decimal(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimal(item) for item in obj]
            else:
                return obj
        
        # 从 AI 评分结果中提取信息
        total_score = ai_score_result.get("total_score", 0)
        performance_level = ai_score_result.get("performance_level", "未知")
        dimension_scores = ai_score_result.get("dimension_scores", {})
        details = ai_score_result.get("details", {})
        
        # 构建步骤分数（基于动作完整性检测结果）
        step_scores = {}
        completeness_details = details.get("completeness_details", {})
        standardization_details = details.get("standardization_details", {})
        timeliness_details = details.get("timeliness_details", {})
        
        # 从动作完整性详情中获取步骤信息
        detected_steps = completeness_details.get("detected_steps", 6)
        average_detection_rate = completeness_details.get("average_detection_rate", 1.0)
        
        # 为每个步骤生成分数（参考 system.md 第 7.2 节）
        for i in range(1, detected_steps + 1):
            step_key = f"step{i}"
            step_name = self._get_step_name(i)
            
            # 计算步骤分数（基于检测率和姿态规范性）
            # 参考 system.md 第 7 章：动作完整性 40% + 姿态规范性 40% + 时效性 20%
            action_completeness_score = dimension_scores.get(
                "action_completeness", {}
            ).get("score", 85)
            
            pose_standardization_score = dimension_scores.get(
                "pose_standardization", {}
            ).get("score", 85)
            
            # 综合计算该步骤的分数
            step_score = (action_completeness_score * 0.6 + 
                         pose_standardization_score * 0.4)
            
            # 判断是否正确（>= 60 分为正确）
            is_correct = step_score >= 60
            
            # 生成步骤反馈（参考 system.md 第 7.6 节）
            feedback = self._generate_step_feedback(step_name, step_score)
            
            step_scores[step_key] = {
                "step_name": step_name,
                "score": round(step_score, 2),
                "is_correct": is_correct,
                "feedback": feedback,
                "weight": 1.0 / detected_steps  # 平均权重
            }
        
        # 生成总体反馈（参考 system.md 第 7.6 节）
        overall_feedback = self._generate_overall_feedback(
            total_score=float(convert_decimal(total_score)),
            performance_level=performance_level,
            dimension_scores=dimension_scores
        )
        
        # 生成改进建议（参考 system.md 第 7.6 节）
        suggestions = self._generate_suggestions(
            step_scores=step_scores,
            total_score=float(convert_decimal(total_score)),
            timeliness_details=timeliness_details
        )
        
        return {
            "total_score": convert_decimal(total_score),
            "step_scores": step_scores,
            "feedback": overall_feedback,
            "suggestions": suggestions,
            "action_logs": [],  # 后续可以从 frame_results 生成
            "performance_level": performance_level,
            "dimension_scores": convert_decimal(dimension_scores)
        }
    
    def _generate_step_feedback(self, step_name: str, score: float) -> str:
        """
        生成步骤反馈（参考 system.md 第 7.6.1 节）
        
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
    
    def _generate_overall_feedback(
        self,
        total_score: float,
        performance_level: str,
        dimension_scores: Dict[str, Any]
    ) -> str:
        """
        生成总体反馈（参考 system.md 第 7.5 条和第 7.6 节）
        
        Args:
            total_score: 总分
            performance_level: 表现等级
            dimension_scores: 各维度分数
            
        Returns:
            总体反馈文本
        """
        # 根据总分和等级生成反馈
        if total_score >= 90:
            base_feedback = "优秀！动作规范，流程熟练，继续保持"
        elif total_score >= 80:
            base_feedback = "良好！基本掌握操作要领，注意细节改进"
        elif total_score >= 60:
            base_feedback = "合格！但还有提升空间，建议多加练习"
        else:
            base_feedback = "不合格！操作存在较大问题，请重新学习标准流程"
        
        # 添加各维度的具体评价
        dimension_comments = []
        
        # 动作完整性评价
        action_score = dimension_scores.get("action_completeness", {}).get("score", 0)
        if action_score >= 90:
            dimension_comments.append("动作完整性优秀")
        elif action_score >= 60:
            dimension_comments.append("动作完整性基本达标")
        else:
            dimension_comments.append("动作完整性需要加强")
        
        # 姿态规范性评价
        pose_score = dimension_scores.get("pose_standardization", {}).get("score", 0)
        if pose_score >= 90:
            dimension_comments.append("姿态非常规范")
        elif pose_score >= 60:
            dimension_comments.append("姿态基本正确")
        else:
            dimension_comments.append("姿态需要改进")
        
        # 时效性评价
        time_score = dimension_scores.get("timeliness", {}).get("score", 0)
        if time_score >= 90:
            dimension_comments.append("操作时间合理")
        elif time_score >= 60:
            dimension_comments.append("操作时间基本合适")
        else:
            dimension_comments.append("需要注意操作时间")
        
        return f"{base_feedback}。{'；'.join(dimension_comments)}"
    
    def _generate_suggestions(
        self,
        step_scores: Dict[str, Any],
        total_score: float,
        timeliness_details: Dict[str, Any]
    ) -> List[str]:
        """
        生成改进建议（参考 system.md 第 7.6 节）
        
        Args:
            step_scores: 步骤分数
            total_score: 总分
            timeliness_details: 时效性详情
            
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
        
        # 根据时效性生成建议（参考 system.md 第 7.4 节）
        actual_duration = timeliness_details.get("actual_duration")
        standard_range = timeliness_details.get("standard_range", (90, 150))
        
        if actual_duration:
            min_time, max_time = standard_range
            if actual_duration < min_time:
                suggestions.append("操作时间较短，注意不要遗漏步骤")
            elif actual_duration > max_time:
                suggestions.append("操作时间较长，建议加强熟练度练习")
            else:
                suggestions.append("操作时间控制良好")
        
        # 如果整体表现好，给出进阶建议
        if total_score >= 80 and len(suggestions) > 0:
            suggestions.append("可以尝试提高操作速度和流畅度")
        elif total_score >= 90:
            suggestions.append("表现优异，可以协助指导他人")
        
        # 默认建议（如果没有具体建议）
        if not suggestions:
            suggestions = [
                "保持现有水平，定期复习操作流程",
                "注意安全防护，确保操作规范"
            ]
        
        return suggestions
    
    def _get_step_name(self, step_index: int) -> str:
        """根据步骤索引获取步骤名称"""
        step_names = [
            "准备阶段",
            "提灭火器",
            "拔保险销",
            "握喷管",
            "瞄准火源",
            "压把手"
        ]
        if 1 <= step_index <= len(step_names):
            return step_names[step_index - 1]
        return f"步骤{step_index}"
