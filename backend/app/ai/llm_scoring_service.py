"""LLM 评分服务

通过调用外部大模型 API（兼容 OpenAI 格式），基于预定义的灭火器操作规程评分规则，
对训练视频分析结果进行 AI 评分并生成改进建议。
"""
import json
import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# ============================================================
# 系统提示词（灭火器操作 6 步标准评分规则）
# ============================================================
SCORING_SYSTEM_PROMPT = """你是专业的消防安全培训评估专家，拥有丰富的灭火器操作培训和考核经验。

你的任务是：根据学员训练数据（视频分析结果），严格按照下面的【评分规则】对学员的灭火器操作进行评分，并给出针对性的改进建议。

══════════════════════════════════════════
【灭火器操作标准规程与评分规则】
══════════════════════════════════════════

▶ 步骤1：准备阶段（权重 15%）
  标准要求：发现火情后，迅速判断火源位置，以正确姿势站立准备，目视火源方向。
  - 优秀（90-100分）：立即作出反应，站姿端正，目视前方，无犹豫
  - 良好（75-89分）：反应较快，站姿基本正确
  - 合格（60-74分）：能完成准备，但反应迟缓或姿势略差
  - 不合格（0-59分）：反应明显迟缓，站姿不规范

▶ 步骤2：提灭火器（权重 20%）
  标准要求：双手或单手握住灭火器筒体把手，平稳提起，保持灭火器竖直。
  - 优秀（90-100分）：握持方式正确，动作流畅，灭火器始终竖直
  - 良好（75-89分）：握法基本正确，灭火器基本竖直
  - 合格（60-74分）：能提起灭火器，但姿势不够规范或有倾斜
  - 不合格（0-59分）：握持方式错误，或灭火器明显倾斜

▶ 步骤3：拔保险销（权重 15%）
  标准要求：一手持灭火器，另一手食指插入保险环，用力将保险销笔直拔出。
  - 优秀（90-100分）：动作准确，一次拔出，拔销方向正确
  - 良好（75-89分）：操作正确，一次完成，稍有停顿
  - 合格（60-74分）：能拔出保险销，但费力或多次尝试
  - 不合格（0-59分）：未能正确拔出，或操作方式明显错误

▶ 步骤4：握喷管（权重 15%）
  标准要求：一手握住喷管距喷嘴约 20-30 cm 处（避免冻伤），对准火源方向。
  - 优秀（90-100分）：握持位置正确，喷嘴指向准确，手腕稳定
  - 良好（75-89分）：握持基本正确，方向大致准确
  - 合格（60-74分）：能握喷管，但握持位置或方向有偏差
  - 不合格（0-59分）：握持方式错误（如握近喷嘴）或方向明显偏差

▶ 步骤5：瞄准火源（权重 20%）
  标准要求：双脚分开与肩同宽，重心略低，手臂自然伸展，喷嘴对准火焰根部，与火源保持 3-5 米安全距离。
  - 优秀（90-100分）：站姿稳定，瞄准精确（指向火焰根部），距离合适
  - 良好（75-89分）：瞄准基本正确，姿态较稳
  - 合格（60-74分）：能对准大致方向，但姿态或距离有明显偏差
  - 不合格（0-59分）：未对准火焰根部，或距离不当，存在安全隐患

▶ 步骤6：压把手（权重 15%）
  标准要求：用力均匀向下压灭火器把手，对准火焰根部来回扫射，直至火焰完全熄灭，手指不要覆盖喷嘴。
  - 优秀（90-100分）：压力均匀，扫射动作规范，持续有效操作至灭火
  - 良好（75-89分）：操作基本正确，扫射动作较规范
  - 合格（60-74分）：能压下把手，但扫射不规范或持续时间不足
  - 不合格（0-59分）：操作方式错误，或未能进行有效扫射

══════════════════════════════════════════
【整体评分维度权重】
══════════════════════════════════════════
1. 动作完整性（40%）：6个步骤是否全部完成，各步骤执行质量
2. 姿态规范性（40%）：手臂角度、身体姿态是否符合标准
3. 操作时效性（20%）：总操作时间是否在合理范围（60-150秒）

【时效性评分参考】
- 60-90秒：优秀（反应迅速且动作规范）
- 90-120秒：良好（节奏适中）
- 120-150秒：合格（偏慢但完成操作）
- <60秒：需关注（过快可能遗漏步骤）
- >150秒：不合格（操作时间过长）

【总分计算】
total_score = 动作完整性得分 × 0.4 + 姿态规范性得分 × 0.4 + 操作时效性得分 × 0.2

【等级划分】
- 优秀：≥ 90分
- 良好：80-89分
- 合格：60-79分
- 不合格：< 60分

══════════════════════════════════════════
【输出格式要求】
══════════════════════════════════════════
请严格按照以下 JSON 格式输出，不要输出任何 JSON 以外的内容，不要添加 markdown 代码块标记：

{
  "total_score": <0-100的浮点数，保留一位小数>,
  "performance_level": "<excellent|good|pass|fail 之一>",
  "dimension_scores": {
    "action_completeness": {
      "score": <0-100的整数>,
      "weight": 0.4,
      "comment": "<30字以内的维度评语>"
    },
    "pose_standardization": {
      "score": <0-100的整数>,
      "weight": 0.4,
      "comment": "<30字以内的维度评语>"
    },
    "timeliness": {
      "score": <0-100的整数>,
      "weight": 0.2,
      "comment": "<30字以内的维度评语>"
    }
  },
  "step_scores": {
    "step1": {"step_name": "准备阶段", "score": <0-100的整数>, "is_correct": <true|false>, "feedback": "<20字以内的具体反馈>", "weight": 0.15},
    "step2": {"step_name": "提灭火器", "score": <0-100的整数>, "is_correct": <true|false>, "feedback": "<20字以内的具体反馈>", "weight": 0.20},
    "step3": {"step_name": "拔保险销", "score": <0-100的整数>, "is_correct": <true|false>, "feedback": "<20字以内的具体反馈>", "weight": 0.15},
    "step4": {"step_name": "握喷管", "score": <0-100的整数>, "is_correct": <true|false>, "feedback": "<20字以内的具体反馈>", "weight": 0.15},
    "step5": {"step_name": "瞄准火源", "score": <0-100的整数>, "is_correct": <true|false>, "feedback": "<20字以内的具体反馈>", "weight": 0.20},
    "step6": {"step_name": "压把手", "score": <0-100的整数>, "is_correct": <true|false>, "feedback": "<20字以内的具体反馈>", "weight": 0.15}
  },
  "feedback": "<100字以内的整体评价，指出主要优点和不足>",
  "suggestions": [
    "<针对性改进建议1，30字以内>",
    "<针对性改进建议2，30字以内>",
    "<针对性改进建议3，30字以内>"
  ]
}"""


