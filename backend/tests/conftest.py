"""
Pytest configuration and fixtures for testing
"""
import asyncio
import os
import sys

# Generator import removed - not used in this file
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add backend directory to Python path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
# Also add parent directory
sys.path.insert(0, os.path.dirname(backend_dir))

from httpx import AsyncClient

try:
    from tests.test_client_helper import create_test_client
except ImportError:
    try:
        from tests.integration.test_client_helper import create_test_client
    except ImportError:
        # Fallback mock implementation
        def create_test_client(app):
            from fastapi.testclient import TestClient

            return TestClient(app)


# Load test environment variables
from dotenv import load_dotenv

test_env_path = os.path.join(os.path.dirname(__file__), "..", ".env.test")
if os.path.exists(test_env_path):
    load_dotenv(test_env_path)

# Set test environment variables
os.environ["USE_MOCK_RESPONSES"] = "true"
os.environ["USE_TEST_DB"] = "true"
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "testing"
os.environ["HF_ENDPOINT_URL"] = "https://test.endpoint.com"
os.environ["HF_API_KEY"] = "test_key"
os.environ["LLM_TIMEOUT"] = "5"
os.environ["MAX_RETRIES"] = "2"

# FIX: Config validation for allowed_origins (fixes 46 collection errors)
# CRITICAL: ServerConfig uses env_prefix="SERVER_" so we need SERVER_ALLOWED_ORIGINS
import json

os.environ["SERVER_ALLOWED_ORIGINS"] = json.dumps(
    ["http://localhost:3000", "http://localhost:5173"]
)
os.environ[
    "CORS_ALLOWED_ORIGINS"
] = "http://localhost:3000,http://localhost:5173,http://localhost:8080"

# FIX: Security keys for testing
if "SECRET_KEY" not in os.environ:
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-min-32-chars-long"
if "JWT_SECRET_KEY" not in os.environ:
    os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-only-32-chars"

# FIX: Disable CSRF for tests (unless explicitly testing CSRF)
os.environ["ENABLE_CSRF"] = os.getenv("TEST_CSRF", "false")

# FIX: Use redis-py instead of deprecated aioredis
# redis-py 5.0+ has built-in async support and fixes Python 3.11+ compatibility
# If your code still imports aioredis, update to: from redis import asyncio as aioredis
# For tests, we disable Redis entirely
os.environ["ENABLE_REDIS"] = "false"
os.environ["REDIS_ENABLED"] = "false"

# Database URL - use PostgreSQL for integration tests, SQLite for fast tests
if os.getenv("USE_POSTGRES_TESTS", "false").lower() == "true":
    os.environ["DATABASE_URL"] = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://testuser:test123@localhost:5433/testdb",
    )
else:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

os.environ["SQLALCHEMY_WARN_20"] = "false"  # Suppress SQLAlchemy warnings

# Import test database setup
try:
    from tests.fixtures.test_database import setup_test_environment

    setup_test_environment()
except ImportError:
    pass  # test_database module is optional


# Note: event_loop fixture removed - pytest-asyncio 0.21+ handles this automatically
# Duplicate fixture from root conftest.py has been removed to avoid conflicts


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app"""
    from main import app

    client = create_test_client(app)
    yield client
    client.close()


@pytest.fixture
async def async_client():
    """Create an async test client for the FastAPI app"""
    from main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient for LLM requests"""
    with patch("agents.httpx.AsyncClient") as mock:
        mock_instance = MagicMock()
        mock_instance.post = AsyncMock()
        mock_instance.aclose = AsyncMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_llm_response():
    """Mock successful LLM response"""
    return {"generated_text": "This is a mock LLM response for testing purposes."}


@pytest.fixture
def mock_env_with_llm():
    """Mock environment with LLM enabled"""
    with patch.dict(
        os.environ,
        {
            "USE_MOCK_RESPONSES": "false",
            "HF_ENDPOINT_URL": "https://test.endpoint.com",
            "HF_API_KEY": "test_key",
        },
    ):
        yield


@pytest.fixture
def mock_env_without_llm():
    """Mock environment with LLM disabled"""
    with patch.dict(os.environ, {"USE_MOCK_RESPONSES": "true"}):
        yield


