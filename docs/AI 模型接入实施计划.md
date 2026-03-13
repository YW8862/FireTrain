# FireTrain AI 模型接入实施计划

## 📋 概述

本文档提供从**当前状态**（使用模拟评分）到**完整 AI 评分系统**的实施路线图。

---

## 🎯 当前状态分析

### ✅ 已完成的工作

| 模块 | 状态 | 说明 |
|------|------|------|
| 后端架构 | ✅ 完成 | FastAPI 单体应用，分层清晰 |
| 数据库 | ✅ 完成 | SQLite/MySQL，表结构完整 |
| API 接口 | ✅ 完成 | 用户、训练、统计接口全部实现 |
| 规则引擎 | ✅ 完成 | `rule_engine.py` 实现完整评分逻辑 |
| 反馈生成 | ✅ 完成 | `feedback_generator.py` 可生成详细报告 |
| YOLO 框架 | ✅ 完成 | `fire_extinguisher_detector.py` 框架就绪 |
| MediaPipe | ✅ 完成 | `pose_analyzer.py` 基础功能可用 |
| 测试数据 | ✅ 完成 | 3 个测试账号，联调脚本就绪 |

### ❌ 未接入 AI 的部分

| 模块 | 当前实现 | 需要改进 |
|------|---------|---------|
| YOLOv8 | 使用 COCO 预训练权重 | 需要训练灭火器专用模型 |
| MediaPipe | 独立使用，未集成 | 需要与评分系统深度集成 |
| ScoringService | 使用随机数模拟评分 | 需要调用真实 AI 模型 |
| 端到端流程 | 模拟数据传递 | 需要真实视频分析 |

---

## 🚀 实施路线图

### 阶段 1: YOLOv8 模型训练（3-5 天）

#### Day 1-2: 数据准备

**任务**:
- [ ] 采集 500-1000 张灭火器操作图片
- [ ] 覆盖不同场景、光照、角度
- [ ] 使用 LabelImg 进行标注
- [ ] 组织数据集结构

**交付物**:
```
datasets/fire_extinguisher/
├── images/train/ (350-700 张)
├── images/val/ (100-200 张)
├── images/test/ (50-100 张)
├── labels/train/
├── labels/val/
└── labels/test/
```

**验收标准**:
- ✅ 图片数量 >= 500 张
- ✅ 标注质量检查通过率 > 95%
- ✅ 类别定义清晰（fire_extinguisher, person）

---

#### Day 3-4: 模型训练

**任务**:
- [ ] 安装 ultralytics 包
- [ ] 配置训练参数
- [ ] 启动训练
- [ ] 监控训练过程

**训练命令**:
```bash
cd backend
python scripts/train_yolov8.py
# 或
yolo detect train data=datasets/fire_extinguisher/data.yaml model=yolov8n.pt epochs=100
```

**预期输出**:
```
Epoch   GPU_mem   box_loss   cls_loss   Instances   Size
      1/100     0.234G      1.234      0.567         128        640: 100%|██████████| 
...
Training completed.
Best mAP50: 0.78
Best mAP50-95: 0.52
```

**交付物**:
- `runs/detect/fire_extinguisher_train/weights/best.pt`
- `runs/detect/fire_extinguisher_train/results.csv`
- TensorBoard 日志

**验收标准**:
- ✅ mAP50 >= 0.75
- ✅ mAP50-95 >= 0.50
- ✅ 单帧推理时间 < 100ms

---

#### Day 5: 模型评估与导出

**任务**:
- [ ] 在测试集上评估模型
- [ ] 导出为 ONNX 格式
- [ ] 进行量化优化（可选）

**评估命令**:
```bash
yolo val model=runs/detect/fire_extinguisher_train/weights/best.pt data=datasets/fire_extinguisher/data.yaml
```

**交付物**:
- 评估报告（mAP、precision、recall）
- ONNX 模型文件
- 性能测试报告

---

### 阶段 2: MediaPipe 增强（2-3 天）

#### Day 1-2: 增强姿态分析器

**任务**:
- [ ] 创建 `pose_analyzer_enhanced.py`
- [ ] 实现步骤识别逻辑
- [ ] 添加时序分析
- [ ] 集成角度计算和评分

**关键代码**:
```python
class EnhancedPoseAnalyzer:
    def analyze_training_video(self, video_path: str):
        # 分析整个视频
        # 识别每个步骤
        # 计算姿态得分
        pass
    
    def recognize_current_step(self, pose_result):
        # 根据姿态识别当前步骤
        pass
```

**交付物**:
- `backend/app/ai/pose_analyzer_enhanced.py`
- 单元测试 `tests/test_pose_analyzer.py`

---

#### Day 3: 测试与验证

