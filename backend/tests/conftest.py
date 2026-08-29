"""
Pytest configuration and fixtures for testing
"""

# ============================================================================
# KNOWN HANGING TESTS - Skip until properly mocked
# These tests make REAL network calls (model downloads, HTTP requests, DB connections)
# ============================================================================
# collect_ignore is now empty - all tests properly mocked

import asyncio
import os
import sys

# Note: WindowsSelectorEventLoopPolicy is set in root conftest.py (before collection)
# Generator import removed - not used in this file
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add backend directory to Python path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # noqa: PTH120, PTH100
sys.path.insert(0, backend_dir)
# Also add parent directory
sys.path.insert(0, os.path.dirname(backend_dir))  # noqa: PTH120

# Testcontainers support - activate with USE_TESTCONTAINERS=true
if os.getenv("USE_TESTCONTAINERS", "false").lower() == "true":
    try:
        from conftest_testcontainers import *  # noqa: F403
    except ImportError:
        print("conftest_testcontainers modulu bulunamadi, atlaniyor (opsiyonel)")

from httpx import ASGITransport, AsyncClient

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

test_env_path = os.path.join(os.path.dirname(__file__), "..", ".env.test")  # noqa: PTH118, PTH120
if os.path.exists(test_env_path):  # noqa: PTH110
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
os.environ["CORS_ALLOWED_ORIGINS"] = (
    "http://localhost:3000,http://localhost:5173,http://localhost:8080"
)

# FIX: Security keys for testing
if "SECRET_KEY" not in os.environ:
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-min-32-chars-long"  # noqa: S105
if "JWT_SECRET_KEY" not in os.environ:
    os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-only-32-chars"  # noqa: S105

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

# Patch SQLite to accept PostgreSQL JSONB
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler


def visit_JSONB(self, type_, **kw):  # noqa: N802
    return "JSON"


SQLiteTypeCompiler.visit_JSONB = visit_JSONB

try:
    from tests.fixtures.test_database import setup_test_environment

    setup_test_environment()
except ImportError:
    print("test_database modulu bulunamadi, atlaniyor (opsiyonel)")


# Note: event_loop fixture removed - pytest-asyncio 0.21+ handles this automatically
# Duplicate fixture from root conftest.py has been removed to avoid conflicts


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app"""
    from main import app

    client = create_test_client(app)
    yield client
    client.close()


def create_async_test_client(app):
    """Create an async httpx client using ASGITransport (httpx 0.27+ compatible).

    Usage in tests::

        async with create_async_test_client(app) as client:
            resp = await client.get("/health")
    """
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture(autouse=True)
def override_database_manager(test_async_engine):
    """Override DatabaseManager engine to use the shared test engine."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from core.database import db_manager

    original_engine = db_manager.engine
    original_maker = db_manager.async_session_maker
    original_initialized = db_manager._initialized

    db_manager.engine = test_async_engine
    db_manager.async_session_maker = async_sessionmaker(
        test_async_engine, class_=AsyncSession, expire_on_commit=False
    )
    db_manager._initialized = True

    yield

    db_manager.engine = original_engine
    db_manager.async_session_maker = original_maker
    db_manager._initialized = original_initialized


@pytest.fixture
async def async_client(setup_database):
    """Create an async test client for the FastAPI app"""
    from application.bootstrap import bootstrap_cqrs
    from main import app

    bootstrap_cqrs()

    async with create_async_test_client(app) as client:
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
    try:
        from simple_agents import LearningAgent
    except ImportError:
        pytest.skip("simple_agents module removed")
    agent = LearningAgent()
    try:
        yield agent
    finally:
        if hasattr(agent, "llm_client"):
            try:
                await agent.llm_client.close()
            except Exception as exc:
                print(f"learning_agent teardown: llm_client.close() basarisiz: {exc}")


@pytest.fixture
async def study_agent():
    """Create a StudyAgent instance"""
    try:
        from simple_agents import StudyAgent
    except ImportError:
        pytest.skip("simple_agents module removed")
    agent = StudyAgent()
    try:
        yield agent
    finally:
        if hasattr(agent, "llm_client"):
            try:
                await agent.llm_client.close()
            except Exception as exc:
                print(f"study_agent teardown: llm_client.close() basarisiz: {exc}")


