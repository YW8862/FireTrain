# FireTrain API 接口文档

## 📋 目录

- [1. 接口概览](#1-接口概览)
- [2. 认证说明](#2-认证说明)
- [3. 用户管理接口](#3-用户管理接口)
- [4. 训练管理接口](#4-训练管理接口)
- [5. 统计分析接口](#5-统计分析接口)
- [6. 错误码说明](#6-错误码说明)
- [7. 快速开始](#7-快速开始)

---

## 1. 接口概览

### 基础信息

- **Base URL**: `http://localhost:8000`
- **API 版本**: v1
- **文档地址**: 
  - Swagger UI: http://localhost:8000/docs
  - ReDoc: http://localhost:8000/redoc

### 接口分类

| 分类 | 前缀 | 说明 |
|------|------|------|
| 用户管理 | `/api/user/*` | 注册、登录、个人信息管理 |
| 训练管理 | `/api/training/*` | 训练任务、视频上传、评分查询 |
| 统计分析 | `/api/stats/*` | 个人统计、趋势分析、步骤分析 |

---

## 2. 认证说明

### JWT Token 认证

大部分接口需要使用 JWT Token 进行认证。

**请求头格式:**
```
Authorization: Bearer <your_token>
```

**获取 Token:**
1. 调用 `POST /api/user/login` 接口
2. 使用用户名和密码登录
3. 从响应中获取 `token` 字段

**Token 有效期:** 30 分钟

---

## 3. 用户管理接口

### 3.1 用户注册

**接口**: `POST /api/user/register`

**请求参数:**
```json
{
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "password": "123456",
  "phone": "13800138000"
}
```

**响应示例:**
```json
{
  "message": "注册成功",
  "user_id": 1
}
```

**状态码:**
- `201`: 注册成功
- `400`: 用户名已存在

---

### 3.2 用户登录

**接口**: `POST /api/user/login`

**请求参数 (Form Data):**
```
username: zhangsan
password: 123456
```

**响应示例:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_info": {
    "id": 1,
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "role": "student",
    "is_active": true,
    "created_at": "2026-03-11T10:00:00Z"
  }
}
```

**状态码:**
- `200`: 登录成功
- `401`: 用户名或密码错误

---

### 3.3 获取用户信息

**接口**: `GET /api/user/profile`

**认证**: ✅ 需要 Bearer Token

**响应示例:**
```json
{
  "id": 1,
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "phone": "13800138000",
  "role": "student",
  "is_active": true,
  "last_login_at": "2026-03-11T10:00:00Z",
  "created_at": "2026-03-11T10:00:00Z"
}
```

---

### 3.4 更新用户信息

**接口**: `PUT /api/user/profile`

**认证**: ✅ 需要 Bearer Token

**请求参数:**
```json
{
  "nickname": "张三",
  "phone": "13800138000",
  "avatar_url": "https://example.com/avatar.jpg"
}
```

---

### 3.5 退出登录

**接口**: `POST /api/user/logout`

**认证**: ✅ 需要 Bearer Token

**响应示例:**
```json
{
  "message": "退出登录成功",
  "code": 200
}
```

---

## 4. 训练管理接口

### 4.1 开始训练

**接口**: `POST /api/training/start`

**请求参数:**
```json
{
  "training_type": "extinguisher",
  "duration_seconds": 60
}
```

**响应示例:**
```json
{
  "training_id": 1,
  "status": "created",
  "message": "训练已创建，请上传视频或开始录制"
}
```

---

### 4.2 上传训练视频

**接口**: `POST /api/training/upload`

**请求参数 (Form Data):**
```
training_id: 1
file: <video_file>
```

**响应示例:**
```json
{
  "id": 1,
  "user_id": 1,
  "training_type": "extinguisher",
  "status": "completed",
  "total_score": 88.50,
  "step_scores": {
    "step1": 18.0,
    "step2": 20.0
  },
  "video_path": "./data/videos/1_training.mp4",
  "feedback": "整体流程正确，注意压把动作衔接",
  "created_at": "2026-03-11T10:00:00Z"
}
```

---

### 4.3 获取训练详情

**接口**: `GET /api/training/{training_id}`

**路径参数:**
- `training_id`: 训练记录 ID

**响应示例:**
```json
{
  "id": 1,
  "user_id": 1,
  "training_type": "extinguisher",
  "status": "completed",
  "total_score": 88.50,
  "step_scores": {"step1": 18.0, "step2": 20.0},
  "video_path": "./data/videos/1_training.mp4",
  "feedback": "整体流程正确",
  "action_count": 5,
  "actions": [
    {
      "action_name": "check_pressure",
      "step_index": 1,
      "is_correct": true,
      "confidence_score": 0.9625
    }
  ],
  "created_at": "2026-03-11T10:00:00Z"
}
```

---

### 4.4 获取训练历史

**接口**: `GET /api/training/history`

**查询参数:**
- `page`: 页码（默认 1）
- `page_size`: 每页数量（默认 10，最大 50）
- `status_filter`: 状态筛选（可选）
- `start_date`: 开始日期（可选，ISO 8601 格式）
- `end_date`: 结束日期（可选，ISO 8601 格式）

**请求示例:**
```
GET /api/training/history?page=1&page_size=10&status_filter=completed
```

**响应示例:**
```json
{
  "total": 25,
  "page": 1,
  "page_size": 10,
  "records": [
    {
      "id": 1,
      "user_id": 1,
      "training_type": "extinguisher",
      "status": "completed",
      "total_score": 88.50,
      "created_at": "2026-03-11T10:00:00Z"
    }
  ]
}
```

---

### 4.5 手动触发评分

**接口**: `POST /api/training/{training_id}/score`

**路径参数:**
- `training_id`: 训练记录 ID

**响应示例:**
```json
{
  "total_score": 88.50,
  "step_scores": [
    {
      "step_name": "提灭火器",
      "score": 18.5,
      "is_correct": true,
      "feedback": "动作标准"
    }
  ],
  "feedback": "整体表现良好",
  "suggestions": ["建议改进压把动作"]
}
```

---

## 5. 统计分析接口

### 5.1 获取个人统计

**接口**: `GET /api/stats/personal`

**认证**: ✅ 需要 Bearer Token

**响应示例:**
```json
{
  "user_id": 1,
  "total_trainings": 10,
  "completed_trainings": 8,
  "total_training_seconds": 3600.00,
  "average_score": 85.50,
  "best_score": 95.00,
  "last_training_at": "2026-03-11T10:00:00Z"
}
```

---

### 5.2 获取训练趋势

**接口**: `GET /api/stats/trend`

**查询参数:**
- `days`: 查询天数（默认 7，最多 30）

**响应示例:**
```json
{
  "trend_data": [
    {
      "date": "2026-03-11",
      "training_count": 3,
      "average_score": 85.5,
      "best_score": 90.0
    }
  ],
  "total_days": 7
}
```

---

### 5.3 获取步骤分析

**接口**: `GET /api/stats/step-analysis`

**响应示例:**
```json
{
  "step_analysis": [
    {
      "step_name": "提灭火器",
      "average_score": 18.5,
      "success_rate": 92.5,
      "improvement_suggestion": "保持手臂伸直"
    },
    {
      "step_name": "拔保险销",
      "average_score": 19.0,
      "success_rate": 95.0,
      "improvement_suggestion": null
    }
  ]
}
```

---

### 5.4 获取统计概览

**接口**: `GET /api/stats/overview`

**查询参数:**
- `days`: 趋势天数（默认 7）

**响应示例:**
```json
{
  "personal_stats": {
    "user_id": 1,
    "total_trainings": 10,
    "completed_trainings": 8,
    "average_score": 85.50,
    "best_score": 95.00
  },
  "recent_trend": {
    "trend_data": [...],
    "total_days": 7
  },
  "step_analysis": [...]
}
```

---

## 6. 错误码说明

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（Token 无效或过期） |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 业务错误码

| 错误码 | 说明 |
|--------|------|
| USER_EXISTS | 用户已存在 |
| INVALID_CREDENTIALS | 用户名或密码错误 |
| TRAINING_NOT_FOUND | 训练记录不存在 |
| VIDEO_UPLOAD_FAILED | 视频上传失败 |
| SCORING_FAILED | 评分失败 |

### 错误响应格式

```json
{
  "detail": "错误描述信息",
  "code": "ERROR_CODE"
}
```

---

## 7. 快速开始

### 7.1 使用 cURL 测试

**注册:**
```bash
curl -X POST http://localhost:8000/api/user/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "123456"
  }'
```

**登录:**
```bash
curl -X POST http://localhost:8000/api/user/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=123456"
```

**获取用户信息:**
```bash
curl -X GET http://localhost:8000/api/user/profile \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 7.2 使用 Python 测试

```python
import requests

BASE_URL = "http://localhost:8000"

# 注册
response = requests.post(f"{BASE_URL}/api/user/register", json={
    "username": "testuser",
    "email": "test@example.com",
    "password": "123456"
})
print("注册:", response.json())

# 登录
response = requests.post(f"{BASE_URL}/api/user/login", data={
    "username": "testuser",
    "password": "123456"
})
token = response.json()["token"]
print("登录成功，Token:", token[:50] + "...")

# 获取用户信息
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/api/user/profile", headers=headers)
print("用户信息:", response.json())
```

---

## 附录

### A. Schema 定义

所有请求和响应的 Schema 都在 `backend/app/schemas/` 目录下定义：

- `user.py`: 用户相关 Schema
- `training.py`: 训练相关 Schema
- `statistics.py`: 统计相关 Schema

### B. 路由文件

所有 API 路由都在 `backend/app/api/` 目录下：

- `users.py`: 用户管理路由
- `training.py`: 训练管理路由
- `statistics.py`: 统计分析路由

### C. 待实现功能

当前 API 使用了临时硬编码数据，以下功能需要在后续阶段实现：

1. **数据库集成**
   - 用户数据的持久化存储
   - 训练记录的 CRUD 操作
   
2. **JWT 认证**
   - Token 生成和验证
   - 密码 hash 和验证

3. **AI 评分集成**
   - YOLOv8 检测
   - MediaPipe 姿态分析
   - 规则引擎评分

4. **文件上传**
   - 视频文件保存
   - 文件路径管理

---

**文档版本**: v1.0  
**最后更新**: 2026-03-11  
**维护者**: FireTrain 开发团队
