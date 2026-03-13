# FireTrain AI 模型训练与接入指南（下）

## 4. 评分规则引擎接入

### 4.1 规则引擎集成

当前的 `rule_engine.py` 已经实现了完整的评分逻辑，需要做的是将 YOLOv8 和 MediaPipe 的输出转换为规则引擎的输入格式。

#### 4.1.1 创建 AI 评分适配器

创建 `backend/app/ai/ai scoring_adapter.py`:

```python
"""AI 评分适配器 - 将 YOLO 和 MediaPipe 结果转换为规则引擎输入"""

from typing import Any, Dict, List, Optional
from decimal import Decimal
from app.ai.fire_extinguisher_detector import FireExtinguisherDetector
from app.ai.pose_analyzer_enhanced import EnhancedPoseAnalyzer
from app.ai.rule_engine import RuleEngine
from app.ai.feedback_generator import FeedbackGenerator


class AIScoringAdapter:
    """AI 评分适配器
    
    整合 YOLOv8 检测、MediaPipe 姿态分析和规则引擎评分
    """
    
    def __init__(
        self,
        yolo_model_path: str = "yolov8n.pt",
        use_pose_analysis: bool = True
    ):
        """初始化 AI 评分适配器
        
        Args:
            yolo_model_path: YOLO 模型路径
            use_pose_analysis: 是否使用姿态分析
        """
        self.yolo_detector = FireExtinguisherDetector(
            model_path=yolo_model_path,
            conf_threshold=0.5,
            iou_threshold=0.45
        )
        
        self.pose_analyzer = EnhancedPoseAnalyzer() if use_pose_analysis else None
        self.rule_engine = RuleEngine()
        self.feedback_generator = FeedbackGenerator()
        
        self.use_pose_analysis = use_pose_analysis
    
    async def score_training(
        self,
        video_path: str,
        training_type: str = "fire_extinguisher"
    ) -> Dict[str, Any]:
        """对训练视频进行完整评分
        
        Args:
            video_path: 视频文件路径
            training_type: 训练类型
            
        Returns:
            完整评分结果
        """
        print(f"开始分析训练视频：{video_path}")
        
        # 1. YOLOv8 目标检测
        print("步骤 1: YOLOv8 目标检测...")
        yolo_detections = self.yolo_detector.detect_video(video_path)
        action_scores = self._process_yolo_detections(yolo_detections)
        
        # 2. MediaPipe 姿态分析
        pose_scores = {}
        if self.use_pose_analysis:
            print("步骤 2: MediaPipe 姿态分析...")
            pose_report = self.pose_analyzer.analyze_training_video(video_path)
            pose_scores = self._process_pose_analysis(pose_report)
        
        # 3. 规则引擎评分
        print("步骤 3: 规则引擎评分...")
        evaluation_result = await self.rule_engine.evaluate(
            action_scores=action_scores,
            pose_scores=pose_scores,
            duration_seconds=Decimal(str(pose_report.get("total_duration", 0))) if self.use_pose_analysis else None,
            training_type=training_type
        )
        
        # 4. 生成反馈
        print("步骤 4: 生成反馈报告...")
        feedback_result = self.feedback_generator.generate_feedback(
            evaluation_result=evaluation_result,
            action_logs=self._generate_action_logs(yolo_detections),
            pose_details=pose_scores
        )
        
        # 5. 合并结果
        final_result = {
            "total_score": evaluation_result["total_score"],
            "performance_level": evaluation_result["performance_level"],
            "dimension_scores": evaluation_result["dimension_scores"],
            "step_scores": self._merge_step_scores(action_scores, pose_scores),
            "feedback": feedback_result["overall_feedback"],
            "suggestions": feedback_result["suggestions"],
            "detailed_report": feedback_result["detailed_report"],
            "action_logs": feedback_result.get("action_logs", []),
            "metadata": {
                "yolo_detections_count": len(yolo_detections),
                "pose_frames_analyzed": pose_report.get("frame_count", 0) if self.use_pose_analysis else 0,
                "model_version": "yolov8n_v1.0"
            }
        }
        
        print(f"评分完成！总分：{final_result['total_score']:.2f}")
        
        return final_result
    
    def _process_yolo_detections(
        self,
        detections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """处理 YOLO 检测结果
        
        Args:
            detections: YOLO 检测结果列表
            
        Returns:
            动作完整性评分输入
        """
        # 统计各步骤的检测情况
        step_detections = {
            "step1": {"count": 0, "avg_conf": 0},  # 准备阶段
            "step2": {"count": 0, "avg_conf": 0},  # 提灭火器
            "step3": {"count": 0, "avg_conf": 0},  # 拔保险销
            "step4": {"count": 0, "avg_conf": 0},  # 握喷管
            "step5": {"count": 0, "avg_conf": 0},  # 瞄准火源
            "step6": {"count": 0, "avg_conf": 0},  # 压把手
        }
        
        # 简化处理：根据检测到的灭火器和人的置信度计算
        for det in detections:
            class_name = det.get("class_name", "")
            confidence = det.get("confidence", 0)
            
            if class_name == "fire_extinguisher":
                # 根据检测位置和时间判断属于哪个步骤
                # 这里简化处理，假设检测到灭火器就给所有步骤加分
                for step_key in step_detections.keys():
                    step_detections[step_key]["count"] += 1
                    step_detections[step_key]["avg_conf"] = (
                        step_detections[step_key]["avg_conf"] + confidence
                    ) / 2
        
        # 转换为规则引擎需要的格式
        step_scores = {}
        for step_key, step_data in step_detections.items():
            count = step_data["count"]
            avg_conf = step_data["avg_conf"]
            
            # 检测到且置信度高则得分高
            if count > 0:
                score = min(100, avg_conf * 100 + count * 5)
            else:
                score = 0
            
            step_scores[step_key] = {
                "step_name": self._get_step_name(step_key),
                "score": score,
                "is_correct": score >= 60,
                "detection_count": count,
                "average_confidence": avg_conf
            }
        
        return {
            "step_scores": step_scores,
            "average_detection_rate": sum(s["score"] for s in step_scores.values()) / len(step_scores)
        }
    
    def _process_pose_analysis(
        self,
        pose_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理姿态分析报告
        
        Args:
            pose_report: 姿态分析报告
            
        Returns:
            姿态规范性评分输入
        """
        step_scores = pose_report.get("step_scores", {})
        
        # 添加姿态规范性特有的信息
        for step_key, step_data in step_scores.items():
            if isinstance(step_data, dict):
                # 添加权重信息
                step_data["weight"] = 0.15  # 默认权重
                
                # 添加角度详情
                if "angles" in step_data:
                    step_data["details"] = {
                        "angles": step_data["angles"]
                    }
        
        return {
            "step_scores": step_scores,
            "frame_count": pose_report.get("completed_steps", 0),
            "average_angles": self._calculate_average_angles(pose_report)
        }
    
    def _calculate_average_angles(self, pose_report: Dict[str, Any]) -> Dict[str, float]:
        """计算平均角度
        
        Args:
            pose_report: 姿态分析报告
            
        Returns:
            平均角度字典
        """
        # 简化实现
        return {
            "right_arm": 165.0,
            "left_arm": 160.0,
            "body": 10.0,
            "aim": 15.0
        }
    
    def _merge_step_scores(
        self,
        action_scores: Dict[str, Any],
        pose_scores: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并动作和姿态的步骤分数
        
        Args:
            action_scores: 动作完整性分数
            pose_scores: 姿态规范性分数
            
        Returns:
            合并后的步骤分数
        """
        merged = {}
        
        action_step_scores = action_scores.get("step_scores", {})
        pose_step_scores = pose_scores.get("step_scores", {})
        
        all_keys = set(list(action_step_scores.keys()) + list(pose_step_scores.keys()))
        
        for key in all_keys:
            action_data = action_step_scores.get(key, {})
            pose_data = pose_step_scores.get(key, {})
            
            # 加权平均（动作 60%，姿态 40%）
            action_score = action_data.get("score", 0) * 0.6
            pose_score = pose_data.get("score", 0) * 0.4
            
            merged[key] = {
                "step_name": action_data.get("step_name", pose_data.get("step_name", key)),
                "score": round(action_score + pose_score, 2),
                "is_correct": (action_score + pose_score) >= 60,
                "action_score": action_data.get("score", 0),
                "pose_score": pose_data.get("score", 0),
                "feedback": action_data.get("feedback", "") + " | " + pose_data.get("feedback", "")
            }
        
        return merged
    
    def _generate_action_logs(
        self,
        detections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """生成动作日志
        
        Args:
            detections: YOLO 检测结果
            
        Returns:
            动作日志列表
        """
        logs = []
        
        # 按时间分组
        timestamps = sorted(set(det.get("timestamp", 0) for det in detections))
        
        for i, ts in enumerate(timestamps):
            frame_dets = [d for d in detections if d.get("timestamp", 0) == ts]
            
            log = {
                "step_index": i + 1,
                "step_name": f"步骤{i+1}",
                "timestamp": ts,
                "detections": len(frame_dets),
                "average_confidence": sum(d.get("confidence", 0) for d in frame_dets) / len(frame_dets) if frame_dets else 0
            }
            logs.append(log)
        
        return logs
    
    def _get_step_name(self, step_key: str) -> str:
        """获取步骤名称
        
        Args:
            step_key: 步骤键（如 step1）
            
        Returns:
            步骤名称
        """
        names = {
            "step1": "准备阶段",
            "step2": "提灭火器",
            "step3": "拔保险销",
            "step4": "握喷管",
            "step5": "瞄准火源",
            "step6": "压把手"
        }
        
        return names.get(step_key, step_key)
    
    def close(self):
        """释放资源"""
        self.yolo_detector.close()
        if self.pose_analyzer:
            self.pose_analyzer.close()
```

