"""训练相关的 Pydantic Schema"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============ 请求 Schema ============

class TrainingStartRequest(BaseModel):
    """开始训练请求"""
    training_type: str = Field(..., description="训练类型，如 extinguisher（灭火器）")
    duration_seconds: Optional[Decimal] = Field(None, description="预计时长（秒）")


class TrainingUploadRequest(BaseModel):
    """上传训练视频请求"""
    training_id: int = Field(..., description="训练记录 ID")
    video_path: str = Field(..., max_length=255, description="视频文件路径")


class TrainingQueryRequest(BaseModel):
    """训练历史查询请求"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=50, description="每页数量")
    status: Optional[str] = Field(None, description="状态筛选")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")


# ============ 响应 Schema ============

class TrainingRecordResponse(BaseModel):
    """训练记录响应"""
    id: int
    user_id: int
    training_type: str
    status: str
    total_score: Decimal
    step_scores: Optional[Dict[str, Any]] = None
    video_path: Optional[str] = None
    duration_seconds: Optional[Decimal] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    feedback: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TrainingDetailResponse(TrainingRecordResponse):
    """训练详情响应（包含动作日志）"""
    action_count: int = 0
    actions: Optional[List[Dict[str, Any]]] = None


class TrainingHistoryResponse(BaseModel):
    """训练历史列表响应"""
    total: int
    page: int
    page_size: int
    records: List[TrainingRecordResponse]


class TrainingStartResponse(BaseModel):
    """开始训练响应"""
    training_id: int
    status: str
    message: str = "训练已创建，请上传视频"


# ============ 评分相关 Schema ============

class StepScoreSchema(BaseModel):
    """步骤分数 Schema"""
    step_name: str
    score: Decimal
    is_correct: bool
    feedback: Optional[str] = None


class ScoringResultSchema(BaseModel):
    """评分结果 Schema"""
    total_score: Decimal
    step_scores: List[StepScoreSchema]
    feedback: str
    suggestions: List[str] = Field(default_factory=list)
