"""
管理员视频检测相关 Schema
"""
from typing import Optional
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
