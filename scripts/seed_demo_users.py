#!/usr/bin/env python3
"""一次性补齐演示用户：
- 把 admin 的 role 从 'user' 修成 'admin'
- 创建 yangwei1（student / yangwei2003!）
- 创建 root（root / root123）
- 创建 admin1~3（admin / admin123）
- 创建 student5~14（student / student123）

幂等：用户名已存在则跳过；admin role 已经是 admin 则跳过。
"""
import os
import sys
import asyncio
from pathlib import Path

# 必须先切到 backend 再 import app，避免 DATABASE_URL 相对路径走偏
os.chdir("/home/yw/FireTrain/backend")
sys.path.insert(0, "/home/yw/FireTrain/backend")

from sqlalchemy import select, update

from app.db.session import async_session_maker
from app.models.user import User
from app.services.user_service import get_password_hash


DEMO_USERS = [
    # (username, password, role, email, phone)
    ("yangwei1", "yangwei2003!", "student", "yangwei1@firetrain.cn", "13900001001"),
    ("root",     "root123",      "root",    "root@firetrain.cn",     "13900001000"),
    ("admin1",   "admin123",     "admin",   "admin1@firetrain.cn",   "13900002001"),
    ("admin2",   "admin123",     "admin",   "admin2@firetrain.cn",   "13900002002"),
    ("admin3",   "admin123",     "admin",   "admin3@firetrain.cn",   "13900002003"),
] + [
    (f"student{i}", "student123", "student", f"student{i}@firetrain.cn", f"139000030{i:02d}")
    for i in range(5, 15)
]


async def main(dry_run: bool = False):
    async with async_session_maker() as s:
        # 1) admin role 修正
        admin = (await s.execute(select(User).where(User.username == "admin"))).scalar_one_or_none()
        if admin is None:
            print("[skip] admin 不存在，跳过 role 修正")
        elif admin.role == "admin":
            print(f"[skip] admin.role 已是 admin，跳过")
        else:
            print(f"[plan] UPDATE admin.role: {admin.role!r} -> 'admin'")
            if not dry_run:
                admin.role = "admin"

        # 2) 批量插入
        for username, password, role, email, phone in DEMO_USERS:
            existing = (await s.execute(select(User).where(User.username == username))).scalar_one_or_none()
            if existing:
                print(f"[skip] {username} 已存在 (id={existing.id}, role={existing.role})")
                continue
            print(f"[plan] INSERT {username:<12s} role={role:<8s} email={email}")
            if not dry_run:
                s.add(User(
                    username=username,
                    email=email,
                    phone=phone,
                    password_hash=get_password_hash(password),
                    role=role,
                    is_active=True,
                ))

        if dry_run:
            print("\n[DRY-RUN] 未提交")
            await s.rollback()
        else:
            await s.commit()
            print("\n[OK] 已提交")

        # 3) 汇总
        print("\n--- 当前用户清单（按 role 分组）---")
        from sqlalchemy import func
        rows = (await s.execute(
            select(User.role, func.count(User.id)).group_by(User.role).order_by(User.role)
        )).all()
        for role, cnt in rows:
            print(f"  {role:<10s} count={cnt}")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    asyncio.run(main(dry_run=dry))