### 4.2 集成到 ScoringService

修改 `backend/app/services/scoring_service.py`:

```python
# 在文件顶部添加导入
from app.ai.ai_scoring_adapter import AIScoringAdapter

# 在 ScoringService 类中添加新方法
class ScoringService:
    # ... 现有代码 ...
    
    async def score_with_ai(
        self,
        video_path: str,
        training_type: str = "fire_extinguisher",
        yolo_model_path: str = "yolov8n.pt"
    ) -> Dict[str, Any]:
        """使用 AI 模型进行真实评分
        
        Args:
            video_path: 视频文件路径
            training_type: 训练类型
            yolo_model_path: YOLO 模型路径
            
        Returns:
            评分结果
        """
        # 创建 AI 评分适配器
        adapter = AIScoringAdapter(
            yolo_model_path=yolo_model_path,
            use_pose_analysis=True
        )
        
        try:
            # 执行 AI 评分
            result = await adapter.score_training(
                video_path=video_path,
                training_type=training_type
            )
            
            return result
        finally:
            adapter.close()
```

---

## 5. 完整集成流程

### 5.1 修改 TrainingService

编辑 `backend/app/services/training_service.py`:

```python
# 找到 upload_video 或相关方法
# 修改为调用 AI 评分

async def upload_video(
    self,
    training_id: int,
    video_file: UploadFile,
    user_id: int
) -> TrainingRecord:
    # ... 现有上传逻辑 ...
    
    # 保存视频后，调用 AI 评分
    scoring_service = ScoringService()
    
    # 使用 AI 评分（替换原来的模拟评分）
    scoring_result = await scoring_service.score_with_ai(
        video_path=saved_video_path,
        training_type=training.training_type,
        yolo_model_path="backend/runs/detect/fire_extinguisher_train/weights/best.pt"
    )
    
    # 更新训练记录
    training.total_score = scoring_result["total_score"]
    training.step_scores = scoring_result["step_scores"]
    training.feedback = scoring_result["feedback"]
    
    await session.commit()
    
    return training
```

