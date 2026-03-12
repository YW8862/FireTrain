"""训练相关的 API 路由"""
import os
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.training_repository import TrainingRepository
from app.services.training_service import TrainingService
from app.schemas.training import (
    TrainingDetailResponse,
    TrainingHistoryResponse,
    TrainingRecordResponse,
    TrainingStartRequest,
    TrainingStartResponse,
    TrainingUploadRequest,
)

router = APIRouter(prefix="/api/training", tags=["训练管理"])


# OAuth2 scheme for token authentication（简化版，实际应该解析 JWT）
# TODO: 实现真实的 JWT 验证
async def get_current_user_id(db: Annotated[AsyncSession, Depends(get_db)]) -> int:
    """
    获取当前用户 ID（临时实现）
    TODO: 从 JWT token 中解析真实用户 ID
    """
    # 临时返回一个测试用户 ID
    return 1


# ============ 训练任务接口 ============

@router.post("/start", response_model=TrainingStartResponse)
async def start_training(
    request: TrainingStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    开始训练任务
    
    - **training_type**: 训练类型（如 extinguisher-灭火器）
    - **duration_seconds**: 预计时长（秒，可选）
    
    返回训练记录 ID，用于后续上传视频
    """
    training_repo = TrainingRepository(db)
    training_service = TrainingService(training_repo)
    
    try:
        training = await training_service.start_training(current_user_id, request)
        
        return TrainingStartResponse(
            training_id=training.id,
            status=training.status,
            message="训练已创建，请上传视频"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/upload")
async def upload_video(
    request: TrainingUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    上传训练视频
    
    - **training_id**: 训练记录 ID
    - **video_path**: 视频文件路径
    
    注意：当前版本只保存文件路径，后续会实现真实文件上传
    """
    training_repo = TrainingRepository(db)
    training_service = TrainingService(training_repo)
    
    try:
        training = await training_service.upload_video(request.training_id, request.video_path)
        
        if not training:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="训练记录不存在"
            )
        
        return {
            "message": "视频上传成功",
            "training_id": training.id,
            "status": training.status,
            "video_path": training.video_path
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/upload-file/{training_id}")
async def upload_video_file(
    training_id: int,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    上传视频文件（真实文件上传）
    
    文件会被保存到服务器的视频目录
    """
    training_repo = TrainingRepository(db)
    training_service = TrainingService(training_repo)
    
    # 验证训练记录是否存在
    training = await training_repo.get_by_id(training_id)
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="训练记录不存在"
        )
    
    # 验证用户权限
    if training.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此训练记录"
        )
    
    # 保存文件
    video_dir = "./data/videos"
    os.makedirs(video_dir, exist_ok=True)
    
    # 生成唯一文件名
    import uuid
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "mp4"
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(video_dir, unique_filename)
    
    try:
        # 读取并保存文件
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 更新训练记录
        updated_training = await training_service.upload_video(training_id, file_path)
        
        return {
            "message": "视频上传成功",
            "training_id": training_id,
            "status": updated_training.status,
            "video_path": file_path,
            "file_size": len(content)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败：{str(e)}"
        )


@router.post("/complete/{training_id}")
async def complete_training(
    training_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    完成训练并计算分数
    
    当前使用模拟分数，后续会接入真实 AI 评分
    """
    training_repo = TrainingRepository(db)
    training_service = TrainingService(training_repo)
    
    # 获取训练记录
    training = await training_repo.get_by_id(training_id)
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="训练记录不存在"
        )
    
    # 验证用户权限
    if training.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此训练记录"
        )
    
    try:
        # 生成模拟分数
        scoring_result = await training_service.generate_mock_score(training.training_type)
        
        # 保存评分结果
        updated_training = await training_service.complete_training_with_score(
            training_id=training_id,
            total_score=scoring_result["total_score"],
            step_scores=scoring_result["step_scores"],
            feedback=scoring_result["feedback"]
        )
        
        return {
            "message": "训练已完成",
            "training_id": training_id,
            "status": updated_training.status,
            "total_score": float(updated_training.total_score),
            "feedback": updated_training.feedback,
            "scoring_details": scoring_result
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============ 查询接口 ============

@router.get("/history", response_model=TrainingHistoryResponse)
async def get_training_history(
    page: int = 1,
    page_size: int = 10,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    获取用户训练历史（分页查询）
    
    - **page**: 页码（默认 1）
    - **page_size**: 每页数量（默认 10，最大 50）
    - **status**: 状态筛选（created/processing/done）
    - **start_date**: 开始日期（ISO 8601 格式）
    - **end_date**: 结束日期（ISO 8601 格式）
    """
    training_repo = TrainingRepository(db)
    training_service = TrainingService(training_repo)
    
    records, total = await training_service.get_user_training_history(
        user_id=current_user_id,
        page=page,
        page_size=page_size,
        status=status,
        start_date=start_date,
        end_date=end_date
    )
    
    return TrainingHistoryResponse(
        total=total,
        page=page,
        page_size=page_size,
        records=[
            TrainingRecordResponse(
                id=r.id,
                user_id=r.user_id,
                training_type=r.training_type,
                status=r.status,
                total_score=r.total_score,
                step_scores=r.step_scores,
                video_path=r.video_path,
                duration_seconds=r.duration_seconds,
                started_at=r.started_at,
                completed_at=r.completed_at,
                feedback=r.feedback,
                created_at=r.created_at
            )
            for r in records
        ]
    )


@router.get("/{training_id}", response_model=TrainingDetailResponse)
async def get_training_detail(
    training_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取训练详情"""
    training_repo = TrainingRepository(db)
    training = await training_repo.get_by_id(training_id)
    
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="训练记录不存在"
        )
    
    # 验证用户权限
    if training.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看此训练记录"
        )
    
    return TrainingDetailResponse(
        id=training.id,
        user_id=training.user_id,
        training_type=training.training_type,
        status=training.status,
        total_score=training.total_score,
        step_scores=training.step_scores,
        video_path=training.video_path,
        duration_seconds=training.duration_seconds,
        started_at=training.started_at,
        completed_at=training.completed_at,
        feedback=training.feedback,
        created_at=training.created_at,
        action_count=0,  # TODO: 获取动作日志数量
        actions=None
    )
