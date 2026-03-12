"""测试 YOLOv8 检测模块"""
import pytest
import numpy as np
from pathlib import Path


class TestFireExtinguisherDetector:
    """测试灭火器检测器"""
    
    @pytest.fixture
    def detector(self):
        """创建检测器实例（使用 nano 模型）"""
        from app.ai.fire_extinguisher_detector import FireExtinguisherDetector
        
        return FireExtinguisherDetector(
            model_path="yolov8n.pt",
            conf_threshold=0.5,
            img_size=640,
            device="cpu"
        )
    
    def test_detector_initialization(self, detector):
        """测试检测器初始化"""
        assert detector.model is not None
        assert detector.conf_threshold == 0.5
        assert detector.img_size == 640
    
    def test_detect_frame_blank_image(self, detector):
        """测试空白图像的检测"""
        # 创建空白图像
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        detections = detector.detect_frame(blank_frame)
        
        # 空白图像应该没有或很少检测到目标
        assert isinstance(detections, list)
    
    def test_detect_frame_random_image(self, detector):
        """测试随机图像的检测"""
        # 创建随机图像
        random_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        detections = detector.detect_frame(random_frame)
        
        # 验证返回结构
        assert isinstance(detections, list)
        
        if detections:
            for det in detections:
                assert "class_id" in det
                assert "class_name" in det
                assert "confidence" in det
                assert "bbox" in det
                assert "center" in det
                
                # 验证数据类型
                assert 0 <= det["confidence"] <= 1
                assert len(det["bbox"]) == 4
                assert len(det["center"]) == 2
    
    def test_draw_detections(self, detector):
        """测试绘制检测结果"""
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # 模拟检测结果
        mock_detections = [
            {
                "class_id": 0,
                "class_name": "person",
                "confidence": 0.85,
                "bbox": [100, 100, 200, 300],
                "center": (150, 200)
            }
        ]
        
        annotated_frame = detector.draw_detections(frame, mock_detections)
        
        # 验证返回的是图像
        assert isinstance(annotated_frame, np.ndarray)
        assert annotated_frame.shape == frame.shape
    
    def test_get_detection_statistics(self, detector):
        """测试检测统计信息计算"""
        mock_detections = [
            {
                "class_id": 0,
                "class_name": "person",
                "confidence": 0.85,
                "frame_idx": 0
            },
            {
                "class_id": 0,
                "class_name": "person",
                "confidence": 0.90,
                "frame_idx": 1
            },
            {
                "class_id": 0,
                "class_name": "person",
                "confidence": 0.75,
                "frame_idx": 2
            }
        ]
        
        stats = detector.get_detection_statistics(mock_detections)
        
        assert stats["total_detections"] == 3
        assert "person" in stats["class_counts"]
        assert stats["class_counts"]["person"] == 3
        assert 0.75 <= stats["average_confidence"] <= 0.90
    
    def test_export_results_json(self, detector, tmp_path):
        """测试导出 JSON 结果"""
        mock_detections = [
            {
                "class_id": 0,
                "class_name": "person",
                "confidence": 0.85,
                "bbox": [100, 100, 200, 300]
            }
        ]
        
        output_path = tmp_path / "detections.json"
        detector.export_results(mock_detections, str(output_path), format="json")
        
        # 验证文件存在
        assert output_path.exists()
        
        # 验证可以读取
        import json
        with open(output_path, "r") as f:
            data = json.load(f)
            assert len(data) == 1