**任务**:
- [ ] 使用测试视频验证
- [ ] 调整角度阈值
- [ ] 优化步骤识别准确率

**验收标准**:
- ✅ 步骤识别准确率 > 85%
- ✅ 姿态分析速度 > 15 FPS

---

### 阶段 3: AI 评分适配器开发（2-3 天）

#### Day 1-2: 创建适配器

**任务**:
- [ ] 创建 `ai_scoring_adapter.py`
- [ ] 整合 YOLO 和 MediaPipe 输出
- [ ] 转换为规则引擎输入格式

**关键代码**:
```python
class AIScoringAdapter:
    async def score_training(self, video_path: str):
        # 1. YOLO 检测
        yolo_detections = self.yolo_detector.detect_video(video_path)
        
        # 2. MediaPipe 姿态分析
        pose_report = self.pose_analyzer.analyze_training_video(video_path)
        
        # 3. 规则引擎评分
        evaluation = await self.rule_engine.evaluate(
            action_scores=self._process_yolo(yolo_detections),
            pose_scores=self._process_pose(pose_report)
        )
        
        # 4. 生成反馈
        feedback = self.feedback_generator.generate_feedback(evaluation)
        
        return {
            "total_score": evaluation["total_score"],
            "feedback": feedback["overall_feedback"],
            ...
        }
```

**交付物**:
- `backend/app/ai/ai_scoring_adapter.py`
- 集成测试 `tests/test_ai_integration.py`

---

#### Day 3: 集成到 ScoringService

**任务**:
- [ ] 修改 `scoring_service.py`
- [ ] 添加 `score_with_ai()` 方法
- [ ] 替换原有的模拟评分

**修改代码**:
```python
class ScoringService:
    async def score_with_ai(self, video_path: str, training_type: str):
        adapter = AIScoringAdapter(yolo_model_path="...")
        return await adapter.score_training(video_path, training_type)
```

**验收标准**:
- ✅ 能够处理真实视频并返回评分
- ✅ 评分结果合理（总分 0-100）
- ✅ 反馈内容有针对性

---

### 阶段 4: 端到端测试（2-3 天）

#### Day 1: 准备测试视频

**任务**:
- [ ] 录制 3-5 个标准训练视频
- [ ] 包含不同表现水平（优秀/良好/合格/不合格）
- [ ] 标注期望得分

**测试视频清单**:
1. `excellent_demo.mp4` - 期望得分：90-95
2. `good_demo.mp4` - 期望得分：80-85
3. `pass_demo.mp4` - 期望得分：60-70
4. `fail_demo.mp4` - 期望得分：< 60

---

#### Day 2: 端到端测试

**任务**:
- [ ] 运行完整流程测试
- [ ] 对比 AI 评分与期望得分
- [ ] 记录偏差并分析原因

**测试脚本**:
```bash
python scripts/test_end_to_end.py
```

**验收标准**:
- ✅ AI 评分与期望得分偏差 < 15 分
- ✅ 反馈建议合理
- ✅ 系统稳定性好（无崩溃）

---

#### Day 3: Bug 修复与优化

**任务**:
- [ ] 修复发现的问题
- [ ] 优化性能瓶颈
- [ ] 调整评分参数

---

### 阶段 5: 性能优化与部署（2-3 天）

#### Day 1: 性能优化

**任务**:
- [ ] YOLOv8 推理优化（跳帧、降分辨率）
- [ ] MediaPipe 优化（轻量模型）
- [ ] 并发处理优化

**优化措施**:
```python
# YOLO 优化
detector = FireExtinguisherDetector(
    img_size=416,      # 降低分辨率
    conf_threshold=0.6  # 提高阈值减少检测
)

# MediaPipe 优化
pose = mp.solutions.pose.Pose(
    model_complexity=0,  # 轻量模型
    min_detection_confidence=0.3
)
```

---

#### Day 2: 配置管理

**任务**:
- [ ] 创建 `ai_config.py`
- [ ] 添加环境变量配置
- [ ] 编写部署文档

**配置文件**:
```python
# ai_config.py
YOLO_CONFIG = {
    "model_path": "data/models/fire_extinguisher/weights/best.pt",
    "conf_threshold": 0.5,
    "img_size": 640
}

SCORING_CONFIG = {
    "use_ai_scoring": True,
    "action_weight": 0.4,
    "pose_weight": 0.4
}
```

---

#### Day 3: 文档与培训

**任务**:
- [ ] 更新 API 文档
- [ ] 编写用户使用手册
- [ ] 准备演示材料

**交付物**:
- 更新的 API 文档
- 用户使用手册
- 演示 PPT

---

## 📊 总体时间表

