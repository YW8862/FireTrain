#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速验证脚本 - 验证 AI 模块集成是否成功（ONNX 版本）

使用方法:
    cd backend
    python3 scripts/verify_ai_integration.py
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def check_file_exists(file_path, description):
    """检查文件是否存在"""
    path = Path(file_path)
    if path.exists():
        size = path.stat().st_size
        print(f"✅ {description}: {file_path} ({size / 1024:.1f} KB)")
        return True
    else:
        print(f"❌ {description}不存在：{file_path}")
        return False


def main():
    """主验证函数"""
    print_section("FireTrain AI 模块集成验证（ONNX Runtime 版本）")
    
    all_passed = True
    
    # 1. 检查核心文件
    print_section("1. 检查核心文件")
    
    files_to_check = [
        ("backend/app/ai/training_inference_service.py", "训练推理服务"),
        ("backend/app/ai/fire_extinguisher_detector.py", "YOLOv8 检测器（ONNX）"),
        ("backend/app/ai/pose_analyzer.py", "姿态分析器"),
        ("backend/app/ai/rule_engine.py", "规则引擎"),
        ("backend/yolov8.onnx", "YOLOv8 ONNX 模型"),
        ("backend/tests/test_ai_inference.py", "单元测试文件"),
        ("backend/scripts/test_ai_integration.py", "集成测试脚本"),
    ]
    
    for file_path, description in files_to_check:
        if not check_file_exists(file_path, description):
            all_passed = False
    
    # 2. 检查导入和初始化
    print_section("2. 检查模块导入和初始化")
    
    try:
        from app.ai.fire_extinguisher_detector import FireExtinguisherDetector
        print("✅ FireExtinguisherDetector 导入成功")
        
        # 尝试初始化检测器
        detector = FireExtinguisherDetector(model_path="yolov8.onnx")
        print(f"✅ YOLOv8 ONNX 检测器加载成功")
        print(f"   输入形状：{detector.input_shape}")
        print(f"   类别数：{len(detector.names)}")
        detector.close()
        
    except Exception as e:
        print(f"❌ FireExtinguisherDetector 初始化失败：{e}")
        all_passed = False
    
    try:
        from app.ai.training_inference_service import TrainingInferenceService
        print("✅ TrainingInferenceService 导入成功")
        
        # 尝试初始化推理服务
        service = TrainingInferenceService(yolo_model_path="yolov8.onnx")
        print(f"✅ TrainingInferenceService 初始化成功")
        service.close()
        
    except Exception as e:
        print(f"❌ TrainingInferenceService 初始化失败：{e}")
        all_passed = False
    
    try:
        from app.ai.pose_analyzer import PoseAnalyzer
        print("✅ PoseAnalyzer 导入成功")
        
    except Exception as e:
        print(f"❌ PoseAnalyzer 导入失败：{e}")
        all_passed = False
    
    try:
        from app.ai.rule_engine import RuleEngine
        print("✅ RuleEngine 导入成功")
        
    except Exception as e:
        print(f"❌ RuleEngine 导入失败：{e}")
        all_passed = False
    
    # 3. 检查 Service 层集成
    print_section("3. 检查 Service 层集成")
    
    try:
        from app.services.training_service import TrainingService
        from app.repositories.training_repository import TrainingRepository
        
        print("✅ TrainingService 导入成功")
        print("✅ TrainingRepository 导入成功")
        
        # 检查是否有 AI 相关方法
        if hasattr(TrainingService, 'complete_training_with_ai_analysis'):
            print("✅ complete_training_with_ai_analysis 方法存在")
        else:
            print("⚠️  complete_training_with_ai_analysis 方法不存在")
            all_passed = False
        
        if hasattr(TrainingService, '_convert_ai_score_to_dict'):
            print("✅ _convert_ai_score_to_dict 方法存在")
        else:
            print("⚠️  _convert_ai_score_to_dict 方法不存在")
        
    except Exception as e:
        print(f"❌ TrainingService 导入失败：{e}")
        all_passed = False
    
    # 4. 检查 API 路由集成
    print_section("4. 检查 API 路由集成")
    
    try:
        from app.api.training import router as training_router
        print("✅ Training API Router 导入成功")
        
        # 检查响应模型
        from app.api.training import TrainingCompleteResponse
        print("✅ TrainingCompleteResponse 响应模型存在")
        
    except Exception as e:
        print(f"❌ Training API 导入失败：{e}")
        all_passed = False
    
    # 5. 总结
    print_section("验证总结")
    
    if all_passed:
        print("🎉 所有验证通过！AI 模块集成成功！")
        print("\n下一步:")
        print("1. 运行集成测试：python3 scripts/test_ai_integration.py")
        print("2. 创建测试视频：./scripts/create_test_video.sh")
        print("3. 启动后端服务：uvicorn app.main:app --reload")
        print("4. 访问 Swagger UI: http://localhost:8000/docs")
        return 0
    else:
        print("⚠️  部分验证失败，请检查上述错误信息")
        print("\n建议:")
        print("1. 确保已安装所有依赖：pip install -r requirements.txt")
        print("2. 确保 ONNX 模型文件存在：backend/yolov8.onnx")
        print("3. 查看详细错误信息并修复")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
