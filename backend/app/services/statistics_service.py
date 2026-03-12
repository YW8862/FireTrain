"""统计相关的 Service 层"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.training_record import TrainingRecord
from app.models.training_statistics import TrainingStatistics
from app.schemas.statistics import (
    PersonalStatisticsResponse,
    TrainingTrendItem,
    StepAnalysisItem,
)


class StatisticsService:
    """统计业务逻辑层"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_personal_statistics(self, user_id: int) -> Optional[PersonalStatisticsResponse]:
        """
        获取个人统计数据
        
        Args:
            user_id: 用户 ID
            
        Returns:
            个人统计数据，如果不存在则返回 None
        """
        # 首先尝试从 training_statistics 表获取（预计算的统计数据）
        stmt = select(TrainingStatistics).where(TrainingStatistics.user_id == user_id)
        result = await self.session.execute(stmt)
        stats = result.scalar_one_or_none()
        
        if stats:
            return PersonalStatisticsResponse(
                user_id=stats.user_id,
                total_trainings=stats.total_trainings,
                completed_trainings=stats.completed_trainings,
                total_training_seconds=stats.total_training_seconds,
                average_score=stats.average_score,
                best_score=stats.best_score,
                last_training_at=stats.last_training_at
            )
        
        # 如果 training_statistics 表没有数据，从 training_records 实时计算
        return await self._calculate_from_records(user_id)
    
    async def _calculate_from_records(self, user_id: int) -> Optional[PersonalStatisticsResponse]:
        """
        从 training_records 实时计算统计数据
        
        Args:
            user_id: 用户 ID
            
        Returns:
            个人统计数据
        """
        # 查询该用户的所有训练记录
        stmt = select(TrainingRecord).where(
            TrainingRecord.user_id == user_id,
            TrainingRecord.status.in_(["done", "completed"])  # 只统计已完成的训练
        )
        result = await self.session.execute(stmt)
        records = result.scalars().all()
        
        if not records:
            return None
        
        # 计算统计数据
        total_trainings = len(records)
        completed_trainings = sum(1 for r in records if r.status == "done")
        
        # 计算总时长
        total_training_seconds = sum(
            float(r.duration_seconds or Decimal("0")) 
            for r in records
        )
        
        # 计算平均分和最高分
        scores = [float(r.total_score) for r in records if r.total_score is not None]
        average_score = Decimal(str(sum(scores) / len(scores))) if scores else Decimal("0")
        best_score = Decimal(str(max(scores))) if scores else Decimal("0")
        
        # 最后训练时间
        last_training_at = max(r.completed_at or r.created_at for r in records)
        
        return PersonalStatisticsResponse(
            user_id=user_id,
            total_trainings=total_trainings,
            completed_trainings=completed_trainings,
            total_training_seconds=Decimal(str(total_training_seconds)),
            average_score=average_score,
            best_score=best_score,
            last_training_at=last_training_at
        )
    
    async def get_training_trend(
        self, 
        user_id: int, 
        days: int = 7,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[TrainingTrendItem]:
        """
        获取训练趋势数据
        
        Args:
            user_id: 用户 ID
            days: 查询天数
            start_date: 开始日期（可选，如果提供则优先使用）
            end_date: 结束日期（可选，如果提供则优先使用）
            
        Returns:
            训练趋势数据列表
        """
        # 确定日期范围
        if start_date and end_date:
            query_start = start_date
            query_end = end_date
        else:
            query_end = datetime.utcnow()
            query_start = query_end - timedelta(days=days)
        
        # 按日期分组统计
        # 注意：SQLite 不支持 DATE 函数，使用 strftime
        stmt = select(
            func.strftime("%Y-%m-%d", TrainingRecord.created_at).label("date"),
            func.count(TrainingRecord.id).label("count"),
            func.avg(TrainingRecord.total_score).label("avg_score"),
            func.max(TrainingRecord.total_score).label("max_score")
        ).where(
            TrainingRecord.user_id == user_id,
            TrainingRecord.status.in_(["done", "completed"]),
            TrainingRecord.created_at >= query_start,
            TrainingRecord.created_at <= query_end
        ).group_by(
            func.strftime("%Y-%m-%d", TrainingRecord.created_at)
        ).order_by(
            func.strftime("%Y-%m-%d", TrainingRecord.created_at)
        )
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        trend_data = []
        for row in rows:
            trend_data.append(
                TrainingTrendItem(
                    date=row.date,
                    training_count=row.count,
                    average_score=Decimal(str(row.avg_score)) if row.avg_score else Decimal("0"),
                    best_score=Decimal(str(row.max_score)) if row.max_score else None
                )
            )
        
        return trend_data
    
    async def get_step_analysis(self, user_id: int) -> List[StepAnalysisItem]:
        """
        获取步骤分析数据
        
        Args:
            user_id: 用户 ID
            
        Returns:
            步骤分析数据列表
        """
        # 查询所有已完成的训练记录
        stmt = select(TrainingRecord).where(
            TrainingRecord.user_id == user_id,
            TrainingRecord.status.in_(["done", "completed"])
        )
        result = await self.session.execute(stmt)
        records = result.scalars().all()
        
        if not records:
            return []
        
        # 收集所有步骤的分数
        step_scores_map: Dict[str, List[Decimal]] = {}
        
        for record in records:
            if record.step_scores:
                for step_key, step_data in record.step_scores.items():
                    if isinstance(step_data, dict) and "score" in step_data:
                        step_name = step_data.get("step_name", step_key)
                        score = Decimal(str(step_data["score"]))
                        
                        if step_name not in step_scores_map:
                            step_scores_map[step_name] = []
                        step_scores_map[step_name].append(score)
        
        # 计算每个步骤的统计信息
        step_analysis = []
        for step_name, scores in step_scores_map.items():
            avg_score = sum(scores) / len(scores)
            # 计算成功率（分数>=60 视为成功）
            success_count = sum(1 for s in scores if s >= 60)
            success_rate = Decimal(str(success_count / len(scores) * 100))
            
            # 生成改进建议
            suggestion = self._generate_step_suggestion(step_name, avg_score)
            
            step_analysis.append(
                StepAnalysisItem(
                    step_name=step_name,
                    average_score=avg_score.quantize(Decimal("0.01")),
                    success_rate=success_rate.quantize(Decimal("0.01")),
                    improvement_suggestion=suggestion
                )
            )
        
        # 按平均分排序（从低到高，突出问题点）
        step_analysis.sort(key=lambda x: float(x.average_score))
        
        return step_analysis
    
    def _generate_step_suggestion(self, step_name: str, avg_score: Decimal) -> Optional[str]:
        """
        根据步骤名称和平均分生成改进建议
        
        Args:
            step_name: 步骤名称
            avg_score: 平均分
            
        Returns:
            改进建议文本
        """
        if avg_score >= 90:
            return None  # 表现优秀，无需建议
        
        # 根据步骤名称提供针对性建议
        suggestions = {
            "提灭火器": "保持背部挺直，屈膝下蹲，用腿部力量提起灭火器",
            "拔保险销": "确保保险销完全拔出，检查是否卡住",
            "握喷管": "双手稳固握持，保持喷管方向稳定",
            "瞄准火源": "对准火焰根部，保持安全距离 2-3 米",
            "压把手": "均匀用力下压，保持连续喷射",
            "准备阶段": "做好个人防护，确认逃生路线",
            "操作阶段": "按照标准流程操作，不要慌乱",
            "收尾阶段": "确认火源完全熄灭，清理现场"
        }
        
        # 查找匹配的建议
        for key, suggestion in suggestions.items():
            if key in step_name:
                return suggestion
        
        # 默认建议
        if avg_score < 60:
            return "需要加强练习，建议观看标准操作视频"
        elif avg_score < 80:
            return "基本掌握要领，注意细节改进"
        else:
            return "表现良好，继续保持"
    
    async def refresh_statistics(self, user_id: int) -> Optional[TrainingStatistics]:
        """
        刷新用户的统计数据（更新到 training_statistics 表）
        
        Args:
            user_id: 用户 ID
            
        Returns:
            更新后的统计数据
        """
        # 从 records 计算最新统计
        personal_stats = await self._calculate_from_records(user_id)
        
        if not personal_stats:
            return None
        
        # 查询是否已有统计记录
        stmt = select(TrainingStatistics).where(TrainingStatistics.user_id == user_id)
        result = await self.session.execute(stmt)
        statistics = result.scalar_one_or_none()
        
        if statistics:
            # 更新现有记录
            statistics.total_trainings = personal_stats.total_trainings
            statistics.completed_trainings = personal_stats.completed_trainings
            statistics.total_training_seconds = personal_stats.total_training_seconds
            statistics.average_score = personal_stats.average_score
            statistics.best_score = personal_stats.best_score
            statistics.last_training_at = personal_stats.last_training_at
        else:
            # 创建新记录
            statistics = TrainingStatistics(
                user_id=user_id,
                total_trainings=personal_stats.total_trainings,
                completed_trainings=personal_stats.completed_trainings,
                total_training_seconds=personal_stats.total_training_seconds,
                average_score=personal_stats.average_score,
                best_score=personal_stats.best_score,
                last_training_at=personal_stats.last_training_at
            )
            self.session.add(statistics)
        
        await self.session.flush()
        await self.session.refresh(statistics)
        
        return statistics
