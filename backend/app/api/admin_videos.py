"""
管理员视频检测 API

功能：
- 管理员上传视频并指定用户
- AI 自动分析视频
- 生成训练记录和评分报告
"""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.users import get_current_user
from app.middleware.permission import require_role
from app.repositories.user_repository import UserRepository
from app.repositories.training_repository import TrainingRepository
from app.core.config import settings
from app.services.training_service import TrainingService
from app.services.upload_service import save_upload_file
from app.services.analysis_progress import (
    STAGE_BASE_PROGRESS,
    STAGE_LABELS,
    progress_tracker,
)
from app.schemas.admin_video import AdminVideoStatusResponse, AdminVideoUploadResponse

router = APIRouter(prefix="/api/admin/video", tags=["管理员视频检测"])


def _build_status_response(training) -> AdminVideoStatusResponse:
    step_scores = training.step_scores or {}
    total_score = float(training.total_score) if training.total_score is not None else None

    # 合并进程内进度追踪器与数据库状态
    progress_snapshot = progress_tracker.get(training.id)

    if training.status in ("done", "failed"):
        # 终态：直接给 100%，使用数据库权威状态
        stage = training.status
        stage_label = STAGE_LABELS.get(stage, stage)
        progress = 100.0
        stage_message = (progress_snapshot or {}).get("stage_message")
    elif progress_snapshot is not None:
        stage = progress_snapshot["stage"]
        stage_label = progress_snapshot["stage_label"]
        progress = progress_snapshot["progress"]
        stage_message = progress_snapshot["stage_message"]
    else:
        # processing 但追踪器里没有（比如后端刚重启），给一个占位
        stage = "queued"
        stage_label = STAGE_LABELS["queued"]
        progress = STAGE_BASE_PROGRESS["queued"]
        stage_message = None

    return AdminVideoStatusResponse(
        training_id=training.id,
        status=training.status,
        total_score=total_score,
        feedback=training.feedback,
        performance_level=step_scores.get("_performance_level"),
        analysis_summary=step_scores.get("_analysis_summary"),
        completed_at=training.completed_at,
        stage=stage,
        stage_label=stage_label,
        progress=progress,
        stage_message=stage_message,
    )


