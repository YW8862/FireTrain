#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FireTrain 性能测试脚本
测试文档中涉及的各项性能指标

运行方式:
    cd /home/yw/FireTrain/backend
    python -m scripts.performance_test

或直接运行:
    cd /home/yw/FireTrain
    python scripts/performance_test.py
"""

import asyncio
import time
import statistics
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 添加 backend 路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# 导入项目模块
from app.core.config import settings


# ============ 配置 ============
API_BASE_URL = "http://localhost:8000/api"
TEST_USER = {"username": "admin", "password": "admin123"}
TEST_VIDEO_PATH = "../data/videos/test.mp4"


class Colors:
    """终端颜色输出"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(msg: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}{Colors.ENDC}")


def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.ENDC}")


def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.ENDC}")


def print_info(msg: str):
    print(f"{Colors.CYAN}ℹ {msg}{Colors.ENDC}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.ENDC}")


# ============ 1. 统计查询性能测试 ============

async def test_statistics_performance():
    """测试统计查询性能：传统方案 vs 数据库聚合方案"""
    print_header("1. 统计查询性能测试")

    # 确保后端服务正常运行
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code != 200:
                print_error("后端服务未正常运行")
                return {}
    except Exception as e:
        print_error(f"无法连接到后端服务: {e}")
        print_info("请确保后端服务正在运行 (uvicorn)")
        return {}

    # 登录获取 token
    token = await login()
    if not token:
        print_error("登录失败，无法进行测试")
        return {}

    headers = {"Authorization": f"Bearer {token}"}

    # 测试统计接口响应时间
    stats_endpoints = [
        "/stats/personal",
        "/stats/trend?days=7",
        "/stats/step-analysis",
        "/stats/overview?days=7",
    ]

    results = {}
    all_times = []

    print_info("测试各统计接口响应时间...")

    for endpoint in stats_endpoints:
        times = []
        for i in range(5):
            start = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}{endpoint}",
                    headers=headers,
                    timeout=30.0
                )
            elapsed = (time.time() - start) * 1000  # ms
            times.append(elapsed)
            all_times.append(elapsed)
            await asyncio.sleep(0.1)

        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0

        results[endpoint] = {
            "avg_ms": round(avg_time, 2),
            "min_ms": round(min_time, 2),
            "max_ms": round(max_time, 2),
            "std_dev": round(std_dev, 2),
        }

        print_success(f"{endpoint}: 平均 {avg_time:.2f}ms (min: {min_time:.2f}ms, max: {max_time:.2f}ms)")

    # 分析统计：平均响应时间
    overall_avg = statistics.mean(all_times)
    print_info(f"\n整体平均响应时间: {overall_avg:.2f}ms")

    return results


# ============ 2. 数据库聚合性能测试 ============

async def test_database_aggregation():
    """测试数据库聚合 vs 内存聚合性能"""
    print_header("2. 数据库聚合性能测试")

    # 使用与后端相同的数据库配置
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with AsyncSession(engine) as session:
        try:
            # 获取训练记录数量
            result = await session.execute(text("SELECT COUNT(*) as cnt FROM training_records"))
            count = result.scalar() or 0
            print_info(f"数据库中训练记录数量: {count}")

            if count == 0:
                print_warning("数据库中没有训练记录，无法进行有效的性能测试")
                print_info("请先创建一些训练数据再运行性能测试")
                return {}

            # 测试数据库聚合方案 (使用 SQL 的 AVG, MAX, JSON_EXTRACT)
            print_info("\n测试数据库聚合查询性能...")

            # 模拟数据库聚合方案 (单次查询)
            db_query_times = []
            for _ in range(10):
                start = time.time()

                # 使用数据库原生聚合
                result = await session.execute(text("""
                    SELECT
                        COUNT(*) as total_count,
                        AVG(CAST(total_score AS REAL)) as avg_score,
                        MAX(CAST(total_score AS REAL)) as max_score,
                        MIN(CAST(total_score AS REAL)) as min_score
                    FROM training_records
                    WHERE status = 'done' AND total_score IS NOT NULL
                """))

                row = result.fetchone()
                elapsed = (time.time() - start) * 1000
                db_query_times.append(elapsed)

            db_avg = statistics.mean(db_query_times)
            print_success(f"数据库聚合方案平均耗时: {db_avg:.2f}ms (10次查询)")

            # 对比：模拟内存聚合 (多次查询 + Python 计算)
            mem_agg_times = []
            for _ in range(10):
                start = time.time()

                # 模拟多次查询获取所有记录
                result = await session.execute(text("""
                    SELECT total_score FROM training_records
                    WHERE status = 'done' AND total_score IS NOT NULL
                """))
                rows = result.fetchall()
                scores = [float(row[0]) for row in rows]

                # Python 计算
                if scores:
                    avg = sum(scores) / len(scores)
                    max_score = max(scores)

                elapsed = (time.time() - start) * 1000
                mem_agg_times.append(elapsed)

            mem_avg = statistics.mean(mem_agg_times)
            print_success(f"内存聚合方案平均耗时: {mem_avg:.2f}ms (10次查询)")

            # 计算性能提升
            improvement = ((mem_avg - db_avg) / mem_avg) * 100 if mem_avg > 0 else 0
            print_info(f"\n性能提升: {improvement:.1f}%")

            # 验证公式: S_average = (1/n) * Σscore_i
            print_header("验证数据库聚合公式")
            result = await session.execute(text("""
                SELECT
                    AVG(CAST(total_score AS REAL)) as avg_formula_result,
                    MAX(CAST(total_score AS REAL)) as max_formula_result
                FROM training_records
                WHERE status = 'done' AND total_score IS NOT NULL
            """))
            row = result.fetchone()
            print_info(f"S_average (数据库): {row[0]:.2f}" if row[0] else "N/A")
            print_info(f"S_max (数据库): {row[1]:.2f}" if row[1] else "N/A")

            return {
                "db_avg_ms": round(db_avg, 2),
                "mem_avg_ms": round(mem_avg, 2),
                "improvement_percent": round(improvement, 1),
                "record_count": count,
            }

        except Exception as e:
            print_error(f"数据库测试失败: {e}")
            return {}


