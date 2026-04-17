# FireTrain API 接口文档

> 本文档按当前后端代码实现更新。若本文档与运行中的 Swagger 不一致，请以 `http://localhost:8000/docs` 为准。

## 1. 接口概览

### 基础信息

- Base URL: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- 健康检查: `GET /health`
- 根路径: `GET /`

### 路由分组

| 分组 | 前缀 | 说明 |
|------|------|------|
| 用户 | `/api/user` | 注册、登录、个人资料、退出、身份切换 |
| 训练 | `/api/training` | 训练创建、视频上传、预检测、完成评分、历史查询 |
| 统计 | `/api/stats` | 个人统计、趋势、步骤分析、统计总览 |
| 后台管理 | `/api/admin` | 管理员、普通用户、训练数据、仪表盘、操作日志 |
| 管理员视频检测 | `/api/admin/video` | 管理员代用户上传视频并异步分析 |

### 角色说明

- `student`：普通用户
- `admin`：管理员
- `root`：超级管理员
- 兼容旧值 `user`，系统内部仍有部分逻辑会兼容处理

## 2. 认证说明

### Bearer Token

除注册、登录、根路径和健康检查外，大部分接口都需要在请求头中带上 Token：

```text
Authorization: Bearer <your_token>
```

### 获取 Token

调用 `POST /api/user/login`，使用 `application/x-www-form-urlencoded` 提交：

```text
username=<用户名或邮箱>
password=<密码>
```

### Token 相关说明

- Token 默认有效期为 30 分钟
- `POST /api/user/logout` 会将当前 Token 加入黑名单
- `POST /api/user/switch-role` 会返回一个新的 Token，前端应替换本地旧 Token

## 3. 系统基础接口

### 3.1 根路径

**接口**：`GET /`

**响应示例**：

```json
{
  "message": "欢迎使用 FireTrain 智能消防技能训练评测系统",
  "version": "0.1.0",
  "docs": "/docs",
  "health": "/health"
}
```

### 3.2 健康检查

**接口**：`GET /health`

**响应示例**：

```json
{
  "status": "ok"
}
```

## 4. 用户接口

### 4.1 用户注册

**接口**：`POST /api/user/register`

**认证**：否

**请求体**：

```json
{
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "password": "123456",
  "phone": "13800138000"
}
```

**响应示例**：

```json
{
  "message": "注册成功",
  "user_id": 1
}
```

### 4.2 用户登录

**接口**：`POST /api/user/login`

**认证**：否

**提交格式**：`application/x-www-form-urlencoded`

**请求参数**：

```text
username=zhangsan
password=123456
```

