# 智能消防技能训练评测系统设计文档

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 系统需求分析](#2-系统需求分析)
- [2.4 硬件、软件与设备需求](#24-硬件软件与设备需求)
- [3. 技术架构设计](#3-技术架构设计)
- [3.2.5 模型训练策略](#325-模型训练策略)
- [3.4 微服务拆分与 gRPC 调用设计](#34-微服务拆分与-grpc-调用设计)
- [4. 核心功能模块设计](#4-核心功能模块设计)
- [5. 数据库设计](#5-数据库设计)
- [6. 界面设计说明](#6-界面设计说明)
- [7. 评分规则详细说明](#7-评分规则详细说明)
- [8. 开发计划与时间安排](#8-开发计划与时间安排)
- [8.5 最小可行训练计划（1周）](#85-最小可行训练计划1周)
- [9. 预期成果](#9-预期成果)
- [10. 答辩准备指南](#10-答辩准备指南)
- [附录 A：核心代码示例](#附录-a核心代码示例)
- [附录 B：参考文献](#附录-b参考文献)
- [附录 C：资源链接](#附录-c资源链接)

## 1. 项目概述

### 1.1 项目背景

消防安全是校园安全和社会安全的重要组成部分。目前消防技能训练存在以下问题：

| 问题 | 描述 |
| --- | --- |
| 人工评测效率低 | 需要专业教官一对一指导，人力成本高 |
| 评分标准不统一 | 不同教官评分存在主观差异 |
| 训练反馈不及时 | 无法实时纠正错误动作 |
| 训练数据难追溯 | 缺乏数字化记录，难以分析训练效果 |

### 1.2 项目目标

开发一套智能消防技能训练评测系统，实现：

- 自动化评测：计算机视觉自动识别动作，减少人工干预
- 实时反馈：训练过程中即时提示错误动作
- 量化评分：基于规则的客观评分，标准统一
- 数据追溯：完整记录训练历史，支持效果分析
- 易用性强：Web 界面，无需专业设备，普通摄像头即可使用

### 1.3 应用场景

- 高校消防技能训练课程
- 企业消防安全培训
- 社区消防演练活动
- 消防员基础技能练习

### 1.4 聚焦场景

本系统聚焦于灭火器操作流程评测，原因如下：

| 因素 | 说明 |
| --- | --- |
| 动作简单 | 5 个标准步骤，易于识别和评分 |
| 设备常见 | 灭火器是最常见的消防器材 |
| 资料丰富 | 开源代码和参考资料较多 |
| 演示直观 | 答辩时容易展示效果 |

## 2. 系统需求分析

### 2.1 功能需求

#### 2.1.1 用户管理模块

| 功能 | 描述 | 优先级 |
| --- | --- | --- |
| 用户注册 | 手机号/邮箱注册，设置密码 | 高 |
| 用户登录 | 账号密码登录，支持记住登录 | 高 |
| 个人信息 | 查看和修改个人基本信息 | 中 |
| 训练历史 | 查看历史训练记录和成绩 | 高 |

#### 2.1.2 训练评测模块

| 功能 | 描述 | 优先级 |
| --- | --- | --- |
| 视频采集 | 调用摄像头实时采集或上传视频文件 | 高 |
| 动作识别 | 识别灭火器操作的关键动作 | 高 |
| 姿态分析 | 检测手臂角度、身体姿态等 | 高 |
| 实时反馈 | 训练过程中提示错误动作 | 中 |
| 评分报告 | 生成详细评分报告和改进建议 | 高 |

#### 2.1.3 数据可视化模块

| 功能 | 描述 | 优先级 |
| --- | --- | --- |
| 成绩统计 | 个人成绩汇总统计 | 中 |
| 趋势分析 | 训练效果变化趋势图 | 中 |
| 排行榜 | 用户成绩排名（可选） | 低 |

#### 2.1.4 系统管理模块

| 功能 | 描述 | 优先级 |
| --- | --- | --- |
| 评分规则配置 | 管理员可调整评分标准 | 低 |
| 用户管理 | 管理员管理用户账号 | 低 |
| 数据备份 | 定期备份训练数据 | 低 |

### 2.2 非功能需求

| 需求类型 | 指标要求 |
| --- | --- |
| 性能要求 | 单路视频处理延迟 <= 1 秒 |
| 并发要求 | 支持至少 5 人同时使用 |
| 可用性 | 系统可用性 >= 95% |
| 兼容性 | 支持 Chrome、Edge 等主流浏览器 |
| 安全性 | 用户密码加密存储，防止数据泄露 |

### 2.3 运行环境

| 环境 | 配置要求 |
| --- | --- |
| 服务器 | CPU 4 核+，内存 8G+，无需 GPU（可选） |
| 客户端 | 普通电脑 + USB 摄像头/笔记本自带摄像头 |
| 操作系统 | Windows/Linux/MacOS |
| 浏览器 | Chrome 90+ / Edge 90+ |

### 2.4 硬件、软件与设备需求

#### 2.4.1 硬件需求（部署端）

| 类别 | 最低配置 | 推荐配置 | 说明 |
| --- | --- | --- | --- |
| CPU | 4 核（Intel i5 同级） | 8 核（Intel i7/AMD Ryzen 7 同级） | 负责后端服务与视频推理 |
| 内存 | 8 GB | 16 GB 及以上 | 同时运行 Web 服务、数据库、推理模块 |
| 存储 | 256 GB SSD | 512 GB SSD 及以上 | 用于系统、数据库、训练视频 |
| GPU（可选） | 无 | NVIDIA 6 GB 显存及以上 | 提升多路视频或更高分辨率处理效率 |
| 网络 | 千兆局域网 | 千兆局域网 + 稳定外网 | 支持前后端访问与模型下载 |

#### 2.4.2 终端设备需求（训练端）

| 设备 | 最低要求 | 推荐要求 | 说明 |
| --- | --- | --- | --- |
| 训练电脑 | 双核 CPU、4 GB 内存 | 四核 CPU、8 GB 内存 | 运行浏览器并采集视频 |
| 摄像头 | 720p，25fps | 1080p，30fps，自动对焦 | 影响姿态识别稳定性 |
| 麦克风（可选） | 可省略 | 外接降噪麦克风 | 若后续加入语音提示/交互可使用 |
| 显示器 | 1366x768 | 1920x1080 | 方便展示实时反馈与评分报告 |
| 灭火器训练道具 | 标准干粉灭火器（演示道具） | 标准道具 + 火源模拟标靶 | 保证动作识别场景一致性 |

#### 2.4.3 软件需求（开发与运行）

| 软件 | 版本建议 | 用途 |
| --- | --- | --- |
| Python | 3.9+ | 后端服务与 AI 推理 |
| Node.js | 18+ | 前端构建与本地开发 |
| MySQL | 8.0+（或 SQLite 3） | 训练数据持久化 |
| gRPC | 1.60+ | 微服务间高性能 RPC 通信 |
| Protocol Buffers | 3.20+ | 服务接口定义与代码生成 |
| Git | 2.30+ | 版本管理 |
| Docker（可选） | 24+ | 一键部署与环境隔离 |
| Nginx（可选） | 1.20+ | 反向代理与静态资源服务 |

#### 2.4.4 浏览器与客户端软件要求

| 项目 | 要求 |
| --- | --- |
| 浏览器 | Chrome 90+、Edge 90+，需开启摄像头权限 |
| 摄像头权限 | 首次访问训练页面需授权，建议固定“允许” |
| 编码支持 | 建议 H.264/MP4，便于视频上传与回放 |
| 屏幕缩放 | 建议 100%-125%，避免页面布局错位 |

#### 2.4.5 存储与数据保留建议

| 数据类型 | 建议保留周期 | 说明 |
| --- | --- | --- |
| 原始训练视频 | 30-90 天 | 可按课程周期清理，节约空间 |
| 评分结果与日志 | >= 1 年 | 用于趋势分析与教学复盘 |
| 数据库备份 | 每日增量、每周全量 | 防止误删和系统故障导致数据丢失 |

## 3. 技术架构设计

### 3.1 系统架构图

```text
┌─────────────────────────────────────────────────────────────────────┐
│                           前端展示层                                 │
│                    Vue3 + Element Plus + ECharts                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ 登录页面 │  │ 训练页面 │  │ 历史页面 │  │ 统计页面 │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────────────┐
│                    API Gateway（FastAPI/BFF）                        │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼ gRPC
┌─────────────────────────────────────────────────────────────────────┐
│                         微服务层（Python）                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │ UserService │ │TrainingSvc  │ │ ScoringSvc  │ │ AnalyticsSvc│   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           AI 推理层                                   │
│         YOLOv8(物体检测) + MediaPipe(姿态估计) + 规则引擎           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │灭火器检测│  │姿态关键点│  │评分计算  │  │ gRPC AI Inference │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           数据存储层                                 │
│                      MySQL/SQLite + 文件系统                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                          │
│  │ 用户数据 │  │ 训练记录 │  │ 视频文件 │                          │
│  └──────────┘  └──────────┘  └──────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 技术选型说明

#### 3.2.1 前端技术

| 技术 | 版本 | 选型理由 |
| --- | --- | --- |
| Vue3 | 3.3+ | 响应式框架，学习资源丰富 |
| Element Plus | 2.3+ | UI 组件库，快速搭建界面 |
| ECharts | 5.4+ | 数据可视化，图表美观 |
| Axios | 1.4+ | HTTP 请求库，简单易用 |

#### 3.2.2 后端技术

| 技术 | 版本 | 选型理由 |
| --- | --- | --- |
| Python | 3.9+ | AI 生态完善，开发效率高 |
| FastAPI（Gateway） | 0.100+ | 统一对外 API，前后端解耦 |
| gRPC | 1.60+ | 服务间低延迟、高吞吐调用 |
| Protocol Buffers | 3.20+ | 统一接口契约，便于多语言扩展 |
| SQLAlchemy | 2.0+ | ORM 框架，数据库操作方便 |
| Pydantic | 2.0+ | 数据验证，类型安全 |

#### 3.2.3 AI 技术

| 技术 | 版本 | 选型理由 |
| --- | --- | --- |
| YOLOv8 | 8.0+ | 预训练模型，检测精度高 |
| MediaPipe | 0.10+ | 无需训练，CPU 可运行 |
| OpenCV | 4.8+ | 图像处理基础库 |

#### 3.2.4 数据库

| 技术 | 版本 | 选型理由 |
| --- | --- | --- |
| MySQL | 8.0+ | 稳定可靠，学习资料多 |
| SQLite | 3.0+ | 轻量级，无需配置服务器 |

#### 3.2.5 模型训练策略

为保证毕设可交付、可演示、可解释，本项目采用“少量训练 + 工程调参”的路线。

**核心结论：真正需要自行训练的模型主要是 YOLOv8。**

| 分类 | 项目 | 是否需要训练 | 难度 | 说明 |
| --- | --- | --- | --- | --- |
| 必训（推荐） | YOLOv8 目标检测微调 | 需要 | 中等 | 用于提升本场景（教室/走廊/光照变化/遮挡）下的检测稳定性 |
| 可不训（直接用） | MediaPipe Pose | 不需要 | 低 | 直接调用现成方案，重点在关键点映射、角度计算、阈值调参 |
| 可不训（规则） | 规则引擎与评分逻辑 | 不需要 | 低-中 | 属于规则设计与工程实现，不是机器学习训练 |
| 可选提升 | 时序动作识别模型 | 可选 | 中高-高 | 可提升智能化，但需视频片段标注与时序模型训练，周期风险较高 |

**1) 必训部分：YOLOv8 目标检测微调**

- 训练目标：检测灭火器及关键目标（可按阶段定义类别）
- 数据规模建议：先从几百张标注图起步，再迭代到 1000+ 张
- 主要难点：
  - 数据采集与标注耗时高
  - 类别定义需提前固定（仅灭火器，或扩展到喷管/把手/保险销）
- 难度判断：中等（本科毕设可完成）

**2) 不需要训练的部分**

- `MediaPipe Pose`：直接调用预置模型，做关键点映射与阈值调参
- `规则引擎`：基于流程、角度、时长进行评分，不涉及模型训练

**3) 可选训练提升（非必需）**

- 时序动作识别（如骨架序列/视频序列模型）：
  - 可识别完整动作链“检查→拔销→握管→对准→喷射”
  - 需要额外视频切片标注与时序训练
  - 对毕设周期与算力要求更高，不建议作为主线依赖

**推荐落地方案（答辩可讲）**

- 训练部分：YOLOv8 场景化小规模微调
- 非训练部分：MediaPipe + 可解释评分规则
- 工程价值：强调系统可部署、可复现、可演示，而非仅追求算法复杂度

### 3.3 目录结构

```text
fire_training_system/
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── views/
│   │   ├── api/
│   │   ├── router/
│   │   └── store/
│   ├── package.json
│   └── vite.config.js
│
├── gateway/                      # 对外 HTTP API（FastAPI）
│   ├── app/
│   │   ├── api/
│   │   ├── middleware/
│   │   ├── grpc_clients/
│   │   └── main.py
│   └── requirements.txt
│
├── services/
│   ├── user-service/
│   │   ├── app/
│   │   └── main.py
│   ├── training-service/
│   │   ├── app/
│   │   └── main.py
│   ├── scoring-service/
│   │   ├── app/
│   │   └── main.py
│   └── analytics-service/
│       ├── app/
│       └── main.py
│
├── proto/                        # gRPC 接口定义
│   ├── user.proto
│   ├── training.proto
│   ├── scoring.proto
│   └── analytics.proto
│
├── data/
│   ├── videos/
│   ├── models/
│   └── database.db
│
└── docs/
    ├── 需求文档.md
    ├── 设计文档.md
    └── 用户手册.md
```

### 3.4 微服务拆分与 gRPC 调用设计

#### 3.4.1 服务拆分原则

- 单一职责：每个服务只负责一个核心业务域
- 数据边界清晰：服务拥有各自数据模型，避免强耦合
- 接口契约优先：所有内部调用以 `.proto` 为单一真源

#### 3.4.2 服务清单

| 服务名 | 主要职责 | 对外/对内接口 |
| --- | --- | --- |
| API Gateway | 统一鉴权、聚合响应、对前端暴露 REST API | 对外 REST；对内 gRPC Client |
| UserService | 用户注册、登录、资料管理 | gRPC |
| TrainingService | 训练任务创建、视频管理、状态跟踪 | gRPC |
| ScoringService | 姿态计算、流程判定、评分与反馈 | gRPC |
| AnalyticsService | 统计报表、趋势分析、排行榜 | gRPC |

#### 3.4.3 典型调用链路

1. 前端调用 Gateway：`POST /api/training/start`
2. Gateway 调用 TrainingService（gRPC）创建训练任务
3. TrainingService 调用 ScoringService（gRPC）执行推理评分
4. ScoringService 返回结果，TrainingService 落库
5. Gateway 汇总响应返回前端

#### 3.4.4 gRPC 接口设计示例

```proto
syntax = "proto3";

package training;

service TrainingService {
  rpc StartTraining (StartTrainingRequest) returns (StartTrainingResponse);
  rpc GetTrainingResult (GetTrainingResultRequest) returns (GetTrainingResultResponse);
}

message StartTrainingRequest {
  int64 user_id = 1;
  string training_type = 2;
}

message StartTrainingResponse {
  string training_id = 1;
  string status = 2;
}
```

#### 3.4.5 通信与容错策略

- 超时控制：默认 1-3 秒，关键推理接口可配置更长超时
- 重试策略：幂等查询接口可重试，写操作谨慎重试
- 错误码规范：统一业务码与 gRPC status 映射
- 可观测性：记录请求链路 ID、耗时、错误日志，便于排障

## 4. 核心功能模块设计

### 4.1 用户管理模块

#### 4.1.1 功能流程

```text
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 注册页面 │ →  │ 填写信息 │ →  │ 验证提交 │ →  │ 注册成功 │
└─────────┘    └─────────┘    └─────────┘    └─────────┘

┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 登录页面 │ →  │ 输入账号 │ →  │ 验证密码 │ →  │ 登录成功 │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

#### 4.1.2 数据模型

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # 加密存储
    email = Column(String(100), unique=True)
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)

    training_records = relationship("TrainingRecord", back_populates="user")
```

#### 4.1.3 API 接口

对外由 API Gateway 暴露 REST API；内部由 gRPC 服务完成实际业务处理。

| 接口 | 方法 | 路径 | 描述 |
| --- | --- | --- | --- |
| 用户注册 | POST | /api/user/register | 注册新用户 |
| 用户登录 | POST | /api/user/login | 用户登录 |
| 获取信息 | GET | /api/user/profile | 获取个人信息 |
| 修改信息 | PUT | /api/user/profile | 修改个人信息 |

### 4.2 训练评测模块

#### 4.2.1 功能流程

```text
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 选择训练模式 │ →  │ 启动摄像头  │ →  │ 开始训练    │
└─────────────┘    └─────────────┘    └─────────────┘
       ↓
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 动作识别分析 │ →  │ 实时反馈提示 │ →  │ 生成评分报告 │
└─────────────┘    └─────────────┘    └─────────────┘
```

#### 4.2.2 灭火器操作标准流程

| 步骤 | 动作名称 | 标准时长 | 检测要点 |
| --- | --- | --- | --- |
| 1 | 检查压力表 | 2-3 秒 | 头部朝向灭火器，手部指向压力表 |
| 2 | 拔掉保险销 | 2-3 秒 | 手部抓握保险销，向上拔出动作 |
| 3 | 握住喷管 | 1-2 秒 | 单手或双手握住喷管前端 |
| 4 | 对准火源 | 1-2 秒 | 喷管对准目标，手臂伸直 |
| 5 | 按压喷射 | 3-5 秒 | 另一只手按压把手，保持喷射姿态 |

#### 4.2.3 AI 推理流程

```python
def analyze_training_video(video_path):
    yolo_model = YOLO("yolov8n.pt")
    mp_pose = mp.solutions.pose.Pose()

    results = []
    for frame in video_frames:
        fire_extinguisher = yolo_model.detect(frame, classes=[fire_extinguisher_class])
        pose_landmarks = mp_pose.process(frame)
        action = recognize_action(fire_extinguisher, pose_landmarks)
        results.append({
            "frame": frame_id,
            "action": action,
            "pose": pose_landmarks,
            "timestamp": current_time
        })

    score = calculate_score(results)
    return score, results
```

#### 4.2.4 数据模型

```python
class TrainingRecord(Base):
    __tablename__ = "training_records"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    training_type = Column(String(50))
    total_score = Column(Float)
    step_scores = Column(JSON)
    video_path = Column(String(255))
    duration = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    feedback = Column(Text)

    user = relationship("User", back_populates="training_records")
```

#### 4.2.5 API 接口

对外由 API Gateway 暴露 REST API；Gateway 再调用 TrainingService/ScoringService 的 gRPC 接口。

| 接口 | 方法 | 路径 | 描述 |
| --- | --- | --- | --- |
| 开始训练 | POST | /api/training/start | 开始新训练 |
| 上传视频 | POST | /api/training/upload | 上传训练视频 |
| 获取结果 | GET | /api/training/result/{id} | 获取训练结果 |
| 历史记录 | GET | /api/training/history | 获取训练历史 |

### 4.3 数据可视化模块

#### 4.3.1 统计图表类型

| 图表类型 | 展示内容 | 使用场景 |
| --- | --- | --- |
| 折线图 | 成绩变化趋势 | 个人训练效果跟踪 |
| 柱状图 | 各步骤得分对比 | 找出薄弱环节 |
| 雷达图 | 多维度能力评估 | 综合能力展示 |
| 饼图 | 成绩分布统计 | 整体训练情况分析 |

#### 4.3.2 数据模型

```python
class TrainingStatistics(Base):
    __tablename__ = "training_statistics"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_trainings = Column(Integer)
    average_score = Column(Float)
    best_score = Column(Float)
    last_training = Column(DateTime)

    user = relationship("User")
```

#### 4.3.3 API 接口

对外由 API Gateway 暴露 REST API；内部通过 AnalyticsService 的 gRPC 接口实现。

| 接口 | 方法 | 路径 | 描述 |
| --- | --- | --- | --- |
| 个人统计 | GET | /api/stats/personal | 个人训练统计 |
| 趋势数据 | GET | /api/stats/trend | 成绩趋势数据 |
| 排行榜 | GET | /api/stats/ranking | 用户排行榜 |

## 5. 数据库设计

### 5.1 ER 图

```text
┌─────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    users    │       │ training_records│       │training_statistics│
├─────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)     │───┐   │ id (PK)         │   ┌───│ id (PK)         │
│ username    │   │   │ user_id (FK)    │───┘   │ user_id (FK)    │
│ password    │   │   │ training_type   │       │ total_trainings │
│ email       │   │   │ total_score     │       │ average_score   │
│ phone       │   │   │ step_scores     │       │ best_score      │
│ created_at  │   │   │ video_path      │       │ last_training   │
│ last_login  │   │   │ duration        │       └─────────────────┘
└─────────────┘   │   │ created_at      │
                  │   │ feedback        │
                  │   └─────────────────┘
                  │
                  │   ┌─────────────────┐
                  │   │  action_logs    │
                  │   ├─────────────────┤
                  └───│ id (PK)         │
                      │ record_id (FK)  │
                      │ action_name     │
                      │ is_correct      │
                      │ timestamp       │
                      └─────────────────┘
```

### 5.2 数据表详细设计

#### 5.2.1 用户表（users）

| 字段名 | 类型 | 长度 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| id | INT | - | PK, AUTO | 用户 ID |
| username | VARCHAR | 50 | UNIQUE, NOT NULL | 用户名 |
| password_hash | VARCHAR | 255 | NOT NULL | 密码哈希 |
| email | VARCHAR | 100 | UNIQUE | 邮箱 |
| phone | VARCHAR | 20 | - | 手机号 |
| created_at | DATETIME | - | DEFAULT NOW | 创建时间 |
| last_login | DATETIME | - | - | 最后登录时间 |

#### 5.2.2 训练记录表（training_records）

| 字段名 | 类型 | 长度 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| id | INT | - | PK, AUTO | 记录 ID |
| user_id | INT | - | FK, NOT NULL | 用户 ID |
| training_type | VARCHAR | 50 | NOT NULL | 训练类型 |
| total_score | FLOAT | - | NOT NULL | 总分 |
| step_scores | JSON | - | - | 各步骤得分 |
| video_path | VARCHAR | 255 | - | 视频路径 |
| duration | FLOAT | - | - | 训练时长 |
| created_at | DATETIME | - | DEFAULT NOW | 创建时间 |
| feedback | TEXT | - | - | 改进建议 |

#### 5.2.3 动作日志表（action_logs）

| 字段名 | 类型 | 长度 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| id | INT | - | PK, AUTO | 日志 ID |
| record_id | INT | - | FK, NOT NULL | 训练记录 ID |
| action_name | VARCHAR | 50 | NOT NULL | 动作名称 |
| is_correct | BOOLEAN | - | NOT NULL | 是否正确 |
| timestamp | DATETIME | - | NOT NULL | 时间戳 |

### 5.3 数据库初始化脚本

```sql
CREATE DATABASE fire_training DEFAULT CHARACTER SET utf8mb4;
USE fire_training;

CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);

CREATE TABLE training_records (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    training_type VARCHAR(50) NOT NULL,
    total_score FLOAT NOT NULL,
    step_scores JSON,
    video_path VARCHAR(255),
    duration FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    feedback TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE action_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    record_id INT NOT NULL,
    action_name VARCHAR(50) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    timestamp DATETIME NOT NULL,
    FOREIGN KEY (record_id) REFERENCES training_records(id)
);

CREATE TABLE training_statistics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    total_trainings INT DEFAULT 0,
    average_score FLOAT DEFAULT 0,
    best_score FLOAT DEFAULT 0,
    last_training DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## 6. 界面设计说明

### 6.1 界面整体风格

| 设计要素 | 说明 |
| --- | --- |
| 主色调 | 消防红（#E74C3C）+ 安全蓝（#3498DB） |
| 字体 | 微软雅黑/思源黑体 |
| 布局 | 响应式布局，适配不同屏幕 |
| 图标 | Element Plus 图标库 + 自定义消防图标 |

### 6.2 页面设计

#### 6.2.1 登录页面

```text
┌─────────────────────────────────────────────────────────────┐
│                    🔥 消防技能训练系统                        │
│         ┌─────────────────────────────────────┐             │
│         │  用户名：[________________]         │             │
│         │  密  码：[________________]         │             │
│         │  [ ] 记住我      忘记密码？         │             │
│         │        [    登    录    ]           │             │
│         │        还没有账号？ 立即注册        │             │
│         └─────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

#### 6.2.2 训练主页面

```text
┌─────────────────────────────────────────────────────────────┐
│  🔥 消防技能训练系统    首页  训练  历史  统计  [用户]退出   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────┐    │
│  │   视频预览区    │    │  训练步骤                    │    │
│  │   (摄像头画面)  │    │  1. 检查压力表  [✓/✗]       │    │
│  │   [开始] [停止] │    │  2. 拔掉保险销  [✓/✗]       │    │
│  │                 │    │  3. 握住喷管    [✓/✗]       │    │
│  │                 │    │  4. 对准火源    [✓/✗]       │    │
│  │                 │    │  5. 按压喷射    [✓/✗]       │    │
│  └─────────────────┘    └─────────────────────────────┘    │
│  实时提示：请保持手臂伸直，喷管对准目标区域                   │
└─────────────────────────────────────────────────────────────┘
```

#### 6.2.3 评分报告页面

```text
┌─────────────────────────────────────────────────────────────┐
│                    训练评分报告                              │
│                    2024-01-15 14:30                         │
│           总分：85 分（85%）                                │
│  动作完整性：90分  姿态规范性：80分  操作时效性：85分        │
│  改进建议：                                                  │
│  • 步骤2拔销动作不够流畅，建议练习手腕发力                   │
│  • 步骤4手臂角度偏差5度，请保持手臂伸直                      │
│  • 整体操作时间优秀，继续保持                                │
└─────────────────────────────────────────────────────────────┘
```

#### 6.2.4 数据统计页面

```text
┌─────────────────────────────────────────────────────────────┐
│  个人训练统计：总训练次数15次，平均分82分，最高分95分         │
│  展示区域：成绩趋势图（折线图）                               │
│  展示区域：各步骤得分（柱状图）                               │
│  展示区域：能力雷达图                                         │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 响应式设计

| 屏幕宽度 | 布局方式 |
| --- | --- |
| >=1200px | 三栏布局，完整功能 |
| 768-1199px | 两栏布局，适当简化 |
| <768px | 单栏布局，移动端优化 |

## 7. 评分规则详细说明

### 7.1 评分体系总览

总分 100 分，由三部分构成：

- 动作完整性：40 分
- 姿态规范性：40 分
- 操作时效性：20 分

### 7.2 动作完整性评分（40 分）

#### 7.2.1 评分标准

| 步骤 | 分值 | 评分规则 |
| --- | --- | --- |
| 1. 检查压力表 | 8 分 | 完成得 8 分，未完成得 0 分 |
| 2. 拔掉保险销 | 8 分 | 完成得 8 分，未完成得 0 分 |
| 3. 握住喷管 | 8 分 | 完成得 8 分，未完成得 0 分 |
| 4. 对准火源 | 8 分 | 完成得 8 分，未完成得 0 分 |
| 5. 按压喷射 | 8 分 | 完成得 8 分，未完成得 0 分 |

#### 7.2.2 动作识别规则

```python
def check_action_completeness(action_sequence):
    standard_sequence = ["check", "pull", "hold", "aim", "spray"]
    score = 0

    for i, action in enumerate(standard_sequence):
        if action in action_sequence:
            if action_sequence.index(action) >= i:
                score += 8
            else:
                score += 4
    return score
```

### 7.3 姿态规范性评分（40 分）

#### 7.3.1 关键姿态指标

| 指标 | 标准值 | 允许偏差 | 分值 |
| --- | --- | --- | --- |
| 手臂角度 | 150-170° | ±15° | 10 分 |
| 身体站位 | 侧身 45° | ±20° | 10 分 |
| 握管位置 | 距喷口 15cm | ±5cm | 10 分 |
| 喷射角度 | 对准目标中心 | ±10° | 10 分 |

#### 7.3.2 角度计算方法

```python
import numpy as np

def calculate_angle(point_a, point_b, point_c):
    ba = point_a - point_b
    bc = point_c - point_b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))
    return angle

def score_pose_angle(actual_angle, standard_angle, tolerance):
    deviation = abs(actual_angle - standard_angle)
    if deviation <= tolerance:
        return 10
    elif deviation <= tolerance * 2:
        return 7
    elif deviation <= tolerance * 3:
        return 4
    else:
        return 1
```

#### 7.3.3 MediaPipe 关键点映射

- `0`：鼻子（头部朝向判断）
- `11`、`12`：左右肩
- `13`、`14`：左右肘
- `15`、`16`：左右手腕
- `23`、`24`：左右髋

### 7.4 操作时效性评分（20 分）

#### 7.4.1 时间标准

| 指标 | 标准时间 | 评分规则 |
| --- | --- | --- |
| 总操作时间 | 15-25 秒 | 范围内 20 分，每超 1 秒扣 2 分 |
| 步骤 1 时间 | 2-3 秒 | 范围内 4 分 |
| 步骤 2 时间 | 2-3 秒 | 范围内 4 分 |
| 步骤 3 时间 | 1-2 秒 | 范围内 4 分 |
| 步骤 4 时间 | 1-2 秒 | 范围内 4 分 |
| 步骤 5 时间 | 3-5 秒 | 范围内 4 分 |

#### 7.4.2 时间评分计算

```python
def score_duration(actual_time, min_time, max_time, max_score):
    if min_time <= actual_time <= max_time:
        return max_score
    elif actual_time < min_time:
        return max(0, max_score - (min_time - actual_time) * 2)
    else:
        return max(0, max_score - (actual_time - max_time) * 2)
```

### 7.5 综合评分计算

```python
def calculate_total_score(completeness_score, pose_score, duration_score):
    total = completeness_score + pose_score + duration_score

    if total >= 90:
        grade = "优秀"
    elif total >= 80:
        grade = "良好"
    elif total >= 70:
        grade = "合格"
    else:
        grade = "需改进"

    return {
        "total_score": total,
        "grade": grade,
        "completeness": completeness_score,
        "pose": pose_score,
        "duration": duration_score
    }
```

### 7.6 反馈建议生成

#### 7.6.1 建议模板库

| 问题类型 | 反馈建议 |
| --- | --- |
| 手臂角度过小 | 请保持手臂伸直，手臂角度应保持在 150-170 度之间 |
| 手臂角度过大 | 手臂不要过度伸展，保持在 150-170 度之间 |
| 身体正对火源 | 请侧身站立，与火源保持约 45 度角，避免正面面对 |
| 握管位置太近 | 手握喷管位置距离喷口应约 15cm，防止冻伤 |
| 握管位置太远 | 手握喷管位置距离喷口应约 15cm，确保控制稳定 |
| 操作时间过长 | 操作时间较长，建议加强熟练度练习 |
| 操作时间过短 | 操作时间过短，可能动作不够规范，请注重质量 |
| 步骤遗漏 | 检测到步骤 [X] 未完成，请按照标准流程操作 |
| 步骤顺序错误 | 步骤顺序有误，正确顺序为：检查→拔销→握管→对准→喷射 |

#### 7.6.2 反馈生成逻辑

```python
def generate_feedback(score_details):
    feedbacks = []

    if score_details["pose"]["arm_angle"] < 7:
        feedbacks.append(feedback_templates["arm_angle_small"])

    if score_details["completeness"]["missing_steps"]:
        for step in score_details["completeness"]["missing_steps"]:
            feedbacks.append(f"检测到步骤[{step}]未完成，请按照标准流程操作")

    if score_details["duration"]["total"] < 15:
        feedbacks.append(feedback_templates["too_fast"])
    elif score_details["duration"]["total"] > 25:
        feedbacks.append(feedback_templates["too_slow"])

    if not feedbacks and score_details["total"] >= 90:
        feedbacks.append("操作非常规范，继续保持！")

    return feedbacks
```

## 8. 开发计划与时间安排

### 8.1 总体时间规划

| 时间阶段 | 核心任务 |
| --- | --- |
| 第 1-2 周 | 环境搭建与技术调研 |
| 第 3-4 周 | 后端开发 |
| 第 5-7 周 | 前端开发 |
| 第 8-9 周 | 系统集成与测试 |
| 第 10-12 周 | 论文撰写与答辩准备 |

### 8.2 详细任务分解

#### 第 1-2 周：环境搭建与技术调研

| 周次 | 任务 | 交付物 |
| --- | --- | --- |
| 第 1 周 | 开发环境搭建、技术栈学习 | 环境配置文档 |
| 第 1 周 | 需求分析细化、数据库设计 | 需求规格说明书 |
| 第 2 周 | 预训练模型测试、数据采集 | 模型测试报告 |
| 第 2 周 | 系统架构设计、接口定义 | 系统设计文档 |

#### 第 3-4 周：后端开发

| 周次 | 任务 | 交付物 |
| --- | --- | --- |
| 第 3 周 | 微服务拆分（User/Training/Scoring/Analytics） | 各服务骨架代码 |
| 第 3 周 | Proto 定义与 gRPC 基础联通 | `.proto` 文件与联调记录 |
| 第 4 周 | AI 推理模块集成、评分逻辑（ScoringService） | 评分服务接口 |
| 第 4 周 | Gateway 聚合接口与文档完善 | REST API + gRPC 接口文档 |

#### 第 5-7 周：前端开发

| 周次 | 任务 | 交付物 |
| --- | --- | --- |
| 第 5 周 | 项目初始化、登录注册页面 | 用户页面 |
| 第 5 周 | 训练主页面、视频采集功能 | 训练页面 |
| 第 6 周 | 评分报告页面、历史记录页面 | 报告页面 |
| 第 6 周 | 数据统计页面、图表展示 | 统计页面 |
| 第 7 周 | 前后端联调、界面优化 | 完整前端 |

#### 第 8-9 周：系统集成与测试

| 周次 | 任务 | 交付物 |
| --- | --- | --- |
| 第 8 周 | 系统部署、功能测试 | 测试报告 |
| 第 8 周 | 性能优化、Bug 修复 | 优化版本 |
| 第 9 周 | 用户测试、反馈收集 | 用户反馈报告 |
| 第 9 周 | 系统完善、演示准备 | 演示版本 |

#### 第 10-12 周：论文撰写与答辩准备

| 周次 | 任务 | 交付物 |
| --- | --- | --- |
| 第 10 周 | 论文初稿、系统截图 | 论文初稿 |
| 第 11 周 | 论文修改、格式调整 | 论文终稿 |
| 第 11 周 | 演示视频录制、PPT 制作 | 答辩材料 |
| 第 12 周 | 模拟答辩、最终完善 | 答辩准备完成 |

### 8.3 里程碑节点

| 节点 | 时间 | 检查内容 |
| --- | --- | --- |
| M1 | 第 2 周末 | 环境搭建完成，技术方案确定 |
| M2 | 第 4 周末 | 后端核心功能完成，API 可调用 |
| M3 | 第 7 周末 | 前端页面完成，前后端联调通过 |
| M4 | 第 9 周末 | 系统测试完成，可演示版本 |
| M5 | 第 12 周末 | 论文完成，答辩准备就绪 |

### 8.4 风险与应对

| 风险 | 可能性 | 影响 | 应对措施 |
| --- | --- | --- | --- |
| 模型识别精度不足 | 中 | 高 | 调整评分阈值，增加人工复核选项 |
| 开发进度延迟 | 中 | 中 | 优先保证核心功能，简化次要功能 |
| 硬件资源不足 | 低 | 中 | 使用云服务或降低视频分辨率 |
| 数据收集困难 | 中 | 低 | 使用公开数据集 + 模拟数据 |
| 微服务调用复杂度上升 | 中 | 中-高 | 先落地最小服务集，统一 proto 与错误码规范 |
| 分布式链路排障困难 | 中 | 中 | 增加链路 ID、统一日志格式、关键接口监控 |

### 8.5 最小可行训练计划（1周）

本计划用于在毕设周期内完成“可演示、可复现”的 YOLOv8 小规模微调。

#### 8.5.1 训练目标与范围

| 项目 | 内容 |
| --- | --- |
| 训练对象 | YOLOv8（从 `yolov8n.pt` 迁移学习） |
| 必做类别（最低） | `fire_extinguisher` |
| 可扩展类别（选做） | `hose`、`handle`、`safety_pin` |
| 成果要求 | 在本地典型场景下稳定检测，支持演示流程 |

#### 8.5.2 数据量建议

| 阶段 | 图像数量 | 说明 |
| --- | --- | --- |
| MVP 起步 | 300-500 张 | 先完成一版可训练、可推理模型 |
| 稳定版 | 800-1500 张 | 覆盖光照变化、角度变化、遮挡情况 |
| 分布建议 | 训练集/验证集/测试集 = 7:2:1 | 保证评估有效性 |

#### 8.5.3 一周任务拆分

| 天数 | 任务 | 交付物 |
| --- | --- | --- |
| Day 1 | 场景拍摄与数据清洗 | 原始图片集、命名规范 |
| Day 2 | 标注与类别复核（Label Studio/Roboflow 等） | 标注数据（YOLO 格式） |
| Day 3 | 首轮训练（`yolov8n`，小批次） | 首版权重文件、训练日志 |
| Day 4 | 验证误检漏检并补采样本 | 错误样本清单、补充数据集 |
| Day 5 | 第二轮训练与参数微调 | 改进版权重、对比结果 |
| Day 6 | 接入后端推理流程联调 | 接口可调用、可视化检测结果 |
| Day 7 | 压测与答辩材料整理 | 指标表、演示视频/截图 |

#### 8.5.4 训练参数建议（起步版）

| 参数 | 建议值 | 说明 |
| --- | --- | --- |
| 模型 | yolov8n | 轻量、训练快，适合毕设周期 |
| epochs | 50-100 | 小数据下先看收敛趋势 |
| imgsz | 640 | 平衡速度与精度 |
| batch | 8-16 | 依据显存/内存调整 |
| optimizer | SGD/AdamW | 先用默认，再对比 |
| early stopping | 开启 | 防止过拟合，节省时间 |

#### 8.5.5 验收指标（建议）

| 指标 | 建议目标 |
| --- | --- |
| mAP50 | >= 0.75（场景相关） |
| 漏检率 | 持续下降，重点场景可控 |
| 单帧推理时延 | 满足系统实时性目标（见 2.2） |
| 演示稳定性 | 连续演示 3 次无关键故障 |

## 9. 预期成果

### 9.1 系统成果

| 成果类型 | 具体内容 |
| --- | --- |
| 可运行系统 | 基于微服务 + gRPC 的完整 Web 应用系统，支持本地部署 |
| 源代码 | 前端 + Gateway + 各微服务完整源代码，含注释 |
| 数据库 | 完整的数据库结构和初始数据 |
| 部署文档 | 系统部署和配置说明文档 |
| 接口契约文档 | gRPC `proto` 定义与 REST 网关映射说明 |

### 9.2 文档成果

| 文档类型 | 内容说明 |
| --- | --- |
| 毕业论文 | 符合学校格式要求的完整论文 |
| 需求文档 | 系统需求分析说明书 |
| 设计文档 | 系统架构和模块设计文档 |
| 用户手册 | 系统使用说明书 |
| API 文档 | 接口定义和使用说明 |

### 9.3 演示成果

| 成果类型 | 内容说明 |
| --- | --- |
| 演示视频 | 3-5 分钟系统功能演示视频 |
| 答辩 PPT | 15-20 页答辩演示文稿 |
| 测试案例 | 典型场景的测试视频和结果 |

### 9.4 可选成果

| 成果类型 | 内容说明 |
| --- | --- |
| 软件著作权 | 申请计算机软件著作权 |
| 学术论文 | 发表相关学术论文 |
| 竞赛参赛 | 参加相关创新创业竞赛 |

## 10. 答辩准备指南

### 10.1 答辩 PPT 结构

- 封面（1 页）：项目名称、姓名、导师、日期
- 目录（1 页）：汇报内容概览
- 研究背景（2 页）：问题提出、研究意义
- 相关工作（2 页）：国内外研究现状
- 系统设计（3 页）：架构设计、技术选型
- 核心功能（4 页）：关键模块实现、评分规则
- 系统演示（3 页）：界面展示、功能演示
- 测试结果（2 页）：性能测试、用户反馈
- 总结展望（1 页）：工作总结、未来改进
- 致谢（1 页）：感谢导师和评委

### 10.2 演示视频准备

#### 10.2.1 视频内容规划

| 片段 | 时长 | 内容 |
| --- | --- | --- |
| 片头 | 10 秒 | 项目名称、功能简介 |
| 登录注册 | 30 秒 | 用户管理功能演示 |
| 训练评测 | 90 秒 | 核心功能完整演示 |
| 评分报告 | 30 秒 | 评分结果和反馈展示 |
| 数据统计 | 30 秒 | 数据可视化展示 |
| 片尾 | 20 秒 | 总结和技术亮点 |
| 总计 | 约 3 分 30 秒 | - |

#### 10.2.2 演示注意事项

- 准备多段演示视频（主视频 + 备用视频）
- 视频分辨率 1080P，格式 MP4
- 添加字幕说明关键操作
- 准备离线版本，防止网络问题
- 提前测试播放设备兼容性

### 10.3 常见问题准备

#### 10.3.1 技术类问题

| 问题 | 参考回答 |
| --- | --- |
| 为什么选择 YOLOv8？ | YOLOv8 是较新的目标检测模型，精度高、速度快，且有完善的预训练模型，适合本项目的实时检测需求。 |
| 姿态估计为什么用 MediaPipe？ | MediaPipe 无需训练即可使用，CPU 可运行，适合本科毕业设计的资源限制，且精度满足应用需求。 |
| 评分规则如何保证客观性？ | 评分基于几何计算和规则引擎，所有标准可量化，避免主观判断，且规则透明可解释。 |
| 系统实时性如何保证？ | 采用轻量级模型、视频降采样处理、关键帧分析，保证单帧处理时间 < 100ms。 |

#### 10.3.2 应用类问题

| 问题 | 参考回答 |
| --- | --- |
| 系统有什么实际应用价值？ | 可降低消防培训人力成本 50% 以上，提供标准化评分，支持训练数据追溯，适合学校和企业培训场景。 |
| 与人工评测相比优势在哪？ | 评分标准统一、可 24 小时使用、数据可追溯、反馈即时、成本更低。 |
| 系统有什么局限性？ | 目前仅支持灭火器操作，复杂场景识别精度有限，需要良好光照条件。 |
| 后续如何改进？ | 增加更多训练场景、引入更先进模型、支持多人同时训练、增加 VR/AR 功能。 |

#### 10.3.3 创新类问题

| 问题 | 参考回答 |
| --- | --- |
| 项目的创新点是什么？ | 将计算机视觉技术应用于消防培训场景，实现自动化评测；设计了可解释的评分规则体系；实现了完整系统而非单纯算法研究。 |
| 与现有系统有什么不同？ | 现有系统多为纯硬件或简单视频录制，本系统实现了智能动作识别和自动评分，且成本低、易部署。 |
| 为什么不做算法创新？ | 本科毕业设计重点在系统完整性和应用价值，使用成熟技术保证项目可完成，同时满足实际应用需求。 |

### 10.4 答辩技巧

- 时间控制：严格控制在 10-15 分钟内，预留问答时间
- 重点突出：核心功能和评分规则是重点，多花时间讲解
- 演示优先：现场演示优先，视频备用，防止技术问题
- 回答技巧：先肯定问题，再给出回答，不会的诚实说明
- 着装仪表：正式着装，展现专业态度
- 材料准备：打印论文摘要、系统截图备查

### 10.5 检查清单

#### 答辩前 1 周

- 论文最终版完成并提交
- PPT 制作完成并演练 3 次以上
- 演示视频录制完成并测试播放
- 系统部署到演示环境
- 准备备用 U 盘（含 PPT、视频、系统）

#### 答辩前 1 天

- 确认答辩时间和地点
- 测试演示设备（投影、音响）
- 准备纸质版材料（论文、PPT 打印）
- 充足休息，保持良好状态

#### 答辩当天

- 提前 30 分钟到达现场
- 再次测试演示设备
- 手机静音，专注答辩
- 记录评委问题和建议

## 附录 A：核心代码示例

### A.1 姿态角度计算

```python
import cv2
import mediapipe as mp
import numpy as np

class PoseAnalyzer:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def calculate_angle(self, a, b, c):
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        ba = a - b
        bc = c - b
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        return np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))

    def analyze_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            shoulder = [landmarks[12].x, landmarks[12].y]
            elbow = [landmarks[14].x, landmarks[14].y]
            wrist = [landmarks[16].x, landmarks[16].y]
            arm_angle = self.calculate_angle(shoulder, elbow, wrist)
            return {"arm_angle": arm_angle, "landmarks": landmarks}
        return None
```

### A.2 评分计算

```python
class ScoreCalculator:
    def __init__(self):
        self.standard_angles = {"arm": (160, 15)}
        self.standard_duration = {
            "total": (15, 25),
            "step1": (2, 3),
            "step2": (2, 3),
            "step3": (1, 2),
            "step4": (1, 2),
            "step5": (3, 5)
        }

    def calculate_pose_score(self, angles):
        arm_angle = angles.get("arm_angle", 0)
        standard, tolerance = self.standard_angles["arm"]
        deviation = abs(arm_angle - standard)
        if deviation <= tolerance:
            return 10
        elif deviation <= tolerance * 2:
            return 7
        elif deviation <= tolerance * 3:
            return 4
        return 1

    def calculate_duration_score(self, durations):
        total_time = sum(durations.values())
        min_t, max_t = self.standard_duration["total"]
        if min_t <= total_time <= max_t:
            return 20
        elif total_time < min_t:
            return max(0, 20 - (min_t - total_time) * 2)
        return max(0, 20 - (total_time - max_t) * 2)

    def calculate_total_score(self, completeness, pose, duration):
        total = completeness + pose + duration
        if total >= 90:
            grade = "优秀"
        elif total >= 80:
            grade = "良好"
        elif total >= 70:
            grade = "合格"
        else:
            grade = "需改进"
        return {
            "total": total,
            "grade": grade,
            "completeness": completeness,
            "pose": pose,
            "duration": duration
        }
```

## 附录 B：参考文献

1. Redmon J, et al. You Only Look Once: Unified, Real-Time Object Detection. CVPR 2016.
2. Lugaresi C, et al. MediaPipe: A Framework for Building Perception Pipelines. 2019.
3. 公安部消防局。消防安全技能培训规范。2020。
4. 张三，李四。基于深度学习的人体姿态估计研究。计算机学报，2023。
5. Ultralytics. YOLOv8 Documentation. <https://docs.ultralytics.com/>

## 附录 C：资源链接

| 资源类型 | 链接 |
| --- | --- |
| YOLOv8 官方 | <https://github.com/ultralytics/ultralytics> |
| MediaPipe 官方 | <https://google.github.io/mediapipe/> |
| Vue3 官方 | <https://vuejs.org/> |
| FastAPI 官方 | <https://fastapi.tiangolo.com/> |
| gRPC 官方 | <https://grpc.io/> |
| Element Plus | <https://element-plus.org/> |
