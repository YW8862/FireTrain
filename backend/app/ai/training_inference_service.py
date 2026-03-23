"""训练推理服务

整合 YOLOv8 检测和 MediaPipe 姿态分析，对训练视频进行完整分析。
"""
import cv2
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from decimal import Decimal

from app.ai.fire_extinguisher_detector import FireExtinguisherDetector
from app.ai.pose_analyzer import PoseAnalyzer


class TrainingInferenceService:
    """训练推理服务
    
    对训练视频进行完整的 AI 分析，包括：
    1. YOLOv8 目标检测（灭火器、人）
    2. MediaPipe 姿态分析（关键角度）
    3. 动作识别（6 个标准步骤）
    4. 时序分析（各步骤用时）
    """
    
    # 灭火器操作 6 个标准步骤
    STANDARD_STEPS = [
        "准备阶段",
        "提灭火器",
        "拔保险销",
        "握喷管",
        "瞄准火源",
        "压把手"
    ]
    
    def __init__(
        self,
        yolo_model_path: str = "yolov8n.pt",
        yolo_conf_threshold: float = 0.5,
        use_pose_analysis: bool = True
    ):
        """初始化推理服务
        
        Args:
            yolo_model_path: YOLO 模型路径
            yolo_conf_threshold: YOLO 置信度阈值
            use_pose_analysis: 是否启用姿态分析
        """
        self.yolo_detector = FireExtinguisherDetector(
            model_path=yolo_model_path,
            conf_threshold=yolo_conf_threshold
        )
        self.use_pose_analysis = use_pose_analysis
        self.pose_analyzer = PoseAnalyzer() if use_pose_analysis else None
    
    def analyze_video(
        self,
        video_path: str,
        training_type: str = "fire_extinguisher"
    ) -> Dict[str, Any]:
        """分析训练视频
        
        Args:
            video_path: 视频文件路径
            training_type: 训练类型
            
        Returns:
            分析结果字典
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"无法打开视频：{video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        # 存储所有帧的分析结果
        frame_results = []
        all_detections = []
        all_pose_results = []
        
        frame_idx = 0
        processed_frames = 0
        
        # 每隔几帧处理一次（提高速度）
        frame_skip = 1 if total_frames < 300 else 2
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # 跳帧处理
            if frame_idx % frame_skip == 0:
                timestamp = frame_idx / fps if fps > 0 else 0
                
                # 1. YOLO 目标检测
                detections = self.yolo_detector.detect_frame(frame)
                all_detections.extend(detections)
                
                # 2. MediaPipe 姿态分析
                pose_result = None
                if self.use_pose_analysis:
                    pose_result = self.pose_analyzer.analyze_pose(frame, training_type)
                    if pose_result:
                        all_pose_results.append(pose_result)
                
                # 3. 保存帧结果
                frame_results.append({
                    "frame_idx": frame_idx,
                    "timestamp": timestamp,
                    "detections": detections,
                    "pose_result": pose_result
                })
                
                processed_frames += 1
            
            frame_idx += 1
        
        cap.release()
        
        # 4. 识别动作步骤
        step_sequence = self._recognize_action_sequence(frame_results)
        
        # 5. 计算各步骤用时
        step_times = self._calculate_step_times(frame_results, step_sequence, fps)
        
        # 6. 生成分析摘要
        analysis_summary = {
            "video_duration": duration,
            "total_frames": total_frames,
            "processed_frames": processed_frames,
            "fps": fps,
            "step_sequence": step_sequence,
            "step_times": step_times,
            "total_detections": len(all_detections),
            "pose_frame_count": len(all_pose_results),
            "frame_results": frame_results,  # 详细帧数据
            "all_detections": all_detections,
            "all_pose_results": all_pose_results
        }
        
        return analysis_summary
    
    def _recognize_action_sequence(
        self,
        frame_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """识别动作序列（6 个标准步骤）
        
        基于 YOLO 检测结果和 MediaPipe 姿态，识别每个步骤的执行情况。
        
        Args:
            frame_results: 所有帧的分析结果
            
        Returns:
            步骤序列列表
        """
        step_sequence = []
        current_step_idx = 0
        
        for i, frame_data in enumerate(frame_results):
            detections = frame_data["detections"]
            pose_result = frame_data["pose_result"]
            timestamp = frame_data["timestamp"]
            
            # 简化的步骤识别逻辑（后续可以改进）
            # 基于时间和检测结果判断步骤
            
            detected_actions = set()
            for det in detections:
                class_name = det["class_name"]
                if class_name == "person":
                    detected_actions.add("person_detected")
                # 如果训练了灭火器检测，可以添加：
                # elif class_name == "fire_extinguisher":
                #     detected_actions.add("extinguisher_detected")
            
            # 基于姿态判断步骤
            if pose_result and "angles" in pose_result:
                angles = pose_result["angles"]
                
                # 示例：手臂角度判断
                right_arm_angle = angles.get("right_arm", 180)
                
                # 简化的规则：根据角度范围判断步骤
                if 150 <= right_arm_angle <= 180:
                    detected_actions.add("arm_raised")
                elif 90 <= right_arm_angle < 150:
                    detected_actions.add("arm_bent")
            
            # 判断当前步骤
            if current_step_idx < len(self.STANDARD_STEPS):
                step_info = {
                    "step_index": current_step_idx + 1,
                    "step_name": self.STANDARD_STEPS[current_step_idx],
                    "start_timestamp": timestamp,
                    "end_timestamp": timestamp,
                    "detected_actions": list(detected_actions),
                    "is_completed": True  # 简化版，假设都完成了
                }
                
                # 如果是第一步，记录开始时间
                if not step_sequence:
                    step_info["start_timestamp"] = timestamp
                
                # 每 5 秒切换一步（简化逻辑）
                if step_sequence:
                    prev_step = step_sequence[-1]
                    time_diff = timestamp - prev_step["start_timestamp"]
                    
                    if time_diff > 5:  # 5 秒后切换到下一步
                        prev_step["end_timestamp"] = timestamp
                        current_step_idx = min(current_step_idx + 1, len(self.STANDARD_STEPS) - 1)
                        step_info["start_timestamp"] = timestamp
                
                step_sequence.append(step_info)
        
        # 确保最后一步有结束时间
        if step_sequence and frame_results:
            step_sequence[-1]["end_timestamp"] = frame_results[-1]["timestamp"]
        
        return step_sequence
    
    def _calculate_step_times(
        self,
        frame_results: List[Dict[str, Any]],
        step_sequence: List[Dict[str, Any]],
        fps: float
    ) -> Dict[str, Decimal]:
        """计算各步骤用时
        
        Args:
            frame_results: 帧结果列表
            step_sequence: 步骤序列
            fps: 视频 FPS
            
        Returns:
            各步骤用时的字典
        """
        step_times = {}
        
        for step in step_sequence:
            step_key = f"step{step['step_index']}"
            start_time = step["start_timestamp"]
            end_time = step["end_timestamp"]
            duration = Decimal(str(round(end_time - start_time, 2)))
            step_times[step_key] = duration
        
        # 计算总时间
        if frame_results:
            total_time = Decimal(str(round(frame_results[-1]["timestamp"], 2)))
            step_times["total"] = total_time
        
        return step_times
    
    def generate_ai_scores(
        self,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """基于 AI 分析结果生成评分
        
        调用 RuleEngine 综合评分
        
        Args:
            analysis_result: AI 分析结果
            
        Returns:
            评分结果字典
        """
        from app.ai.rule_engine import RuleEngine
        
        rule_engine = RuleEngine()
        
        # 1. 准备动作完整性分数（基于步骤完成情况）
        action_scores = {"step_scores": {}}
        for step in analysis_result["step_sequence"]:
            step_key = f"step{step['step_index']}"
            action_scores["step_scores"][step_key] = {
                "step_name": step["step_name"],
                "score": 100 if step["is_completed"] else 0,
                "is_completed": step["is_completed"],
                "duration": float(analysis_result["step_times"].get(step_key, 0))
            }
        
        # 2. 准备姿态规范性分数（基于 MediaPipe）
        pose_scores = {"step_scores": {}, "frame_count": analysis_result["pose_frame_count"]}
        
        if analysis_result["all_pose_results"]:
            # 计算平均角度
            angle_sums = {}
            angle_counts = {}
            
            for pose_result in analysis_result["all_pose_results"]:
                if "angles" in pose_result:
                    for angle_name, angle_value in pose_result["angles"].items():
                        if angle_name not in angle_sums:
                            angle_sums[angle_name] = 0
                            angle_counts[angle_name] = 0
                        angle_sums[angle_name] += angle_value
                        angle_counts[angle_name] += 1
            
            avg_angles = {}
            for angle_name in angle_sums:
                avg_angles[angle_name] = round(
                    angle_sums[angle_name] / angle_counts[angle_name],
                    2
                )
            
            pose_scores["average_angles"] = avg_angles
            
            # 为每个步骤生成姿态分数
            for i, step in enumerate(analysis_result["step_sequence"]):
                step_key = f"step{step['step_index']}"
                pose_scores["step_scores"][step_key] = {
                    "step_name": step["step_name"],
                    "score": 85,  # 简化版，给固定分数
                    "weight": 0.15,
                    "angles": avg_angles
                }
        
        # 3. 获取总用时
        total_duration = analysis_result["step_times"].get("total")
        
        # 4. 调用规则引擎综合评分
        evaluation_result = rule_engine.evaluate(
            action_scores=action_scores,
            pose_scores=pose_scores,
            duration_seconds=total_duration,
            step_times=analysis_result["step_times"]
        )
        
        return evaluation_result
    
    def close(self):
        """释放资源"""
        if self.pose_analyzer:
            self.pose_analyzer.close()
        self.yolo_detector.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