@pytest.fixture
async def learning_agent():
    """Create a LearningAgent instance"""
    from simple_agents import LearningAgent

    agent = LearningAgent()
    yield agent
    # Cleanup
    if hasattr(agent, "llm_client"):
        await agent.llm_client.close()


@pytest.fixture
async def study_agent():
    """Create a StudyAgent instance"""
    from simple_agents import StudyAgent

    agent = StudyAgent()
    yield agent
    # Cleanup
    if hasattr(agent, "llm_client"):
        await agent.llm_client.close()


@pytest.fixture
async def exam_agent():
    """Create an ExamAgent instance"""
    from simple_agents import ExamAgent

    agent = ExamAgent()
    yield agent
    # Cleanup
    if hasattr(agent, "llm_client"):
        await agent.llm_client.close()


@pytest.fixture
def sample_chat_request():
    """Sample chat request data"""
    return {
        "agent": "learning",
        "message": "Bana bir öğrenme planı oluştur",
        "session_id": "test_session_123",
    }


@pytest.fixture
def sample_ws_message():
    """Sample WebSocket message"""
    return {"agent": "study", "message": "Python nedir?"}


# Parallel Test Execution - Database Isolation
@pytest.fixture(scope="session", autouse=True)
def worker_id(request):
    """Get worker ID for parallel test execution"""
    if hasattr(request.config, "workerinput"):
        return request.config.workerinput["workerid"]
    return "master"


@pytest.fixture(scope="session")
def test_database_url(worker_id):
    """Create isolated database URL for each test worker"""
    if worker_id == "master":
        db_name = "test_db"
    else:
        db_name = f"test_db_{worker_id}"

    # SQLite için test database
    return f"sqlite+aiosqlite:///./test_{db_name}.db"


@pytest.fixture(scope="session", autouse=True)
def setup_test_database(test_database_url, worker_id):
    """Setup isolated test database for parallel execution"""
    import os

    # Test environment değişkenlerini ayarla
    os.environ["DATABASE_URL"] = test_database_url
    os.environ["USE_TEST_DB"] = "true"
    os.environ["TEST_WORKER_ID"] = worker_id

    yield

    # Cleanup: Test database dosyasını sil
    if "sqlite" in test_database_url:
        db_file = test_database_url.split(":///")[-1]
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except Exception as e:
                print(f"Warning: Could not remove test database {db_file}: {e}")


@pytest.fixture
def isolated_cache_key(worker_id):
    """Create isolated cache keys for parallel tests"""

    def _key(base_key: str) -> str:
        return f"{base_key}_{worker_id}"

    return _key


# Consolidated Database Test Fixtures
@pytest.fixture
def mock_db():
    """Mock database dependency for testing"""
    return AsyncMock()


@pytest.fixture
def mock_db_session():
    """Mock database session for testing"""
    return AsyncMock()


# Consolidated User Test Fixtures
@pytest.fixture
def mock_student_user():
    """Mock student user for testing"""
    return {
        "user_id": "test_student_123",
        "username": "test_student",
        "role": "student",
        "email": "student@test.com",
    }


@pytest.fixture
def mock_admin_user():
    """Mock admin user for testing"""
    return {
        "user_id": "test_admin_123",
        "username": "test_admin",
        "role": "admin",
        "email": "admin@test.com",
    }


@pytest.fixture
def mock_teacher_user():
    """Mock teacher user for testing"""
    return {
        "user_id": "test_teacher_123",
        "username": "test_teacher",
        "role": "teacher",
        "email": "teacher@test.com",
    }


# ============================================================================
# PostgreSQL Test Fixtures and Database Session Management
# Provides comprehensive database fixtures for integration testing
# ============================================================================
import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
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

# Note: test_engine fixture removed - use test_async_engine from root conftest.py
# This avoids duplicate engine fixtures and ensures consistent engine configuration
# Import from root: from conftest import test_async_engine


# Note: setup_database fixture integrated into root conftest.py
# Database setup/teardown is handled automatically by the root fixtures


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
    from datetime import datetime
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
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
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
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
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
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
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

# Note: pytest_configure removed - markers are defined in pytest.ini
# This avoids redundant marker registration and ensures single source of truth