### 5.2 配置文件更新

创建 `backend/app/core/ai_config.py`:

```python
"""AI 模型配置"""

from pathlib import Path

# 模型路径
BASE_DIR = Path(__file__).parent.parent.parent
MODELS_DIR = BASE_DIR / "data" / "models"

# YOLOv8 模型
YOLO_CONFIG = {
    "default_model": MODELS_DIR / "yolov8n.pt",
    "trained_model": MODELS_DIR / "fire_extinguisher" / "weights" / "best.pt",
    "conf_threshold": 0.5,
    "iou_threshold": 0.45,
    "img_size": 640,
    "device": "cpu"  # 或 "cuda:0"
}

# MediaPipe 配置
MEDIAPIPE_CONFIG = {
    "model_complexity": 1,
    "smooth_landmarks": True,
    "min_detection_confidence": 0.5,
    "min_tracking_confidence": 0.5
}

# 评分配置
SCORING_CONFIG = {
    "use_ai_scoring": True,  # 设置为 True 启用 AI 评分
    "use_pose_analysis": True,
    "action_weight": 0.4,
    "pose_weight": 0.4,
    "timeliness_weight": 0.2
}
```

### 5.3 环境变量配置

编辑 `.env` 文件:

```bash
# AI 模型配置
USE_AI_SCORING=true
USE_POSE_ANALYSIS=true
YOLO_MODEL_PATH=./backend/data/models/fire_extinguisher/weights/best.pt
YOLO_CONF_THRESHOLD=0.5
YOLO_IOU_THRESHOLD=0.45

# 性能配置
AI_BATCH_SIZE=1
AI_WORKERS=2
AI_TIMEOUT=120
```

