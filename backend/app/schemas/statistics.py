"""统计相关的 Pydantic Schema"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


# ============ 响应 Schema ============

class PersonalStatisticsResponse(BaseModel):
    """个人统计响应"""
    user_id: int
    total_trainings: int
    completed_trainings: int
    total_training_seconds: Decimal
    average_score: Decimal
    best_score: Decimal
    last_training_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TrainingTrendItem(BaseModel):
    """训练趋势项"""
    date: str  # YYYY-MM-DD 格式
    training_count: int
    average_score: Decimal
    best_score: Optional[Decimal] = None


class TrainingTrendResponse(BaseModel):
    """训练趋势响应"""
    trend_data: List[TrainingTrendItem]
    total_days: int


class StepAnalysisItem(BaseModel):
    """步骤分析项"""
    step_name: str
    average_score: Decimal
    success_rate: Decimal  # 成功率 0-100
    improvement_suggestion: Optional[str] = None


class StepAnalysisResponse(BaseModel):
    """步骤分析响应"""
    step_analysis: List[StepAnalysisItem]


class StatisticsOverviewResponse(BaseModel):
    """统计概览响应"""
    personal_stats: PersonalStatisticsResponse
    recent_trend: TrainingTrendResponse
    step_analysis: StepAnalysisResponse
