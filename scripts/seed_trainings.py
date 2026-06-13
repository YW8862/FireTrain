#!/usr/bin/env python3
"""批量创建学生用户 + 管理员代上传视频（异步 AI 分析）。"""
import asyncio, os, random, sys, time
from pathlib import Path

# 必须先切到 backend 目录再 import app（避免 DATABASE_URL 相对路径落到错位置）
os.chdir("/home/yw/FireTrain/backend")
sys.path.insert(0, "/home/yw/FireTrain/backend")

import httpx

API = "http://localhost:8000"
VIDEOS = sorted(Path("/home/yw/FireTrain/data/videos/admin_uploads").glob("*.mp4"))
STUDENTS = [f"student{i}" for i in range(1, 5)]
PWD = "student123"


async def login(c, u, p):
    r = await c.post(f"{API}/api/user/login", data={"username": u, "password": p}, timeout=10)
    r.raise_for_status()
    return r.json()["token"]


async def main():
    random.seed(7)

    # 1) create students via direct DB
    sys.path.insert(0, "/home/yw/FireTrain/backend")
    from app.db.session import async_session_maker
    from app.models.user import User
    from app.services.user_service import get_password_hash

    from sqlalchemy import select, delete
    async with async_session_maker() as s:
        # 清理掉之前测试用的
        await s.execute(delete(User).where(User.username.in_(["_test_upload_"])))
        for i, u in enumerate(STUDENTS, 1):
            existing = (await s.execute(select(User).where(User.username == u))).scalar_one_or_none()
            if existing:
                continue
            s.add(User(username=u, email=f"{u}@firetrain.cn", phone=f"139000000{i:02d}",
                       password_hash=get_password_hash(PWD), role="student", is_active=True))
        await s.commit()
    print(f"[seed] {len(STUDENTS)} students ready: {STUDENTS}  (pwd: {PWD})")

    # 2) login as admin
    async with httpx.AsyncClient() as c:
        admin_token = await login(c, "admin", "admin123")
        admin_h = {"Authorization": f"Bearer {admin_token}"}

        # 3) fire uploads
        plan = []
        for u in STUDENTS:
            chosen = random.sample(VIDEOS, 4)
            for v in chosen:
                plan.append((u, v))
        print(f"[upload] firing {len(plan)} uploads ...")
        t0 = time.time()

        async def do_upload(username, video_path):
            with open(video_path, "rb") as f:
                files = {"file": (video_path.name, f, "video/mp4")}
                data = {"username": username, "training_type": "fire_extinguisher"}
                r = await c.post(f"{API}/api/admin/video/upload",
                                 headers=admin_h, files=files, data=data, timeout=30)
                r.raise_for_status()
                return username, r.json()["training_id"]

        results = await asyncio.gather(*[do_upload(u, v) for u, v in plan], return_exceptions=True)
        ids = []
        for r in results:
            if isinstance(r, Exception):
                print(f"  ERR: {r}")
            else:
                u, tid = r
                ids.append((u, tid))
        print(f"[upload] kicked off {len(ids)}/{len(plan)} in {time.time()-t0:.1f}s")

        # 4) poll all
        print(f"[poll] waiting for AI analysis ...")
        todo = dict(ids)
        last_print = 0
        while todo:
            await asyncio.sleep(8)
            done = []
            for tid in list(todo.keys()):
                r = await c.get(f"{API}/api/admin/video/status/{tid}", headers=admin_h, timeout=10)
                d = r.json()
                if d["status"] in ("done", "failed"):
                    done.append((tid, todo[tid], d["status"], d.get("total_score")))
            for tid, u, st, sc in done:
                del todo[tid]
            if time.time() - last_print > 15:
                print(f"  remaining={len(todo)}/{len(ids)}  done={sum(1 for x in done if x[2]=='done')}  failed={sum(1 for x in done if x[2]=='failed')}")
                last_print = time.time()
        print(f"[poll] all {len(ids)} finished in {time.time()-t0:.1f}s")

    # 5) summary
    from sqlalchemy import text
    async with async_session_maker() as s:
        r = await s.execute(text("SELECT user_id, COUNT(*), ROUND(AVG(total_score),1) "
                                 "FROM training_records WHERE status='done' "
                                 "GROUP BY user_id ORDER BY user_id"))
        print("\n[summary] done records per user:")
        for row in r:
            uid, cnt, avg = row
            u = (await s.execute(text("SELECT username FROM users WHERE id=:i"), {"i": uid})).scalar()
            print(f"  {u:<10} id={uid}  count={cnt}  avg_score={avg}")


if __name__ == "__main__":
    asyncio.run(main())
