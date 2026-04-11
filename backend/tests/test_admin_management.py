"""管理员管理 API 测试"""
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

    response = client.post(
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

    return login_response.json()["token"], username, email


def test_get_admins_as_root():
    """Root 用户可以获取管理员列表"""
    token, _, _ = create_test_user(role="root")

    response = client.get(
        "/api/admin/admins",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "admins" in data
    assert "total" in data
    assert isinstance(data["admins"], list)


def test_get_admins_as_admin_forbidden():
    """Admin 用户访问管理员列表被拒绝"""
    token, _, _ = create_test_user(role="admin")

    response = client.get(
        "/api/admin/admins",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


def test_get_admins_as_user_forbidden():
    """普通用户访问管理员列表被拒绝"""
    token, _, _ = create_test_user(role="user")

    response = client.get(
        "/api/admin/admins",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


def test_create_admin_as_root():
    """Root 用户可以创建管理员"""
    token, _, _ = create_test_user(role="root")

    unique_id = str(uuid.uuid4())[:8]
    response = client.post(
        "/api/admin/admins",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": f"newadmin_{unique_id}",
            "email": f"newadmin_{unique_id}@example.com",
            "password": "admin123456",
            "role": "admin",
            "can_switch_role": True
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == f"newadmin_{unique_id}"
    assert data["role"] == "admin"
    assert data["can_switch_role"] is True


def test_create_root_as_root():
    """Root 用户可以创建新的 Root 用户"""
    token, _, _ = create_test_user(role="root")

    unique_id = str(uuid.uuid4())[:8]
    response = client.post(
        "/api/admin/admins",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": f"newroot_{unique_id}",
            "email": f"newroot_{unique_id}@example.com",
            "password": "root123456",
            "role": "root",
            "can_switch_role": True
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "root"


def test_create_admin_as_admin_forbidden():
    """Admin 用户创建管理员被拒绝"""
    token, _, _ = create_test_user(role="admin")

    unique_id = str(uuid.uuid4())[:8]
    response = client.post(
        "/api/admin/admins",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": f"newadmin_{unique_id}",
            "email": f"newadmin_{unique_id}@example.com",
            "password": "admin123456",
            "role": "admin",
            "can_switch_role": True
        }
    )

    assert response.status_code == 403


def test_create_admin_duplicate_username():
    """创建管理员时用户名重复"""
    token, username, _ = create_test_user(role="root")

    response = client.post(
        "/api/admin/admins",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": username,
            "email": "different@example.com",
            "password": "admin123456",
            "role": "admin",
            "can_switch_role": True
        }
    )

    assert response.status_code == 400
    assert "用户名已存在" in response.json()["detail"]


def test_delete_admin_as_root():
    """Root 用户可以删除管理员"""
    root_token, _, _ = create_test_user(role="root")
    admin_token, _, _ = create_test_user(role="admin")

    # 获取 admin 的 ID
    profile_response = client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    admin_id = profile_response.json()["id"]

    # 删除 admin
    response = client.delete(
        f"/api/admin/admins/{admin_id}",
        headers={"Authorization": f"Bearer {root_token}"}
    )

    assert response.status_code == 200
    assert "删除成功" in response.json()["message"]


def test_delete_self_forbidden():
    """禁止删除自己"""
    token, _, _ = create_test_user(role="root")

    # 获取自己的 ID
    profile_response = client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    user_id = profile_response.json()["id"]

    # 尝试删除自己
    response = client.delete(
        f"/api/admin/admins/{user_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert "不能删除自己" in response.json()["detail"]


def test_update_admin_role():
    """Root 用户可以修改管理员角色"""
    root_token, _, _ = create_test_user(role="root")
    user_token, _, _ = create_test_user(role="user")

    # 获取 user 的 ID
    profile_response = client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    user_id = profile_response.json()["id"]

    # 将 user 提升为 admin
    response = client.put(
        f"/api/admin/admins/{user_id}/role",
        headers={"Authorization": f"Bearer {root_token}"},
        json={"role": "admin"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "admin"


def test_update_self_role_forbidden():
    """禁止修改自己的角色"""
    token, _, _ = create_test_user(role="root")

    # 获取自己的 ID
    profile_response = client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    user_id = profile_response.json()["id"]

    # 尝试修改自己的角色
    response = client.put(
        f"/api/admin/admins/{user_id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "user"}
    )

    assert response.status_code == 400
    assert "不能修改自己的角色" in response.json()["detail"]


def test_search_admins_by_keyword():
    """测试按关键词搜索管理员"""
    token, username, _ = create_test_user(role="root")

    response = client.get(
        f"/api/admin/admins?keyword={username[:10]}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["admins"]) > 0
    assert any(username in admin["username"] for admin in data["admins"])
