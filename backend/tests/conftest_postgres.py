"""
PostgreSQL Test Fixtures and Database Session Management
Provides comprehensive database fixtures for integration testing
"""
import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

# Import database models to ensure they're registered
from models.database import Base

# Test database configuration
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+asyncpg://testuser:test123@localhost:5433/testdb"
)


# ============================================================================
# Database Engine Fixtures
# ============================================================================

# Note: event_loop fixture removed - pytest-asyncio auto mode handles this
# Duplicate fixtures cause conflicts with pytest-asyncio>=0.21


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create a test database engine for the entire test session.
    Uses NullPool to avoid connection pooling issues in tests.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,  # Set to True for SQL debugging
        poolclass=NullPool,  # No connection pooling for tests
        future=True,
    )

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def setup_database(test_engine: AsyncEngine) -> None:
    """
    Setup database tables once per test session.
    Creates all tables defined in Base.metadata.
    """
    async with test_engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Teardown: drop all tables after session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ============================================================================
# Database Session Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def db_session(
    test_engine: AsyncEngine, setup_database: None
) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a new database session for each test.
    Automatically rolls back changes after each test for isolation.

    Usage:
        async def test_something(db_session):
            user = User(email="test@example.com")
            db_session.add(user)
            await db_session.commit()
    """
    # Create a connection
    async with test_engine.connect() as connection:
        # Start a transaction
        async with connection.begin() as transaction:
            # Create session bound to the transaction
            async_session_factory = async_sessionmaker(
                bind=connection,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            session = async_session_factory()

            yield session

            # Rollback transaction after test
            await session.close()
            await transaction.rollback()


@pytest_asyncio.fixture
async def db_session_autocommit(
    test_engine: AsyncEngine, setup_database: None
) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session that auto-commits changes.
    Use this for tests that need to verify committed data.

    WARNING: Changes are NOT automatically rolled back!
    Use with caution or implement manual cleanup.
    """
    async_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        yield session


# ============================================================================
# Data Cleanup Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def clean_database(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a clean database by truncating all tables before the test.
    Useful for tests that need a completely fresh database state.
    """
    # Get all table names
    async with db_session.begin():
        result = await db_session.execute(
            text(
                """
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename != 'alembic_version'
            """
            )
        )
        tables = [row[0] for row in result]

        # Truncate all tables
        if tables:
            await db_session.execute(
                text(f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE")
            )
        await db_session.commit()

    yield db_session


# ============================================================================
# Factory Fixtures for Creating Test Data
# ============================================================================


@pytest.fixture
def user_factory(db_session: AsyncSession):
    """
    Factory for creating test users.

    Usage:
        async def test_user(user_factory):
            user = await user_factory(
                email="test@example.com",
                username="testuser"
            )
    """
    from models.database import User
    from datetime import datetime, timezone
    import uuid

    async def _create_user(
        email: str = None,
        username: str = None,
        password_hash: str = "hashed_password_123",
        first_name: str = "Test",
        last_name: str = "User",
        role: str = "STUDENT",
        is_active: bool = True,
        is_verified: bool = True,
        **kwargs,
    ) -> User:
        if email is None:
            email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        if username is None:
            username = f"user_{uuid.uuid4().hex[:8]}"

        user = User(
            id=str(uuid.uuid4()),
            email=email,
            username=username,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=is_active,
            is_verified=is_verified,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            **kwargs,
        )

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        return user

    return _create_user


@pytest.fixture
def student_profile_factory(db_session: AsyncSession, user_factory):
    """
    Factory for creating test student profiles.

    Usage:
        async def test_student(student_profile_factory):
            profile = await student_profile_factory()
    """
    from models.database import StudentProfile
    import uuid
    from datetime import datetime

    async def _create_student_profile(
        user=None, grade_level: int = 9, target_exam: str = "TYT", **kwargs
    ):
        if user is None:
            user = await user_factory(role="STUDENT")

        profile = StudentProfile(
            id=str(uuid.uuid4()),
            user_id=user.id,
            grade_level=grade_level,
            target_exam=target_exam,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            **kwargs,
        )

        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        return profile

    return _create_student_profile


@pytest.fixture
def question_factory(db_session: AsyncSession):
    """
    Factory for creating test questions.
    """
    from models.database import Question
    import uuid
    from datetime import datetime

    async def _create_question(
        question_text: str = "Test question?",
        subject_area: str = "MATEMATIK",
        difficulty: str = "MEDIUM",
        correct_answer: str = "A",
        **kwargs,
    ):
        question = Question(
            id=str(uuid.uuid4()),
            question_text=question_text,
            option_a="Option A",
            option_b="Option B",
            option_c="Option C",
            option_d="Option D",
            correct_answer=correct_answer,
            exam_type="TYT",
            subject_area=subject_area,
            topic="Test Topic",
            difficulty=difficulty,
            irt_difficulty=0.5,
            irt_discrimination=1.0,
            irt_guessing=0.25,
            morphology_complexity=0.5,
            readability_score=0.7,
            times_asked=0,
            times_correct=0,
            average_response_time=0.0,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            **kwargs,
        )

        db_session.add(question)
        await db_session.commit()
        await db_session.refresh(question)

        return question

    return _create_question


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def sample_user(user_factory):
    """Pre-created sample user for tests."""
    return await user_factory(email="sample@example.com", username="sampleuser")


@pytest_asyncio.fixture
async def sample_student(student_profile_factory):
    """Pre-created sample student profile for tests."""
    return await student_profile_factory()


@pytest_asyncio.fixture
async def sample_questions(question_factory):
    """Pre-created sample questions for tests."""
    questions = []
    for i in range(5):
        q = await question_factory(
            question_text=f"Test question {i+1}?",
            subject_area="MATEMATIK",
            difficulty=["EASY", "MEDIUM", "HARD"][i % 3],
        )
        questions.append(q)
    return questions


# ============================================================================
# Mock Fixtures (for non-database tests)
# ============================================================================


@pytest.fixture
def mock_db_session():
    """Mock database session for unit tests that don't need real DB."""
    from unittest.mock import AsyncMock

    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_user():
    """Mock user object for unit tests."""
    from unittest.mock import MagicMock

    user = MagicMock()
    user.id = "test_user_123"
    user.email = "mock@example.com"
    user.username = "mockuser"
    user.role = "STUDENT"
    user.is_active = True
    user.is_verified = True
    return user


# ============================================================================
# Integration Test Markers
# ============================================================================


def pytest_configure(config):
    """Register custom markers for integration tests."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires database)"
    )
    config.addinivalue_line(
        "markers", "fast: mark test as fast unit test (no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow test (may take >10 seconds)"
    )
