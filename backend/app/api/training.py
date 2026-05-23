"""训练相关的 API 路由"""
import os
import logging
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Dict, List, Optional

from fastapi.concurrency import run_in_threadpool
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.training_repository import TrainingRepository
from app.services.training_service import TrainingService
from app.services.upload_service import save_upload_file
from app.core.security import get_current_user_id
from app.core.config import settings
from app.schemas.training import (
    TrainingDetailResponse,
    TrainingHistoryResponse,
    TrainingRecordResponse,
    TrainingStartRequest,
    TrainingStartResponse,
    TrainingUploadRequest,
)

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/training", tags=["训练管理"])


# ============ 响应模型 ============

class StepScoreDetail(BaseModel):
    """步骤分数详情"""
    step_name: str = Field(..., description="步骤名称")
    score: float = Field(..., description="分数 (0-100)")
    is_correct: bool = Field(..., description="是否正确")
    feedback: str = Field(..., description="反馈信息")
    weight: float = Field(default=1.0, description="权重")


class ScoringDetails(BaseModel):
    """评分详情"""
    total_score: float = Field(..., description="总分")
    step_scores: Dict[str, Any] = Field(default={}, description="步骤分数")
    feedback: str = Field(..., description="总体反馈")
    suggestions: List[str] = Field(default=[], description="改进建议")
    performance_level: Optional[str] = Field(None, description="表现等级")
    dimension_scores: Optional[Dict[str, Any]] = Field(None, description="维度分数")


class TrainingCompleteResponse(BaseModel):
    """完成训练响应（支持 AI 评分）"""
    message: str = Field(..., description="响应消息")
    training_id: int = Field(..., description="训练记录 ID")
    status: str = Field(..., description="训练状态")
    total_score: float = Field(..., description="总分")
    feedback: str = Field(..., description="反馈信息")
    used_ai_scoring: bool = Field(..., description="是否使用 AI 评分")
    scoring_details: ScoringDetails = Field(..., description="评分详情")


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


