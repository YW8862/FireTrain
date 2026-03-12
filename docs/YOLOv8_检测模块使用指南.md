# YOLOv8 检测模块使用指南

## 快速开始

### 1. 基本使用

```python
from app.ai.fire_extinguisher_detector import FireExtinguisherDetector

# 初始化检测器（使用 nano 模型，最快）
detector = FireExtinguisherDetector(
    model_path="yolov8n.pt",
    conf_threshold=0.5,
    img_size=640,
    device="cpu"
)

try:
    # 读取图像
    import cv2
    image = cv2.imread("test.jpg")
    
    # 检测
    detections = detector.detect_frame(image)
    
    # 打印结果
    for det in detections:
        print(f"检测到：{det['class_name']}")
        print(f"置信度：{det['confidence']:.2f}")
        print(f"位置：{det['bbox']}")
        print("---")
    
    # 绘制检测结果
    annotated_image = detector.draw_detections(image, detections)
    cv2.imwrite("result.jpg", annotated_image)
    
finally:
    detector.close()
```

### 2. 视频检测

```python
# 初始化检测器
detector = FireExtinguisherDetector(model_path="yolov8s.pt")

try:
    # 检测视频文件
    results = detector.detect_video(
        video_path="training_video.mp4",
        frame_skip=5,          # 每 5 帧检测一次
        max_frames=100         # 最多检测 100 帧
    )
    
    # 统计结果
    stats = detector.get_detection_statistics(results)
    print(f"总检测数：{stats['total_detections']}")
    print(f"类别分布：{stats['class_distribution']}")
    print(f"检出率：{stats['detection_rate']:.1%}")
    
    # 导出结果
    detector.export_results(results, "detections.json", format="json")
    
finally:
    detector.close()
```

### 3. 实时流检测

```python
def on_detection(frame, detections):
    """每帧检测结果的回调"""
    annotated_frame = detector.draw_detections(frame, detections)
    cv2.imshow("Detection", annotated_frame)

detector = FireExtinguisherDetector()

try:
    # 打开摄像头进行实时检测
    detector.detect_stream(camera_id=0, callback=on_detection)
finally:
    detector.close()
```

## 日志记录与分析

### 使用 DetectionLogger

```python
from app.ai.detection_logger import DetectionLogger

# 初始化日志记录器
logger = DetectionLogger(log_dir="data/logs")

# 开始会话
session_id = logger.start_session()
print(f"会话 ID: {session_id}")

# 记录检测结果
for frame_idx, detections in enumerate(all_detections):
    logger.log_detection(
        frame_idx=frame_idx,
        detections=detections,
        inference_time=0.05  # 50ms
    )

# 获取统计信息
stats = logger.get_session_statistics()
print(f"总帧数：{stats['total_frames']}")
print(f"平均推理时间：{stats['average_inference_time_ms']:.2f}ms")
print(f"处理 FPS: {stats['fps']:.2f}")

# 保存日志
log_path = logger.save_session_log()
print(f"日志已保存到：{log_path}")

# 导出摘要报告
report_path = logger.export_summary_report()
print(f"报告已保存到：{report_path}")
```

### 质量分析

```python
from app.ai.detection_logger import DetectionAnalyzer

analyzer = DetectionAnalyzer()

# 分析检测质量
quality_report = analyzer.analyze_detection_quality(detections)

print(f"质量分数：{quality_report['quality_score']}")
print(f"平均置信度：{quality_report['average_confidence']}")
print(f"问题：{quality_report['issues']}")
print(f"建议：{quality_report['suggestions']}")

# 获取优化参数推荐
current_stats = {
    "fps": 8,
    "detection_rate": 0.3
}

recommendations = analyzer.optimize_parameters(current_stats)
print(f"推荐图像尺寸：{recommendations['suggested_img_size']}")
print(f"推荐置信度阈值：{recommendations['suggested_conf_threshold']}")
```

## API 参考

### FireExtinguisherDetector

#### 初始化参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model_path` | str | `"yolov8n.pt"` | 模型文件路径 |
| `conf_threshold` | float | `0.5` | 置信度阈值 |
| `iou_threshold` | float | `0.45` | NMS IoU 阈值 |
| `img_size` | int | `640` | 输入图像尺寸 |
| `device` | str | `"cpu"` | 计算设备 |

#### 主要方法

##### detect_frame(frame, classes=None)
检测单帧图像
- **输入**: 
  - `frame`: BGR 格式的图像帧
  - `classes`: 要检测的类别列表
- **输出**: 检测结果列表

##### detect_video(video_path, frame_skip=1, max_frames=None)
检测视频文件
- **输入**: 
  - `video_path`: 视频文件路径
  - `frame_skip`: 跳帧数
  - `max_frames`: 最大检测帧数
- **输出**: 检测结果列表