| 阶段 | 任务 | 天数 | 开始日期 | 结束日期 |
|------|------|------|----------|----------|
| 阶段 1 | YOLOv8 训练 | 5 | Day 1 | Day 5 |
| 阶段 2 | MediaPipe 增强 | 3 | Day 6 | Day 8 |
| 阶段 3 | AI 适配器开发 | 3 | Day 9 | Day 11 |
| 阶段 4 | 端到端测试 | 3 | Day 12 | Day 14 |
| 阶段 5 | 优化部署 | 3 | Day 15 | Day 17 |

**总计**: 17 个工作日（约 3-4 周）

---

## ✅ 验收标准

### 功能验收

- [ ] **YOLOv8 检测**
  - mAP50 >= 0.75
  - 单帧推理 < 100ms
  - 支持灭火器、人检测

- [ ] **MediaPipe 姿态分析**
  - 步骤识别准确率 > 85%
  - 分析速度 > 15 FPS
  - 角度误差 < 10 度

- [ ] **AI 评分系统**
  - 评分范围 0-100
  - 与期望得分偏差 < 15 分
  - 反馈建议有针对性

- [ ] **端到端流程**
  - 视频上传 → AI 分析 → 评分返回 < 60 秒
  - 系统稳定无崩溃
  - 错误处理完善

### 性能验收

| 指标 | 目标值 | 实测值 | 状态 |
|------|--------|--------|------|
| 视频分析速度 | < 30 秒/分钟视频 | - | ⏳ |
| 并发支持 | >= 5 用户同时使用 | - | ⏳ |
| 内存占用 | < 2GB | - | ⏳ |
| CPU 占用 | < 80% | - | ⏳ |

---

## 🛠️ 资源需求

### 硬件资源

| 资源 | 最低配置 | 推荐配置 |
|------|----------|----------|
| GPU | 无（CPU 推理） | NVIDIA GTX 1060+ |
| 内存 | 8GB | 16GB |
| 存储 | 50GB | 100GB SSD |

### 软件资源

- Python 3.9+
- ultralytics (YOLOv8)
- mediapipe
- opencv-python
- torch (可选，GPU 支持)

### 数据资源

- 灭火器操作图片：500-1000 张
- 训练视频：10-20 个
- 测试视频：3-5 个（不同水平）

---

## 📝 交付清单

### 代码交付

- [ ] `backend/app/ai/pose_analyzer_enhanced.py` - 增强姿态分析器
- [ ] `backend/app/ai/ai_scoring_adapter.py` - AI 评分适配器
- [ ] `backend/app/services/scoring_service.py` - 修改后的评分服务
- [ ] `backend/scripts/train_yolov8.py` - YOLO 训练脚本
- [ ] `backend/tests/test_ai_integration.py` - AI 集成测试

### 模型交付

- [ ] `data/models/fire_extinguisher/weights/best.pt` - 训练好的 YOLO 模型
- [ ] `data/models/fire_extinguisher/weights/best.onnx` - ONNX 格式模型
- [ ] `datasets/fire_extinguisher/` - 完整数据集

### 文档交付

- [ ] `docs/AI 模型训练与接入指南.md` - 完整技术文档
- [ ] `docs/AI 模型接入实施计划.md` - 本实施计划
- [ ] `scripts/README_AI_TESTING.md` - 测试说明

---

## 🔍 风险与应对

### 风险 1: YOLOv8 训练效果不佳

**可能性**: 中  
**影响**: 高  
**应对措施**:
- 增加训练数据量
- 调整数据增强策略
- 使用更大模型（yolov8s/m）
- 延长训练轮数

---

### 风险 2: MediaPipe 姿态识别不稳定

**可能性**: 中  
**影响**: 中  
**应对措施**:
- 改善拍摄环境（光照、背景）
- 调整置信度阈值
- 使用平滑处理
- 结合 YOLO 检测结果辅助判断

---

### 风险 3: AI 评分与预期偏差大

**可能性**: 高  
**影响**: 中  
**应对措施**:
- 收集更多标定数据
- 调整评分权重配置
- 校准阈值参数
- 引入人工复核机制

---

### 风险 4: 性能不达标

**可能性**: 低  
**影响**: 高  
**应对措施**:
- 使用更小模型
- 降低输入分辨率
- 跳帧处理
- 使用 GPU 加速

---

## 📞 支持与联系

**技术支持**:
- YOLOv8 文档：https://docs.ultralytics.com/
- MediaPipe 文档：https://google.github.io/mediapipe/
- 项目 Issues: GitHub Issues

**团队联系**:
- 开发负责人：[姓名]
- AI 负责人：[姓名]
- 联系方式：[邮箱/电话]

---

**文档版本**: v1.0  
**创建日期**: 2026-03-13  
**最后更新**: 2026-03-13  
**维护者**: FireTrain 开发团队
