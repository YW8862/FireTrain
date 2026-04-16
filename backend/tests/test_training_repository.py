from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.repositories.training_repository import TrainingRepository


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


class _MappingsResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows


@pytest.mark.asyncio
async def test_query_with_filters_fetches_page_with_single_list_query():
    fake_session = AsyncMock()
    fake_session.execute.side_effect = [
        _ScalarResult(2),
        _MappingsResult([
            {
                "id": 101,
                "user_id": 7,
                "username": "admin",
                "training_type": "fire_extinguisher",
                "total_score": Decimal("88.50"),
                "status": "done",
                "duration_seconds": Decimal("123"),
                "created_at": datetime(2026, 4, 1, 10, 0, 0),
                "completed_at": datetime(2026, 4, 1, 10, 2, 3),
            },
            {
                "id": 102,
                "user_id": 8,
                "username": "student",
                "training_type": "fire_extinguisher",
                "total_score": None,
                "status": "processing",
                "duration_seconds": None,
                "created_at": datetime(2026, 4, 2, 9, 0, 0),
                "completed_at": None,
            },
        ]),
    ]

    repository = TrainingRepository(fake_session)

    trainings, total = await repository.query_with_filters(page=1, page_size=20)

    assert total == 2
    assert len(trainings) == 2
    assert trainings[0]["username"] == "admin"
    assert trainings[0]["score"] == 88.5
    assert trainings[0]["duration"] == 123.0
    assert trainings[1]["username"] == "student"
    assert trainings[1]["score"] is None
    assert trainings[1]["duration"] is None
    assert fake_session.execute.await_count == 2
