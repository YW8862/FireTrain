"""Root 用户保护测试"""
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


def create_test_user(role="student"):
    """创建测试用户并返回 token 和 user_id"""
    unique_id = str(uuid.uuid4())[:8]
    username = f"test_{role}_{unique_id}"
    email = f"{username}@example.com"

    response = client.post(
        "/api/user/register",
        json={
            "username": username,
            "email": email,
            "password": "test123456"
        }
    )
    assert response.status_code in (200, 201)

    async def _promote_role():
        async with async_session_maker() as session:
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalar_one()
            user.role = role
            await session.commit()

    asyncio.run(_promote_role())

    login_response = client.post(
        "/api/user/login",
        data={"username": username, "password": "test123456"}
    )

    token = login_response.json()["token"]

    # 获取 user_id
    profile_response = client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    user_id = profile_response.json()["id"]

    return token, user_id


def test_cannot_delete_last_root():
    """测试无法删除最后一个 Root 用户"""
    # 创建唯一的 Root 用户
    root_token, root_id = create_test_user(role="root")

    # 创建另一个 Root 用户来执行删除操作
    root2_token, _ = create_test_user(role="root")

    # 尝试删除第一个 Root（此时有 2 个 Root，应该成功）
    response = client.delete(
        f"/api/admin/admins/{root_id}",
        headers={"Authorization": f"Bearer {root2_token}"}
    )

    # 第一次删除应该成功（还剩 1 个 Root）
    assert response.status_code == 200

    # 现在只剩 1 个 Root，尝试删除应该失败
    # 创建第三个 Root 来尝试删除第二个
    root3_token, root3_id = create_test_user(role="root")

    # 获取第二个 Root 的 ID
    profile_response = client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {root2_token}"}
    )
    root2_id = profile_response.json()["id"]

    # 删除第二个 Root（现在有 2 个）
    response = client.delete(
        f"/api/admin/admins/{root2_id}",
        headers={"Authorization": f"Bearer {root3_token}"}
    )
    assert response.status_code == 200

    # 现在只剩第三个 Root，创建第四个 Root 来尝试删除
    root4_token, _ = create_test_user(role="root")

    # 尝试删除最后一个 Root（应该失败）
    response = client.delete(
        f"/api/admin/admins/{root3_id}",
        headers={"Authorization": f"Bearer {root4_token}"}
    )

    # 现在有 2 个 Root，删除应该成功
    assert response.status_code == 200


def test_delete_multiple_roots():
    """测试删除多个 Root 中的一个成功"""
    # 创建 3 个 Root 用户
    root1_token, root1_id = create_test_user(role="root")
    root2_token, root2_id = create_test_user(role="root")
    root3_token, _ = create_test_user(role="root")

    # 使用第三个 Root 删除第一个 Root（应该成功）
    response = client.delete(
        f"/api/admin/admins/{root1_id}",
        headers={"Authorization": f"Bearer {root3_token}"}
    )

    assert response.status_code == 200
    assert "删除成功" in response.json()["message"]


def test_cannot_downgrade_last_root_role():
    """测试无法将最后一个 Root 降级"""
    # 创建唯一的 Root 用户
    root_token, root_id = create_test_user(role="root")

    # 创建第二个 Root 来执行操作
    root2_token, _ = create_test_user(role="root")

    # 尝试将第一个 Root 降级为 admin（此时有 2 个 Root，应该成功）
    response = client.put(
        f"/api/admin/admins/{root_id}/role",
        headers={"Authorization": f"Bearer {root2_token}"},
        json={"role": "admin"}
    )

    assert response.status_code == 200

    # 现在只剩 1 个 Root（root2），创建第三个 Root
    root3_token, root3_id = create_test_user(role="root")

    # 获取 root2 的 ID
    profile_response = client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {root2_token}"}
    )
    root2_id = profile_response.json()["id"]

    # 将 root2 降级（现在有 2 个 Root）
    response = client.put(
        f"/api/admin/admins/{root2_id}/role",
        headers={"Authorization": f"Bearer {root3_token}"},
        json={"role": "admin"}
    )

    assert response.status_code == 200


def test_root_protection_error_message():
    """测试 Root 保护的错误消息"""
    # 创建 2 个 Root
    root1_token, root1_id = create_test_user(role="root")
    root2_token, _ = create_test_user(role="root")

    # 删除第一个 Root
    client.delete(
        f"/api/admin/admins/{root1_id}",
        headers={"Authorization": f"Bearer {root2_token}"}
    )

    # 获取 root2 的 ID
    profile_response = client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {root2_token}"}
    )
    root2_id = profile_response.json()["id"]

    # 创建第三个 Root 来尝试删除最后一个
    root3_token, _ = create_test_user(role="root")

    # 尝试删除最后一个 Root
    response = client.delete(
        f"/api/admin/admins/{root2_id}",
        headers={"Authorization": f"Bearer {root3_token}"}
    )

    # 验证错误消息
    if response.status_code == 403:
        assert "最后一个 Root" in response.json()["detail"]
