"""统计服务层 - 处理统计相关的业务逻辑"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.training_repository import TrainingRepository
from app.repositories.user_repository import UserRepository
from app.schemas.statistics import (
    PersonalStatisticsResponse,
    StepAnalysisItem,
    TrainingTrendItem,
)


class StatisticsService:
    """统计服务类"""

    COMPLETED_STATUSES = {"done", "completed"}
    ZERO_DECIMAL = Decimal("0.00")

    def __init__(self, session: AsyncSession):
        self.session = session
        self.training_repo = TrainingRepository(session)
        self.user_repo = UserRepository(session)

    @staticmethod
    def _to_decimal(value: Any, places: str = "0.01") -> Decimal:
        """将数值转换为 Decimal，并统一保留两位小数。"""
        if value is None:
            return Decimal("0").quantize(Decimal(places), rounding=ROUND_HALF_UP)
        return Decimal(str(value)).quantize(Decimal(places), rounding=ROUND_HALF_UP)

    @staticmethod
    def _normalize_datetime(value: Optional[datetime]) -> Optional[datetime]:
        """统一时间对象，避免时区混用导致比较报错。"""
        if value is None:
            return None
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    @classmethod
    def _is_completed(cls, status: Optional[str]) -> bool:
        return (status or "").lower() in cls.COMPLETED_STATUSES

    @classmethod
    def _get_training_datetime(cls, training: Any) -> Optional[datetime]:
        return (
            cls._normalize_datetime(getattr(training, "completed_at", None))
            or cls._normalize_datetime(getattr(training, "started_at", None))
            or cls._normalize_datetime(getattr(training, "created_at", None))
        )

    @staticmethod
    def _build_improvement_suggestion(average_score: Decimal, success_rate: Decimal) -> Optional[str]:
        """根据平均分和成功率生成简短建议。"""
        if average_score >= Decimal("90") and success_rate >= Decimal("90"):
            return "表现优秀，继续保持当前动作稳定性。"
        if average_score >= Decimal("80") and success_rate >= Decimal("80"):
            return "整体表现良好，可继续优化动作细节和连贯性。"
        if average_score >= Decimal("60") and success_rate >= Decimal("60"):
            return "已基本掌握该步骤，建议加强重复练习提升熟练度。"
        return "该步骤仍需重点练习，建议对照标准流程反复纠正动作。"

    async def get_system_statistics(self) -> Dict:
        """
        获取系统统计数据

        Returns:
            系统统计数据字典
        """
        total_users = await self.user_repo.count_all()
        total_trainings = await self.training_repo.count_all()

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        new_users_today = await self.user_repo.count_by_date_range(today_start, today_end)
        trainings_today = await self.training_repo.count_by_date_range(today_start, today_end)
        average_score = await self.training_repo.get_average_score()

        return {
            "total_users": total_users,
            "active_users": total_users,
            "new_users_today": new_users_today,
            "total_trainings": total_trainings,
            "trainings_today": trainings_today,
            "average_score": round(average_score, 2) if average_score else 0,
            "pending_videos": 0,
            "completed_videos": 0,
            "admin_actions_today": 0,
        }

    def _build_empty_personal_statistics(self, user_id: int) -> PersonalStatisticsResponse:
        """为无训练数据的用户返回零值统计。"""
        return PersonalStatisticsResponse(
            user_id=user_id,
            total_trainings=0,
            completed_trainings=0,
            total_training_seconds=self.ZERO_DECIMAL,
            average_score=self.ZERO_DECIMAL,
            best_score=self.ZERO_DECIMAL,
            last_training_at=None,
        )

    async def get_user_statistics(self, user_id: int) -> Dict:
        """
        获取用户统计数据

        Args:
            user_id: 用户ID

        Returns:
            用户统计数据字典
        """
        personal_stats = await self.get_personal_statistics(user_id)
        recent_trend = await self.get_training_trend(user_id, days=7)
        recent_trainings = sum(item.training_count for item in recent_trend)

        total_trainings = personal_stats.total_trainings
        completed_trainings = personal_stats.completed_trainings

        return {
            "total_trainings": total_trainings,
            "completed_trainings": completed_trainings,
            "average_score": float(personal_stats.average_score),
            "highest_score": float(personal_stats.best_score),
            "recent_trainings_7d": recent_trainings,
            "completion_rate": round(
                (completed_trainings / total_trainings * 100) if total_trainings > 0 else 0,
                2,
            ),
        }

    async def get_personal_statistics(self, user_id: int) -> PersonalStatisticsResponse:
        """获取个人统计数据。"""
        trainings = await self.training_repo.get_by_user_id(user_id)
        if not trainings:
            return self._build_empty_personal_statistics(user_id)

        completed_trainings = [t for t in trainings if self._is_completed(getattr(t, "status", None))]
        scored_trainings = [t for t in completed_trainings if getattr(t, "total_score", None) is not None]

        scores = [Decimal(str(t.total_score)) for t in scored_trainings]
        durations = [
            Decimal(str(t.duration_seconds))
            for t in completed_trainings
            if getattr(t, "duration_seconds", None) is not None
        ]
        timestamps = [self._get_training_datetime(t) for t in trainings]
        timestamps = [t for t in timestamps if t is not None]

        average_score = sum(scores) / len(scores) if scores else self.ZERO_DECIMAL
        best_score = max(scores) if scores else self.ZERO_DECIMAL
        total_training_seconds = sum(durations, self.ZERO_DECIMAL) if durations else self.ZERO_DECIMAL

        return PersonalStatisticsResponse(
            user_id=user_id,
            total_trainings=len(trainings),
            completed_trainings=len(completed_trainings),
            total_training_seconds=self._to_decimal(total_training_seconds),
            average_score=self._to_decimal(average_score),
            best_score=self._to_decimal(best_score),
            last_training_at=max(timestamps) if timestamps else None,
        )

    async def get_training_trend(self, user_id: int, days: int = 7) -> List[TrainingTrendItem]:
        """获取最近 N 天的训练趋势。"""
        trainings = await self.training_repo.get_by_user_id(user_id)

        today = datetime.utcnow().date()
        start_date = today - timedelta(days=days - 1)
        buckets: Dict[str, Dict[str, Any]] = {}

        for offset in range(days):
            current_date = start_date + timedelta(days=offset)
            buckets[current_date.isoformat()] = {"count": 0, "scores": []}

        for training in trainings:
            training_time = self._get_training_datetime(training)
            if training_time is None:
                continue

            date_key = training_time.date().isoformat()
            if date_key not in buckets:
                continue

            buckets[date_key]["count"] += 1
            if getattr(training, "total_score", None) is not None:
                buckets[date_key]["scores"].append(Decimal(str(training.total_score)))

        trend_items: List[TrainingTrendItem] = []
        for date_key, bucket in buckets.items():
            scores = bucket["scores"]
            average_score = sum(scores) / len(scores) if scores else self.ZERO_DECIMAL
            best_score = max(scores) if scores else None
            trend_items.append(
                TrainingTrendItem(
                    date=date_key,
                    training_count=bucket["count"],
                    average_score=self._to_decimal(average_score),
                    best_score=self._to_decimal(best_score) if best_score is not None else None,
                )
            )

        return trend_items

    async def get_step_analysis(self, user_id: int) -> List[StepAnalysisItem]:
        """获取用户各步骤表现分析。"""
        trainings = await self.training_repo.get_by_user_id(user_id)
        step_buckets: Dict[str, Dict[str, Any]] = {}

        for training in trainings:
            if not self._is_completed(getattr(training, "status", None)):
                continue

            step_scores = getattr(training, "step_scores", None) or {}
            if not isinstance(step_scores, dict):
                continue

            for step_key, step_data in step_scores.items():
                if step_key.startswith("_") or not isinstance(step_data, dict):
                    continue

                score = step_data.get("score")
                if score is None:
                    continue

                step_name = step_data.get("step_name") or step_key
                bucket = step_buckets.setdefault(
                    step_name,
                    {"scores": [], "success_count": 0, "training_count": 0},
                )

                numeric_score = Decimal(str(score))
                bucket["scores"].append(numeric_score)
                bucket["training_count"] += 1

                is_correct = step_data.get("is_correct")
                if isinstance(is_correct, bool):
                    bucket["success_count"] += int(is_correct)
                elif numeric_score >= Decimal("60"):
                    bucket["success_count"] += 1

        analysis: List[StepAnalysisItem] = []
        for step_name, bucket in step_buckets.items():
            training_count = bucket["training_count"]
            if training_count == 0:
                continue

            average_score = sum(bucket["scores"]) / training_count
            success_rate = Decimal(bucket["success_count"] * 100) / Decimal(training_count)

            analysis.append(
                StepAnalysisItem(
                    step_name=step_name,
                    average_score=self._to_decimal(average_score),
                    success_rate=self._to_decimal(success_rate),
                    improvement_suggestion=self._build_improvement_suggestion(
                        self._to_decimal(average_score),
                        self._to_decimal(success_rate),
                    ),
                )
            )

        analysis.sort(key=lambda item: (item.average_score, item.step_name))
        return analysis

    async def refresh_statistics(self, user_id: int) -> PersonalStatisticsResponse:
        """刷新并返回最新个人统计。"""
        return await self.get_personal_statistics(user_id)