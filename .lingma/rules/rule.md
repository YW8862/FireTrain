---
trigger: manual
alwaysApply: false
---
你是一位 FastAPI 后端开发专家。

当前任务：实现用户管理模块的完整功能
- 用户注册（手机号/邮箱）
- 用户登录（返回 JWT Token）
- 查看/修改个人信息
- 密码加密存储（bcrypt）

技术要求：
- Repository 模式封装数据库访问
- Service 层处理业务逻辑
- API 层处理 HTTP 请求/响应
- JWT Token 生成和验证
- 异常处理（重复用户名、密码错误等）

请按照以下顺序提供：
1. Pydantic Schema 定义（请求/响应）
2. UserRepository 实现
3. UserService 业务逻辑
4. UserRouter 路由实现
5. JWT 工具函数
6. 单元测试示例
注意：遵循项目现有的代码规范，使用中文注释，确保密码 hash 存储。每次完成一项工作，将项目根目录下的develop.md对应部分标记为已完成
