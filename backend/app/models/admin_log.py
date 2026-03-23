"""管理员操作日志模型"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AdminLog(Base):
    """管理员操作日志表"""
    
    __tablename__ = "admin_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('users.id'), 
        nullable=False,
        comment='管理员 ID'
    )
    action: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment='操作类型'
    )
    target_type: Mapped[Optional[str]] = mapped_column(
        String(50), 
        nullable=True,
        comment='目标类型'
    )
    target_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True,
        comment='目标 ID'
    )
    details: Mapped[Optional[dict]] = mapped_column(
        JSON, 
        nullable=True,
        comment='操作详情'
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), 
        nullable=True,
        comment='IP 地址'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        server_default=text('CURRENT_TIMESTAMP'),
        comment='创建时间'
    )
    
    # 关系
    admin: Mapped["User"] = relationship(
        back_populates="admin_logs",
        foreign_keys=[admin_id]
    )
