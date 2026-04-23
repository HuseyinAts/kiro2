"""
Test database configuration and isolation
"""
import os
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

# Test database configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SYNC_DATABASE_URL = "sqlite:///test.db"


class TestDatabase:
    """Test database manager with proper isolation"""

    def __init__(self):
        self.async_engine = None
        self.sync_engine = None
        self.async_session_factory = None
        self.sync_session_factory = None
        self._initialized = False

    async def initialize(self):
        """Initialize test database"""
        if self._initialized:
            return

        # Create async engine
        self.async_engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
            future=True,
            poolclass=None,  # Disable pooling for tests
        )

        # Create sync engine for schema creation
        self.sync_engine = create_engine(TEST_SYNC_DATABASE_URL, echo=False)

        # Create session factories
        self.async_session_factory = async_sessionmaker(
            self.async_engine, class_=AsyncSession, expire_on_commit=False
        )

        self.sync_session_factory = sessionmaker(
            self.sync_engine, expire_on_commit=False
        )

        self._initialized = True

    async def create_tables(self):
        """Create tables with proper isolation"""
        try:
            # Import Base in an isolated way
            from core.database import Base

            # Clear metadata to prevent conflicts
            Base.metadata.clear()

            # Create tables
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        except Exception as e:
            # If import fails, use mock base
            print(f"Warning: Could not create tables: {e}")

    async def drop_tables(self):
        """Drop all tables"""
        try:
            from core.database import Base

            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

        except Exception:
            pass

    async def get_session(self) -> AsyncSession:
        """Get test database session"""
        if not self._initialized:
            await self.initialize()

        return self.async_session_factory()

    async def cleanup(self):
        """Cleanup test database"""
        if self.async_engine:
            await self.async_engine.dispose()
        if self.sync_engine:
            self.sync_engine.dispose()

        # Remove test db file
        if os.path.exists("test.db"):
            try:
                os.remove("test.db")
            except Exception:
                pass


# Global test database instance
test_db = TestDatabase()


@pytest.fixture(scope="session")
async def test_database():
    """Session-scoped test database fixture"""
    await test_db.initialize()
    yield test_db
    await test_db.cleanup()


@pytest.fixture(scope="function")
async def db_session(test_database):
    """Function-scoped database session fixture"""
    session = await test_database.get_session()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture(scope="function")
async def clean_db(test_database):
    """Clean database for each test"""
    # Create tables
    await test_database.create_tables()
    yield
    # Drop tables after test
    await test_database.drop_tables()


def patch_database_imports():
    """Patch database imports to prevent conflicts"""

    def mock_get_session():
        """Mock session factory"""

        async def _get_session():
            session = await test_db.get_session()
            try:
                yield session
            finally:
                await session.close()

        return _get_session()

    return patch("core.database.get_session", side_effect=mock_get_session)


# Environment setup for tests
def setup_test_environment():
    """Setup test environment variables"""
    os.environ.update(
        {
            "DATABASE_URL": TEST_DATABASE_URL,
            "USE_TEST_DB": "true",
            "TESTING": "true",
            "USE_MOCK_RESPONSES": "true",
            "SQLALCHEMY_WARN_20": "false",  # Suppress SQLAlchemy warnings
        }
    )