@router.delete("/{training_id}")
async def delete_training(
    training_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    删除当前用户自己的未完成训练记录
    """
    training_repo = TrainingRepository(db)

    training = await training_repo.get_by_id(training_id)
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="训练记录不存在"
        )

    if training.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此训练记录"
        )

    if training.status == "done":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已完成训练记录不能取消删除"
        )

    try:
        if training.video_path and os.path.exists(training.video_path):
            os.remove(training.video_path)
    except OSError as exc:
        logger.warning("删除训练视频文件失败: %s", exc)

    await training_repo.delete(training)
    return {"message": "训练记录删除成功", "training_id": training_id}


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


@router.post("/precheck/{training_id}")
async def precheck_training(
    training_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    预检测训练视频（快速分析）
    
    - **training_id**: 训练记录 ID
    
    快速分析视频，检查是否有有效动作
    
    返回：
    {
        "is_valid": true/false,
        "reason": "原因说明"
    }
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
    
    # 如果没有视频，直接返回无效
    if not training.video_path:
        return {"is_valid": False, "reason": "未上传视频"}
    
    try:
        # 快速 AI 分析（只分析前 5 秒的视频）
        from app.ai.training_inference_service import TrainingInferenceService
        inference_service = TrainingInferenceService(
            yolo_model_path=settings.YOLO_MODEL_PATH,
            yolo_conf_threshold=0.5,
            use_pose_analysis=True
        )
        
        analysis_result = await run_in_threadpool(
            lambda: inference_service.analyze_video(
                video_path=training.video_path,
                training_type=training.training_type
            )
        )
        inference_service.close()

        validation_result = training_service._validate_detection_result(
            analysis_result.get("analysis_summary", analysis_result)
        )
        return validation_result
        
    except Exception as e:
        print(f"预检测失败：{e}")
        return {"is_valid": False, "reason": f"预检测失败：{str(e)}"}


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
    
    try:
        saved_file = await save_upload_file(
            file,
            settings.VIDEO_DIR,
        )
        
        # 更新训练记录
        updated_training = await training_service.upload_video(training_id, saved_file.file_path)
        
        return {
            "message": "视频上传成功",
            "training_id": training_id,
            "status": updated_training.status,
            "video_path": saved_file.file_path,
            "file_size": saved_file.file_size,
            "save_duration_ms": saved_file.save_duration_ms
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败：{str(e)}"
        )


@router.post("/complete/{training_id}", response_model=TrainingCompleteResponse)
async def complete_training(
    training_id: int,
    use_ai_scoring: bool = True,  # 新增参数：是否使用 AI 评分
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    完成训练并计算分数（支持 AI 评分）
    
    - **training_id**: 训练记录 ID
    - **use_ai_scoring**: 是否使用 AI 评分（默认 True）
    
    如果 use_ai_scoring=True 且有视频文件，将使用 AI 模型分析视频：
    1. YOLOv8 目标检测
    2. MediaPipe 姿态分析
    3. 规则引擎综合评分
    
    否则使用模拟评分（基于规则和随机性）
    
    ## 响应示例
    ```json
    {
      "message": "训练已完成",
      "training_id": 1,
      "status": "done",
      "total_score": 85.5,
      "feedback": "优秀！动作规范，流程熟练，继续保持",
      "used_ai_scoring": true,
      "scoring_details": {
        "total_score": 85.5,
        "step_scores": {...},
        "feedback": "...",
        "suggestions": [...]
      }
    }
    ```
    
    ## 异常处理
    - 404: 训练记录不存在
    - 403: 无权操作此训练记录
    - 400: 当前状态不能完成训练/视频路径为空
    - 500: AI 推理失败（已降级到模拟评分）
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
    
    # 验证用户权限（参考 system.md 第 3.4.5 节）
    if training.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此训练记录"
        )
    
    try:
        # 使用 AI 分析或直接模拟评分
        result = await training_service.complete_training_with_ai_analysis(
            training_id=training_id,
            use_ai_scoring=use_ai_scoring
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="训练记录不存在"
            )
        
        # 返回标准化响应（参考 system.md 第 4.2.5 节）
        return TrainingCompleteResponse(
            message="训练已完成",
            training_id=training_id,
            status=result["status"],
            total_score=result["total_score"],
            feedback=result["feedback"],
            used_ai_scoring=result["used_ai_scoring"],
            scoring_details=result["scoring_result"]
        )
    except ValueError as e:
        # 业务逻辑异常（参考 system.md 第 3.4.5 节）
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # 未知异常（降级处理）
        logger.error(f"完成训练时发生异常：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"训练完成失败：{str(e)}"
        )


# ============ 查询接口 ============

@router.get("/types")
async def get_training_types():
    """
    获取所有训练类型配置（统一配置接口）

    返回所有可用的训练类型，包括步骤定义、操作指引、提示文字等。
    前端所有训练类型选择组件都应调用此接口获取配置。
    """
    from app.ai.fire_extinguisher_standard import (
        TRAINING_TYPE_FIRE_EXTINGUISHER,
        STEP_DEFINITIONS,
    )

    types = [
        {
            "value": TRAINING_TYPE_FIRE_EXTINGUISHER,
            "label": "灭火器训练",
            "steps": STEP_DEFINITIONS,
            "instructions": [
                "准备阶段：做好个人防护，确认逃生路线",
                "提起灭火器：用腿部力量提起灭火器",
                "拔保险销：握住拉环用力拔出",
                "握喷管：双手稳固握持喷管",
                "瞄准火源：对准火焰根部，保持 2-3 米距离",
                "压把手：均匀用力下压，左右扫射"
            ],
            "bannerMessage": "请保持摄像头对准训练人员全身，避免遮挡关键动作，确保动作连续清晰。",
            "confirmMessage": "准备好开始训练了吗？请确保已做好个人防护，确认逃生路线畅通，灭火器在有效期内。",
            "stepCount": len(STEP_DEFINITIONS),
        }
    ]

    return {"types": types}


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
    - **status**: 状态筛选（pending/processing/done/failed）
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
    """获取训练详情
    
    - 普通用户只能查看自己的训练记录
    - 管理员可以查看所有训练记录
    """
    logger.error(f"⚠️⚠️⚠️ get_training_detail 被调用！training_id={training_id}, current_user_id={current_user_id}")
    
    from app.repositories.user_repository import UserRepository
    
    training_repo = TrainingRepository(db)
    training = await training_repo.get_by_id(training_id)
    
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="训练记录不存在"
        )
    
    # 验证用户权限
    logger.info(f"🔍 开始权限检查: training_id={training_id}, user_id={training.user_id}, current_user_id={current_user_id}")
    
    # 如果是管理员或 Root，可以查看所有记录
    user_repo = UserRepository(db)
    current_user = await user_repo.get_by_id(current_user_id)
    
    logger.info(f"👤 当前用户: {current_user.username if current_user else 'None'}, 角色: {current_user.role if current_user else 'None'}")
    
    if current_user and current_user.role in ["admin", "root"]:
        # 管理员可以查看所有记录
        logger.info(f"✅ 管理员 {current_user.username} 查看训练记录 {training_id}")
    elif training.user_id != current_user_id:
        # 普通用户只能查看自己的记录
        logger.warning(f"❌ 权限不足: training.user_id={training.user_id} != current_user_id={current_user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看此训练记录"
        )
    
    # 查询训练记录所属用户，便于前端直接展示用户名
    training_owner = await user_repo.get_by_id(training.user_id)

    return TrainingDetailResponse(
        id=training.id,
        user_id=training.user_id,
        username=training_owner.username if training_owner else None,
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
        actions=None,
        suggestions=(training.step_scores or {}).get("_suggestions", []),
        dimension_scores=(training.step_scores or {}).get("_dimension_scores"),
        performance_level=(training.step_scores or {}).get("_performance_level"),
        analysis_summary=(training.step_scores or {}).get("_analysis_summary"),
    )