**响应示例**：

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_info": {
    "id": 1,
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "phone": "13800138000",
    "role": "student",
    "can_switch_role": false,
    "original_role": null,
    "is_active": true,
    "last_login_at": "2026-04-17T10:00:00Z",
    "created_at": "2026-04-01T08:00:00Z"
  }
}
```

### 4.3 获取当前用户信息

**接口**：`GET /api/user/profile`

**认证**：是

**响应示例**：

```json
{
  "id": 1,
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "phone": "13800138000",
  "role": "student",
  "can_switch_role": false,
  "original_role": null,
  "is_active": true,
  "last_login_at": "2026-04-17T10:00:00Z",
  "created_at": "2026-04-01T08:00:00Z"
}
```

### 4.4 更新当前用户信息

**接口**：`PUT /api/user/profile`

**认证**：是

**请求体**：

```json
{
  "email": "new@example.com",
  "phone": "13900000000",
  "current_password": "123456",
  "new_password": "654321"
}
```

说明：

- `email`、`phone` 可单独修改
- 若要修改密码，需同时提供 `current_password` 和 `new_password`

### 4.5 退出登录

**接口**：`POST /api/user/logout`

**认证**：是

**响应示例**：

```json
{
  "message": "退出登录成功",
  "code": 200
}
```

### 4.6 身份切换

**接口**：`POST /api/user/switch-role`

**认证**：是

**请求体**：

```json
{
  "target_role": "student"
}
```

说明：

- 主要用于允许切换身份的管理员
- `target_role` 支持 `student`、`admin`，兼容旧值 `user`
- 成功后会返回新的 `token`

**响应示例**：

```json
{
  "role": "student",
  "original_role": "admin",
  "can_switch_role": true,
  "token": "NEW_JWT_TOKEN"
}
```

## 5. 训练接口

### 5.1 开始训练

**接口**：`POST /api/training/start`

**认证**：是

**请求体**：

```json
{
  "training_type": "extinguisher",
  "duration_seconds": 60
}
```

**响应示例**：

```json
{
  "training_id": 1,
  "status": "created",
  "message": "训练已创建，请上传视频"
}
```

### 5.2 上传训练视频路径

**接口**：`POST /api/training/upload`

**认证**：是

**说明**：该接口接收“服务器可访问的视频路径”，并非文件二进制上传。

**请求体**：

```json
{
  "training_id": 1,
  "video_path": "/absolute/or/relative/path/to/video.mp4"
}
```

**响应示例**：

```json
{
  "message": "视频上传成功",
  "training_id": 1,
  "status": "processing",
  "video_path": "/path/to/video.mp4"
}
```

### 5.3 上传训练视频文件

**接口**：`POST /api/training/upload-file/{training_id}`

**认证**：是

**提交格式**：`multipart/form-data`

**表单字段**：

- `file`：视频文件

**响应示例**：

```json
{
  "message": "视频上传成功",
  "training_id": 1,
  "status": "processing",
  "video_path": "/home/yw/FireTrain/data/videos/xxx.mp4",
  "file_size": 10485760,
  "save_duration_ms": 132
}
```

### 5.4 视频预检测

**接口**：`POST /api/training/precheck/{training_id}`

**认证**：是

**说明**：对训练视频做快速 AI 检测，检查视频是否具备有效动作信号。

**响应示例**：

```json
{
  "is_valid": true,
  "reason": "检测通过"
}
```

当没有视频或分析失败时，也可能返回：

```json
{
  "is_valid": false,
  "reason": "未上传视频"
}
```

### 5.5 完成训练并评分

**接口**：`POST /api/training/complete/{training_id}`

**认证**：是

**查询参数**：

- `use_ai_scoring`：是否启用 AI 评分，默认 `true`

**说明**：

- 启用 AI 评分时，后端会执行：
  1. YOLOv8 检测
  2. MediaPipe 姿态分析
  3. 规则引擎/评分逻辑汇总
- 若相关条件不满足，接口会返回业务错误

**响应示例**：

```json
{
  "message": "训练已完成",
  "training_id": 1,
  "status": "done",
  "total_score": 85.5,
  "feedback": "优秀！动作规范，流程熟练，继续保持",
  "used_ai_scoring": true,
  "scoring_details": {
    "total_score": 85.5,
    "step_scores": {
      "lift_extinguisher": {
        "step_name": "提灭火器",
        "score": 18.0,
        "is_correct": true,
        "feedback": "动作标准"
      }
    },
    "feedback": "整体表现良好",
    "suggestions": [
      "优先加强步骤：压把手"
    ],
    "performance_level": "good",
    "dimension_scores": {
      "completeness": 88,
      "stability": 82,
      "timing": 86
    }
  }
}
```

### 5.6 获取训练历史

**接口**：`GET /api/training/history`

**认证**：是

**查询参数**：

- `page`：页码，默认 `1`
- `page_size`：每页数量，默认 `10`
- `status`：状态筛选，如 `created`、`processing`、`done`
- `start_date`：开始时间，ISO 8601
- `end_date`：结束时间，ISO 8601

**响应示例**：

```json
{
  "total": 25,
  "page": 1,
  "page_size": 10,
  "records": [
    {
      "id": 1,
      "user_id": 1,
      "username": null,
      "training_type": "extinguisher",
      "status": "done",
      "total_score": 88.5,
      "step_scores": {
        "_performance_level": "good"
      },
      "video_path": "/path/to/video.mp4",
      "duration_seconds": 60,
      "started_at": "2026-04-17T10:00:00Z",
      "completed_at": "2026-04-17T10:02:00Z",
      "feedback": "整体表现良好",
      "created_at": "2026-04-17T10:00:00Z"
    }
  ]
}
```

### 5.7 获取训练详情

**接口**：`GET /api/training/{training_id}`

**认证**：是

**权限说明**：

- 普通用户只能查看自己的训练记录
- `admin` / `root` 可以查看全部训练记录

**响应示例**：

```json
{
  "id": 1,
  "user_id": 1,
  "username": "zhangsan",
  "training_type": "extinguisher",
  "status": "done",
  "total_score": 88.5,
  "step_scores": {
    "_performance_level": "good",
    "_suggestions": [
      "整体动作较完整，可继续强化压把后的持续扫射稳定性"
    ],
    "_dimension_scores": {
      "completeness": 88,
      "stability": 82,
      "timing": 86
    }
  },
  "video_path": "/path/to/video.mp4",
  "duration_seconds": 60,
  "started_at": "2026-04-17T10:00:00Z",
  "completed_at": "2026-04-17T10:02:00Z",
  "feedback": "整体表现良好",
  "created_at": "2026-04-17T10:00:00Z",
  "action_count": 0,
  "actions": null,
  "suggestions": [
    "整体动作较完整，可继续强化压把后的持续扫射稳定性"
  ],
  "dimension_scores": {
    "completeness": 88,
    "stability": 82,
    "timing": 86
  },
  "performance_level": "good",
  "analysis_summary": {
    "training_type": "extinguisher",
    "video_duration": 60.0
  }
}
```

### 5.8 删除训练记录

**接口**：`DELETE /api/training/{training_id}`

**认证**：是

**说明**：仅允许用户删除自己的未完成训练记录。

**响应示例**：

```json
{
  "message": "训练记录删除成功",
  "training_id": 1
}
```

## 6. 统计接口

### 6.1 获取个人统计

**接口**：`GET /api/stats/personal`

**认证**：是

**响应示例**：

```json
{
  "user_id": 1,
  "total_trainings": 10,
  "completed_trainings": 8,
  "total_training_seconds": 3600,
  "average_score": 85.5,
  "best_score": 95.0,
  "last_training_at": "2026-04-17T10:00:00Z"
}
```

### 6.2 获取训练趋势

**接口**：`GET /api/stats/trend`

**认证**：是

**查询参数**：

- `days`：查询最近 N 天，默认 `7`，最大 `30`

**响应示例**：

```json
{
  "trend_data": [
    {
      "date": "2026-04-17",
      "training_count": 3,
      "average_score": 85.5,
      "best_score": 90.0
    }
  ],
  "total_days": 1
}
```

### 6.3 获取步骤分析

**接口**：`GET /api/stats/step-analysis`

**认证**：是

**响应示例**：

```json
{
  "step_analysis": [
    {
      "step_name": "提灭火器",
      "average_score": 18.5,
      "success_rate": 92.5,
      "improvement_suggestion": "保持站姿稳定"
    }
  ]
}
```

### 6.4 获取统计总览

**接口**：`GET /api/stats/overview`

**认证**：是

**查询参数**：

- `days`：趋势天数，默认 `7`

**响应示例**：

```json
{
  "personal_stats": {
    "user_id": 1,
    "total_trainings": 10,
    "completed_trainings": 8,
    "total_training_seconds": 3600,
    "average_score": 85.5,
    "best_score": 95.0,
    "last_training_at": "2026-04-17T10:00:00Z"
  },
  "recent_trend": {
    "trend_data": [
      {
        "date": "2026-04-17",
        "training_count": 3,
        "average_score": 85.5,
        "best_score": 90.0
      }
    ],
    "total_days": 1
  },
  "step_analysis": {
    "step_analysis": [
      {
        "step_name": "提灭火器",
        "average_score": 18.5,
        "success_rate": 92.5,
        "improvement_suggestion": "保持站姿稳定"
      }
    ]
  }
}
```

## 7. 后台管理接口

> 除特殊说明外，本章接口均需要 `admin` 或 `root` 权限；管理员账户管理中的部分接口仅 `root` 可用。

### 7.1 管理员账户管理（仅 Root）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/admins` | 分页查询管理员列表 |
| POST | `/api/admin/admins` | 创建管理员 |
| GET | `/api/admin/admins/{admin_id}` | 获取管理员详情 |
| PUT | `/api/admin/admins/{admin_id}` | 更新管理员资料 |
| PUT | `/api/admin/admins/{admin_id}/role` | 修改管理员角色 |
| PUT | `/api/admin/admins/{admin_id}/reset-password` | 重置管理员密码 |
| DELETE | `/api/admin/admins/{admin_id}` | 删除管理员 |