@router.post("/upload", response_model=AdminVideoUploadResponse)
@require_role("admin", "root")
async def admin_upload_video(
    file: UploadFile = File(...),
    username: str = Form(...),
    training_type: str = Form(default="extinguisher"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员上传视频进行检测
    
    - 指定用户名，视频检测结果将保存给该用户
    - 自动进行 AI 分析
    - 生成完整的训练报告和评分
    
    参数：
    - file: 视频文件
    - username: 目标用户名（视频结果归属的用户）
    - training_type: 训练类型（默认 extinguisher）
    """
    # 1. 查找目标用户
    user_repo = UserRepository(db)
    target_user = await user_repo.get_by_username(username)
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 '{username}' 不存在"
        )
    
    # 2. 验证文件类型
    allowed_extensions = ['.mp4', '.avi', '.mov', '.webm']
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式：{file_extension}。支持的格式：{', '.join(allowed_extensions)}"
        )
    
    # 3. 保存视频文件
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    try:
        saved_file = await save_upload_file(
            file,
            settings.ADMIN_VIDEO_DIR,
            filename=unique_filename,
        )
        
        print(f"✅ 视频文件已保存: {saved_file.file_path}")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {str(e)}"
        )
    
    # 4. 创建训练记录
    training_repo = TrainingRepository(db)
    training_service = TrainingService(training_repo)
    
    from datetime import datetime
    from decimal import Decimal
    
    # 创建训练记录
    training_data = {
        "user_id": target_user.id,
        "training_type": training_service._normalize_training_type(training_type),
        "status": "processing",
        "total_score": Decimal("0.00"),
        "video_path": saved_file.file_path,
        "started_at": datetime.utcnow(),
    }
    
    training = await training_repo.create(training_data)
    # 显式 commit：worker 在 _should_process 里会开新 session 读这行，
    # 不 commit 的话 worker 立即拿到 task 也会因为看不到未提交行而跳过
    await db.commit()

    print(f"✅ 训练记录已创建 (ID: {training.id}, 用户: {username})")

    # 5. 异步执行 AI 分析和评分（不传递 db 会话，在任务内部创建）
    #    走有界队列 + worker 池，避免之前 fire-and-forget 模式下的 GC + 孤儿 worker 问题
    from app.services.ai_task_queue import ai_task_queue

    await ai_task_queue.enqueue(training.id)
    
    return AdminVideoUploadResponse(
        message="视频上传成功，正在进行 AI 分析",
        training_id=training.id,
        username=username,
        file_name=file.filename,
        status="processing",
        save_duration_ms=saved_file.save_duration_ms,
    )


@router.get("/status/{training_id}", response_model=AdminVideoStatusResponse)
@require_role("admin", "root")
async def get_admin_video_status(
    training_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询管理员上传视频的分析状态。"""
    training_repo = TrainingRepository(db)
    training = await training_repo.get_by_id(training_id)

    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="训练记录不存在",
        )

    return _build_status_response(training)


@router.delete("/upload/{training_id}")
@require_role("admin", "root")
async def cancel_video_upload(
    training_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    取消视频上传并删除相关文件
    
    - 删除训练记录
    - 删除已上传的视频文件
    """
    import os
    
    training_repo = TrainingRepository(db)
    
    # 获取训练记录
    training = await training_repo.get_by_id(training_id)
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="训练记录不存在"
        )
    
    # 验证权限（只有管理员可以删除）
    # 注意：这里不需要验证 user_id，因为这是管理员上传的
    
    try:
        # 删除视频文件
        if training.video_path and os.path.exists(training.video_path):
            os.remove(training.video_path)
            print(f"✅ 已删除视频文件: {training.video_path}")
        
        # 删除训练记录
        await training_repo.delete(training)
        await db.commit()
        print(f"✅ 已删除训练记录 (ID: {training_id})")
        
        return {
            "message": "已取消上传并删除相关文件",
            "training_id": training_id
        }
        
    except Exception as e:
        print(f"❌ 删除失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )


async def process_admin_video_analysis(training_id: int):
    """
    处理管理员上传视频的 AI 分析
    
    Args:
        training_id: 训练记录 ID
    """
    from app.db.session import async_session_maker
    
    # 在异步任务内部创建新的数据库会话
    async with async_session_maker() as db:
        training_repo = TrainingRepository(db)
        training_service = TrainingService(training_repo)
        
        try:
            print(f"🔄 开始 AI 分析 (训练ID: {training_id})")
            result = await training_service.complete_training_with_ai_analysis(
                training_id=training_id,
                use_ai_scoring=True,
            )
            if not result:
                print(f"❌ 训练记录 {training_id} 不存在")
                return

            await db.commit()
            print(f"✅ 训练记录已更新 (ID: {training_id}, 分数: {result['total_score']})")
            print(f"✅ AI 分析流程完成 (训练ID: {training_id})")
            
        except Exception as e:
            print(f"❌ AI 分析失败 (训练ID: {training_id}): {e}")
            import traceback
            traceback.print_exc()

            progress_tracker.mark_failed(training_id, message=str(e)[:200])

            # 先回滚之前失败的事务，否则后续任何写操作都会被 SQLAlchemy
            # 以 "transaction has been rolled back due to a previous exception" 拒绝，
            # 导致记录永远停留在 processing 状态
            try:
                await db.rollback()
            except Exception as rollback_error:
                print(f"⚠️ 回滚事务失败: {rollback_error}")

            # 更新状态为失败
            try:
                training = await training_repo.get_by_id(training_id)
                if training:
                    await training_repo.update(training, {
                        "status": "failed",
                        "feedback": f"AI 分析失败: {str(e)[:500]}"
                    })
                    await db.commit()
            except Exception as update_error:
                print(f"❌ 更新失败状态时出错: {update_error}")
                try:
                    await db.rollback()
                except Exception:
                    pass
