"""角色切换功能测试"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.session import engine
import asyncio
import uuid

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """测试前创建数据库表"""
    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_setup())
    yield
    asyncio.run(engine.dispose())


def create_test_user(role="user", can_switch_role=False):
    """创建测试用户并返回 token"""
    unique_id = str(uuid.uuid4())[:8]
    username = f"test_{role}_{unique_id}"
    email = f"{username}@example.com"

    client.post(
        "/api/user/register",
        json={
            "username": username,
            "email": email,
            "password": "test123456",
            "role": role,
            "can_switch_role": can_switch_role
        }
    )

    login_response = client.post(
        "/api/user/login",
        data={"username": username, "password": "test123456"}
    )

    return login_response.json()["token"]


def test_admin_switch_to_user():
    """Admin 切换到 User 成功"""
    token = create_test_user(role="admin", can_switch_role=True)

    response = client.post(
        "/api/users/switch-role",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_role": "user"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["original_role"] == "admin"

    # 验证新 token 的角色
    new_token = data["token"]
    profile_response = client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {new_token}"}
    )

    assert profile_response.status_code == 200
    assert profile_response.json()["role"] == "user"


def test_user_switch_back_to_admin():
    """User 切回 Admin 成功"""
    # 先创建 admin 并切换到 user
    admin_token = create_test_user(role="admin", can_switch_role=True)

    switch_response = client.post(
        "/api/users/switch-role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"target_role": "user"}
    )

    user_token = switch_response.json()["token"]
    original_role = switch_response.json()["original_role"]

    # 切回 admin
    response = client.post(
        "/api/users/switch-role",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"target_role": original_role}
    )

    assert response.status_code == 200
    data = response.json()
    assert "token" in data

    # 验证角色已恢复
    new_token = data["token"]
    profile_response = client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {new_token}"}
    )

    assert profile_response.status_code == 200
    assert profile_response.json()["role"] == "admin"


def test_root_switch_to_user():
    """Root 切换到 User 成功"""
    token = create_test_user(role="root", can_switch_role=True)

    response = client.post(
        "/api/users/switch-role",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_role": "user"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["original_role"] == "root"


def test_cannot_switch_without_permission():
    """can_switch_role=False 的用户无法切换"""
    token = create_test_user(role="admin", can_switch_role=False)

    response = client.post(
        "/api/users/switch-role",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_role": "user"}
    )

    assert response.status_code == 403
    assert "没有权限切换角色" in response.json()["detail"]


def test_cannot_switch_to_invalid_role():
    """无法切换到非法角色"""
    token = create_test_user(role="admin", can_switch_role=True)

    response = client.post(
        "/api/users/switch-role",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_role": "superadmin"}
    )

    assert response.status_code == 400


def test_user_cannot_switch_to_admin_without_original_role():
    """普通用户无法直接切换到 admin"""
    token = create_test_user(role="user", can_switch_role=True)

    response = client.post(
        "/api/users/switch-role",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_role": "admin"}
    )

    assert response.status_code == 403


def test_switch_role_token_refresh():
    """测试角色切换后 token 正确刷新"""
    token = create_test_user(role="admin", can_switch_role=True)

    # 切换到 user
    response = client.post(
        "/api/users/switch-role",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_role": "user"}
    )

    new_token = response.json()["token"]

    # 验证旧 token 仍然有效（取决于实现）
    # 验证新 token 有效
    profile_response = client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {new_token}"}
    )

    assert profile_response.status_code == 200
    assert profile_response.json()["role"] == "user"