##### draw_detections(frame, detections, show_confidence=True, show_class=True)
在图像上绘制检测结果
- **输入**: 
  - `frame`: 图像帧
  - `detections`: 检测结果列表
  - `show_confidence`: 是否显示置信度
  - `show_class`: 是否显示类别
- **输出**: 绘制了检测结果的图像

##### get_detection_statistics(detections)
计算检测统计信息
- **输入**: 检测结果列表
- **输出**: 统计信息字典

### DetectionLogger

#### 主要方法

##### start_session(session_id=None)
开始新的检测会话

##### log_detection(frame_idx, detections, inference_time=0, metadata=None)
记录单帧的检测结果

##### get_session_statistics()
获取当前会话的统计信息

##### save_session_log(output_path=None)
保存会话日志到文件

##### export_summary_report(output_path=None)
导出摘要报告

## 模型选择指南

### YOLOv8 系列对比

| 模型 | 速度 | 精度 | 适用场景 |
|------|------|------|---------|
| yolov8n.pt | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 实时检测，CPU 环境 |
| yolov8s.pt | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 平衡速度和精度（推荐） |
| yolov8m.pt | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 精度要求高的场景 |
| yolov8l.pt | ⭐⭐ | ⭐⭐⭐⭐⭐ | 离线分析，GPU 环境 |
| yolov8x.pt | ⭐ | ⭐⭐⭐⭐⭐ | 最高精度要求 |

### 推荐配置

#### 实时检测（摄像头）
```python
detector = FireExtinguisherDetector(
    model_path="yolov8n.pt",      # 最快
    img_size=416,                  # 低分辨率
    conf_threshold=0.4             # 较低阈值
)
```

#### 视频分析（离线）
```python
detector = FireExtinguisherDetector(
    model_path="yolov8s.pt",      # 平衡
    img_size=640,                  # 标准分辨率
    conf_threshold=0.5             # 标准阈值
)
```

#### 高精度分析
```python
detector = FireExtinguisherDetector(
    model_path="yolov8m.pt",      # 更准确
    img_size=800,                  # 高分辨率
    conf_threshold=0.6             # 较高阈值
)
```

## 性能优化

### 1. 降低分辨率
```python
# 从 640 降到 416，速度提升约 2 倍
detector = FireExtinguisherDetector(img_size=416)
```

### 2. 抽帧处理
```python
# 每秒只检测 5 帧
results = detector.detect_video(
    video_path="video.mp4",
    frame_skip=6  # 假设视频 30fps
)
```

### 3. 批量处理
```python
# 一次性处理多张图像
images = [image1, image2, image3]
all_results = []

for image in images:
    results = detector.detect_frame(image)
    all_results.extend(results)
```

### 4. 使用 GPU（如果可用）
```python
detector = FireExtinguisherDetector(device="cuda:0")
```

## 常见问题

### Q1: 为什么检测不到灭火器？
**答**: COCO 预训练模型中没有专门的"灭火器"类别。
- 第一版可以检测"人" (class 0) 来辅助姿态分析
- 后续需要微调 YOLOv8 模型来检测灭火器

### Q2: 如何提高检测速度？
**答**: 
- 使用更小的模型（yolov8n.pt）
- 降低输入分辨率（img_size=416）
- 增加抽帧频率（frame_skip=10）
- 使用 GPU 加速

### Q3: 如何自定义检测类别？
**答**: 
```python
# 检测特定类别（COCO 类别）
detections = detector.detect_frame(
    frame,
    classes=[0, 1, 2]  # 只检测这些类别
)
```

### Q4: 置信度阈值如何设置？
**答**:
- 高阈值 (0.7-0.8): 减少误检，可能漏检
- 中阈值 (0.5-0.6): 平衡（推荐）
- 低阈值 (0.3-0.4): 减少漏检，可能误检

## 与 MediaPipe 集成

```python
from app.ai.fire_extinguisher_detector import FireExtinguisherDetector
from app.ai.pose_analyzer import PoseAnalyzer

# 初始化两个模型
detector = FireExtinguisherDetector()
pose_analyzer = PoseAnalyzer()

try:
    # 读取图像
    image = cv2.imread("training.jpg")
    
    # 同时进行检测和姿态分析
    detections = detector.detect_frame(image)
    pose_result = pose_analyzer.analyze_pose(image, "fire_extinguisher")
    
    # 综合分析
    if detections and pose_result:
        print("检测到人和完整姿态")
        
        # 可以在这里添加逻辑判断：
        # - 人是否持有灭火器
        # - 操作姿势是否正确
        # - 给出综合评分
    
finally:
    detector.close()
    pose_analyzer.close()
```

## 下一步

- 学习如何微调 YOLOv8 模型
- 集成到训练服务中进行自动评分
- 实现实时检测和反馈系统
