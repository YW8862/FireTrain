"""LLM 评分服务。"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.ai.fire_extinguisher_standard import DIMENSION_WEIGHTS, STEP_DEFINITIONS, get_performance_level

logger = logging.getLogger(__name__)


def _build_scoring_system_prompt() -> str:
    step_descriptions = []
    for step in STEP_DEFINITIONS:
        step_descriptions.append(
            f"▶ {step['key']} {step['name']}（权重 {int(step['weight'] * 100)}%）："
            f"{'；'.join(step['key_points'])}"
        )

    return f"""你是专业的消防实操评估教官，需要根据结构化视频分析摘要对学员的灭火器操作进行评分。

请严格依据输入证据评分，不要臆造视频中不存在的画面细节。你会收到：
1. 视频基础摘要
2. 检测与姿态统计
3. 每个步骤的完成情况、置信度、时长、问题点
4. 规则引擎给出的基线分
5. （可能存在）"证据强度提示"：当状态机只识别到少数步骤但底层证据充足时，
   请不要机械按步骤数扣分，而是结合灭火器出现帧数、姿态帧数、手臂动作等
   帧级证据合理推断每个步骤是否隐含完成，给出公允评分。

统一训练步骤如下：
{chr(10).join(step_descriptions)}

评分维度与权重：
- 动作完整性：{DIMENSION_WEIGHTS['action_completeness']}
- 姿态规范性：{DIMENSION_WEIGHTS['pose_standardization']}
- 操作时效性：{DIMENSION_WEIGHTS['timeliness']}

评分原则（宽松模式）：
- 只要有灭火器或姿态证据，即使状态机未识别出完整步骤，也应给出 50-80 分
- 只要视频中有操作动作（灭火器出现），每个步骤至少给 60-70 分
- 有完整步骤链且动作基本正确应给 80-90 分
- 步骤完整且动作非常规范给 90-100 分
- 重点考察：是否完成动作，而非动作是否完美

