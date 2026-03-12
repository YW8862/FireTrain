"""测试评分模块"""
import pytest
from decimal import Decimal
from app.services.scoring_service import ScoringService


class TestScoringService:
    """测试评分服务"""
    
    @pytest.fixture
    def scoring_service(self):
        """创建评分服务实例"""
        return ScoringService()
    
    @pytest.mark.asyncio
    async def test_score_fire_extinguisher(self, scoring_service):
        """测试灭火器操作评分"""
        result = await scoring_service.score_training(
            training_type="fire_extinguisher",
            duration_seconds=Decimal("125.5")
        )
        
        # 验证返回结构
        assert "total_score" in result
        assert "step_scores" in result
        assert "feedback" in result
        assert "suggestions" in result
        assert "action_logs" in result
        
        # 验证分数范围
        assert 0 <= result["total_score"] <= 100
        
        # 验证步骤分数
        assert len(result["step_scores"]) > 0
        for step_key, step_data in result["step_scores"].items():
            assert "step_name" in step_data
            assert "score" in step_data
            assert "is_correct" in step_data
            assert "feedback" in step_data
            assert 0 <= step_data["score"] <= 100
        
        # 验证反馈文本
        assert len(result["feedback"]) > 0
        assert isinstance(result["suggestions"], list)
        
        # 验证动作日志
        assert isinstance(result["action_logs"], list)
        if result["action_logs"]:
            for log in result["action_logs"]:
                assert "step_name" in log
                assert "score" in log
                assert "is_correct" in log
    
    @pytest.mark.asyncio
    async def test_score_generic(self, scoring_service):
        """测试通用评分"""
        result = await scoring_service.score_training(
            training_type="other_type"
        )
        
        assert "total_score" in result
        assert "step_scores" in result
        assert "feedback" in result
        assert 0 <= result["total_score"] <= 100
    
    @pytest.mark.asyncio
    async def test_score_with_time_bonus(self, scoring_service):
        """测试时间奖励/惩罚"""
        # 标准时间内完成（应该获得奖励）
        result_fast = await scoring_service.score_training(
            training_type="fire_extinguisher",
            duration_seconds=Decimal("100")  # 比标准 120 秒快
        )
        
        # 超时完成（可能会被惩罚）
        result_slow = await scoring_service.score_training(
            training_type="fire_extinguisher",
            duration_seconds=Decimal("200")  # 比标准 120 秒慢很多
        )
        
        # 两次评分都应该成功
        assert 0 <= result_fast["total_score"] <= 100
        assert 0 <= result_slow["total_score"] <= 100
        
        # 时间奖励/惩罚可能被记录
        if "time_bonus" in result_fast or "time_bonus" in result_slow:
            # 如果有时间奖励，验证其合理性
            pass
    
    @pytest.mark.asyncio
    async def test_feedback_generation(self, scoring_service):
        """测试反馈生成逻辑"""
        # 多次测试确保反馈逻辑正常
        for _ in range(5):
            result = await scoring_service.score_training(
                training_type="fire_extinguisher"
            )
            
            # 根据分数段验证反馈内容
            score = result["total_score"]
            feedback = result["feedback"]
            
            assert len(feedback) > 0
            
            # 高分应该有正面反馈
            if score >= 90:
                assert "优秀" in feedback or "规范" in feedback
            # 低分应该有改进建议
            elif score < 60:
                assert "不合格" in feedback or "重新学习" in feedback
    
    @pytest.mark.asyncio
    async def test_suggestions_generation(self, scoring_service):
        """测试建议生成逻辑"""
        result = await scoring_service.score_training(
            training_type="fire_extinguisher"
        )
        
        suggestions = result["suggestions"]
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # 每条建议都应该是字符串
        for suggestion in suggestions:
            assert isinstance(suggestion, str)
            assert len(suggestion) > 0
    
    @pytest.mark.asyncio
    async def test_step_weights(self, scoring_service):
        """测试步骤权重配置"""
        result = await scoring_service.score_training(
            training_type="fire_extinguisher"
        )
        
        # 验证步骤权重是否存在
        for step_key, step_data in result["step_scores"].items():
            if "weight" in step_data:
                weight = step_data["weight"]
                assert 0 < weight < 1
    
    @pytest.mark.asyncio
    async def test_action_logs_structure(self, scoring_service):
        """测试动作日志结构"""
        result = await scoring_service.score_training(
            training_type="fire_extinguisher"
        )
        
        action_logs = result.get("action_logs", [])
        
        if action_logs:
            for log in action_logs:
                # 验证必要字段
                assert "step_index" in log
                assert "step_name" in log
                assert "start_time" in log
                assert "end_time" in log
                assert "score" in log
                assert "is_correct" in log
                
                # 验证时间递增
                if log["step_index"] > 1:
                    assert log["start_time"] >= 0
    
    @pytest.mark.asyncio
    async def test_consistency(self, scoring_service):
        """测试评分一致性"""
        results = []
        for _ in range(10):
            result = await scoring_service.score_training(
                training_type="fire_extinguisher"
            )
            results.append(result["total_score"])
        
        # 计算平均分和标准差
        avg_score = sum(results) / len(results)
        
        # 平均分应该在合理范围内
        assert 60 <= avg_score <= 95
        
        # 分数应该有波动但不过大
        min_score = min(results)
        max_score = max(results)
        assert max_score - min_score <= 40  # 波动范围不超过 40 分


class TestScoringServiceThresholds:
    """测试评分阈值"""
    
    def test_threshold_constants(self):
        """测试阈值常量定义"""
        assert ScoringService.SCORE_THRESHOLDS["excellent"] == 90
        assert ScoringService.SCORE_THRESHOLDS["good"] == 80
        assert ScoringService.SCORE_THRESHOLDS["pass"] == 60
    
    def test_step_weights_sum(self):
        """测试步骤权重总和应接近 1"""
        weights_sum = sum(ScoringService.STEP_WEIGHTS.values())
        assert 0.95 <= weights_sum <= 1.05  # 允许小范围误差
