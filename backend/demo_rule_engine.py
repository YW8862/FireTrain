"""规则引擎与反馈生成演示

演示如何使用规则引擎进行综合评分并生成可解释的反馈。
"""
import asyncio
from decimal import Decimal
from app.ai.rule_engine import RuleEngine
from app.ai.feedback_generator import FeedbackGenerator


async def demo_basic_scoring():
    """基础评分演示"""
    print("=" * 60)
    print("FireTrain 规则引擎与反馈生成演示")
    print("=" * 60)
    print()
    
    # 初始化
    rule_engine = RuleEngine()
    feedback_generator = FeedbackGenerator()
    
    # 模拟数据 - 表现良好的情况
    print("场景 1: 表现良好的训练")
    print("-" * 60)
    
    action_scores_good = {
        "step_scores": {
            "step1": {"step_name": "准备阶段", "score": 88},
            "step2": {"step_name": "提灭火器", "score": 85},
            "step3": {"step_name": "拔保险销", "score": 90},
            "step4": {"step_name": "握喷管", "score": 82},
            "step5": {"step_name": "瞄准火源", "score": 87},
            "step6": {"step_name": "压把手", "score": 89},
        },
        "average_detection_rate": 0.95
    }
    
    pose_scores_good = {
        "step_scores": {
            "step1": {"step_name": "准备阶段", "score": 87, "weight": 0.2},
            "step2": {"step_name": "提灭火器", "score": 83, "weight": 0.15},
            "step3": {"step_name": "拔保险销", "score": 91, "weight": 0.25},
            "step4": {"step_name": "握喷管", "score": 80, "weight": 0.1},
            "step5": {"step_name": "瞄准火源", "score": 88, "weight": 0.2},
            "step6": {"step_name": "压把手", "score": 86, "weight": 0.15},
        },
        "frame_count": 30,
        "average_angles": {
            "right_arm": 165.5,
            "body": 92.3
        }
    }
    
    duration_good = Decimal("118.5")
    
    # 评估
    evaluation = await rule_engine.evaluate(
        action_scores=action_scores_good,
        pose_scores=pose_scores_good,
        duration_seconds=duration_good,
        training_type="fire_extinguisher"
    )
    
    # 生成反馈
    feedback = feedback_generator.generate_feedback(
        evaluation_result=evaluation,
        action_logs=None,
        pose_details=pose_scores_good
    )
    
    # 输出结果
    print(f"总分：{evaluation['total_score']:.2f}")
    print(f"等级：{evaluation['performance_level']}")
    print()
    print(f"总体反馈：{feedback['overall_feedback']}")
    print()
    print("各维度得分:")
    for dim_name, dim_data in evaluation['dimension_scores'].items():
        dim_name_cn = {
            "action_completeness": "动作完整性",
            "pose_standardization": "姿态规范性",
            "timeliness": "时效性"
        }.get(dim_name, dim_name)
        print(f"  - {dim_name_cn}: {dim_data['score']:.2f}分 (权重{dim_data['weight']:.0%})")
    print()
    
    if feedback['problems']:
        print("存在的问题:")
        for problem in feedback['problems']:
            print(f"  - [{problem.get('severity', 'medium')}] {problem.get('description', '')}")
        print()
    
    print("改进建议:")
    for i, suggestion in enumerate(feedback['suggestions'], 1):
        print(f"  {i}. {suggestion}")
    print()
    print()
    
    # 场景 2 - 需要改进的情况
    print("场景 2: 需要改进的训练")
    print("-" * 60)
    
    action_scores_poor = {
        "step_scores": {
            "step1": {"step_name": "准备阶段", "score": 65},
            "step2": {"step_name": "提灭火器", "score": 70},
            "step3": {"step_name": "拔保险销", "score": 55},
            "step4": {"step_name": "握喷管", "score": 60},
            "step5": {"step_name": "瞄准火源", "score": 68},
            "step6": {"step_name": "压把手", "score": 62},
        },
        "average_detection_rate": 0.75
    }
    
    pose_scores_poor = {
        "step_scores": {
            "step1": {"step_name": "准备阶段", "score": 62, "weight": 0.2},
            "step2": {"step_name": "提灭火器", "score": 68, "weight": 0.15},
            "step3": {"step_name": "拔保险销", "score": 55, "weight": 0.25},
            "step4": {"step_name": "握喷管", "score": 58, "weight": 0.1},
            "step5": {"step_name": "瞄准火源", "score": 65, "weight": 0.2},
            "step6": {"step_name": "压把手", "score": 60, "weight": 0.15},
        },
        "frame_count": 25,
        "average_angles": {
            "right_arm": 145.2,  # 角度偏低
            "body": 78.5         # 身体前倾过多
        }
    }
    
    duration_poor = Decimal("185.0")  # 超时严重
    
    # 评估
    evaluation_poor = await rule_engine.evaluate(
        action_scores=action_scores_poor,
        pose_scores=pose_scores_poor,
        duration_seconds=duration_poor,
        training_type="fire_extinguisher"
    )
    
    # 生成反馈
    feedback_poor = feedback_generator.generate_feedback(
        evaluation_result=evaluation_poor,
        action_logs=None,
        pose_details=pose_scores_poor
    )
    
    # 输出结果
    print(f"总分：{evaluation_poor['total_score']:.2f}")
    print(f"等级：{evaluation_poor['performance_level']}")
    print()
    print(f"总体反馈：{feedback_poor['overall_feedback']}")
    print()
    
    if feedback_poor['problems']:
        print("存在的问题:")
        for problem in feedback_poor['problems']:
            severity = problem.get('severity', 'medium')
            severity_cn = {"high": "严重", "medium": "中等", "low": "轻微"}.get(severity, severity)
            print(f"  - [{severity_cn}] {problem.get('description', '')}")
        print()
    
    print("改进建议:")
    for i, suggestion in enumerate(feedback_poor['suggestions'], 1):
        print(f"  {i}. {suggestion}")
    print()
    print()
    
    # 显示详细报告
    print("=" * 60)
    print("详细报告示例（场景 1）")
    print("=" * 60)
    print()
    print(feedback['detailed_report'])
    print()


