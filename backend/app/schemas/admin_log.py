"""管理员操作日志相关的 Pydantic Schema"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============ 请求 Schema ============

class AdminLogCreateRequest(BaseModel):
    """创建管理员日志请求"""
    action: str = Field(..., max_length=50, description="操作类型")
    target_type: Optional[str] = Field(None, max_length=50, description="目标类型")
    target_id: Optional[int] = Field(None, description="目标 ID")
    details: Optional[dict] = Field(None, description="操作详情")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP 地址")


# ============ 响应 Schema ============

class AdminLogResponse(BaseModel):
    """管理员日志响应"""
    id: int
    admin_id: int
    action: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AdminLogListResponse(BaseModel):
    """管理员日志列表响应"""
    logs: list[AdminLogResponse]
    total: int
    page: int
    page_size: int
