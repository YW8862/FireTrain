#!/usr/bin/env python3
"""核心接口并发压测：多梯度并发 + 成功率/失败率/QPS/平均/P95。

输出：
  docs/perf-load-YYYYMMDD-HHMMSS.md   可读报告
  docs/perf-load-YYYYMMDD-HHMMSS.json 原始数据
"""
import asyncio
import json
import os
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx


API = "http://localhost:8000"
USER = {"username": "yangwei", "password": "yangwei2003!"}

# 核心接口：覆盖静态/单表/聚合/分页/写 五种代码路径
CORE_ENDPOINTS = [
    {"name": "健康检查",         "method": "GET",  "path": "/health",                                         "auth": False, "weight": "轻量静态读"},
    {"name": "用户登录",         "method": "POST", "path": "/api/user/login",     "data": USER,              "auth": False, "weight": "写+bcrypt"},
    {"name": "个人信息",         "method": "GET",  "path": "/api/user/profile",                                "auth": True,  "weight": "单表主键读"},
    {"name": "个人统计",         "method": "GET",  "path": "/api/stats/personal",                              "auth": True,  "weight": "单表聚合"},
    {"name": "统计总览",         "method": "GET",  "path": "/api/stats/overview?days=7",                       "auth": True,  "weight": "多表聚合"},
    {"name": "训练历史",         "method": "GET",  "path": "/api/training/history?page=1&page_size=20",        "auth": True,  "weight": "分页查询"},
]

CONCURRENCY_LEVELS = [10, 50, 100, 200]
REQUESTS_PER_BATCH = 200
TIMEOUT_S = 30


def percentile(sorted_list, p):
    """按线性插值计算 p 分位数（0-100），输入已排序列表。"""
    if not sorted_list:
        return 0.0
    if len(sorted_list) == 1:
        return sorted_list[0]
    k = (len(sorted_list) - 1) * (p / 100)
    f = int(k)
    c = min(f + 1, len(sorted_list) - 1)
    if f == c:
        return sorted_list[f]
    return sorted_list[f] + (sorted_list[c] - sorted_list[f]) * (k - f)


async def login(client: httpx.AsyncClient) -> str:
    r = await client.post(f"{API}/api/user/login", data=USER, timeout=10)
    r.raise_for_status()
    return r.json()["token"]


async def hit(client, method, path, headers, data):
    t0 = time.perf_counter()
    try:
        if method == "GET":
            r = await client.get(f"{API}{path}", headers=headers, timeout=TIMEOUT_S)
        else:
            r = await client.post(f"{API}{path}", headers=headers, data=data, timeout=TIMEOUT_S)
        return (r.status_code, (time.perf_counter() - t0) * 1000, None)
    except Exception as e:
        return (0, (time.perf_counter() - t0) * 1000, str(e))


async def run_concurrency(client, ep, headers, concurrency, total):
    """对单个接口在固定并发下打 total 次请求。"""
    sem = asyncio.Semaphore(concurrency)
    results = []  # list of (status, latency_ms, err)

    async def one():
        async with sem:
            res = await hit(client, ep["method"], ep["path"], headers, ep.get("data"))
            results.append(res)

    t0 = time.perf_counter()
    await asyncio.gather(*[one() for _ in range(total)])
    wall = time.perf_counter() - t0

    statuses = [s for s, _, _ in results]
    lats = sorted([l for _, l, _ in results])
    succ = sum(1 for s, _, _ in results if s in (200, 201))
    errs = [r for r in results if r[0] not in (200, 201)]

    # 错误分布：按 status code 或 exception 分组
    err_breakdown = {}
    for s, _, e in errs:
        key = str(s) if s else f"exception:{type(e).__name__ if e else 'unknown'}"
        err_breakdown[key] = err_breakdown.get(key, 0) + 1

    n = len(results)
    return {
        "endpoint": ep["name"],
        "method": ep["method"],
        "path": ep["path"],
        "weight": ep["weight"],
        "concurrency": concurrency,
        "total_requests": n,
        "wall_time_s": round(wall, 3),
        "qps": round(n / wall, 2),
        "success": succ,
        "failed": n - succ,
        "success_rate_pct": round(succ / n * 100, 2) if n else 0,
        "error_rate_pct": round((n - succ) / n * 100, 2) if n else 0,
        "error_breakdown": err_breakdown,
        "avg_ms": round(statistics.mean(lats), 2) if lats else 0,
        "p50_ms": round(percentile(lats, 50), 2),
        "p95_ms": round(percentile(lats, 95), 2),
        "p99_ms": round(percentile(lats, 99), 2),
        "min_ms": round(min(lats), 2) if lats else 0,
        "max_ms": round(max(lats), 2) if lats else 0,
    }


