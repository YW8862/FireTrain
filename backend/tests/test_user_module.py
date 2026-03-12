"""用户模块测试脚本"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService, get_password_hash, verify_password
from app.schemas.user import UserRegisterRequest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def test_user_module():
    """测试用户模块的所有功能"""
    print("=" * 60)
    print("🧪 开始测试用户模块")
    print("=" * 60)
    
    # 创建数据库表
    print("\n1️⃣ 创建数据库表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表创建成功")
    
    # 创建会话工厂
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # 测试密码 hash
    print("\n2️⃣ 测试密码 hash...")
    password = "test123456"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed), "密码验证失败"
    print(f"✅ 密码 hash 测试通过")
    print(f"   原始密码：{password}")
    print(f"   Hash 后：{hashed[:20]}...")
    
    # 测试用户注册
    print("\n3️⃣ 测试用户注册...")
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user_service = UserService(user_repo)
        
        user_data = UserRegisterRequest(
            username="testuser",
            email="test@example.com",
            password="test123456",
            phone="13800138000"
        )
        
        try:
            user = await user_service.register(user_data)
            print(f"✅ 用户注册成功")
            print(f"   用户 ID: {user.id}")
            print(f"   用户名：{user.username}")
            print(f"   邮箱：{user.email}")
            await session.commit()  # 提交事务
        except ValueError as e:
            print(f"⚠️  用户已存在：{e}")
            # 获取已存在的用户
            user = await user_repo.get_by_username("testuser")
    
    # 测试用户登录
    print("\n4️⃣ 测试用户登录...")
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user_service = UserService(user_repo)
        
        try:
            token, user = await user_service.login("testuser", "test123456")
            print(f"✅ 登录成功")
            print(f"   Token: {token[:50]}...")
            print(f"   用户：{user.username}")
        except ValueError as e:
            print(f"❌ 登录失败：{e}")
    
    # 测试获取用户信息
    print("\n5️⃣ 测试获取用户信息...")
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_username("testuser")
        if user:
            print(f"✅ 获取用户成功")
            print(f"   ID: {user.id}")
            print(f"   用户名：{user.username}")
            print(f"   邮箱：{user.email}")
            print(f"   角色：{user.role}")
        else:
            print(f"❌ 用户不存在")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
    print("\n💡 提示：现在可以启动后端服务测试 API 接口")
    print("   命令：cd backend && ./start.sh")
    print("   API 文档：http://localhost:8000/docs\n")


if __name__ == "__main__":
    asyncio.run(test_user_module())
