"""管理员管理 API 测试"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.db.base import Base
from app.db.session import async_session_maker, engine
from app.models.user import User
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


def create_test_user(role="student", can_switch_role=False):
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
        }
    )
    assert response.status_code in (200, 201)

    async def _promote_role():
        async with async_session_maker() as session:
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalar_one()
            user.role = role
            user.can_switch_role = can_switch_role
            await session.commit()

    asyncio.run(_promote_role())

    login_response = client.post(
        "/api/user/login",
        data={"username": username, "password": "test123456"}
    )
    assert login_response.status_code == 200

    return login_response.json()["token"], username, email


def get_profile(token: str) -> dict:
    response = client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    return response.json()


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
    token, _, _ = create_test_user(role="student")

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


def test_create_root_forbidden():
    """系统内 Root 账号唯一，通过 API 创建新的 Root 用户应被拒绝"""
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

    assert response.status_code == 400
    assert "Root" in response.json()["detail"]


def test_update_role_to_root_forbidden():
    """不允许通过角色变更接口将任何账号提升为 Root"""
    root_token, _, _ = create_test_user(role="root")
    admin_token, _, _ = create_test_user(role="admin")
    admin_id = get_profile(admin_token)["id"]

    response = client.put(
        f"/api/admin/admins/{admin_id}/role",
        headers={"Authorization": f"Bearer {root_token}"},
        json={"role": "root"}
    )

    assert response.status_code == 400
    assert "Root" in response.json()["detail"]


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
    admin_id = get_profile(admin_token)["id"]

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
    user_id = get_profile(token)["id"]

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
    user_token, _, _ = create_test_user(role="student")

    # 获取 user 的 ID
    user_id = get_profile(user_token)["id"]

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
    user_id = get_profile(token)["id"]

    # 尝试修改自己的角色
    response = client.put(
        f"/api/admin/admins/{user_id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "student"}
    )

    assert response.status_code == 400
    assert "不能修改自己的角色" in response.json()["detail"]


def test_admin_can_list_student_users():
    """Admin 用户可以看到 student 角色的普通用户列表"""
    admin_token, _, _ = create_test_user(role="admin")
    student_token, username, _ = create_test_user(role="student")
    student_id = get_profile(student_token)["id"]

    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(user["id"] == student_id for user in data["users"])
    assert any(user["username"] == username for user in data["users"])


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


def test_admin_can_manage_normal_user_detail_and_stats():
    admin_token, _, _ = create_test_user(role="admin")
    user_token, username, email = create_test_user(role="student", can_switch_role=True)
    user_id = get_profile(user_token)["id"]

    detail_response = client.get(
        f"/api/admin/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["username"] == username
    assert detail["email"] == email
    assert detail["role"] == "student"

    stats_response = client.get(
        f"/api/admin/users/{user_id}/stats/overview",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["personal_stats"]["user_id"] == user_id
    assert stats["recent_trend"]["total_days"] == 7

    trainings_response = client.get(
        f"/api/admin/users/{user_id}/trainings",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert trainings_response.status_code == 200
    assert trainings_response.json()["records"] == []


def test_admin_cannot_manage_admin_via_user_endpoints():
    admin_token, _, _ = create_test_user(role="admin")
    root_token, _, _ = create_test_user(role="root")
    root_id = get_profile(root_token)["id"]

    response = client.get(
        f"/api/admin/users/{root_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 403
    assert "不能操作管理员或 Root 用户" in response.json()["detail"]


def test_root_can_update_admin_profile_and_reset_password():
    root_token, _, _ = create_test_user(role="root")
    admin_token, _, _ = create_test_user(role="admin")
    admin_profile = get_profile(admin_token)

    update_response = client.put(
        f"/api/admin/admins/{admin_profile['id']}",
        headers={"Authorization": f"Bearer {root_token}"},
        json={
            "username": f"{admin_profile['username']}_upd",
            "email": f"updated_{admin_profile['email']}",
            "phone": "13800138000",
            "is_active": True,
            "can_switch_role": True,
            "original_role": None,
            "password": "newpass123"
        }
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["username"].endswith("_upd")
    assert updated["phone"] == "13800138000"

    reset_response = client.put(
        f"/api/admin/admins/{admin_profile['id']}/reset-password",
        headers={"Authorization": f"Bearer {root_token}"}
    )

    assert reset_response.status_code == 200
    reset_data = reset_response.json()
    assert len(reset_data["temp_password"]) == 8
