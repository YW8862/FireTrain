#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加角色切换相关字段

使用方法:
    python backend/scripts/migrate_add_role_fields.py
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import engine


async def migrate():
    """执行数据库迁移"""
    
    async with engine.connect() as conn:
        # 开始事务
        async with conn.begin():
            try:
                print("开始执行数据库迁移...")
                
                # 添加 can_switch_role 字段
                await conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN can_switch_role BOOLEAN DEFAULT FALSE
                """))
                print("✓ 添加 can_switch_role 字段成功")
                
                # 添加 original_role 字段
                await conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN original_role VARCHAR(20) NULL
                """))
                print("✓ 添加 original_role 字段成功")
                
                # 更新现有管理员，允许角色切换
                await conn.execute(text("""
                    UPDATE users 
                    SET can_switch_role = TRUE 
                    WHERE role = 'admin'
                """))
                print("✓ 更新现有管理员角色切换权限成功")
                
                print("\n✅ 数据库迁移完成！")
                print("\n迁移详情:")
                print("- users 表新增 can_switch_role 字段 (BOOLEAN)")
                print("- users 表新增 original_role 字段 (VARCHAR(20))")
                print("- 所有 admin 角色的用户 can_switch_role 设置为 TRUE")
                
            except Exception as e:
                print(f"\n❌ 迁移失败：{e}")
                raise


if __name__ == "__main__":
    asyncio.run(migrate())
