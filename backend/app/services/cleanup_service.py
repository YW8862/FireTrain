"""清理服务层 - 处理定时清理任务"""
import asyncio
import logging

logger = logging.getLogger(__name__)


class CleanupService:
    """清理服务类"""
    
    def __init__(self):
        self.is_running = False
    
    async def start_cleanup_task(self):
        """启动定时清理任务"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("启动定时清理任务")
        
        # 在后台运行清理任务
        asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """清理任务循环"""
        while self.is_running:
            try:
                await self._perform_cleanup()
                # 每小时执行一次清理
                await asyncio.sleep(3600)
            except Exception as e:
                logger.error(f"清理任务执行失败: {e}")
                await asyncio.sleep(3600)  # 出错后也继续执行
    
    async def _perform_cleanup(self):
        """执行清理操作"""
        logger.info("开始执行定时清理任务")
        
        # 这里可以添加具体的清理逻辑
        # 例如：清理过期的token、清理临时文件等
        
        logger.info("定时清理任务完成")
    
    def stop_cleanup_task(self):
        """停止定时清理任务"""
        self.is_running = False
        logger.info("停止定时清理任务")


# 全局清理服务实例
cleanup_service = CleanupService()


async def setup_cleanup_task(app=None):
    """设置清理任务（供main.py调用）"""
    await cleanup_service.start_cleanup_task()
    return cleanup_service


def stop_cleanup_task(app=None):
    """停止清理任务（供main.py调用）"""
    cleanup_service.stop_cleanup_task()
    return cleanup_service