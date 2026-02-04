import pytest
import asyncio
from typing import AsyncGenerator, Generator
import os
import sys
from pathlib import Path

# Backend dizinini path'e ekle
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from models_unified import Base

# Test database URL - MUST be set via environment variable (security requirement)
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
SYNC_DATABASE_URL = os.getenv("SYNC_TEST_DATABASE_URL")

# Validate that required test database URLs are set
if not TEST_DATABASE_URL:
    # Use in-memory SQLite as fallback for fast tests
    TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    print("WARNING: TEST_DATABASE_URL not set, using in-memory SQLite")

if not SYNC_DATABASE_URL:
    SYNC_DATABASE_URL = "sqlite:///:memory:"
    print("WARNING: SYNC_TEST_DATABASE_URL not set, using in-memory SQLite")

# Note: event_loop fixture removed - pytest-asyncio handles this automatically


# Session-scoped engine for performance
@pytest.fixture(scope="session")
async def test_async_engine():
    """Create async engine once per test session (PERFORMANCE FIX)"""
    engine = create_async_engine(
        TEST_DATABASE_URL, echo=False, pool_pre_ping=True, pool_size=5, max_overflow=10
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def async_db_session(test_async_engine):
    """Create async database session for tests (OPTIMIZED)"""
    # Use session-scoped engine (not creating new engine each time)
    async_session_maker = async_sessionmaker(
        test_async_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Session with transaction rollback
    async with async_session_maker() as session:
        async with session.begin():
            yield session
            await session.rollback()  # Test sonrasi rollback


@pytest.fixture(scope="function")
def sync_db_session():
    """Create sync database session for tests"""
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(SYNC_DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    session = SessionLocal()
    try:
        yield session
        session.rollback()  # Test sonrasi rollback
    finally:
        session.close()

    engine.dispose()


@pytest.fixture(scope="session")
def setup_test_env_once():
    """
    Setup test environment variables ONCE per session.
    Note: Not autouse - tests must explicitly request this fixture if needed.
    """
    # Set environment variables once, not for every test
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["REDIS_URL"] = os.getenv("TEST_REDIS_URL", "redis://localhost:6380/1")
    os.environ["JWT_SECRET_KEY"] = os.getenv(
        "TEST_JWT_SECRET", "test-secret-key-for-testing-only-32-chars"
    )
    os.environ["ALLOWED_ORIGINS"] = '["http://localhost:3000"]'
    os.environ["SECRET_KEY"] = os.getenv(
        "TEST_SECRET_KEY", "test-secret-key-for-testing-only-32-chars"
    )
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    os.environ["OPENAI_API_KEY"] = "test-key"
    yield
    # Cleanup after all tests
    # (optional - usually not needed as process ends)
