"""数据库初始化脚本"""
import asyncio
from app.db.base import Base, engine
from app.models import User, TrainingRecord, ActionLog, TrainingStatistics


async def init_db():
    """初始化数据库，创建所有表"""
    print("正在初始化数据库...")
    
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ 数据库表创建成功！")
    print("\n已创建的表:")
    print("- users (用户表)")
    print("- training_records (训练记录表)")
    print("- action_logs (动作日志表)")
    print("- training_statistics (统计表)")


if __name__ == "__main__":
    asyncio.run(init_db())
