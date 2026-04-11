"""统计服务层 - 处理统计相关的业务逻辑"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.training_repository import TrainingRepository
from app.repositories.user_repository import UserRepository


class StatisticsService:
    """统计服务类"""
    
    def __init__(self, training_repo: TrainingRepository, user_repo: UserRepository):
        self.training_repo = training_repo
        self.user_repo = user_repo
    
    async def get_system_statistics(self) -> Dict:
        """
        获取系统统计数据
        
        Returns:
            系统统计数据字典
        """
        # 获取用户统计
        total_users = await self.user_repo.count_all()
        
        # 获取训练统计
        total_trainings = await self.training_repo.count_all()
        
        # 获取今日统计数据
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        new_users_today = await self.user_repo.count_by_date_range(today_start, today_end)
        trainings_today = await self.training_repo.count_by_date_range(today_start, today_end)
        
        # 获取平均分数
        average_score = await self.training_repo.get_average_score()
        
        return {
            "total_users": total_users,
            "active_users": total_users,  # 简化处理，实际应该查询活跃用户
            "new_users_today": new_users_today,
            "total_trainings": total_trainings,
            "trainings_today": trainings_today,
            "average_score": round(average_score, 2) if average_score else 0,
            "pending_videos": 0,  # TODO: 实现待检测视频统计
            "completed_videos": 0,  # TODO: 实现已完成视频统计
            "admin_actions_today": 0  # TODO: 实现管理员操作统计
        }
    
    async def get_user_statistics(self, user_id: int) -> Dict:
        """
        获取用户统计数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户统计数据字典
        """
        # 获取用户训练历史
        trainings, _ = await self.training_repo.get_user_history(user_id, page=1, page_size=1000)
        
        # 计算统计信息
        total_trainings = len(trainings)
        completed_trainings = len([t for t in trainings if t.status == "done"])
        
        # 计算平均分数
        scores = [t.total_score for t in trainings if t.total_score is not None]
        average_score = sum(scores) / len(scores) if scores else 0
        
        # 计算最高分数
        highest_score = max(scores) if scores else 0
        
        # 计算最近7天训练次数
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_trainings = len([t for t in trainings if t.started_at and t.started_at >= week_ago])
        
        return {
            "total_trainings": total_trainings,
            "completed_trainings": completed_trainings,
            "average_score": round(average_score, 2),
            "highest_score": round(highest_score, 2),
            "recent_trainings_7d": recent_trainings,
            "completion_rate": round((completed_trainings / total_trainings * 100) if total_trainings > 0 else 0, 2)
        }