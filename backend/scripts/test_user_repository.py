#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UserRepository 查询功能测试脚本

测试任务 1.2 的所有功能
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


async def test_user_repository():
    """测试 UserRepository 的查询功能"""
    
    print("\n" + "="*60)
    print("  UserRepository 查询功能测试")
    print("="*60)
    
    results = []
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        
        # ========== 测试 1: 按角色过滤查询 ==========
        print("\n📋 测试 1: 按角色过滤查询")
        try:
            # 查询所有普通用户
            users, total = await user_repo.query_with_filters(
                page=1,
                page_size=10,
                role_filter="user"
            )
            
            print(f"✅ 查询成功")
            print(f"   - 总记录数: {total}")
            print(f"   - 返回用户数: {len(users)}")
            
            if users:
                print(f"   - 第一个用户:")
                print(f"     * ID: {users[0]['id']}")
                print(f"     * 用户名: {users[0]['username']}")
                print(f"     * 角色: {users[0]['role']}")
            
            # 验证不包含密码
            has_password = any('password' in user for user in users)
            if not has_password:
                print(f"✅ 返回数据不包含密码字段")
                results.append(("按角色过滤", True))
            else:
                print(f"❌ 返回数据包含密码字段")
                results.append(("按角色过滤", False))
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results.append(("按角色过滤", False))
        
        # ========== 测试 2: 按关键词搜索 ==========
        print("\n📋 测试 2: 按关键词搜索")
        try:
            # 使用 "admin" 作为关键词搜索
            users, total = await user_repo.query_with_filters(
                page=1,
                page_size=10,
                keyword="admin"
            )
            
            print(f"✅ 搜索成功")
            print(f"   - 关键词: 'admin'")
            print(f"   - 找到记录数: {total}")
            print(f"   - 返回用户数: {len(users)}")
            
            if users:
                print(f"   - 匹配的用户:")
                for user in users[:3]:  # 只显示前3个
                    print(f"     * {user['username']} ({user['email']})")
            
            results.append(("按关键词搜索", True))
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results.append(("按关键词搜索", False))
        
        # ========== 测试 3: 分页功能 ==========
        print("\n📋 测试 3: 分页功能")
        try:
            # 第一页
            page1_users, page1_total = await user_repo.query_with_filters(
                page=1,
                page_size=5
            )
            
            # 第二页
            page2_users, page2_total = await user_repo.query_with_filters(
                page=2,
                page_size=5
            )
            
            print(f"✅ 分页查询成功")
            print(f"   - 总记录数: {page1_total}")
            print(f"   - 第一页用户数: {len(page1_users)}")
            print(f"   - 第二页用户数: {len(page2_users)}")
            
            # 验证两页数据不重复
            page1_ids = {u['id'] for u in page1_users}
            page2_ids = {u['id'] for u in page2_users}
            
            if not page1_ids.intersection(page2_ids):
                print(f"✅ 分页数据无重复")
                results.append(("分页功能", True))
            else:
                print(f"❌ 分页数据有重复")
                results.append(("分页功能", False))
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results.append(("分页功能", False))
        
        # ========== 测试 4: 组合过滤（角色+关键词） ==========
        print("\n📋 测试 4: 组合过滤（角色+关键词）")
        try:
            users, total = await user_repo.query_with_filters(
                page=1,
                page_size=10,
                role_filter="user",
                keyword="test"
            )
            
            print(f"✅ 组合过滤成功")
            print(f"   - 角色过滤: 'user'")
            print(f"   - 关键词: 'test'")
            print(f"   - 找到记录数: {total}")
            print(f"   - 返回用户数: {len(users)}")
            
            # 验证所有返回用户的角色都是 'user'
            all_correct_role = all(u['role'] == 'user' for u in users)
            if all_correct_role:
                print(f"✅ 角色过滤正确")
                results.append(("组合过滤", True))
            else:
                print(f"❌ 角色过滤有误")
                results.append(("组合过滤", False))
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results.append(("组合过滤", False))
        
        # ========== 测试 5: 删除用户功能 ==========
        print("\n📋 测试 5: 删除用户功能")
        try:
            # 创建一个测试用户
            test_user = User(
                username="test_delete_user",
                email="test_delete@example.com",
                password_hash=get_password_hash("test123"),
                role="user",
                is_active=True
            )
            session.add(test_user)
            await session.flush()
            
            print(f"✅ 创建测试用户 (ID: {test_user.id})")
            
            # 删除该用户
            await user_repo.delete(test_user)
            print(f"✅ 删除用户成功")
            
            # 验证用户已被删除
            deleted_user = await user_repo.get_by_id(test_user.id)
            if deleted_user is None:
                print(f"✅ 用户已从数据库中移除")
                results.append(("删除用户", True))
            else:
                print(f"❌ 用户仍然存在")
                results.append(("删除用户", False))
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            await session.rollback()
            results.append(("删除用户", False))
        
        # ========== 测试 6: 返回数据格式验证 ==========
        print("\n📋 测试 6: 返回数据格式验证")
        try:
            users, total = await user_repo.query_with_filters(
                page=1,
                page_size=1
            )
            
            if users:
                user = users[0]
                required_fields = [
                    'id', 'username', 'email', 'phone', 
                    'role', 'is_active', 'last_login_at', 
                    'created_at', 'can_switch_role'
                ]
                
                missing_fields = [f for f in required_fields if f not in user]
                
                if not missing_fields:
                    print(f"✅ 返回数据包含所有必需字段")
                    print(f"   - 字段列表: {', '.join(required_fields)}")
                    results.append(("数据格式", True))
                else:
                    print(f"❌ 缺少字段: {missing_fields}")
                    results.append(("数据格式", False))
                    
                # 验证不包含敏感字段
                sensitive_fields = ['password', 'password_hash']
                has_sensitive = any(f in user for f in sensitive_fields)
                
                if not has_sensitive:
                    print(f"✅ 不包含敏感字段")
                else:
                    print(f"❌ 包含敏感字段")
                    results[-1] = ("数据格式", False)
            else:
                print(f"⚠️  没有用户数据可验证")
                results.append(("数据格式", True))
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results.append(("数据格式", False))
    
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
        print("\n🎉 所有测试通过！任务 1.2 完成！")
        return True
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_user_repository())
    sys.exit(0 if success else 1)
