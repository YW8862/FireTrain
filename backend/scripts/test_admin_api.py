#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台管理 API 测试脚本

测试任务 1.1 的所有接口功能
"""
import requests
import json
from urllib3.exceptions import InsecureRequestWarning

# 禁用 SSL 警告
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

BASE_URL = "https://localhost:8000"

def print_section(title):
    """打印分节标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health_check():
    """测试健康检查"""
    print_section("测试 1: 健康检查")
    try:
        response = requests.get(f"{BASE_URL}/health", verify=False)
        print(f"✅ 状态码: {response.status_code}")
        print(f"✅ 响应: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_login(username="admin", password="admin123"):
    """登录并获取 token"""
    print_section("测试 2: 管理员登录")
    try:
        response = requests.post(
            f"{BASE_URL}/api/user/login",
            data={"username": username, "password": password},
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data["token"]
            print(f"✅ 登录成功")
            print(f"✅ Token: {token[:50]}...")
            print(f"✅ 用户角色: {data['user_info']['role']}")
            return token
        else:
            print(f"❌ 登录失败: {response.status_code}")
            print(f"❌ 响应: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def test_get_users(token):
    """测试获取用户列表"""
    print_section("测试 3: 获取用户列表")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers=headers,
            params={"page": 1, "page_size": 10},
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 状态码: {response.status_code}")
            print(f"✅ 总用户数: {data['total']}")
            print(f"✅ 当前页: {data['page']}")
            print(f"✅ 返回用户数: {len(data['users'])}")
            if data['users']:
                print(f"\n第一个用户:")
                print(f"  - ID: {data['users'][0]['id']}")
                print(f"  - 用户名: {data['users'][0]['username']}")
                print(f"  - 邮箱: {data['users'][0]['email']}")
                print(f"  - 角色: {data['users'][0]['role']}")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"❌ 响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_get_trainings(token):
    """测试获取训练记录"""
    print_section("测试 4: 获取训练记录列表")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/trainings",
            headers=headers,
            params={"page": 1, "page_size": 10},
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 状态码: {response.status_code}")
            print(f"✅ 总记录数: {data['total']}")
            print(f"✅ 当前页: {data['page']}")
            print(f"✅ 返回记录数: {len(data['trainings'])}")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"❌ 响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_get_dashboard_stats(token):
    """测试获取仪表盘统计"""
    print_section("测试 5: 获取仪表盘统计数据")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/statistics/dashboard",
            headers=headers,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 状态码: {response.status_code}")
            print(f"\n📊 用户统计:")
            print(f"  - 总用户数: {data['user_statistics']['total_users']}")
            print(f"  - 今日新增: {data['user_statistics']['new_users_today']}")
            print(f"  - 活跃用户: {data['user_statistics']['active_users']}")
            print(f"\n📊 训练统计:")
            print(f"  - 总训练次数: {data['training_statistics']['total_trainings']}")
            print(f"  - 今日训练: {data['training_statistics']['trainings_today']}")
            print(f"  - 平均分数: {data['training_statistics']['average_score']}")
            print(f"\n📊 视频检测统计:")
            print(f"  - 待检测: {data['video_statistics']['pending']}")
            print(f"  - 已完成: {data['video_statistics']['completed']}")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"❌ 响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_get_admin_logs(token):
    """测试获取操作日志"""
    print_section("测试 6: 获取管理员操作日志")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/logs",
            headers=headers,
            params={"page": 1, "page_size": 10},
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 状态码: {response.status_code}")
            print(f"✅ 总日志数: {data['total']}")
            print(f"✅ 当前页: {data['page']}")
            print(f"✅ 返回日志数: {len(data['logs'])}")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"❌ 响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_permission_denied():
    """测试权限控制（无 token）"""
    print_section("测试 7: 权限控制测试（无 token）")
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            verify=False
        )
        
        if response.status_code == 401:
            print(f"✅ 正确拒绝未授权访问: {response.status_code}")
            return True
        else:
            print(f"❌ 权限控制失败，期望 401，实际: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def main():
    """主测试函数"""
    print("\n" + "🔥"*30)
    print("  FireTrain 后台管理 API 测试")
    print("🔥"*30)
    
    results = []
    
    # 测试 1: 健康检查
    results.append(("健康检查", test_health_check()))
    
    # 测试 2: 登录
    token = test_login()
    if not token:
        print("\n⚠️  登录失败，无法继续测试其他接口")
        print("提示: 请确保数据库中有 admin 用户")
        return
    
    results.append(("管理员登录", token is not None))
    
    # 测试 3-6: 需要 token 的接口
    results.append(("获取用户列表", test_get_users(token)))
    results.append(("获取训练记录", test_get_trainings(token)))
    results.append(("获取仪表盘统计", test_get_dashboard_stats(token)))
    results.append(("获取操作日志", test_get_admin_logs(token)))
    
    # 测试 7: 权限控制
    results.append(("权限控制", test_permission_denied()))
    
    # 总结
    print_section("测试结果总结")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print("\n" + "="*60)
    print(f"总计: {passed}/{total} 测试通过")
    print("="*60)
    
    if passed == total:
        print("\n🎉 所有测试通过！任务 1.1 完成！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查")

if __name__ == "__main__":
    main()
