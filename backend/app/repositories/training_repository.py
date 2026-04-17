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
    
    async def create(self, training_data: dict | TrainingRecord) -> TrainingRecord:
        """创建训练记录"""
        training = training_data if isinstance(training_data, TrainingRecord) else TrainingRecord(**training_data)
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
    
    async def update(
        self,
        training: TrainingRecord,
        update_data: dict,
    ) -> TrainingRecord:
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
        from sqlalchemy import func
        count_query = select(func.count(TrainingRecord.id)).where(TrainingRecord.user_id == user_id)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.session.execute(query)
        records = result.scalars().all()
        
        return records, total
    
    async def delete(self, training: TrainingRecord) -> None:
        """删除训练记录"""
        await self.session.delete(training)
        await self.session.commit()
    
    async def query_with_filters(
        self,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[int] = None,
        training_type: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> tuple[list[dict], int]:
        """
        带过滤条件的训练记录查询
        
        Returns:
            (训练记录列表, 总数)
        """
        from sqlalchemy import select, func
        from datetime import datetime
        from app.models.user import User
        
        query = (
            select(
                TrainingRecord.id,
                TrainingRecord.user_id,
                User.username,
                TrainingRecord.training_type,
                TrainingRecord.total_score,
                TrainingRecord.status,
                TrainingRecord.duration_seconds,
                TrainingRecord.created_at,
                TrainingRecord.completed_at,
            )
            .select_from(TrainingRecord)
            .outerjoin(User, User.id == TrainingRecord.user_id)
        )
        count_query = select(func.count(TrainingRecord.id))
        
        # 用户ID过滤
        if user_id:
            query = query.where(TrainingRecord.user_id == user_id)
            count_query = count_query.where(TrainingRecord.user_id == user_id)
        
        # 训练类型过滤
        if training_type:
            query = query.where(TrainingRecord.training_type == training_type)
            count_query = count_query.where(TrainingRecord.training_type == training_type)
        
        # 状态过滤
        if status:
            query = query.where(TrainingRecord.status == status)
            count_query = count_query.where(TrainingRecord.status == status)
        
        # 日期范围过滤
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.where(TrainingRecord.created_at >= start_dt)
            count_query = count_query.where(TrainingRecord.created_at >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            query = query.where(TrainingRecord.created_at <= end_dt)
            count_query = count_query.where(TrainingRecord.created_at <= end_dt)
        
        # 查询总数
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        query = (
            query.order_by(TrainingRecord.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        
        result = await self.session.execute(query)
        trainings = result.mappings().all()
        
        training_list = [
            {
                "id": training["id"],
                "user_id": training["user_id"],
                "username": training["username"],
                "training_type": training["training_type"],
                "score": float(training["total_score"]) if training["total_score"] else None,
                "status": training["status"],
                "duration": float(training["duration_seconds"]) if training["duration_seconds"] else None,
                "created_at": training["created_at"],
                "completed_at": training["completed_at"],
            }
            for training in trainings
        ]
        
        return training_list, total
    
    async def count_all(self) -> int:
        """统计所有训练记录数量"""
        from sqlalchemy import select, func
        
        count_query = select(func.count(TrainingRecord.id))
        result = await self.session.execute(count_query)
        return result.scalar()
    
    async def count_by_date_range(self, start_date: datetime, end_date: datetime) -> int:
        """统计指定日期范围内的训练记录数量"""
        from sqlalchemy import select, func
        
        count_query = select(func.count(TrainingRecord.id)).where(
            TrainingRecord.created_at >= start_date,
            TrainingRecord.created_at < end_date
        )
        result = await self.session.execute(count_query)
        return result.scalar()
    
    async def get_average_score(self) -> Optional[float]:
        """获取平均分数"""
        from sqlalchemy import select, func
        
        avg_query = select(func.avg(TrainingRecord.total_score)).where(
            TrainingRecord.total_score.isnot(None)
        )
        result = await self.session.execute(avg_query)
        return result.scalar()
    
    async def get_user_history(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> tuple[List[TrainingRecord], int]:
        """
        获取用户训练历史
        
        Returns:
            (训练记录列表, 总数)
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
