import asyncio
import os
import sys
from pathlib import Path

# CRITICAL: Prevent HuggingFace model downloads during tests (MUST be before any imports)
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Windows: Use SelectorEventLoop BEFORE any test collection
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# CRITICAL: Set TESTING=true at MODULE LEVEL before ANY imports
# This is the absolute earliest point - before pytest, before any test collection
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ["REDIS_URL"] = os.getenv("TEST_REDIS_URL", "redis://localhost:6380/1")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-32-chars"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-32-chars"
os.environ["ALLOWED_ORIGINS"] = '["http://localhost:3000"]'
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["OPENAI_API_KEY"] = "test-key"

# Backend dizinini path'e ilk olarak ekle (pytest collection'dan önce)
_backend_dir = str(Path(__file__).parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import pytest


def pytest_configure(config):
    """
    Pytest configuration hook.

    Note: Environment variables are already set at module level above.
    This hook is kept for future configuration needs.
    """
    print("[OK] TESTING environment configured at module level")


@pytest.fixture(scope="module")
def test_app():
    """
    Create a minimal FastAPI app for smoke tests.

    This avoids importing main.py which triggers full router loading.
    Instead, we create a minimal app with only health endpoints.
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(
        title="KIRO2 Test App",
        version="1.0.0-test",
        description="Minimal app for smoke tests",
    )

    # Add basic CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add health endpoints (minimal, no database required)
    @app.get("/health")
    async def health():
        return {
            "health_status": "healthy",
            "response_time_ms": 1.0,
        }

    @app.get("/health/ready")
    async def ready():
        return {"status": "ready"}

    @app.get("/health/live")
    async def live():
        return {"status": "alive"}

    @app.get("/health/startup")
    async def startup():
        return {"status": "started"}

    @app.get("/health/database")
    async def database():
        return {"status": "healthy", "database": {"connected": False}}

    @app.get("/health/detailed")
    async def detailed():
        return {"status": "healthy", "components": []}

    return app


from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine

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
    # SQLite doesn't support pool_size/max_overflow - only use for PostgreSQL
    if "sqlite" in TEST_DATABASE_URL.lower():
        engine = create_async_engine(
            TEST_DATABASE_URL, echo=False
        )
    else:
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

    Note: Environment variables are now set at module level (before imports)
    to prevent database connection attempts during pytest collection.
    This fixture is kept for backward compatibility but is now mostly a no-op.
    """
    # Environment already set at module level
    yield
    # Cleanup after all tests
    # (optional - usually not needed as process ends)