---

## 6. 测试与验证

### 6.1 单元测试

创建 `backend/tests/test_ai_integration.py`:

```python
"""AI 集成测试"""

import pytest
from pathlib import Path
from app.ai.ai_scoring_adapter import AIScoringAdapter
from app.services.scoring_service import ScoringService


@pytest.mark.asyncio
async def test_yolo_detection():
    """测试 YOLO 检测"""
    from app.ai.fire_extinguisher_detector import FireExtinguisherDetector
    
    detector = FireExtinguisherDetector(model_path="yolov8n.pt")
    
    # 使用测试图片
    test_image = Path("tests/test_data/test_image.jpg")
    
    if test_image.exists():
        import cv2
        frame = cv2.imread(str(test_image))
        detections = detector.detect_frame(frame)
        
        assert isinstance(detections, list)
        print(f"检测到 {len(detections)} 个目标")
        for det in detections:
            print(f"  - {det['class_name']}: {det['confidence']:.2f}")


@pytest.mark.asyncio
async def test_pose_analysis():
    """测试姿态分析"""
    from app.ai.pose_analyzer_enhanced import EnhancedPoseAnalyzer
    
    analyzer = EnhancedPoseAnalyzer()
    
    # 使用测试视频
    test_video = Path("tests/test_data/test_training.mp4")
    
    if test_video.exists():
        report = analyzer.analyze_training_video(str(test_video))
        
        assert "total_duration" in report
        assert "step_scores" in report
        print(f"视频时长：{report['total_duration']:.2f}秒")
        print(f"完成步骤：{report['completed_steps']}/6")


@pytest.mark.asyncio
async def test_full_ai_scoring():
    """测试完整 AI 评分流程"""
    adapter = AIScoringAdapter(
        yolo_model_path="yolov8n.pt",
        use_pose_analysis=True
    )
    
    test_video = Path("tests/test_data/test_training.mp4")
    
    if test_video.exists():
        result = await adapter.score_training(
            video_path=str(test_video),
            training_type="fire_extinguisher"
        )
        
        assert "total_score" in result
        assert "performance_level" in result
        assert "feedback" in result
        
        print(f"\n总分：{result['total_score']:.2f}")
        print(f"等级：{result['performance_level']}")
        print(f"反馈：{result['feedback']}")


@pytest.mark.asyncio
async def test_scoring_service_with_ai():
    """测试 ScoringService 集成 AI"""
    service = ScoringService()
    
    test_video = Path("tests/test_data/test_training.mp4")
    
    if test_video.exists():
        result = await service.score_with_ai(
            video_path=str(test_video),
            training_type="fire_extinguisher"
        )
        
        assert result["total_score"] >= 0
        assert result["total_score"] <= 100
        print(f"AI 评分结果：{result['total_score']:.2f}")
```

**运行测试**:
```bash
cd backend
pytest tests/test_ai_integration.py -v -s
```

### 6.2 端到端测试

创建测试脚本 `scripts/test_end_to_end.py`:

```python
#!/usr/bin/env python3
"""端到端测试脚本"""

import asyncio
import aiohttp
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

async def test_full_workflow():
    """测试完整工作流程"""
    
    # 1. 登录
    print("1. 登录...")
    async with aiohttp.ClientSession() as session:
        login_data = {
            "username": "student001",
            "password": "Test123456"
        }
        
        async with session.post(f"{BASE_URL}/api/user/login", data=login_data) as resp:
            result = await resp.json()
            token = result["token"]
            print(f"   登录成功！Token: {token[:50]}...")
        
        # 2. 开始训练
        print("2. 开始训练...")
        training_data = {
            "training_type": "fire_extinguisher",
            "duration_seconds": 60
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        async with session.post(
            f"{BASE_URL}/api/training/start",
            json=training_data,
            headers=headers
        ) as resp:
            result = await resp.json()
            training_id = result["training_id"]
            print(f"   训练创建成功！ID: {training_id}")
        
        # 3. 上传视频
        print("3. 上传视频...")
        test_video = Path("tests/test_data/test_training.mp4")
        
        if not test_video.exists():
            print(f"   ⚠️  测试视频不存在：{test_video}")
            return
        
        with open(test_video, "rb") as f:
            files = {"file": f}
            data = {"training_id": training_id}
            
            async with session.post(
                f"{BASE_URL}/api/training/upload",
                data=data,
                files=files,
                headers=headers
            ) as resp:
                result = await resp.json()
                
                if resp.status == 200:
                    print(f"   ✅ 上传成功！")
                    print(f"   总分：{result.get('total_score', 0):.2f}")
                    print(f"   反馈：{result.get('feedback', '')}")
                else:
                    print(f"   ❌ 上传失败：{result}")
        
        # 4. 查询训练详情
        print("4. 查询训练详情...")
        async with session.get(
            f"{BASE_URL}/api/training/{training_id}",
            headers=headers
        ) as resp:
            result = await resp.json()
            print(f"   状态：{result.get('status')}")
            print(f"   总分：{result.get('total_score', 0):.2f}")


if __name__ == "__main__":
    print("="*60)
    print("FireTrain AI 集成端到端测试")
    print("="*60)
    
    asyncio.run(test_full_workflow())
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
```

