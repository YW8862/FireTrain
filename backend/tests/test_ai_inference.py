"""测试 AI 推理服务（ONNX Runtime 版本）

测试 TrainingInferenceService 的完整功能，包括：
1. YOLOv8 ONNX 模型检测
2. MediaPipe 姿态分析
3. 动作序列识别
4. AI 评分生成
"""
import pytest
from pathlib import Path
from app.ai.training_inference_service import TrainingInferenceService


class TestTrainingInferenceService:
    """测试训练推理服务（ONNX 版本）"""
    
    def test_analyze_mock_video(self):
        """测试分析模拟视频"""
        # 创建一个空的测试视频（或使用真实视频文件）
        video_path = "data/videos/test_videos/mock_training.mp4"
        
        if not Path(video_path).exists():
            pytest.skip("测试视频不存在，跳过此测试")
        
        # 使用 ONNX 模型路径
        service = TrainingInferenceService(
            yolo_model_path="yolov8.onnx",  # ✅ ONNX 格式
            yolo_conf_threshold=0.5,
            use_pose_analysis=True
        )
        
        try:
            result = service.analyze_video(video_path, "fire_extinguisher")
            
            # 验证基本字段
            assert "video_duration" in result
            assert "step_sequence" in result
            assert "step_times" in result
            assert "frame_results" in result
            assert "total_frames" in result
            assert "processed_frames" in result
            
            # 验证数据类型
            assert isinstance(result["video_duration"], (int, float))
            assert isinstance(result["step_sequence"], list)
            assert isinstance(result["step_times"], dict)
            
            # 打印调试信息
            print(f"\n✅ 视频分析成功:")
            print(f"  视频时长：{result['video_duration']:.2f}秒")
            print(f"  总帧数：{result['total_frames']}")
            print(f"  处理帧数：{result['processed_frames']}")
            print(f"  检测到的步骤：{len(result['step_sequence'])}")
            print(f"  目标检测次数：{result['total_detections']}")
            print(f"  姿态分析帧数：{result['pose_frame_count']}")
            
        except Exception as e:
            pytest.fail(f"视频分析失败：{e}")
        finally:
            service.close()
    
    def test_generate_ai_scores(self):
        """测试 AI 评分生成"""
        service = TrainingInferenceService(
            yolo_model_path="yolov8.onnx",
            use_pose_analysis=True
        )
        
        # 构造模拟分析结果
        mock_analysis = {
            "step_sequence": [
                {
                    "step_index": 1,
                    "step_name": "准备阶段",
                    "start_timestamp": 0.0,
                    "end_timestamp": 5.0,
                    "is_completed": True,
                    "detected_actions": ["person_detected"]
                },
                {
                    "step_index": 2,
                    "step_name": "提灭火器",
                    "start_timestamp": 5.0,
                    "end_timestamp": 10.0,
                    "is_completed": True,
                    "detected_actions": ["person_detected", "arm_raised"]
                },
                {
                    "step_index": 3,
                    "step_name": "拔保险销",
                    "start_timestamp": 10.0,
                    "end_timestamp": 15.0,
                    "is_completed": True,
                    "detected_actions": ["person_detected"]
                },
                {
                    "step_index": 4,
                    "step_name": "握喷管",
                    "start_timestamp": 15.0,
                    "end_timestamp": 20.0,
                    "is_completed": True,
                    "detected_actions": ["person_detected"]
                },
                {
                    "step_index": 5,
                    "step_name": "瞄准火源",
                    "start_timestamp": 20.0,
                    "end_timestamp": 25.0,
                    "is_completed": True,
                    "detected_actions": ["person_detected", "arm_raised"]
                },
                {
                    "step_index": 6,
                    "step_name": "压把手",
                    "start_timestamp": 25.0,
                    "end_timestamp": 30.0,
                    "is_completed": True,
                    "detected_actions": ["person_detected"]
                }
            ],
            "step_times": {
                "step1": 5.0,
                "step2": 5.0,
                "step3": 5.0,
                "step4": 5.0,
                "step5": 5.0,
                "step6": 5.0,
                "total": 30.0
            },
            "pose_frame_count": 10,
            "all_pose_results": [
                {
                    "angles": {
                        "right_arm": 160,
                        "left_arm": 155,
                        "body": 90
                    }
                },
                {
                    "angles": {
                        "right_arm": 165,
                        "left_arm": 160,
                        "body": 88
                    }
                }
            ]
        }
        
        try:
            score_result = service.generate_ai_scores(mock_analysis)
            
            # 验证基本字段
            assert "total_score" in score_result
            assert "performance_level" in score_result
            assert "dimension_scores" in score_result
            
            # 验证分数范围
            total_score = float(score_result["total_score"])
            assert 0 <= total_score <= 100, f"总分超出范围：{total_score}"
            
            # 验证维度分数
            dimension_scores = score_result["dimension_scores"]
            assert "action_completeness" in dimension_scores
            assert "pose_standardization" in dimension_scores
            assert "timeliness" in dimension_scores
            
            # 打印调试信息
            print(f"\n✅ AI 评分生成成功:")
            print(f"  总分：{total_score:.2f}")
            print(f"  等级：{score_result['performance_level']}")
            print(f"  动作完整性：{dimension_scores['action_completeness']['score']:.2f}")
            print(f"  姿态规范性：{dimension_scores['pose_standardization']['score']:.2f}")
            print(f"  时效性：{dimension_scores['timeliness']['score']:.2f}")
            
        except Exception as e:
            pytest.fail(f"AI 评分生成失败：{e}")
        finally:
            service.close()
    
    def test_service_initialization(self):
        """测试服务初始化（ONNX 模型加载）"""
        try:
            service = TrainingInferenceService(
                yolo_model_path="yolov8.onnx",
                yolo_conf_threshold=0.5,
                use_pose_analysis=True
            )
            
            # 验证服务已正确初始化
            assert service.yolo_detector is not None
            assert service.pose_analyzer is not None
            assert service.use_pose_analysis == True
            
            print("\n✅ 服务初始化成功:")
            print(f"  YOLO 检测器：{type(service.yolo_detector).__name__}")
            print(f"  姿态分析器：{type(service.pose_analyzer).__name__}")
            
            service.close()
            
        except Exception as e:
            pytest.fail(f"服务初始化失败：{e}")
    
    @pytest.mark.skip(reason="需要真实视频文件")
    def test_real_video_analysis(self):
        """测试真实视频分析（需要真实灭火器操作视频）"""
        # 这个测试需要真实的灭火器操作视频
        # 可以手动准备视频后运行
        
        video_path = "data/videos/real_training.mp4"
        
        if not Path(video_path).exists():
            pytest.skip("真实训练视频不存在，跳过此测试")
        
        service = TrainingInferenceService(
            yolo_model_path="yolov8.onnx",
            yolo_conf_threshold=0.5,
            use_pose_analysis=True
        )
        
        try:
            result = service.analyze_video(video_path, "fire_extinguisher")
            
            # 验证结果合理性
            assert result["video_duration"] > 0
            assert len(result["step_sequence"]) > 0
            assert result["total_detections"] > 0
            
            print(f"\n✅ 真实视频分析成功:")
            print(f"  视频时长：{result['video_duration']:.2f}秒")
            print(f"  检测到的步骤：{len(result['step_sequence'])}")
            print(f"  目标检测次数：{result['total_detections']}")
            
        except Exception as e:
            print(f"❌ 真实视频分析失败：{e}")
            pytest.fail(f"真实视频分析失败：{e}")
        finally:
            service.close()


