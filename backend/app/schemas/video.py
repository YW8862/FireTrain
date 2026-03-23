"""视频检测任务相关的 Pydantic Schema"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.video_detection_task import VideoTaskStatus


# ============ 请求 Schema ============

class VideoUploadRequest(BaseModel):
    """视频上传请求（用于文档）"""
    pass  # 实际使用 multipart/form-data


# ============ 响应 Schema ============

class VideoTaskResponse(BaseModel):
    """视频检测任务响应"""
    id: int
    uploader_id: int
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    status: VideoTaskStatus
    ai_result: Optional[dict] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class VideoTaskListResponse(BaseModel):
    """视频检测任务列表响应"""
    tasks: list[VideoTaskResponse]
    total: int
    page: int
    page_size: int


class VideoUploadResponse(BaseModel):
    """视频上传响应"""
    message: str
    task_id: int
    file_name: str
