import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.modules.setdefault("chromadb", MagicMock())
sys.modules.setdefault("chromadb.config", MagicMock())

# CRITICAL: Prevent HuggingFace model downloads during tests (MUST be before any imports)
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Windows: Use SelectorEventLoop BEFORE any test collection
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# CRITICAL: Set TESTING=true at MODULE LEVEL before ANY imports
# This is the absolute earliest point - before pytest, before any test collection
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared&uri=true",
)
os.environ["REDIS_URL"] = os.getenv("TEST_REDIS_URL", "redis://localhost:6380/1")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-32-chars"  # noqa: S105  # pragma: allowlist secret
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-32-chars"  # noqa: S105  # pragma: allowlist secret
os.environ["ALLOWED_ORIGINS"] = '["http://localhost:3000"]'
os.environ["ANTHROPIC_API_KEY"] = "test-key"  # pragma: allowlist secret
os.environ["OPENAI_API_KEY"] = "test-key"  # pragma: allowlist secret

# Backend dizinini path'e ilk olarak ekle (pytest collection'dan önce)
_backend_dir = str(Path(__file__).parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import pytest


def pytest_configure(config):
    """
    Pytest configuration hook.

    Note: Environment variables are already set at module level above.
    This hook is kept for future configuration needs.
    """
    print("[OK] TESTING environment configured at module level")


@pytest.fixture(scope="module")
def test_app():
    """
    Create a minimal FastAPI app for smoke tests.

    This avoids importing main.py which triggers full router loading.
    Instead, we create a minimal app with only health endpoints.
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(
        title="KIRO2 Test App",
        version="1.0.0-test",
        description="Minimal app for smoke tests",
    )

    # Add basic CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add health endpoints (minimal, no database required)
    @app.get("/health")
    async def health():
        return {
            "health_status": "healthy",
            "response_time_ms": 1.0,
        }

    @app.get("/health/ready")
    async def ready():
        return {"status": "ready"}

    @app.get("/health/live")
    async def live():
        return {"status": "alive"}

    @app.get("/health/startup")
    async def startup():
        return {"status": "started"}

    @app.get("/health/database")
    async def database():
        return {"status": "healthy", "database": {"connected": False}}

    @app.get("/health/detailed")
    async def detailed():
        return {"status": "healthy", "components": []}

    return app


from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Test database URL - MUST be set via environment variable (security requirement)
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
SYNC_DATABASE_URL = os.getenv("SYNC_TEST_DATABASE_URL")

# Validate that required test database URLs are set
if not TEST_DATABASE_URL:
    # Use in-memory SQLite as fallback for fast tests
    TEST_DATABASE_URL = (
        "sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared&uri=true"
    )
    print("WARNING: TEST_DATABASE_URL not set, using in-memory SQLite")

if not SYNC_DATABASE_URL:
    SYNC_DATABASE_URL = "sqlite:///file:testdb?mode=memory&cache=shared&uri=true"
    print("WARNING: SYNC_TEST_DATABASE_URL not set, using in-memory SQLite")


# Session-scoped engine for performance
@pytest.fixture(scope="session")
def test_async_engine():
    """Create async engine once per test session (PERFORMANCE FIX).

    Deliberately a SYNC fixture, not ``async def`` -- same rationale as
    ``global_db_manager_cleanup`` in tests/conftest.py. This repo pins
    pytest-asyncio==0.21.1 (requirements.txt, requirements-test.txt,
    requirements.qa*.txt); that version ties every async fixture to the
    legacy ``event_loop`` fixture (always function-scoped), regardless of
    pytest.ini's ``asyncio_default_fixture_loop_scope = session`` (that key
    isn't honored by 0.21.x for a bare ``@pytest.fixture`` async def -- it's
    dead config under the pinned version). A session-scoped async fixture
    then hits ScopeMismatch ("function scoped fixture event_loop with a
    session scoped request object") and collection errors out before any
    test runs -- confirmed as the cause of Quality Gate's "Router
    registration check" failure on test_router_registration.py (29 Aug
    2026), which doesn't even touch the DB itself.

    ``create_async_engine()`` is a plain sync call (verified: not a
    coroutine function, builds an AsyncEngine with zero running event
    loop) -- the only real async step was teardown's ``await
    engine.dispose()``, which ``asyncio.run()`` covers without pytest-
    asyncio's loop-scope machinery. Downstream consumers (async_db_session,
    setup_database, override_database_manager, ...) are unaffected: they
    still get the same live AsyncEngine and still open their own ``async
    with test_async_engine.connect()`` on their own event loop -- only how
    pytest calls *this* fixture changes, not the object it yields.
    """
    from sqlalchemy.pool import NullPool, StaticPool

    # SQLite doesn't support pool_size/max_overflow - only use for PostgreSQL
    if "sqlite" in TEST_DATABASE_URL.lower():
        engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
    else:
        engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
            poolclass=NullPool,  # Prevent connection pool deadlocks in tests
        )
    yield engine
    asyncio.run(engine.dispose())


@pytest.fixture(scope="function")
async def async_db_session(test_async_engine):
    """Create async database session for tests (OPTIMIZED)"""
    async with test_async_engine.connect() as connection:
        transaction = await connection.begin()
        async_session_maker = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        session = async_session_maker()

        try:
            yield session
        finally:
            await session.close()
            if transaction.is_active:
                await transaction.rollback()


@pytest.fixture(scope="function")
def sync_db_session():
    """Create sync database session for tests"""
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(SYNC_DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    session = SessionLocal()
    try:
        yield session
        session.rollback()  # Test sonrasi rollback
    finally:
        session.close()

    engine.dispose()


@pytest.fixture(scope="session")
def setup_test_env_once():
    """
    Setup test environment variables ONCE per session.

    Note: Environment variables are now set at module level (before imports)
    to prevent database connection attempts during pytest collection.
    This fixture is kept for backward compatibility but is now mostly a no-op.
    """
    # Environment already set at module level
    yield
    # Cleanup after all tests
    # (optional - usually not needed as process ends)


# ============================================================================
# Hypothesis Profile Configuration (Phase 2: Enterprise-grade Test Stratification)
# ============================================================================
# Profile selection via HYPOTHESIS_PROFILE env var:
#   - property_fast: Fewer examples (10), fast execution, reduced false-fail
#   - property_strict: More examples (100), CI-quality signal
# ============================================================================

# Register profiles at module import time (before any test runs)
import os as _os

_hypothesis_profile = _os.getenv("HYPOTHESIS_PROFILE", "property_fast")

try:
    import hypothesis as _hypothesis

    # Register profiles
    _hypothesis.settings.register_profile(
        "property_fast",
        max_examples=10,
        deadline=None,
        suppress_health_check=[],
    )
    _hypothesis.settings.register_profile(
        "property_strict",
        max_examples=100,
        deadline=2000,  # 2 second deadline
        suppress_health_check=[],
    )

    # Load the selected profile
    _hypothesis.settings.load_profile(_hypothesis_profile)

    # Make hypothesis available globally for tests
    hypothesis = _hypothesis

except ImportError:
    # hypothesis not installed - profiles not available
    print("WARNING: hypothesis not installed, property-based test profiles atlaniyor")


# ============================================================================
# Phase 3, 4, 7, 8, 9, 10 & 11: Auto Marker Assignment
# ============================================================================
# Phase 3: property auto-mark for tests/property/
# Phase 4: infra auto-mark for tests/devops/
# Phase 7: Conservative integration/unit auto-mark to reduce unstratified
# Phase 8: Tighten integration (AND logic), add unit override before integration
# Phase 9: tests/unit/ coverage + API high-confidence integration (AND)
# Phase 10: Unit purity audit + Integration AND lock + Serial isolation
# Phase 11: Serial orthogonal + Integration HIGH CONF / CONTROLLED + Unstratified burn-down
# ============================================================================


def pytest_collection_modifyitems(config, items):
    """Add property/infra/integration/unit/serial markers to tests based on path."""
    import pytest as _pytest

    property_path = "/tests/property/"
    # Phase 4: Infra patterns - very conservative
    infra_paths = ["/tests/devops/"]

    # Phase 11: Integration - TWO LEVELS
    # HIGH CONF: /tests/integration/ path-only (most confident)
    integration_high_conf_path = "/tests/integration/"
    # CONTROLLED: api/routes/endpoints/http/clients - needs AND with name token
    integration_controlled_paths = [
        "/tests/api/",
        "/tests/routes/",
        "/tests/endpoints/",
        "/tests/http/",
        "/tests/clients/",
    ]
    integration_filename_tokens = [
        "_integration",
        "integration_",
        "_client",
        "_endpoint",
        "_router",
        "_repo",
        "_repository",
        "client",
        "router",
        "endpoint",
        "route",
        "http",
        "request",
        "response",
        "db",
        "repo",
        "repository",
    ]

    # Phase 10/11: Serial high-confidence patterns (very conservative)
    # Only very obvious flaky/threading/timing patterns
    serial_high_conf_tokens = [
        "concurrency",
        "concurrent",
        "thread",
        "threading",
        "lock",
        "timing",
        "rate_limit",
        "rate-limit",
        "global_state",
        "global-state",
        "shared_state",
        "race_condition",
        "deadlock",
    ]

    # Phase 7/8/9/10/11: Unit patterns - high confidence with forbidden token check
    unit_names = [
        "test_utils",
        "test_validators",
        "test_schemas",
        "test_pure_",
        "test_helpers",
        "test_constants",
        "test_validation",
        "test_helper",
        "test_schema",
    ]
    # Forbidden tokens - if these appear, DO NOT assign to unit (external deps)
    forbidden_unit_tokens = [
        "elasticsearch",
        "httpx",
        "requests",
        "redis",
        "sqlalchemy",
        "docker",
        "k8s",
        "boto",
        "s3",
        "openai",
        "anthropic",
        "chromadb",
        "qdrant",
        "postgres",
        "mysql",
    ]
    # Only apply to backend/tests/ directory
    tests_dir = "/tests/"

    # Phase 14: Routing directories - map unstratified tests to integration
    routing_dirs_p14 = [
        "/tests/services/",
        "/tests/core/",
        "/tests/test_pipeline/",
        "/tests/accessibility/",
    ]
    # Phase 15: Additional high-confidence routing directories
    routing_dirs_p15 = [
        "/tests/slow/",
        "/tests/smoke/",
        "/tests/functional/",
    ]
    # Phase 16: Final high-confidence routing - infra + integration
    # Infra: database, health - external dependencies
    routing_infra_p16 = [
        "/tests/db/",
        "/tests/health/",
    ]
    # Integration: fast, hooks, performance, agents, guardrails, mcp_servers
    routing_integration_p16 = [
        "/tests/fast/",
        "/tests/hooks/",
        "/tests/performance/",
        "/tests/agents/",
        "/tests/guardrails/",
        "/tests/mcp_servers/",
    ]
    stratification_markers = {"unit", "property", "integration", "infra", "serial"}

    # Helper: Check if item already has a stratification marker
    def is_stratified(item):
        """Check if item already has any stratification marker."""
        # Method 1: get_closest_marker (most reliable)
        for marker_name in stratification_markers:
            if item.get_closest_marker(marker_name):
                return True
        # Method 2: Check keywords (includes markers added during collection)
        for marker_name in stratification_markers:
            if marker_name in item.keywords:
                return True
        return False

    # Helper: Get normalized path from item
    def get_normalized_path(item):
        """Get normalized path from item."""
        fspath = getattr(item, "fspath", None)
        if fspath is not None:
            return str(fspath).replace("\\", "/")
        path = getattr(item, "path", None)
        if path is not None:
            return str(path).replace("\\", "/")
        try:
            return str(item.location[0]).replace("\\", "/")
        except (AttributeError, IndexError):
            return ""

    for item in items:
        # Get the file path safely - convert to string
        fspath = getattr(item, "fspath", None)
        if fspath is not None:
            fspath = str(fspath)
        else:
            path = getattr(item, "path", None)
            if path is not None:
                fspath = str(path)
            else:
                try:
                    fspath = str(item.location[0])
                except (AttributeError, IndexError):
                    continue

        if fspath is None:
            continue

        # Normalize path for cross-platform compatibility
        normalized_path = fspath.replace("\\", "/")

        # Only apply to backend/tests/ directory
        if tests_dir not in normalized_path:
            continue

        # Get nodeid for more detailed matching
        nodeid = getattr(item, "nodeid", "")

        # Phase 11: Check serial FIRST - orthogonal, doesn't block other markers
        # Add serial marker but DON'T break the flow
        has_serial_signal = any(
            token in normalized_path.lower() or token in nodeid.lower()
            for token in serial_high_conf_tokens
        )
        if has_serial_signal:
            markers = getattr(item, "own_markers", []) or []
            has_serial = any(m.name == "serial" for m in markers)
            if not has_serial:
                item.add_marker(_pytest.mark.serial)

        # Phase 4: Check if infra - add infra marker FIRST (highest priority)
        is_infra = any(infra_path in normalized_path for infra_path in infra_paths)

        if is_infra:
            markers = getattr(item, "own_markers", []) or []
            has_infra = any(m.name == "infra" for m in markers)
            if not has_infra:
                item.add_marker(_pytest.mark.infra)
            continue

        # Phase 10/11: Check tests/unit/ path FIRST
        # tests/unit/ is a strong signal for unit
        in_tests_unit = "/tests/unit/" in normalized_path

        # Check forbidden tokens
        has_forbidden = any(
            token in normalized_path.lower() or token in nodeid.lower()
            for token in forbidden_unit_tokens
        )

        if in_tests_unit:
            if not has_forbidden:
                # tests/unit/ without forbidden tokens → unit
                markers = getattr(item, "own_markers", []) or []
                has_unit = any(m.name == "unit" for m in markers)
                if not has_unit:
                    item.add_marker(_pytest.mark.unit)
                continue
            # tests/unit/ with forbidden tokens → re-route
            # Go to re-routing logic below
        else:
            # Not in tests/unit/ - check unit_names pattern
            is_unit = any(
                name in normalized_path or name in nodeid for name in unit_names
            )
            if is_unit and not has_forbidden:
                markers = getattr(item, "own_markers", []) or []
                has_unit = any(m.name == "unit" for m in markers)
                if not has_unit:
                    item.add_marker(_pytest.mark.unit)
                continue

        # Phase 10/11: Re-routing logic for tests with forbidden tokens
        # OR tests that are not high-confidence unit
        if has_forbidden:
            # Check infra signal (more specific than just devops path)
            # Expanded infra tokens for re-routing
            infra_tokens = [
                "elasticsearch",
                "redis",
                "sqlalchemy",
                "docker",
                "k8s",
                "postgres",
                "mysql",
                "chromadb",
                "qdrant",
            ]
            has_infra_signal = any(
                token in normalized_path.lower() or token in nodeid.lower()
                for token in infra_tokens
            )

            if has_infra_signal:
                # Has infra signal - mark as infra
                markers = getattr(item, "own_markers", []) or []
                has_infra = any(m.name == "infra" for m in markers)
                if not has_infra:
                    item.add_marker(_pytest.mark.infra)
                continue

            # Phase 11: Integration TWO LEVELS
            # Level 1: HIGH CONF - /tests/integration/ path-only (no name token needed)
            if integration_high_conf_path in normalized_path:
                markers = getattr(item, "own_markers", []) or []
                has_integration = any(m.name == "integration" for m in markers)
                if not has_integration:
                    item.add_marker(_pytest.mark.integration)
                continue

            # Level 2: CONTROLLED - api/routes/endpoints/http/clients - needs AND
            matches_path = any(
                token in normalized_path for token in integration_controlled_paths
            )
            matches_filename = any(
                token in normalized_path or token in nodeid
                for token in integration_filename_tokens
            )

            # MUST have BOTH - AND logic (no OR!)
            is_integration = matches_path and matches_filename

            if is_integration:
                markers = getattr(item, "own_markers", []) or []
                has_integration = any(m.name == "integration" for m in markers)
                if not has_integration:
                    item.add_marker(_pytest.mark.integration)
                continue

            # No clear signal - leave unstratified
            continue

        # Phase 11: Integration TWO LEVELS for non-forbidden tests
        # Level 1: HIGH CONF - /tests/integration/ path-only
        if integration_high_conf_path in normalized_path:
            markers = getattr(item, "own_markers", []) or []
            has_integration = any(m.name == "integration" for m in markers)
            if not has_integration:
                item.add_marker(_pytest.mark.integration)
            continue

        # Level 2: CONTROLLED - api/routes/endpoints/http/clients - needs AND
        matches_path = any(
            token in normalized_path for token in integration_controlled_paths
        )
        matches_filename = any(
            token in normalized_path or token in nodeid
            for token in integration_filename_tokens
        )

        # MUST have BOTH - AND logic (no OR!)
        is_integration = matches_path and matches_filename

        if is_integration:
            markers = getattr(item, "own_markers", []) or []
            has_integration = any(m.name == "integration" for m in markers)
            if not has_integration:
                item.add_marker(_pytest.mark.integration)
            continue

        # Phase 3: If path contains /tests/property/, add property marker
        if property_path in normalized_path:
            markers = getattr(item, "own_markers", []) or []
            has_property = any(m.name == "property" for m in markers)
            if not has_property:
                item.add_marker(_pytest.mark.property)

        # Phase 14: Routing directories - map unstratified tests to integration
        # Check if test is still unstratified after all above rules
        if not is_stratified(item):
            matches_routing_dir = any(
                routing_dir in normalized_path for routing_dir in routing_dirs_p14
            )
            if matches_routing_dir:
                markers = getattr(item, "own_markers", []) or []
                has_integration = any(m.name == "integration" for m in markers)
                if not has_integration:
                    item.add_marker(_pytest.mark.integration)

        # Phase 15: Additional high-confidence routing directories
        # slow/, smoke/, functional/ - these are clearly integration-level by domain
        if not is_stratified(item):
            matches_routing_dir = any(
                routing_dir in normalized_path for routing_dir in routing_dirs_p15
            )
            if matches_routing_dir:
                markers = getattr(item, "own_markers", []) or []
                has_integration = any(m.name == "integration" for m in markers)
                if not has_integration:
                    item.add_marker(_pytest.mark.integration)

        # Phase 16: Final high-confidence routing - infra (db, health) + integration
        if not is_stratified(item):
            # First check infra directories (db, health)
            matches_infra = any(
                routing_dir in normalized_path for routing_dir in routing_infra_p16
            )
            if matches_infra:
                markers = getattr(item, "own_markers", []) or []
                has_infra = any(m.name == "infra" for m in markers)
                if not has_infra:
                    item.add_marker(_pytest.mark.infra)
            # Then check integration directories
            else:
                matches_integration = any(
                    routing_dir in normalized_path
                    for routing_dir in routing_integration_p16
                )
                if matches_integration:
                    markers = getattr(item, "own_markers", []) or []
                    has_integration = any(m.name == "integration" for m in markers)
                    if not has_integration:
                        item.add_marker(_pytest.mark.integration)


def pytest_sessionfinish(session, exitstatus):
    """
    Teardown hook called after the entire test session finishes.
    Ensures SRE Bulkhead worker pools are cleanly shut down to avoid hanging.
    """
    try:
        from core.worker_pools import shutdown_pools

        shutdown_pools()
    except Exception as exc:
        print(f"WARNING: pytest_sessionfinish: shutdown_pools() basarisiz: {exc}")
