# FireTrain

智能消防技能训练评测系统项目骨架（初始化阶段）。

## 目录说明

- `frontend/`：前端应用（Vue3 + Element Plus，后续初始化）
- `gateway/`：API Gateway（FastAPI，后续实现）
- `services/`：微服务目录
  - `user-service/`
  - `training-service/`
  - `scoring-service/`
  - `analytics-service/`
- `proto/`：gRPC 契约定义
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
4. （可选）启动占位容器：
   - `make docker-up`
   - `make docker-down`

## 下一步开发建议

- 在 `proto/` 中先完成 `user.proto`、`training.proto` 等契约定义。
- 在 `services/` 中优先实现 `user-service` 和 `training-service` 最小链路。
- 在 `gateway/` 中实现 REST 到 gRPC 的映射。
