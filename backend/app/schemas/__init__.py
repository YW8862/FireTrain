"""Pydantic Schema 统一导出"""
from .user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserUpdateRequest,
    UserInfoResponse,
    TokenResponse,
    LoginResponse,
    RegisterResponse,
    MessageResponse,
)

from .training import (
    TrainingStartRequest,
    TrainingUploadRequest,
    TrainingQueryRequest,
    TrainingRecordResponse,
    TrainingDetailResponse,
    TrainingHistoryResponse,
    TrainingStartResponse,
    StepScoreSchema,
    ScoringResultSchema,
)

from .statistics import (
    PersonalStatisticsResponse,
    TrainingTrendItem,
    TrainingTrendResponse,
    StepAnalysisItem,
    StepAnalysisResponse,
    StatisticsOverviewResponse,
)

__all__ = [
    # User
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserUpdateRequest",
    "UserInfoResponse",
    "TokenResponse",
    "LoginResponse",
    "RegisterResponse",
    "MessageResponse",
    # Training
    "TrainingStartRequest",
    "TrainingUploadRequest",
    "TrainingQueryRequest",
    "TrainingRecordResponse",
    "TrainingDetailResponse",
    "TrainingHistoryResponse",
    "TrainingStartResponse",
    "StepScoreSchema",
    "ScoringResultSchema",
    # Statistics
    "PersonalStatisticsResponse",
    "TrainingTrendItem",
    "TrainingTrendResponse",
    "StepAnalysisItem",
    "StepAnalysisResponse",
    "StatisticsOverviewResponse",
]