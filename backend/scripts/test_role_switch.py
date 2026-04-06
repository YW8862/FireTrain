#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色切换功能测试脚本

测试管理员和普通用户之间的角色切换
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import async_session_maker
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService, get_password_hash
from app.models.user import User


async def test_role_switch():
    """测试角色切换功能"""
    
    print("\n" + "="*60)
    print("  角色切换功能测试")
    print("="*60)
    
    results = []
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user_service = UserService(user_repo)
        
        # ========== 测试 1: 创建测试管理员 ==========
        print("\n📋 测试 1: 创建测试管理员账户")
        try:
            # 检查是否已存在
            existing = await user_repo.get_by_username("test_admin_switch")
            
            if not existing:
                test_admin = User(
                    username="test_admin_switch",
                    email="test_admin@example.com",
                    password_hash=get_password_hash("admin123"),
                    role="admin",
                    is_active=True,
                    can_switch_role=True  # 允许角色切换
                )
                session.add(test_admin)
                await session.flush()
                admin_id = test_admin.id
                print(f"✅ 创建测试管理员 (ID: {admin_id})")
            else:
                admin_id = existing.id
                print(f"✅ 使用现有管理员 (ID: {admin_id})")
            
            results.append(("创建测试管理员", True))
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            await session.rollback()
            results.append(("创建测试管理员", False))
            return False
        
        # ========== 测试 2: 管理员切换到用户模式 ==========
        print("\n📋 测试 2: 管理员切换到用户模式")
        try:
            result = await user_service.switch_role(admin_id, "user")
            
            print(f"✅ 切换成功")
            print(f"   - 当前角色: {result['role']}")
            print(f"   - 原始角色: {result['original_role']}")
            
            if result['role'] == 'user' and result['original_role'] == 'admin':
                print(f"✅ 角色切换正确")
                results.append(("切换到用户模式", True))
            else:
                print(f"❌ 角色切换异常")
                results.append(("切换到用户模式", False))
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results.append(("切换到用户模式", False))
        
        # ========== 测试 3: 验证数据库中的角色已更新 ==========
        print("\n📋 测试 3: 验证数据库中的角色")
        try:
            updated_user = await user_repo.get_by_id(admin_id)
            
            print(f"   - 用户名: {updated_user.username}")
            print(f"   - 当前角色: {updated_user.role}")
            print(f"   - 原始角色: {updated_user.original_role}")
            print(f"   - 可切换: {updated_user.can_switch_role}")
            
            if updated_user.role == 'user' and updated_user.original_role == 'admin':
                print(f"✅ 数据库记录正确")
                results.append(("数据库验证", True))
            else:
                print(f"❌ 数据库记录异常")
                results.append(("数据库验证", False))
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results.append(("数据库验证", False))
        
        # ========== 测试 4: 从用户模式切换回管理员 ==========
        print("\n📋 测试 4: 切换回管理员模式")
        try:
            result = await user_service.switch_role(admin_id, "admin")
            
            print(f"✅ 切换成功")
            print(f"   - 当前角色: {result['role']}")
            print(f"   - 原始角色: {result['original_role']}")
            
            if result['role'] == 'admin' and result['original_role'] is None:
                print(f"✅ 恢复管理员角色正确")
                results.append(("恢复管理员", True))
            else:
                print(f"❌ 恢复管理员角色异常")
                results.append(("恢复管理员", False))
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results.append(("恢复管理员", False))
        
        # ========== 测试 5: 普通用户尝试切换（应该失败） ==========
        print("\n📋 测试 5: 普通用户尝试切换（应失败）")
        try:
            # 创建一个普通用户
            test_user = User(
                username="test_user_no_switch",
                email="test_user@example.com",
                password_hash=get_password_hash("user123"),
                role="user",
                is_active=True,
                can_switch_role=False  # 不允许切换
            )
            session.add(test_user)
            await session.flush()
            user_id = test_user.id
            
            # 尝试切换
            try:
                await user_service.switch_role(user_id, "admin")
                print(f"❌ 普通用户不应该能切换角色")
                results.append(("权限控制", False))
            except ValueError as e:
                print(f"✅ 正确拒绝切换: {e}")
                results.append(("权限控制", True))
            
            # 清理测试用户
            await user_repo.delete(test_user)
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            await session.rollback()
            results.append(("权限控制", False))
        
        # ========== 测试 6: 多次切换测试 ==========
        print("\n📋 测试 6: 多次切换稳定性测试")
        try:
            # 切换 3 次
            for i in range(3):
                # 切换到用户
                result1 = await user_service.switch_role(admin_id, "user")
                # 切换回管理员
                result2 = await user_service.switch_role(admin_id, "admin")
                
                if result1['role'] != 'user' or result2['role'] != 'admin':
                    print(f"❌ 第 {i+1} 次切换失败")
                    results.append(("多次切换", False))
                    break
            else:
                print(f"✅ 3 次切换全部成功")
                results.append(("多次切换", True))
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results.append(("多次切换", False))
        
        # ========== 清理测试数据 ==========
        print("\n🧹 清理测试数据")
        try:
            test_admin = await user_repo.get_by_id(admin_id)
            if test_admin:
                await user_repo.delete(test_admin)
                print(f"✅ 删除测试管理员")
        except Exception as e:
            print(f"⚠️  清理失败: {e}")
    
    # ========== 测试结果总结 ==========
    print("\n" + "="*60)
    print("  测试结果总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print("\n" + "="*60)
    print(f"总计: {passed}/{total} 测试通过")
    print("="*60)
    
    if passed == total:
        print("\n🎉 所有测试通过！角色切换功能正常！")
        return True
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_role_switch())
    sys.exit(0 if success else 1)
