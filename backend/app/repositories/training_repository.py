"""训练记录相关的 Repository 层"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.training_record import TrainingRecord


class TrainingRepository:
    """训练记录数据访问层"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, training_data: dict) -> TrainingRecord:
        """创建训练记录"""
        training = TrainingRecord(**training_data)
        self.session.add(training)
        await self.session.flush()  # 获取生成的 ID
        await self.session.refresh(training)
        return training
    
    async def get_by_id(self, training_id: int) -> Optional[TrainingRecord]:
        """根据 ID 获取训练记录"""
        result = await self.session.execute(
            select(TrainingRecord).where(TrainingRecord.id == training_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: int) -> List[TrainingRecord]:
        """根据用户 ID 获取训练记录列表"""
        result = await self.session.execute(
            select(TrainingRecord)
            .where(TrainingRecord.user_id == user_id)
            .order_by(TrainingRecord.created_at.desc())
        )
        return result.scalars().all()
    
    async def update(self, training: TrainingRecord, update_data: dict) -> TrainingRecord:
        """更新训练记录"""
        for field, value in update_data.items():
            setattr(training, field, value)
        await self.session.flush()
        await self.session.refresh(training)
        return training
    
    async def complete_training(
        self, 
        training_id: int, 
        total_score: Decimal,
        step_scores: Optional[Dict[str, Any]],
        feedback: str
    ) -> Optional[TrainingRecord]:
        """完成训练并保存评分结果"""
        training = await self.get_by_id(training_id)
        if not training:
            return None
        
        training.status = "done"
        training.total_score = total_score
        training.step_scores = step_scores
        training.feedback = feedback
        training.completed_at = datetime.utcnow()
        
        await self.session.flush()
        await self.session.refresh(training)
        return training
    
    async def query_with_pagination(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> tuple[List[TrainingRecord], int]:
        """
        分页查询训练记录
        
        Returns:
            tuple: (训练记录列表，总数)
        """
        # 构建基础查询
        query = select(TrainingRecord).where(TrainingRecord.user_id == user_id)
        
        # 添加筛选条件
        conditions = []
        if status:
            conditions.append(TrainingRecord.status == status)
        if start_date:
            conditions.append(TrainingRecord.created_at >= start_date)
        if end_date:
            conditions.append(TrainingRecord.created_at <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 按创建时间倒序
        query = query.order_by(TrainingRecord.created_at.desc())
        
        # 获取总数
        count_query = select(TrainingRecord).where(TrainingRecord.user_id == user_id)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.session.execute(count_query)
        total = len(total_result.scalars().all())
        
        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.session.execute(query)
        records = result.scalars().all()
        
        return records, total
