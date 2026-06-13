"""AI 任务有界队列 + Worker 池

为什么需要这个模块？
--------------------
原 `app/api/admin_videos.py:154` 用
    asyncio.create_task(process_admin_video_analysis(training.id))
启动后台任务，返回值未保存，FastAPI 请求 handler 返回后任务可能被 GC，
加上 YOLO 在子进程/线程池里跑，当 record 被删除时 worker 不知道仍死磕，
导致线程池被占满，新任务一直卡在 'queued' 阶段。

这里用「持久 worker + 有界 asyncio.Queue」替代 fire-and-forget：
- 任务不会因为引用丢失被 GC（worker 任务保存在 `_workers` 列表里）
- 队列有界，新任务排队而不是丢失
- Worker 启动时自动恢复孤儿 'processing' 记录
- Worker 处理前再 check 一次 record 是否还活着（被删/取消则跳过）
- 优雅 shutdown
"""
import asyncio
import logging
from typing import List, Set

from sqlalchemy import text

from app.db.session import async_session_maker

logger = logging.getLogger(__name__)


class AITaskQueue:
    """AI 推理任务的有界队列 + Worker 池（模块级单例使用）"""

    def __init__(self, num_workers: int = 2, queue_maxsize: int = 1000):
        self.num_workers = num_workers
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=queue_maxsize)
        self._workers: List[asyncio.Task] = []
        self._inflight: Set[int] = set()  # 防止同一 training_id 被并发处理
        self._stopped = False
        self._started = False

    async def start(self) -> None:
        """启动 N 个 worker + 恢复孤儿 'processing' 记录。"""
        if self._started:
            logger.warning("AITaskQueue 已经启动，忽略重复 start()")
            return

        self._started = True
        self._stopped = False

        # 1) 恢复：DB 里所有 status='processing' 的都重新入队
        try:
            async with async_session_maker() as s:
                r = await s.execute(
                    text("SELECT id FROM training_records WHERE status='processing'")
                )
                orphan_ids = [row[0] for row in r.fetchall()]
        except Exception as e:
            logger.exception(f"恢复孤儿任务时查询 DB 失败: {e}")
            orphan_ids = []

        for tid in orphan_ids:
            try:
                await self.enqueue(tid)
            except Exception as e:
                logger.exception(f"恢复孤儿任务 {tid} 入队失败: {e}")
        logger.info(
            f"AITaskQueue 启动: workers={self.num_workers}, "
            f"恢复 {len(orphan_ids)} 条 'processing' 孤儿任务"
        )

        # 2) 启动 worker
        for i in range(self.num_workers):
            t = asyncio.create_task(self._worker_loop(i), name=f"ai-worker-{i}")
            self._workers.append(t)

    async def enqueue(self, training_id: int) -> None:
        """入队一个训练任务。如果已经在 inflight 集合里则跳过。"""
        if self._stopped:
            logger.warning(f"队列已停止，task {training_id} 不再入队")
            return
        if training_id in self._inflight:
            logger.info(f"task {training_id} 已在 inflight，跳过重复入队")
            return
        self._inflight.add(training_id)
        await self._queue.put(training_id)
        logger.info(
            f"task {training_id} 已入队 (queue_size={self._queue.qsize()}, "
            f"workers={self.num_workers})"
        )

    async def _worker_loop(self, worker_id: int) -> None:
        """worker 循环：从队列取任务 -> 检查是否还需要 -> 执行 -> 清理。"""
        logger.info(f"ai-worker-{worker_id} 启动")
        while not self._stopped:
            try:
                training_id = await self._queue.get()
            except asyncio.CancelledError:
                logger.info(f"ai-worker-{worker_id} 被取消")
                break

            try:
                if not await self._should_process(training_id):
                    logger.info(
                        f"ai-worker-{worker_id} 跳过 task {training_id} "
                        "(记录不存在或已被取消)"
                    )
                    continue

                # 真正干活
                logger.info(f"ai-worker-{worker_id} 开始处理 task {training_id}")
                try:
                    await process_admin_video_analysis(training_id)
                    logger.info(f"ai-worker-{worker_id} 完成 task {training_id}")
                except Exception as e:
                    logger.exception(
                        f"ai-worker-{worker_id} 处理 task {training_id} 失败: {e}"
                    )
            except asyncio.CancelledError:
                logger.info(f"ai-worker-{worker_id} 被取消（处理中）")
                break
            except Exception as e:
                logger.exception(f"ai-worker-{worker_id} 顶层循环出错: {e}")
            finally:
                self._inflight.discard(training_id)
                self._queue.task_done()

        logger.info(f"ai-worker-{worker_id} 退出")

    async def _should_process(self, training_id: int) -> bool:
        """Worker 处理前再 check 一次：record 是否还存在 + 不是 cancelled。"""
        try:
            async with async_session_maker() as s:
                row = (
                    await s.execute(
                        text("SELECT status FROM training_records WHERE id=:i"),
                        {"i": training_id},
                    )
                ).first()
        except Exception as e:
            # DB 出错时保守地跳过，宁可漏处理也不要在损坏的 session 上死磕
            logger.exception(f"check task {training_id} 状态失败: {e}")
            return False

        if row is None:
            return False
        return row[0] != "cancelled"

    async def stop(self) -> None:
        """优雅停止：先标记 stopped，再 cancel 所有 worker。"""
        if not self._started:
            return
        logger.info("AITaskQueue 正在停止 ...")
        self._stopped = True
        for w in self._workers:
            w.cancel()
        # 等所有 worker 退出
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        self._inflight.clear()
        self._started = False
        logger.info("AITaskQueue 已停止")

    def status(self) -> dict:
        """健康检查用：返回当前队列/worker 状态。"""
        return {
            "started": self._started,
            "stopped": self._stopped,
            "workers": len(self._workers),
            "queue_size": self._queue.qsize(),
            "inflight": list(self._inflight),
        }


# 模块级单例
ai_task_queue = AITaskQueue(num_workers=2)


# 局部 import 避免循环引用（admin_videos 也会 import 这个模块）
async def process_admin_video_analysis(training_id: int):
    """从 admin_videos.py 复用的处理函数（懒加载）。"""
    from app.api.admin_videos import process_admin_video_analysis as _impl

    return await _impl(training_id)
