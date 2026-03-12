"""测试规则引擎和反馈生成器"""
import pytest
from decimal import Decimal
from app.ai.rule_engine import RuleEngine, PerformanceLevel
from app.ai.feedback_generator import FeedbackGenerator


class TestRuleEngine:
    """测试规则引擎"""
    
    @pytest.fixture
    def rule_engine(self):
        """创建规则引擎实例"""
        return RuleEngine()
    
    def test_action_completeness_calculation(self, rule_engine):
        """测试动作完整性计算"""
        action_scores = {
            "step_scores": {
                "step1": {"step_name": "准备阶段", "score": 85},
                "step2": {"step_name": "提灭火器", "score": 90},
                "step3": {"step_name": "拔保险销", "score": 75},
            }
        }
        
        score = rule_engine._calculate_action_completeness(action_scores)
        
        assert isinstance(score, Decimal)
        assert 0 <= score <= 100
    
    def test_pose_standardization_calculation(self, rule_engine):
        """测试姿态规范性计算"""
        pose_scores = {
            "step_scores": {
                "step1": {"step_name": "准备阶段", "score": 88, "weight": 0.2},
                "step2": {"step_name": "提灭火器", "score": 92, "weight": 0.15},
            }
        }
        
        score = rule_engine._calculate_pose_standardization(pose_scores)
        
        assert isinstance(score, Decimal)
        assert 0 <= score <= 100
    
    def test_timeliness_within_range(self, rule_engine):
        """测试时效性计算（标准时间内）"""
        duration = Decimal("120")  # 2 分钟，在标准范围内
        
        score = rule_engine._calculate_timeliness(
            duration_seconds=duration,
            training_type="fire_extinguisher"
        )
        
        assert score == Decimal("100")
    
    def test_timeliness_too_slow(self, rule_engine):
        """测试时效性计算（超时）"""
        duration = Decimal("180")  # 3 分钟，超出标准范围
        
        score = rule_engine._calculate_timeliness(
            duration_seconds=duration,
            training_type="fire_extinguisher"
        )
        
        assert score < Decimal("100")
        assert score >= Decimal("0")
    
    def test_timeliness_too_fast(self, rule_engine):
        """测试时效性计算（过快）"""
        duration = Decimal("60")  # 1 分钟，低于标准范围
        
        score = rule_engine._calculate_timeliness(
            duration_seconds=duration,
            training_type="fire_extinguisher"
        )
        
        assert score < Decimal("100")
        assert score >= Decimal("0")
    
    def test_performance_level_classification(self, rule_engine):
        """测试表现等级分类"""
        assert rule_engine._get_performance_level(95) == PerformanceLevel.EXCELLENT
        assert rule_engine._get_performance_level(85) == PerformanceLevel.GOOD
        assert rule_engine._get_performance_level(70) == PerformanceLevel.PASS
        assert rule_engine._get_performance_level(50) == PerformanceLevel.FAIL
    
    @pytest.mark.asyncio
    async def test_full_evaluation(self, rule_engine):
        """测试完整评估流程"""
        action_scores = {
            "step_scores": {
                "step1": {"step_name": "准备阶段", "score": 85},
                "step2": {"step_name": "提灭火器", "score": 90},
            }
        }
        
        pose_scores = {
            "step_scores": {
                "step1": {"step_name": "准备阶段", "score": 88, "weight": 0.2},
                "step2": {"step_name": "提灭火器", "score": 92, "weight": 0.15},
            },
            "frame_count": 30
        }
        
        duration = Decimal("125.5")
        
        result = await rule_engine.evaluate(
            action_scores=action_scores,
            pose_scores=pose_scores,
            duration_seconds=duration,
            training_type="fire_extinguisher"
        )
        
        # 验证返回结构
        assert "total_score" in result
        assert "performance_level" in result
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
        
        # 准备测试数据
        action_scores = {
            "step_scores": {
                "step1": {"step_name": "准备阶段", "score": 88},
                "step2": {"step_name": "提灭火器", "score": 85},
                "step3": {"step_name": "拔保险销", "score": 90},
            }
        }
        
        pose_scores = {
            "step_scores": {
                "step1": {"step_name": "准备阶段", "score": 87, "weight": 0.2},
                "step2": {"step_name": "提灭火器", "score": 83, "weight": 0.15},
                "step3": {"step_name": "拔保险销", "score": 91, "weight": 0.25},
            },
            "frame_count": 25,
            "average_angles": {
                "right_arm": 165.5,
                "body": 92.3
            }
        }
        
        duration = Decimal("118.5")
        
        # 1. 规则引擎评估
        evaluation = await rule_engine.evaluate(
            action_scores=action_scores,
            pose_scores=pose_scores,
            duration_seconds=duration,
            training_type="fire_extinguisher"
        )
        
        # 2. 生成反馈
        feedback = feedback_generator.generate_feedback(
            evaluation_result=evaluation,
            action_logs=None,
            pose_details=pose_scores
        )
        
        # 验证
        assert evaluation["total_score"] > 0
        assert feedback["overall_feedback"] != ""
        assert len(feedback["suggestions"]) > 0
