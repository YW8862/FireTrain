from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base, utc_now
from app.models import ActionLog, TrainingRecord, TrainingStatistics, User


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "verify.db"
        engine = create_engine(f"sqlite:///{db_path}", future=True)
        Base.metadata.create_all(engine)

        with Session(engine) as session:
            user = User(
                username="demo_user",
                email="demo@example.com",
                password_hash="hashed-password",
            )
            session.add(user)
            session.flush()

            record = TrainingRecord(
                user_id=user.id,
                training_type="extinguisher",
                total_score=Decimal("88.50"),
                step_scores={"check_pressure": 18.0, "pull_pin": 20.0},
                duration_seconds=Decimal("35.20"),
                started_at=utc_now(),
                completed_at=utc_now(),
                feedback="整体流程正确，注意压把动作衔接。",
            )
            session.add(record)
            session.flush()

            session.add_all(
                [
                    ActionLog(
                        record_id=record.id,
                        action_name="check_pressure",
                        step_index=1,
                        is_correct=True,
                        confidence_score=Decimal("0.9625"),
                        action_timestamp=utc_now(),
                        detail={"source": "rule-engine"},
                    ),
                    ActionLog(
                        record_id=record.id,
                        action_name="pull_pin",
                        step_index=2,
                        is_correct=True,
                        confidence_score=Decimal("0.9510"),
                        action_timestamp=utc_now(),
                        detail={"source": "rule-engine"},
                    ),
                    TrainingStatistics(
                        user_id=user.id,
                        total_trainings=1,
                        completed_trainings=1,
                        total_training_seconds=Decimal("35.20"),
                        average_score=Decimal("88.50"),
                        best_score=Decimal("88.50"),
                        last_training_at=utc_now(),
                    ),
                ]
            )
            session.commit()

            inserted_record = session.scalar(
                select(TrainingRecord).where(TrainingRecord.user_id == user.id)
            )
            statistics = session.scalar(
                select(TrainingStatistics).where(TrainingStatistics.user_id == user.id)
            )

            if inserted_record is None or statistics is None:
                raise RuntimeError("数据库验证失败：未查询到刚插入的数据。")

            result = {
                "username": inserted_record.user.username,
                "training_type": inserted_record.training_type,
                "action_count": len(inserted_record.action_logs),
                "total_score": str(inserted_record.total_score),
                "average_score": str(statistics.average_score),
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
