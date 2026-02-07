"""
Testcontainers configuration for real integration tests
Uses Docker containers for PostgreSQL and Redis
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
import redis


# Module-scoped containers (shared across all tests in session)
@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for testing"""
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def redis_container():
    """Start Redis container for testing"""
    with RedisContainer("redis:7-alpine") as redis_c:
        yield redis_c


@pytest.fixture(scope="session")
def db_engine(postgres_container):
    """Create database engine using Testcontainer PostgreSQL"""
    engine = create_engine(postgres_container.get_connection_url())

    # Import all models to register them with Base
    from models.database import (
        Base,
    )

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Provide clean database session for each test"""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    yield session

    # Rollback after each test
    session.rollback()
    session.close()


@pytest.fixture(scope="session")
def redis_client(redis_container):
    """Provide Redis client using Testcontainer"""
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)

    client = redis.Redis(host=host, port=port, decode_responses=True)

    yield client

    # Cleanup
    client.flushall()
    client.close()


@pytest.fixture(scope="function")
def redis_session(redis_client):
    """Provide clean Redis session for each test"""
    yield redis_client
    # Flush all data after each test
    redis_client.flushall()


@pytest.fixture(scope="function")
def sync_db_session(db_engine):
    """Provide clean synchronous database session for each test"""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    yield session

    # Rollback and close after each test
    session.rollback()
    session.close()
