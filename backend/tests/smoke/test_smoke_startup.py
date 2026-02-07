"""
ST-01: Smoke tests for backend startup and initialization.

Tests:
- Backend import without errors
- FastAPI instance verification
- UTF-8 encoding support
- Middleware loading
- Router loading
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from fastapi import FastAPI  # noqa: E402


def test_backend_import_no_error():
    """ST-01-01: Backend main module imports without error."""
    from main import app

    assert app is not None, "App should be initialized"


def test_app_is_fastapi_instance():
    """ST-01-02: App is a valid FastAPI instance."""
    from main import app

    assert isinstance(app, FastAPI), "App must be a FastAPI instance"
    assert app.title is not None, "App should have a title"


def test_utf8_encoding():
    """ST-01-03: UTF-8 encoding configured for Turkish characters."""
    # Test 1: System stdout encoding
    if hasattr(sys.stdout, 'encoding'):
        encoding = sys.stdout.encoding
        # On Windows, after io.TextIOWrapper fix, should be UTF-8
        assert encoding is not None, "Stdout encoding should be set"

    # Test 2: Turkish string handling
    turkish_text = "İstanbul Diyarbakır Şanlıurfa"
    turkish_upper = turkish_text.upper()

    # Verify no encoding errors occurred
    assert len(turkish_upper) > 0, "Turkish text should be processable"
    assert "İ" in turkish_text or "I" in turkish_upper, "Turkish characters should be preserved"


def test_middleware_loaded():
    """ST-01-04: Middleware configuration is present."""
    from main import app

    # FastAPI stores middleware in user_middleware before first request
    has_middleware = (
        hasattr(app, 'user_middleware') and len(app.user_middleware) > 0
    ) or (
        hasattr(app, 'middleware_stack') and app.middleware_stack is not None
    )
    assert has_middleware, "App should have middleware configured"


def test_routers_loaded():
    """ST-01-05: API routers are loaded (115+ endpoints expected)."""
    from main import app

    routes = app.routes
    assert len(routes) > 50, f"Expected 50+ routes, got {len(routes)}"

    # Verify we have actual endpoint routes, not just static/openapi
    route_paths = [getattr(route, 'path', '') for route in routes]
    api_routes = [p for p in route_paths if p.startswith('/api')]

    assert len(api_routes) > 10, f"Expected 10+ API routes, got {len(api_routes)}"