# ============ 3. API 并发性能测试 ============

async def test_concurrent_performance():
    """测试并发请求性能"""
    print_header("3. API 并发性能测试")

    token = await login()
    if not token:
        return {}

    headers = {"Authorization": f"Bearer {token}"}

    async def make_request(client, endpoint):
        start = time.time()
        try:
            response = await client.get(f"{API_BASE_URL}{endpoint}", headers=headers, timeout=30.0)
            elapsed = (time.time() - start) * 1000
            return {"success": response.status_code == 200, "time": elapsed}
        except Exception as e:
            return {"success": False, "time": 0, "error": str(e)}

    print_info("测试 20 个并发请求...")

    async with httpx.AsyncClient() as client:
        tasks = []
        for _ in range(20):
            tasks.append(make_request(client, "/stats/personal"))

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

    success_count = sum(1 for r in results if r["success"])
    times = [r["time"] for r in results if r["success"]]

    print_success(f"并发测试完成: {success_count}/20 成功")
    print_info(f"总耗时: {total_time*1000:.2f}ms")
    if times:
        print_info(f"平均响应: {statistics.mean(times):.2f}ms")
        print_info(f"最大响应: {max(times):.2f}ms")

    return {"success_count": success_count, "total_time_ms": round(total_time*1000, 2)}


# ============ 4. 登录认证性能测试 ============

async def test_auth_performance():
    """测试 JWT 认证性能"""
    print_header("4. JWT 认证性能测试")

    times = []
    for i in range(10):
        start = time.time()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/user/login",
                data={"username": "admin", "password": "admin123"},
                timeout=10.0
            )
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        await asyncio.sleep(0.1)

    avg_time = statistics.mean(times)
    print_success(f"登录平均响应时间: {avg_time:.2f}ms")
    print_info(f"文档参考值: 约 50-100ms")

    return {"avg_login_ms": round(avg_time, 2)}


# ============ 5. 训练记录 CRUD 性能测试 ============

async def test_training_crud_performance():
    """测试训练记录 CRUD 性能"""
    print_header("5. 训练记录 CRUD 性能测试")

    token = await login()
    if not token:
        return {}

    headers = {"Authorization": f"Bearer {token}"}

    # 测试历史记录查询
    times = []
    for page in range(1, 6):
        start = time.time()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/training/history?page={page}&page_size=10",
                headers=headers,
                timeout=30.0
            )
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        await asyncio.sleep(0.1)

    avg_time = statistics.mean(times)
    print_success(f"训练历史查询平均响应时间: {avg_time:.2f}ms")

    return {"history_avg_ms": round(avg_time, 2)}


# ============ 辅助函数 ============

async def login() -> str | None:
    """登录获取 token"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/user/login",
                data={"username": "admin", "password": "admin123"},
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json().get("token")
    except Exception as e:
        print_error(f"登录失败: {e}")
    return None


async def check_backend_health() -> bool:
    """检查后端服务健康状态"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            return response.status_code == 200
    except:
        return False


# ============ 主函数 ============

async def main():
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          FireTrain 性能测试套件                               ║")
    print("║          测试文档中涉及的各项性能指标                          ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")

    # 检查后端服务
    print_info("检查后端服务状态...")
    if not await check_backend_health():
        print_error("后端服务未运行，请先启动后端服务:")
        print_info("  cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return

    print_success("后端服务运行正常")

    results = {}

    # 1. 统计查询性能
    results["statistics"] = await test_statistics_performance()

    # 2. 数据库聚合性能
    results["database_aggregation"] = await test_database_aggregation()

    # 3. 并发性能
    results["concurrent"] = await test_concurrent_performance()

    # 4. 认证性能
    results["auth"] = await test_auth_performance()

    # 5. CRUD 性能
    results["crud"] = await test_training_crud_performance()

    # 汇总报告
    print_header("性能测试汇总报告")

    print(f"\n{Colors.BOLD}文档参考指标 vs 实际测试结果:{Colors.ENDC}")
    print("-" * 60)
    print(f"{'指标':<30} {'文档值':<15} {'实测值':<15}")
    print("-" * 60)

    if "statistics" in results and results["statistics"]:
        avg_stat = statistics.mean([r["avg_ms"] for r in results["statistics"].values()])
        print(f"{'统计接口平均响应时间':<30} {'<200ms':<15} {avg_stat:.2f}ms")

    if "database_aggregation" in results and results["database_aggregation"]:
        db_result = results["database_aggregation"]
        print(f"{'数据库聚合响应时间':<30} {'115ms':<15} {db_result.get('db_avg_ms', 'N/A')}ms")
        print(f"{'性能提升':<30} {'86.4%':<15} {db_result.get('improvement_percent', 'N/A')}%")

    if "auth" in results and results["auth"]:
        print(f"{'登录响应时间':<30} {'~100ms':<15} {results['auth'].get('avg_login_ms', 'N/A')}ms")

    if "crud" in results and results["crud"]:
        print(f"{'历史记录查询时间':<30} {'<500ms':<15} {results['crud'].get('history_avg_ms', 'N/A')}ms")

    print("-" * 60)

    print(f"\n{Colors.GREEN}测试完成！{Colors.ENDC}")
    print_info("建议：对比文档中的性能指标，如有较大差异需分析原因")


if __name__ == "__main__":
    asyncio.run(main())