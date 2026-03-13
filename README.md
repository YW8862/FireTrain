# 🔥 FireTrain - 消防技能训练系统

<div align="center">

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/node-20.x-green.svg)](https://nodejs.org/)
[![Vue](https://img.shields.io/badge/vue-3.5.x-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.109.0-green.svg)](https://fastapi.tiangolo.com/)

**基于 AI 视觉识别的消防技能智能训练平台**

[特性](#--功能特性) • [快速开始](#--快速开始) • [技术栈](#-技术栈) • [项目结构](#-项目结构) • [API 文档](#-api-文档) • [开发指南](#-开发指南)

</div>

---

## 📖 项目简介

FireTrain 是一个现代化的消防技能训练系统，结合了计算机视觉和人工智能技术，为消防员提供智能化、标准化的操作训练平台。系统通过 YOLOv8 和 MediaPipe 实时分析操作动作，自动评估训练质量，帮助消防员掌握正确的操作流程。

### 🎯 核心优势

- **AI 智能评估** - 基于计算机视觉技术，实时分析操作动作
- **标准化流程** - 严格按照消防操作规范，培养正确习惯
- **数据统计分析** - 记录训练历史，可视化展示进步轨迹
- **实时反馈** - 即时纠正错误动作，提升训练效果

---

## ✨ 功能特性

### 👤 用户功能

- ✅ **用户认证系统** - 注册、登录、JWT Token 认证
- ✅ **个人中心** - 查看个人信息、训练统计
- ✅ **训练记录** - 完整的训练历史查询
- ✅ **数据报表** - 个人训练数据分析与可视化

### 🎓 训练功能

- ✅ **灭火器操作训练** - 6 步标准流程教学与考核
  1. 准备阶段（个人防护、逃生路线确认）
  2. 提起灭火器（腿部力量使用）
  3. 拔保险销（拉环操作）
  4. 握喷管（双手稳固握持）
  5. 瞄准火源（对准根部，2-3 米距离）
  6. 压把手（均匀用力，左右扫射）

- ✅ **AI 动作识别** - 实时姿态分析与评分
- ✅ **视频录制** - 训练过程全程记录
- ✅ **即时反馈** - 每步操作实时评估与建议

### 📊 管理功能

- ✅ **训练统计** - 多维度数据分析（ECharts 可视化）
- ✅ **成绩报告** - 详细评分与改进建议
- ✅ **历史记录** - 可追溯的训练档案

---

## 🛠️ 技术栈

### 后端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| **Python** | 3.9+ | 主要编程语言 |
| **FastAPI** | 0.109.0 | 高性能 Web 框架 |
| **SQLAlchemy** | 2.0.25 | ORM 框架 |
| **Pydantic** | 2.5.3 | 数据验证 |
| **YOLOv8** | 8.1.10 | 目标检测模型 |
| **MediaPipe** | 0.10.11 | 姿态识别 |
| **OpenCV** | 4.9.0.80 | 计算机视觉 |
| **PyTorch** | 2.2.0 | 深度学习框架 |

### 前端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| **Vue 3** | 3.5.30 | 渐进式 JavaScript 框架 |
| **Vite** | 7.3.1 | 下一代前端构建工具 |
| **Element Plus** | 2.13.5 | Vue 3 组件库 |
| **Pinia** | 3.0.4 | Vue 状态管理 |
| **Vue Router** | 5.0.3 | 官方路由管理器 |
| **Axios** | 1.13.6 | HTTP 客户端 |
| **ECharts** | 6.0.0 | 数据可视化库 |

### 基础设施

- **Docker** - 容器化部署
- **MySQL 8.0** - 生产数据库
- **SQLite** - 开发数据库
- **HTTPS** - SSL/TLS 加密通信

---

## 📁 项目结构

```
FireTrain/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── ai/                # AI 模块
│   │   │   ├── fire_extinguisher_detector.py  # 灭火器检测
│   │   │   ├── pose_analyzer.py              # 姿态分析
│   │   │   ├── rule_engine.py                # 规则引擎
│   │   │   └── feedback_generator.py         # 反馈生成
│   │   ├── api/               # API 路由
│   │   │   ├── users.py       # 用户接口
│   │   │   ├── training.py    # 训练接口
│   │   │   └── statistics.py  # 统计接口
│   │   ├── core/              # 核心配置
│   │   │   ├── config.py      # 配置管理
│   │   │   └── security.py    # 安全认证
│   │   ├── db/                # 数据库
│   │   │   ├── base.py        # 基类
│   │   │   └── session.py     # 会话管理
│   │   ├── models/            # 数据模型
│   │   │   ├── user.py        # 用户模型
│   │   │   └── training_record.py  # 训练记录
│   │   ├── schemas/           # Pydantic 模式
│   │   ├── services/          # 业务逻辑
│   │   └── middleware/        # 中间件
│   ├── tests/                 # 测试文件
│   ├── requirements.txt       # Python 依赖
│   └── Dockerfile            # Docker 配置
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   │   ├── HomeView.vue          # 首页
│   │   │   ├── TrainingView.vue      # 训练页
│   │   │   ├── HistoryView.vue       # 历史页
│   │   │   ├── StatsView.vue         # 统计页
│   │   │   └── ProfileView.vue       # 个人中心
│   │   ├── components/        # 公共组件
│   │   │   └── NavBar.vue     # 导航栏
│   │   ├── api/               # API 调用
│   │   ├── store/             # 状态管理
│   │   ├── router/            # 路由配置
│   │   └── utils/             # 工具函数
│   ├── package.json          # 依赖配置
│   └── Dockerfile            # Docker 配置
│
├── data/                      # 数据目录
│   ├── models/               # AI 模型
│   └── videos/               # 训练视频
│
├── db/                        # 数据库脚本
│   └── init.sql              # 初始化脚本
│
├── certs/                     # SSL 证书
│   ├── cert.pem
│   └── key.pem
│
├── docker-compose.yml         # Docker 编排
├── .env.example              # 环境变量示例
└── Makefile                  # 快捷命令
```

---

## 🚀 快速开始

### 前置要求

- **Python** 3.9+ (推荐 3.10)
- **Node.js** 20.x
- **npm** 10+
- **Docker** 29+ (可选，用于容器化部署)
- **Docker Compose** V2 5.0+

### 方式一：Docker 部署（推荐）

#### 1. 克隆项目

```bash
git clone <repository-url>
cd FireTrain
```

#### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，根据需要修改配置
```

#### 3. 启动服务

```bash
# 使用 Docker Compose 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 4. 访问应用

- **前端**: http://localhost:5173
- **后端 API**: https://localhost:8000
- **API 文档**: https://localhost:8000/docs

### 方式二：本地开发

#### 1. 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python scripts/init_db.py

# 启动后端服务
uvicorn app.main:app --reload --ssl-keyfile=../certs/key.pem --ssl-certfile=../certs/cert.pem
```

#### 2. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

#### 3. 访问应用

- **前端**: http://localhost:5173
- **后端 API**: https://localhost:8000

---

## 🔐 认证说明

### JWT Token 机制

系统采用 JWT（JSON Web Token）进行身份认证：

1. **登录** - 用户输入账号密码获取 access_token
2. **存储** - Token 保存在 localStorage
3. **请求** - 每次请求携带 Token
4. **验证** - 后端验证 Token 有效性

### 受保护的路由

以下路由需要登录后访问：

- `/training` - 训练页面
- `/history` - 历史记录
- `/stats` - 数据统计
- `/profile` - 个人中心
- `/report/:id` - 训练报告

---

## 📡 API 文档

### 端点概览

#### 用户接口 (`/api/users`)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/register` | 用户注册 | ❌ |
| POST | `/login` | 用户登录 | ❌ |
| GET | `/me` | 获取当前用户信息 | ✅ |
| PUT | `/me` | 更新用户信息 | ✅ |
| POST | `/logout` | 退出登录 | ✅ |

#### 训练接口 (`/api/training`)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/` | 开始训练 | ✅ |
| GET | `/{id}` | 获取训练详情 | ✅ |
| PUT | `/{id}/complete` | 完成训练 | ✅ |
| DELETE | `/{id}` | 取消训练 | ✅ |
| GET | `/history` | 获取历史记录 | ✅ |

#### 统计接口 (`/api/statistics`)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/overview` | 总体统计 | ✅ |
| GET | `/daily` | 每日统计 | ✅ |
| GET | `/weekly` | 每周统计 | ✅ |
| GET | `/monthly` | 每月统计 | ✅ |

### 请求示例

#### 用户登录

```bash
curl -X POST "https://localhost:8000/api/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

#### 开始训练

```bash
curl -X POST "https://localhost:8000/api/training/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "training_type": "fire_extinguisher",
    "duration_seconds": 120
  }'
```

完整 API 文档请访问：https://localhost:8000/docs

---

## 🧪 测试

### 后端测试

```bash
cd backend
source venv/bin/activate

# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_user_api.py -v

# 查看测试覆盖率
pytest --cov=app --cov-report=html
```

### 前端测试

```bash
cd frontend

# 运行测试
npm run test

# 代码检查
npm run lint

# 格式化检查
npm run format:check
```

---

## 🛠️ 开发指南

### 添加新的训练类型

1. **后端** - 在 `backend/app/ai/` 添加新的检测逻辑
2. **评分规则** - 在 `backend/app/services/scoring_service.py` 添加评分标准
3. **前端页面** - 在 `frontend/src/views/` 添加训练界面
4. **路由配置** - 更新 `frontend/src/router/index.js`

### 数据库迁移

```bash
# 使用 Alembic 进行迁移（推荐）
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### 添加新的 API 端点

```python
# backend/app/api/your_module.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/your-module", tags=["your-module"])

@router.get("/endpoint")
async def get_endpoint():
    return {"message": "Hello"}
```

---

## 📊 评分系统

### 灭火器操作评分标准

| 步骤 | 权重 | 评分要点 |
|------|------|----------|
| **提灭火器** | 20% | 姿势正确、使用腿部力量 |
| **拔保险销** | 20% | 拉环操作准确、力度适中 |
| **握喷管** | 15% | 双手稳固、位置正确 |
| **瞄准火源** | 20% | 对准根部、距离适当（2-3 米） |
| **压把手** | 25% | 用力均匀、左右扫射 |

### 等级评定

- **优秀** (≥90 分) - 操作规范，动作标准
- **良好** (80-89 分) - 操作基本规范，有小瑕疵
- **合格** (60-79 分) - 完成操作，需改进
- **待改进** (<60 分) - 操作不规范，需重新训练

---

## 🔧 常见问题

### Q: 无法访问摄像头？

A: 请检查浏览器权限设置：
- Chrome: 地址栏左侧锁图标 → 摄像头权限 → 允许
- Firefox: 选项 → 隐私与安全 → 权限 → 摄像头

### Q: HTTPS 证书警告？

A: 开发环境使用自签名证书，出现警告是正常的。可以点击"继续访问"或导入 `certs/` 目录中的证书。

### Q: 数据库连接失败？

A: 检查以下几点：
1. 确认 MySQL 服务已启动
2. 检查 `.env` 文件中的数据库配置
3. 确认数据库用户权限正确

### Q: AI 模型加载失败？

A: 确保已下载模型文件：
```bash
# YOLOv8 模型会自动下载
# 检查路径：backend/yolov8n.pt
```

