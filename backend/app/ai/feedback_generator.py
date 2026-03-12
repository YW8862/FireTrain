"""反馈生成器模块

根据评分结果生成可解释的反馈文本，指出问题和改进建议。
"""
from typing import Any, Dict, List, Optional
from app.ai.rule_engine import PerformanceLevel


class FeedbackGenerator:
    """反馈生成器
    
    生成可解释的反馈文本，包括：
    - 总体评价
    - 各步骤表现
    - 具体问题
    - 改进建议
    """
    
    # 反馈模板库
    FEEDBACK_TEMPLATES = {
        "excellent": [
            "表现优秀！动作规范流畅，继续保持",
            "非常出色！每个步骤都完成得很好",
            "优秀的表现！已经达到专业水准"
        ],
        "good": [
            "表现良好！基本掌握操作要领，注意细节改进",
            "不错的表现！主要步骤正确，部分细节需要优化",
            "良好的开始！继续练习可以达到更高水平"
        ],
        "pass": [
            "合格！但还有提升空间，建议多加练习",
            "通过！但动作规范性需要加强",
            "基本完成！建议观看标准视频学习"
        ],
        "fail": [
            "不合格！操作存在较大问题，请重新学习标准流程",
            "未完成！关键步骤有误，需要重点练习",
            "需要改进！建议从基础动作开始训练"
        ]
    }
    
    # 各步骤的反馈模板
    STEP_FEEDBACK_TEMPLATES = {
        "准备阶段": {
            "excellent": "准备充分，个人防护到位",
            "good": "准备工作基本到位",
            "pass": "准备不够充分，需要检查装备",
            "fail": "准备严重不足，存在安全隐患"
        },
        "提灭火器": {
            "excellent": "提拿姿势标准，用力正确",
            "good": "提拿基本正确",
            "pass": "提拿姿势需要改进",
            "fail": "提拿方式错误，可能造成伤害"
        },
        "拔保险销": {
            "excellent": "拔销动作干净利落",
            "good": "拔销基本成功",
            "pass": "拔销不够顺畅",
            "fail": "未能正确拔出保险销"
        },
        "握喷管": {
            "excellent": "握持稳固，方向正确",
            "good": "握持基本正确",
            "pass": "握持不够稳固",
            "fail": "握持方式错误"
        },
        "瞄准火源": {
            "excellent": "瞄准准确，距离适当",
            "good": "瞄准基本准确",
            "pass": "瞄准有偏差",
            "fail": "未能正确瞄准"
        },
        "压把手": {
            "excellent": "按压有力，喷射连续",
            "good": "按压基本正确",
            "pass": "按压力度不足",
            "fail": "未能正确按压把手"
        }
    }
    
    # 问题描述模板
    PROBLEM_DESCRIPTIONS = {
        "low_score": "{step_name}得分较低，仅为{score}分",
        "incorrect": "{step_name}操作不规范",
        "slow": "{step_name}用时过长",
        "fast": "{step_name}用时过短，可能不够规范",
        "angle_error": "{angle_name}角度偏差{deviation}度"
    }
    
    # 改进建议模板
    IMPROVEMENT_SUGGESTIONS = {
        "low_score": "重点练习【{step_name}】，观看标准动作视频",
        "incorrect": "纠正【{step_name}】的操作手法",
        "slow": "加快【{step_name}】的速度，但不要牺牲规范性",
        "fast": "放慢【{step_name}】，确保每个动作到位",
        "angle_error": "调整{angle_name}，标准角度为{standard_range}",
        "time_error": "控制总用时在{time_range}秒范围内"
    }
    
    def __init__(self):
        """初始化反馈生成器"""
        pass
    
    def generate_feedback(
        self,
        evaluation_result: Dict[str, Any],
        action_logs: Optional[List[Dict[str, Any]]] = None,
        pose_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成完整反馈
        
        Args:
            evaluation_result: 规则引擎评估结果
            action_logs: 动作日志列表
            pose_details: 姿态分析详情
            
        Returns:
            反馈结果字典
        """
        total_score = evaluation_result.get("total_score", 0)
        performance_level = evaluation_result.get("performance_level", "合格")
        
        # 1. 生成总体反馈
        overall_feedback = self._generate_overall_feedback(performance_level, total_score)
        
        # 2. 生成各步骤反馈
        step_feedbacks = self._generate_step_feedbacks(evaluation_result)
        
        # 3. 识别具体问题
        problems = self._identify_problems(evaluation_result, action_logs, pose_details)
        
        # 4. 生成改进建议
        suggestions = self._generate_suggestions(evaluation_result, problems)
        
        # 5. 生成详细报告
        detailed_report = self._generate_detailed_report(
            evaluation_result,
            problems,
            suggestions
        )
        
        return {
            "overall_feedback": overall_feedback,
            "step_feedbacks": step_feedbacks,
            "problems": problems,
            "suggestions": suggestions,
            "detailed_report": detailed_report,
            "total_score": total_score,
            "performance_level": performance_level
        }
    
    def _generate_overall_feedback(
        self,
        performance_level: str,
        total_score: float
    ) -> str:
        """
        生成总体反馈
        
        Args:
            performance_level: 表现等级
            total_score: 总分
            
        Returns:
            总体反馈文本
        """
        import random
        
        # 根据等级选择模板
        templates = self.FEEDBACK_TEMPLATES.get(performance_level.lower(), self.FEEDBACK_TEMPLATES["pass"])
        
        # 随机选择一个模板并添加分数信息
        base_feedback = random.choice(templates)
        
        return f"{base_feedback}（得分：{total_score:.1f}）"
    
    def _generate_step_feedbacks(
        self,
        evaluation_result: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        生成各步骤反馈
        
        Args:
            evaluation_result: 评估结果
            
        Returns:
            各步骤反馈字典
        """
        step_feedbacks = {}
        
        details = evaluation_result.get("details", {})
        completeness_details = details.get("completeness_details", {})
        standardization_details = details.get("standardization_details", {})
        
        # 为每个步骤生成反馈
        step_scores = evaluation_result.get("dimension_scores", {})
        pose_scores = standardization_details.get("average_angles", {})
        
        # 简化版本：使用预设模板
        for step_name in self.STEP_FEEDBACK_TEMPLATES.keys():
            # 根据等级生成反馈
            level = self._estimate_step_level(step_name, evaluation_result)
            template = self.STEP_FEEDBACK_TEMPLATES[step_name].get(
                level,
                self.STEP_FEEDBACK_TEMPLATES[step_name]["pass"]
            )
            step_feedbacks[step_name] = template
        
        return step_feedbacks
    
    def _estimate_step_level(
        self,
        step_name: str,
        evaluation_result: Dict[str, Any]
    ) -> str:
        """
        估算步骤的表现等级
        
        Args:
            step_name: 步骤名称
            evaluation_result: 评估结果
            
        Returns:
            表现等级
        """
        # 简化实现：使用总体等级
        overall_level = evaluation_result.get("performance_level", "合格")
        return overall_level.lower()
    
    def _identify_problems(
        self,
        evaluation_result: Dict[str, Any],
        action_logs: Optional[List[Dict[str, Any]]],
        pose_details: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        识别具体问题
        
        Args:
            evaluation_result: 评估结果
            action_logs: 动作日志
            pose_details: 姿态详情
            
        Returns:
            问题列表
        """
        problems = []
        
        # 检查各维度得分
        dimension_scores = evaluation_result.get("dimension_scores", {})
        
        # 动作完整性问题
        completeness = dimension_scores.get("action_completeness", {})
        if completeness.get("score", 100) < 80:
            problems.append({
                "type": "low_completeness",
                "severity": "high" if completeness.get("score", 100) < 60 else "medium",
                "description": "动作完整性不足，部分步骤未检测到"
            })
        
        # 姿态规范性问题
        standardization = dimension_scores.get("pose_standardization", {})
        if standardization.get("score", 100) < 80:
            problems.append({
                "type": "poor_pose",
                "severity": "high" if standardization.get("score", 100) < 60 else "medium",
                "description": "姿态规范性需要改进"
            })
        
        # 时效性问题
        timeliness = dimension_scores.get("timeliness", {})
        if timeliness.get("score", 100) < 80:
            details = evaluation_result.get("details", {}).get("timeliness_details", {})
            actual = details.get("actual_duration")
            std_range = details.get("standard_range", [])
            
            if actual and std_range:
                if actual < std_range[0]:
                    problems.append({
                        "type": "too_fast",
                        "severity": "medium",
                        "description": f"操作过快，实际用时{actual:.1f}秒，标准范围{std_range[0]}-{std_range[1]}秒"
                    })
                elif actual > std_range[1]:
                    problems.append({
                        "type": "too_slow",
                        "severity": "medium",
                        "description": f"操作过慢，实际用时{actual:.1f}秒，标准范围{std_range[0]}-{std_range[1]}秒"
                    })
        
        # 姿态角度问题
        if pose_details:
            avg_angles = pose_details.get("average_angles", {})
            for angle_name, angle_value in avg_angles.items():
                if isinstance(angle_value, (int, float)):
                    # 检查角度是否合理（简化版）
                    if angle_value < 90 or angle_value > 170:
                        problems.append({
                            "type": "angle_error",
                            "severity": "medium",
                            "description": f"{angle_name}异常：{angle_value:.1f}°",
                            "angle_name": angle_name,
                            "angle_value": angle_value
                        })
        
        return problems
    
    def _generate_suggestions(
        self,
        evaluation_result: Dict[str, Any],
        problems: List[Dict[str, Any]]
    ) -> List[str]:
        """
        生成改进建议
        
        Args:
            evaluation_result: 评估结果
            problems: 问题列表
            
        Returns:
            建议列表
        """
        suggestions = []
        
        # 根据问题生成建议
        for problem in problems:
            problem_type = problem.get("type")
            
            if problem_type in self.IMPROVEMENT_SUGGESTIONS:
                # 填充模板
                template = self.IMPROVEMENT_SUGGESTIONS[problem_type]
                
                if problem_type == "angle_error":
                    suggestion = template.format(
                        angle_name=problem.get("angle_name", "该角度"),
                        standard_range="150-180°"
                    )
                elif problem_type == "time_error":
                    suggestion = template.format(
                        time_range="90-150"
                    )
                else:
                    suggestion = template.format(
                        step_name="相关步骤"
                    )
                
                suggestions.append(suggestion)
        
        # 如果没有具体问题，给出一般性建议
        if not suggestions:
            performance_level = evaluation_result.get("performance_level", "").lower()
            
            if performance_level == "优秀":
                suggestions = [
                    "保持现有水平，定期复习操作流程",
                    "可以尝试指导他人"
                ]
            elif performance_level == "良好":
                suggestions = [
                    "继续练习，争取达到优秀水平",
                    "注意细节改进"
                ]
            elif performance_level == "合格":
                suggestions = [
                    "加强练习，提高动作规范性",
                    "观看标准操作视频"
                ]
            else:
                suggestions = [
                    "重新学习标准操作流程",
                    "从基础动作开始练习",
                    "寻求教练指导"
                ]
        
        return suggestions
    
    def _generate_detailed_report(
        self,
        evaluation_result: Dict[str, Any],
        problems: List[Dict[str, Any]],
        suggestions: List[str]
    ) -> str:
        """
        生成详细报告
        
        Args:
            evaluation_result: 评估结果
            problems: 问题列表
            suggestions: 建议列表
            
        Returns:
            详细报告文本
        """
        lines = []
        
        # 标题
        lines.append("=" * 60)
        lines.append("训练评估详细报告")
        lines.append("=" * 60)
        lines.append("")
        
        # 总体表现
        total_score = evaluation_result.get("total_score", 0)
        performance_level = evaluation_result.get("performance_level", "未知")
        
        lines.append(f"总体得分：{total_score:.2f}")
        lines.append(f"表现等级：{performance_level}")
        lines.append("")
        
        # 各维度得分
        lines.append("各维度得分:")
        dimension_scores = evaluation_result.get("dimension_scores", {})
        
        for dim_name, dim_data in dimension_scores.items():
            score = dim_data.get("score", 0)
            weight = dim_data.get("weight", 0)
            dim_name_cn = {
                "action_completeness": "动作完整性",
                "pose_standardization": "姿态规范性",
                "timeliness": "时效性"
            }.get(dim_name, dim_name)
            
            lines.append(f"  - {dim_name_cn}: {score:.2f}分 (权重：{weight:.0%})")
        
        lines.append("")
        
        # 存在的问题
        if problems:
            lines.append("存在的问题:")
            for i, problem in enumerate(problems, 1):
                severity = problem.get("severity", "medium")
                severity_cn = {"high": "严重", "medium": "中等", "low": "轻微"}.get(severity, severity)
                lines.append(f"  {i}. [{severity_cn}] {problem.get('description', '')}")
            lines.append("")
        
        # 改进建议
        lines.append("改进建议:")
        for i, suggestion in enumerate(suggestions, 1):
            lines.append(f"  {i}. {suggestion}")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