请输出严格 JSON，不要输出 JSON 以外的内容：
{{
  "total_score": <0-100 的浮点数，保留 1 位小数>,
  "performance_level": "<excellent|good|pass|fail>",
  "dimension_scores": {{
    "action_completeness": {{"score": <0-100>, "weight": {DIMENSION_WEIGHTS['action_completeness']}, "comment": "<30字以内>"}},
    "pose_standardization": {{"score": <0-100>, "weight": {DIMENSION_WEIGHTS['pose_standardization']}, "comment": "<30字以内>"}},
    "timeliness": {{"score": <0-100>, "weight": {DIMENSION_WEIGHTS['timeliness']}, "comment": "<30字以内>"}}
  }},
  "step_scores": {{
    "step1": {{"step_name": "准备阶段", "score": <0-100>, "is_correct": <true|false>, "feedback": "<20字以内>", "weight": 0.15}},
    "step2": {{"step_name": "提灭火器", "score": <0-100>, "is_correct": <true|false>, "feedback": "<20字以内>", "weight": 0.20}},
    "step3": {{"step_name": "拔保险销", "score": <0-100>, "is_correct": <true|false>, "feedback": "<20字以内>", "weight": 0.15}},
    "step4": {{"step_name": "握喷管", "score": <0-100>, "is_correct": <true|false>, "feedback": "<20字以内>", "weight": 0.15}},
    "step5": {{"step_name": "瞄准火源", "score": <0-100>, "is_correct": <true|false>, "feedback": "<20字以内>", "weight": 0.20}},
    "step6": {{"step_name": "压把手", "score": <0-100>, "is_correct": <true|false>, "feedback": "<20字以内>", "weight": 0.15}}
  }},
  "feedback": "<100字以内整体评价>",
  "suggestions": ["<建议1>", "<建议2>", "<建议3>"]
}}"""


SCORING_SYSTEM_PROMPT = _build_scoring_system_prompt()


class LLMScoringService:
    """通过外部大模型 API 对训练数据进行评分。"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        timeout: float = 60.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def score_training(
        self,
        analysis_result: Dict[str, Any],
        baseline_score: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        user_prompt = self._build_user_prompt(analysis_result, baseline_score)
        raw_response = await self._call_llm(user_prompt)
        return self._parse_llm_response(raw_response)

    def _build_user_prompt(
        self,
        analysis_result: Dict[str, Any],
        baseline_score: Optional[Dict[str, Any]] = None,
    ) -> str:
        summary = analysis_result.get("analysis_summary", analysis_result)
        detection_stats = summary.get("detection_stats", {})
        pose_stats_summary = summary.get("pose_stats_summary", {})
        step_feature_summary = summary.get("step_feature_summary", {})

        # 证据强度评估：帮助 LLM 判断是否应走"弱证据推断"路径
        completed_count = summary.get("completed_steps_count", 0)
        processed_frames = max(summary.get("processed_frames", 0), 1)
        ext_frames = detection_stats.get("fire_extinguisher", {}).get("frame_count", 0)
        pose_frames = summary.get("pose_frame_count", 0)
        ext_ratio = ext_frames / processed_frames
        pose_ratio = pose_frames / processed_frames
        evidence_hint_lines: List[str] = []
        if completed_count < 4 and (ext_ratio > 0.2 or pose_ratio > 0.5):
            evidence_hint_lines.append(
                f"⚠️ 状态机仅识别出 {completed_count}/6 个完整步骤，"
                f"但灭火器出现 {ext_frames}/{processed_frames} 帧（{ext_ratio:.0%}），"
                f"人体姿态 {pose_frames}/{processed_frames} 帧（{pose_ratio:.0%}）。"
            )
            evidence_hint_lines.append(
                "这通常意味着视频中动作连贯但状态机分段保守（例如教学/示范视频、镜头切换频繁）。"
                "请结合帧级证据推断隐含完成的步骤，给出合理推断分数（建议总分 40-70 分区间），"
                "不要因步骤未被状态机显式完成就给 0 分。"
            )
        elif completed_count == 0 and ext_frames == 0 and pose_frames == 0:
            evidence_hint_lines.append(
                "⚠️ 视频中几乎没有有效证据（无灭火器、无姿态），可给极低分数或 0 分。"
            )

        detection_lines = [
            f"- {class_name}: frame_count={stats.get('frame_count', 0)}, "
            f"detection_count={stats.get('detection_count', 0)}, "
            f"average_confidence={stats.get('average_confidence', 0)}"
            for class_name, stats in detection_stats.items()
        ]

        pose_lines = [
            f"- {angle_name}: mean={stats.get('mean', 0)}, min={stats.get('min', 0)}, "
            f"max={stats.get('max', 0)}, stability={stats.get('stability', 0)}"
            for angle_name, stats in pose_stats_summary.items()
        ]

        step_lines = []
        for step in STEP_DEFINITIONS:
            step_data = step_feature_summary.get(step["key"], {})
            step_lines.append(
                f"- {step['name']}: completed={step_data.get('completed', False)}, "
                f"confidence={step_data.get('confidence', 0)}, duration={step_data.get('duration', 0)}, "
                f"pose_quality_score={step_data.get('pose_quality_score', 0)}, "
                f"extinguisher_presence_ratio={step_data.get('extinguisher_presence_ratio', 0)}, "
                f"detected_actions={step_data.get('detected_actions', [])}, "
                f"issues={step_data.get('issues', [])}"
            )

        baseline_text = (
            json.dumps(
                {
                    "total_score": baseline_score.get("total_score"),
                    "performance_level": baseline_score.get("performance_level"),
                    "dimension_scores": baseline_score.get("dimension_scores"),
                    "step_scores": baseline_score.get("step_scores"),
                },
                ensure_ascii=False,
                indent=2,
            )
            if baseline_score
            else "未提供规则基线分"
        )

        baseline_reminder = (
            "【重要】规则引擎基线分仅供参考，本规则引擎对姿态波动较敏感（稳定性 70° 以上会大幅扣分）。"
            "请基于视频证据进行独立评分，不要被基线分锚定——如果你认为实际动作更规范，请给出更合理的分数。"
            if baseline_score
            else ""
        )

        evidence_hint_block = (
            "【证据强度提示】\n" + "\n".join(evidence_hint_lines) + "\n"
            if evidence_hint_lines else ""
        )

        return f"""请根据以下灭火器训练摘要进行评分：

【基础摘要】
- video_duration={summary.get('video_duration', 0)}
- processed_frames={summary.get('processed_frames', 0)}
- pose_frame_count={summary.get('pose_frame_count', 0)}
- extinguisher_detected={summary.get('extinguisher_detected', False)}
- person_detected={summary.get('person_detected', False)}
- completed_steps_count={summary.get('completed_steps_count', 0)}
- completed_steps={summary.get('completed_steps', [])}
- missing_steps={summary.get('missing_steps', [])}

【检测统计】
{chr(10).join(detection_lines) if detection_lines else '- 无检测数据'}

【姿态统计】
{chr(10).join(pose_lines) if pose_lines else '- 无姿态统计'}

【步骤级证据】
{chr(10).join(step_lines)}

【规则引擎基线分】
{baseline_text}

{baseline_reminder}

{evidence_hint_block}请基于证据输出最终 JSON 评分结果。"""

    async def _call_llm(self, user_prompt: str) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SCORING_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 1500,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                logger.info(f"LLM 评分完成，模型：{self.model}，tokens 使用：{data.get('usage', {})}")
                return content
        except httpx.TimeoutException:
            raise RuntimeError(f"LLM API 请求超时（{self.timeout}秒），请检查网络连接")
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.json().get("error", {}).get("message", "")
            except Exception:
                pass
            raise RuntimeError(f"LLM API 请求失败（HTTP {e.response.status_code}）：{error_detail}")
        except Exception as e:
            raise RuntimeError(f"LLM API 调用异常：{str(e)}")

    def _parse_llm_response(self, raw_response: str) -> Dict[str, Any]:
        text = raw_response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        text = text.strip()

        try:
            result = json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"LLM 响应 JSON 解析失败：{e}\n原始内容：{raw_response[:500]}")
            raise RuntimeError(f"LLM 返回格式错误，无法解析评分结果：{str(e)}")

        required_fields = ["total_score", "performance_level", "step_scores", "feedback", "suggestions"]
        for field in required_fields:
            if field not in result:
                raise RuntimeError(f"LLM 返回结果缺少必要字段：{field}")

        result["total_score"] = float(result["total_score"])
        performance = self._normalize_performance_level(result.get("performance_level"))
        result["performance_level"] = performance["code"]
        result["performance_label"] = performance["label"]

        step_scores = result.get("step_scores", {})
        for step_key, step_data in step_scores.items():
            if isinstance(step_data, dict):
                score = float(step_data.get("score", 0))
                step_data["score"] = score
                if "is_correct" not in step_data:
                    step_data["is_correct"] = score >= 60

        if not isinstance(result.get("suggestions"), list):
            result["suggestions"] = [str(result.get("suggestions", ""))]

        return result

    def _normalize_performance_level(self, raw_level: Any) -> Dict[str, Any]:
        mapping = {
            "excellent": "excellent",
            "good": "good",
            "pass": "pass",
            "fail": "fail",
            "优秀": "excellent",
            "良好": "good",
            "合格": "pass",
            "不合格": "fail",
            "待改进": "fail",
        }
        normalized_code = mapping.get(str(raw_level or "").strip().lower(), None)
        if normalized_code is None:
            return get_performance_level(0)

        threshold_map = {
            "excellent": 95,
            "good": 85,
            "pass": 70,
            "fail": 0,
        }
        return get_performance_level(threshold_map[normalized_code])

    @classmethod
    def from_settings(cls) -> Optional["LLMScoringService"]:
        from app.core.config import settings

        if not settings.LLM_API_KEY:
            logger.warning("未配置 LLM_API_KEY，LLM 评分功能不可用")
            return None

        return cls(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            model=settings.LLM_MODEL,
            timeout=settings.LLM_TIMEOUT,
        )
