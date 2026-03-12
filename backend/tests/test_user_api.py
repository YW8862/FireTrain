"""用户 API 接口测试"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.session import engine
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
import asyncio

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """测试前创建数据库表"""
    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    asyncio.run(_setup())
    yield
    # 测试后清理数据库
    asyncio.run(engine.dispose())


def test_user_register():
    """测试用户注册"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    response = client.post(
        "/api/user/register",
        json={
            "username": f"testuser_{unique_id}",
            "email": f"test{unique_id}@example.com",
            "password": "test123456",
            "phone": "13800138000"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "注册成功"
    assert "user_id" in data


def test_user_register_duplicate_username():
    """测试重复用户名"""
    # 先注册一个用户
    client.post(
        "/api/user/register",
        json={
            "username": "duplicate_user",
            "email": "dup1@example.com",
            "password": "test123456"
        }
    )
    
    # 尝试用相同用户名注册
    response = client.post(
        "/api/user/register",
        json={
            "username": "duplicate_user",
            "email": "dup2@example.com",
            "password": "test123456"
        }
    )
    assert response.status_code == 400
    assert "用户名已被注册" in response.json()["detail"]


def test_user_register_duplicate_email():
    """测试重复邮箱"""
    # 先注册一个用户
    client.post(
        "/api/user/register",
        json={
            "username": "user1",
            "email": "same@example.com",
            "password": "test123456"
        }
    )
    
    # 尝试用相同邮箱注册
    response = client.post(
        "/api/user/register",
        json={
            "username": "user2",
            "email": "same@example.com",
            "password": "test123456"
        }
    )
    assert response.status_code == 400
    assert "邮箱已被注册" in response.json()["detail"]


def test_user_login_success():
    """测试登录成功"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    # 先注册用户
    client.post(
        "/api/user/register",
        json={
            "username": f"logintest_{unique_id}",
            "email": f"login{unique_id}@example.com",
            "password": "test123456"
        }
    )
    
    # 测试登录
    response = client.post(
        "/api/user/login",
        data={
            "username": f"logintest_{unique_id}",
            "password": "test123456"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["token_type"] == "bearer"
    assert "user_info" in data
    assert data["user_info"]["username"] == f"logintest_{unique_id}"


def test_user_login_wrong_password():
    """测试密码错误"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    # 先注册用户
    client.post(
        "/api/user/register",
        json={
            "username": f"pwdtest_{unique_id}",
            "email": f"pwd{unique_id}@example.com",
            "password": "test123456"
        }
    )
    
    # 测试错误密码
    response = client.post(
        "/api/user/login",
        data={
            "username": f"pwdtest_{unique_id}",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "用户名或密码错误" in response.json()["detail"]


def test_get_profile_with_valid_token():
    """测试使用有效 token 获取用户信息"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    # 注册并登录
    client.post(
        "/api/user/register",
        json={
            "username": f"profiletest_{unique_id}",
            "email": f"profile{unique_id}@example.com",
            "password": "test123456"
        }
    )
    
    login_response = client.post(
        "/api/user/login",
        data={
            "username": f"profiletest_{unique_id}",
            "password": "test123456"
        }
    )
    token = login_response.json()["token"]
    
    # 使用 token 获取用户信息
    response = client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == f"profiletest_{unique_id}"
    assert data["email"] == f"profile{unique_id}@example.com"


def test_get_profile_with_invalid_token():
    """测试使用无效 token 获取用户信息"""
    response = client.get(
        "/api/user/profile",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


def test_update_profile():
    """测试更新用户信息"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    # 注册并登录
    client.post(
        "/api/user/register",
        json={
            "username": f"updatetest_{unique_id}",
            "email": f"update{unique_id}@example.com",
            "password": "test123456"
        }
    )
    
    login_response = client.post(
        "/api/user/login",
        data={
            "username": f"updatetest_{unique_id}",
            "password": "test123456"
        }
    )
    token = login_response.json()["token"]
    
    # 更新用户信息
    response = client.put(
        "/api/user/profile",
        json={
            "phone": "13900139000"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "13900139000"


def test_logout():
    """测试退出登录"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    # 注册并登录
    client.post(
        "/api/user/register",
        json={
            "username": f"logouttest_{unique_id}",
            "email": f"logout{unique_id}@example.com",
            "password": "test123456"
        }
    )
    
    login_response = client.post(
        "/api/user/login",
        data={
            "username": f"logouttest_{unique_id}",
            "password": "test123456"
        }
    )
    token = login_response.json()["token"]
    
    # 退出登录
    response = client.post(
        "/api/user/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "退出登录成功"
    
    # 验证 token 已失效
    response = client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
