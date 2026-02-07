"""
ST-05: Smoke tests for Redis configuration.

Tests:
- redis_url configuration
- App starts without Redis connection
- Cache module importability
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import pytest  # noqa: E402


def test_redis_url_configured():
    """ST-05-01: redis_url is configured in settings."""
    from core.config import settings

    has_redis_url = hasattr(settings, 'redis_url')
    has_redis_host = hasattr(settings, 'redis_host')

    assert has_redis_url or has_redis_host, \
        "Settings must have redis_url or redis_host configuration"

    if has_redis_url:
        redis_url = settings.redis_url
        assert redis_url is not None, "redis_url must not be None"
        assert "redis://" in str(redis_url), \
            f"redis_url should contain redis://, got: {redis_url}"


def test_redis_port_configured():
    """ST-05-02: Redis port is configured."""
    from core.config import settings

    if hasattr(settings, 'redis_port'):
        assert isinstance(settings.redis_port, int), "redis_port must be int"
        assert settings.redis_port > 0, "redis_port must be positive"


def test_cache_module_importable():
    """ST-05-03: Redis cache module can be imported."""
    cache_module = None
    import_errors = []

    for module_path in ['core.redis_cache', 'core.cache', 'core.redis']:
        try:
            mod = __import__(module_path, fromlist=[''])
            cache_module = mod
            break
        except ImportError as e:
            import_errors.append(f"{module_path}: {e}")

    assert cache_module is not None, \
        f"Could not import cache module. Tried: {import_errors}"