async def demo_custom_scenario():
    """自定义场景演示"""
    print("\n" + "=" * 60)
    print("自定义场景演示")
    print("=" * 60)
    print()
    
    rule_engine = RuleEngine()
    feedback_generator = FeedbackGenerator()
    
    # 用户可以自定义各维度的权重
    print("提示：可以修改 RuleEngine 中的 DIMENSION_WEIGHTS 来自定义权重")
    print()
    
    # 示例：更注重时效性的场景
    print("示例：快速反应训练（更注重时效性）")
    print("-" * 60)
    
    # 临时修改权重
    original_weights = RuleEngine.DIMENSION_WEIGHTS.copy()
    RuleEngine.DIMENSION_WEIGHTS = {
        "action_completeness": Decimal("0.3"),   # 降低到 30%
        "pose_standardization": Decimal("0.3"),  # 降低到 30%
        "timeliness": Decimal("0.4"),            # 提高到 40%
    }
    
    action_scores = {
        "step_scores": {
            "step1": {"step_name": "准备阶段", "score": 85},
            "step2": {"step_name": "提灭火器", "score": 88},
            "step3": {"step_name": "拔保险销", "score": 92},
        }
    }
    
    pose_scores = {
        "step_scores": {
            "step1": {"step_name": "准备阶段", "score": 83, "weight": 0.2},
            "step2": {"step_name": "提灭火器", "score": 87, "weight": 0.15},
            "step3": {"step_name": "拔保险销", "score": 90, "weight": 0.25},
        },
        "frame_count": 20
    }
    
    # 非常快但姿势一般
    duration = Decimal("75.0")  # 比标准快很多
    
    evaluation = await rule_engine.evaluate(
        action_scores=action_scores,
        pose_scores=pose_scores,
        duration_seconds=duration,
        training_type="fire_extinguisher"
    )
    
    feedback = feedback_generator.generate_feedback(
        evaluation_result=evaluation,
        action_logs=None,
        pose_details=pose_scores
    )
    
    print(f"总分：{evaluation['total_score']:.2f}")
    print(f"等级：{evaluation['performance_level']}")
    print(f"总体反馈：{feedback['overall_feedback']}")
    print()
    
    # 恢复原始权重
    RuleEngine.DIMENSION_WEIGHTS = original_weights


if __name__ == "__main__":
    print("\nFireTrain 规则引擎与反馈生成演示系统")
    print("=" * 60)
    print("功能:")
    print("  1. 三维度综合评分（动作完整性、姿态规范性、时效性）")
    print("  2. 可解释的反馈生成")
    print("  3. 问题识别与建议")
    print("=" * 60)
    print()
    
    # 运行基础演示
    asyncio.run(demo_basic_scoring())
    
    # 运行自定义场景演示
    asyncio.run(demo_custom_scenario())
    
    print("\n演示完成!")
    print("\n使用方法:")
    print("  python demo_rule_engine.py")
    print()
