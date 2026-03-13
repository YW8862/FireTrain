#!/usr/bin/env python3
"""
FireTrain API 联调测试脚本
用于验证所有 API 接口的功能
"""

import requests
import json
import sys
from typing import Optional, Dict, Any

# API 基础 URL
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api"

# 测试配置
TEST_USER = {
    "username": "testuser",
    "email": "test@firetrain.com",
    "password": "test123456",
    "phone": "13800138000"
}

class Colors:
    """颜色定义"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_section(title: str):
    """打印章节标题"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_test(name: str, status: str, details: str = ""):
    """打印测试结果"""
    icon = "✅" if status == "PASS" else "❌"
    color = Colors.GREEN if status == "PASS" else Colors.RED
    print(f"{icon} {color}{name}{Colors.END}: {status}")
    if details:
        print(f"   {details}")


def make_request(method: str, url: str, **kwargs) -> Optional[requests.Response]:
    """发送 HTTP 请求并处理异常"""
    try:
        response = requests.request(method, url, timeout=30, **kwargs)
        return response
    except requests.exceptions.Timeout:
        print(f"{Colors.RED}❌ 请求超时 (30s){Colors.END}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}❌ 连接失败，请确保后端服务正在运行{Colors.END}")
        return None
    except Exception as e:
        print(f"{Colors.RED}❌ 请求异常：{e}{Colors.END}")
        return None


