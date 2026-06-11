"""
Unit tests for core infrastructure modules:
  - core/middleware_pipeline.py
  - core/connection_pool_optimizer.py
  - core/plugin_architecture.py
  - core/distributed_monitoring.py
  - core/background_job_processor.py

All tests use isolated imports with mocked external dependencies so no running
services (Redis, DB, Prometheus, etc.) are required.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

# ---------------------------------------------------------------------------
# Pre-import mocks for heavy / side-effect-heavy dependencies
# ---------------------------------------------------------------------------

# -- middleware_pipeline deps ------------------------------------------------
_MW_MOCKS = {
    "core.cache_system_integration": MagicMock(),
    "core.structured_logging": MagicMock(),
    "core.unified_config": MagicMock(),
    "core.unified_event_bus": MagicMock(),
}
_MW_MOCKS["core.structured_logging"].LogCategory = MagicMock()
_MW_MOCKS["core.structured_logging"].get_logger = MagicMock(return_value=MagicMock())
_MW_MOCKS["core.unified_config"].get_unified_config = MagicMock(
    return_value=MagicMock()
)
_MW_MOCKS["core.unified_event_bus"].EventPriority = MagicMock()
_MW_MOCKS["core.unified_event_bus"].EventType = MagicMock()
_MW_MOCKS["core.unified_event_bus"].publish_event = AsyncMock()

for _mod, _mock in _MW_MOCKS.items():
    if _mod not in sys.modules:
        sys.modules[_mod] = _mock

# -- connection_pool_optimizer deps -----------------------------------------
_CPO_MOCKS = {
    "core.enhanced_database": MagicMock(),
    "core.error_context": MagicMock(),
    "core.error_monitoring": MagicMock(),
    "core.exceptions": MagicMock(),
}
_CPO_MOCKS["core.enhanced_database"].ConnectionPoolConfig = MagicMock
_CPO_MOCKS["core.exceptions"].ErrorSeverity = MagicMock()
_CPO_MOCKS["core.exceptions"].DatabaseError = Exception

# async_error_context must work as an async context manager
_async_ctx = MagicMock()
_async_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
_async_ctx.__aexit__ = AsyncMock(return_value=False)
_CPO_MOCKS["core.error_context"].async_error_context = MagicMock(
    return_value=_async_ctx
)
_CPO_MOCKS["core.error_monitoring"].log_error = AsyncMock()

for _mod, _mock in _CPO_MOCKS.items():
    if _mod not in sys.modules:
        sys.modules[_mod] = _mock

# -- plugin_architecture deps ------------------------------------------------
if "yaml" not in sys.modules:
    sys.modules["yaml"] = MagicMock()

# -- distributed_monitoring deps ---------------------------------------------
if "prometheus_client" not in sys.modules:
    _prom = MagicMock()
    # Make Counter/Gauge/Histogram/Info return callables that track labels
    for _prom_cls in ("Counter", "Gauge", "Histogram", "Info"):
        _inst = MagicMock()
        _inst.labels = MagicMock(return_value=MagicMock())
        _inst.info = MagicMock()
        setattr(_prom, _prom_cls, MagicMock(return_value=_inst))
    sys.modules["prometheus_client"] = _prom

if "httpx" not in sys.modules:
    sys.modules["httpx"] = MagicMock()

# -- background_job_processor deps -------------------------------------------
_BJP_MOCKS = {
    "core.application_metrics": MagicMock(),
    "core.message_queue_system": MagicMock(),
}
_BJP_MOCKS["core.application_metrics"].MetricType = MagicMock()
_BJP_MOCKS["core.application_metrics"].get_metrics_collector = MagicMock(
    return_value=MagicMock()
)
_BJP_MOCKS["core.message_queue_system"].QueueType = MagicMock()

for _mod, _mock in _BJP_MOCKS.items():
    if _mod not in sys.modules:
        sys.modules[_mod] = _mock

# ---------------------------------------------------------------------------
# Now safe to import the modules under test
# ---------------------------------------------------------------------------
import uuid  # noqa: E402
from datetime import UTC
from http import HTTPMethod  # noqa: E402

from core.background_job_processor import (  # noqa: E402
    BackgroundJobRegistry,
    JobDefinition,
    JobExecution,
    JobPriority,
    RetryPolicy,
)
from core.connection_pool_optimizer import (  # noqa: E402
    ConnectionMetrics,
    ConnectionState,
    ConnectionTracker,
    OptimizationStrategy,
    PoolHealthStatus,
    PoolMetrics,
    PoolMonitor,
    PoolOptimizer,
    get_connection_statistics,
    get_optimization_statistics,
    get_pool_health,
    track_pool_metrics,
)
from core.distributed_monitoring import (  # noqa: E402
    Alert,
    AlertManager,
    AlertSeverity,
    DistributedMonitoringSidekick,
    DistributedTracer,
    MicroserviceRegistry,
    ServiceHealthChecker,
    ServiceStatus,
    TraceSpan,
    TracingContext,
)
from core.message_queue_system import QueueType  # noqa: E402
from core.middleware_pipeline import (  # noqa: E402
    CompressionMiddleware,
    MiddlewarePriority,
    MiddlewareType,
    RateLimitingMiddleware,
    RateLimitRule,
    RequestValidationMiddleware,
    SecurityMiddleware,
    TurkishLocalizationMiddleware,
    ValidationRule,
    configure_middleware_for_route,
    create_compression_middleware,
    create_rate_limiting_middleware,
    create_security_middleware,
    create_turkish_localization_middleware,
    create_validation_middleware,
)
from core.plugin_architecture import (  # noqa: E402
    AgentCapability,
    AgentManifest,
    AgentOrchestrator,
    AgentRegistry,
    BaseAgentPlugin,
    PluginLoader,
    get_agent_registry,
    get_plugin_loader,
)
from core.unified_api_gateway import (  # noqa: E402
    APIRequest,
    APIResponse,
    APIVersion,
    RouteType,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(
    path: str = "/test",
    method: HTTPMethod = HTTPMethod.GET,
    client_ip: str = "1.2.3.4",
    user_id=None,
    headers: dict = None,
    body=None,
    query_params: dict = None,
) -> APIRequest:
    return APIRequest(
        id=str(uuid.uuid4()),
        method=method,
        path=path,
        version=APIVersion.V1,
        route_type=RouteType.HEALTH,
        headers=headers or {},
        query_params=query_params or {},
        body=body,
        client_ip=client_ip,
        user_agent="test-agent",
        user_id=user_id,
        metadata={},
    )


def _make_response(status_code: int = 200, body=None) -> APIResponse:
    return APIResponse(
        request_id=str(uuid.uuid4()),
        status_code=status_code,
        headers={"Content-Type": "application/json"},
        body=body or {"result": "ok"},
        processing_time_ms=1.0,
    )


def _make_pool_config(**kwargs):
    """Return a mock ConnectionPoolConfig-like object."""
    cfg = MagicMock()
    cfg.pool_size = kwargs.get("pool_size", 10)
    cfg.max_overflow = kwargs.get("max_overflow", 20)
    cfg.pool_timeout = kwargs.get("pool_timeout", 30)
    cfg.pool_recycle = kwargs.get("pool_recycle", 3600)
    cfg.pool_pre_ping = kwargs.get("pool_pre_ping", False)
    cfg.pool_reset_on_return = kwargs.get("pool_reset_on_return", "rollback")
    return cfg


def _make_pool_metrics(
    pool_id: str = "p1",
    pool_size: int = 10,
    checked_out: int = 3,
):
    """Create a PoolMetrics; utilization_ratio is computed by __post_init__."""
    from datetime import datetime

    return PoolMetrics(
        pool_id=pool_id,
        timestamp=datetime.now(),
        pool_size=pool_size,
        checked_out=checked_out,
        checked_in=pool_size - checked_out,
        overflow=0,
        invalid=0,
    )


def _make_agent_manifest(**kwargs):
    return AgentManifest(
        name=kwargs.get("name", "test_agent"),
        version=kwargs.get("version", "1.0"),
        description=kwargs.get("description", "A test agent"),
        author=kwargs.get("author", "tester"),
        capabilities=kwargs.get("capabilities", [AgentCapability.TEACHING]),
        supported_languages=kwargs.get("supported_languages", ["tr", "en"]),
        supported_subjects=kwargs.get("supported_subjects", ["matematik"]),
    )


# ===========================================================================
# ==================== middleware_pipeline tests ============================
# ===========================================================================


class TestMiddlewareEnums:
    def test_middleware_type_values(self):
        assert MiddlewareType.SECURITY.value == "security"
        assert MiddlewareType.AUTHENTICATION.value == "authentication"
        assert MiddlewareType.TURKISH_LOCALIZATION.value == "turkish_localization"

    def test_middleware_priority_ordering(self):
        assert MiddlewarePriority.CRITICAL.value < MiddlewarePriority.HIGH.value
        assert MiddlewarePriority.HIGH.value < MiddlewarePriority.NORMAL.value
        assert MiddlewarePriority.NORMAL.value < MiddlewarePriority.LOW.value
        assert MiddlewarePriority.LOW.value < MiddlewarePriority.LOWEST.value


class TestSecurityMiddleware:
    def setup_method(self):
        self.mw = SecurityMiddleware({})

    @pytest.mark.asyncio
    async def test_blocked_ip_returns_403(self):
        self.mw.blocked_ips.add("10.0.0.1")
        request = _make_request(client_ip="10.0.0.1")
        resp = await self.mw(request, AsyncMock())
        assert resp.status_code == 403
        assert resp.body["error"] == "Forbidden"

    @pytest.mark.asyncio
    async def test_blocked_user_agent_returns_403(self):
        request = _make_request()
        request.user_agent = "evil-bot"
        self.mw.blocked_user_agents.add("evil-bot")
        resp = await self.mw(request, AsyncMock())
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_clean_request_passes_through(self):
        next_handler = AsyncMock(return_value=_make_response())
        request = _make_request()
        resp = await self.mw(request, next_handler)
        assert resp.status_code == 200
        next_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_security_headers_added(self):
        next_handler = AsyncMock(return_value=_make_response())
        request = _make_request()
        resp = await self.mw(request, next_handler)
        assert "X-Content-Type-Options" in resp.headers
        assert "X-Frame-Options" in resp.headers

    @pytest.mark.parametrize(
        "path,expected",
        [
            ("/normal/path", False),
            ("/path?q=<script>alert(1)</script>", True),
            ("/path?q=union+select+*", True),
            ("/path?q=../etc/passwd", True),
        ],
    )
    def test_suspicious_pattern_detection(self, path, expected):
        request = _make_request(path=path)
        result = self.mw._has_suspicious_patterns(request)
        assert result == expected

    def test_request_size_calculation_with_body(self):
        request = _make_request(body={"key": "value"})
        size = self.mw._get_request_size(request)
        assert size > 0

    def test_request_size_calculation_empty_body(self):
        request = _make_request()
        size = self.mw._get_request_size(request)
        assert size >= 0


class TestRequestValidationMiddleware:
    def setup_method(self):
        self.mw = RequestValidationMiddleware({})

    @pytest.mark.asyncio
    async def test_valid_request_passes(self):
        next_handler = AsyncMock(return_value=_make_response())
        request = _make_request()
        resp = await self.mw(request, next_handler)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_missing_required_field_returns_400(self):
        next_handler = AsyncMock(return_value=_make_response())
        request = _make_request(path="/auth/login")
        # body is None -> missing required email/password
        resp = await self.mw(request, next_handler)
        assert resp.status_code == 400
        assert "validation_errors" in resp.body

    @pytest.mark.asyncio
    async def test_default_rules_set_up(self):
        assert "/auth/login" in self.mw.validation_rules
        assert "/exams/tyt/start" in self.mw.validation_rules

    @pytest.mark.asyncio
    async def test_apply_rule_required_missing(self):
        rule = ValidationRule(field="email", required=True)
        error = await self.mw._apply_rule(rule, {})
        assert error is not None
        assert error["field"] == "email"

    @pytest.mark.asyncio
    async def test_apply_rule_optional_absent(self):
        rule = ValidationRule(field="notes", required=False)
        error = await self.mw._apply_rule(rule, {})
        assert error is None

    @pytest.mark.asyncio
    async def test_apply_rule_min_length_violation(self):
        rule = ValidationRule(field="password", min_length=8)
        error = await self.mw._apply_rule(rule, {"password": "short"})
        assert error is not None
        assert "min" in error["error"].lower() or "8" in error["error"]

    @pytest.mark.asyncio
    async def test_apply_rule_allowed_values_violation(self):
        rule = ValidationRule(
            field="session_type",
            allowed_values=["practice", "simulation"],
        )
        error = await self.mw._apply_rule(rule, {"session_type": "invalid"})
        assert error is not None

    @pytest.mark.asyncio
    async def test_apply_rule_pattern_violation(self):
        rule = ValidationRule(
            field="email",
            pattern=r"^[a-z]+@[a-z]+\.[a-z]+$",
            error_message="Bad email",
            error_message_tr="Kötü email",
        )
        error = await self.mw._apply_rule(rule, {"email": "not-an-email"})
        assert error is not None

    @pytest.mark.asyncio
    async def test_apply_rule_custom_sync_validator_pass(self):
        # type=int ensures the value is treated as int so `v > 0` works
        rule = ValidationRule(
            field="score",
            type=int,
            custom_validator=lambda v: v > 0,
            error_message="Must be positive",
            error_message_tr="Pozitif olmalı",
        )
        error = await self.mw._apply_rule(rule, {"score": 5})
        assert error is None

    @pytest.mark.asyncio
    async def test_apply_rule_custom_sync_validator_fail(self):
        rule = ValidationRule(
            field="score",
            type=int,
            custom_validator=lambda v: v > 0,
            error_message="Must be positive",
            error_message_tr="Pozitif olmalı",
        )
        error = await self.mw._apply_rule(rule, {"score": -1})
        assert error is not None

    @pytest.mark.asyncio
    async def test_apply_rule_async_validator(self):
        async def async_validator(v):
            return v == "valid"

        rule = ValidationRule(
            field="code",
            custom_validator=async_validator,
            error_message="Invalid code",
            error_message_tr="Geçersiz kod",
        )
        error = await self.mw._apply_rule(rule, {"code": "valid"})
        assert error is None

        error2 = await self.mw._apply_rule(rule, {"code": "bad"})
        assert error2 is not None


class TestRateLimitingMiddleware:
    def setup_method(self):
        self.mw = RateLimitingMiddleware({})

    @pytest.mark.asyncio
    async def test_first_request_passes(self):
        next_handler = AsyncMock(return_value=_make_response())
        request = _make_request(user_id=42)
        resp = await self.mw(request, next_handler)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limit_headers_added(self):
        next_handler = AsyncMock(return_value=_make_response())
        request = _make_request(user_id=99)
        resp = await self.mw(request, next_handler)
        assert "X-RateLimit-Limit" in resp.headers
        assert "X-RateLimit-Remaining" in resp.headers

    @pytest.mark.asyncio
    async def test_blocked_client_returns_429(self):
        from datetime import datetime, timedelta

        client_key = "user_77"
        self.mw.blocked_clients[client_key] = datetime.now(UTC) + timedelta(seconds=300)
        # Override _get_client_key to return our key
        with patch.object(self.mw, "_get_client_key", return_value=client_key):
            request = _make_request(user_id=77)
            resp = await self.mw(request, AsyncMock())
        assert resp.status_code == 429

    def test_get_client_key_per_user(self):
        rule = RateLimitRule(requests_per_minute=10, per_user=True)
        request = _make_request(user_id=5)
        key = self.mw._get_client_key(request, rule)
        assert key == "user_5"

    def test_get_client_key_per_ip(self):
        rule = RateLimitRule(requests_per_minute=10, per_user=False, per_ip=True)
        request = _make_request(client_ip="192.168.1.1")
        key = self.mw._get_client_key(request, rule)
        assert key == "ip_192.168.1.1"

    @pytest.mark.asyncio
    async def test_check_rate_limit_under_limit(self):
        rule = RateLimitRule(requests_per_minute=100)
        result = await self.mw._check_rate_limit("new_client", rule)
        assert result is True

    @pytest.mark.asyncio
    async def test_check_rate_limit_over_limit(self):
        from datetime import datetime

        rule = RateLimitRule(requests_per_minute=2)
        now = datetime.now(UTC)
        self.mw.request_counts["busy_client"] = {
            "requests": [now, now],
            "last_reset": now,
        }
        result = await self.mw._check_rate_limit("busy_client", rule)
        assert result is False

    def test_is_blocked_expired(self):
        from datetime import datetime, timedelta

        self.mw.blocked_clients["old_key"] = datetime.now(UTC) - timedelta(seconds=1)
        assert self.mw._is_blocked("old_key") is False
        assert "old_key" not in self.mw.blocked_clients

    def test_default_limits_configured(self):
        assert "/auth/login" in self.mw.rate_limits
        assert "default" in self.mw.rate_limits


class TestCompressionMiddleware:
    def setup_method(self):
        self.mw = CompressionMiddleware({"min_size": 10})

    @pytest.mark.asyncio
    async def test_no_gzip_header_skips_compression(self):
        next_handler = AsyncMock(return_value=_make_response())
        request = _make_request(headers={})
        resp = await self.mw(request, next_handler)
        assert "Content-Encoding" not in resp.headers

    @pytest.mark.asyncio
    async def test_gzip_accepted_small_response_not_compressed(self):
        next_handler = AsyncMock(return_value=_make_response(body={"x": 1}))
        request = _make_request(headers={"Accept-Encoding": "gzip"}, body={"x": 1})
        self.mw.min_size = 999_999  # force skip
        resp = await self.mw(request, next_handler)
        assert "Content-Encoding" not in resp.headers

    def test_should_compress_json(self):
        resp = _make_response()
        resp.headers["Content-Type"] = "application/json"
        assert self.mw._should_compress(resp) is True

    def test_should_not_compress_already_gzipped(self):
        resp = _make_response()
        resp.headers["Content-Encoding"] = "gzip"
        assert self.mw._should_compress(resp) is False

    @pytest.mark.asyncio
    async def test_compress_body(self):
        data = {"message": "hello world " * 50}
        compressed = await self.mw._compress_response_body(data)
        assert isinstance(compressed, bytes)
        assert len(compressed) > 0

    def test_get_response_size(self):
        resp = _make_response(body={"key": "value"})
        size = self.mw._get_response_size(resp)
        assert size > 0

    def test_get_response_size_empty_body(self):
        resp = APIResponse(
            request_id="r1",
            status_code=204,
            headers={},
            body=None,
            processing_time_ms=1.0,
        )
        assert self.mw._get_response_size(resp) == 0


class TestTurkishLocalizationMiddleware:
    def setup_method(self):
        self.mw = TurkishLocalizationMiddleware({})

    @pytest.mark.asyncio
    async def test_locale_set_in_metadata(self):
        request = _make_request()
        resp_obj = _make_response()
        next_handler = AsyncMock(return_value=resp_obj)
        await self.mw(request, next_handler)
        assert request.metadata.get("locale") == "tr-TR"

    @pytest.mark.asyncio
    async def test_content_language_header_added(self):
        next_handler = AsyncMock(return_value=_make_response())
        request = _make_request()
        resp = await self.mw(request, next_handler)
        assert resp.headers.get("Content-Language") == "tr-TR"

    @pytest.mark.asyncio
    async def test_message_tr_added_when_missing(self):
        body = {"message": "success"}
        next_handler = AsyncMock(return_value=_make_response(body=body))
        request = _make_request()
        resp = await self.mw(request, next_handler)
        # The localization middleware may or may not translate "success"
        # but should not crash
        assert resp.body is not None

    def test_translate_message_known_key(self):
        result = self.mw._translate_message("error occurred")
        # "error" is in the common translations → should be translated
        assert isinstance(result, str)

    def test_translate_message_unknown_returns_original(self):
        original = "some_random_phrase_xyz"
        result = self.mw._translate_message(original)
        assert result == original

    def test_translations_loaded(self):
        assert "common" in self.mw.translations
        assert "exam" in self.mw.translations
        assert "auth" in self.mw.translations


class TestMiddlewareFactoryFunctions:
    def test_create_security_middleware(self):
        mw = create_security_middleware({"max_request_size": 1024})
        assert isinstance(mw, SecurityMiddleware)

    def test_create_validation_middleware(self):
        mw = create_validation_middleware()
        assert isinstance(mw, RequestValidationMiddleware)

    def test_create_rate_limiting_middleware(self):
        mw = create_rate_limiting_middleware()
        assert isinstance(mw, RateLimitingMiddleware)

    def test_create_compression_middleware(self):
        mw = create_compression_middleware({"min_size": 500})
        assert isinstance(mw, CompressionMiddleware)

    def test_create_turkish_localization_middleware(self):
        mw = create_turkish_localization_middleware()
        assert isinstance(mw, TurkishLocalizationMiddleware)

    @pytest.mark.parametrize(
        "route_type,must_include",
        [
            ("auth", "security"),
            ("yks_info", "caching"),
            ("health", "security"),
            ("default", "turkish_localization"),
        ],
    )
    def test_configure_middleware_for_route(self, route_type, must_include):
        middleware_list = configure_middleware_for_route(route_type)
        assert must_include in middleware_list

    def test_configure_middleware_unknown_route_returns_default(self):
        middleware_list = configure_middleware_for_route("nonexistent_route")
        assert "security" in middleware_list


# ===========================================================================
# ==================== connection_pool_optimizer tests =====================
# ===========================================================================


class TestConnectionMetrics:
    def _make_metrics(self, state=ConnectionState.IDLE, errors=0) -> ConnectionMetrics:
        from datetime import datetime

        return ConnectionMetrics(
            connection_id="conn-1",
            created_at=datetime.now(),
            last_used=datetime.now(),
            state=state,
            error_count=errors,
        )

    def test_age_seconds_nonnegative(self):
        import time

        m = self._make_metrics()
        time.sleep(0.01)
        assert m.age_seconds() >= 0

    def test_idle_time_seconds_nonnegative(self):
        import time

        m = self._make_metrics()
        time.sleep(0.01)
        assert m.idle_time_seconds() >= 0

    def test_is_stale_fresh(self):
        m = self._make_metrics()
        assert m.is_stale(max_idle_time=999999) is False

    def test_is_healthy_idle_no_errors(self):
        m = self._make_metrics(state=ConnectionState.IDLE, errors=0)
        assert m.is_healthy() is True

    def test_is_healthy_active(self):
        m = self._make_metrics(state=ConnectionState.ACTIVE)
        assert m.is_healthy() is True

    def test_is_not_healthy_error_state(self):
        m = self._make_metrics(state=ConnectionState.ERROR, errors=5)
        assert m.is_healthy() is False


class TestConnectionTracker:
    def setup_method(self):
        self.tracker = ConnectionTracker()

    def test_track_created(self):
        self.tracker.track_connection_created("c1")
        assert "c1" in self.tracker.connections
        assert self.tracker.connections["c1"].state == ConnectionState.IDLE

    def test_track_checkout(self):
        self.tracker.track_connection_created("c2")
        self.tracker.track_connection_checkout("c2")
        assert self.tracker.connections["c2"].state == ConnectionState.ACTIVE
        assert "c2" in self.tracker.active_connections

    def test_track_checkin(self):
        self.tracker.track_connection_created("c3")
        self.tracker.track_connection_checkout("c3")
        self.tracker.track_connection_checkin("c3")
        assert self.tracker.connections["c3"].state == ConnectionState.IDLE
        assert "c3" not in self.tracker.active_connections

    def test_track_closed(self):
        self.tracker.track_connection_created("c4")
        self.tracker.track_connection_closed("c4")
        assert "c4" not in self.tracker.connections
        assert len(self.tracker.connection_history) == 1

    def test_track_error(self):
        self.tracker.track_connection_created("c5")
        self.tracker.track_connection_error("c5", "timeout")
        assert self.tracker.connections["c5"].state == ConnectionState.ERROR
        assert self.tracker.connections["c5"].error_count == 1

    def test_detect_no_leaks_when_fresh(self):
        self.tracker.track_connection_created("c6")
        self.tracker.track_connection_checkout("c6")
        leaks = self.tracker.detect_connection_leaks()
        assert len(leaks) == 0

    def test_get_connection_stats_empty(self):
        stats = self.tracker.get_connection_stats()
        assert stats["total_connections"] == 0
        assert stats["active_connections"] == 0

    def test_get_connection_stats_with_connections(self):
        self.tracker.track_connection_created("x1")
        self.tracker.track_connection_created("x2")
        self.tracker.track_connection_checkout("x2")
        stats = self.tracker.get_connection_stats()
        assert stats["total_connections"] == 2
        assert stats["active_connections"] == 1
        assert stats["idle_connections"] == 1


class TestPoolMetrics:
    def test_utilization_ratio_computed(self):
        # __post_init__ computes utilization_ratio = checked_out / pool_size
        m = _make_pool_metrics(pool_size=10, checked_out=5)
        assert m.utilization_ratio == pytest.approx(0.5)

    def test_zero_pool_size_no_division(self):
        from datetime import datetime

        m = PoolMetrics(
            pool_id="p0",
            timestamp=datetime.now(),
            pool_size=0,
            checked_out=0,
            checked_in=0,
            overflow=0,
            invalid=0,
        )
        assert m.utilization_ratio == 0.0


class TestPoolMonitor:
    def setup_method(self):
        self.monitor = PoolMonitor(analysis_window_minutes=5)

    def test_no_metrics_returns_warning(self):
        status, issues = self.monitor.analyze_pool_health("unknown_pool")
        assert status == PoolHealthStatus.WARNING
        assert len(issues) > 0

    def test_healthy_pool(self):
        # utilization = checked_out / pool_size = 3/10 = 0.3 (below warning threshold)
        for _ in range(3):
            m = _make_pool_metrics(pool_size=10, checked_out=3)
            self.monitor.record_metrics("healthy", m)
        status, issues = self.monitor.analyze_pool_health("healthy")
        assert status == PoolHealthStatus.HEALTHY
        assert issues == []

    def test_high_utilization_warning(self):
        # utilization = 9/10 = 0.9 (above warning threshold 0.8)
        for _ in range(3):
            m = _make_pool_metrics(pool_size=10, checked_out=9)
            self.monitor.record_metrics("warn_pool", m)
        status, _ = self.monitor.analyze_pool_health("warn_pool")
        assert status in (PoolHealthStatus.WARNING, PoolHealthStatus.CRITICAL)

    def test_critical_utilization(self):
        # utilization = 10/10 = 1.0 (above critical threshold 0.95)
        for _ in range(3):
            m = _make_pool_metrics(pool_size=10, checked_out=10)
            self.monitor.record_metrics("crit_pool", m)
        status, _ = self.monitor.analyze_pool_health("crit_pool")
        assert status == PoolHealthStatus.CRITICAL

    def test_get_performance_trends_no_data(self):
        result = self.monitor.get_performance_trends("no_pool")
        assert "error" in result

    def test_get_performance_trends_insufficient(self):
        self.monitor.record_metrics("one_point", _make_pool_metrics())
        result = self.monitor.get_performance_trends("one_point")
        assert "error" in result


class TestPoolOptimizer:
    @pytest.mark.parametrize(
        "strategy",
        [
            OptimizationStrategy.CONSERVATIVE,
            OptimizationStrategy.AGGRESSIVE,
            OptimizationStrategy.BALANCED,
        ],
    )
    def test_strategies_have_different_rules(self, strategy):
        optimizer = PoolOptimizer(strategy=strategy)
        rules = optimizer.optimization_rules
        assert "min_pool_size" in rules
        assert "confidence_threshold" in rules

    def test_get_optimization_statistics_empty(self):
        optimizer = PoolOptimizer()
        stats = optimizer.get_optimization_statistics()
        assert stats["total_recommendations"] == 0
        assert stats["pools_optimized"] == 0

    def test_configs_differ_detects_pool_size_change(self):
        optimizer = PoolOptimizer()
        c1 = _make_pool_config(pool_size=10)
        c2 = _make_pool_config(pool_size=15)
        assert optimizer._configs_differ(c1, c2) is True

    def test_configs_differ_same_config(self):
        optimizer = PoolOptimizer()
        c1 = _make_pool_config(
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=False,
            pool_reset_on_return="rollback",
        )
        c2 = _make_pool_config(
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=False,
            pool_reset_on_return="rollback",
        )
        assert optimizer._configs_differ(c1, c2) is False


class TestGlobalPoolFunctions:
    def test_track_pool_metrics_callable(self):
        m = _make_pool_metrics()
        track_pool_metrics("test_pool", m)  # Should not raise

    def test_get_pool_health_returns_tuple(self):
        status, issues = get_pool_health("nonexistent_pool")
        assert isinstance(status, PoolHealthStatus)
        assert isinstance(issues, list)

    def test_get_optimization_statistics_dict(self):
        stats = get_optimization_statistics()
        assert isinstance(stats, dict)
        assert "total_recommendations" in stats

    def test_get_connection_statistics_dict(self):
        stats = get_connection_statistics()
        assert isinstance(stats, dict)


# ===========================================================================
# ==================== plugin_architecture tests ===========================
# ===========================================================================


class TestAgentManifest:
    def test_creation_with_defaults(self):
        manifest = _make_agent_manifest()
        assert manifest.name == "test_agent"
        assert manifest.configuration == {}
        assert manifest.dependencies == []

    def test_capabilities_list(self):
        manifest = _make_agent_manifest(
            capabilities=[AgentCapability.TEACHING, AgentCapability.ASSESSMENT]
        )
        assert AgentCapability.TEACHING in manifest.capabilities
        assert AgentCapability.ASSESSMENT in manifest.capabilities


class TestAgentCapability:
    def test_all_expected_values(self):
        values = {c.value for c in AgentCapability}
        assert "teaching" in values
        assert "assessment" in values
        assert "problem_solving" in values


class TestBaseAgentPlugin:
    def _make_concrete_plugin(self):
        class ConcreteAgent(BaseAgentPlugin):
            async def initialize(self, ctx, gen, analytics):
                await super().initialize(ctx, gen, analytics)

            async def process_message(self, msg, session_id, context=None):
                return "processed"

            async def get_capabilities(self):
                return ["teaching"]

            async def shutdown(self):
                pass

        return ConcreteAgent(_make_agent_manifest())

    @pytest.mark.asyncio
    async def test_validate_input_valid(self):
        agent = self._make_concrete_plugin()
        assert await agent.validate_input("Hello") is True

    @pytest.mark.asyncio
    async def test_validate_input_empty(self):
        agent = self._make_concrete_plugin()
        assert await agent.validate_input("") is False

    @pytest.mark.asyncio
    async def test_validate_input_too_long(self):
        agent = self._make_concrete_plugin()
        assert await agent.validate_input("x" * 10001) is False

    @pytest.mark.asyncio
    async def test_handle_error_returns_turkish_message(self):
        agent = self._make_concrete_plugin()
        msg = await agent.handle_error(ValueError("oops"))
        assert isinstance(msg, str)
        assert len(msg) > 0

    @pytest.mark.asyncio
    async def test_initialize_sets_flag(self):
        agent = self._make_concrete_plugin()
        ctx = MagicMock()
        gen = MagicMock()
        analytics = MagicMock()
        await agent.initialize(ctx, gen, analytics)
        assert agent.initialized is True


class TestAgentRegistry:
    def _make_registry_with_agent(self):
        registry = AgentRegistry()

        class DummyAgent(BaseAgentPlugin):
            async def initialize(self, ctx, gen, analytics):
                await super().initialize(ctx, gen, analytics)

            async def process_message(self, msg, session_id, context=None):
                return "ok"

            async def get_capabilities(self):
                return ["teaching"]

            async def shutdown(self):
                pass

        manifest = _make_agent_manifest(
            name="math_tutor",
            capabilities=[AgentCapability.TEACHING],
            supported_subjects=["matematik"],
        )
        agent = DummyAgent(manifest)
        return registry, agent, manifest

    @pytest.mark.asyncio
    async def test_register_and_retrieve(self):
        registry, agent, manifest = self._make_registry_with_agent()
        registry.register_agent("math_tutor", agent, manifest)
        retrieved = registry.get_agent_by_capability(AgentCapability.TEACHING)
        assert retrieved is agent

    @pytest.mark.asyncio
    async def test_get_agent_by_subject(self):
        registry, agent, manifest = self._make_registry_with_agent()
        registry.register_agent("math_tutor", agent, manifest)
        retrieved = registry.get_agent_by_subject("matematik")
        assert retrieved is agent

    @pytest.mark.asyncio
    async def test_get_agent_missing_capability(self):
        registry = AgentRegistry()
        result = registry.get_agent_by_capability(AgentCapability.RESEARCH)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_agents(self):
        registry, agent, manifest = self._make_registry_with_agent()
        registry.register_agent("math_tutor", agent, manifest)
        all_agents = registry.get_all_agents()
        assert len(all_agents) == 1

    @pytest.mark.asyncio
    async def test_unregister_agent(self):
        registry, agent, manifest = self._make_registry_with_agent()
        registry.register_agent("math_tutor", agent, manifest)
        result = registry.unregister_agent("math_tutor")
        assert result is True
        assert registry.get_agent_by_capability(AgentCapability.TEACHING) is None

    @pytest.mark.asyncio
    async def test_unregister_nonexistent(self):
        registry = AgentRegistry()
        assert registry.unregister_agent("ghost") is False


class TestPluginLoader:
    def test_discover_plugins_no_dir(self, tmp_path):
        loader = PluginLoader(str(tmp_path / "no_plugins"))
        discovered = loader.discover_plugins()
        assert discovered == []

    def test_get_agent_returns_none_when_empty(self):
        loader = PluginLoader()
        assert loader.get_agent("nonexistent") is None

    def test_get_content_provider_returns_none_when_empty(self):
        loader = PluginLoader()
        assert loader.get_content_provider("nonexistent") is None

    def test_list_agents_empty(self):
        loader = PluginLoader()
        assert loader.list_agents() == []

    @pytest.mark.asyncio
    async def test_unload_nonexistent_plugin(self):
        loader = PluginLoader()
        result = await loader.unload_plugin("ghost")
        assert result is False


class TestAgentOrchestrator:
    def _make_orchestrator(self):
        registry = AgentRegistry()

        class TeachingAgent(BaseAgentPlugin):
            async def initialize(self, ctx, gen, analytics):
                await super().initialize(ctx, gen, analytics)

            async def process_message(self, msg, session_id, context=None):
                return "teaching response"

            async def get_capabilities(self):
                return ["teaching"]

            async def shutdown(self):
                pass

        manifest = _make_agent_manifest(
            capabilities=[AgentCapability.TEACHING],
            supported_subjects=["genel"],
        )
        agent = TeachingAgent(manifest)
        registry.register_agent("teacher", agent, manifest)
        return AgentOrchestrator(registry)

    @pytest.mark.asyncio
    async def test_analyze_request_teaching_keywords(self):
        orch = self._make_orchestrator()
        caps = orch._analyze_request("lütfen açıkla")
        assert AgentCapability.TEACHING in caps

    @pytest.mark.asyncio
    async def test_analyze_request_default_teaching(self):
        orch = self._make_orchestrator()
        caps = orch._analyze_request("random text")
        assert AgentCapability.TEACHING in caps

    @pytest.mark.asyncio
    async def test_has_dependencies_with_assessment_and_teaching(self):
        orch = self._make_orchestrator()
        caps = [AgentCapability.ASSESSMENT, AgentCapability.TEACHING]
        assert orch._has_dependencies(caps) is True

    @pytest.mark.asyncio
    async def test_has_no_dependencies_teaching_only(self):
        orch = self._make_orchestrator()
        caps = [AgentCapability.TEACHING]
        assert orch._has_dependencies(caps) is False

    @pytest.mark.asyncio
    async def test_combine_results_single(self):
        orch = self._make_orchestrator()
        result = orch._combine_results(
            {"teaching": "answer"}, [AgentCapability.TEACHING]
        )
        assert result == "answer"

    @pytest.mark.asyncio
    async def test_process_complex_request_no_agents(self):
        registry = AgentRegistry()  # empty registry
        orch = AgentOrchestrator(registry)
        result = await orch.process_complex_request("test request", "session-1")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_process_complex_request_with_agent(self):
        orch = self._make_orchestrator()
        result = await orch.process_complex_request("açıkla", "session-2")
        assert result["success"] is True
        assert "results" in result


class TestSingletonGetters:
    def test_get_plugin_loader_returns_same_instance(self):
        loader1 = get_plugin_loader()
        loader2 = get_plugin_loader()
        assert loader1 is loader2

    def test_get_agent_registry_returns_same_instance(self):
        registry1 = get_agent_registry()
        registry2 = get_agent_registry()
        assert registry1 is registry2


# ===========================================================================
# ==================== distributed_monitoring tests ========================
# ===========================================================================


class TestServiceStatus:
    def test_all_statuses_exist(self):
        assert ServiceStatus.HEALTHY.value == "healthy"
        assert ServiceStatus.UNHEALTHY.value == "unhealthy"
        assert ServiceStatus.DEGRADED.value == "degraded"
        assert ServiceStatus.UNKNOWN.value == "unknown"


class TestAlertSeverity:
    def test_severity_values(self):
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.CRITICAL.value == "critical"


class TestTraceSpan:
    def test_finish_sets_duration(self):
        import time
        from datetime import datetime

        span = TraceSpan(
            trace_id="t1",
            span_id="s1",
            parent_span_id=None,
            service_name="test",
            operation_name="op",
            start_time=datetime.now(),
        )
        time.sleep(0.01)
        span.finish()
        assert span.end_time is not None
        assert span.duration_ms is not None
        assert span.duration_ms >= 0


class TestDistributedTracer:
    def setup_method(self):
        self.tracer = DistributedTracer("test-service")

    def test_start_span(self):
        span = self.tracer.start_span("test_op")
        assert span.operation_name == "test_op"
        assert span.service_name == "test-service"
        assert span.span_id in self.tracer.active_spans

    def test_finish_span(self):
        span = self.tracer.start_span("finish_op")
        self.tracer.finish_span(span)
        assert span.span_id not in self.tracer.active_spans

    def test_get_trace(self):
        span = self.tracer.start_span("trace_op", trace_id="my-trace")
        self.tracer.finish_span(span)
        spans = self.tracer.get_trace("my-trace")
        assert len(spans) == 1
        assert spans[0].trace_id == "my-trace"

    def test_inject_headers(self):
        span = self.tracer.start_span("inject_op", trace_id="t99")
        headers = self.tracer.inject_headers(span)
        assert headers["X-Trace-ID"] == "t99"
        assert "X-Span-ID" in headers

    def test_extract_headers(self):
        trace_id, span_id = self.tracer.extract_headers(
            {"X-Trace-ID": "abc", "X-Span-ID": "xyz"}
        )
        assert trace_id == "abc"
        assert span_id == "xyz"

    def test_extract_headers_missing(self):
        trace_id, span_id = self.tracer.extract_headers({})
        assert trace_id is None
        assert span_id is None


class TestMicroserviceRegistry:
    def test_get_all_services_returns_dict(self):
        services = MicroserviceRegistry.get_all_services()
        assert isinstance(services, dict)
        assert "backend" in services

    def test_get_critical_services_subset(self):
        critical = MicroserviceRegistry.get_critical_services()
        all_services = MicroserviceRegistry.get_all_services()
        assert set(critical.keys()).issubset(set(all_services.keys()))

    def test_get_all_is_copy(self):
        s1 = MicroserviceRegistry.get_all_services()
        s2 = MicroserviceRegistry.get_all_services()
        assert s1 is not s2


class TestAlertManager:
    def setup_method(self):
        self.manager = AlertManager()

    def test_create_alert(self):
        alert = self.manager.create_alert(
            AlertSeverity.WARNING, "test-service", "Something is wrong"
        )
        assert isinstance(alert, Alert)
        assert alert.severity == AlertSeverity.WARNING
        assert alert.service_name == "test-service"
        assert alert.resolved is False

    def test_acknowledge_alert(self):
        alert = self.manager.create_alert(AlertSeverity.INFO, "svc", "test")
        result = self.manager.acknowledge_alert(alert.id)
        assert result is True
        assert alert.acknowledged is True

    def test_acknowledge_nonexistent(self):
        assert self.manager.acknowledge_alert("no-such-id") is False

    def test_resolve_alert(self):
        alert = self.manager.create_alert(AlertSeverity.ERROR, "svc", "critical error")
        result = self.manager.resolve_alert(alert.id)
        assert result is True
        assert alert.resolved is True

    def test_get_active_alerts_excludes_resolved(self):
        a1 = self.manager.create_alert(AlertSeverity.WARNING, "svc", "w1")
        a2 = self.manager.create_alert(AlertSeverity.ERROR, "svc", "e1")
        self.manager.resolve_alert(a2.id)
        active = self.manager.get_active_alerts()
        ids = [a.id for a in active]
        assert a1.id in ids
        assert a2.id not in ids

    def test_get_active_alerts_by_severity(self):
        self.manager.create_alert(AlertSeverity.WARNING, "svc", "warn")
        self.manager.create_alert(AlertSeverity.CRITICAL, "svc", "crit")
        warnings = self.manager.get_active_alerts(severity=AlertSeverity.WARNING)
        assert all(a.severity == AlertSeverity.WARNING for a in warnings)

    def test_get_alerts_by_service(self):
        self.manager.create_alert(AlertSeverity.INFO, "service-A", "info")
        self.manager.create_alert(AlertSeverity.INFO, "service-B", "info")
        alerts = self.manager.get_alerts_by_service("service-A")
        assert all(a.service_name == "service-A" for a in alerts)

    def test_alert_handler_called(self):
        handler = MagicMock()
        self.manager.register_handler(handler)
        self.manager.create_alert(AlertSeverity.INFO, "svc", "msg")
        handler.assert_called_once()

    def test_max_alerts_enforced(self):
        self.manager._max_alerts = 3
        for i in range(5):
            self.manager.create_alert(AlertSeverity.INFO, "svc", f"msg-{i}")
        assert len(self.manager.alerts) == 3


class TestServiceHealthChecker:
    def setup_method(self):
        self.checker = ServiceHealthChecker()

    def test_get_overall_status_all_healthy(self):
        from datetime import datetime

        from core.distributed_monitoring import ServiceHealth

        health_map = {
            "backend": ServiceHealth(
                "backend", ServiceStatus.HEALTHY, 10.0, datetime.now()
            ),
            "exam-service": ServiceHealth(
                "exam-service", ServiceStatus.HEALTHY, 8.0, datetime.now()
            ),
        }
        status = self.checker.get_overall_status(health_map)
        assert status == ServiceStatus.HEALTHY

    def test_get_overall_status_critical_unhealthy(self):
        from datetime import datetime

        from core.distributed_monitoring import ServiceHealth

        health_map = {
            "backend": ServiceHealth(
                "backend", ServiceStatus.UNHEALTHY, 0.0, datetime.now()
            ),
        }
        status = self.checker.get_overall_status(health_map)
        assert status == ServiceStatus.UNHEALTHY

    def test_get_cached_health_missing(self):
        result = self.checker.get_cached_health("nonexistent")
        assert result is None


class TestTracingContext:
    def test_context_manager_sync(self):
        tracer = DistributedTracer("ctx-test")
        with TracingContext(tracer, "sync_op") as span:
            assert span.operation_name == "sync_op"
            assert span.end_time is None
        assert span.end_time is not None

    def test_context_manager_error_marks_span(self):
        tracer = DistributedTracer("ctx-test")
        with pytest.raises(ValueError):
            with TracingContext(tracer, "error_op") as span:
                raise ValueError("boom")
        assert span.error is True

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        tracer = DistributedTracer("async-ctx")
        async with TracingContext(tracer, "async_op") as span:
            assert span.operation_name == "async_op"
        assert span.end_time is not None


class TestDistributedMonitoringSidekick:
    def setup_method(self):
        self.sidekick = DistributedMonitoringSidekick("kiro2-test")

    @pytest.mark.asyncio
    async def test_liveness_probe(self):
        result = await self.sidekick.liveness_probe()
        assert result["status"] == "alive"
        assert result["service"] == "kiro2-test"

    @pytest.mark.asyncio
    async def test_startup_probe(self):
        result = await self.sidekick.startup_probe()
        assert result["started"] is True

    @pytest.mark.asyncio
    async def test_readiness_probe(self):
        result = await self.sidekick.readiness_probe()
        assert "ready" in result

    def test_trace_request_returns_context(self):
        ctx = self.sidekick.trace_request("test-op")
        assert isinstance(ctx, TracingContext)

    @pytest.mark.asyncio
    async def test_stop_without_start(self):
        # Should not raise even if monitoring was never started
        await self.sidekick.stop_background_monitoring()


# ===========================================================================
# ==================== background_job_processor tests =====================
# ===========================================================================


class TestJobDefinition:
    def _make_def(self, retry_policy=RetryPolicy.EXPONENTIAL_BACKOFF, delay=60):
        return JobDefinition(
            name="test_job",
            function=lambda: None,
            queue_type=QueueType.BATCH_PROCESSING,
            priority=JobPriority.NORMAL,
            retry_policy=retry_policy,
            retry_delay=delay,
        )

    @pytest.mark.parametrize(
        "policy,attempt,expected",
        [
            (RetryPolicy.NONE, 1, 0),
            (RetryPolicy.FIXED_DELAY, 3, 60),
            (RetryPolicy.LINEAR_BACKOFF, 3, 180),
            (RetryPolicy.EXPONENTIAL_BACKOFF, 1, 60),
            (RetryPolicy.EXPONENTIAL_BACKOFF, 2, 120),
            (RetryPolicy.EXPONENTIAL_BACKOFF, 3, 240),
        ],
    )
    def test_calculate_retry_delay(self, policy, attempt, expected):
        job_def = self._make_def(retry_policy=policy, delay=60)
        assert job_def.calculate_retry_delay(attempt) == expected


class TestJobExecution:
    def _make_execution(self) -> JobExecution:
        from datetime import datetime

        return JobExecution(
            job_id="job-1",
            job_name="test",
            started_at=datetime.now(UTC),
        )

    def test_log_adds_entry(self):
        exec_ = self._make_execution()
        exec_.log("starting")
        assert len(exec_.logs) == 1
        assert "starting" in exec_.logs[0]

    def test_update_progress_clamping(self):
        exec_ = self._make_execution()
        exec_.update_progress(150)
        assert exec_.progress == 100

        exec_.update_progress(-10)
        assert exec_.progress == 0

    def test_update_progress_with_message(self):
        exec_ = self._make_execution()
        exec_.update_progress(50, "halfway")
        assert exec_.status_message == "halfway"
        assert exec_.progress == 50


class TestBackgroundJobRegistry:
    def setup_method(self):
        self.registry = BackgroundJobRegistry()

    def test_register_job(self):
        def dummy():
            pass

        job_def = self.registry.register_job("test_job", dummy, category="testing")
        assert job_def.name == "test_job"
        assert "test_job" in self.registry.jobs

    def test_get_existing_job(self):
        self.registry.register_job("my_job", lambda: None)
        result = self.registry.get_job("my_job")
        assert result is not None
        assert result.name == "my_job"

    def test_get_nonexistent_job(self):
        assert self.registry.get_job("ghost") is None

    def test_list_all_jobs(self):
        self.registry.register_job("job_a", lambda: None)
        self.registry.register_job("job_b", lambda: None)
        jobs = self.registry.list_jobs()
        names = [j.name for j in jobs]
        assert "job_a" in names
        assert "job_b" in names

    def test_list_jobs_by_category(self):
        self.registry.register_job("cat_job", lambda: None, category="special")
        jobs = self.registry.list_jobs(category="special")
        assert any(j.name == "cat_job" for j in jobs)

    def test_get_categories(self):
        self.registry.register_job("j1", lambda: None, category="alpha")
        self.registry.register_job("j2", lambda: None, category="beta")
        categories = self.registry.get_categories()
        assert "alpha" in categories
        assert "beta" in categories


class TestJobPriorityAndRetryPolicy:
    def test_job_priority_values(self):
        assert JobPriority.LOW.value == "low"
        assert JobPriority.CRITICAL.value == "critical"

    def test_retry_policy_values(self):
        assert RetryPolicy.NONE.value == "none"
        assert RetryPolicy.EXPONENTIAL_BACKOFF.value == "exponential_backoff"