class TestDetectionLogger:
    """测试检测日志记录器"""
    
    @pytest.fixture
    def logger(self, tmp_path):
        """创建日志记录器实例"""
        from app.ai.detection_logger import DetectionLogger
        
        return DetectionLogger(log_dir=str(tmp_path))
    
    def test_start_session(self, logger):
        """测试开始会话"""
        session_id = logger.start_session("test_session_001")
        
        assert session_id == "test_session_001"
        assert logger.session_id == "test_session_001"
        assert logger.session_logs == []
    
    def test_log_detection(self, logger):
        """测试记录检测结果"""
        logger.start_session()
        
        mock_detections = [
            {
                "class_id": 0,
                "class_name": "person",
                "confidence": 0.85
            }
        ]
        
        logger.log_detection(
            frame_idx=0,
            detections=mock_detections,
            inference_time=0.05
        )
        
        assert len(logger.session_logs) == 1
        log_entry = logger.session_logs[0]
        assert log_entry["frame_idx"] == 0
        assert log_entry["detection_count"] == 1
        assert log_entry["inference_time_ms"] == 50
    
    def test_get_session_statistics(self, logger):
        """测试获取会话统计信息"""
        logger.start_session()
        
        # 添加一些模拟数据
        for i in range(10):
            logger.log_detection(
                frame_idx=i,
                detections=[{"class_name": "person", "confidence": 0.8}],
                inference_time=0.05
            )
        
        stats = logger.get_session_statistics()
        
        assert stats["total_frames"] == 10
        assert stats["total_detections"] == 10
        assert stats["average_inference_time_ms"] == 50
    
    def test_save_session_log(self, logger, tmp_path):
        """测试保存会话日志"""
        logger.start_session()
        
        logger.log_detection(
            frame_idx=0,
            detections=[],
            inference_time=0.05
        )
        
        output_path = logger.save_session_log(str(tmp_path / "test_log.json"))
        
        # 验证文件存在
        assert Path(output_path).exists()
    
    def test_export_summary_report(self, logger, tmp_path):
        """测试导出摘要报告"""
        logger.start_session()
        
        # 添加一些数据
        for i in range(5):
            logger.log_detection(
                frame_idx=i,
                detections=[{"class_name": "person", "confidence": 0.8 + i * 0.02}],
                inference_time=0.05
            )
        
        report_path = logger.export_summary_report(str(tmp_path / "report.txt"))
        
        # 验证文件存在
        assert Path(report_path).exists()
        
        # 验证报告内容
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "YOLOv8 检测日志摘要报告" in content
            assert "总帧数：5" in content


class TestDetectionAnalyzer:
    """测试检测分析器"""
    
    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        from app.ai.detection_logger import DetectionAnalyzer
        
        return DetectionAnalyzer()
    
    def test_analyze_detection_quality_empty(self, analyzer):
        """测试空检测的质量分析"""
        result = analyzer.analyze_detection_quality([])
        
        assert result["quality_score"] == 0
        assert "未检测到任何目标" in result["issues"]
    
    def test_analyze_detection_quality_good(self, analyzer):
        """测试高质量检测的分析"""
        mock_detections = [
            {
                "confidence": 0.95,
                "area": 10000
            },
            {
                "confidence": 0.90,
                "area": 8000
            }
        ]
        
        result = analyzer.analyze_detection_quality(mock_detections)
        
        assert result["quality_score"] > 80
        assert result["average_confidence"] > 0.9
    
    def test_optimize_parameters_slow_fps(self, analyzer):
        """测试低 FPS 时的优化建议"""
        current_stats = {
            "fps": 5,
            "detection_rate": 0.2
        }
        
        recommendations = analyzer.optimize_parameters(current_stats)
        
        assert recommendations["suggested_img_size"] == 416
        assert recommendations["suggested_conf_threshold"] == 0.3
    
    def test_optimize_parameters_good_performance(self, analyzer):
        """测试良好性能时的优化建议"""
        current_stats = {
            "fps": 25,
            "detection_rate": 0.8
        }
        
        recommendations = analyzer.optimize_parameters(current_stats)
        
        assert recommendations["suggested_img_size"] == 640
        assert recommendations["suggested_conf_threshold"] == 0.5


class TestIntegration:
    """集成测试"""
    
    def test_detector_with_logger_integration(self, tmp_path):
        """测试检测器和日志记录器的集成"""
        from app.ai.fire_extinguisher_detector import FireExtinguisherDetector
        from app.ai.detection_logger import DetectionLogger
        
        detector = FireExtinguisherDetector(model_path="yolov8n.pt")
        logger = DetectionLogger(log_dir=str(tmp_path))
        
        try:
            # 开始会话
            logger.start_session("integration_test")
            
            # 创建测试图像
            test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            # 检测并记录
            start_time = time.time()
            detections = detector.detect_frame(test_frame)
            inference_time = time.time() - start_time
            
            logger.log_detection(
                frame_idx=0,
                detections=detections,
                inference_time=inference_time
            )
            
            # 获取统计信息
            stats = logger.get_session_statistics()
            
            assert stats["total_frames"] == 1
            assert "total_detections" in stats
            
        finally:
            detector.close()


# 导入 time 模块用于集成测试
import time
