# MediaPipe 姿态分析使用指南

## 快速开始

### 1. 基本使用

```python
import cv2
from app.ai.pose_analyzer import PoseAnalyzer
from app.ai.pose_scoring_service import PoseScoringService

# 初始化分析器和评分器
analyzer = PoseAnalyzer()
scorer = PoseScoringService()

try:
    # 读取视频帧
    cap = cv2.VideoCapture(0)  # 或使用视频文件
    ret, frame = cap.read()
    
    if ret:
        # 分析姿态
        pose_result = analyzer.analyze_pose(frame, "fire_extinguisher")
        
        if pose_result:
            # 显示检测结果
            print(f"检测到人体关键点")
            print(f"右臂角度：{pose_result['angles'].get('right_arm', 'N/A')}°")
            print(f"左臂角度：{pose_result['angles'].get('left_arm', 'N/A')}°")
            print(f"身体角度：{pose_result['angles'].get('body', 'N/A')}°")
            
            # 在图像上绘制关键点
            annotated_frame = analyzer.draw_pose_landmarks(frame.copy(), pose_result["keypoints"])
            cv2.imwrite("pose_result.jpg", annotated_frame)
finally:
    analyzer.close()
    cap.release()
```

### 2. 姿态评分

```python
import asyncio
from decimal import Decimal

async def score_pose_demo():
    analyzer = PoseAnalyzer()
    scorer = PoseScoringService()
    
    try:
        # 从视频中提取多帧
        cap = cv2.VideoCapture("training_video.mp4")
        frames = []
        
        # 每秒抽取一帧
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % fps == 0:  # 每秒抽一帧
                frames.append(frame)
            
            frame_count += 1
            
            # 限制最多分析 30 帧
            if len(frames) >= 30:
                break
        
        cap.release()
        
        # 分析所有帧的姿态
        pose_results = []
        for frame in frames:
            result = analyzer.analyze_pose(frame, "fire_extinguisher")
            if result:
                pose_results.append(result)
        
        # 计算姿态评分
        if pose_results:
            score_result = await scorer.score_pose_analysis(
                pose_results=pose_results,
                training_type="fire_extinguisher"
            )
            
            print(f"总分：{score_result['total_score']}")
            print(f"反馈：{score_result['feedback']}")
            print(f"建议：{score_result['suggestions']}")
            
            # 查看各步骤分数
            for step_key, step_data in score_result["step_scores"].items():
                print(f"{step_data['step_name']}: {step_data['score']}分 ({step_data['level']})")
    
    finally:
        analyzer.close()

# 运行
asyncio.run(score_pose_demo())
```

### 3. 集成到训练服务

```python
from app.services.scoring_service import ScoringService

async def complete_training_with_pose_analysis(training_id: str, video_path: str):
    """使用姿态分析完成训练评分"""
    
    scoring_service = ScoringService()
    
    # 加载视频并提取帧
    cap = cv2.VideoCapture(video_path)
    frames = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append({"image": frame})
    
    cap.release()
    
    # 使用姿态分析进行评分
    result = await scoring_service.score_training(
        training_type="fire_extinguisher",
        frame_data=frames,
        use_pose_analysis=True  # 启用姿态分析
    )
    
    # 保存评分结果到数据库
    # ... (数据库操作)
    
    return result
```

## API 参考

### PoseAnalyzer

#### 初始化参数
- `model_complexity`: 模型复杂度 (0=轻量，1=标准，2=高精度)，默认 1
- `smooth_landmarks`: 是否平滑关键点，默认 True
- `min_detection_confidence`: 最小检测置信度，默认 0.5
- `min_tracking_confidence`: 最小跟踪置信度，默认 0.5

#### 主要方法

##### extract_keypoints(frame)
提取人体关键点
- **输入**: BGR 格式的图像帧
- **输出**: 关键点数据字典或 None

