from __future__ import annotations

from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base, utc_now
from app.models import ActionLog, TrainingRecord, TrainingStatistics, User


def test_database_models_support_insert_and_query() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(
            username="tester",
            email="tester@example.com",
            password_hash="hashed-password",
        )
        session.add(user)
        session.flush()

        record = TrainingRecord(
            user_id=user.id,
            training_type="extinguisher",
            total_score=Decimal("91.50"),
            step_scores={"aim": 30, "spray": 31.5},
            duration_seconds=Decimal("42.10"),
            started_at=utc_now(),
            completed_at=utc_now(),
        )
        session.add(record)
        session.flush()

        session.add(
            ActionLog(
                record_id=record.id,
                action_name="aim",
                step_index=1,
                is_correct=True,
                confidence_score=Decimal("0.9735"),
                action_timestamp=utc_now(),
                detail={"landmark_count": 33},
            )
        )
        session.add(
            TrainingStatistics(
                user_id=user.id,
                total_trainings=1,
                completed_trainings=1,
                total_training_seconds=Decimal("42.10"),
                average_score=Decimal("91.50"),
                best_score=Decimal("91.50"),
                last_training_at=utc_now(),
            )
        )
        session.commit()

        inserted_record = session.scalar(
            select(TrainingRecord).where(TrainingRecord.user_id == user.id)
        )
        inserted_statistics = session.scalar(
            select(TrainingStatistics).where(TrainingStatistics.user_id == user.id)
        )

        assert inserted_record is not None
        assert inserted_statistics is not None
        assert inserted_record.user.username == "tester"
        assert len(inserted_record.action_logs) == 1
        assert inserted_record.action_logs[0].action_name == "aim"
        assert inserted_statistics.average_score == Decimal("91.50")
