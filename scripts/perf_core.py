#!/usr/bin/env python3
"""FireTrain 核心接口性能测试（精简版）

覆盖：响应时间、并发、吞吐、资源使用
结果输出：stdout + perf_results.json
"""
import asyncio, json, os, statistics, time, sys
from datetime import datetime
import httpx, psutil

API = "http://localhost:8000"
USER = {"username": "perf_user", "password": "perf123456"}
RESULTS: dict = {}
RESULTS_FILE = os.path.join(os.path.dirname(__file__), "perf_results.json")

# ============ 单接口响应时间（核心 8 个） ============
CORE_ENDPOINTS = [
    ("GET", "/health", None, "健康检查"),
    ("POST", "/api/user/login", {"data": USER}, "用户登录"),
    ("GET", "/api/user/profile", None, "获取个人信息"),
    ("GET", "/api/training/types", None, "训练类型列表"),
    ("GET", "/api/training/history?page=1&page_size=20", None, "训练历史"),
    ("GET", "/api/stats/personal", None, "个人统计"),
    ("GET", "/api/stats/trend?days=7", None, "训练趋势"),
    ("GET", "/api/stats/step-analysis", None, "步骤分析"),
    ("GET", "/api/stats/overview?days=7", None, "统计总览"),
]

async def login_token(client: httpx.AsyncClient) -> str:
    r = await client.post(f"{API}/api/user/login", data=USER, timeout=10)
    r.raise_for_status()
    return r.json()["token"]