def test_user_registration() -> bool:
    """测试用户注册"""
    print_section("1. 用户注册测试")
    
    url = f"{BASE_URL}{API_PREFIX}/user/register"
    data = {
        "username": TEST_USER["username"],
        "email": TEST_USER["email"],
        "password": TEST_USER["password"],
        "phone": TEST_USER["phone"]
    }
    
    print(f"请求：POST {url}")
    print(f"数据：{json.dumps(data, indent=2)}\n")
    
    response = make_request("POST", url, json=data)
    
    if response is None:
        return False
    
    print(f"响应状态码：{response.status_code}")
    print(f"响应内容：{json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    
    if response.status_code in [200, 201]:
        print_test("用户注册", "PASS")
        return True
    elif response.status_code == 400 and "已存在" in response.json().get("detail", ""):
        print_test("用户注册", "PASS", "用户已存在")
        return True
    else:
        print_test("用户注册", "FAIL", f"状态码：{response.status_code}")
        return False


def test_user_login() -> Optional[str]:
    """测试用户登录并返回 Token"""
    print_section("2. 用户登录测试")
    
    url = f"{BASE_URL}{API_PREFIX}/user/login"
    data = {
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]
    }
    
    print(f"请求：POST {url}")
    print(f"数据：username={TEST_USER['username']}&password=******\n")
    
    response = make_request("POST", url, data=data)
    
    if response is None:
        return None
    
    print(f"响应状态码：{response.status_code}")
    print(f"响应内容：{json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    
    if response.status_code == 200:
        token = response.json().get("token")
        if token:
            print_test("用户登录", "PASS")
            print(f"Token: {token[:50]}...\n")
            return token
        else:
            print_test("用户登录", "FAIL", "未获取到 Token")
            return None
    else:
        print_test("用户登录", "FAIL", f"状态码：{response.status_code}")
        return None


def test_get_profile(token: str) -> bool:
    """测试获取用户信息"""
    print_section("3. 获取用户信息测试")
    
    url = f"{BASE_URL}{API_PREFIX}/user/profile"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"请求：GET {url}")
    print(f"Headers: Authorization: Bearer {token[:30]}...\n")
    
    response = make_request("GET", url, headers=headers)
    
    if response is None:
        return False
    
    print(f"响应状态码：{response.status_code}")
    print(f"响应内容：{json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    
    if response.status_code == 200:
        user_info = response.json()
        print_test("获取用户信息", "PASS")
        print(f"用户名：{user_info.get('username')}")
        print(f"邮箱：{user_info.get('email')}")
        print(f"角色：{user_info.get('role')}")
        return True
    else:
        print_test("获取用户信息", "FAIL", f"状态码：{response.status_code}")
        return False


def test_start_training(token: str) -> Optional[int]:
    """测试开始训练"""
    print_section("4. 开始训练测试")
    
    url = f"{BASE_URL}{API_PREFIX}/training/start"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "training_type": "extinguisher",
        "duration_seconds": 60
    }
    
    print(f"请求：POST {url}")
    print(f"数据：{json.dumps(data, indent=2)}\n")
    
    response = make_request("POST", url, headers=headers, json=data)
    
    if response is None:
        return None
    
    print(f"响应状态码：{response.status_code}")
    print(f"响应内容：{json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    
    if response.status_code == 200:
        training_id = response.json().get("training_id")
        if training_id:
            print_test("开始训练", "PASS")
            print(f"训练 ID: {training_id}")
            return training_id
        else:
            print_test("开始训练", "FAIL", "未获取到训练 ID")
            return None
    else:
        print_test("开始训练", "FAIL", f"状态码：{response.status_code}")
        return None


def test_get_training_history(token: str) -> bool:
    """测试获取训练历史"""
    print_section("5. 获取训练历史测试")
    
    url = f"{BASE_URL}{API_PREFIX}/training/history"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page": 1, "page_size": 10}
    
    print(f"请求：GET {url}")
    print(f"参数：page=1&page_size=10\n")
    
    response = make_request("GET", url, headers=headers, params=params)
    
    if response is None:
        return False
    
    print(f"响应状态码：{response.status_code}")
    print(f"响应内容：{json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    
    if response.status_code == 200:
        result = response.json()
        print_test("获取训练历史", "PASS")
        print(f"总记录数：{result.get('total', 0)}")
        print(f"当前页数：{result.get('page', 0)}")
        print(f"记录数量：{len(result.get('records', []))}")
        return True
    else:
        print_test("获取训练历史", "FAIL", f"状态码：{response.status_code}")
        return False


def test_get_personal_stats(token: str) -> bool:
    """测试获取个人统计"""
    print_section("6. 获取个人统计测试")
    
    url = f"{BASE_URL}{API_PREFIX}/stats/personal"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"请求：GET {url}\n")
    
    response = make_request("GET", url, headers=headers)
    
    if response is None:
        return False
    
    print(f"响应状态码：{response.status_code}")
    print(f"响应内容：{json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    
    if response.status_code == 200:
        stats = response.json()
        print_test("获取个人统计", "PASS")
        print(f"总训练次数：{stats.get('total_trainings', 0)}")
        print(f"完成次数：{stats.get('completed_trainings', 0)}")
        print(f"平均分：{stats.get('average_score', 0)}")
        print(f"最高分：{stats.get('best_score', 0)}")
        return True
    else:
        print_test("获取个人统计", "FAIL", f"状态码：{response.status_code}")
        return False


def test_get_trend_stats(token: str) -> bool:
    """测试获取训练趋势"""
    print_section("7. 获取训练趋势测试")
    
    url = f"{BASE_URL}{API_PREFIX}/stats/trend"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"days": 7}
    
    print(f"请求：GET {url}")
    print(f"参数：days=7\n")
    
    response = make_request("GET", url, headers=headers, params=params)
    
    if response is None:
        return False
    
    print(f"响应状态码：{response.status_code}")
    print(f"响应内容：{json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    
    if response.status_code == 200:
        result = response.json()
        print_test("获取训练趋势", "PASS")
        print(f"天数：{result.get('total_days', 0)}")
        print(f"数据点数：{len(result.get('trend_data', []))}")
        return True
    else:
        print_test("获取训练趋势", "FAIL", f"状态码：{response.status_code}")
        return False


def test_token_authentication() -> bool:
    """测试 Token 鉴权"""
    print_section("8. Token 鉴权测试")
    
    url = f"{BASE_URL}{API_PREFIX}/user/profile"
    headers = {"Authorization": "Bearer invalid_token"}
    
    print(f"请求：GET {url}")
    print(f"Headers: Authorization: Bearer invalid_token\n")
    
    response = make_request("GET", url, headers=headers)
    
    if response is None:
        return False
    
    print(f"响应状态码：{response.status_code}")
    print(f"响应内容：{json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    
    if response.status_code == 401:
        print_test("Token 鉴权", "PASS", "无效 Token 被正确拒绝")
        return True
    else:
        print_test("Token 鉴权", "FAIL", f"状态码：{response.status_code}")
        return False


def run_all_tests():
    """运行所有测试"""
    print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}🧪 FireTrain API 联调测试{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"\n后端地址：{BASE_URL}")
    print(f"测试账号：{TEST_USER['username']} / {TEST_USER['password']}\n")
    
    # 测试计数器
    total_tests = 0
    passed_tests = 0
    
    # 1. 用户注册
    total_tests += 1
    if test_user_registration():
        passed_tests += 1
    
    # 2. 用户登录
    token = test_user_login()
    total_tests += 1
    if token:
        passed_tests += 1
    else:
        print(f"\n{Colors.RED}⚠️  由于登录失败，后续需要 Token 的测试将跳过{Colors.END}\n")
        token = None
    
    # 3. 获取用户信息
    if token:
        total_tests += 1
        if test_get_profile(token):
            passed_tests += 1
    
    # 4. 开始训练
    if token:
        total_tests += 1
        if test_start_training(token):
            passed_tests += 1
    
    # 5. 获取训练历史
    if token:
        total_tests += 1
        if test_get_training_history(token):
            passed_tests += 1
    
    # 6. 获取个人统计
    if token:
        total_tests += 1
        if test_get_personal_stats(token):
            passed_tests += 1
    
    # 7. 获取训练趋势
    if token:
        total_tests += 1
        if test_get_trend_stats(token):
            passed_tests += 1
    
    # 8. Token 鉴权
    total_tests += 1
    if test_token_authentication():
        passed_tests += 1
    
    # 打印总结
    print_section("测试总结")
    print(f"总测试数：{total_tests}")
    print(f"通过数量：{Colors.GREEN}{passed_tests}{Colors.END}")
    print(f"失败数量：{Colors.RED}{total_tests - passed_tests}{Colors.END}")
    print(f"通过率：{(passed_tests/total_tests*100):.1f}%\n")
    
    if passed_tests == total_tests:
        print(f"{Colors.GREEN}🎉 所有测试通过！{Colors.END}\n")
        return 0
    else:
        print(f"{Colors.YELLOW}⚠️  部分测试失败，请检查日志{Colors.END}\n")
        return 1


if __name__ == "__main__":
    try:
        exit_code = run_all_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  测试被用户中断{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}❌ 测试过程中发生异常：{e}{Colors.END}")
        sys.exit(1)