**管理员列表查询参数**：

- `page`
- `page_size`
- `keyword`

**创建管理员请求体示例**：

```json
{
  "username": "admin02",
  "email": "admin02@example.com",
  "password": "123456",
  "role": "admin",
  "can_switch_role": true
}
```

**重置管理员密码响应示例**：

```json
{
  "message": "管理员密码重置成功",
  "temp_password": "Ab12Cd34",
  "warning": "请立即将此密码告知管理员，并要求其首次登录后修改"
}
```

### 7.2 普通用户管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/users` | 获取用户列表 |
| POST | `/api/admin/users` | 创建普通用户 |
| GET | `/api/admin/users/{user_id}` | 获取普通用户详情 |
| PUT | `/api/admin/users/{user_id}` | 更新普通用户 |
| PUT | `/api/admin/users/{user_id}/reset-password` | 重置用户密码 |
| DELETE | `/api/admin/users/{user_id}` | 删除用户 |
| GET | `/api/admin/users/{user_id}/trainings` | 查看用户训练记录 |
| GET | `/api/admin/users/{user_id}/stats/overview` | 查看用户统计概览 |

**用户列表查询参数**：

- `page`
- `page_size`
- `keyword`
- `role`

说明：

- 普通管理员查询 `/api/admin/users` 时，只能看到普通用户
- `root` 可通过 `role=all|student|admin|root` 查看不同角色范围