def render_markdown(meta, all_results):
    """生成可读的 Markdown 报告。"""
    lines = []
    lines.append(f"# FireTrain 核心接口并发压测报告")
    lines.append("")
    lines.append(f"- **生成时间**: {meta['generated_at']}")
    lines.append(f"- **后端地址**: `{API}`")
    lines.append(f"- **测试账号**: `{USER['username']}`")
    lines.append(f"- **并发梯度**: {CONCURRENCY_LEVELS}")
    lines.append(f"- **单梯度请求数**: {REQUESTS_PER_BATCH}")
    lines.append(f"- **Python 工具链**: httpx (asyncio) + statistics")
    lines.append("")
    lines.append("## 1. 接口选择与代码路径覆盖")
    lines.append("")
    lines.append("| 接口 | 方法 | 路径 | 代码路径 |")
    lines.append("|---|---|---|---|")
    for ep in CORE_ENDPOINTS:
        auth_mark = "🔒" if ep["auth"] else "🌐"
        lines.append(f"| {auth_mark} {ep['name']} | {ep['method']} | `{ep['path']}` | {ep['weight']} |")
    lines.append("")
    lines.append("> 🔒 = 需要 JWT；🌐 = 公开接口。")
    lines.append("")

    # 按接口分组展示
    for ep in CORE_ENDPOINTS:
        lines.append(f"## 2.{CORE_ENDPOINTS.index(ep)+1} {ep['name']}（{ep['method']} {ep['path']}）")
        lines.append("")
        lines.append("| 并发 | QPS | 成功率 | 失败率 | 平均(ms) | P50(ms) | P95(ms) | P99(ms) | max(ms) | 错误分布 |")
        lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
        ep_results = [r for r in all_results if r["endpoint"] == ep["name"]]
        for r in ep_results:
            errs = ", ".join(f"{k}:{v}" for k, v in r["error_breakdown"].items()) or "—"
            lines.append(
                f"| {r['concurrency']} | {r['qps']} | {r['success_rate_pct']}% | {r['error_rate_pct']}% | "
                f"{r['avg_ms']} | {r['p50_ms']} | {r['p95_ms']} | {r['p99_ms']} | {r['max_ms']} | {errs} |"
            )
        lines.append("")

    # 横向对比：每个并发级别下谁最快
    lines.append("## 3. 同并发下的 QPS 横向对比")
    lines.append("")
    for c in CONCURRENCY_LEVELS:
        lines.append(f"### 并发 = {c}")
        lines.append("")
        lines.append("| 接口 | QPS | P95(ms) | 失败率 |")
        lines.append("|---|---:|---:|---:|")
        rows = sorted(
            [r for r in all_results if r["concurrency"] == c],
            key=lambda x: -x["qps"]
        )
        for r in rows:
            lines.append(f"| {r['endpoint']} | {r['qps']} | {r['p95_ms']} | {r['error_rate_pct']}% |")
        lines.append("")

    # 瓶颈识别
    lines.append("## 4. 瓶颈与观察")
    lines.append("")
    # 找出 P95 > 100ms 或 错误率 > 0% 的项
    issues = []
    for r in all_results:
        if r["error_rate_pct"] > 0:
            issues.append(f"- ⚠️ **{r['endpoint']}** @c={r['concurrency']}: 失败率 {r['error_rate_pct']}%（{r['error_breakdown']}）")
        elif r["p95_ms"] > 200:
            issues.append(f"- 🐢 **{r['endpoint']}** @c={r['concurrency']}: P95 = {r['p95_ms']}ms 偏高")
    if issues:
        lines.extend(issues)
    else:
        lines.append("- ✅ 所有接口在测试梯度内未出现失败，P95 均在 200ms 以内。")
    lines.append("")

    return "\n".join(lines)


async def main():
    print(f"FireTrain 核心接口并发压测  @ {datetime.now().isoformat(timespec='seconds')}")
    print(f"后端: {API}  账号: {USER['username']}")
    print(f"并发梯度: {CONCURRENCY_LEVELS}  单梯度请求数: {REQUESTS_PER_BATCH}\n")

    # 健康检查
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{API}/health", timeout=5)
            assert r.status_code == 200
    except Exception as e:
        print(f"❌ 后端不可达: {e}")
        sys.exit(1)

    async with httpx.AsyncClient() as client:
        token = await login(client)
        headers = {"Authorization": f"Bearer {token}"}

        all_results = []
        for ep in CORE_ENDPOINTS:
            auth_headers = headers if ep["auth"] else {}
            for conc in CONCURRENCY_LEVELS:
                print(f"  → {ep['name']:<8s} {ep['method']} {ep['path']}  c={conc}  n={REQUESTS_PER_BATCH}")
                r = await run_concurrency(client, ep, auth_headers, conc, REQUESTS_PER_BATCH)
                all_results.append(r)
                print(f"     QPS={r['qps']:>7}  ok={r['success']:>3}/{r['total_requests']}  "
                      f"avg={r['avg_ms']:>7.2f}ms  p95={r['p95_ms']:>7.2f}ms  err={r['failed']}")

    # 输出
    repo_root = Path(__file__).resolve().parent.parent
    docs_dir = repo_root / "docs"
    docs_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    md_path = docs_dir / f"perf-load-{ts}.md"
    json_path = docs_dir / f"perf-load-{ts}.json"

    meta = {"generated_at": datetime.now().isoformat(timespec='seconds'), "concurrency_levels": CONCURRENCY_LEVELS, "requests_per_batch": REQUESTS_PER_BATCH}
    md_content = render_markdown(meta, all_results)
    md_path.write_text(md_content, encoding="utf-8")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "user": USER, "results": all_results}, f, ensure_ascii=False, indent=2)

    print(f"\n📝 Markdown 报告: {md_path}")
    print(f"📦 原始数据:    {json_path}")


if __name__ == "__main__":
    asyncio.run(main())
