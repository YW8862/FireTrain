"""测试规则引擎和反馈生成器"""
import pytest
from app.ai.rule_engine import RuleEngine
from app.ai.fire_extinguisher_standard import get_performance_level
from app.ai.feedback_generator import FeedbackGenerator


class TestRuleEngine:
    """测试规则引擎"""
    
    @pytest.fixture
    def rule_engine(self):
        """创建规则引擎实例"""
        return RuleEngine()
    
    def test_action_completeness_calculation(self, rule_engine):
        """测试动作完整性计算"""
        step_scores = {
            "step1": {"step_name": "准备阶段", "score": 85, "weight": 0.2},
            "step2": {"step_name": "提灭火器", "score": 90, "weight": 0.2},
            "step3": {"step_name": "拔保险销", "score": 75, "weight": 0.2},
        }

        score = rule_engine._calculate_action_completeness(step_scores)

        assert isinstance(score, (int, float))
        assert 0 <= score <= 100

    def test_pose_standardization_calculation(self, rule_engine):
        """测试姿态规范性计算"""
        step_feature_summary = {
            "step1": {"pose_quality_score": 88, "completed": True},
            "step2": {"pose_quality_score": 92, "completed": True},
        }
        pose_stats_summary = {
            "body": {"stability": 25.0},
        }

        score = rule_engine._calculate_pose_standardization(step_feature_summary, pose_stats_summary)

        assert isinstance(score, (int, float))
        assert 0 <= score <= 100

    def test_timeliness_within_range(self, rule_engine):
        """测试时效性计算（标准时间内）"""
        score = rule_engine._calculate_timeliness(
            duration_seconds=120.0,
            training_type="fire_extinguisher"
        )

        assert score == 100.0

    def test_timeliness_too_slow(self, rule_engine):
        """测试时效性计算（超时）"""
        score = rule_engine._calculate_timeliness(
            duration_seconds=180.0,
            training_type="fire_extinguisher"
        )

        assert score < 100
        assert score >= 0

    def test_timeliness_too_fast(self, rule_engine):
        """测试时效性计算（过快）"""
        score = rule_engine._calculate_timeliness(
            duration_seconds=30.0,
            training_type="fire_extinguisher"
        )

        assert score < 100
        assert score >= 0
    
    def test_performance_level_classification(self, rule_engine):
        """测试表现等级分类"""
        assert get_performance_level(95)["code"] == "excellent"
        assert get_performance_level(85)["code"] == "good"
        assert get_performance_level(70)["code"] == "pass"
        assert get_performance_level(50)["code"] == "fail"

    def test_action_completeness_returns_zero_without_step_scores(self, rule_engine):
        assert rule_engine._calculate_action_completeness({}) == 0.0

    def test_pose_standardization_uses_body_stability_default_when_no_pose_data(self, rule_engine):
        # 无 step 姿态数据时，pose 部分得 0，body_stability 取默认 70.0 → 21.0
        score = rule_engine._calculate_pose_standardization({}, {})

        assert score == 21.0

    def test_pose_standardization_uses_only_pose_quality_and_body_stability(self, rule_engine):
        # 当前实现只看 pose_quality_score 和 body_stability，不再读 weight
        score = rule_engine._calculate_pose_standardization(
            {"step1": {"pose_quality_score": 80.0, "completed": True}},
            {"body": {"stability": 20.0}},
        )

        # avg_pose_score=80.0, body_stability≈93.4 → 0.7*80 + 0.3*93.4
        assert score == round(80.0 * 0.7 + (100.0 - 20.0 * 0.33) * 0.3, 1)

    def test_timeliness_returns_zero_when_duration_missing(self, rule_engine):
        assert rule_engine._calculate_timeliness(
            duration_seconds=0.0,
            training_type="fire_extinguisher",
        ) == 0.0

    @pytest.mark.asyncio
    async def test_full_evaluation(self, rule_engine):
        """测试完整评估流程"""
        analysis_summary = {
            "video_duration": 125.5,
            "training_type": "fire_extinguisher",
            "step_feature_summary": {
                "step1": {"completed": True, "confidence": 85, "pose_quality_score": 80},
                "step2": {"completed": True, "confidence": 90, "pose_quality_score": 85},
            },
            "pose_stats_summary": {
                "body": {"stability": 25.0},
            },
            "completed_steps_count": 2,
            "completed_steps": ["step1", "step2"],
            "missing_steps": [],
        }

        result = await rule_engine.evaluate(analysis_summary)

        # 验证返回结构
        assert "total_score" in result
        assert "performance_level" in result
        assert "performance_label" in result
        assert "dimension_scores" in result
        assert "details" in result

        # 验证分数范围
        assert 0 <= result["total_score"] <= 100

        # 验证维度得分
        dimensions = result["dimension_scores"]
        assert "action_completeness" in dimensions
        assert "pose_standardization" in dimensions
        assert "timeliness" in dimensions


