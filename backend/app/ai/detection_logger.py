"""检测日志和统计模块

记录和分析 YOLOv8 检测结果。
"""
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path


class DetectionLogger:
    """检测日志记录器
    
    记录检测结果的详细信息，用于后续分析和调试。
    """
    
    def __init__(self, log_dir: str = "data/logs"):
        """初始化检测日志记录器
        
        Args:
            log_dir: 日志目录
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前会话的日志
        self.session_logs = []
        self.session_start_time = None
        self.session_id = None
    
    def start_session(self, session_id: Optional[str] = None):
        """开始新的检测会话
        
        Args:
            session_id: 会话 ID，None 则自动生成
        """
        if session_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = f"det_{timestamp}"
        
        self.session_id = session_id
        self.session_start_time = datetime.now()
        self.session_logs = []
        
        return session_id
    
    def log_detection(
        self,
        frame_idx: int,
        detections: List[Dict[str, Any]],
        inference_time: float = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """记录单帧的检测结果
        
        Args:
            frame_idx: 帧索引
            detections: 检测结果列表
            inference_time: 推理时间（秒）
            metadata: 额外元数据
        """
        log_entry = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "frame_idx": frame_idx,
            "detection_count": len(detections),
            "detections": detections,
            "inference_time_ms": round(inference_time * 1000, 2),
            "metadata": metadata or {}
        }
        
        self.session_logs.append(log_entry)
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """获取当前会话的统计信息
        
        Returns:
            统计信息字典
        """
        if not self.session_logs:
            return {
                "session_id": self.session_id,
                "total_frames": 0,
                "total_detections": 0,
                "average_inference_time_ms": 0,
                "fps": 0,
                "detection_rate": 0,
                "class_distribution": {}
            }
        
        # 计算统计信息
        total_frames = len(self.session_logs)
        total_detections = sum(log["detection_count"] for log in self.session_logs)
        total_inference_time = sum(log["inference_time_ms"] for log in self.session_logs)
        
        avg_inference_time = total_inference_time / total_frames if total_frames > 0 else 0
        
        # 计算 FPS
        session_duration = (datetime.now() - self.session_start_time).total_seconds()
        fps = total_frames / session_duration if session_duration > 0 else 0
        
        # 类别分布
        class_distribution = {}
        frames_with_detections = 0
        
        for log in self.session_logs:
            if log["detection_count"] > 0:
                frames_with_detections += 1
            
            for det in log["detections"]:
                class_name = det.get("class_name", "unknown")
                if class_name not in class_distribution:
                    class_distribution[class_name] = 0
                class_distribution[class_name] += 1
        
        detection_rate = frames_with_detections / total_frames if total_frames > 0 else 0
        
        return {
            "session_id": self.session_id,
            "total_frames": total_frames,
            "total_detections": total_detections,
            "average_inference_time_ms": round(avg_inference_time, 2),
            "fps": round(fps, 2),
            "detection_rate": round(detection_rate, 3),
            "class_distribution": class_distribution,
            "session_duration_seconds": session_duration if session_duration else 0
        }
    
    def save_session_log(self, output_path: Optional[str] = None):
        """保存会话日志到文件
        
        Args:
            output_path: 输出文件路径，None 则自动生成
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.log_dir / f"detection_log_{timestamp}.json"
        else:
            output_path = Path(output_path)
        
        # 确保目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存完整日志
        log_data = {
            "session_info": {
                "session_id": self.session_id,
                "start_time": self.session_start_time.isoformat() if self.session_start_time else None,
                "end_time": datetime.now().isoformat(),
                "statistics": self.get_session_statistics()
            },
            "logs": self.session_logs
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        return str(output_path)
    
    def export_summary_report(self, output_path: Optional[str] = None) -> str:
        """导出摘要报告
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            报告文件路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.log_dir / f"summary_report_{timestamp}.txt"
        else:
            output_path = Path(output_path)
        
        stats = self.get_session_statistics()
        
        report_lines = [
            "=" * 60,
            "YOLOv8 检测日志摘要报告",
            "=" * 60,
            "",
            f"会话 ID: {stats['session_id']}",
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "-" * 60,
            "检测统计",
            "-" * 60,
            f"总帧数：{stats['total_frames']}",
            f"总检测数：{stats['total_detections']}",
            f"检出率：{stats['detection_rate']:.1%}",
            "",
            "-" * 60,
            "性能指标",
            "-" * 60,
            f"平均推理时间：{stats['average_inference_time_ms']:.2f} ms",
            f"处理 FPS: {stats['fps']:.2f}",
            f"会话时长：{stats['session_duration_seconds']:.2f} 秒",
            "",
            "-" * 60,
            "类别分布",
            "-" * 60,
        ]
        
        for class_name, count in sorted(stats["class_distribution"].items(), key=lambda x: x[1], reverse=True):
            percentage = count / stats["total_detections"] * 100 if stats["total_detections"] > 0 else 0
            report_lines.append(f"  {class_name}: {count} ({percentage:.1f}%)")
        
        report_lines.extend([
            "",
            "=" * 60,
            "报告结束",
            "=" * 60
        ])
        
        report_text = "\n".join(report_lines)
        
        # 保存到文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_text)
        
        return str(output_path)
    
    def clear_session(self):
        """清空当前会话"""
        self.session_logs = []
        self.session_id = None
        self.session_start_time = None


class DetectionAnalyzer:
    """检测分析器
    
    分析检测结果，提供质量评估和优化建议。
    """
    
    def __init__(self):
        """初始化检测分析器"""
        pass
    
    def analyze_detection_quality(
        self,
        detections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析检测质量
        
        Args:
            detections: 检测结果列表
            
        Returns:
            质量分析报告
        """
        if not detections:
            return {
                "quality_score": 0,
                "issues": ["未检测到任何目标"],
                "suggestions": ["检查输入图像是否包含目标物体"]
            }
        
        # 分析置信度分布
        confidences = [det["confidence"] for det in detections]
        avg_confidence = sum(confidences) / len(confidences)
        min_confidence = min(confidences)
        max_confidence = max(confidences)
        
        # 分析检测目标大小
        areas = [det.get("area", 0) for det in detections]
        avg_area = sum(areas) / len(areas)
        
        # 质量问题判断
        issues = []
        suggestions = []
        
        if avg_confidence < 0.5:
            issues.append("平均置信度较低")
            suggestions.append("降低置信度阈值或更换更准确的模型")
        
        if len(detections) == 0:
            issues.append("未检测到目标")
            suggestions.append("检查图像中是否有目标物体")
        
        # 计算质量分数
        quality_score = min(100, avg_confidence * 100)
        
        return {
            "quality_score": round(quality_score, 2),
            "average_confidence": round(avg_confidence, 3),
            "confidence_range": [round(min_confidence, 3), round(max_confidence, 3)],
            "average_target_area": round(avg_area, 2),
            "issues": issues,
            "suggestions": suggestions
        }
    
    def optimize_parameters(
        self,
        current_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """根据当前统计信息推荐优化参数
        
        Args:
            current_stats: 当前检测统计信息
            
        Returns:
            推荐的优化参数
        """
        recommendations = {}
        
        # 根据 FPS 推荐
        fps = current_stats.get("fps", 0)
        if fps < 10:
            recommendations["suggested_img_size"] = 416  # 降低分辨率
            recommendations["suggested_model"] = "yolov8n.pt"  # 使用更小模型
        elif fps < 20:
            recommendations["suggested_img_size"] = 512
            recommendations["suggested_model"] = "yolov8s.pt"
        else:
            recommendations["suggested_img_size"] = 640  # 保持当前
            recommendations["suggested_model"] = "current"
        
        # 根据检出率推荐
        detection_rate = current_stats.get("detection_rate", 0)
        if detection_rate < 0.3:
            recommendations["suggested_conf_threshold"] = 0.3  # 降低置信度阈值
        elif detection_rate < 0.6:
            recommendations["suggested_conf_threshold"] = 0.4
        else:
            recommendations["suggested_conf_threshold"] = 0.5  # 保持当前
        
        return recommendations
