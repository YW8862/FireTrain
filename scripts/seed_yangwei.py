#!/usr/bin/env python3
"""给 yangwei 上传 25 个视频，每 120 秒一个。"""
import asyncio, os, random, sys, time
from pathlib import Path

os.chdir("/home/yw/FireTrain/backend")
sys.path.insert(0, "/home/yw/FireTrain/backend")

import httpx
from sqlalchemy import text
from app.db.session import async_session_maker

API = "http://localhost:8000"
VIDEOS = sorted(Path("/home/yw/FireTrain/data/videos/admin_uploads").glob("*.mp4"))
TARGET = "yangwei"
N = 25
INTERVAL = 120  # 秒


async def verify_user():
    async with async_session_maker() as s:
        uid = (await s.execute(text("SELECT id FROM users WHERE username=:u"), {"u": TARGET})).scalar()
        if not uid:
            raise SystemExit(f"❌ 用户 {TARGET} 不存在")
        print(f"[verify] {TARGET} uid={uid}  DB cwd={os.getcwd()}", flush=True)


async def login(c, u, p):
    r = await c.post(f"{API}/api/user/login", data={"username": u, "password": p}, timeout=10)
    r.raise_for_status()
    return r.json()["token"]


async def main():
    await verify_user()
    random.seed(11)
    chosen = [random.choice(VIDEOS) for _ in range(N)]

    async with httpx.AsyncClient(timeout=30) as c:
        admin_token = await login(c, "admin", "admin123")
        h = {"Authorization": f"Bearer {admin_token}"}

        print(f"[upload] {N} 个, {INTERVAL}s/个, 总预计 {N*INTERVAL/60:.0f} 分钟", flush=True)
        ids = []
        t0 = time.time()
        for i, v in enumerate(chosen, 1):
            with open(v, "rb") as f:
                files = {"file": (v.name, f, "video/mp4")}
                data = {"username": TARGET, "training_type": "fire_extinguisher"}
                try:
                    r = await c.post(f"{API}/api/admin/video/upload",
                                     headers=h, files=files, data=data, timeout=60)
                    r.raise_for_status()
                    tid = r.json()["training_id"]
                    ids.append(tid)
                    elapsed = time.time() - t0
                    print(f"  [{i:2}/{N}] ✓ tid={tid}  +{elapsed:5.0f}s  next in {INTERVAL}s", flush=True)
                except Exception as e:
                    print(f"  [{i:2}/{N}] ✗ {e}", flush=True)
            if i < N:
                await asyncio.sleep(INTERVAL)
        print(f"[upload] 全部发起，{(time.time()-t0):.0f}s", flush=True)

        # 持续 poll 直到全部完成
        print(f"[poll] 等待 AI 分析完成 ...", flush=True)
        todo = set(ids)
        last_print = time.time()
        while todo:
            await asyncio.sleep(20)
            for tid in list(todo):
                try:
                    d = (await c.get(f"{API}/api/admin/video/status/{tid}", headers=h, timeout=10)).json()
                except Exception:
                    continue
                if d.get("status") in ("done", "failed"):
                    todo.discard(tid)
            if time.time() - last_print > 60:
                print(f"  remaining={len(todo)}/{len(ids)}  elapsed={(time.time()-t0):.0f}s", flush=True)
                last_print = time.time()
        print(f"[poll] 全部完成，{(time.time()-t0):.0f}s", flush=True)

    async with async_session_maker() as s:
        rows = (await s.execute(text("""
            SELECT status, COUNT(*), ROUND(AVG(total_score),1)
            FROM training_records WHERE user_id=(SELECT id FROM users WHERE username=:u)
            GROUP BY status
        """), {"u": TARGET})).fetchall()
        print(f"\n[summary] {TARGET}:", flush=True)
        for row in rows:
            print(f"  {row[0]:<10}  count={row[1]:<3}  avg_score={row[2]}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
