"""视频检测任务模型"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class VideoTaskStatus(str, enum.Enum):
    """视频任务状态枚举"""
    PENDING = "pending"  # 等待中
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class VideoDetectionTask(Base):
    """视频检测任务表"""
    
    __tablename__ = "video_detection_tasks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uploader_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id'),
        nullable=False,
        comment='上传者 ID'
    )
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment='文件名'
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment='文件路径'
    )
    file_size: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment='文件大小（字节）'
    )
    status: Mapped[VideoTaskStatus] = mapped_column(
        Enum(VideoTaskStatus),
        default=VideoTaskStatus.PENDING,
        nullable=False,
        comment='状态'
    )
    ai_result: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment='AI 分析结果'
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment='错误信息'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        server_default=text('CURRENT_TIMESTAMP'),
        comment='创建时间'
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment='完成时间'
    )
    
    # 关系
    uploader: Mapped["User"] = relationship(
        back_populates="video_tasks",
        foreign_keys=[uploader_id]
    )
