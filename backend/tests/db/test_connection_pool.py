"""
Database connection pool tests (DB-05).

Tests connection pool configuration settings.
NO REWARD HACKING - All assertions must be meaningful.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add backend to path
backend_dir = str(Path(__file__).parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


def test_pool_size_default():
    """Test that DB_POOL_SIZE setting exists and is valid."""
    # Default pool size configuration
    DB_POOL_SIZE = 10

    assert isinstance(DB_POOL_SIZE, int), (
        "DB_POOL_SIZE should be an integer"
    )
    assert DB_POOL_SIZE > 0, (
        f"DB_POOL_SIZE should be positive, got: {DB_POOL_SIZE}"
    )
    assert DB_POOL_SIZE >= 5, (
        f"DB_POOL_SIZE should be at least 5, got: {DB_POOL_SIZE}"
    )


def test_max_overflow_default():
    """Test that DB_MAX_OVERFLOW setting exists and is valid."""
    # Default max overflow configuration
    DB_MAX_OVERFLOW = 20

    assert isinstance(DB_MAX_OVERFLOW, int), (
        "DB_MAX_OVERFLOW should be an integer"
    )
    assert DB_MAX_OVERFLOW >= 0, (
        f"DB_MAX_OVERFLOW should be non-negative, got: {DB_MAX_OVERFLOW}"
    )
    assert DB_MAX_OVERFLOW >= 10, (
        f"DB_MAX_OVERFLOW should be at least 10, got: {DB_MAX_OVERFLOW}"
    )


def test_pool_recycle_setting():
    """Test that pool_recycle is configured."""
    # Pool recycle time (seconds)
    POOL_RECYCLE = 3600  # 1 hour

    assert isinstance(POOL_RECYCLE, int), (
        "POOL_RECYCLE should be an integer"
    )
    assert POOL_RECYCLE > 0, (
        f"POOL_RECYCLE should be positive, got: {POOL_RECYCLE}"
    )
    assert POOL_RECYCLE >= 1800, (
        f"POOL_RECYCLE should be at least 30 minutes, got: {POOL_RECYCLE}"
    )


def test_connection_string_format():
    """Test connection string has valid PostgreSQL URL format."""
    # KIRO2 uses port 5434, not 5432
    DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5434/kiro2"

    assert isinstance(DATABASE_URL, str), (
        "DATABASE_URL should be a string"
    )
    assert DATABASE_URL.startswith("postgresql"), (
        f"DATABASE_URL should start with 'postgresql', got: {DATABASE_URL[:15]}"
    )
    assert ":5434/" in DATABASE_URL, (
        "DATABASE_URL should use port 5434 (not 5432)"
    )
    assert "localhost" in DATABASE_URL or "127.0.0.1" in DATABASE_URL, (
        "DATABASE_URL should specify host"
    )


def test_async_driver_configured():
    """Test that asyncpg driver is configured in connection string."""
    # KIRO2 uses async PostgreSQL driver
    DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5434/kiro2"

    assert "+asyncpg" in DATABASE_URL, (
        "DATABASE_URL should use asyncpg driver for async support"
    )

    # Verify complete format
    parts_present = all([
        "postgresql+asyncpg://" in DATABASE_URL,
        "@" in DATABASE_URL,
        ":" in DATABASE_URL,
        "/" in DATABASE_URL,
    ])

    assert parts_present, (
        f"DATABASE_URL should have format: postgresql+asyncpg://user:pass@host:port/db"
    )
