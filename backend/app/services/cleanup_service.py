"""
定时清理未开始的训练记录

定期删除超过指定时间仍未开始的训练记录
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.training_record import TrainingRecord

logger = logging.getLogger(__name__)

# 清理配置（单位：分钟）
CLEANUP_INTERVAL_MINUTES = 30  # 每 30 分钟执行一次
MAX_AGE_MINUTES = 30  # 删除超过 30 分钟未开始的记录


async def cleanup_unstarted_trainings():
    """清理超时未开始的训练记录"""
    try:
        logger.info(f"开始清理超时未开始的训练记录...")
        
        async for db in get_db():
            # 计算截止时间
            cutoff_time = datetime.utcnow() - timedelta(minutes=MAX_AGE_MINUTES)
            
            # 查询超时的未开始记录
            query = (
                delete(TrainingRecord)
                .where(TrainingRecord.status == 'created')
                .where(TrainingRecord.created_at < cutoff_time)
            )
            
            result = await db.execute(query)
            deleted_count = result.rowcount
            
            await db.commit()
            
            if deleted_count > 0:
                logger.info(f"已删除 {deleted_count} 条超时未开始的训练记录")
            else:
                logger.info("没有需要清理的记录")
            
            break  # 只需要一个数据库会话
            
    except Exception as e:
        logger.error(f"清理任务失败：{e}")
        raise


async def start_cleanup_scheduler():
    """启动定时清理任务"""
    logger.info(f"启动定时清理任务：每{CLEANUP_INTERVAL_MINUTES}分钟执行一次")
    
    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_MINUTES * 60)
            await cleanup_unstarted_trainings()
        except asyncio.CancelledError:
            logger.info("清理任务已停止")
            break
        except Exception as e:
            logger.error(f"清理任务异常：{e}")
            # 继续下一次执行


def setup_cleanup_task(app):
    """在 FastAPI 应用中设置清理任务"""
    
    @app.on_event("startup")
    async def startup_event():
        # 创建后台任务
        app.state.cleanup_task = asyncio.create_task(start_cleanup_scheduler())
        logger.info("清理任务已注册")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        # 取消后台任务
        if hasattr(app.state, 'cleanup_task'):
            app.state.cleanup_task.cancel()
            try:
                await app.state.cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("清理任务已停止")
