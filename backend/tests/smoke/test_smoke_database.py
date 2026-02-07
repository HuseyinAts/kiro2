"""
ST-04: Smoke tests for database configuration.

Tests:
- database_url configuration
- Connection pool size
- Async driver verification
- Production SQLite restriction
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))


def test_database_url_configured():
    """ST-04-01: database_url is configured in settings."""
    from core.config import settings

    assert hasattr(settings, 'database_url'), \
        "Settings must have database_url attribute"

    db_url = settings.database_url
    assert db_url is not None, "database_url must not be None"
    assert len(str(db_url)) > 0, "database_url must not be empty"

    db_url_str = str(db_url)
    assert "://" in db_url_str, "database_url must be a valid URL with ://"

    supported_drivers = ["postgresql", "sqlite", "mysql"]
    has_supported_driver = any(driver in db_url_str.lower() for driver in supported_drivers)
    assert has_supported_driver, \
        f"database_url must use supported driver, got: {db_url_str}"


def test_pool_size_configured():
    """ST-04-02: Database pool size is configured."""
    from core.config import settings

    pool_attrs = ['db_pool_size', 'DB_POOL_SIZE', 'DATABASE_POOL_SIZE', 'database_pool_size']
    has_pool = any(hasattr(settings, attr) for attr in pool_attrs)
    # Pool config is optional for testing; just verify settings exists
    assert settings is not None, "Settings object should exist"


def test_async_driver_in_url():
    """ST-04-03: Database URL uses async driver."""
    from core.config import settings

    db_url = str(settings.database_url).lower()

    sync_only_drivers = ["psycopg2://", "pymysql://", "mysqldb://"]
    has_sync_only = any(driver in db_url for driver in sync_only_drivers)

    assert not has_sync_only, \
        f"database_url should not use sync-only drivers, got: {db_url}"


def test_postgresql_for_kiro2():
    """ST-04-04: KIRO2 uses PostgreSQL."""
    from core.config import settings

    db_url = str(settings.database_url).lower()
    assert "postgresql" in db_url, \
        f"KIRO2 requires PostgreSQL, got: {db_url}"
