"""
Integration tests configuration
Use existing Docker PostgreSQL container for faster testing
"""

import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


# Set test environment variables before any imports that load config
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")

# Fix ALLOWED_ORIGINS JSON parsing error - must be valid JSON array string
# Remove any malformed values and use simple test value
for key in ["ALLOWED_ORIGINS", "SERVER_ALLOWED_ORIGINS"]:
    if key in os.environ:
        # Only keep if it's already valid JSON, otherwise remove it
        try:
            import json

            json.loads(os.environ[key])
        except (json.JSONDecodeError, ValueError):
            del os.environ[key]


@pytest.fixture(scope="session")
def db_engine():
    """Use existing Docker PostgreSQL container"""
    # Use the test-postgres container running on port 5433
    try:
        engine = create_engine("postgresql://testuser:test123@localhost:5433/testdb")
        # Test connection before proceeding
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        pytest.skip("Test PostgreSQL not available on port 5433")

    # Import all models to register with Base
    from models.database import (
        Base,
    )

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup - drop all tables after tests
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def sync_db_session(db_engine):
    """Provide clean database session with auto-rollback"""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    yield session

    # Auto-rollback to clean up test data
    session.rollback()
    session.close()
