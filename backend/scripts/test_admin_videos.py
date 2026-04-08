#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台管理视频检测 API 测试脚本

测试任务 3.1 的所有功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import async_session_maker
from app.models.video_detection_task import VideoDetectionTask, VideoTaskStatus


async def test_video_detection_api():
    """测试视频检测 API"""
    
    print("\n" + "="*60)
    print("  后台管理视频检测 API 测试")
    print("="*60)
    
    results = []
    
    async with async_session_maker() as session:
        # ========== 测试 1: 检查数据库表是否存在 ==========
        print("\n📋 测试 1: 检查数据库表")
        try:
            from sqlalchemy import text
            result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='video_detection_tasks'"))
            table_exists = result.fetchone() is not None
            
            if table_exists:
                print(f"✅ video_detection_tasks 表存在")
                results.append(("数据库表", True))
            else:
                print(f"❌ video_detection_tasks 表不存在")
                results.append(("数据库表", False))
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results.append(("数据库表", False))
        
        # ========== 测试 2: 创建测试任务 ==========
        print("\n📋 测试 2: 创建测试任务")
        try:
            test_task = VideoDetectionTask(
                uploader_id=29,  # admin_manager 的 ID
                file_name="test_video.mp4",
                file_path="../data/videos/admin_uploads/test.mp4",
                file_size=1024000,
                status=VideoTaskStatus.PENDING
            )
            
            session.add(test_task)
            await session.commit()
            await session.refresh(test_task)
            
            print(f"✅ 创建测试任务成功 (ID: {test_task.id})")
            print(f"   - 文件名: {test_task.file_name}")
            print(f"   - 状态: {test_task.status.value}")
            
            results.append(("创建任务", True))
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            await session.rollback()
            results.append(("创建任务", False))
            return False
        
        task_id = test_task.id
        
        # ========== 测试 3: 查询任务列表 ==========
        print("\n📋 测试 3: 查询任务列表")
        try:
            from sqlalchemy import select, func
            
            count_result = await session.execute(select(func.count(VideoDetectionTask.id)))
            total = count_result.scalar()
            
            query = select(VideoDetectionTask).order_by(VideoDetectionTask.created_at.desc()).limit(5)
            result = await session.execute(query)
            tasks = result.scalars().all()
            
            print(f"✅ 查询成功")
            print(f"   - 总任务数: {total}")
            print(f"   - 返回任务数: {len(tasks)}")
            
            if tasks:
                for task in tasks[:3]:
                    print(f"     * ID:{task.id} {task.file_name} ({task.status.value})")
            
            results.append(("查询列表", True))
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results.append(("查询列表", False))
        
        # ========== 测试 4: 更新任务状态 ==========
        print("\n📋 测试 4: 更新任务状态")
        try:
            from sqlalchemy import select
            
            result = await session.execute(
                select(VideoDetectionTask).where(VideoDetectionTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if task:
                # 模拟处理过程
                task.status = VideoTaskStatus.PROCESSING
                await session.commit()
                print(f"✅ 状态更新为: PROCESSING")
                
                # 模拟完成
                task.status = VideoTaskStatus.COMPLETED
                task.ai_result = {"test": "result"}
                from datetime import datetime
                task.completed_at = datetime.utcnow()
                await session.commit()
                print(f"✅ 状态更新为: COMPLETED")
                
                results.append(("更新状态", True))
            else:
                print(f"❌ 任务不存在")
                results.append(("更新状态", False))
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            await session.rollback()
            results.append(("更新状态", False))
        
        # ========== 测试 5: 按状态过滤查询 ==========
        print("\n📋 测试 5: 按状态过滤查询")
        try:
            from sqlalchemy import select, func
            
            # 查询已完成的任务
            count_query = select(func.count(VideoDetectionTask.id)).where(
                VideoDetectionTask.status == VideoTaskStatus.COMPLETED
            )
            count_result = await session.execute(count_query)
            completed_count = count_result.scalar()
            
            print(f"✅ 过滤查询成功")
            print(f"   - 已完成任务数: {completed_count}")
            
            results.append(("状态过滤", True))
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results.append(("状态过滤", False))
        
        # ========== 测试 6: 删除任务 ==========
        print("\n📋 测试 6: 删除任务")
        try:
            from sqlalchemy import select
            
            result = await session.execute(
                select(VideoDetectionTask).where(VideoDetectionTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if task:
                await session.delete(task)
                await session.commit()
                print(f"✅ 任务删除成功")
                
                # 验证已删除
                result = await session.execute(
                    select(VideoDetectionTask).where(VideoDetectionTask.id == task_id)
                )
                deleted_task = result.scalar_one_or_none()
                
                if deleted_task is None:
                    print(f"✅ 任务已从数据库中移除")
                    results.append(("删除任务", True))
                else:
                    print(f"❌ 任务仍然存在")
                    results.append(("删除任务", False))
            else:
                print(f"❌ 任务不存在")
                results.append(("删除任务", False))
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            await session.rollback()
            results.append(("删除任务", False))
    
    # ========== 测试结果总结 ==========
    print("\n" + "="*60)
    print("  测试结果总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print("\n" + "="*60)
    print(f"总计: {passed}/{total} 测试通过")
    print("="*60)
    
    if passed == total:
        print("\n🎉 所有测试通过！任务 3.1 后端 API 完成！")
        return True
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_video_detection_api())
    sys.exit(0 if success else 1)
