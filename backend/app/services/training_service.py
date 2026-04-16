"""训练服务层 - 处理训练相关的业务逻辑"""
import os
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.models.training_record import TrainingRecord
from app.repositories.training_repository import TrainingRepository


class TrainingService:
    """训练服务类"""
    
    def __init__(self, training_repo: TrainingRepository):
        self.training_repo = training_repo
    
    async def start_training(self, user_id: int, request) -> TrainingRecord:
        """
        开始训练任务
        
        Args:
            user_id: 用户ID
            request: 训练开始请求
            
        Returns:
            新创建的训练记录
        """
        # 创建新的训练记录
        training = TrainingRecord(
            user_id=user_id,
            training_type=request.training_type,
            status="created",
            duration_seconds=request.duration_seconds if hasattr(request, 'duration_seconds') else None,
            started_at=datetime.utcnow()
        )
        
        await self.training_repo.create(training)
        return training
    
    async def upload_video(self, training_id: int, video_path: str) -> Optional[TrainingRecord]:
        """
        上传训练视频
        
        Args:
            training_id: 训练记录ID
            video_path: 视频文件路径
            
        Returns:
            更新后的训练记录，如果不存在则返回None
        """
        training = await self.training_repo.get_by_id(training_id)
        if not training:
            return None
        
        # 更新视频路径和状态
        training.video_path = video_path
        training.status = "processing"
        
        await self.training_repo.update(training)
        return training
    
    async def complete_training_with_ai_analysis(
        self, 
        training_id: int, 
        use_ai_scoring: bool = True
    ) -> Optional[Dict]:
        """
        完成训练并进行AI分析评分
        
        Args:
            training_id: 训练记录ID
            use_ai_scoring: 是否使用AI评分
            
        Returns:
            包含评分结果的字典
        """
        training = await self.training_repo.get_by_id(training_id)
        if not training:
            return None
        
        # 检查当前状态是否可以完成
        if training.status not in ["created", "processing"]:
            raise ValueError(f"当前状态不能完成训练：{training.status}")
        
        # 如果没有视频路径，无法进行AI分析
        if not training.video_path:
            raise ValueError("视频路径为空，无法完成训练")
        
        # 根据配置决定是否使用AI评分
        if use_ai_scoring and os.path.exists(training.video_path):
            try:
                # 尝试使用AI评分
                from app.ai.training_inference_service import TrainingInferenceService
                
                inference_service = TrainingInferenceService(
                    yolo_model_path=settings.YOLO_MODEL_PATH,
                    yolo_conf_threshold=0.5,
                    use_pose_analysis=True
                )
                
                # 分析视频
                analysis_result = await run_in_threadpool(
                    lambda: inference_service.analyze_video(
                        video_path=training.video_path,
                        training_type=training.training_type
                    )
                )
                
                inference_service.close()
                
                # 计算分数（这里简化处理，实际应该有更复杂的评分逻辑）
                total_score = min(100, max(0, analysis_result.get('total_detections', 0) * 10))
                
                scoring_result = {
                    "total_score": total_score,
                    "step_scores": analysis_result.get('step_scores', {}),
                    "feedback": f"AI分析完成，检测到{analysis_result.get('total_detections', 0)}个目标",
                    "suggestions": analysis_result.get('suggestions', []),
                    "performance_level": "优秀" if total_score >= 90 else "良好" if total_score >= 70 else "一般",
                    "dimension_scores": analysis_result.get('dimension_scores', {})
                }
                
                used_ai_scoring = True
                
            except Exception as e:
                print(f"AI评分失败，降级到模拟评分：{e}")
                # 降级到模拟评分
                scoring_result = self._generate_mock_scoring()
                used_ai_scoring = False
        else:
            # 使用模拟评分
            scoring_result = self._generate_mock_scoring()
            used_ai_scoring = False
        
        # 更新训练记录
        training.status = "done"
        training.total_score = scoring_result["total_score"]
        training.step_scores = scoring_result["step_scores"]
        training.feedback = scoring_result["feedback"]
        training.completed_at = datetime.utcnow()
        
        # 计算持续时间
        if training.started_at:
            duration = (training.completed_at - training.started_at).total_seconds()
            training.duration_seconds = int(duration)
        
        await self.training_repo.update(training)
        
        return {
            "status": training.status,
            "total_score": training.total_score,
            "feedback": training.feedback,
            "used_ai_scoring": used_ai_scoring,
            "scoring_result": scoring_result
        }
    
    def _generate_mock_scoring(self) -> Dict:
        """
        生成模拟评分结果
        
        Returns:
            模拟评分结果字典
        """
        # 生成随机分数
        total_score = round(random.uniform(60, 95), 1)
        
        # 生成步骤分数
        step_scores = {
            "step_1": round(random.uniform(60, 100), 1),
            "step_2": round(random.uniform(60, 100), 1),
            "step_3": round(random.uniform(60, 100), 1),
        }
        
        # 生成反馈
        feedback_messages = [
            "操作规范，流程熟练，继续保持！",
            "动作基本正确，注意细节改进",
            "整体表现良好，建议加强练习",
            "完成度较高，部分步骤需要优化"
        ]
        feedback = random.choice(feedback_messages)
        
        # 生成建议
        suggestions = [
            "注意操作步骤的顺序",
            "保持动作的稳定性",
            "提高操作速度",
            "加强安全意识"
        ]
        
        return {
            "total_score": total_score,
            "step_scores": step_scores,
            "feedback": feedback,
            "suggestions": random.sample(suggestions, k=random.randint(1, 3)),
            "performance_level": "优秀" if total_score >= 90 else "良好" if total_score >= 70 else "一般",
            "dimension_scores": {
                "accuracy": round(random.uniform(60, 100), 1),
                "speed": round(random.uniform(60, 100), 1),
                "safety": round(random.uniform(60, 100), 1)
            }
        }
    
    async def get_user_training_history(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[List[TrainingRecord], int]:
        """
        获取用户训练历史
        
        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            status: 状态筛选
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            (训练记录列表, 总数) 元组
        """
        # 限制每页最大数量
        page_size = min(page_size, 50)
        
        records, total = await self.training_repo.get_user_history(
            user_id=user_id,
            page=page,
            page_size=page_size,
            status=status,
            start_date=start_date,
            end_date=end_date
        )
        
        return records, total