class TestFeedbackGenerator:
    """测试反馈生成器"""
    
    @pytest.fixture
    def feedback_generator(self):
        """创建反馈生成器实例"""
        return FeedbackGenerator()
    
    def test_overall_feedback_generation_excellent(self, feedback_generator):
        """测试优秀等级的总体反馈"""
        feedback = feedback_generator._generate_overall_feedback(
            performance_level="优秀",
            total_score=95.0
        )
        
        assert len(feedback) > 0
        assert "95.0" in feedback
    
    def test_overall_feedback_generation_fail(self, feedback_generator):
        """测试不合格等级的总体反馈"""
        feedback = feedback_generator._generate_overall_feedback(
            performance_level="不合格",
            total_score=45.0
        )
        
        assert len(feedback) > 0
        assert "45.0" in feedback
    
    def test_step_feedbacks_generation(self, feedback_generator):
        """测试步骤反馈生成"""
        evaluation_result = {
            "performance_level": "良好",
            "total_score": 85.0
        }
        
        step_feedbacks = feedback_generator._generate_step_feedbacks(evaluation_result)
        
        assert isinstance(step_feedbacks, dict)
        assert len(step_feedbacks) > 0
    
    def test_problem_identification_low_score(self, feedback_generator):
        """测试问题识别（低分）"""
        evaluation_result = {
            "dimension_scores": {
                "action_completeness": {"score": 65},
                "pose_standardization": {"score": 70},
                "timeliness": {"score": 90}
            }
        }
        
        problems = feedback_generator._identify_problems(
            evaluation_result=evaluation_result,
            action_logs=None,
            pose_details=None
        )
        
        assert isinstance(problems, list)
        # 应该识别出动作完整性和姿态规范性问题
        assert len(problems) >= 2
    
    def test_problem_identification_time_issue(self, feedback_generator):
        """测试问题识别（时间问题）"""
        evaluation_result = {
            "dimension_scores": {
                "action_completeness": {"score": 90},
                "pose_standardization": {"score": 90},
                "timeliness": {"score": 60}
            },
            "details": {
                "timeliness_details": {
                    "actual_duration": 180.0,
                    "standard_range": [90, 150]
                }
            }
        }
        
        problems = feedback_generator._identify_problems(
            evaluation_result=evaluation_result,
            action_logs=None,
            pose_details=None
        )
        
        assert isinstance(problems, list)
        # 应该识别出时间过慢的问题
        time_problems = [p for p in problems if "过慢" in p.get("description", "")]
        assert len(time_problems) > 0
    
    def test_suggestions_generation(self, feedback_generator):
        """测试建议生成"""
        problems = [
            {
                "type": "low_completeness",
                "severity": "medium",
                "description": "动作完整性不足"
            }
        ]
        
        suggestions = feedback_generator._generate_suggestions(
            evaluation_result={},
            problems=problems
        )
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

    def test_problem_identification_detects_fast_and_angle_issue(self, feedback_generator):
        evaluation_result = {
            "dimension_scores": {
                "timeliness": {"score": 60}
            },
            "details": {
                "timeliness_details": {
                    "actual_duration": 50.0,
                    "standard_range": [90, 150]
                }
            }
        }

        problems = feedback_generator._identify_problems(
            evaluation_result=evaluation_result,
            action_logs=None,
            pose_details={"average_angles": {"right_arm": 180.0}},
        )

        assert any(problem["type"] == "too_fast" for problem in problems)
        assert any(problem["type"] == "angle_error" for problem in problems)

    def test_suggestions_generation_handles_angle_error_template(self, feedback_generator):
        suggestions = feedback_generator._generate_suggestions(
            evaluation_result={},
            problems=[
                {
                    "type": "angle_error",
                    "angle_name": "right_arm",
                    "angle_value": 180.0,
                }
            ],
        )

        assert suggestions == ["调整right_arm，标准角度为150-180°"]

    def test_suggestions_generation_handles_time_error_template(self, feedback_generator):
        suggestions = feedback_generator._generate_suggestions(
            evaluation_result={},
            problems=[{"type": "time_error"}],
        )

        assert suggestions == ["控制总用时在90-150秒范围内"]

    def test_suggestions_generation_handles_generic_template(self, feedback_generator):
        suggestions = feedback_generator._generate_suggestions(
            evaluation_result={},
            problems=[{"type": "incorrect"}],
        )

        assert suggestions == ["纠正【相关步骤】的操作手法"]

    def test_suggestions_generation_falls_back_for_unknown_level(self, feedback_generator):
        suggestions = feedback_generator._generate_suggestions(
            evaluation_result={"performance_level": "未知"},
            problems=[],
        )

        assert "重新学习标准操作流程" in suggestions

    def test_suggestions_generation_falls_back_for_excellent_level(self, feedback_generator):
        suggestions = feedback_generator._generate_suggestions(
            evaluation_result={"performance_level": "优秀"},
            problems=[],
        )

        assert suggestions == ["保持现有水平，定期复习操作流程", "可以尝试指导他人"]

    def test_suggestions_generation_falls_back_for_good_level(self, feedback_generator):
        suggestions = feedback_generator._generate_suggestions(
            evaluation_result={"performance_level": "良好"},
            problems=[],
        )

        assert suggestions == ["继续练习，争取达到优秀水平", "注意细节改进"]

    def test_detailed_report_generation_without_problems(self, feedback_generator):
        report = feedback_generator._generate_detailed_report(
            evaluation_result={
                "total_score": 95.0,
                "performance_level": "优秀",
                "dimension_scores": {},
            },
            problems=[],
            suggestions=["保持现有水平"],
        )

        assert "存在的问题:" not in report
        assert "改进建议:" in report
    
    def test_detailed_report_generation(self, feedback_generator):
        """测试详细报告生成"""
        evaluation_result = {
            "total_score": 75.5,
            "performance_level": "合格",
            "dimension_scores": {
                "action_completeness": {"score": 70, "weight": 0.4},
                "pose_standardization": {"score": 80, "weight": 0.4},
                "timeliness": {"score": 75, "weight": 0.2}
            }
        }
        
        problems = [
            {
                "type": "low_completeness",
                "severity": "medium",
                "description": "动作完整性不足"
            }
        ]
        
        suggestions = ["加强练习，提高动作规范性"]
        
        report = feedback_generator._generate_detailed_report(
            evaluation_result=evaluation_result,
            problems=problems,
            suggestions=suggestions
        )
        
        assert isinstance(report, str)
        assert len(report) > 100
        assert "训练评估详细报告" in report
        assert "75.5" in report
    
    @pytest.mark.asyncio
    async def test_full_feedback_generation(self, feedback_generator):
        """测试完整反馈生成"""
        evaluation_result = {
            "total_score": 82.5,
            "performance_level": "良好",
            "dimension_scores": {
                "action_completeness": {"score": 85, "weight": 0.4},
                "pose_standardization": {"score": 80, "weight": 0.4},
                "timeliness": {"score": 80, "weight": 0.2}
            },
            "details": {}
        }
        
        result = feedback_generator.generate_feedback(
            evaluation_result=evaluation_result,
            action_logs=None,
            pose_details=None
        )
        
        # 验证返回结构
        assert "overall_feedback" in result
        assert "step_feedbacks" in result
        assert "problems" in result
        assert "suggestions" in result
        assert "detailed_report" in result
        
        # 验证内容
        assert len(result["overall_feedback"]) > 0
        assert isinstance(result["step_feedbacks"], dict)
        assert isinstance(result["suggestions"], list)
        assert len(result["detailed_report"]) > 0


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_rule_engine_and_feedback_integration(self):
        """测试规则引擎和反馈生成器的集成"""
        rule_engine = RuleEngine()
        feedback_generator = FeedbackGenerator()

        # 准备测试数据（统一 analysis_summary 结构）
        analysis_summary = {
            "video_duration": 118.5,
            "training_type": "fire_extinguisher",
            "step_feature_summary": {
                "step1": {"completed": True, "confidence": 88, "pose_quality_score": 87},
                "step2": {"completed": True, "confidence": 85, "pose_quality_score": 83},
                "step3": {"completed": True, "confidence": 90, "pose_quality_score": 91},
            },
            "pose_stats_summary": {
                "body": {"stability": 25.0},
                "right_arm": {"mean": 165.5},
            },
            "completed_steps_count": 3,
            "completed_steps": ["step1", "step2", "step3"],
            "missing_steps": [],
        }

        # 1. 规则引擎评估
        evaluation = await rule_engine.evaluate(analysis_summary)

        # 2. 生成反馈
        feedback = feedback_generator.generate_feedback(
            evaluation_result=evaluation,
            action_logs=None,
            pose_details=analysis_summary.get("pose_stats_summary"),
        )

        # 验证
        assert evaluation["total_score"] > 0
        assert feedback["overall_feedback"] != ""
        assert len(feedback["suggestions"]) > 0
