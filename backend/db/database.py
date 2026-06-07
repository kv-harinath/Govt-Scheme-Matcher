"""
Async SQLAlchemy database configuration and session management.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from backend.config import settings


# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=False,
    poolclass=NullPool,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session for dependency injection.
    
    Yields:
        AsyncSession: An async database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions.
    
    Yields:
        AsyncSession: An async database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database and create tables."""
    async with engine.begin() as conn:
        from backend.models import Base
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
