"""
管理员视频检测 API

功能：
- 管理员上传视频并指定用户
- AI 自动分析视频
- 生成训练记录和评分报告
"""
import os
import uuid
from typing import Optional

from fastapi.concurrency import run_in_threadpool
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
from app.schemas.admin_video import AdminVideoUploadResponse
from app.models.training_record import TrainingRecord

router = APIRouter(prefix="/api/admin/video", tags=["管理员视频检测"])


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
            "../data/videos/admin_uploads",
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
    
    from app.schemas.training import TrainingStartRequest
    from datetime import datetime
    from decimal import Decimal
    
    # 创建训练记录
    training_data = {
        "user_id": target_user.id,
        "training_type": training_type,
        "status": "processing",
        "total_score": Decimal("0.00"),
        "video_path": saved_file.file_path,
        "started_at": datetime.utcnow(),
    }
    
    training = await training_repo.create(training_data)
    
    print(f"✅ 训练记录已创建 (ID: {training.id}, 用户: {username})")
    
    # 5. 异步执行 AI 分析和评分（不传递 db 会话，在任务内部创建）
    import asyncio
    asyncio.create_task(
        process_admin_video_analysis(training.id)
    )
    
    return AdminVideoUploadResponse(
        message="视频上传成功，正在进行 AI 分析",
        training_id=training.id,
        username=username,
        file_name=file.filename,
        status="processing",
        save_duration_ms=saved_file.save_duration_ms,
    )


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
    from app.ai.training_inference_service import TrainingInferenceService
    from datetime import datetime
    from app.db.session import async_session_maker
    
    # 在异步任务内部创建新的数据库会话
    async with async_session_maker() as db:
        training_repo = TrainingRepository(db)
        training_service = TrainingService(training_repo)
        
        try:
            # 获取训练记录
            training = await training_repo.get_by_id(training_id)
            if not training:
                print(f"❌ 训练记录 {training_id} 不存在")
                return
            
            print(f"🔄 开始 AI 分析 (训练ID: {training_id})")
            
            # 初始化 AI 推理服务
            inference_service = TrainingInferenceService(
                yolo_model_path=settings.YOLO_MODEL_PATH,
                yolo_conf_threshold=0.5,
                use_pose_analysis=True
            )
            
            # 分析视频
            analysis_result = await run_in_threadpool(
                lambda: inference_service.analyze_video(
                    video_path=training.video_path,
                    training_type=training.training_type
                )
            )
            
            print(f"✅ AI 分析完成，检测到 {analysis_result.get('total_detections', 0)} 个目标")
            
            # 验证检测结果
            validation_result = training_service._validate_detection_result(analysis_result)
            
            if not validation_result['is_valid']:
                print(f"⚠️ 未检测到有效动作：{validation_result['reason']}")
                # 生成 0 分结果
                scoring_result = await training_service._generate_zero_score_result(
                    training_type=training.training_type,
                    reason=validation_result['reason']
                )
            else:
                # 使用 LLM 或降级方案评分
                scoring_result = await training_service._score_with_llm_or_fallback(
                    analysis_result=analysis_result,
                    inference_service=inference_service,
                )
            
            inference_service.close()
            
            # 更新训练记录
            from decimal import Decimal
            
            update_data = {
                "status": "done",
                "total_score": Decimal(str(scoring_result["total_score"])),
                "step_scores": scoring_result.get("step_scores", {}),
                "feedback": scoring_result.get("feedback", ""),
                "completed_at": datetime.utcnow(),
            }
            
            await training_repo.update(training, update_data)
            await db.commit()
            
            print(f"✅ 训练记录已更新 (ID: {training_id}, 分数: {scoring_result['total_score']})")
            
            # 保存动作日志（如果有）
            if scoring_result.get("action_logs"):
                from app.repositories.action_log_repository import ActionLogRepository
                action_log_repo = ActionLogRepository(db)
                
                for action_log in scoring_result["action_logs"]:
                    await action_log_repo.create({
                        "training_id": training_id,
                        **action_log
                    })
                
                await db.commit()
            
            print(f"✅ AI 分析流程完成 (训练ID: {training_id})")
            
        except Exception as e:
            print(f"❌ AI 分析失败 (训练ID: {training_id}): {e}")
            import traceback
            traceback.print_exc()
            
            # 更新状态为失败
            try:
                training = await training_repo.get_by_id(training_id)
                if training:
                    await training_repo.update(training, {
                        "status": "failed",
                        "feedback": f"AI 分析失败: {str(e)}"
                    })
                    await db.commit()
            except Exception as update_error:
                print(f"❌ 更新失败状态时出错: {update_error}")
