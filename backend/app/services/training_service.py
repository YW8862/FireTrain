"""训练服务层 - 处理训练相关的业务逻辑。"""

from __future__ import annotations

import os
import random
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from fastapi.concurrency import run_in_threadpool

from app.ai.fire_extinguisher_standard import STEP_DEFINITIONS, get_performance_level
from app.ai.llm_scoring_service import LLMScoringService
from app.core.config import settings
from app.models.training_record import TrainingRecord
from app.repositories.training_repository import TrainingRepository
from app.services.analysis_progress import progress_tracker


class TrainingService:
    """训练服务类。"""

    def __init__(self, training_repo: TrainingRepository):
        self.training_repo = training_repo

    async def start_training(self, user_id: int, request) -> TrainingRecord:
        training = TrainingRecord(
            user_id=user_id,
            training_type=self._normalize_training_type(request.training_type),
            status="created",
            duration_seconds=request.duration_seconds if hasattr(request, "duration_seconds") else None,
            started_at=datetime.utcnow(),
        )
        await self.training_repo.create(training)
        return training

    async def upload_video(self, training_id: int, video_path: str) -> Optional[TrainingRecord]:
        training = await self.training_repo.get_by_id(training_id)
        if not training:
            return None

        return await self.training_repo.update(
            training,
            {
                "video_path": video_path,
                "status": "processing",
            },
        )

    async def complete_training_with_ai_analysis(
        self,
        training_id: int,
        use_ai_scoring: bool = True,
    ) -> Optional[Dict]:
        training = await self.training_repo.get_by_id(training_id)
        if not training:
            return None

        if training.status not in ["created", "processing"]:
            raise ValueError(f"当前状态不能完成训练：{training.status}")
        if not training.video_path:
            raise ValueError("视频路径为空，无法完成训练")
        if not os.path.exists(training.video_path):
            raise ValueError("视频文件不存在，无法完成训练")

        # 先上报排队 / 加载模型阶段
        progress_tracker.set_stage(training_id, "queued")

        analysis_result: Optional[Dict] = None
        analysis_error_reason: Optional[str] = None
        from app.ai.training_inference_service import TrainingInferenceService

        progress_tracker.set_stage(training_id, "loading_model")
        inference_service = TrainingInferenceService(
            yolo_model_path=settings.YOLO_MODEL_PATH,
            yolo_conf_threshold=0.5,
            use_pose_analysis=True,
        )
        try:
            try:
                progress_tracker.set_stage(training_id, "video_analysis")

                def _on_frame_progress(processed: int, total: int) -> None:
                    progress_tracker.update_video_analysis(training_id, processed, total)

                analysis_result = await run_in_threadpool(
                    lambda: inference_service.analyze_video(
                        video_path=training.video_path,
                        training_type=self._normalize_training_type(training.training_type),
                        progress_callback=_on_frame_progress,
                    )
                )
            except Exception as exc:
                analysis_error_reason = f"视频分析失败：{exc}"
        finally:
            inference_service.close()

        if analysis_result:
            validation_result = self._validate_detection_result(
                analysis_result.get("analysis_summary", analysis_result)
            )
            if not validation_result["is_valid"]:
                progress_tracker.set_stage(
                    training_id,
                    "saving",
                    message=f"关键步骤未识别完整：{validation_result['reason']}",
                )
                scoring_result = await self._generate_zero_score_result(
                    training_type=training.training_type,
                    reason=validation_result["reason"],
                    analysis_result=analysis_result,
                )
            else:
                progress_tracker.set_stage(training_id, "rule_scoring")
                # 是否走 LLM 取决于调用方参数以及 LLM 服务配置
                if use_ai_scoring and LLMScoringService.from_settings() is not None:
                    scoring_result = await self._score_with_llm_or_fallback(
                        analysis_result=analysis_result,
                        allow_llm=True,
                        training_id=training_id,
                    )
                else:
                    scoring_result = await self._score_with_llm_or_fallback(
                        analysis_result=analysis_result,
                        allow_llm=False,
                        training_id=training_id,
                    )
        else:
            progress_tracker.set_stage(
                training_id,
                "saving",
                message=analysis_error_reason or "未获取到有效视频分析结果",
            )
            scoring_result = await self._generate_zero_score_result(
                training_type=training.training_type,
                reason=analysis_error_reason or "未获取到有效视频分析结果",
                analysis_result=analysis_result,
            )

        progress_tracker.set_stage(training_id, "saving")

        completed_at = datetime.utcnow()
        duration_seconds = training.duration_seconds
        if training.started_at:
            duration_seconds = Decimal(str(round((completed_at - training.started_at).total_seconds(), 2)))

        persisted_step_scores = self._build_persisted_step_scores(scoring_result)
        await self.training_repo.update(
            training,
            {
                "status": "done",
                "total_score": Decimal(str(scoring_result["total_score"])),
                "step_scores": persisted_step_scores,
                "feedback": scoring_result["feedback"],
                "completed_at": completed_at,
                "duration_seconds": duration_seconds,
            },
        )

        progress_tracker.mark_done(training_id)

        return {
            "status": "done",
            "total_score": float(scoring_result["total_score"]),
            "feedback": scoring_result["feedback"],
            "used_ai_scoring": scoring_result.get("score_source") in {"rule", "llm"},
            "scoring_result": scoring_result,
        }

    def _normalize_training_type(self, training_type: str) -> str:
        if training_type in {"extinguisher", "extinguisher_use"}:
            return "fire_extinguisher"
        return training_type

    def _validate_detection_result(self, analysis_summary: Dict) -> Dict[str, str | bool]:
        """判断分析结果是否可评分。

        仅在"完全无可用信号"时拒绝评分。只要检测到灭火器或人体姿态，
        就进入评分流程（规则引擎 + 可选 LLM），由评分层按证据强度给分，
        不再因步骤数量不足一刀切 0 分。
        """
        validity_checks = analysis_summary.get("validity_checks", {})
        supports_extinguisher_detection = analysis_summary.get("supports_extinguisher_detection", True)
        has_pose = bool(validity_checks.get("has_pose"))
        has_extinguisher = bool(validity_checks.get("has_extinguisher"))

        if not validity_checks and analysis_summary.get("total_detections", 0) > 0:
            return {"is_valid": True, "reason": ""}

        # 同时没有姿态和灭火器 → 确实没证据，给 0 分
        if not has_pose and (supports_extinguisher_detection and not has_extinguisher):
            return {"is_valid": False, "reason": "视频中未检测到人体姿态和灭火器，无有效证据"}
        # 视频过短（< 8s）：无法形成任何有效时序
        if float(analysis_summary.get("video_duration", 0)) < 8:
            return {"is_valid": False, "reason": "视频时长过短（不足 8 秒），无法完成评估"}
        # 其余情况一律放行，由规则引擎和 LLM 基于证据强度给分
        return {"is_valid": True, "reason": ""}

    async def _generate_zero_score_result(
        self,
        training_type: str,
        reason: str,
        analysis_result: Optional[Dict] = None,
    ) -> Dict:
        step_scores = {}
        for step in STEP_DEFINITIONS:
            step_scores[step["key"]] = {
                "step_name": step["name"],
                "score": 0.0,
                "is_correct": False,
                "feedback": reason,
                "weight": step["weight"],
            }

        return {
            "total_score": 0.0,
            "performance_level": "fail",
            "performance_label": "待改进",
            "dimension_scores": {
                "action_completeness": {"score": 0.0, "weight": 0.4, "comment": "关键步骤未完整识别"},
                "pose_standardization": {"score": 0.0, "weight": 0.4, "comment": "姿态证据不足"},
                "timeliness": {"score": 0.0, "weight": 0.2, "comment": "无法形成有效时序"},
            },
            "step_scores": step_scores,
            "feedback": f"本次训练无法形成有效评分：{reason}",
            "suggestions": ["请确保灭火器和操作者完整入镜后重新训练", "先按标准步骤慢速演练，再进行完整录制"],
            "analysis_summary": (analysis_result or {}).get("analysis_summary"),
            "score_source": "zero",
        }

    async def _score_with_llm_or_fallback(
        self,
        analysis_result: Dict[str, Any],
        allow_llm: bool = True,
        training_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        from app.ai.rule_engine import RuleEngine
        from app.ai.training_inference_service import TrainingInferenceService

        summary = analysis_result.get("analysis_summary", analysis_result)
        if "step_feature_summary" not in summary and analysis_result.get("step_scores"):
            legacy_total = float(
                analysis_result.get("total_score")
                or self._estimate_total_from_legacy_steps(analysis_result.get("step_scores", {}))
            )
            performance = get_performance_level(legacy_total)
            return {
                "total_score": legacy_total,
                "performance_level": performance["code"],
                "performance_label": performance["label"],
                "dimension_scores": analysis_result.get("dimension_scores", {}),
                "step_scores": analysis_result.get("step_scores", {}),
                "feedback": analysis_result.get(
                    "feedback",
                    f"AI分析完成，检测到{analysis_result.get('total_detections', 0)}个目标",
                ),
                "suggestions": analysis_result.get("suggestions", []),
                "analysis_summary": {},
                "score_source": "rule",
            }
        rule_result = await RuleEngine().evaluate(summary)
        rule_result["suggestions"] = TrainingInferenceService.generate_real_suggestions(
            summary,
            rule_result.get("step_scores", {}),
        )

        rule_result["analysis_summary"] = analysis_result.get("analysis_summary", analysis_result)
        rule_result["score_source"] = "rule"

        if not allow_llm:
            return rule_result

        llm_service = LLMScoringService.from_settings()
        if not llm_service:
            return rule_result

        if training_id is not None:
            progress_tracker.set_stage(training_id, "llm_scoring")
        try:
            llm_result = await llm_service.score_training(analysis_result, baseline_score=rule_result)
            llm_result.setdefault("suggestions", rule_result.get("suggestions", []))
            llm_result.setdefault("dimension_scores", rule_result.get("dimension_scores", {}))
            llm_result.setdefault("feedback", rule_result.get("feedback", ""))
            llm_result["analysis_summary"] = analysis_result.get("analysis_summary", analysis_result)
            llm_result["score_source"] = "llm"
            return llm_result
        except Exception as exc:
            print(f"LLM 评分失败，回退规则评分：{exc}")
            return rule_result

    def _estimate_total_from_legacy_steps(self, step_scores: Dict[str, Any]) -> float:
        values = []
        for step_data in step_scores.values():
            if isinstance(step_data, dict):
                values.append(float(step_data.get("score", 0.0)))
            elif isinstance(step_data, (int, float)):
                values.append(float(step_data))
        return round(sum(values) / len(values), 1) if values else 0.0

    def _build_persisted_step_scores(self, scoring_result: Dict[str, Any]) -> Dict[str, Any]:
        step_scores = dict(scoring_result.get("step_scores", {}))
        step_scores["_suggestions"] = scoring_result.get("suggestions", [])
        step_scores["_dimension_scores"] = scoring_result.get("dimension_scores", {})
        step_scores["_performance_level"] = scoring_result.get("performance_level")
        step_scores["_score_source"] = scoring_result.get("score_source", "rule")
        step_scores["_analysis_summary"] = scoring_result.get("analysis_summary", {})
        # JSON 列使用默认 json.dumps 序列化，Decimal/numpy 标量会抛 TypeError，
        # 这里统一做一次 JSON-safe 清洗，避免一条 Decimal 把整条记录卡死在 processing
        return self._sanitize_json(step_scores)

    @classmethod
    def _sanitize_json(cls, value: Any) -> Any:
        """递归地把 Decimal / numpy 标量 / set 等转换成 JSON 可序列化的 Python 原生类型。"""
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, dict):
            return {str(k): cls._sanitize_json(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [cls._sanitize_json(item) for item in value]
        if isinstance(value, set):
            return [cls._sanitize_json(item) for item in value]
        if isinstance(value, datetime):
            return value.isoformat()
        # numpy 标量（如 float32/int64）有 .item() 可转成原生 Python 类型
        if hasattr(value, "item") and callable(getattr(value, "item", None)):
            try:
                return value.item()
            except Exception:
                return str(value)
        return value

    def _generate_mock_scoring(self) -> Dict:
        total_score = round(random.uniform(60, 85), 1)
        performance = get_performance_level(total_score)
        step_scores = {}
        for step in STEP_DEFINITIONS:
            step_score = round(random.uniform(60, 85), 1)
            step_scores[step["key"]] = {
                "step_name": step["name"],
                "score": step_score,
                "is_correct": step_score >= 60,
                "feedback": "未提供视频，使用降级评分",
                "weight": step["weight"],
            }

        return {
            "total_score": total_score,
            "performance_level": performance["code"],
            "performance_label": performance["label"],
            "dimension_scores": {
                "action_completeness": {"score": total_score, "weight": 0.4, "comment": "缺少视频证据，按降级规则评分"},
                "pose_standardization": {"score": max(total_score - 5, 60), "weight": 0.4, "comment": "姿态证据不足，采用保守估计"},
                "timeliness": {"score": max(total_score - 10, 55), "weight": 0.2, "comment": "无法验证完整时序"},
            },
            "step_scores": step_scores,
            "feedback": "未获取到有效视频分析结果，系统已使用降级评分。",
            "suggestions": ["请确保视频上传成功后再提交评分", "重新录制时保持灭火器和人体完整入镜"],
            "analysis_summary": {},
            "score_source": "mock",
        }

    async def get_user_training_history(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Tuple[List[TrainingRecord], int]:
        page_size = min(page_size, 50)
        return await self.training_repo.get_user_history(
            user_id=user_id,
            page=page,
            page_size=page_size,
            status=status,
            start_date=start_date,
            end_date=end_date,
        )