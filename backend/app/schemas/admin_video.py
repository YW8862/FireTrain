"""
管理员视频检测相关 Schema
"""
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AdminVideoUploadRequest(BaseModel):
    """管理员上传视频请求"""
    username: str = Field(..., description="目标用户名（视频结果归属的用户）")
    training_type: str = Field(default="extinguisher", description="训练类型")


class AdminVideoUploadResponse(BaseModel):
    """管理员上传视频响应"""
    message: str
    training_id: int
    username: str
    file_name: str
    status: str
    save_duration_ms: int = Field(..., description="服务端落盘耗时（毫秒）")


class AdminVideoStatusResponse(BaseModel):
    """管理员视频分析状态响应"""
    training_id: int
    status: str
    total_score: Optional[float] = Field(default=None, description="分析完成后的总分")
    feedback: Optional[str] = Field(default=None, description="整体反馈")
    performance_level: Optional[str] = Field(default=None, description="表现等级编码")
    analysis_summary: Optional[Dict[str, Any]] = Field(default=None, description="统一分析摘要")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    # 细粒度进度字段（仅 processing 阶段有值）
    stage: Optional[str] = Field(
        default=None,
        description="当前阶段代码：queued/loading_model/video_analysis/rule_scoring/llm_scoring/saving/done/failed",
    )
    stage_label: Optional[str] = Field(default=None, description="当前阶段中文说明，UI 直接展示")
    progress: Optional[float] = Field(
        default=None,
        description="整体分析进度百分比 0-100",
    )
    stage_message: Optional[str] = Field(
        default=None,
        description="阶段附加信息（如帧处理进度、失败原因等）",
    )
