# FireTrain

FireTrain 是一个面向消防技能训练的智能评测系统，当前聚焦灭火器实操训练。项目提供用户端训练流程、AI 视频分析与评分、训练历史与统计看板，以及后台管理能力。

## 项目概览

- 前端基于 `Vue 3 + Vite + Element Plus`
- 后端基于 `FastAPI + SQLAlchemy`
- AI 能力基于 `YOLOv8`、`MediaPipe`、规则评分引擎与 LLM（千问）智能评分
- 默认开发数据库为 `SQLite`，仓库内也提供了 `MySQL` 的 `docker-compose` 编排

当前已覆盖的核心链路：

- 用户注册、登录、JWT 鉴权
- 灭火器训练创建、视频上传、预检测、完整评分
- 训练报告、历史记录、个人统计
- 后台管理员、用户、训练记录、操作日志、管理员视频检测
- 支持多训练类型动态配置（步骤、提示语、评分维度）

## 技术栈

### 后端

- `Python 3.10+`
- `FastAPI 0.109.0`
- `SQLAlchemy 2.0`
- `Pydantic 2`
- `PyTorch 2.2`
- `OpenCV / MediaPipe / Ultralytics`

### 前端

- `Node.js 20+`
- `Vue 3.5`
- `Vite 7`
- `Element Plus`
- `Pinia`
- `Vue Router`
- `ECharts`

## 目录结构

```text
FireTrain/
├── backend/                # FastAPI 后端、AI 推理、测试
├── frontend/               # Vue 前端
├── data/                   # 模型、视频、运行时数据
├── db/                     # SQL 初始化脚本
├── docs/                   # 设计、API、数据库等文档
├── scripts/                # 本地启动、日志、证书等脚本
├── certs/                  # 本地 HTTPS 证书
├── docker-compose.yml
├── Makefile
└── .env.example
```

## 快速开始

### 环境要求

- `Python 3.10+`
- `Node.js 20+`
- `npm 10+`
- `make`（推荐）
- `Docker / Docker Compose`（可选）

### 1. 初始化环境变量

```bash
cp .env.example .env
```

建议至少检查这些配置项：

- `JWT_SECRET_KEY`
- `DATABASE_URL`
- `MODEL_DIR`
- `VIDEO_DIR`
- `LLM_API_KEY`

### 2. 本地开发启动

推荐直接使用仓库自带脚本：

```bash
make install-backend
make install-frontend
make local-up
```

常用配套命令：

```bash
make local-logs
make local-down
make help
```

脚本会处理这些事情：

- 创建并使用 `backend/.venv`
- 初始化数据库
- 启动后端与前端
- 将日志写入 `logs/`

### 3. 手动启动（需要时）

后端：

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python scripts/init_db.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

### 4. Docker 启动

```bash
docker compose up -d
docker compose logs -f
docker compose down
```

说明：

- 当前 `docker-compose.yml` 中已包含 `mysql`、`backend`、`frontend`
- 后端容器默认仍使用 `SQLite` 数据库地址；如果要切到 MySQL，需要同步调整 `DATABASE_URL`

## 访问地址

- 前端：`http://localhost:5173`
- 后端：`http://localhost:8000`
- Swagger：`http://localhost:8000/docs`
- ReDoc：`http://localhost:8000/redoc`
- 健康检查：`http://localhost:8000/health`

如果本地配置了证书，也可以通过 HTTPS 启动部分脚本流程。

## 常用命令

```bash
make install-backend   # 安装后端依赖
make install-frontend  # 安装前端依赖
make lint              # 前后端代码检查
make test              # 运行关键后端测试
make test-backend-all  # 运行完整后端测试
make test-frontend     # 运行前端测试
make docker-up         # Docker 启动
make docker-down       # Docker 停止
```

## API 概览

当前后端主要路由前缀如下：

| 模块 | 前缀 | 说明 |
|------|------|------|
| 用户 | `/api/user` | 注册、登录、个人信息、退出、身份切换 |
| 训练 | `/api/training` | 开始训练、视频上传、预检测、评分、历史查询 |
| 统计 | `/api/stats` | 个人统计、趋势分析、步骤分析、总览 |
| 后台 | `/api/admin` | 管理员、用户、训练数据、操作日志 |
| 后台视频检测 | `/api/admin/video` | 管理员上传视频检测 |

# 操作日志（返回中文操作类型）
curl -X GET "http://localhost:8000/api/admin/logs?action=DELETE_USER&page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"

示例：

```bash
curl -X POST "http://localhost:8000/api/user/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"
```

```bash
curl -X POST "http://localhost:8000/api/training/start" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "training_type": "extinguisher",
    "duration_seconds": 60
  }'
```

更完整的接口说明见 `docs/API 接口文档.md`。

## 前端页面

用户侧主要页面：

- `/`
- `/login`
- `/register`
- `/training`
- `/report/:id`
- `/history`
- `/profile`
- `/stats`

后台主要页面：

- `/admin/dashboard`
- `/admin/users`
- `/admin/trainings`
- `/admin/video-upload`
- `/admin/logs`
- `/admin/admins`

## 测试与代码检查

后端：

```bash
cd backend
. .venv/bin/activate
pytest
```

前端：

```bash
cd frontend
npm run lint
npm run format:check
npm run test
```

如果只想走项目统一入口，直接执行：

```bash
make lint
make test
```

## 相关文档

- `docs/API 接口文档.md`
- `docs/数据库设计.md`
- `docs/YOLOv8_检测模块使用指南.md`
- `docs/身份切换功能说明.md`
- `scripts/README.md`
- `develop.md`

## 开发提示

- 后端入口：`backend/app/main.py`
- 前端路由：`frontend/src/router/index.js`
- AI 推理主服务：`backend/app/ai/training_inference_service.py`
- 训练数据访问层：`backend/app/repositories/training_repository.py`
- 评分服务（含规则引擎 + LLM 评分）：`backend/app/ai/llm_scoring_service.py`
- 训练类型配置（动态步骤/提示语）：`frontend/src/utils/trainingType.js`
- PDF 报告导出：`frontend/src/utils/reportExport.js`

## 注意事项

- `README` 默认按当前代码状态编写，若新增训练类型或改动接口，请同步更新文档
- `.env.example` 仅应保留示例值，部署前请替换全部敏感配置
- 本地脚本依赖 `backend/.venv`，首次运行前请先执行 `make install-backend`

