from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="student", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # 角色切换相关字段
    can_switch_role: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    original_role: Mapped[str | None] = mapped_column(String(20), nullable=True)

    training_records: Mapped[list["TrainingRecord"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    training_statistics: Mapped["TrainingStatistics | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    admin_logs: Mapped[list["AdminLog"]] = relationship(
        back_populates="admin",
        cascade="all, delete-orphan",
        foreign_keys="AdminLog.admin_id"
    )
    video_tasks: Mapped[list["VideoDetectionTask"]] = relationship(
        back_populates="uploader",
        cascade="all, delete-orphan",
        foreign_keys="VideoDetectionTask.uploader_id"
    )
