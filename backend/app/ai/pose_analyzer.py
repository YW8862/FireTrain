"""MediaPipe 姿态分析模块

使用 MediaPipe Pose 进行人体关键点检测，计算姿态角度并评分。
"""
import cv2
import mediapipe as mp
import numpy as np
from typing import Any, Dict, List, Optional, Tuple


class PoseAnalyzer:
    """姿态分析器
    
    使用 MediaPipe Pose 进行人体关键点检测和角度计算。
    """
    
    # MediaPipe 关键点索引
    KEYPOINT_INDICES = {
        "nose": 0,
        "left_shoulder": 11,
        "right_shoulder": 12,
        "left_elbow": 13,
        "right_elbow": 14,
        "left_wrist": 15,
        "right_wrist": 16,
        "left_hip": 23,
        "right_hip": 24,
        "left_knee": 25,
        "right_knee": 26,
        "left_ankle": 27,
        "right_ankle": 28,
    }
    
    # 标准角度范围（灭火器操作）
    STANDARD_ANGLES = {
        "arm_raise": (150, 180),      # 手臂上举角度范围（度）
        "elbow_flex": (90, 120),       # 肘关节弯曲角度
        "shoulder_stable": (0, 30),    # 肩部稳定性角度
        "body_upright": (80, 100),     # 身体直立角度
        "aim_direction": (0, 45),      # 瞄准方向角度
    }
    
    # 角度容差（度）
    ANGLE_TOLERANCE = {
        "excellent": 10,    # 优秀级别容差
        "good": 20,         # 良好级别容差
        "pass": 30,         # 合格级别容差
    }
    
    def __init__(
        self,
        model_complexity: int = 1,
        smooth_landmarks: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5
    ):
        """初始化姿态分析器
        
        Args:
            model_complexity: 模型复杂度 (0=轻量，1=标准，2=高精度)
            smooth_landmarks: 是否平滑关键点
            min_detection_confidence: 最小检测置信度
            min_tracking_confidence: 最小跟踪置信度
        """
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            enable_segmentation=False,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
    
    def extract_keypoints(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """提取人体关键点
        
        Args:
            frame: BGR 格式的图像帧
            
        Returns:
            关键点数据字典，包含：
            - landmarks: 33 个关键点的坐标列表
            - visibility: 每个关键点的可见度
            - normalized: 是否归一化坐标
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)
        
        if not results.pose_landmarks:
            return None
        
        landmarks_data = {
            "landmarks": [],
            "visibility": [],
            "normalized": True
        }
        
        for landmark in results.pose_landmarks.landmark:
            landmarks_data["landmarks"].append({
                "x": landmark.x,
                "y": landmark.y,
                "z": landmark.z
            })
            landmarks_data["visibility"].append(landmark.visibility)
        
        return landmarks_data
    
    def calculate_angle(
        self,
        point_a: Tuple[float, float],
        point_b: Tuple[float, float],
        point_c: Tuple[float, float]
    ) -> float:
        """计算三点形成的角度
        
        Args:
            point_a: 第一个点 (x, y)
            point_b: 顶点 (x, y)
            point_c: 第三个点 (x, y)
            
        Returns:
            角度值（度），范围 0-180
        """
        a = np.array(point_a, dtype=np.float64)
        b = np.array(point_b, dtype=np.float64)
        c = np.array(point_c, dtype=np.float64)
        
        ba = a - b
        bc = c - b
        
        # 防止除零错误
        norm_ba = np.linalg.norm(ba)
        norm_bc = np.linalg.norm(bc)
        
        if norm_ba == 0 or norm_bc == 0:
            return 90.0  # 默认返回直角
        
        cosine_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
        angle = np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))
        
        return angle
    
    def calculate_arm_angle(
        self,
        landmarks: List[Dict[str, float]],
        side: str = "right"
    ) -> Optional[float]:
        """计算手臂角度（肩 - 肘 - 腕）
        
        Args:
            landmarks: 关键点列表
            side: 哪一侧的手臂 ("left" 或 "right")
            
        Returns:
            手臂角度（度）
        """
        if side == "right":
            shoulder_idx = self.KEYPOINT_INDICES["right_shoulder"]
            elbow_idx = self.KEYPOINT_INDICES["right_elbow"]
            wrist_idx = self.KEYPOINT_INDICES["right_wrist"]
        else:
            shoulder_idx = self.KEYPOINT_INDICES["left_shoulder"]
            elbow_idx = self.KEYPOINT_INDICES["left_elbow"]
            wrist_idx = self.KEYPOINT_INDICES["left_wrist"]
        
        shoulder = (landmarks[shoulder_idx]["x"], landmarks[shoulder_idx]["y"])
        elbow = (landmarks[elbow_idx]["x"], landmarks[elbow_idx]["y"])
        wrist = (landmarks[wrist_idx]["x"], landmarks[wrist_idx]["y"])
        
        return self.calculate_angle(shoulder, elbow, wrist)
    
    def calculate_body_angle(
        self,
        landmarks: List[Dict[str, float]]
    ) -> Optional[float]:
        """计算身体直立角度（肩 - 髋 - 垂直线）
        
        Args:
            landmarks: 关键点列表
            
        Returns:
            身体角度（度）
        """
        # 取左右肩的中点
        left_shoulder = landmarks[self.KEYPOINT_INDICES["left_shoulder"]]
        right_shoulder = landmarks[self.KEYPOINT_INDICES["right_shoulder"]]
        shoulder_mid = (
            (left_shoulder["x"] + right_shoulder["x"]) / 2,
            (left_shoulder["y"] + right_shoulder["y"]) / 2
        )
        
        # 取左右髋的中点
        left_hip = landmarks[self.KEYPOINT_INDICES["left_hip"]]
        right_hip = landmarks[self.KEYPOINT_INDICES["right_hip"]]
        hip_mid = (
            (left_hip["x"] + right_hip["x"]) / 2,
            (left_hip["y"] + right_hip["y"]) / 2
        )
        
        # 计算肩髋连线与垂直线的夹角
        vertical_point = (shoulder_mid[0], hip_mid[1])
        return self.calculate_angle(vertical_point, shoulder_mid, hip_mid)
    
    def score_pose_angle(
        self,
        actual_angle: float,
        standard_range: Tuple[int, int],
        tolerance_map: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """对姿态角度进行评分
        
        Args:
            actual_angle: 实际角度
            standard_range: 标准角度范围 (min, max)
            tolerance_map: 容差映射
            
        Returns:
            评分结果字典
        """
        if tolerance_map is None:
            tolerance_map = self.ANGLE_TOLERANCE
        
        standard_min, standard_max = standard_range
        standard_mid = (standard_min + standard_max) / 2
        
        # 计算偏差
        if standard_min <= actual_angle <= standard_max:
            deviation = 0
        elif actual_angle < standard_min:
            deviation = standard_min - actual_angle
        else:
            deviation = actual_angle - standard_max
        
        # 根据偏差评分
        if deviation <= tolerance_map["excellent"]:
            score = 100
            level = "优秀"
            feedback = "动作标准"
        elif deviation <= tolerance_map["good"]:
            score = 80
            level = "良好"
            feedback = "基本正确，注意细节"
        elif deviation <= tolerance_map["pass"]:
            score = 60
            level = "合格"
            feedback = "需要改进"
        else:
            score = max(0, 100 - deviation * 2)
            level = "不合格"
            feedback = "动作不规范，需重新学习"
        
        return {
            "actual_angle": round(actual_angle, 2),
            "standard_range": list(standard_range),
            "deviation": round(deviation, 2),
            "score": score,
            "level": level,
            "feedback": feedback
        }
    
    def analyze_pose(
        self,
        frame: np.ndarray,
        pose_type: str = "fire_extinguisher"
    ) -> Optional[Dict[str, Any]]:
        """分析姿态并返回详细结果
        
        Args:
            frame: BGR 格式的图像帧
            pose_type: 姿态类型
            
        Returns:
            姿态分析结果字典
        """
        keypoints = self.extract_keypoints(frame)
        
        if not keypoints or not keypoints["landmarks"]:
            return None
        
        landmarks = keypoints["landmarks"]
        
        # 计算各个关键角度
        result = {
            "keypoints": keypoints,
            "angles": {},
            "scores": {}
        }
        
        # 计算并评分右臂角度
        right_arm_angle = self.calculate_arm_angle(landmarks, "right")
        if right_arm_angle:
            result["angles"]["right_arm"] = right_arm_angle
            result["scores"]["right_arm"] = self.score_pose_angle(
                right_arm_angle,
                self.STANDARD_ANGLES["arm_raise"]
            )
        
        # 计算并评分左臂角度
        left_arm_angle = self.calculate_arm_angle(landmarks, "left")
        if left_arm_angle:
            result["angles"]["left_arm"] = left_arm_angle
            result["scores"]["left_arm"] = self.score_pose_angle(
                left_arm_angle,
                self.STANDARD_ANGLES["arm_raise"]
            )
        
        # 计算并评分身体角度
        body_angle = self.calculate_body_angle(landmarks)
        if body_angle:
            result["angles"]["body"] = body_angle
            result["scores"]["body"] = self.score_pose_angle(
                body_angle,
                self.STANDARD_ANGLES["body_upright"]
            )
        
        return result
    
    def draw_pose_landmarks(
        self,
        frame: np.ndarray,
        keypoints: Dict[str, Any]
    ) -> np.ndarray:
        """在图像上绘制姿态关键点
        
        Args:
            frame: BGR 格式的图像帧
            keypoints: 关键点数据
            
        Returns:
            绘制了关键点的图像
        """
        if not keypoints or not keypoints["landmarks"]:
            return frame
        
        # 创建用于绘图的 LandmarkList
        pose_landmarks = mp.solutions.pose.PoseLandmarkList()
        for lm_data in keypoints["landmarks"]:
            pose_landmarks.append(
                mp.solutions.pose.PoseLandmark(
                    x=lm_data["x"],
                    y=lm_data["y"],
                    z=lm_data.get("z", 0),
                    visibility=1.0
                )
            )
        
        # 绘制关键点
        self.mp_drawing.draw_landmarks(
            frame,
            pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
        )
        
        return frame
    
    def close(self):
        """释放资源"""
        self.pose.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
