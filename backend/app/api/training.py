"""训练相关的 API 路由"""
from datetime import datetime
from decimal import Decimal
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status

from app.schemas.training import (
    TrainingStartRequest,
    TrainingStartResponse,
    TrainingRecordResponse,
    TrainingDetailResponse,
    TrainingHistoryResponse,
    TrainingUploadRequest,
    ScoringResultSchema,
)

router = APIRouter(prefix="/api/training", tags=["训练管理"])


# TODO: 实现训练数据库操作
async def create_training_record(user_id: int, training_type: str):
    """创建训练记录（待实现）"""
    return {
        "id": 1,
        "user_id": user_id,
        "training_type": training_type,
        "status": "created",
        "total_score": Decimal("0.00"),
        "created_at": datetime.utcnow()
    }


async def get_training_by_id(training_id: int):
    """根据 ID 获取训练记录（待实现）"""
    return {
        "id": training_id,
        "user_id": 1,
        "training_type": "extinguisher",
        "status": "completed",
        "total_score": Decimal("88.50"),
        "step_scores": {"step1": 18.0, "step2": 20.0},
        "feedback": "整体流程正确",
        "created_at": datetime.utcnow()
    }


async def get_user_trainings(
    user_id: int,
    page: int = 1,
    page_size: int = 10,
    status_filter: str = None,
    start_date: datetime = None,
    end_date: datetime = None
):
    """获取用户训练历史（待实现）"""
    return {
        "total": 5,
        "page": page,
        "page_size": page_size,
        "records": [
            {
                "id": i,
                "user_id": user_id,
                "training_type": "extinguisher",
                "status": "completed",
                "total_score": Decimal(f"{80 + i}"),
                "created_at": datetime.utcnow()
            }
            for i in range(1, 6)
        ]
    }


async def update_training_with_video(training_id: int, video_path: str):
    """更新训练视频路径（待实现）"""
    return True


async def score_training(training_id: int) -> ScoringResultSchema:
    """对训练进行评分（待实现 - AI 模块集成）"""
    return ScoringResultSchema(
        total_score=Decimal("88.50"),
        step_scores=[],
        feedback="评分完成",
        suggestions=["建议改进压把动作"]
    )


# ============ 训练任务接口 ============

@router.post("/start", response_model=TrainingStartResponse, status_code=status.HTTP_201_CREATED)
async def start_training(
    request: TrainingStartRequest,
    # TODO: 添加用户认证
    current_user_id: int = 1  # 临时硬编码
):
    """
    开始训练
    
    - **training_type**: 训练类型（如 extinguisher）
    - **duration_seconds**: 预计时长（可选）
    
    返回训练记录 ID，用于后续上传视频和查询
    """
    training = await create_training_record(current_user_id, request.training_type)
    
    return TrainingStartResponse(
        training_id=training["id"],
        status=training["status"],
        message="训练已创建，请上传视频或开始录制"
    )


@router.post("/upload", response_model=TrainingRecordResponse)
async def upload_video(
    training_id: int = Query(..., description="训练记录 ID"),
    file: UploadFile = File(..., description="视频文件")
):
    """
    上传训练视频
    
    - **training_id**: 训练记录 ID
    - **file**: 视频文件（支持 mp4, avi, mov 等格式）
    """
    # 验证训练记录是否存在
    training = await get_training_by_id(training_id)
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="训练记录不存在"
        )
    
    # 保存文件（实际应该保存到配置的路径）
    video_path = f"./data/videos/{training_id}_{file.filename}"
    
    # TODO: 实际保存文件
    # with open(video_path, "wb") as buffer:
    #     content = await file.read()
    #     buffer.write(content)
    
    # 更新训练记录
    await update_training_with_video(training_id, video_path)
    
    # 触发 AI 评分（异步）
    # TODO: 使用 Celery 或其他异步任务队列
    scoring_result = await score_training(training_id)
    
    return TrainingRecordResponse(
        id=training_id,
        user_id=1,
        training_type="extinguisher",
        status="completed",
        total_score=scoring_result.total_score,
        step_scores={s.step_name: float(s.score) for s in scoring_result.step_scores},
        video_path=video_path,
        feedback=scoring_result.feedback,
        created_at=datetime.utcnow()
    )


@router.get("/{training_id}", response_model=TrainingDetailResponse)
async def get_training_detail(training_id: int):
    """
    获取训练详情
    
    包含完整的训练信息、评分结果和动作日志
    """
    training = await get_training_by_id(training_id)
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="训练记录不存在"
        )
    
    # TODO: 获取动作日志
    actions = []  # 临时返回空
    
    return TrainingDetailResponse(
        **training,
        action_count=len(actions),
        actions=actions
    )


@router.get("/history", response_model=TrainingHistoryResponse)
async def get_training_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    status_filter: str = Query(None, description="状态筛选"),
    start_date: datetime = Query(None, description="开始日期"),
    end_date: datetime = Query(None, description="结束日期"),
    # TODO: 添加用户认证
    current_user_id: int = 1  # 临时硬编码
):
    """
    获取训练历史
    
    支持分页、状态筛选、日期范围筛选
    """
    result = await get_user_trainings(
        current_user_id,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        start_date=start_date,
        end_date=end_date
    )
    
    return TrainingHistoryResponse(
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        records=[
            TrainingRecordResponse(**record)
            for record in result["records"]
        ]
    )


@router.post("/{training_id}/score", response_model=ScoringResultSchema)
async def score_training_api(training_id: int):
    """
    手动触发评分
    
    通常视频上传后会自动触发评分，此接口用于重新评分或调试
    """
    training = await get_training_by_id(training_id)
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="训练记录不存在"
        )
    
    return await score_training(training_id)