class LLMScoringService:
    """大模型评分服务

    通过外部大模型 API（兼容 OpenAI 格式）对训练数据进行评分。
    支持 OpenAI、DeepSeek、Qwen（通义千问）、Zhipu AI（智谱）等兼容接口。
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        timeout: float = 60.0,
    ):
        """初始化 LLM 评分服务

        Args:
            api_key: API 密钥
            base_url: API 基础 URL（OpenAI 兼容格式）
                - OpenAI:  https://api.openai.com/v1
                - DeepSeek: https://api.deepseek.com/v1
                - Qwen:     https://dashscope.aliyuncs.com/compatible-mode/v1
                - Zhipu:    https://open.bigmodel.cn/api/paas/v4
            model: 模型名称
                - OpenAI:   gpt-4o-mini / gpt-4o
                - DeepSeek: deepseek-chat
                - Qwen:     qwen-turbo / qwen-plus / qwen-max
                - Zhipu:    glm-4-flash / glm-4
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def score_training(
        self,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """基于 AI 视频分析结果，调用大模型进行评分

        Args:
            analysis_result: TrainingInferenceService.analyze_video() 返回的分析结果

        Returns:
            评分结果字典，包含：
            - total_score: 总分
            - performance_level: 等级
            - dimension_scores: 三维度分数
            - step_scores: 6步骤分数
            - feedback: 整体评价
            - suggestions: 改进建议列表

        Raises:
            RuntimeError: 调用 LLM API 失败
        """
        # 构建用户提示词（将分析数据格式化为可读文本）
        user_prompt = self._build_user_prompt(analysis_result)

        # 调用 LLM API
        raw_response = await self._call_llm(user_prompt)

        # 解析并验证 JSON 响应
        scoring_result = self._parse_llm_response(raw_response)

        return scoring_result

    def _build_user_prompt(self, analysis_result: Dict[str, Any]) -> str:
        """将视频分析结果格式化为 LLM 可理解的描述文本

        Args:
            analysis_result: 视频分析结果

        Returns:
            格式化的用户提示词
        """
        duration = analysis_result.get("video_duration", 0)
        total_detections = analysis_result.get("total_detections", 0)
        pose_frame_count = analysis_result.get("pose_frame_count", 0)
        processed_frames = analysis_result.get("processed_frames", 0)
        step_sequence = analysis_result.get("step_sequence", [])
        step_times = analysis_result.get("step_times", {})
        all_pose_results = analysis_result.get("all_pose_results", [])

        # 计算姿态角度统计
        pose_stats = self._compute_pose_stats(all_pose_results)

        # 步骤完成情况
        completed_steps = len([s for s in step_sequence if s.get("is_completed", False)])
        step_detail_lines = []
        seen_steps = set()
        for step in step_sequence:
            step_name = step.get("step_name", "")
            if step_name in seen_steps:
                continue
            seen_steps.add(step_name)
            step_idx = step.get("step_index", 0)
            step_key = f"step{step_idx}"
            duration_val = step_times.get(step_key, 0)
            is_done = step.get("is_completed", False)
            step_detail_lines.append(
                f"  - {step_name}：{'已完成' if is_done else '未完成'}，"
                f"耗时 {float(duration_val):.1f} 秒"
            )

        step_detail_text = "\n".join(step_detail_lines) if step_detail_lines else "  - 未检测到有效步骤"

        # 姿态分析文本
        pose_lines = []
        if pose_stats:
            if "right_arm" in pose_stats:
                pose_lines.append(
                    f"  - 右臂角度：平均 {pose_stats['right_arm']['mean']:.1f}°，"
                    f"范围 {pose_stats['right_arm']['min']:.1f}°-{pose_stats['right_arm']['max']:.1f}°"
                    f"（标准范围：提灭火器时约 90°，瞄准时约 150-180°）"
                )
            if "left_arm" in pose_stats:
                pose_lines.append(
                    f"  - 左臂角度：平均 {pose_stats['left_arm']['mean']:.1f}°，"
                    f"范围 {pose_stats['left_arm']['min']:.1f}°-{pose_stats['left_arm']['max']:.1f}°"
                )
            if "body" in pose_stats or "torso" in pose_stats:
                key = "body" if "body" in pose_stats else "torso"
                pose_lines.append(
                    f"  - 身体姿态角度：平均 {pose_stats[key]['mean']:.1f}°"
                    f"（标准直立约 80-100°）"
                )
            if "right_knee" in pose_stats:
                pose_lines.append(
                    f"  - 右膝角度：平均 {pose_stats['right_knee']['mean']:.1f}°"
                )
        pose_text = "\n".join(pose_lines) if pose_lines else "  - 姿态数据不足，无法详细分析"

        prompt = f"""请根据以下学员灭火器操作训练数据进行评分：

【基本信息】
- 视频总时长：{duration:.1f} 秒
- 检测到的目标总数：{total_detections} 个
- 姿态分析帧数：{pose_frame_count} 帧（共处理 {processed_frames} 帧）
- 完成步骤数：{completed_steps} / 6 步

【步骤完成详情】
{step_detail_text}

【姿态分析数据】
{pose_text}

【时效性分析】
- 总操作时长：{duration:.1f} 秒
- 标准时长范围：60-150 秒
- 评价：{'操作过快，可能遗漏步骤' if duration < 60 else ('操作时间合理' if duration <= 150 else '操作时间过长，需加强熟练度')}

请严格按照要求的 JSON 格式输出评分结果，不要输出任何额外内容。"""

        return prompt

    def _compute_pose_stats(
        self,
        all_pose_results: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """计算姿态角度的统计信息（均值、最小值、最大值）

        Args:
            all_pose_results: 所有帧的姿态分析结果

        Returns:
            各角度的统计信息字典
        """
        if not all_pose_results:
            return {}

        angle_data: Dict[str, List[float]] = {}
        for pose in all_pose_results:
            angles = pose.get("angles", {})
            for angle_name, angle_value in angles.items():
                if isinstance(angle_value, (int, float)):
                    angle_data.setdefault(angle_name, []).append(float(angle_value))

        stats = {}
        for angle_name, values in angle_data.items():
            if values:
                stats[angle_name] = {
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                }
        return stats

    async def _call_llm(self, user_prompt: str) -> str:
        """调用 LLM API（OpenAI Chat Completions 格式）

        Args:
            user_prompt: 用户消息内容

        Returns:
            模型的回复文本

        Raises:
            RuntimeError: API 调用失败
        """
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
            "temperature": 0.2,  # 低温度，确保输出稳定
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
        """解析 LLM 返回的 JSON 评分结果，并做容错处理

        Args:
            raw_response: LLM 返回的原始文本

        Returns:
            解析后的评分结果字典

        Raises:
            RuntimeError: JSON 解析失败
        """
        # 去除可能的 markdown 代码块标记
        text = raw_response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # 去掉第一行（```json 或 ```）和最后一行（```）
            text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        text = text.strip()

        try:
            result = json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"LLM 响应 JSON 解析失败：{e}\n原始内容：{raw_response[:500]}")
            raise RuntimeError(f"LLM 返回格式错误，无法解析评分结果：{str(e)}")

        # 验证必要字段
        required_fields = ["total_score", "performance_level", "step_scores", "feedback", "suggestions"]
        for field in required_fields:
            if field not in result:
                raise RuntimeError(f"LLM 返回结果缺少必要字段：{field}")

        # 确保数值类型正确
        result["total_score"] = float(result["total_score"])

        # 确保 step_scores 中每个步骤都有 is_correct 字段
        step_scores = result.get("step_scores", {})
        for step_key, step_data in step_scores.items():
            if isinstance(step_data, dict):
                score = float(step_data.get("score", 0))
                step_data["score"] = score
                if "is_correct" not in step_data:
                    step_data["is_correct"] = score >= 60

        # 确保 suggestions 是列表
        if not isinstance(result.get("suggestions"), list):
            result["suggestions"] = [str(result.get("suggestions", ""))]

        return result

    @classmethod
    def from_settings(cls) -> Optional["LLMScoringService"]:
        """从应用配置创建实例（若未配置 API Key 则返回 None）

        Returns:
            LLMScoringService 实例，或 None（未配置时）
        """
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