@pytest.fixture
async def exam_agent():
    """Create an ExamAgent instance"""
    try:
        from simple_agents import ExamAgent
    except ImportError:
        pytest.skip("simple_agents module removed")
    agent = ExamAgent()
    try:
        yield agent
    finally:
        if hasattr(agent, "llm_client"):
            try:
                await agent.llm_client.close()
            except Exception as exc:
                print(f"exam_agent teardown: llm_client.close() basarisiz: {exc}")


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
        if os.path.exists(db_file):  # noqa: PTH110
            try:
                os.remove(db_file)  # noqa: PTH107
            except Exception as e:
                print(f"Warning: Could not remove test database {db_file}: {e}")


@pytest.fixture(scope="session", autouse=True)
def global_db_manager_cleanup():
    """Ensure db_manager is closed to prevent hanging aiosqlite threads in pytest-asyncio teardown.

    Deliberately a SYNC fixture, not ``async def``. pytest-asyncio 1.3.0 ties
    every async fixture to an event-loop fixture that defaults to
    function-scope; a session-scoped async fixture then hits a ScopeMismatch
    ("You tried to access the function scoped fixture event_loop with a
    session scoped request object") and the whole collection errors out
    before any test runs (this is what broke the Quality Gate workflow's
    "Router registration check" step). Running the one async call we
    actually need (`db_manager.close()`) through `asyncio.run()` inside a
    plain sync fixture sidesteps pytest-asyncio's loop-scope machinery
    entirely, instead of widening `asyncio_default_fixture_loop_scope`
    globally (which would change timing/isolation for every other async
    fixture in the suite -- a much bigger blast radius for one cleanup call).
    """
    yield
    from core.database import db_manager

    asyncio.run(db_manager.close())


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
# Test Password Generator - Solves recurring password validator failures
# Sessions 7, 8: Sequential chars (123, abc) rejected by validator
# ============================================================================
import uuid as _uuid


def generate_test_password(prefix: str = "Test") -> str:
    """Generate a strong password that passes all validators.

    This solves the recurring issue from Sessions 7 and 8 where test passwords
    like 'Test123!' were rejected by the password validator due to sequential
    characters (123, abc).

    Returns:
        A strong, unique password like 'Test_Kx9m4Rp7!'
    """
    unique = _uuid.uuid4().hex[:8]
    return f"{prefix}_{unique}Zq7!"


# Pre-generated test passwords for common use
TEST_PASSWORD_STUDENT = generate_test_password("Student")
TEST_PASSWORD_ADMIN = generate_test_password("Admin")
TEST_PASSWORD_TEACHER = generate_test_password("Teacher")


# ============================================================================
# JWT Test Helper - Centralized Token Generation (DRY)
# All test files should use these instead of defining their own
# ============================================================================
from datetime import UTC, datetime, timedelta

import jwt as pyjwt

TEST_JWT_SECRET = "test-secret-for-unit-tests-only"  # noqa: S105
TEST_JWT_ALGORITHM = "HS256"


def _generate_test_jwt(
    user_id: str, email: str | None = None, role: str = "student"
) -> str:
    """Generate valid JWT token for testing.

    Args:
        user_id: User ID to include in token (as 'sub' claim)
        email: Email address (auto-generated if not provided)
        role: User role (default: student)

    Returns:
        Valid JWT token string with 3 segments (header.payload.signature)
    """
    if email is None:
        email = f"user_{user_id}@test.com"

    payload = {
        "sub": user_id,
        "username": email.split("@")[0],
        "role": role,
        "email": email,
        "permissions": [],
        "exp": datetime.now(UTC) + timedelta(hours=1),
    }
    return pyjwt.encode(payload, TEST_JWT_SECRET, algorithm=TEST_JWT_ALGORITHM)


