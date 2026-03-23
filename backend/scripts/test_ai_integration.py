#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI 推理集成测试脚本（ONNX Runtime 版本）

测试完整的 AI 推理流程：
1. YOLOv8 ONNX 模型加载
2. MediaPipe 姿态分析
3. 视频分析
4. AI 评分生成

使用方法:
    cd backend
    python3 scripts/test_ai_integration.py
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai.training_inference_service import TrainingInferenceService
from app.ai.fire_extinguisher_detector import FireExtinguisherDetector


def test_onnx_model_loading():
    """测试 ONNX 模型加载"""
    print("=" * 60)
    print("测试 1: ONNX 模型加载")
    print("=" * 60)
    
    try:
        detector = FireExtinguisherDetector(
            model_path="yolov8.onnx",
            conf_threshold=0.5,
            img_size=640
        )
        
        print(f"✅ ONNX 模型加载成功")
        print(f"   模型路径：{detector.model_path}")
        print(f"   输入形状：{detector.input_shape}")
        print(f"   类别数：{len(detector.names)}")
        
        detector.close()
        return True
        
    except Exception as e:
        print(f"❌ ONNX 模型加载失败：{e}")
        return False


def test_service_initialization():
    """测试推理服务初始化"""
    print("\n" + "=" * 60)
    print("测试 2: 推理服务初始化")
    print("=" * 60)
    
    try:
        service = TrainingInferenceService(
            yolo_model_path="yolov8.onnx",
            yolo_conf_threshold=0.5,
            use_pose_analysis=True
        )
        
        print(f"✅ 推理服务初始化成功")
        print(f"   YOLO 检测器：{type(service.yolo_detector).__name__}")
        print(f"   姿态分析器：{type(service.pose_analyzer).__name__}")
        print(f"   启用姿态分析：{service.use_pose_analysis}")
        
        service.close()
        return True
        
    except Exception as e:
        print(f"❌ 推理服务初始化失败：{e}")
        return False


def test_video_analysis():
    """测试视频分析"""
    print("\n" + "=" * 60)
    print("测试 3: 视频分析")
    print("=" * 60)
    
    # 查找测试视频
    test_video_paths = [
        "data/videos/test_videos/mock_training.mp4",
        "../data/videos/test_videos/mock_training.mp4",
    ]
    
    video_path = None
    for path in test_video_paths:
        if Path(path).exists():
            video_path = path
            break
    
    if not video_path:
        print(f"⚠️  测试视频不存在，跳过此测试")
        print(f"   建议运行：./scripts/create_test_video.sh 创建测试视频")
        return True  # 不视为失败
    
    try:
        service = TrainingInferenceService(
            yolo_model_path="yolov8.onnx",
            yolo_conf_threshold=0.5,
            use_pose_analysis=True
        )
        
        print(f"📹 开始分析视频：{video_path}")
        result = service.analyze_video(video_path, "fire_extinguisher")
        
        print(f"✅ 视频分析成功")
        print(f"   视频时长：{result['video_duration']:.2f}秒")
        print(f"   总帧数：{result['total_frames']}")
        print(f"   处理帧数：{result['processed_frames']}")
        print(f"   检测到的步骤：{len(result['step_sequence'])}")
        print(f"   目标检测次数：{result['total_detections']}")
        print(f"   姿态分析帧数：{result['pose_frame_count']}")
        
        # 打印步骤信息
        if result['step_sequence']:
            print(f"\n   步骤序列:")
            for step in result['step_sequence'][:3]:  # 只显示前 3 个步骤
                print(f"     - {step['step_name']}: {step['start_timestamp']:.1f}s - {step['end_timestamp']:.1f}s")
            if len(result['step_sequence']) > 3:
                print(f"     ... 还有 {len(result['step_sequence']) - 3} 个步骤")
        
        service.close()
        return True
        
    except Exception as e:
        print(f"❌ 视频分析失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_scoring():
    """测试 AI 评分生成"""
    print("\n" + "=" * 60)
    print("测试 4: AI 评分生成")
    print("=" * 60)
    
    try:
        service = TrainingInferenceService(
            yolo_model_path="yolov8.onnx",
            use_pose_analysis=True
        )
        
        # 构造模拟分析结果
        mock_analysis = {
            "step_sequence": [
                {"step_index": i, "step_name": name, "start_timestamp": (i-1)*5.0, 
                 "end_timestamp": i*5.0, "is_completed": True}
                for i, name in enumerate(["准备阶段", "提灭火器", "拔保险销", 
                                         "握喷管", "瞄准火源", "压把手"], 1)
            ],
            "step_times": {f"step{i}": 5.0 for i in range(1, 7)},
            "pose_frame_count": 10,
            "all_pose_results": [
                {"angles": {"right_arm": 160, "left_arm": 155, "body": 90}},
                {"angles": {"right_arm": 165, "left_arm": 160, "body": 88}}
            ]
        }
        
        print(f"📊 开始生成 AI 评分")
        score_result = service.generate_ai_scores(mock_analysis)
        
        print(f"✅ AI 评分生成成功")
        print(f"   总分：{float(score_result['total_score']):.2f}")
        print(f"   等级：{score_result['performance_level']}")
        
        # 打印维度分数
        dimension_scores = score_result.get("dimension_scores", {})
        if "action_completeness" in dimension_scores:
            print(f"   动作完整性：{float(dimension_scores['action_completeness']['score']):.2f}")
        if "pose_standardization" in dimension_scores:
            print(f"   姿态规范性：{float(dimension_scores['pose_standardization']['score']):.2f}")
        if "timeliness" in dimension_scores:
            print(f"   时效性：{float(dimension_scores['timeliness']['score']):.2f}")
        
        service.close()
        return True
        
    except Exception as e:
        print(f"❌ AI 评分生成失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("FireTrain AI 推理集成测试（ONNX Runtime 版本）")
    print("=" * 60)
    
    tests = [
        ("ONNX 模型加载", test_onnx_model_loading),
        ("推理服务初始化", test_service_initialization),
        ("视频分析", test_video_analysis),
        ("AI 评分生成", test_ai_scoring),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} 测试异常：{e}")
            results.append((test_name, False))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {test_name}")
    
    print(f"\n总计：{passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！AI 推理模块集成成功！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
