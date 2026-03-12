"""统计相关的 API 路由"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.statistics import (
    PersonalStatisticsResponse,
    TrainingTrendResponse,
    StepAnalysisResponse,
    StatisticsOverviewResponse,
)

router = APIRouter(prefix="/api/stats", tags=["统计分析"])


# TODO: 实现统计数据查询
async def get_user_statistics(user_id: int):
    """获取用户统计数据（待实现）"""
    return {
        "user_id": user_id,
        "total_trainings": 10,
        "completed_trainings": 8,
        "total_training_seconds": Decimal("3600.00"),
        "average_score": Decimal("85.50"),
        "best_score": Decimal("95.00"),
        "last_training_at": datetime.utcnow()
    }


async def get_training_trend(user_id: int, days: int = 7):
    """获取训练趋势数据（待实现）"""
    today = datetime.utcnow().date()
    trend_data = []
    
    for i in range(days):
        date = today - timedelta(days=i)
        trend_data.append({
            "date": date.isoformat(),
            "training_count": i % 3 + 1,
            "average_score": Decimal(f"{80 + i}"),
            "best_score": Decimal(f"{90 + i}") if i % 2 == 0 else None
        })
    
    return {
        "trend_data": trend_data,
        "total_days": days
    }


async def get_step_analysis(user_id: int):
    """获取步骤分析数据（待实现）"""
    return {
        "step_analysis": [
            {
                "step_name": "提灭火器",
                "average_score": Decimal("18.5"),
                "success_rate": Decimal("92.5"),
                "improvement_suggestion": "保持手臂伸直"
            },
            {
                "step_name": "拔保险销",
                "average_score": Decimal("19.0"),
                "success_rate": Decimal("95.0"),
                "improvement_suggestion": None
            },
            {
                "step_name": "握喷管",
                "average_score": Decimal("17.5"),
                "success_rate": Decimal("87.5"),
                "improvement_suggestion": "双手握持更稳定"
            },
            {
                "step_name": "瞄准火源",
                "average_score": Decimal("18.0"),
                "success_rate": Decimal("90.0"),
                "improvement_suggestion": "保持安全距离"
            },
            {
                "step_name": "压把手",
                "average_score": Decimal("17.0"),
                "success_rate": Decimal("85.0"),
                "improvement_suggestion": "均匀用力下压"
            }
        ]
    }


# ============ 统计接口 ============

@router.get("/personal", response_model=PersonalStatisticsResponse)
async def get_personal_statistics(
    # TODO: 添加用户认证
    current_user_id: int = 1  # 临时硬编码
):
    """
    获取个人统计
    
    返回用户的总训练次数、平均分、最佳成绩等统计信息
    """
    stats = await get_user_statistics(current_user_id)
    
    return PersonalStatisticsResponse(**stats)


@router.get("/trend", response_model=TrainingTrendResponse)
async def get_training_trend(
    days: int = Query(7, ge=1, le=30, description="查询天数"),
    # TODO: 添加用户认证
    current_user_id: int = 1  # 临时硬编码
):
    """
    获取训练趋势
    
    - **days**: 查询最近 N 天的数据（默认 7 天，最多 30 天）
    
    返回每天的训练次数和平均分数，用于绘制趋势图
    """
    return await get_training_trend(current_user_id, days=days)


@router.get("/step-analysis", response_model=StepAnalysisResponse)
async def get_step_analysis_api(
    # TODO: 添加用户认证
    current_user_id: int = 1  # 临时硬编码
):
    """
    获取步骤分析
    
    分析用户在各操作步骤上的表现，提供改进建议
    """
    analysis = await get_step_analysis(current_user_id)
    return analysis


@router.get("/overview", response_model=StatisticsOverviewResponse)
async def get_statistics_overview(
    days: int = Query(7, ge=1, le=30, description="趋势天数"),
    # TODO: 添加用户认证
    current_user_id: int = 1  # 临时硬编码
):
    """
    获取统计概览
    
    包含个人统计、近期趋势和步骤分析的完整数据
    适用于首页看板展示
    """
    personal_stats = await get_user_statistics(current_user_id)
    trend = await get_training_trend(current_user_id, days=days)
    step_analysis = await get_step_analysis(current_user_id)
    
    return StatisticsOverviewResponse(
        personal_stats=PersonalStatisticsResponse(**personal_stats),
        recent_trend=TrainingTrendResponse(**trend),
        step_analysis=StepAnalysisResponse(**step_analysis)
    )