@pytest.fixture
def auth_headers(monkeypatch):
    """Generate authenticated headers with valid JWT token (student role).

    Automatically patches JWT_SECRET and JWT_ALGORITHM in dependencies.
    Use this fixture for tests requiring authenticated API calls.

    Example:
        def test_protected_endpoint(test_client, auth_headers):
            response = test_client.get("/api/v1/protected", headers=auth_headers)
            assert response.status_code == 200
    """
    monkeypatch.setattr("core.dependencies.JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setattr("core.dependencies.JWT_ALGORITHM", TEST_JWT_ALGORITHM)

    token = _generate_test_jwt("1", "test@example.com", "student")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_admin(monkeypatch):
    """Generate authenticated headers with admin role."""
    monkeypatch.setattr("core.dependencies.JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setattr("core.dependencies.JWT_ALGORITHM", TEST_JWT_ALGORITHM)

    token = _generate_test_jwt("admin_1", "admin@example.com", "admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_teacher(monkeypatch):
    """Generate authenticated headers with teacher role."""
    monkeypatch.setattr("core.dependencies.JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setattr("core.dependencies.JWT_ALGORITHM", TEST_JWT_ALGORITHM)

    token = _generate_test_jwt("teacher_1", "teacher@example.com", "teacher")
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Health Check Mock Fixture - Solves recurring Health 503 failures
# Sessions 7, 12, 19: Health endpoint returns 503 when Redis/DB unavailable
# ============================================================================


@pytest.fixture
def mock_health_check():
    """Mock health check to return 200 in test environment.

    Solves recurring issue: health endpoints return 503 in test environment
    because Redis and PostgreSQL are not available.

    Usage:
        def test_something(test_client, mock_health_check):
            response = test_client.get("/health")
            assert response.status_code == 200
    """
    health_result = {
        "status": "healthy",
        "services": {
            "database": {"status": "healthy", "latency_ms": 1},
            "redis": {"status": "healthy", "latency_ms": 1},
        },
    }
    with patch(
        "core.comprehensive_health_check.HealthChecker.check_all",
        new_callable=AsyncMock,
        return_value=health_result,
    ):
        yield health_result


# ============================================================================
# PostgreSQL Test Fixtures and Database Session Management
# Provides comprehensive database fixtures for integration testing
# ============================================================================
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

# Import database models to ensure they're registered

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
# Safe Database Setup (DuplicateTable Prevention)
# ============================================================================


@pytest_asyncio.fixture(scope="session")
async def setup_database(test_async_engine: AsyncEngine):
    """Create all tables safely, handling DuplicateTable/DuplicateObject errors.

    This fixture uses create_all(checkfirst=True) and catches PostgreSQL
    DuplicateObject errors for indexes/constraints. Prevents the recurring
    'DuplicateTable' crash seen in Sessions 12+ when reusing test databases.

    Usage:
        async def test_something(setup_database, db_session):
            ...
    """
    try:
        from models.base import Base

        async with test_async_engine.begin() as conn:
            # checkfirst=True is default but explicit for clarity
            print("Registered tables:", Base.metadata.tables.keys())
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
    except Exception as e:
        err_msg = str(e).lower()
        if (
            "already exists" in err_msg
            or "duplicatetable" in err_msg
            or "duplicateobject" in err_msg
        ):
            pass  # Tables already exist - safe to continue
        else:
            pytest.skip(f"Database setup failed: {e}")

    yield


# ============================================================================
# Database Session Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def db_session(
    test_async_engine: AsyncEngine, setup_database: None
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
    async with test_async_engine.connect() as connection:
        # Start a transaction manually to avoid context manager double-rollback deadlocks
        transaction = await connection.begin()
        # Create session bound to the transaction
        async_session_factory = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        session = async_session_factory()

        try:
            yield session
        finally:
            await session.close()
            # Rollback transaction cleanly
            if transaction.is_active:
                await transaction.rollback()


@pytest_asyncio.fixture
async def db_session_autocommit(
    test_async_engine: AsyncEngine, setup_database: None
) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session that auto-commits changes.
    Use this for tests that need to verify committed data.

    WARNING: Changes are NOT automatically rolled back!
    Use with caution or implement manual cleanup.
    """
    async_session_factory = async_sessionmaker(
        bind=test_async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


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
    import uuid
    from datetime import datetime  # TIMEZONE FIX

    from models.database import User

    async def _create_user(
        email: str = None,  # noqa: RUF013
        username: str = None,  # noqa: RUF013
        password_hash: str = "hashed_password_123",  # noqa: S107
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
            created_at=datetime.now(UTC),  # TIMEZONE FIX: deprecated utcnow()
            updated_at=datetime.now(UTC),  # TIMEZONE FIX: deprecated utcnow()
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
    import uuid
    from datetime import datetime  # TIMEZONE FIX

    from models.database import StudentProfile

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
            created_at=datetime.now(UTC),  # TIMEZONE FIX: deprecated utcnow()
            updated_at=datetime.now(UTC),  # TIMEZONE FIX: deprecated utcnow()
            **kwargs,
        )

        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        return profile

    return _create_student_profile


@pytest_asyncio.fixture
async def _test_topic(db_session: AsyncSession):
    """Shared test topic for question_factory FK requirement."""
    import uuid as _uuid

    from models.question_bank import TopicHierarchy

    topic_id = str(_uuid.uuid4())
    topic = TopicHierarchy(
        id=topic_id,
        level=1,
        code=f"TEST.{topic_id[:8]}",
        name_tr="Test Konu",
    )
    db_session.add(topic)
    await db_session.flush()
    return topic


@pytest.fixture
def question_factory(db_session: AsyncSession, _test_topic):
    """
    Factory for creating test questions in question_bank (production table).
    Uses QuestionBankItem (77K+ production soru) instead of legacy Question (BOŞ tablo).
    """
    import uuid
    from datetime import datetime

    from models.question_bank import QuestionBankItem, QuestionDifficultyLevel

    _difficulty_map = {
        "EASY": QuestionDifficultyLevel.EASY,
        "MEDIUM": QuestionDifficultyLevel.MEDIUM,
        "HARD": QuestionDifficultyLevel.HARD,
        "VERY_EASY": QuestionDifficultyLevel.VERY_EASY,
        "VERY_HARD": QuestionDifficultyLevel.VERY_HARD,
    }

    async def _create_question(
        question_text: str = "Test question?",
        subject_area: str = "MATEMATIK",
        difficulty: str = "MEDIUM",
        correct_answer: str = "A",
        **kwargs,
    ):
        question = QuestionBankItem(
            id=str(uuid.uuid4()),
            question_text=question_text,
            option_a="Option A",
            option_b="Option B",
            option_c="Option C",
            option_d="Option D",
            correct_answer=correct_answer,
            exam_type="TYT",
            subject_area=subject_area,
            primary_topic_id=kwargs.pop("primary_topic_id", _test_topic.id),
            grade_level=kwargs.pop("grade_level", 11),
            difficulty_level=_difficulty_map.get(
                difficulty, QuestionDifficultyLevel.MEDIUM
            ),
            irt_difficulty=0.5,
            irt_discrimination=1.0,
            irt_guessing=0.25,
            morphology_complexity=0.5,
            readability_score=0.7,
            times_asked=0,
            times_correct=0,
            average_response_time=0.0,
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
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
            question_text=f"Test question {i + 1}?",
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


# ============================================================================
# Test Isolation Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def isolate_environment(request, monkeypatch):
    """
    Automatically isolate environment variables per test.
    Prevents test pollution from environment changes.
    """
    # Store original environment
    original_env = os.environ.copy()

    yield

    # Restore environment after test
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def isolated_test_state():
    """
    Provides isolated state container for tests.
    Use when testing stateful components.

    Usage:
        def test_something(isolated_test_state):
            isolated_test_state["counter"] = 0
            # test logic
    """
    state = {}
    yield state
    state.clear()


@pytest.fixture
def reset_singletons():
    """
    Reset singleton instances between tests.
    Call this fixture when testing singleton patterns.
    """
    # Track singletons that need reset
    singletons_to_reset = []

    def _register(singleton_class):
        """Register a singleton for reset."""
        singletons_to_reset.append(singleton_class)
        return singleton_class

    yield _register

    # Reset registered singletons
    for cls in singletons_to_reset:
        if hasattr(cls, "_instance"):
            cls._instance = None
        if hasattr(cls, "_instances"):
            cls._instances.clear()


@pytest.fixture
def capture_logs(caplog):
    """
    Capture and analyze logs during test.
    Enhanced wrapper around pytest's caplog.

    Usage:
        def test_logging(capture_logs):
            some_function()
            assert capture_logs.contains("Expected message")
    """
    import logging

    class LogCapture:
        def __init__(self, caplog):
            self._caplog = caplog

        def contains(self, message: str, level: str = None) -> bool:  # noqa: RUF013
            """Check if logs contain message."""
            for record in self._caplog.records:
                if message in record.message:  # noqa: SIM102
                    if level is None or record.levelname == level:
                        return True
            return False

        def count(self, message: str) -> int:
            """Count occurrences of message."""
            return sum(1 for r in self._caplog.records if message in r.message)

        @property
        def messages(self):
            """Get all log messages."""
            return [r.message for r in self._caplog.records]

        @property
        def errors(self):
            """Get error-level messages."""
            return [
                r.message for r in self._caplog.records if r.levelno >= logging.ERROR
            ]

        @property
        def warnings(self):
            """Get warning-level messages."""
            return [
                r.message for r in self._caplog.records if r.levelno == logging.WARNING
            ]

    caplog.set_level(logging.DEBUG)
    return LogCapture(caplog)


@pytest.fixture
def temp_file(tmp_path):
    """
    Create temporary files for testing.

    Usage:
        def test_file_processing(temp_file):
            path = temp_file("test.txt", "content")
            result = process_file(path)
    """
    created_files = []

    def _create(name: str, content: str = "") -> str:
        file_path = tmp_path / name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        created_files.append(file_path)
        return str(file_path)

    yield _create

    # Cleanup
    for f in created_files:
        if f.exists():
            f.unlink()


# ============================================================================
# Test Data Cleanup
# ============================================================================


@pytest.fixture
def cleanup_after_test():
    """
    Register cleanup functions to run after test.

    Usage:
        def test_something(cleanup_after_test):
            resource = create_resource()
            cleanup_after_test(lambda: resource.close())
    """
    cleanup_funcs = []

    def _register(func):
        cleanup_funcs.append(func)

    yield _register

    # Run cleanup in reverse order
    for func in reversed(cleanup_funcs):
        try:
            func()
        except Exception as e:
            print(f"Cleanup error: {e}")


@pytest_asyncio.fixture
async def async_cleanup_after_test():
    """
    Register async cleanup functions to run after test.
    """
    cleanup_funcs = []

    def _register(func):
        cleanup_funcs.append(func)

    yield _register

    # Run cleanup in reverse order
    import asyncio

    for func in reversed(cleanup_funcs):
        try:
            if asyncio.iscoroutinefunction(func):
                await func()
            else:
                func()
        except Exception as e:
            print(f"Async cleanup error: {e}")


# ============================================================================
# Integration with test_helpers
# ============================================================================

# Import test helpers fixtures for global availability
try:
    from tests.utils.test_helpers import (
        fake_cache,  # noqa: F401
        fake_db,  # noqa: F401
        fake_http,  # noqa: F401
        question_builder,  # noqa: F401
        user_builder,  # noqa: F401
    )
except ImportError:
    print("test_helpers modulu bulunamadi, atlaniyor (opsiyonel)")

# =========================
# Client fixture - plain TestClient (no default Authorization)
# =========================
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a plain TestClient for the FastAPI app.

    Note: Use auth_headers fixture for authenticated requests.
    The auth_headers, auth_headers_admin, auth_headers_teacher fixtures
    are defined earlier in this file (lines 368-404).
    """
    from application.bootstrap import bootstrap_cqrs
    from main import app

    bootstrap_cqrs()

    c = TestClient(app, raise_server_exceptions=True)
    c.headers.pop("Authorization", None)

    with c:
        yield c