async def bench_endpoint(client, method, path, opts, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"{API}{path}"
    times = []
    successes = 0
    n = 5
    for _ in range(n):
        t0 = time.perf_counter()
        try:
            if method == "GET":
                r = await client.get(url, headers=headers, timeout=30)
            else:
                r = await client.post(url, headers=headers, timeout=30, **opts or {})
            ok = r.status_code in (200, 201)
        except Exception:
            ok = False
        elapsed_ms = (time.perf_counter() - t0) * 1000
        times.append(elapsed_ms)
        if ok:
            successes += 1
    return {
        "n": n,
        "success": successes,
        "avg_ms": round(statistics.mean(times), 2),
        "p50_ms": round(statistics.median(times), 2),
        "p95_ms": round(sorted(times)[int(n * 0.95) - 1], 2) if n >= 2 else round(times[-1], 2),
        "min_ms": round(min(times), 2),
        "max_ms": round(max(times), 2),
    }

async def response_time_test():
    print("\n== [1/4] 单接口响应时间 ==")
    out = {}
    async with httpx.AsyncClient() as c:
        token = await login_token(c)
        for method, path, opts, name in CORE_ENDPOINTS:
            r = await bench_endpoint(c, method, path, opts,
                                     token=None if "/login" in path or "/health" in path else token)
            out[name] = {"method": method, "path": path, **r}
            status = "✓" if r["success"] == r["n"] else "✗"
            print(f"  {status} {name:<14} avg={r['avg_ms']:>7.2f}ms  p95={r['p95_ms']:>7.2f}ms  max={r['max_ms']:>7.2f}ms")
    return out

# ============ 并发压测 ============
async def run_concurrent(client, method, path, headers, concurrency, total):
    sem = asyncio.Semaphore(concurrency)
    times, ok, err = [], 0, 0
    t0 = time.perf_counter()
    async def one():
        nonlocal ok, err
        async with sem:
            s = time.perf_counter()
            try:
                if method == "GET":
                    r = await client.get(f"{API}{path}", headers=headers, timeout=30)
                else:
                    r = await client.post(f"{API}{path}", headers=headers, timeout=30, data=USER)
                if r.status_code in (200, 201):
                    ok += 1
                else:
                    err += 1
            except Exception:
                err += 1
            times.append((time.perf_counter() - s) * 1000)
    await asyncio.gather(*[one() for _ in range(total)])
    wall = (time.perf_counter() - t0)
    return {
        "concurrency": concurrency,
        "total_requests": total,
        "wall_time_s": round(wall, 3),
        "qps": round(total / wall, 2),
        "success": ok,
        "failed": err,
        "avg_ms": round(statistics.mean(times), 2),
        "p50_ms": round(statistics.median(times), 2),
        "p95_ms": round(sorted(times)[int(len(times) * 0.95) - 1], 2),
        "max_ms": round(max(times), 2),
    }

async def concurrency_test():
    print("\n== [2/4] 并发压测（多接口） ==")
    out = {}
    # 读接口：覆盖静态/轻量、单表聚合、多表聚合、分页查询四种代码路径
    READ_APIS = [
        ("/api/training/types", "轻量静态读"),
        ("/api/user/profile", "单表主键读"),
        ("/api/stats/personal", "单表聚合"),
        ("/api/stats/trend?days=7", "时序聚合"),
        ("/api/stats/overview?days=7", "多表聚合"),
        ("/api/training/history?page=1&page_size=20", "分页查询"),
    ]
    # 写接口
    WRITE_APIS = [
        ("/api/user/login", "POST", "登录（bcrypt）"),
        ("/api/user/logout", "POST", "登出（Token 黑名单）"),
    ]

    async with httpx.AsyncClient() as c:
        token = await login_token(c)
        headers = {"Authorization": f"Bearer {token}"}

        for path, label in READ_APIS:
            for conc, total in [(10, 100), (50, 200)]:
                print(f"  -- {label}  GET {path}  c={conc}  total={total}")
                r = await run_concurrent(c, "GET", path, headers, conc, total)
                out[f"GET {path} @c={conc}"] = r
                print(f"     QPS={r['qps']:>7}  success={r['success']:>3}/{total:<3}  avg={r['avg_ms']:>8.2f}ms  p95={r['p95_ms']:>8.2f}ms  max={r['max_ms']:>8.2f}ms")

        # 写：登录（需无 token）
        for conc, total in [(10, 50), (50, 150)]:
            print(f"  -- 登录  POST /api/user/login  c={conc}  total={total}")
            r = await run_concurrent(c, "POST", "/api/user/login", {}, conc, total)
            out[f"POST /api/user/login @c={conc}"] = r
            print(f"     QPS={r['qps']:>7}  success={r['success']:>3}/{total:<3}  avg={r['avg_ms']:>8.2f}ms  p95={r['p95_ms']:>8.2f}ms  max={r['max_ms']:>8.2f}ms")

        # 写：登出（需 token；登出会让 token 进黑名单，故并发场景下只跑一轮 c=20 总数 100）
        print(f"  -- 登出  POST /api/user/logout  c=20  total=100")
        r = await run_concurrent(c, "POST", "/api/user/logout", headers, 20, 100)
        out[f"POST /api/user/logout @c=20"] = r
        print(f"     QPS={r['qps']:>7}  success={r['success']:>3}/100  avg={r['avg_ms']:>8.2f}ms  p95={r['p95_ms']:>8.2f}ms  max={r['max_ms']:>8.2f}ms")
    return out

# ============ 持续吞吐 / 资源监控 ============
async def sustained_load(client, path, headers, duration_s, conc):
    times, ok, err = [], 0, 0
    t0 = time.perf_counter()
    end = t0 + duration_s
    sem = asyncio.Semaphore(conc)
    async def worker():
        nonlocal ok, err
        while time.perf_counter() < end:
            async with sem:
                s = time.perf_counter()
                try:
                    r = await client.get(f"{API}{path}", headers=headers, timeout=30)
                    if r.status_code in (200, 201): ok += 1
                    else: err += 1
                except Exception:
                    err += 1
                times.append((time.perf_counter() - s) * 1000)
                await asyncio.sleep(0)  # yield
    await asyncio.gather(*[worker() for _ in range(conc)])
    wall = time.perf_counter() - t0
    return {
        "concurrency": conc,
        "duration_s": round(wall, 2),
        "total_requests": ok + err,
        "qps": round((ok + err) / wall, 2),
        "success": ok,
        "failed": err,
        "error_rate_pct": round(err / (ok + err) * 100, 2) if (ok + err) else 0,
        "avg_ms": round(statistics.mean(times), 2) if times else 0,
        "p95_ms": round(sorted(times)[int(len(times) * 0.95) - 1], 2) if len(times) > 1 else 0,
        "max_ms": round(max(times), 2) if times else 0,
    }

def sample_proc(pid, interval_s):
    p = psutil.Process(pid)
    cpu_samples, mem_samples = [], []
    # 一次性 0.5s 采样
    try:
        p.cpu_percent(None)
    except Exception:
        pass
    for _ in range(int(interval_s / 0.5)):
        try:
            cpu_samples.append(p.cpu_percent(interval=0.5))
            mem_samples.append(p.memory_info().rss / 1024 / 1024)  # MB
        except Exception:
            break
    return {
        "cpu_avg_pct": round(statistics.mean(cpu_samples), 1) if cpu_samples else 0,
        "cpu_peak_pct": round(max(cpu_samples), 1) if cpu_samples else 0,
        "mem_avg_mb": round(statistics.mean(mem_samples), 1) if mem_samples else 0,
        "mem_peak_mb": round(max(mem_samples), 1) if mem_samples else 0,
    }

def find_backend_pid():
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cl = p.info.get('cmdline') or []
            if any('uvicorn' in s for s in cl) and any('app.main:app' in s for s in cl):
                return p.info['pid']
        except Exception:
            continue
    return None

async def resource_test():
    print("\n== [3/4] 持续负载 + 资源监控（GET /api/stats/overview，30s @c=20） ==")
    async with httpx.AsyncClient() as c:
        token = await login_token(c)
        headers = {"Authorization": f"Bearer {token}"}
        # 找出后端进程（如果有多个则采样平均值）
        pid = find_backend_pid()
        print(f"  后端进程 PID: {pid}")
        # 启动负载 + 监控
        load_task = asyncio.create_task(sustained_load(c, "/api/stats/overview", headers, duration_s=30, conc=20))
        await asyncio.sleep(2)  # 预热
        res = sample_proc(pid, 28) if pid else {"cpu_avg_pct": "N/A", "mem_avg_mb": "N/A"}
        load = await load_task
    print(f"  QPS={load['qps']}  success={load['success']}  err={load['failed']}  p95={load['p95_ms']}ms")
    print(f"  CPU avg={res['cpu_avg_pct']}%  peak={res['cpu_peak_pct']}%  MEM avg={res['mem_avg_mb']}MB  peak={res['mem_peak_mb']}MB")
    return {"sustained_load": load, "resource": res}

# ============ 综合分析 ============
async def analyze_test():
    print("\n== [4/4] 综合接口分析 ==")
    # 错误率 + 慢请求识别
    out = {}
    async with httpx.AsyncClient() as c:
        token = await login_token(c)
        h = {"Authorization": f"Bearer {token}"}
        # 拉一遍 9 个核心接口（多次），统计错误率
        endpoints = [("/health", None), ("/api/user/profile", h), ("/api/stats/overview?days=7", h),
                     ("/api/stats/personal", h), ("/api/stats/trend?days=30", h),
                     ("/api/training/history?page=1&page_size=50", h)]
        for path, hdr in endpoints:
            ok = err = 0
            for _ in range(20):
                try:
                    r = await c.get(f"{API}{path}", headers=hdr or {}, timeout=15)
                    if r.status_code in (200, 201): ok += 1
                    else: err += 1
                except Exception:
                    err += 1
            rate = round(err / 20 * 100, 1)
            out[path] = {"success": ok, "failed": err, "error_rate_pct": rate}
            print(f"  {path:<40}  错误率 {rate}%")
    return out

async def main():
    print(f"FireTrain 性能测试  @ {datetime.now().isoformat(timespec='seconds')}")
    print(f"后端: {API}  测试账号: {USER['username']}")
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{API}/health", timeout=5)
            assert r.status_code == 200
    except Exception as e:
        print(f"后端不可达: {e}")
        sys.exit(1)

    RESULTS["response_time"] = await response_time_test()
    RESULTS["concurrency"] = await concurrency_test()
    RESULTS["sustained"] = await resource_test()
    RESULTS["reliability"] = await analyze_test()

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(RESULTS, f, ensure_ascii=False, indent=2)
    print(f"\n结果已写入 {RESULTS_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
