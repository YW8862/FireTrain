"""Service 层模块"""
from app.services.statistics_service import StatisticsService
from app.services.training_service import TrainingService
from app.services.user_service import UserService

__all__ = [
    "StatisticsService",
    "TrainingService",
    "UserService",
]