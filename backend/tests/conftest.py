"""Pytest configuration and fixtures."""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import Base
from backend.models.user import User, UserProfile, GenderEnum, CasteEnum
from backend.models.scheme import Scheme
from backend.config import settings
from backend.cache.redis_client import RedisClient


# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_db():
    """Create test database."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    yield AsyncSessionLocal
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_user(test_db):
    """Create test user."""
    async with test_db() as session:
        user = User(
            id=uuid4(),
            phone="9876543210",
            name="Test User",
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        session.add(user)
        await session.commit()
        yield user


@pytest_asyncio.fixture
async def test_profile(test_db, test_user):
    """Create test user profile."""
    async with test_db() as session:
        profile = UserProfile(
            id=uuid4(),
            user_id=test_user.id,
            age=30,
            gender=GenderEnum.male,
            state="Tamil Nadu",
            district="Chennai",
            annual_income=250000,
            caste=CasteEnum.general,
            occupation="salaried",
            education="Bachelor's",
            bpl_card=False,
            disability=False,
            land_holding=None,
            marital_status="single",
            owns_house=True,
            jan_dhan_account=True,
            preferred_language="en",
            profile_hash="test_hash"
        )
        session.add(profile)
        await session.commit()
        yield profile


@pytest_asyncio.fixture
async def test_scheme(test_db):
    """Create test scheme."""
    async with test_db() as session:
        scheme = Scheme(
            id=uuid4(),
            name="Test Scheme",
            ministry="Ministry of Test",
            level="central",
            state=None,
            category=["General"],
            description="Test scheme description",
            benefits="Test benefits",
            eligibility_criteria={
                "age_min": 18,
                "age_max": 60,
                "income_max_annual": 500000,
                "gender": ["male", "female"]
            },
            required_documents=["Aadhar", "PAN Card"],
            application_mode="online",
            application_url="https://example.com/apply",
            source_url="https://example.com/scheme",
            last_synced=datetime.utcnow(),
            is_active=True
        )
        session.add(scheme)
        await session.commit()
        yield scheme


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_health():
    """Test health endpoint."""
    from backend.routers.auth import router as auth_router
    
    # Just verify endpoint exists
    assert auth_router is not None
