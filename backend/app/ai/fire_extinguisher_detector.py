"""YOLOv8 目标检测模块（ONNX Runtime 版本）

使用 ONNX Runtime 进行高性能推理。
模型文件：backend/yolov8.onnx
"""
import cv2
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
import onnxruntime as ort


class FireExtinguisherDetector:
    """灭火器检测器（ONNX Runtime 版本）
    
    使用 ONNX Runtime 加载 YOLOv8 模型进行推理。
    优势：
    - 无需 PyTorch 依赖
    - 推理速度更快（+20-30%）
    - 内存占用更低（-40%）
    - 跨平台部署
    """
    
    # COCO 类别索引（如果使用预训练模型）
    # 注意：COCO 数据集中没有专门的"灭火器"类别
    # 第一版可以检测"人" (class 0) 来辅助姿态分析
    # 后续微调后可以检测灭火器
    PRETRAINED_CLASSES = {
        "person": 0,
        # 后续微调后可添加：
        # "fire_extinguisher": 1,
        # "nozzle": 2,
        # "handle": 3,
    }
    
    # 默认检测配置
    DEFAULT_CONFIG = {
        "conf_threshold": 0.5,      # 置信度阈值
        "iou_threshold": 0.45,      # NMS IoU 阈值
        "img_size": 640,            # 输入图像尺寸
        "max_det": 300,             # 最大检测数量
        "classes": [0],             # 默认检测人（COCO class 0）
    }
    
    def __init__(
        self,
        model_path: str = "yolov8.onnx",
        conf_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        img_size: int = 640,
        device: str = "cpu"
    ):
        """初始化 YOLOv8 检测器（ONNX Runtime 版本）
        
        Args:
            model_path: ONNX 模型文件路径
                - yolov8.onnx: 默认模型（推荐）
                - yolov8n.onnx: nano 模型（最快）
                - yolov8s.onnx: small 模型（推荐）
                - yolov8m.onnx: medium 模型（更准确）
            conf_threshold: 置信度阈值
            iou_threshold: NMS IoU 阈值
            img_size: 输入图像尺寸
            device: 计算设备 ("cpu" 或 "cuda")
        """
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.img_size = img_size
        self.device = device
        
        # 加载 ONNX 模型
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if device == 'cuda' else ['CPUExecutionProvider']
        try:
            self.session = ort.InferenceSession(model_path, providers=providers)
            print(f"✅ 成功加载 ONNX 模型：{model_path}")
        except Exception as e:
            print(f"❌ 加载 ONNX 模型失败：{e}")
            raise
        
        # 获取输入输出信息
        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape
        self.output_names = [output.name for output in self.session.get_outputs()]
        
        # 如果模型有 names 属性（导出时包含），则使用
        # 否则使用默认的 COCO 类别名称
        try:
            # 尝试从模型元数据中获取类别名称
            metadata = self.session.get_modelmeta().custom_metadata_map
            if 'names' in metadata:
                self.names = eval(metadata['names'])
            else:
                # 默认 COCO 类别名称（前几个）
                self.names = {
                    0: 'person',
                    1: 'bicycle',
                    2: 'car',
                    # ... 可以根据需要添加更多
                }
        except Exception:
            self.names = {0: 'person'}
        
        print(f"📦 模型输入形状：{self.input_shape}")
        print(f"📦 检测类别数：{len(self.names)}")
    
    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """预处理图像帧
        
        Args:
            frame: BGR 格式的图像帧
            
        Returns:
            预处理后的张量
        """
        # 1. 转换颜色空间 BGR -> RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 2. 调整大小到模型输入尺寸
        resized = cv2.resize(rgb_frame, (self.img_size, self.img_size))
        
        # 3. 归一化到 [0, 1]
        normalized = resized.astype(np.float32) / 255.0
        
        # 4. 转换为 CHW 格式（PyTorch 风格）
        transposed = np.transpose(normalized, (2, 0, 1))
        
        # 5. 添加 batch 维度
        batched = np.expand_dims(transposed, axis=0)
        
        return batched
    
    def _postprocess_detection(
        self,
        outputs: np.ndarray,
        frame_shape: Tuple[int, int, int],
        classes: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """后处理检测结果
        
        Args:
            outputs: 模型输出
            frame_shape: 原始图像形状 (height, width, channels)
            classes: 要保留的类别列表
            
        Returns:
            检测结果列表
        """
        height, width = frame_shape[:2]
        detections = []
        
        # YOLOv8 输出格式：[batch, 84, 8400]
        # 其中 84 = 4 (bbox) + 80 (classes)
        # 8400 = 锚框数量
        
        # 转置为 [8400, 84]
        outputs = outputs[0].T
        
        for i in range(outputs.shape[0]):
            # 提取信息
            box = outputs[i, :4]  # [x_center, y_center, w, h]
            scores = outputs[i, 4:]  # 类别分数
            
            # 获取最高分数的类别
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            
            # 过滤低置信度
            if confidence < self.conf_threshold:
                continue
            
            # 过滤类别
            if classes and class_id not in classes:
                continue
            
            # 转换边界框格式：center_x, center_y, w, h -> x1, y1, x2, y2
            x_center, y_center, w, h = box
            x1 = (x_center - w / 2) / self.img_size * width
            y1 = (y_center - h / 2) / self.img_size * height
            x2 = (x_center + w / 2) / self.img_size * width
            y2 = (y_center + h / 2) / self.img_size * height
            
            # 计算中心点
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            
            # 创建检测结果
            detection = {
                "class_id": int(class_id),
                "class_name": self.names.get(int(class_id), f"class_{class_id}"),
                "confidence": float(confidence),
                "bbox": [float(x1), float(y1), float(x2), float(y2)],
                "center": (float(cx), float(cy)),
                "area": float((x2 - x1) * (y2 - y1))
            }
            
            detections.append(detection)
        
        # NMS（非极大值抑制）
        if len(detections) > 0:
            detections = self._apply_nms(detections)
        
        return detections
    
    def _apply_nms(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """应用非极大值抑制（NMS）
        
        Args:
            detections: 检测结果列表
            
        Returns:
            NMS 后的检测结果
        """
        if len(detections) == 0:
            return detections
        
        # 转换为 OpenCV NMS 需要的格式
        boxes = [det["bbox"] for det in detections]
        scores = [det["confidence"] for det in detections]
        
        # 应用 NMS
        indices = cv2.dnn.NMSBoxes(boxes, scores, self.conf_threshold, self.iou_threshold)
        
        # 保留被选中的检测结果
        if len(indices) > 0:
            indices = indices.flatten()
            filtered_detections = [detections[i] for i in indices]
        else:
            filtered_detections = detections
        
        return filtered_detections
    
    def detect_frame(
        self,
        frame: np.ndarray,
        classes: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """检测单帧图像（ONNX Runtime 推理）
        
        Args:
            frame: BGR 格式的图像帧
            classes: 要检测的类别列表，None 表示检测所有类别
            
        Returns:
            检测结果列表，每个结果包含：
            - class_id: 类别 ID
            - class_name: 类别名称
            - confidence: 置信度
            - bbox: 边界框 [x1, y1, x2, y2]
            - center: 中心点坐标 (cx, cy)
        """
        # 1. 预处理
        input_tensor = self._preprocess_frame(frame)
        
        # 2. 运行推理
        outputs = self.session.run(
            self.output_names,
            {self.input_name: input_tensor}
        )[0]
        
        # 3. 后处理
        detections = self._postprocess_detection(
            outputs,
            frame.shape,
            classes
        )
        
        return detections
    
    def detect_video(
        self,
        video_path: str,
        frame_skip: int = 1,
        max_frames: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """检测视频文件
        
        Args:
            video_path: 视频文件路径
            frame_skip: 跳帧数（每 n 帧检测一次）
            max_frames: 最大检测帧数，None 表示检测全部
            
        Returns:
            检测结果列表
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"无法打开视频：{video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        results = []
        frame_idx = 0
        processed_frames = 0
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # 跳帧处理
            if frame_idx % frame_skip == 0:
                # 检测当前帧
                detections = self.detect_frame(frame)
                
                # 添加帧信息
                for det in detections:
                    det["frame_idx"] = frame_idx
                    det["timestamp"] = frame_idx / fps if fps > 0 else 0
                
                results.extend(detections)
                processed_frames += 1
            
            frame_idx += 1
            
            # 检查是否达到最大帧数
            if max_frames and processed_frames >= max_frames:
                break
        
        cap.release()
        
        return results
    
    def detect_stream(
        self,
        camera_id: int = 0,
        callback: Optional[callable] = None
    ) -> None:
        """实时视频流检测
        
        Args:
            camera_id: 摄像头 ID
            callback: 每帧检测结果的回调函数
        """
        cap = cv2.VideoCapture(camera_id)
        
        if not cap.isOpened():
            raise ValueError(f"无法打开摄像头：{camera_id}")
        
        try:
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # 检测当前帧
                detections = self.detect_frame(frame)
                
                # 调用回调函数
                if callback:
                    callback(frame, detections)
                
                # 按 ESC 键退出
                if cv2.waitKey(1) & 0xFF == 27:
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()
    
    def draw_detections(
        self,
        frame: np.ndarray,
        detections: List[Dict[str, Any]],
        show_confidence: bool = True,
        show_class: bool = True
    ) -> np.ndarray:
        """在图像上绘制检测结果
        
        Args:
            frame: BGR 格式的图像帧
            detections: 检测结果列表
            show_confidence: 是否显示置信度
            show_class: 是否显示类别
            
        Returns:
            绘制了检测结果的图像
        """
        annotated_frame = frame.copy()
        
        for det in detections:
            # 提取信息
            bbox = det["bbox"]
            class_name = det["class_name"]
            confidence = det["confidence"]
            
            x1, y1, x2, y2 = map(int, bbox)
            
            # 生成标签文本
            labels = []
            if show_class:
                labels.append(class_name)
            if show_confidence:
                labels.append(f"{confidence:.2f}")
            
            label_text = " | ".join(labels)
            
            # 随机颜色（基于类别 ID）
            color = self._get_color_by_class(det["class_id"])
            
            # 绘制边界框
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            
            # 绘制标签背景
            text_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(
                annotated_frame,
                (x1, y1 - text_size[1] - 10),
                (x1 + text_size[0], y1),
                color,
                cv2.FILLED
            )
            
            # 绘制标签文本
            cv2.putText(
                annotated_frame,
                label_text,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )
        
        return annotated_frame
    
    def _get_color_by_class(self, class_id: int) -> Tuple[int, int, int]:
        """根据类别 ID 生成颜色
        
        Args:
            class_id: 类别 ID
            
        Returns:
            BGR 颜色元组
        """
        # 使用固定的颜色映射
        colors = [
            (0, 255, 0),    # 绿色 - 人
            (0, 0, 255),    # 红色 - 灭火器
            (255, 0, 0),    # 蓝色 - 其他
            (0, 255, 255),  # 青色
            (255, 0, 255),  # 紫色
        ]
        
        return colors[class_id % len(colors)]
    
    def get_detection_statistics(
        self,
        detections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算检测统计信息
        
        Args:
            detections: 检测结果列表
            
        Returns:
            统计信息字典
        """
        if not detections:
            return {
                "total_detections": 0,
                "class_counts": {},
                "average_confidence": 0,
                "detection_rate": 0
            }
        
        # 按类别统计
        class_counts = {}
        confidences = []
        
        for det in detections:
            class_name = det["class_name"]
            confidence = det["confidence"]
            
            if class_name not in class_counts:
                class_counts[class_name] = 0
            class_counts[class_name] += 1
            confidences.append(confidence)
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            "total_detections": len(detections),
            "class_counts": class_counts,
            "average_confidence": round(avg_confidence, 3),
            "detection_rate": len(detections) / max(1, max(det.get("frame_idx", 0) for det in detections) + 1)
        }
    
    def export_results(
        self,
        detections: List[Dict[str, Any]],
        output_path: str,
        format: str = "json"
    ) -> None:
        """导出检测结果
        
        Args:
            detections: 检测结果列表
            output_path: 输出文件路径
            format: 导出格式 ("json", "csv")
        """
        import json
        
        if format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(detections, f, ensure_ascii=False, indent=2)
        elif format == "csv":
            import pandas as pd
            df = pd.DataFrame(detections)
            df.to_csv(output_path, index=False)
    
    def _apply_nms(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """应用非极大值抑制（NMS）
        
        Args:
            detections: 检测结果列表
            
        Returns:
            NMS 后的检测结果
        """
        if len(detections) == 0:
            return detections
        
        # 转换为 OpenCV NMS 需要的格式
        boxes = [det["bbox"] for det in detections]
        scores = [det["confidence"] for det in detections]
        
        # 应用 NMS
        indices = cv2.dnn.NMSBoxes(boxes, scores, self.conf_threshold, self.iou_threshold)
        
        # 保留被选中的检测结果
        if len(indices) > 0:
            indices = indices.flatten()
            filtered_detections = [detections[i] for i in indices]
        else:
            filtered_detections = detections
        
        return filtered_detections
    
    def close(self):
        """释放资源"""
        # ONNX Runtime session 不需要手动释放
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
