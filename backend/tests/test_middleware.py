"""中间件和通用能力测试"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """测试根路径欢迎信息"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "FireTrain" in data["message"]
    assert data["version"] == "0.1.0"
    assert data["docs"] == "/docs"


def test_health_check():
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_request_logging_middleware():
    """测试请求日志中间件（通过响应头验证）"""
    response = client.get("/health")
    
    # 验证响应头中包含 trace_id
    assert "X-Trace-ID" in response.headers
    trace_id = response.headers["X-Trace-ID"]
    assert len(trace_id) > 0  # trace_id 不应该为空
    
    # 验证 UUID 格式
    import uuid
    try:
        uuid.UUID(trace_id)
    except ValueError:
        pytest.fail(f"trace_id 不是有效的 UUID 格式：{trace_id}")


def test_cors_headers():
    """测试 CORS 配置"""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        }
    )
    
    # 验证 CORS 响应头
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_validation_error_handling():
    """测试参数验证错误处理"""
    # 发送无效的注册数据
    response = client.post(
        "/api/user/register",
        json={
            "username": "ab",  # 太短，最少 3 个字符
            "email": "invalid-email",  # 无效的邮箱格式
            "password": "123"  # 太短，最少 6 个字符
        }
    )
    
    # 应该返回 422 错误
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_user_registration_success():
    """测试用户注册成功流程"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    response = client.post(
        "/api/user/register",
        json={
            "username": f"testuser_{unique_id}",
            "email": f"test{unique_id}@example.com",
            "password": "test123456",
            "phone": None
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "注册成功"
    assert "user_id" in data


def test_user_login_and_jwt_auth():
    """测试用户登录和 JWT 认证"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    # 1. 注册用户
    client.post(
        "/api/user/register",
        json={
            "username": f"logintest_{unique_id}",
            "email": f"login{unique_id}@example.com",
            "password": "test123456"
        }
    )
    
    # 2. 登录获取 token
    login_response = client.post(
        "/api/user/login",
        data={
            "username": f"logintest_{unique_id}",
            "password": "test123456"
        }
    )
    
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "token" in login_data
    token = login_data["token"]
    assert len(token) > 0
    
    # 3. 使用 token 访问需要认证的接口
    profile_response = client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["username"] == f"logintest_{unique_id}"


def test_invalid_token():
    """测试无效 token"""
    response = client.get(
        "/api/user/profile",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    # 应该返回 401 未授权
    assert response.status_code == 401


def test_training_workflow_with_auth():
    """测试带认证的完整训练流程"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    # 1. 注册并登录
    client.post(
        "/api/user/register",
        json={
            "username": f"trainingtest_{unique_id}",
            "email": f"training{unique_id}@example.com",
            "password": "test123456"
        }
    )
    
    login_response = client.post(
        "/api/user/login",
        data={
            "username": f"trainingtest_{unique_id}",
            "password": "test123456"
        }
    )
    
    token = login_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. 开始训练
    start_response = client.post(
        "/api/training/start",
        json={"training_type": "extinguisher"},
        headers=headers
    )
    assert start_response.status_code == 200
    training_id = start_response.json()["training_id"]
    
    # 3. 完成训练
    complete_response = client.post(
        f"/api/training/complete/{training_id}",
        headers=headers
    )
    assert complete_response.status_code == 200
    
    # 4. 查询详情
    detail_response = client.get(
        f"/api/training/{training_id}",
        headers=headers
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["status"] == "done"
    
    # 5. 查询历史
    history_response = client.get(
        "/api/training/history",
        headers=headers
    )
    assert history_response.status_code == 200
    assert history_response.json()["total"] >= 1


def test_unauthorized_access():
    """测试未授权访问"""
    # 尝试在没有 token 的情况下访问需要认证的接口
    response = client.get("/api/user/profile")
    
    # 应该返回 401 或 422（取决于 OAuth2 scheme 的实现）
    assert response.status_code in [401, 422]
