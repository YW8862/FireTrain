from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class TrainingRecord(TimestampMixin, Base):
    __tablename__ = "training_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    training_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="completed", nullable=False)
    total_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    step_scores: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    video_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    duration_seconds: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="training_records")
    action_logs: Mapped[list["ActionLog"]] = relationship(
        back_populates="training_record",
        cascade="all, delete-orphan",
    )