---

## 7. 性能优化

### 7.1 YOLOv8 推理优化

```python
# 1. 使用更小的模型
# yolov8n.pt (最快) > yolov8s.pt > yolov8m.pt

# 2. 降低输入分辨率
detector = FireExtinguisherDetector(img_size=416)  # 从 640 降到 416

# 3. 提高置信度阈值
detector = FireExtinguisherDetector(conf_threshold=0.6)

# 4. 跳帧处理（视频分析）
detections = detector.detect_video(
    video_path="test.mp4",
    frame_skip=2,  # 每 3 帧检测一次
    max_frames=100  # 最多检测 100 帧
)

# 5. 使用 GPU（如果有）
detector = FireExtinguisherDetector(device="cuda:0")
```

### 7.2 MediaPipe 优化

```python
# 1. 降低模型复杂度
pose = mp.solutions.pose.Pose(model_complexity=0)  # 0=轻量

# 2. 降低置信度阈值
pose = mp.solutions.pose.Pose(min_detection_confidence=0.3)

# 3. 跳帧处理
frame_skip = 2  # 每 3 帧分析一次
```

### 7.3 并发处理

```python
# 使用异步并发处理多个请求
from fastapi import BackgroundTasks

async def process_training_video(
    background_tasks: BackgroundTasks,
    video_path: str,
    training_id: int
):
    """后台处理视频"""
    background_tasks.add_task(
        scoring_service.score_with_ai,
        video_path,
        training_id
    )
```

---

## 8. 常见问题

### 8.1 YOLOv8 训练问题

**Q1: 训练 loss 不下降**
- 检查数据标注是否正确
- 调整学习率（尝试更小或更大）
- 增加数据增强
- 检查类别是否平衡

**Q2: mAP 很低（<0.5）**
- 增加训练数据量
- 调整锚框尺寸
- 增加训练轮数
- 检查标注质量

**Q3: 推理速度慢**
- 使用更小的模型（yolov8n）
- 降低输入分辨率
- 使用 GPU 推理
- 跳帧处理

### 8.2 MediaPipe 问题

**Q1: 关键点检测不稳定**
- 提高摄像头分辨率
- 改善光照条件
- 调整置信度阈值
- 使用平滑处理

**Q2: 角度计算不准确**
- 检查关键点映射是否正确
- 调整标准角度范围
- 增加容差范围

### 8.3 集成问题

**Q1: AI 评分与模拟评分差异大**
- 调整评分权重配置
- 校准阈值参数
- 收集更多测试数据进行验证

**Q2: 内存占用过高**
- 减少批次大小
- 及时释放模型资源
- 使用更小的模型

---

## 9. 总结与下一步

### 9.1 完成情况检查清单

- [ ] YOLOv8 数据准备（500+ 张图片）
- [ ] YOLOv8 模型训练（mAP50 > 0.75）
- [ ] MediaPipe 姿态分析增强
- [ ] AI 评分适配器开发
- [ ] 规则引擎集成
- [ ] ScoringService 修改
- [ ] 单元测试编写
- [ ] 端到端测试
- [ ] 性能优化
- [ ] 文档完善

### 9.2 预期成果

完成所有接入工作后，系统将能够：

1. ✅ 自动检测灭火器操作
2. ✅ 分析人体姿态和动作规范性
3. ✅ 基于规则引擎给出客观评分
4. ✅ 生成详细的反馈报告
5. ✅ 提供改进建议

### 9.3 下一步计划

1. **数据持续优化**: 收集更多训练数据，迭代模型
2. **功能扩展**: 支持更多消防训练场景
3. **性能提升**: 优化推理速度，支持实时反馈
4. **用户体验**: 改进界面，增加可视化展示

---

**文档版本**: v1.0  
**最后更新**: 2026-03-13  
**维护者**: FireTrain 开发团队
