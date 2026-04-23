"""
Advanced Database Fixtures
Transaction rollback, async support, test data isolation
"""

from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

from models.base import Base

# ==================== SYNC DATABASE FIXTURES ====================


@pytest.fixture(scope="function")
def sync_db_engine():
    """Create sync in-memory SQLite engine per test"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def sync_db_session(sync_db_engine) -> Generator[Session, None, None]:
    """
    Create sync database session with automatic rollback
    Each test gets fresh database state
    """
    connection = sync_db_engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    # Rollback all changes
    session.close()
    transaction.rollback()
    connection.close()


# ==================== ASYNC DATABASE FIXTURES ====================


@pytest_asyncio.fixture(scope="function")
async def async_db_engine():
    """Create async in-memory SQLite engine per test"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_db_session(async_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create async database session with automatic rollback
    Each test gets fresh database state
    """
    async with async_db_engine.connect() as connection:
        async with connection.begin() as transaction:
            SessionLocal = sessionmaker(
                bind=connection,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            async with SessionLocal() as session:
                yield session

                # Rollback handled by transaction context manager
                await transaction.rollback()


# ==================== NESTED TRANSACTION FIXTURES ====================


@pytest_asyncio.fixture
async def async_db_session_nested(async_db_engine):
    """
    Async session with nested transaction support (savepoints)
    Useful for testing transaction handling
    """
    async with async_db_engine.connect() as connection:
        await connection.begin()

        SessionLocal = sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with SessionLocal() as session:
            await session.begin_nested()  # SAVEPOINT

            yield session

            await session.rollback()  # Rollback to SAVEPOINT


# ==================== ISOLATED DATABASE FIXTURES ====================


@pytest.fixture(scope="session")
def isolated_db_engine():
    """
    Session-scoped database for tests that need persistence
    Use sparingly - prefer function-scoped fixtures
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()


# ==================== FAST API DEPENDENCY OVERRIDE ====================


@pytest.fixture
def override_get_db(sync_db_session):
    """
    Override FastAPI get_db dependency with test session
    Usage:
        app.dependency_overrides[get_db_session] = override_get_db
    """

    def _get_test_db():
        try:
            yield sync_db_session
        finally:
            pass

    return _get_test_db


@pytest.fixture
def override_get_async_db(async_db_session):
    """
    Override FastAPI async get_db dependency
    """

    async def _get_test_async_db():
        yield async_db_session

    return _get_test_async_db


# ==================== DATABASE POPULATION HELPERS ====================


@pytest.fixture
def populate_test_data(sync_db_session):
    """Helper to populate database with test data"""

    def _populate(model_class, data_list):
        """
        Populate database with list of model instances

        Args:
            model_class: SQLAlchemy model class
            data_list: List of dicts with model data

        Returns:
            List of created instances
        """
        instances = []
        for data in data_list:
            instance = model_class(**data)
            sync_db_session.add(instance)
            instances.append(instance)

        sync_db_session.commit()
        return instances

    return _populate


@pytest_asyncio.fixture
async def async_populate_test_data(async_db_session):
    """Async helper to populate database"""

    async def _populate(model_class, data_list):
        instances = []
        for data in data_list:
            instance = model_class(**data)
            async_db_session.add(instance)
            instances.append(instance)

        await async_db_session.commit()
        return instances

    return _populate


# ==================== DATABASE STATE MANAGEMENT ====================


@pytest.fixture
def db_state_manager(sync_db_session):
    """
    Manage database state - snapshots and rollback
    """

    class DBStateManager:
        def __init__(self, session):
            self.session = session
            self.savepoints = []

        def create_savepoint(self, name: str = None):
            """Create a savepoint"""
            savepoint = self.session.begin_nested()
            self.savepoints.append((name or f"sp_{len(self.savepoints)}", savepoint))
            return savepoint

        def rollback_to_savepoint(self, name: str = None):
            """Rollback to named savepoint or last"""
            if not self.savepoints:
                return

            if name:
                # Find named savepoint
                for i, (sp_name, sp) in enumerate(self.savepoints):
                    if sp_name == name:
                        sp.rollback()
                        # Remove this and all later savepoints
                        self.savepoints = self.savepoints[:i]
                        return
            else:
                # Rollback last savepoint
                _, sp = self.savepoints.pop()
                sp.rollback()

        def commit_savepoint(self):
            """Commit last savepoint"""
            if self.savepoints:
                _, sp = self.savepoints.pop()
                sp.commit()

    return DBStateManager(sync_db_session)


# ==================== EVENT LISTENERS ====================


@pytest.fixture
def db_query_counter(sync_db_engine):
    """
    Count database queries for performance testing
    """

    class QueryCounter:
        def __init__(self):
            self.count = 0
            self.queries = []

        def increment(self, conn, cursor, statement, *args):
            self.count += 1
            self.queries.append(statement)

        def reset(self):
            self.count = 0
            self.queries = []

    counter = QueryCounter()

    event.listen(sync_db_engine, "before_cursor_execute", counter.increment)

    yield counter

    event.remove(sync_db_engine, "before_cursor_execute", counter.increment)


# ==================== CLEANUP ====================


@pytest.fixture(autouse=True)
def reset_db_state():
    """
    Auto-reset database state between tests
    Runs automatically for all tests
    """
    yield

    # Cleanup any lingering connections
    # This is handled by fixture teardown