**创建普通用户请求体示例**：

```json
{
  "username": "student01",
  "email": "student01@example.com",
  "password": "123456",
  "phone": "13800138000",
  "is_active": true,
  "can_switch_role": false,
  "original_role": null
}
```

**重置用户密码响应示例**：

```json
{
  "message": "密码重置成功",
  "temp_password": "Xy12Za89",
  "warning": "请立即将此密码告知用户，并要求其首次登录后修改"
}
```

### 7.3 训练数据管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/trainings` | 查询全部训练记录 |
| DELETE | `/api/admin/trainings/{training_id}` | 删除训练记录 |

**查询参数**：

- `page`
- `page_size`
- `user_id`
- `training_type`
- `status`
- `start_date`（`YYYY-MM-DD`）
- `end_date`（`YYYY-MM-DD`）

### 7.4 仪表盘统计

**接口**：`GET /api/admin/statistics/dashboard`

**说明**：返回后台首页所需的聚合统计数据。

**响应示例**：

```json
{
  "user_statistics": {
    "total_users": 100,
    "new_users_today": 3,
    "active_users": 100,
    "role_distribution": {
      "student": 96,
      "admin": 3,
      "root": 1
    }
  },
  "training_statistics": {
    "total_trainings": 500,
    "trainings_today": 12,
    "average_score": 84.6,
    "type_distribution": {
      "extinguisher": 500
    }
  },
  "video_statistics": {
    "pending": 0,
    "processing": 1,
    "completed": 30,
    "failed": 2
  },
  "timestamp": "2026-04-17T10:00:00Z"
}
```

### 7.5 操作日志

**接口**：`GET /api/admin/logs`

**查询参数**：

- `page`
- `page_size`
- `admin_id`
- `action`

说明：

- `root` 可以查看全部日志
- `admin` 查询时会被限制为仅查看自己的日志

