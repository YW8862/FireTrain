# FireTrain

智能消防技能训练评测系统项目骨架（单体架构初始化阶段）。

## 目录说明

- `frontend/`：前端应用（Vue3 + Element Plus，后续初始化）
- `backend/`：单体后端（FastAPI）
  - `app/api/`：REST 路由
  - `app/core/`：配置与安全
  - `app/middleware/`：中间件
  - `app/models/`：ORM 模型
  - `app/repositories/`：数据访问层
  - `app/schemas/`：请求与响应模型
  - `app/services/`：业务服务层
  - `app/ai/`：AI 推理与规则引擎
- `data/`：本地数据目录（视频、模型等）
- `docs/`：项目文档

## 快速开始（当前为骨架阶段）

1. 检查环境：
   - Python 3.9+
   - Node.js 18+
   - Docker（可选）
2. 查看结构：
   - `make tree`
3. 初始化占位文件：
   - `make init`
4. 检查本机环境：
   - `make check-env`
5. 安装依赖：
   - `make install-backend`
   - `make install-frontend`
6. （可选）启动占位容器：
   - `make docker-up`
   - `make docker-down`

## 下一步开发建议

- 在 `backend/app/schemas/` 中先定义 REST 请求和响应模型。
- 在 `backend/app/services/` 中优先实现用户模块和训练模块最小链路。
- 在 `backend/app/api/` 中实现 REST 路由与业务模块映射。
