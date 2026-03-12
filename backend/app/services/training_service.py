"""训练相关的 Service 层"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.models.training_record import TrainingRecord
from app.repositories.training_repository import TrainingRepository
from app.schemas.training import TrainingStartRequest


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
        生成模拟分数（用于测试，后续替换为真实 AI 评分）
        
        Args:
            training_type: 训练类型
            
        Returns:
            评分结果字典
        """
        import random
        
        # 模拟步骤分数
        mock_step_scores = {
            "step1": {
                "step_name": "准备阶段",
                "score": round(random.uniform(70, 100), 2),
                "is_correct": random.choice([True, True, True, False]),
                "feedback": "准备工作基本到位"
            },
            "step2": {
                "step_name": "操作阶段",
                "score": round(random.uniform(60, 100), 2),
                "is_correct": random.choice([True, True, False]),
                "feedback": "操作流程需要改进"
            },
            "step3": {
                "step_name": "收尾阶段",
                "score": round(random.uniform(80, 100), 2),
                "is_correct": True,
                "feedback": "收尾工作良好"
            }
        }
        
        # 计算总分（平均分）
        total = sum(step["score"] for step in mock_step_scores.values())
        avg_score = total / len(mock_step_scores)
        
        # 生成反馈
        if avg_score >= 90:
            feedback = "优秀！动作规范，流程熟练"
        elif avg_score >= 80:
            feedback = "良好！基本掌握操作要领"
        elif avg_score >= 60:
            feedback = "合格！但还有提升空间"
        else:
            feedback = "需要加强练习，注意操作规范"
        
        return {
            "total_score": round(avg_score, 2),
            "step_scores": mock_step_scores,
            "feedback": feedback,
            "suggestions": [
                "建议多加练习操作步骤",
                "注意动作的规范性",
                "提高操作熟练度"
            ]
        }