class TestFireExtinguisherDetectorONNX:
    """测试 YOLOv8 ONNX 检测器"""
    
    def test_detector_initialization(self):
        """测试检测器初始化"""
        from app.ai.fire_extinguisher_detector import FireExtinguisherDetector
        
        try:
            detector = FireExtinguisherDetector(
                model_path="yolov8.onnx",
                conf_threshold=0.5,
                img_size=640
            )
            
            # 验证检测器已正确初始化
            assert detector.session is not None
            assert detector.input_name is not None
            assert detector.output_names is not None
            
            print(f"\n✅ ONNX 检测器初始化成功:")
            print(f"  模型路径：{detector.model_path}")
            print(f"  输入形状：{detector.input_shape}")
            print(f"  类别数：{len(detector.names)}")
            
            detector.close()
            
        except Exception as e:
            pytest.fail(f"ONNX 检测器初始化失败：{e}")
    
    def test_single_frame_detection(self):
        """测试单帧图像检测"""
        import cv2
        import numpy as np
        from app.ai.fire_extinguisher_detector import FireExtinguisherDetector
        
        # 创建一个测试图像（黑色背景）
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        try:
            detector = FireExtinguisherDetector(
                model_path="yolov8.onnx",
                conf_threshold=0.5
            )
            
            # 运行检测
            detections = detector.detect_frame(test_image)
            
            # 验证返回格式
            assert isinstance(detections, list)
            
            # 验证每个检测结果
            for det in detections:
                assert "class_id" in det
                assert "class_name" in det
                assert "confidence" in det
                assert "bbox" in det
                assert "center" in det
                
                # 验证数据类型
                assert isinstance(det["class_id"], int)
                assert isinstance(det["class_name"], str)
                assert isinstance(det["confidence"], float)
                assert isinstance(det["bbox"], list)
                assert len(det["bbox"]) == 4
            
            print(f"\n✅ 单帧检测成功:")
            print(f"  检测到 {len(detections)} 个目标")
            
            detector.close()
            
        except Exception as e:
            pytest.fail(f"单帧检测失败：{e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
