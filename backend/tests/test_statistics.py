"""测试统计模块"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.session import engine, get_db
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
import asyncio

from app.services.statistics_service import StatisticsService
from app.models.training_record import TrainingRecord
from app.models.user import User


client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """测试前创建数据库表"""
    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    asyncio.run(_setup())
    yield
    # 测试后清理数据库
    asyncio.run(engine.dispose())


@pytest.fixture
def db_session():
    """创建异步数据库会话"""
    from app.db.session import async_session_maker
    
    async def override_get_db():
        async with async_session_maker() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async def get_session():
        async with async_session_maker() as session:
            return session
    
    session = asyncio.run(get_session())
    
    yield session
    
    app.dependency_overrides.clear()


class TestStatisticsService:
    """测试 StatisticsService"""
    
    @pytest.fixture
    async def setup_test_data(self, db_session):
        """准备测试数据"""
        session = db_session
        
        # 创建测试用户
        user = User(
            username="test_stats_user",
            email="stats@test.com",
            password_hash="hashed_password"
        )
        session.add(user)
        await session.flush()
        
        # 创建多条训练记录
        base_date = datetime.utcnow() - timedelta(days=10)
        
        for i in range(10):
            record = TrainingRecord(
                user_id=user.id,
                training_type="fire_extinguisher",
                status="done" if i % 2 == 0 else "completed",
                total_score=Decimal(f"{70 + i * 2}"),  # 70, 72, 74, ..., 88
                step_scores={
                    "step1": {
                        "step_name": "提灭火器",
                        "score": float(75 + i),
                        "is_correct": True
                    },
                    "step2": {
                        "step_name": "拔保险销",
                        "score": float(80 + i),
                        "is_correct": True
                    },
                    "step3": {
                        "step_name": "瞄准火源",
                        "score": float(65 + i),
                        "is_correct": i % 2 == 0
                    }
                },
                duration_seconds=Decimal("120.5"),
                created_at=base_date + timedelta(days=i),
                completed_at=base_date + timedelta(days=i) + timedelta(minutes=5)
            )
            session.add(record)
        
        await session.commit()
        
        yield user
        
        # 清理数据
        await session.rollback()
    
    async def test_get_personal_statistics(self, db_session, setup_test_data):
        """测试获取个人统计数据"""
        user = setup_test_data
        stats_service = StatisticsService(db_session)
        
        stats = await stats_service.get_personal_statistics(user.id)
        
        assert stats is not None
        assert stats.user_id == user.id
        assert stats.total_trainings == 10
        assert stats.completed_trainings == 10  # done 和 completed 都计算
        assert stats.average_score > 0
        assert stats.best_score > stats.average_score
    
    async def test_get_training_trend(self, db_session, setup_test_data):
        """测试获取训练趋势"""
        user = setup_test_data
        stats_service = StatisticsService(db_session)
        
        # 查询最近 7 天
        trend = await stats_service.get_training_trend(user.id, days=7)
        
        assert len(trend) > 0
        assert all(item.date is not None for item in trend)
        assert all(item.training_count >= 0 for item in trend)
        assert all(item.average_score >= 0 for item in trend)
    
    async def test_get_step_analysis(self, db_session, setup_test_data):
        """测试获取步骤分析"""
        user = setup_test_data
        stats_service = StatisticsService(db_session)
        
        analysis = await stats_service.get_step_analysis(user.id)
        
        assert len(analysis) > 0
        assert all(item.step_name is not None for item in analysis)
        assert all(item.average_score >= 0 for item in analysis)
        assert all(item.success_rate >= 0 and item.success_rate <= 100 for item in analysis)
        
        # 检查是否按分数排序（从低到高）
        scores = [float(item.average_score) for item in analysis]
        assert scores == sorted(scores)
    
    async def test_refresh_statistics(self, db_session, setup_test_data):
        """测试刷新统计数据"""
        user = setup_test_data
        stats_service = StatisticsService(db_session)
        
        # 刷新统计
        statistics = await stats_service.refresh_statistics(user.id)
        
        assert statistics is not None
        assert statistics.user_id == user.id
        assert statistics.total_trainings == 10
        assert statistics.average_score > 0
    
    async def test_get_personal_statistics_no_data(self, db_session):
        """测试无数据时的个人统计"""
        # 创建一个没有训练记录的用户
        user = User(
            username="test_no_data_user",
            email="nodata@test.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        await db_session.commit()
        
        stats_service = StatisticsService(db_session)
        stats = await stats_service.get_personal_statistics(user.id)
        
        assert stats is None
        
        # 清理
        await db_session.rollback()


class TestStatisticsAPI:
    """测试统计 API 接口"""
    
    async def test_get_personal_statistics_api(self, db_session, setup_test_data):
        """测试个人统计 API"""
        user = setup_test_data
        
        response = client.get("/api/stats/personal")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user.id
        assert data["total_trainings"] > 0
    
    async def test_get_training_trend_api(self, client):
        """测试训练趋势 API"""
        response = client.get("/api/stats/trend?days=7")
        
        # 即使没有数据也应该返回成功（空列表）
        assert response.status_code == 200
        data = response.json()
        assert "trend_data" in data
        assert "total_days" in data
    
    async def test_get_step_analysis_api(self, client):
        """测试步骤分析 API"""
        response = client.get("/api/stats/step-analysis")
        
        assert response.status_code == 200
        data = response.json()
        assert "step_analysis" in data
    
    async def test_get_statistics_overview_api(self, client):
        """测试统计概览 API"""
        response = client.get("/api/stats/overview?days=7")
        
        assert response.status_code == 200
        data = response.json()
        assert "personal_stats" in data
        assert "recent_trend" in data
        assert "step_analysis" in data
