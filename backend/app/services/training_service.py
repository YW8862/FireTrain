"""训练相关的 Service 层"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.models.training_record import TrainingRecord
from app.repositories.training_repository import TrainingRepository
from app.schemas.training import TrainingStartRequest
from app.services.scoring_service import ScoringService


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
