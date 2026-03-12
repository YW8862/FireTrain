"""API 路由统一导出"""
from .users import router as users_router
from .training import router as training_router
from .statistics import router as statistics_router

__all__ = ["users_router", "training_router", "statistics_router"]