**响应示例**：

```json
{
  "logs": [
    {
      "id": 1,
      "admin_id": 2,
      "action": "CREATE_USER",
      "target_type": "user",
      "target_id": 101,
      "details": {
        "username": "student01"
      },
      "ip_address": "127.0.0.1",
      "created_at": "2026-04-17T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

## 8. 管理员视频检测接口

### 8.1 上传视频并开始异步分析

**接口**：`POST /api/admin/video/upload`

**权限**：`admin` / `root`

**提交格式**：`multipart/form-data`

**表单字段**：

- `file`：视频文件
- `username`：结果归属的用户名
- `training_type`：训练类型，默认 `extinguisher`

**响应示例**：

```json
{
  "message": "视频上传成功，正在进行 AI 分析",
  "training_id": 1001,
  "username": "zhangsan",
  "file_name": "demo.mp4",
  "status": "processing",
  "save_duration_ms": 146
}
```

### 8.2 查询视频分析状态

**接口**：`GET /api/admin/video/status/{training_id}`

**权限**：`admin` / `root`

**响应示例**：

```json
{
  "training_id": 1001,
  "status": "processing",
  "total_score": null,
  "feedback": null,
  "performance_level": null,
  "analysis_summary": null,
  "completed_at": null,
  "stage": "video_analysis",
  "stage_label": "视频分析中",
  "progress": 56.0,
  "stage_message": "已处理 280 / 500 帧"
}
```

分析完成后可能返回：

```json
{
  "training_id": 1001,
  "status": "done",
  "total_score": 89.5,
  "feedback": "整体表现良好",
  "performance_level": "good",
  "analysis_summary": {
    "completed_steps_count": 5
  },
  "completed_at": "2026-04-17T10:05:00Z",
  "stage": "done",
  "stage_label": "已完成",
  "progress": 100.0,
  "stage_message": null
}
```

### 8.3 取消上传并删除记录

**接口**：`DELETE /api/admin/video/upload/{training_id}`

**权限**：`admin` / `root`

**响应示例**：

```json
{
  "message": "已取消上传并删除相关文件",
  "training_id": 1001
}
```

## 9. 常见状态码与错误格式

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误或业务条件不满足 |
| 401 | 未登录、Token 无效或已失效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务端内部错误 |

### 错误响应格式

当前项目主要使用 FastAPI 默认错误结构：

```json
{
  "detail": "错误描述信息"
}
```

常见错误信息示例：

- `Token 已失效`
- `无法验证凭据`
- `用户不存在`
- `用户名已存在`
- `训练记录不存在`
- `无权操作此训练记录`

## 10. 快速调用示例

### 10.1 注册

```bash
curl -X POST "http://localhost:8000/api/user/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "123456",
    "phone": "13800138000"
  }'
```

### 10.2 登录

```bash
curl -X POST "http://localhost:8000/api/user/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=123456"
```

### 10.3 开始训练

```bash
curl -X POST "http://localhost:8000/api/training/start" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "training_type": "extinguisher",
    "duration_seconds": 60
  }'
```

### 10.4 上传视频文件

```bash
curl -X POST "http://localhost:8000/api/training/upload-file/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/video.mp4"
```

### 10.5 完成训练并评分

```bash
curl -X POST "http://localhost:8000/api/training/complete/1?use_ai_scoring=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 10.6 查询统计总览

```bash
curl -X GET "http://localhost:8000/api/stats/overview?days=7" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 11. 代码位置

接口定义位于：

- `backend/app/api/users.py`
- `backend/app/api/training.py`
- `backend/app/api/statistics.py`
- `backend/app/api/admin.py`
- `backend/app/api/admin_videos.py`

Schema 定义位于：

- `backend/app/schemas/user.py`
- `backend/app/schemas/training.py`
- `backend/app/schemas/statistics.py`
- `backend/app/schemas/admin_video.py`

---

**文档版本**：v2.0  
**最后更新**：2026-04-17  
**维护者**：FireTrain 开发团队
