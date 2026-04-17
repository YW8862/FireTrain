"""训练分析进度追踪（进程内，线程安全）。

分析流水线是异步后台任务，状态库字段只有 ``processing`` / ``done`` / ``failed``
三态，无法反映"到底卡在哪一步"。这里提供一个进程内的轻量级进度池，把阶段、
整体进度百分比和阶段提示文案上报给 API 层用于前端展示。

设计要点：
- 纯进程内字典，backend 重启后会丢失，这是刻意的：重启后异步任务本身也会丢失
- 使用 ``threading.Lock`` 加锁，支持 threadpool 内的 YOLO 循环回调并发更新
- 终态（done / failed）在读取后保留一段时间再清理，避免前端最后一次轮询丢失结果
"""

from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


# 阶段 → 中文标签（UI 直接展示）
STAGE_LABELS: Dict[str, str] = {
    "queued": "任务已提交，等待分析",
    "loading_model": "加载 AI 模型（YOLO / MediaPipe）",
    "video_analysis": "视频帧分析中（目标检测 + 姿态识别）",
    "rule_scoring": "标准规则评分计算中",
    "llm_scoring": "大模型综合点评生成中",
    "saving": "结果保存中",
    "done": "分析完成",
    "failed": "分析失败",
}


# 每个阶段对应的整体进度百分比基准（不含阶段内部进度）
STAGE_BASE_PROGRESS: Dict[str, float] = {
    "queued": 0.0,
    "loading_model": 5.0,
    "video_analysis": 10.0,  # 视频分析占 10% - 70%（内部按帧线性推进）
    "rule_scoring": 75.0,
    "llm_scoring": 85.0,
    "saving": 95.0,
    "done": 100.0,
    "failed": 100.0,
}

# video_analysis 阶段在整体进度中占据的区间宽度（%）
VIDEO_ANALYSIS_SPAN = 60.0


@dataclass
class ProgressSnapshot:
    """对外返回的进度快照，字段与 API Schema 对齐。"""

    stage: str
    stage_label: str
    progress: float
    stage_message: Optional[str] = None
    updated_at: float = field(default_factory=time.time)


class AnalysisProgressTracker:
    """线程安全的进程内进度追踪单例。"""

    # 终态保留时间（秒）。前端轮询间隔是 3s，这里预留足够余量。
    _TERMINAL_RETENTION_SECONDS = 120.0

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: Dict[int, ProgressSnapshot] = {}

    def set_stage(
        self,
        training_id: int,
        stage: str,
        message: Optional[str] = None,
        progress_override: Optional[float] = None,
    ) -> None:
        """切换阶段，自动写入阶段基准进度。"""
        base = STAGE_BASE_PROGRESS.get(stage, 0.0)
        progress = progress_override if progress_override is not None else base
        snapshot = ProgressSnapshot(
            stage=stage,
            stage_label=STAGE_LABELS.get(stage, stage),
            progress=round(max(0.0, min(progress, 100.0)), 1),
            stage_message=message,
        )
        with self._lock:
            self._store[training_id] = snapshot
            self._cleanup_locked()

    def update_video_analysis(
        self,
        training_id: int,
        processed_frames: int,
        total_frames: int,
    ) -> None:
        """在 video_analysis 阶段内按帧刷新进度。"""
        if total_frames <= 0:
            return
        ratio = max(0.0, min(processed_frames / total_frames, 1.0))
        overall = STAGE_BASE_PROGRESS["video_analysis"] + ratio * VIDEO_ANALYSIS_SPAN
        message = f"已处理 {processed_frames} / {total_frames} 帧"
        self.set_stage(
            training_id,
            "video_analysis",
            message=message,
            progress_override=overall,
        )

    def mark_done(self, training_id: int, message: Optional[str] = None) -> None:
        self.set_stage(training_id, "done", message=message, progress_override=100.0)

    def mark_failed(self, training_id: int, message: Optional[str] = None) -> None:
        self.set_stage(training_id, "failed", message=message, progress_override=100.0)

    def get(self, training_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            snapshot = self._store.get(training_id)
            if snapshot is None:
                return None
            return asdict(snapshot)

    def clear(self, training_id: int) -> None:
        with self._lock:
            self._store.pop(training_id, None)

    def _cleanup_locked(self) -> None:
        """清理过期终态条目（调用方需已持有锁）。"""
        if len(self._store) < 64:
            return
        now = time.time()
        stale = [
            tid
            for tid, snap in self._store.items()
            if snap.stage in ("done", "failed")
            and now - snap.updated_at > self._TERMINAL_RETENTION_SECONDS
        ]
        for tid in stale:
            self._store.pop(tid, None)


# 全局单例
progress_tracker = AnalysisProgressTracker()