##### calculate_angle(point_a, point_b, point_c)
计算三点形成的角度
- **输入**: 三个点的坐标 (x, y)
- **输出**: 角度值（度），范围 0-180

##### analyze_pose(frame, pose_type)
完整姿态分析
- **输入**: BGR 格式的图像帧，姿态类型
- **输出**: 姿态分析结果字典或 None

##### draw_pose_landmarks(frame, keypoints)
在图像上绘制关键点
- **输入**: 图像帧，关键点数据
- **输出**: 绘制了关键点的图像

### PoseScoringService

#### score_pose_analysis(pose_results, training_type)
对姿态分析结果进行综合评分
- **输入**: 
  - `pose_results`: MediaPipe 姿态分析结果列表
  - `training_type`: 训练类型
- **输出**: 评分结果字典

## 评分标准

### 灭火器操作标准角度

| 动作 | 标准角度范围 | 说明 |
|------|-------------|------|
| 手臂上举 | 150°-180° | 手臂应充分上举 |
| 肘关节弯曲 | 90°-120° | 拔保险销时的肘部角度 |
| 肩部稳定性 | 0°-30° | 肩部不应过度紧张 |
| 身体直立 | 80°-100° | 保持身体正直 |
| 瞄准方向 | 0°-45° | 喷管对准火源的角度 |

### 评分等级

| 偏差范围 | 分数 | 等级 | 反馈 |
|---------|------|------|------|
| ≤10° | 100 | 优秀 | 动作标准 |
| ≤20° | 80 | 良好 | 基本正确 |
| ≤30° | 60 | 合格 | 需要改进 |
| >30° | <60 | 不合格 | 不规范 |

## 常见问题

### Q1: 为什么检测不到人体？
- 确保摄像头画面中包含完整的人体
- 光照条件要充足
- 人体不要完全被遮挡
- 调整摄像头角度和距离

### Q2: 角度计算不准确怎么办？
- 检查摄像头标定是否准确
- 确保人体正面或侧面朝向摄像头
- 避免严重遮挡
- 考虑使用更高复杂度的模型

### Q3: 如何提高检测速度？
- 降低视频分辨率（如 640x480）
- 减少抽帧频率（如每秒 5 帧）
- 使用 model_complexity=0（轻量模型）
- 使用 GPU 加速（如果可用）

### Q4: 如何自定义评分标准？
修改 `PoseAnalyzer` 中的 `STANDARD_ANGLES` 和 `ANGLE_TOLERANCE` 配置：

```python
# 自定义标准角度
analyzer.STANDARD_ANGLES["arm_raise"] = (140, 170)  # 调整手臂角度范围

# 自定义容差
analyzer.ANGLE_TOLERANCE["excellent"] = 15  # 放宽优秀标准
```

## 性能基准

### CPU 环境（Intel i7）
- 分辨率 1920x1080: ~50ms/帧
- 分辨率 1280x720: ~30ms/帧
- 分辨率 640x480: ~15ms/帧

### 优化建议
- 实时处理：使用 640x480 分辨率 + 每秒 10 帧
- 离线分析：使用 1280x720 分辨率 + 每秒 5 帧
- 高精度分析：使用 1920x1080 分辨率 + 全帧率

## 调试技巧

### 1. 可视化关键点

```python
# 绘制关键点
annotated_frame = analyzer.draw_pose_landmarks(frame.copy(), keypoints)
cv2.imshow("Pose Landmarks", annotated_frame)
cv2.waitKey(0)
```

### 2. 打印角度信息

```python
for angle_name, angle_value in pose_result["angles"].items():
    print(f"{angle_name}: {angle_value}°")
```

### 3. 检查置信度

```python
for i, visibility in enumerate(keypoints["visibility"]):
    if visibility < 0.5:
        print(f"关键点 {i} 可见度低：{visibility}")
```

## 下一步

- 尝试 D3 YOLOv8 检测接入
- 结合姿态分析和目标检测进行综合评分
- 实现实时反馈系统
