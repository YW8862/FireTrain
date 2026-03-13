#!/usr/bin/env python3
"""
测试清理服务

用于验证实时清理未开始训练记录的功能
"""
import asyncio
from datetime import datetime, timedelta
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, insert
from app.models.training_record import TrainingRecord


async def test_cleanup():
    """测试清理功能"""
    print("=" * 60)
    print("🧪 测试定时清理功能")
    print("=" * 60)
    
    # 数据库 URL（根据实际情况修改）
    DATABASE_URL = "sqlite+aiosqlite:///./fire_training.db"
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        # 1. 创建一些测试数据
        print("\n📝 步骤 1: 创建测试数据...")
        async with async_session() as session:
            # 创建一条超时的未开始记录（60 分钟前）
            old_time = datetime.utcnow() - timedelta(minutes=60)
            new_time = datetime.utcnow() - timedelta(minutes=5)
            
            test_records = [
                {
                    'user_id': 1,
                    'training_type': 'fire_extinguisher',
                    'status': 'created',  # 未开始状态
                    'total_score': None,
                    'step_scores': None,
                    'video_path': None,
                    'duration_seconds': 60,
                    'started_at': None,
                    'completed_at': None,
                    'feedback': None,
                    'created_at': old_time
                },
                {
                    'user_id': 1,
                    'training_type': 'fire_extinguisher',
                    'status': 'created',  # 未开始状态
                    'total_score': None,
                    'step_scores': None,
                    'video_path': None,
                    'duration_seconds': 60,
                    'started_at': None,
                    'completed_at': None,
                    'feedback': None,
                    'created_at': new_time  # 5 分钟前，不应该被删除
                }
            ]
            
            for record in test_records:
                stmt = insert(TrainingRecord).values(record)
                await session.execute(stmt)
            
            await session.commit()
            print(f"✅ 已创建 2 条测试记录（1 条 60 分钟前，1 条 5 分钟前）")
        
        # 2. 查询当前记录数量
        print("\n🔍 步骤 2: 查询当前记录...")
        async with async_session() as session:
            result = await session.execute(
                select(TrainingRecord).where(TrainingRecord.status == 'created')
            )
            records = result.scalars().all()
            print(f"📊 当前未开始的记录数量：{len(records)}")
            for record in records:
                age_minutes = (datetime.utcnow() - record.created_at).total_seconds() / 60
                print(f"   - ID: {record.id}, 创建时间：{record.created_at}, {age_minutes:.1f} 分钟前")
        
        # 3. 执行清理
        print("\n🧹 步骤 3: 执行清理任务...")
        from app.services.cleanup_service import cleanup_unstarted_trainings
        
        async for db in get_db():
            cutoff_time = datetime.utcnow() - timedelta(minutes=30)
            
            query = (
                delete(TrainingRecord)
                .where(TrainingRecord.status == 'created')
                .where(TrainingRecord.created_at < cutoff_time)
            )
            
            result = await db.execute(query)
            deleted_count = result.rowcount
            
            await db.commit()
            break
        
        print(f"✅ 已删除 {deleted_count} 条超时记录")
        
        # 4. 验证清理结果
        print("\n✅ 步骤 4: 验证清理结果...")
        async with async_session() as session:
            result = await session.execute(
                select(TrainingRecord).where(TrainingRecord.status == 'created')
            )
            records = result.scalars().all()
            print(f"📊 清理后剩余的未开始记录数量：{len(records)}")
            
            if len(records) == 1:
                print("✅ 清理成功！只剩下一条 5 分钟前的记录")
                for record in records:
                    age_minutes = (datetime.utcnow() - record.created_at).total_seconds() / 60
                    print(f"   - ID: {record.id}, 创建时间：{record.created_at}, {age_minutes:.1f} 分钟前")
            else:
                print("❌ 清理失败！预期剩余 1 条记录")
                
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await engine.dispose()
    
    print("\n" + "=" * 60)
    print("✨ 测试完成")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_cleanup())
    sys.exit(0 if success else 1)
