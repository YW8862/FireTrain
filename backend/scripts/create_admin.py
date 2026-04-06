#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建管理员账户脚本

用于快速创建管理员或 Root 用户
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import async_session_maker
from app.repositories.user_repository import UserRepository
from app.services.user_service import get_password_hash
from app.models.user import User


async def create_admin_user(
    username: str,
    email: str,
    password: str,
    role: str = "admin",
    phone: str = None
):
    """
    创建管理员用户
    
    Args:
        username: 用户名
        email: 邮箱
        password: 密码
        role: 角色 (admin 或 root)
        phone: 手机号（可选）
    """
    
    print("\n" + "="*60)
    print(f"  创建{ 'Root' if role == 'root' else '管理员' }账户")
    print("="*60)
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        
        # 检查用户名是否已存在
        existing = await user_repo.get_by_username(username)
        if existing:
            print(f"❌ 用户名 '{username}' 已存在")
            return False
        
        # 检查邮箱是否已存在
        existing_email = await user_repo.get_by_email(email)
        if existing_email:
            print(f"❌ 邮箱 '{email}' 已被注册")
            return False
        
        # 创建管理员用户
        admin_user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            phone=phone,
            role=role,
            is_active=True,
            can_switch_role=True if role == "admin" else False  # 仅管理员可切换
        )
        
        session.add(admin_user)
        await session.commit()
        
        print(f"\n✅ { 'Root' if role == 'root' else '管理员' }账户创建成功！\n")
        print("="*60)
        print("  账户信息")
        print("="*60)
        print(f"  用户名: {username}")
        print(f"  密码:   {password}")
        print(f"  邮箱:   {email}")
        print(f"  角色:   {role}")
        if phone:
            print(f"  手机:   {phone}")
        print(f"  ID:     {admin_user.id}")
        print("="*60)
        print("\n⚠️  请妥善保管此密码，建议首次登录后修改\n")
        
        return True


async def main():
    """主函数"""
    
    print("\n请选择要创建的账户类型:")
    print("1. 管理员 (admin) - 可管理普通用户数据，可切换身份")
    print("2. Root 用户 (root) - 最高权限，可管理所有用户和管理员")
    print()
    
    choice = input("请输入选择 (1/2，默认为 1): ").strip() or "1"
    
    if choice not in ["1", "2"]:
        print("❌ 无效选择")
        return False
    
    role = "admin" if choice == "1" else "root"
    
    # 获取用户输入
    print(f"\n请输入{ 'Root' if role == 'root' else '管理员' }账户信息:\n")
    
    username = input("用户名: ").strip()
    if not username:
        print("❌ 用户名不能为空")
        return False
    
    email = input("邮箱: ").strip()
    if not email or "@" not in email:
        print("❌ 邮箱格式不正确")
        return False
    
    password = input("密码 (至少6位): ").strip()
    if len(password) < 6:
        print("❌ 密码长度至少为 6 位")
        return False
    
    phone = input("手机号 (可选，直接回车跳过): ").strip() or None
    
    # 确认创建
    print(f"\n确认创建{ 'Root' if role == 'root' else '管理员' }账户？")
    print(f"  用户名: {username}")
    print(f"  邮箱:   {email}")
    print(f"  角色:   {role}")
    confirm = input("\n确认创建？(y/n): ").strip().lower()
    
    if confirm != "y":
        print("❌ 已取消创建")
        return False
    
    # 创建账户
    success = await create_admin_user(username, email, password, role, phone)
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ 操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
