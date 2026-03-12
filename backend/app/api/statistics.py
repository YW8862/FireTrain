"""统计相关的 API 路由"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.statistics import (
    PersonalStatisticsResponse,
    TrainingTrendResponse,
    StepAnalysisResponse,
    StatisticsOverviewResponse,
)
from app.services.statistics_service import StatisticsService

router = APIRouter(prefix="/api/stats", tags=["统计分析"])


def get_statistics_service(session: AsyncSession = Depends(get_db)) -> StatisticsService:
    """获取 StatisticsService 实例"""
    return StatisticsService(session)


# ============ 统计接口 ============

@router.get("/personal", response_model=PersonalStatisticsResponse)
async def get_personal_statistics(
    stats_service: StatisticsService = Depends(get_statistics_service),
    # TODO: 添加用户认证
    current_user_id: int = 1  # 临时硬编码
):
    """
    获取个人统计
    
    返回用户的总训练次数、平均分、最佳成绩等统计信息
    """
    stats = await stats_service.get_personal_statistics(current_user_id)
    
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到该用户的统计数据"
        )
    
    return stats


@router.get("/trend", response_model=TrainingTrendResponse)
async def get_training_trend(
    days: int = Query(7, ge=1, le=30, description="查询天数"),
    stats_service: StatisticsService = Depends(get_statistics_service),
    # TODO: 添加用户认证
    current_user_id: int = 1  # 临时硬编码
):
    """
    获取训练趋势
    
    - **days**: 查询最近 N 天的数据（默认 7 天，最多 30 天）
    
    返回每天的训练次数和平均分数，用于绘制趋势图
    """
    trend_data = await stats_service.get_training_trend(current_user_id, days=days)
    
    return TrainingTrendResponse(
        trend_data=trend_data,
        total_days=len(trend_data)
    )


@router.get("/step-analysis", response_model=StepAnalysisResponse)
async def get_step_analysis_api(
    stats_service: StatisticsService = Depends(get_statistics_service),
    # TODO: 添加用户认证
    current_user_id: int = 1  # 临时硬编码
):
    """
    获取步骤分析
    
    分析用户在各操作步骤上的表现，提供改进建议
    """
    analysis = await stats_service.get_step_analysis(current_user_id)
    return StepAnalysisResponse(step_analysis=analysis)


@router.get("/overview", response_model=StatisticsOverviewResponse)
async def get_statistics_overview(
    days: int = Query(7, ge=1, le=30, description="趋势天数"),
    stats_service: StatisticsService = Depends(get_statistics_service),
    # TODO: 添加用户认证
    current_user_id: int = 1  # 临时硬编码
):
    """
    获取统计概览
    
    包含个人统计、近期趋势和步骤分析的完整数据
    适用于首页看板展示
    """
    personal_stats = await stats_service.get_personal_statistics(current_user_id)
    if not personal_stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到该用户的统计数据"
        )
    
    trend_data = await stats_service.get_training_trend(current_user_id, days=days)
    step_analysis = await stats_service.get_step_analysis(current_user_id)
    
    return StatisticsOverviewResponse(
        personal_stats=personal_stats,
        recent_trend=TrainingTrendResponse(
            trend_data=trend_data,
            total_days=len(trend_data)
        ),
        step_analysis=StepAnalysisResponse(step_analysis=step_analysis)
    )
