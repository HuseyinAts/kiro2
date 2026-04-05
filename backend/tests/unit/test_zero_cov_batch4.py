"""
Unit tests for zero-coverage / low-coverage backend files – Batch 4.

Targets:
  1. core/global_exception_handler.py       (285 stmts, 28%)
  2. core/database_optimizer.py             (293 stmts, 27%)
  3. services/sequential_reasoning_service.py (240 stmts, 15%)
  4. services/ogretmen_service.py           (233 stmts, 11%)
  5. services/revolutionary_features_service.py (302 stmts, 31%)

All heavy imports are stubbed via sys.modules BEFORE the modules are loaded.
Modules are loaded with importlib.util to avoid cross-file contamination.
"""

import importlib.util
import os
import sys
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Stale-stub cleanup
# ---------------------------------------------------------------------------
_STALE_PREFIXES = (
    "sqlalchemy",
    "fastapi",
    "starlette",
    "pydantic",
    "models.reasoning_models",
    "models.database",
    "models",
    "services.llm",
    "services.reasoning",
    "services.irt_calibration_service",
    "services.user_service",
    "core.unified_config",
    "core.osym_exam_engine",
    "core.quality_gates",
    "algorithms.turkish_zpd_maarif_system",
)
for _key in list(sys.modules):
    for _pfx in _STALE_PREFIXES:
        if _key == _pfx or _key.startswith(_pfx + "."):
            if isinstance(sys.modules[_key], MagicMock):
                del sys.modules[_key]
            break


# ---------------------------------------------------------------------------
# Helper: load a module by file path
# ---------------------------------------------------------------------------
def _load(name: str, rel_path: str):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(_BACKEND, rel_path)
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ===========================================================================
# FILE 1: core/global_exception_handler.py
# ===========================================================================


class TestGlobalExceptionHandler:
    """Tests for core/global_exception_handler.py"""

    @pytest.fixture(autouse=True)
    def _stub_and_load(self):
        """Stub heavy deps and load the module fresh for each test."""
        # Stub fastapi / starlette / pydantic
        _fa = MagicMock()
        _fa.HTTPException = type(
            "HTTPException", (Exception,), {"status_code": 500, "detail": ""}
        )
        _fa.Request = MagicMock()
        _fa.status = MagicMock()
        _fa.status.HTTP_400_BAD_REQUEST = 400
        _fa.status.HTTP_401_UNAUTHORIZED = 401
        _fa.status.HTTP_403_FORBIDDEN = 403
        _fa.status.HTTP_404_NOT_FOUND = 404
        _fa.status.HTTP_408_REQUEST_TIMEOUT = 408
        _fa.status.HTTP_422_UNPROCESSABLE_ENTITY = 422
        _fa.status.HTTP_429_TOO_MANY_REQUESTS = 429
        _fa.status.HTTP_500_INTERNAL_SERVER_ERROR = 500
        _fa.status.HTTP_502_BAD_GATEWAY = 502
        _fa.status.HTTP_503_SERVICE_UNAVAILABLE = 503
        _fa.status.HTTP_507_INSUFFICIENT_STORAGE = 507

        _fa_exc = MagicMock()
        _fa_exc.RequestValidationError = type(
            "RequestValidationError", (Exception,), {}
        )

        _starlette_exc = MagicMock()
        _starlette_exc.HTTPException = type(
            "StarletteHTTPException", (Exception,), {"status_code": 500}
        )

        _fa_resp = MagicMock()
        _fa_resp.JSONResponse = MagicMock(
            side_effect=lambda content, status_code: {
                "content": content,
                "status_code": status_code,
            }
        )

        _pydantic = MagicMock()
        _pydantic.ValidationError = type("PydanticValidationError", (Exception,), {})

        sys.modules.setdefault("fastapi", _fa)
        sys.modules.setdefault("fastapi.exceptions", _fa_exc)
        sys.modules.setdefault("fastapi.responses", _fa_resp)
        sys.modules.setdefault("starlette", MagicMock())
        sys.modules.setdefault("starlette.exceptions", _starlette_exc)
        sys.modules.setdefault("pydantic", _pydantic)

        # Load core.exceptions first (real module)
        _exc_mod = _load("core.exceptions", "core/exceptions.py")
        sys.modules["core.exceptions"] = _exc_mod

        # Stub core.response_models
        _rm = MagicMock()
        _error_detail_cls = MagicMock()
        _rm.ErrorDetail = _error_detail_cls
        _builder = MagicMock()
        _builder.error.return_value = _builder
        _builder.with_errors.return_value = _builder
        _builder.with_meta.return_value = _builder
        _builder.with_data.return_value = _builder
        _built = MagicMock()
        _built.model_dump.return_value = {"success": False, "message": "error"}
        _built.dict.return_value = {"success": False}
        _builder.build.return_value = _built
        _rm.ResponseBuilder.return_value = _builder
        sys.modules.setdefault("core.response_models", _rm)

        # Stub unified_config
        _ucfg = MagicMock()
        _ucfg.get_unified_config.return_value = MagicMock(
            debug=False, app_version="1.0.0"
        )
        sys.modules["core.unified_config"] = _ucfg

        self.exc_mod = _exc_mod
        self.mod = _load(
            "core.global_exception_handler", "core/global_exception_handler.py"
        )
        yield

    # ---- ErrorTracker ----

    def test_error_tracker_record_error_increments_count(self):
        tracker = self.mod.ErrorTracker()
        ctx = MagicMock()
        ctx.user_role = "student"
        tracker.record_error(
            "ValueError", "/api/test", self.exc_mod.ErrorSeverity.MEDIUM, ctx
        )
        assert tracker.error_counts.get("ValueError:/api/test", 0) == 1

    def test_error_tracker_record_error_twice(self):
        tracker = self.mod.ErrorTracker()
        ctx = MagicMock()
        ctx.user_role = "admin"
        for _ in range(3):
            tracker.record_error(
                "DatabaseError", "/api/db", self.exc_mod.ErrorSeverity.HIGH, ctx
            )
        assert tracker.error_counts["DatabaseError:/api/db"] == 3

    def test_error_tracker_get_error_rate_zero_for_unknown(self):
        tracker = self.mod.ErrorTracker()
        rate = tracker.get_error_rate("UnknownError", "/unknown")
        assert rate == 0.0

    def test_error_tracker_get_error_rate_returns_float(self):
        tracker = self.mod.ErrorTracker()
        ctx = MagicMock()
        ctx.user_role = "student"
        tracker.record_error("AuthError", "/login", self.exc_mod.ErrorSeverity.LOW, ctx)
        rate = tracker.get_error_rate("AuthError", "/login", window_minutes=60)
        assert isinstance(rate, float)
        assert rate >= 0.0

    def test_circuit_breaker_initially_closed(self):
        tracker = self.mod.ErrorTracker()
        assert not tracker.is_circuit_breaker_open("/api/test")

    def test_circuit_breaker_opens_after_threshold(self):
        tracker = self.mod.ErrorTracker()
        ctx = MagicMock()
        ctx.user_role = "student"
        # Trigger 10 HIGH severity errors on same endpoint
        for _ in range(10):
            tracker.record_error(
                "DatabaseError", "/api/data", self.exc_mod.ErrorSeverity.HIGH, ctx
            )
        assert tracker.is_circuit_breaker_open("/api/data")

    def test_circuit_breaker_remains_closed_for_low_severity(self):
        tracker = self.mod.ErrorTracker()
        ctx = MagicMock()
        ctx.user_role = "student"
        for _ in range(15):
            tracker.record_error(
                "NotFound", "/api/item", self.exc_mod.ErrorSeverity.LOW, ctx
            )
        assert not tracker.is_circuit_breaker_open("/api/item")

    def test_circuit_breaker_half_open_after_timeout(self):
        tracker = self.mod.ErrorTracker()
        # Manually inject open state with old timestamp
        tracker.circuit_breakers["/api/old"] = {
            "state": "open",
            "error_count": 15,
            "last_failure": datetime.now() - timedelta(seconds=600),
            "opened_at": datetime.now() - timedelta(seconds=600),
            "timeout": 300,
        }
        # Should transition to half_open → returns False (not open)
        result = tracker.is_circuit_breaker_open("/api/old")
        assert not result
        assert tracker.circuit_breakers["/api/old"]["state"] == "half_open"

    def test_get_error_statistics_structure(self):
        tracker = self.mod.ErrorTracker()
        ctx = MagicMock()
        ctx.user_role = "teacher"
        tracker.record_error(
            "ValueError", "/endpoint", self.exc_mod.ErrorSeverity.MEDIUM, ctx
        )
        stats = tracker.get_error_statistics()
        assert "total_error_types" in stats
        assert "recent_errors_24h" in stats
        assert "circuit_breaker_states" in stats
        assert "top_errors" in stats

    # ---- ErrorContext ----

    def test_error_context_from_request(self):
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url = MagicMock()
        mock_request.url.__str__ = lambda self: "http://localhost/api/v1/test"
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.state = MagicMock()
        mock_request.state.request_id = "req-001"
        mock_request.state.correlation_id = "corr-001"
        mock_request.state.user_id = "42"
        mock_request.state.user_role = "student"
        mock_request.state.session_id = "sess-1"
        mock_request.state.api_version = "v1"
        mock_request.state.processing_time = 15.0

        ctx = self.mod.ErrorContext.from_request(mock_request)
        assert ctx.request_method == "GET"
        assert ctx.user_id == "42"
        assert ctx.client_ip == "127.0.0.1"
        assert ctx.processing_time_ms == 15.0

    # ---- ExceptionHandlerConfig ----

    def test_exception_handler_config_defaults(self):
        cfg = self.mod.ExceptionHandlerConfig()
        assert cfg.mode == self.mod.HandlerMode.GRACEFUL
        assert cfg.enable_error_recovery is True
        assert cfg.circuit_breaker_threshold == 10
        assert "max_retries" in cfg.retry_policy

    def test_exception_handler_config_custom(self):
        cfg = self.mod.ExceptionHandlerConfig(
            mode=self.mod.HandlerMode.STRICT,
            enable_error_recovery=False,
            max_error_rate_per_minute=50,
        )
        assert cfg.mode == self.mod.HandlerMode.STRICT
        assert cfg.enable_error_recovery is False
        assert cfg.max_error_rate_per_minute == 50

    # ---- GlobalExceptionHandler ----

    def test_handler_init_creates_tracker(self):
        handler = self.mod.GlobalExceptionHandler()
        assert isinstance(handler.error_tracker, self.mod.ErrorTracker)
        assert handler.config is not None

    def test_handler_register_recovery_function(self):
        handler = self.mod.GlobalExceptionHandler()

        async def my_recovery(err, ctx):
            return {"recovered": True}

        handler.register_recovery_function(ValueError, my_recovery)
        assert ValueError in handler.recovery_functions

    def test_handler_register_notification_callback(self):
        handler = self.mod.GlobalExceptionHandler()
        cb = MagicMock()
        handler.register_notification_callback(cb)
        assert cb in handler.notification_callbacks

    def test_classify_exception_value_error(self):
        handler = self.mod.GlobalExceptionHandler()
        exc = ValueError("bad value")
        info = handler._classify_exception(exc)
        assert info["error_code"] == "VALUE_ERROR"
        assert info["http_status"] == 400

    def test_classify_exception_key_error(self):
        handler = self.mod.GlobalExceptionHandler()
        exc = KeyError("missing")
        info = handler._classify_exception(exc)
        assert info["http_status"] == 400
        assert info["error_code"] == "KEY_ERROR"

    def test_classify_exception_memory_error(self):
        handler = self.mod.GlobalExceptionHandler()
        exc = MemoryError()
        info = handler._classify_exception(exc)
        assert info["severity"] == self.exc_mod.ErrorSeverity.CRITICAL
        assert info["http_status"] == 507

    def test_classify_exception_not_found(self):
        handler = self.mod.GlobalExceptionHandler()
        exc = self.exc_mod.NotFoundError("Not found")
        info = handler._classify_exception(exc)
        assert info["http_status"] == 404

    def test_classify_exception_authentication(self):
        handler = self.mod.GlobalExceptionHandler()
        exc = self.exc_mod.AuthenticationError()
        info = handler._classify_exception(exc)
        assert info["http_status"] == 401

    def test_classify_exception_security(self):
        handler = self.mod.GlobalExceptionHandler()
        exc = self.exc_mod.SecurityError("intrusion detected")
        info = handler._classify_exception(exc)
        assert info["severity"] == self.exc_mod.ErrorSeverity.CRITICAL
        assert info["http_status"] == 403

    def test_classify_enhanced_service_error(self):
        handler = self.mod.GlobalExceptionHandler()
        exc = self.exc_mod.EnhancedServiceError(
            "service down",
            severity=self.exc_mod.ErrorSeverity.HIGH,
            retry_after=30,
            user_message="Servis geçici olarak kapalı",
        )
        info = handler._classify_exception(exc)
        assert info["severity"] == self.exc_mod.ErrorSeverity.HIGH
        assert info["is_retryable"] is True

    @pytest.mark.asyncio
    async def test_attempt_recovery_with_matching_function(self):
        handler = self.mod.GlobalExceptionHandler()
        ctx = MagicMock()

        async def recover(err, c):
            return {"data": "recovered"}

        handler.recovery_functions[ValueError] = recover
        result = await handler._attempt_recovery(ValueError("oops"), ctx)
        assert result == {"data": "recovered"}

    @pytest.mark.asyncio
    async def test_attempt_recovery_no_match_returns_none(self):
        handler = self.mod.GlobalExceptionHandler()
        ctx = MagicMock()
        # No recovery for TypeError
        result = await handler._attempt_recovery(TypeError("type issue"), ctx)
        assert result is None

    @pytest.mark.asyncio
    async def test_log_exception_critical_calls_logger(self):
        handler = self.mod.GlobalExceptionHandler()
        mock_logger = MagicMock()
        handler.logger = mock_logger
        ctx = MagicMock()
        ctx.request_id = "req-x"
        ctx.correlation_id = "corr-x"
        ctx.timestamp = datetime.now()
        ctx.request_method = "POST"
        ctx.request_url = "http://test"
        ctx.user_id = "1"
        ctx.user_role = "admin"
        ctx.client_ip = "127.0.0.1"
        ctx.user_agent = "test-agent"
        error_info = {
            "error_code": "MEMORY_ERROR",
            "severity": self.exc_mod.ErrorSeverity.CRITICAL,
        }
        await handler._log_exception(MemoryError(), ctx, error_info)
        mock_logger.critical.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notifications_async_callback(self):
        handler = self.mod.GlobalExceptionHandler()
        handler.config.enable_error_notification = True
        received = []

        async def async_cb(data):
            received.append(data)

        handler.register_notification_callback(async_cb)
        ctx = MagicMock()
        ctx.request_id = "req-notif"
        error_info = {"severity": self.exc_mod.ErrorSeverity.CRITICAL}
        await handler._send_error_notifications(ValueError("x"), ctx, error_info)
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_send_notifications_sync_callback(self):
        handler = self.mod.GlobalExceptionHandler()
        received = []

        def sync_cb(data):
            received.append(data)

        handler.register_notification_callback(sync_cb)
        ctx = MagicMock()
        ctx.request_id = "req-sync"
        error_info = {}
        await handler._send_error_notifications(ValueError("x"), ctx, error_info)
        assert len(received) == 1

    def test_get_endpoint_identifier(self):
        handler = self.mod.GlobalExceptionHandler()
        req = MagicMock()
        req.method = "DELETE"
        req.url = MagicMock()
        req.url.path = "/api/v1/users/5"
        ident = handler._get_endpoint_identifier(req)
        assert ident == "DELETE:/api/v1/users/5"

    def test_get_error_details_retryable(self):
        handler = self.mod.GlobalExceptionHandler()
        exc = self.exc_mod.DatabaseError("db down", operation="read")
        error_info = {
            "is_retryable": True,
            "expose_details": True,
            "severity": self.exc_mod.ErrorSeverity.HIGH,
        }
        ctx = MagicMock()
        ctx.request_method = "GET"
        ctx.request_url = "http://localhost/api"
        ctx.timestamp = datetime.now()
        details = handler._get_error_details(exc, error_info, ctx)
        assert details is not None
        assert details["retryable"] is True
        assert "max_retries" in details

    def test_setup_global_exception_handlers(self):
        mock_app = MagicMock()
        handler = self.mod.setup_global_exception_handlers(mock_app)
        assert isinstance(handler, self.mod.GlobalExceptionHandler)
        assert mock_app.add_exception_handler.called

    # ---- Utility functions ----

    def test_get_error_handler_no_state(self):
        mock_app = MagicMock()
        mock_app.state = MagicMock(spec=[])  # no global_exception_handler attr
        result = self.mod.get_error_handler(mock_app)
        assert result is None

    @pytest.mark.asyncio
    async def test_handle_with_recovery_success_sync(self):
        def my_op(x):
            return x * 2

        result = await self.mod.handle_with_recovery(my_op, 5)
        assert result == 10

    @pytest.mark.asyncio
    async def test_handle_with_recovery_success_async(self):
        async def my_async_op(x):
            return x + 1

        result = await self.mod.handle_with_recovery(my_async_op, 10)
        assert result == 11

    @pytest.mark.asyncio
    async def test_handle_with_recovery_no_retry_on_validation(self):
        exc_mod = self.exc_mod
        call_count = [0]

        def failing_op():
            call_count[0] += 1
            raise exc_mod.ValidationError("invalid")

        with pytest.raises(exc_mod.ValidationError):
            await self.mod.handle_with_recovery(failing_op, max_retries=3, base_delay=0)
        # Should NOT retry for ValidationError
        assert call_count[0] == 1

    @pytest.mark.asyncio
    async def test_handle_with_recovery_retries_generic(self):
        call_count = [0]

        async def flaky():
            call_count[0] += 1
            if call_count[0] < 3:
                raise RuntimeError("transient")
            return "ok"

        result = await self.mod.handle_with_recovery(flaky, max_retries=3, base_delay=0)
        assert result == "ok"
        assert call_count[0] == 3

    @pytest.mark.asyncio
    async def test_error_context_manager_reraises(self):
        with pytest.raises(ValueError):
            async with self.mod.error_context("corr-123"):
                raise ValueError("context error")


# ===========================================================================
# FILE 2: core/database_optimizer.py
# ===========================================================================


class TestDatabaseOptimizer:
    """Tests for core/database_optimizer.py"""

    @pytest.fixture(autouse=True)
    def _stub_and_load(self):
        _sa = MagicMock()
        _sa.func = MagicMock()
        _sa.select = MagicMock(return_value=MagicMock())
        _sa.text = MagicMock(side_effect=lambda s: s)

        _sa_ext_async = MagicMock()
        _sa_ext_async.AsyncEngine = MagicMock()
        _sa_ext_async.AsyncSession = MagicMock()
        _sa_ext_async.create_async_engine = MagicMock(return_value=MagicMock())

        _sa_orm = MagicMock()
        _sa_pool = MagicMock()
        _sa_pool.QueuePool = MagicMock()

        sys.modules.setdefault("sqlalchemy", _sa)
        sys.modules.setdefault("sqlalchemy.ext", MagicMock())
        sys.modules.setdefault("sqlalchemy.ext.asyncio", _sa_ext_async)
        sys.modules.setdefault("sqlalchemy.orm", _sa_orm)
        sys.modules.setdefault("sqlalchemy.pool", _sa_pool)

        self.mod = _load("core.database_optimizer", "core/database_optimizer.py")

        # database_optimizer.py imports `select`, `func`, `text`, `or_` directly from
        # the real sqlalchemy (already in sys.modules before stubs could intercept).
        # Patch them on the loaded module object so QueryBuilder tests don't hit real SA.
        _mock_query = MagicMock()
        _mock_query.where.return_value = _mock_query
        _mock_query.group_by.return_value = _mock_query
        _mock_query.offset.return_value = _mock_query
        _mock_query.limit.return_value = _mock_query
        _mock_query.options.return_value = _mock_query
        _mock_query.order_by.return_value = _mock_query
        self.mod.select = MagicMock(return_value=_mock_query)
        self.mod.func = MagicMock()
        self.mod.text = MagicMock(side_effect=lambda s: s)
        # `or_` is imported inside the function body — patch it on sqlalchemy module
        import sqlalchemy as _real_sa

        self._orig_sa_or_ = getattr(_real_sa, "or_", None)
        _real_sa.or_ = MagicMock(return_value=MagicMock())
        yield
        # Restore
        if self._orig_sa_or_ is not None:
            _real_sa.or_ = self._orig_sa_or_

    # ---- QueryOptimizer ----

    def test_query_optimizer_init(self):
        opt = self.mod.QueryOptimizer()
        assert opt.query_stats == {}
        assert opt.slow_query_threshold == 1.0

    def test_log_query_performance_fast_query(self):
        opt = self.mod.QueryOptimizer()
        opt.log_query_performance("test_query", 0.05, "SELECT 1")
        stats = opt.query_stats["test_query"]
        assert stats["total_executions"] == 1
        assert stats["slow_queries"] == 0
        assert stats["avg_time"] == pytest.approx(0.05)

    def test_log_query_performance_slow_query(self):
        opt = self.mod.QueryOptimizer()
        opt.log_query_performance("slow_q", 2.5, "SELECT * FROM big_table")
        assert opt.query_stats["slow_q"]["slow_queries"] == 1

    def test_log_query_performance_accumulates(self):
        opt = self.mod.QueryOptimizer()
        opt.log_query_performance("q1", 0.1, "SELECT 1")
        opt.log_query_performance("q1", 0.3, "SELECT 2")
        stats = opt.query_stats["q1"]
        assert stats["total_executions"] == 2
        assert stats["avg_time"] == pytest.approx(0.2)
        assert stats["max_time"] == pytest.approx(0.3)

    def test_get_performance_stats_returns_copy(self):
        opt = self.mod.QueryOptimizer()
        opt.log_query_performance("q_test", 0.5, "SELECT id FROM users")
        stats = opt.get_performance_stats()
        assert "q_test" in stats
        # The copy() is a shallow copy — top-level keys are independent
        stats["new_key"] = "injected"
        assert "new_key" not in opt.query_stats
        assert "q_test" in opt.query_stats

    # ---- ConnectionPoolManager ----

    def test_connection_pool_manager_init(self):
        mgr = self.mod.ConnectionPoolManager()
        assert "active_connections" in mgr.pool_stats
        assert mgr.pool_stats["connection_errors"] == 0

    @pytest.mark.asyncio
    async def test_get_pool_status_success(self):
        mgr = self.mod.ConnectionPoolManager()
        mock_engine = MagicMock()
        mock_pool = MagicMock()
        mock_pool.size.return_value = 10
        mock_pool.checkedin.return_value = 8
        mock_pool.checkedout.return_value = 2
        mock_pool.overflow.return_value = 0
        mock_pool.invalid.return_value = 0
        mock_engine.pool = mock_pool

        result = await mgr.get_pool_status(mock_engine)
        assert result["size"] == 10
        assert result["checked_in"] == 8
        assert result["checked_out"] == 2

    @pytest.mark.asyncio
    async def test_get_pool_status_error_returns_empty(self):
        mgr = self.mod.ConnectionPoolManager()

        # Make pool.size() raise so the try/except path is hit
        class _BrokenPool:
            def size(self):
                raise RuntimeError("pool error")

        mock_engine = MagicMock()
        mock_engine.pool = _BrokenPool()
        result = await mgr.get_pool_status(mock_engine)
        assert result == {}

    # ---- TurkishQueryOptimizer ----

    def test_optimize_search_query_single_column(self):
        q = self.mod.TurkishQueryOptimizer.optimize_search_query(
            "istanbul", ["city"], "users"
        )
        assert "istanbul" not in q.lower()  # Term is a param, not inline
        assert "FROM users" in q
        assert "relevance_score" in q

    def test_optimize_search_query_multiple_columns(self):
        q = self.mod.TurkishQueryOptimizer.optimize_search_query(
            "test", ["name", "description"], "products"
        )
        assert "name" in q
        assert "description" in q
        assert "FROM products" in q

    def test_paginate_query_offset_calculation(self):
        base = "SELECT * FROM users ORDER BY id"
        result = self.mod.TurkishQueryOptimizer.paginate_query(
            base, page=3, page_size=10
        )
        assert "LIMIT 10" in result
        assert "OFFSET 20" in result

    def test_paginate_query_first_page(self):
        base = "SELECT * FROM items"
        result = self.mod.TurkishQueryOptimizer.paginate_query(
            base, page=1, page_size=25
        )
        assert "LIMIT 25" in result
        assert "OFFSET 0" in result

    # ---- QueryBuilder ----
    # QueryBuilder.build_search_query / build_analytics_query call sqlalchemy.select()
    # directly. We patch the `select` name inside the loaded module to avoid the real
    # SQLAlchemy coercion layer rejecting MagicMock column arguments.

    def test_query_builder_build_search_query_no_search_term(self):
        mock_select = MagicMock(return_value=MagicMock())
        mod_name = self.mod.__name__
        with patch.object(self.mod, "select", mock_select):
            mock_model = MagicMock()
            q = self.mod.QueryBuilder.build_search_query(
                mock_model, "", ["name"], filters=None
            )
        # With empty search_term, no OR conditions added; select called once
        assert q is not None
        mock_select.assert_called_once_with(mock_model)

    def test_query_builder_build_search_query_with_filters(self):
        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        mock_select = MagicMock(return_value=mock_query)
        with patch.object(self.mod, "select", mock_select):
            mock_model = MagicMock()
            q = self.mod.QueryBuilder.build_search_query(
                mock_model,
                "test",
                ["name"],
                filters={"status": "active"},
            )
        assert q is not None

    def test_query_builder_build_analytics_query_with_dates(self):
        # Model attributes used in >= / <= comparisons need comparison support
        class _CmpCol:
            def __ge__(self, other):
                return MagicMock()

            def __le__(self, other):
                return MagicMock()

            def __hash__(self):
                return id(self)

        class _FakeModel:
            created_at = _CmpCol()

        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        mock_select = MagicMock(return_value=mock_query)
        with patch.object(self.mod, "select", mock_select):
            q = self.mod.QueryBuilder.build_analytics_query(
                _FakeModel,
                "created_at",
                start_date="2026-01-01",
                end_date="2026-12-31",
            )
        assert q is not None

    def test_query_builder_build_analytics_query_no_dates(self):
        mock_select = MagicMock(return_value=MagicMock())
        with patch.object(self.mod, "select", mock_select):
            mock_model = MagicMock()
            q = self.mod.QueryBuilder.build_analytics_query(mock_model, "date")
        assert q is not None

    # ---- DatabaseOptimizer ----

    def test_database_optimizer_init(self):
        opt = self.mod.DatabaseOptimizer("postgresql+asyncpg://user:pass@localhost/db")
        assert opt.database_url == "postgresql+asyncpg://user:pass@localhost/db"
        assert opt.engine is None
        assert "total_queries" in opt.stats

    @pytest.mark.asyncio
    async def test_database_optimizer_close_no_engine(self):
        opt = self.mod.DatabaseOptimizer("postgresql+asyncpg://u:p@h/d")
        # Should not raise even with no engine
        await opt.close()

    @pytest.mark.asyncio
    async def test_database_optimizer_get_session_no_factory_raises(self):
        opt = self.mod.DatabaseOptimizer("postgresql+asyncpg://u:p@h/d")
        with pytest.raises(RuntimeError, match="not initialized"):
            await opt.get_session()

    @pytest.mark.asyncio
    async def test_database_optimizer_get_connection_stats_no_engine(self):
        opt = self.mod.DatabaseOptimizer("postgresql+asyncpg://u:p@h/d")
        stats = await opt.get_connection_stats()
        assert stats == {}

    @pytest.mark.asyncio
    async def test_database_optimizer_get_connection_stats_with_engine(self):
        opt = self.mod.DatabaseOptimizer("postgresql+asyncpg://u:p@h/d")
        mock_pool = MagicMock()
        mock_pool.size.return_value = 20
        mock_pool.checkedin.return_value = 15
        mock_pool.checkedout.return_value = 5
        mock_pool.overflow.return_value = 0
        mock_pool.invalid.return_value = 0
        opt.engine = MagicMock()
        opt.engine.pool = mock_pool
        stats = await opt.get_connection_stats()
        assert stats["pool_size"] == 20

    # ---- INDEX_RECOMMENDATIONS ----

    def test_index_recommendations_keys(self):
        recs = self.mod.INDEX_RECOMMENDATIONS
        assert "users" in recs
        assert "exams" in recs
        assert "questions" in recs
        assert len(recs["users"]) >= 3

    def test_index_recommendations_are_valid_sql(self):
        recs = self.mod.INDEX_RECOMMENDATIONS
        for table, indexes in recs.items():
            for idx in indexes:
                assert idx.startswith("CREATE INDEX")

    # ---- module-level instances ----

    def test_global_instances_exist(self):
        assert self.mod.query_optimizer is not None
        assert self.mod.connection_pool_manager is not None
        assert self.mod.query_builder is not None


# ===========================================================================
# FILE 3: services/sequential_reasoning_service.py
# ===========================================================================


class TestSequentialReasoningService:
    """Tests for services/sequential_reasoning_service.py"""

    @pytest.fixture(autouse=True)
    def _stub_and_load(self):
        # Stub all heavy deps
        _sa = MagicMock()
        _sa.select = MagicMock(return_value=MagicMock())
        _sa.delete = MagicMock(return_value=MagicMock())
        sys.modules.setdefault("sqlalchemy", _sa)
        sys.modules.setdefault("sqlalchemy.ext", MagicMock())
        sys.modules.setdefault("sqlalchemy.ext.asyncio", MagicMock())
        sys.modules.setdefault("sqlalchemy.orm", MagicMock())

        # Models stub
        _rm = MagicMock()
        _rm.ReasoningSessionStatus = MagicMock()
        _rm.ReasoningSessionStatus.IN_PROGRESS = "in_progress"
        _rm.ReasoningSessionStatus.COMPLETED = "completed"
        _rm.ReasoningSessionStatus.FAILED = "failed"
        _rm.ReasoningStepTypeEnum = MagicMock()
        _rm.ReasoningStepTypeEnum.INFERENCE = "inference"
        _rm.ReasoningStepTypeEnum.CALCULATION = "calculation"
        _rm.ReasoningStepTypeEnum.__call__ = lambda self, v: v
        _rm.LLMProviderEnum = MagicMock()
        _rm.LLMProviderEnum.GEMINI = "gemini"
        _rm.LLMProviderEnum.__call__ = lambda self, v: v

        # Mock ReasoningSession and ReasoningStep constructors
        def _make_session(**kwargs):
            s = MagicMock()
            for k, v in kwargs.items():
                setattr(s, k, v)
            s.id = "session-uuid-1"
            s.steps = []
            s.sub_problems = []
            s.to_dict.return_value = {
                "id": "session-uuid-1",
                "problem": kwargs.get("problem", ""),
            }
            return s

        def _make_step(**kwargs):
            st = MagicMock()
            for k, v in kwargs.items():
                setattr(st, k, v)
            st.to_dict.return_value = kwargs
            return st

        def _make_cache(**kwargs):
            c = MagicMock()
            for k, v in kwargs.items():
                setattr(c, k, v)
            return c

        _rm.ReasoningSession = MagicMock(side_effect=_make_session)
        _rm.ReasoningStep = MagicMock(side_effect=_make_step)
        _rm.ReasoningCache = MagicMock(side_effect=_make_cache)

        # Use a descriptor that supports comparison operators so expressions like
        # `ReasoningCache.expires_at > datetime.now()` return a MagicMock (not TypeError).
        class _CmpCol:
            """Minimal column-like that supports all comparison operators."""

            def __eq__(self, other):
                return MagicMock()

            def __ne__(self, other):
                return MagicMock()

            def __gt__(self, other):
                return MagicMock()

            def __lt__(self, other):
                return MagicMock()

            def __ge__(self, other):
                return MagicMock()

            def __le__(self, other):
                return MagicMock()

            def __hash__(self):
                return id(self)

        _rm.ReasoningCache.problem_hash = _CmpCol()
        _rm.ReasoningCache.expires_at = _CmpCol()
        sys.modules["models.reasoning_models"] = _rm

        # LLM stubs
        _ensemble = MagicMock()
        _ensemble.MultiLLMEnsembleManager = MagicMock()
        sys.modules["services.llm.ensemble_manager"] = _ensemble

        _llm_cfg = MagicMock()
        _llm_cfg.LLMProvider = MagicMock()
        _llm_cfg.LLMProvider.GEMINI = "gemini"
        _llm_cfg.LLMCapability = MagicMock()
        _llm_cfg.LLMCapability.SEQUENTIAL_THINKING = "sequential_thinking"
        sys.modules["services.llm.multi_llm_config"] = _llm_cfg

        # Math/logic stubs
        _math_svc = MagicMock()
        _math_verifier = MagicMock()
        _math_verifier.sympy_available = False
        _math_verifier.detect_problem_type = MagicMock(return_value=None)
        _math_verifier.verify = AsyncMock(
            return_value=MagicMock(
                is_correct=True, confidence=0.9, message="OK", details={}
            )
        )
        _math_svc.get_math_verification_service.return_value = _math_verifier
        _math_svc.MathVerificationService = MagicMock
        _math_svc.MathProblemType = MagicMock()
        _math_svc.MathProblemType.ALGEBRA = "algebra"
        _math_svc.MathProblemType.CALCULUS = "calculus"
        _math_svc.MathProblemType.GEOMETRY = "geometry"
        sys.modules["services.reasoning.math_verification_service"] = _math_svc

        _logic_svc = MagicMock()
        _logic_validator = MagicMock()
        _logic_validator.check_consistency = AsyncMock(
            return_value=MagicMock(
                is_consistent=True, conflicts=[], warnings=[], details={}
            )
        )
        _logic_validator.detect_circular_reasoning = AsyncMock(
            return_value=MagicMock(
                has_circular_reasoning=False, cycles=[], explanation=""
            )
        )
        _logic_validator.track_assumptions = AsyncMock(return_value=[])
        _logic_svc.get_logic_validation_service.return_value = _logic_validator
        _logic_svc.LogicValidationService = MagicMock
        sys.modules["services.reasoning.logic_validation_service"] = _logic_svc

        _dep_graph = MagicMock()
        _graph_inst = MagicMock()
        _graph_inst.topological_sort.return_value = []
        _dep_graph.DependencyGraph.return_value = _graph_inst
        sys.modules["core.quality_gates.dependency_graph"] = _dep_graph
        sys.modules.setdefault("core.quality_gates", MagicMock())

        self.mod = _load(
            "services.sequential_reasoning_service",
            "services/sequential_reasoning_service.py",
        )
        self._rm = _rm
        self._logic_validator = _logic_validator
        self._math_verifier = _math_verifier

        # sequential_reasoning_service.py imports `select`, `delete`, `selectinload`
        # from the real sqlalchemy/sqlalchemy.orm that are already in sys.modules.
        # Patch them on the loaded module so DB-touching tests don't hit real SA coercion.
        _mock_stmt = MagicMock()
        _mock_stmt.where.return_value = _mock_stmt
        _mock_stmt.options.return_value = _mock_stmt
        _mock_stmt.order_by.return_value = _mock_stmt
        _mock_stmt.limit.return_value = _mock_stmt
        self.mod.select = MagicMock(return_value=_mock_stmt)
        self.mod.delete = MagicMock(return_value=_mock_stmt)
        self.mod.selectinload = MagicMock(return_value=MagicMock())
        yield

    def _make_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        # execute returns an object with scalar_one_or_none
        exec_result = MagicMock()
        exec_result.scalar_one_or_none.return_value = None
        exec_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=exec_result)
        return db

    def test_service_init_defaults(self):
        db = self._make_db()
        svc = self.mod.SequentialReasoningService(db)
        assert svc.enable_cache is True
        assert svc.enable_ensemble is True
        assert svc.enable_math_verification is True
        assert svc.enable_logic_validation is True

    def test_service_init_disabled(self):
        db = self._make_db()
        svc = self.mod.SequentialReasoningService(
            db,
            enable_cache=False,
            enable_ensemble=False,
            enable_math_verification=False,
            enable_logic_validation=False,
        )
        assert svc.enable_cache is False
        assert svc._math_verifier is None
        assert svc._logic_validator is None

    def test_hash_problem_deterministic(self):
        db = self._make_db()
        svc = self.mod.SequentialReasoningService(db)
        h1 = svc._hash_problem("What is 2+2?")
        h2 = svc._hash_problem("What is 2+2?")
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_hash_problem_normalizes_whitespace(self):
        db = self._make_db()
        svc = self.mod.SequentialReasoningService(db)
        h1 = svc._hash_problem("  test problem  ")
        h2 = svc._hash_problem("test problem")
        assert h1 == h2

    def test_hash_problem_different_inputs(self):
        db = self._make_db()
        svc = self.mod.SequentialReasoningService(db)
        assert svc._hash_problem("A") != svc._hash_problem("B")

    # ----------------------------------------------------------------
    # DB-accessing methods patch `select` / `delete` inside the loaded
    # module to bypass real SQLAlchemy coercion of MagicMock objects.
    # ----------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_get_cached_reasoning_miss(self):
        db = self._make_db()
        mock_select = MagicMock(return_value=MagicMock())
        with patch.object(self.mod, "select", mock_select):
            svc = self.mod.SequentialReasoningService(db)
            result = await svc._get_cached_reasoning("unique problem xyz")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_cached_reasoning_hit(self):
        db = self._make_db()
        cached_entry = MagicMock()
        cached_entry.hit_count = 5
        cached_entry.last_hit = datetime.now(UTC)
        cached_entry.reasoning_data = {"answer": "42", "provider": "gemini"}
        exec_result = MagicMock()
        exec_result.scalar_one_or_none.return_value = cached_entry
        db.execute = AsyncMock(return_value=exec_result)

        # select(...).where(...).where(...) chain
        mock_stmt = MagicMock()
        mock_stmt.where.return_value = mock_stmt
        mock_select = MagicMock(return_value=mock_stmt)
        with patch.object(self.mod, "select", mock_select):
            svc = self.mod.SequentialReasoningService(db)
            result = await svc._get_cached_reasoning("What is 6 x 7?")
        assert result is not None
        assert result["from_cache"] is True
        assert result["cache_hit_count"] == 6  # incremented

    @pytest.mark.asyncio
    async def test_cache_reasoning_creates_new_entry(self):
        db = self._make_db()
        exec_result = MagicMock()
        exec_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=exec_result)

        mock_stmt = MagicMock()
        mock_stmt.where.return_value = mock_stmt
        mock_select = MagicMock(return_value=mock_stmt)
        with patch.object(self.mod, "select", mock_select):
            svc = self.mod.SequentialReasoningService(db)
            await svc._cache_reasoning(
                "new problem", {"answer": "x", "confidence": 0.9}
            )
        assert db.add.called
        assert db.commit.called

    @pytest.mark.asyncio
    async def test_cache_reasoning_updates_existing(self):
        db = self._make_db()
        existing = MagicMock()
        existing.reasoning_data = {}
        exec_result = MagicMock()
        exec_result.scalar_one_or_none.return_value = existing
        db.execute = AsyncMock(return_value=exec_result)

        mock_stmt = MagicMock()
        mock_stmt.where.return_value = mock_stmt
        mock_select = MagicMock(return_value=mock_stmt)
        with patch.object(self.mod, "select", mock_select):
            svc = self.mod.SequentialReasoningService(db)
            await svc._cache_reasoning("existing problem", {"answer": "y"})
        assert existing.reasoning_data == {"answer": "y"}

    @pytest.mark.asyncio
    async def test_invalidate_cache_specific_problem(self):
        db = self._make_db()
        result_obj = MagicMock()
        result_obj.rowcount = 1
        db.execute = AsyncMock(return_value=result_obj)

        mock_stmt = MagicMock()
        mock_stmt.where.return_value = mock_stmt
        mock_delete = MagicMock(return_value=mock_stmt)
        with patch.object(self.mod, "delete", mock_delete):
            svc = self.mod.SequentialReasoningService(db)
            count = await svc.invalidate_cache("specific problem")
        assert count == 1

    @pytest.mark.asyncio
    async def test_invalidate_cache_all_expired(self):
        db = self._make_db()
        result_obj = MagicMock()
        result_obj.rowcount = 5
        db.execute = AsyncMock(return_value=result_obj)

        mock_stmt = MagicMock()
        mock_stmt.where.return_value = mock_stmt
        mock_delete = MagicMock(return_value=mock_stmt)
        with patch.object(self.mod, "delete", mock_delete):
            svc = self.mod.SequentialReasoningService(db)
            count = await svc.invalidate_cache()
        assert count == 5

    @pytest.mark.asyncio
    async def test_get_session_not_found(self):
        import uuid as _uuid

        db = self._make_db()
        mock_stmt = MagicMock()
        mock_stmt.options.return_value = mock_stmt
        mock_stmt.where.return_value = mock_stmt
        mock_select = MagicMock(return_value=mock_stmt)
        with patch.object(self.mod, "select", mock_select):
            svc = self.mod.SequentialReasoningService(db)
            result = await svc.get_session(_uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_session_found(self):
        import uuid as _uuid

        db = self._make_db()
        sess = MagicMock()
        sess.to_dict.return_value = {"id": "123", "problem": "test"}
        exec_result = MagicMock()
        exec_result.scalar_one_or_none.return_value = sess
        db.execute = AsyncMock(return_value=exec_result)

        mock_stmt = MagicMock()
        mock_stmt.options.return_value = mock_stmt
        mock_stmt.where.return_value = mock_stmt
        mock_select = MagicMock(return_value=mock_stmt)
        with patch.object(self.mod, "select", mock_select):
            svc = self.mod.SequentialReasoningService(db)
            result = await svc.get_session(_uuid.uuid4())
        assert result == {"id": "123", "problem": "test"}

    @pytest.mark.asyncio
    async def test_get_session_steps_empty(self):
        import uuid as _uuid

        db = self._make_db()
        mock_stmt = MagicMock()
        mock_stmt.where.return_value = mock_stmt
        mock_stmt.order_by.return_value = mock_stmt
        mock_select = MagicMock(return_value=mock_stmt)
        with patch.object(self.mod, "select", mock_select):
            svc = self.mod.SequentialReasoningService(db)
            steps = await svc.get_session_steps(_uuid.uuid4())
        assert steps == []

    @pytest.mark.asyncio
    async def test_update_session_with_result(self):
        db = self._make_db()
        svc = self.mod.SequentialReasoningService(db)
        session = MagicMock()
        result = {
            "final_answer": "42",
            "understanding": "clear",
            "confidence": 0.95,
            "latency_ms": 100,
            "model": "gemini-pro",
            "provider": "gemini",
            "ensemble_scores": {"gemini": 0.95},
        }
        await svc._update_session_with_result(session, result)
        assert session.status == "completed"
        assert session.final_answer == "42"
        assert session.confidence == 0.95

    def test_topological_sort_empty(self):
        db = self._make_db()
        svc = self.mod.SequentialReasoningService(db)
        result = svc._topological_sort_subproblems([])
        assert result == []

    def test_topological_sort_no_deps(self):
        db = self._make_db()
        svc = self.mod.SequentialReasoningService(db)
        sps = [
            {"id": "1", "title": "Step 1", "dependencies": []},
            {"id": "2", "title": "Step 2", "dependencies": []},
        ]
        # Graph returns sorted IDs
        from unittest.mock import patch

        with patch.object(
            svc.mod if hasattr(svc, "mod") else self.mod, "DependencyGraph", create=True
        ):
            result = svc._topological_sort_subproblems(sps)
        # Should return list (possibly original order if sort returns [])
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_validate_logic_no_validator(self):
        db = self._make_db()
        svc = self.mod.SequentialReasoningService(db, enable_logic_validation=False)
        session = MagicMock()
        result = await svc._validate_logic(session, [])
        assert result == {"enabled": False}

    @pytest.mark.asyncio
    async def test_validate_logic_with_validator(self):
        db = self._make_db()
        svc = self.mod.SequentialReasoningService(db)
        session = MagicMock()
        session.id = "sess-1"
        steps = [{"reasoning": "A implies B", "result": "B"}]
        result = await svc._validate_logic(session, steps)
        assert result["enabled"] is True
        assert "is_consistent" in result

    @pytest.mark.asyncio
    async def test_get_user_sessions_empty(self):
        import uuid as _uuid

        db = self._make_db()
        mock_stmt = MagicMock()
        mock_stmt.where.return_value = mock_stmt
        mock_stmt.order_by.return_value = mock_stmt
        mock_stmt.limit.return_value = mock_stmt
        mock_select = MagicMock(return_value=mock_stmt)
        with patch.object(self.mod, "select", mock_select):
            svc = self.mod.SequentialReasoningService(db)
            sessions = await svc.get_user_sessions(_uuid.uuid4())
        assert sessions == []


# ===========================================================================
# FILE 4: services/ogretmen_service.py
# ===========================================================================


class TestOgretmenService:
    """Tests for services/ogretmen_service.py"""

    @pytest.fixture(autouse=True)
    def _stub_and_load(self):
        # Stub models
        _models = MagicMock()
        _models.KullaniciRolu = MagicMock()
        _models.KullaniciRolu.OGRENCI = "ogrenci"
        sys.modules["models"] = _models

        # Stub user_service
        _user_svc_mod = MagicMock()
        _kullanici_servisi = MagicMock()
        _kullanici_servisi.ogretmen_profili_getir = AsyncMock()
        _kullanici_servisi.ogrenci_profili_getir = AsyncMock()
        _kullanici_servisi.kullanici_getir = AsyncMock()
        _kullanici_servisi.kullanici_listesi = AsyncMock(return_value=[])
        _kullanici_servisi.ogrenci_profilleri = {}
        _user_svc_mod.kullanici_servisi = _kullanici_servisi
        sys.modules["services.user_service"] = _user_svc_mod

        # We need to also stub osym_exam_engine for lazy import
        _osym = MagicMock()
        _osym.osym_exam_engine = MagicMock()
        _osym.osym_exam_engine.get_student_exams = AsyncMock(return_value=[])
        _osym.session_to_sinav_sonucu = AsyncMock(return_value=None)
        sys.modules["core.osym_exam_engine"] = _osym

        self.mod = _load("services.ogretmen_service", "services/ogretmen_service.py")
        self._kullanici_servisi = _kullanici_servisi
        self._osym = _osym
        yield

    def test_ogretmen_servisi_init(self):
        svc = self.mod.OgretmenServisi()
        assert svc.sinif_ogrenci_iliskileri == {}
        assert svc.ogrenci_notlari == {}
        assert svc.sinif_raporlari == {}
        assert svc.ogretmen_bildirimleri == {}

    @pytest.mark.asyncio
    async def test_bildirim_gonder_creates_notification(self):
        svc = self.mod.OgretmenServisi()
        result = await svc.bildirim_gonder(
            "ogretmen-1",
            {
                "baslik": "Sınav hatırlatma",
                "mesaj": "Sınav 3 gün sonra",
                "tip": "uyari",
            },
        )
        assert result is True
        assert "ogretmen-1" in svc.ogretmen_bildirimleri
        bildirimler = svc.ogretmen_bildirimleri["ogretmen-1"]
        assert len(bildirimler) == 1
        assert bildirimler[0]["baslik"] == "Sınav hatırlatma"

    @pytest.mark.asyncio
    async def test_bildirim_gonder_limits_to_50(self):
        svc = self.mod.OgretmenServisi()
        for i in range(55):
            await svc.bildirim_gonder(
                "ogr-2", {"baslik": f"B{i}", "mesaj": "msg", "tip": "bilgi"}
            )
        assert len(svc.ogretmen_bildirimleri["ogr-2"]) == 50

    @pytest.mark.asyncio
    async def test_bildirimler_getir_empty(self):
        svc = self.mod.OgretmenServisi()
        result = await svc.bildirimler_getir("nonexistent-teacher")
        assert result == []

    @pytest.mark.asyncio
    async def test_bildirimler_getir_with_limit(self):
        svc = self.mod.OgretmenServisi()
        for i in range(10):
            await svc.bildirim_gonder(
                "t1", {"baslik": f"B{i}", "mesaj": "", "tip": "bilgi"}
            )
        result = await svc.bildirimler_getir("t1", limit=3)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_bildirim_okundu_isaretle_found(self):
        svc = self.mod.OgretmenServisi()
        await svc.bildirim_gonder(
            "t1", {"baslik": "Test", "mesaj": "msg", "tip": "bilgi"}
        )
        bildirim_id = svc.ogretmen_bildirimleri["t1"][0]["bildirim_id"]
        result = await svc.bildirim_okundu_isaretle("t1", bildirim_id)
        assert result is True
        assert svc.ogretmen_bildirimleri["t1"][0]["okundu"] is True

    @pytest.mark.asyncio
    async def test_bildirim_okundu_isaretle_not_found(self):
        svc = self.mod.OgretmenServisi()
        result = await svc.bildirim_okundu_isaretle("t1", "nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_ogretmen_ogrenci_yetkisi_kontrol_true(self):
        svc = self.mod.OgretmenServisi()
        svc.sinif_ogrenci_iliskileri["t1"] = ["o1", "o2", "o3"]
        result = await svc._ogretmen_ogrenci_yetkisi_kontrol("t1", "o2")
        assert result is True

    @pytest.mark.asyncio
    async def test_ogretmen_ogrenci_yetkisi_kontrol_false(self):
        svc = self.mod.OgretmenServisi()
        svc.sinif_ogrenci_iliskileri["t1"] = ["o1", "o2"]
        result = await svc._ogretmen_ogrenci_yetkisi_kontrol("t1", "o99")
        assert result is False

    @pytest.mark.asyncio
    async def test_ogretmen_ogrenci_yetkisi_kontrol_no_relation(self):
        svc = self.mod.OgretmenServisi()
        result = await svc._ogretmen_ogrenci_yetkisi_kontrol("t_unknown", "o1")
        assert result is False

    @pytest.mark.asyncio
    async def test_ogrenci_son_performans_no_exams(self):
        svc = self.mod.OgretmenServisi()
        result = await svc._ogrenci_son_performans("o-no-exams")
        assert result["ortalama_net"] == 0
        assert result["toplam_sinav"] == 0
        assert result["gelisim_trendi"] == "veri_yok"

    @pytest.mark.asyncio
    async def test_ogrenci_son_performans_with_exams(self):
        svc = self.mod.OgretmenServisi()
        mock_sinav = MagicMock()
        mock_sinav.session_id = "s1"
        mock_sinav.started_at = datetime(2026, 3, 1)
        self._osym.osym_exam_engine.get_student_exams = AsyncMock(
            return_value=[mock_sinav]
        )
        mock_sonuc = MagicMock()
        mock_sonuc.net_sayisi = 45.0
        self._osym.session_to_sinav_sonucu = AsyncMock(return_value=mock_sonuc)
        result = await svc._ogrenci_son_performans("o1")
        assert result["toplam_sinav"] == 1
        assert result["ortalama_net"] == pytest.approx(45.0)

    @pytest.mark.asyncio
    async def test_ogrenci_onerileri_olustur_weak_topics(self):
        svc = self.mod.OgretmenServisi()
        result = await svc._ogrenci_onerileri_olustur("o1", ["Matematik", "Fizik"], [])
        assert len(result) >= 1
        assert any("Matematik" in r for r in result)

    @pytest.mark.asyncio
    async def test_ogrenci_onerileri_olustur_strong_topics(self):
        svc = self.mod.OgretmenServisi()
        result = await svc._ogrenci_onerileri_olustur("o1", [], ["Kimya", "Biyoloji"])
        assert len(result) >= 1
        assert any("Kimya" in r for r in result)

    @pytest.mark.asyncio
    async def test_ogrenci_onerileri_olustur_no_topics(self):
        svc = self.mod.OgretmenServisi()
        result = await svc._ogrenci_onerileri_olustur("o1", [], [])
        assert len(result) == 1
        assert "sınav" in result[0].lower()

    @pytest.mark.asyncio
    async def test_sinif_onerileri_olustur_low_average(self):
        svc = self.mod.OgretmenServisi()
        result = await svc._sinif_onerileri_olustur(
            {"Matematik": 40.0, "Fizik": 20.0},
            {"ortalama_net": 15, "standart_sapma": 5},
        )
        assert any("temel" in r.lower() or "düşük" in r.lower() for r in result)

    @pytest.mark.asyncio
    async def test_sinif_onerileri_olustur_high_average(self):
        svc = self.mod.OgretmenServisi()
        # Non-empty konu_performanslari so the outer `if konu_performanslari:` branch
        # is entered; all topics > 50% so no zayif_konular; ortalama_net > 60 triggers
        # the success message.
        result = await svc._sinif_onerileri_olustur(
            {"Matematik": 85.0, "Fizik": 90.0},
            {"ortalama_net": 65, "standart_sapma": 8},
        )
        assert any("ileri" in r.lower() or "peki" in r.lower() for r in result)

    @pytest.mark.asyncio
    async def test_sinif_onerileri_olustur_empty_data(self):
        svc = self.mod.OgretmenServisi()
        result = await svc._sinif_onerileri_olustur({}, {"ortalama_net": 45})
        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_ogretmen_dashboard_verisi_no_profile(self):
        svc = self.mod.OgretmenServisi()
        self._kullanici_servisi.ogretmen_profili_getir = AsyncMock(return_value=None)
        with pytest.raises(ValueError, match="Dashboard verisi alınamadı"):
            await svc.ogretmen_dashboard_verisi("t1")

    @pytest.mark.asyncio
    async def test_ogretmen_dashboard_verisi_with_profile(self):
        svc = self.mod.OgretmenServisi()
        mock_profile = MagicMock()
        self._kullanici_servisi.ogretmen_profili_getir = AsyncMock(
            return_value=mock_profile
        )
        # No students assigned
        svc.sinif_ogrenci_iliskileri["t1"] = []
        result = await svc.ogretmen_dashboard_verisi("t1")
        assert "ogretmen_profili" in result
        assert result["genel_istatistikler"]["toplam_ogrenci"] == 0

    @pytest.mark.asyncio
    async def test_sinif_raporu_olustur_no_students(self):
        svc = self.mod.OgretmenServisi()
        svc.sinif_ogrenci_iliskileri["t1"] = []
        with pytest.raises(ValueError, match="öğrenci bulunamadı"):
            await svc.sinif_raporu_olustur("t1", {})

    # ---- Global instance ----

    def test_global_instance_exists(self):
        assert self.mod.ogretmen_servisi is not None
        assert isinstance(self.mod.ogretmen_servisi, self.mod.OgretmenServisi)


# ===========================================================================
# FILE 5: services/revolutionary_features_service.py
# ===========================================================================


class TestRevolutionaryFeaturesService:
    """Tests for services/revolutionary_features_service.py"""

    @pytest.fixture(autouse=True)
    def _stub_and_load(self):
        # Stub TurkishZPDMaarifSystem
        _zpd_mod = MagicMock()
        _zpd_sys = MagicMock()
        _zpd_result = MagicMock()
        _zpd_result.lower_bound = 0.3
        _zpd_result.upper_bound = 0.7
        _zpd_result.optimal_challenge = 0.5
        _zpd_sys.calculate_turkish_zpd = AsyncMock(return_value=_zpd_result)
        _zpd_mod.TurkishZPDMaarifSystem.return_value = _zpd_sys
        sys.modules["algorithms.turkish_zpd_maarif_system"] = _zpd_mod

        # Stub IRTCalibrationService
        _irt_mod = MagicMock()
        sys.modules["services.irt_calibration_service"] = _irt_mod

        self.mod = _load(
            "services.revolutionary_features_service",
            "services/revolutionary_features_service.py",
        )
        self._zpd_result = _zpd_result
        yield

    # ---- Dataclasses ----

    def test_vark_profile_creation(self):
        p = self.mod.VARKProfile(
            visual=0.4, auditory=0.3, reading=0.2, kinesthetic=0.1, dominant="visual"
        )
        assert p.dominant == "visual"
        assert abs(p.visual + p.auditory + p.reading + p.kinesthetic - 1.0) < 0.01

    def test_felder_profile_creation(self):
        p = self.mod.FelderProfile(
            active_reflective=0.5,
            sensing_intuitive=-0.3,
            visual_verbal=0.2,
            sequential_global=-0.1,
            preferences=["active", "intuitive"],
        )
        assert "active" in p.preferences
        assert p.sensing_intuitive == -0.3

    def test_hybrid_learning_profile_creation(self):
        vark = self.mod.VARKProfile(0.4, 0.3, 0.2, 0.1, "visual")
        felder = self.mod.FelderProfile(0.5, -0.3, 0.2, -0.1, ["active"])
        profile = self.mod.HybridLearningProfile(
            student_id="s1",
            hybrid_code="V-ASQV",
            vark_profile=vark,
            felder_profile=felder,
            confidence={"score": 0.8, "level": "Yüksek"},
            data_points_used=10,
            detection_date="2026-01-01",
            last_updated="2026-01-01",
        )
        assert profile.student_id == "s1"
        assert profile.hybrid_code == "V-ASQV"

    # ---- _generate_hybrid_code ----

    def test_generate_hybrid_code_format(self):
        svc = self.mod.RevolutionaryFeaturesService()
        vark = self.mod.VARKProfile(0.4, 0.3, 0.2, 0.1, "visual")
        felder = self.mod.FelderProfile(0.5, 0.6, 0.7, 0.8, ["active", "sensing"])
        code = svc._generate_hybrid_code(vark, felder)
        assert "-" in code
        parts = code.split("-")
        assert len(parts) == 2
        assert len(parts[0]) == 1  # VARK letter
        assert len(parts[1]) == 4  # Felder 4 dimensions

    def test_generate_hybrid_code_negative_felder(self):
        svc = self.mod.RevolutionaryFeaturesService()
        vark = self.mod.VARKProfile(0.1, 0.6, 0.2, 0.1, "auditory")
        felder = self.mod.FelderProfile(-0.5, -0.6, -0.7, -0.8, [])
        code = svc._generate_hybrid_code(vark, felder)
        assert code.startswith("A-")
        # Negative values → R, I, B, G
        assert code == "A-RIBG"

    def test_generate_hybrid_code_positive_felder(self):
        svc = self.mod.RevolutionaryFeaturesService()
        vark = self.mod.VARKProfile(0.0, 0.0, 0.9, 0.1, "reading")
        felder = self.mod.FelderProfile(0.5, 0.5, 0.5, 0.5, [])
        code = svc._generate_hybrid_code(vark, felder)
        assert code == "R-ASVQ"

    # ---- _calculate_confidence ----

    def test_calculate_confidence_no_questionnaire(self):
        svc = self.mod.RevolutionaryFeaturesService()
        behavioral = {f"k{i}": i for i in range(5)}
        conf = svc._calculate_confidence(behavioral, None)
        assert "score" in conf
        assert "level" in conf
        assert "factors" in conf
        assert 0.0 <= conf["score"] <= 1.0

    def test_calculate_confidence_with_questionnaire(self):
        svc = self.mod.RevolutionaryFeaturesService()
        behavioral = {f"k{i}": i * 10 for i in range(10)}
        questionnaire = ["görsel", "şema", "grafik"] * 5
        conf = svc._calculate_confidence(behavioral, questionnaire)
        assert conf["score"] >= 0.0

    def test_calculate_confidence_level_very_low(self):
        svc = self.mod.RevolutionaryFeaturesService()
        conf = svc._calculate_confidence({}, None)
        assert conf["level"] == "Çok Düşük"

    def test_calculate_confidence_level_high(self):
        svc = self.mod.RevolutionaryFeaturesService()
        behavioral = {f"k{i}": 80 for i in range(10)}
        questionnaire = ["görsel"] * 20
        conf = svc._calculate_confidence(behavioral, questionnaire)
        assert conf["level"] in ["Orta", "Yüksek"]

    # ---- _calculate_behavioral_consistency ----

    def test_behavioral_consistency_default(self):
        svc = self.mod.RevolutionaryFeaturesService()
        result = svc._calculate_behavioral_consistency({})
        assert result == 0.5

    def test_behavioral_consistency_video_visual(self):
        svc = self.mod.RevolutionaryFeaturesService()
        result = svc._calculate_behavioral_consistency(
            {
                "video_watch_time": 60,
                "visual_content_performance": 0.5,
            }
        )
        assert 0.0 <= result <= 1.0

    def test_behavioral_consistency_group_individual(self):
        svc = self.mod.RevolutionaryFeaturesService()
        result = svc._calculate_behavioral_consistency(
            {
                "group_study_sessions": 5,
                "individual_study_sessions": 5,
            }
        )
        assert result > 0.0

    # ---- _analyze_questionnaire_for_vark ----

    def test_analyze_questionnaire_for_vark_keywords(self):
        svc = self.mod.RevolutionaryFeaturesService()
        responses = ["görsel öğrenmeyi tercih ederim", "şema ve diyagram kullanırım"]
        bonuses = svc._analyze_questionnaire_for_vark(responses)
        assert bonuses["visual"] > 0.0
        assert "auditory" in bonuses

    def test_analyze_questionnaire_for_vark_empty(self):
        svc = self.mod.RevolutionaryFeaturesService()
        bonuses = svc._analyze_questionnaire_for_vark([])
        assert all(v == 0.0 for v in bonuses.values())

    # ---- _analyze_questionnaire_for_felder ----

    def test_analyze_questionnaire_for_felder_active_keywords(self):
        svc = self.mod.RevolutionaryFeaturesService()
        responses = ["grup çalışması yapmayı severim", "hemen uygulamaya geçerim"]
        bonuses = svc._analyze_questionnaire_for_felder(responses)
        assert bonuses["active_reflective"] > 0.0

    def test_analyze_questionnaire_for_felder_reflective_keywords(self):
        svc = self.mod.RevolutionaryFeaturesService()
        responses = ["tek başıma çalışmayı severim", "önce planlama yaparım"]
        bonuses = svc._analyze_questionnaire_for_felder(responses)
        assert bonuses["active_reflective"] < 0.0

    # ---- _calculate_group_individual_balance ----

    def test_group_individual_balance_equal(self):
        svc = self.mod.RevolutionaryFeaturesService()
        ratio = svc._calculate_group_individual_balance(
            {
                "group_study_sessions": 5,
                "individual_study_sessions": 5,
            }
        )
        assert ratio == pytest.approx(0.5)

    def test_group_individual_balance_all_group(self):
        svc = self.mod.RevolutionaryFeaturesService()
        ratio = svc._calculate_group_individual_balance(
            {
                "group_study_sessions": 10,
                "individual_study_sessions": 0,
            }
        )
        assert ratio == pytest.approx(1.0)

    def test_group_individual_balance_no_sessions(self):
        svc = self.mod.RevolutionaryFeaturesService()
        ratio = svc._calculate_group_individual_balance({})
        assert ratio == 0.5  # Default

    # ---- calculate_maarif_alignment ----

    @pytest.mark.asyncio
    async def test_maarif_alignment_empty_description(self):
        svc = self.mod.RevolutionaryFeaturesService()
        result = await svc.calculate_maarif_alignment("matematik", "")
        assert 0.0 <= result.overall_alignment <= 1.0
        assert result.overall_alignment == pytest.approx(0.0)
        assert isinstance(result.aligned_values, list)

    @pytest.mark.asyncio
    async def test_maarif_alignment_national_keywords(self):
        svc = self.mod.RevolutionaryFeaturesService()
        result = await svc.calculate_maarif_alignment(
            "tarih", "vatan sevgisi ve türk milletinin atatürk'e saygısı"
        )
        assert result.national_values_alignment > 0.0

    @pytest.mark.asyncio
    async def test_maarif_alignment_universal_keywords(self):
        svc = self.mod.RevolutionaryFeaturesService()
        result = await svc.calculate_maarif_alignment(
            "felsefe", "adalet ve hoşgörü barış içinde"
        )
        assert result.universal_values_alignment > 0.0

    @pytest.mark.asyncio
    async def test_maarif_alignment_subject_multiplier(self):
        svc = self.mod.RevolutionaryFeaturesService()
        r1 = await svc.calculate_maarif_alignment("tarih", "türk vatan millet")
        r2 = await svc.calculate_maarif_alignment("matematik", "türk vatan millet")
        # tarih has higher national multiplier (1.5 vs 0.8)
        assert r1.national_values_alignment >= r2.national_values_alignment

    # ---- detect_cultural_context ----

    @pytest.mark.asyncio
    async def test_detect_cultural_context_defaults(self):
        svc = self.mod.RevolutionaryFeaturesService()
        ctx = await svc.detect_cultural_context("s1", {})
        assert ctx.family_involvement == pytest.approx(0.7)
        assert ctx.elder_wisdom_value == pytest.approx(0.8)
        assert ctx.group_learning_preference == pytest.approx(0.0)

    @pytest.mark.asyncio
    async def test_detect_cultural_context_with_data(self):
        svc = self.mod.RevolutionaryFeaturesService()
        ctx = await svc.detect_cultural_context(
            "s1",
            {
                "group_study_sessions": 20,
                "teacher_question_count": 15,
                "peer_interaction_count": 30,
            },
        )
        assert ctx.group_learning_preference == pytest.approx(1.0)
        assert ctx.teacher_respect_level == pytest.approx(1.0)

    # ---- _calculate_vark_profile ----

    @pytest.mark.asyncio
    async def test_calculate_vark_profile_empty_data(self):
        svc = self.mod.RevolutionaryFeaturesService()
        profile = await svc._calculate_vark_profile({})
        # All zeros → total=0, normalization skipped → remains 0, dominant picks arbitrary
        assert profile.dominant in ["visual", "auditory", "reading", "kinesthetic"]

    @pytest.mark.asyncio
    async def test_calculate_vark_profile_video_heavy(self):
        svc = self.mod.RevolutionaryFeaturesService()
        profile = await svc._calculate_vark_profile(
            {
                "video_watch_time": 100,
            }
        )
        # video_watch_time gives highest weight to visual (0.8)
        assert profile.dominant == "visual"

    @pytest.mark.asyncio
    async def test_calculate_vark_profile_reading_heavy(self):
        svc = self.mod.RevolutionaryFeaturesService()
        profile = await svc._calculate_vark_profile(
            {
                "text_reading_time": 100,
            }
        )
        # text_reading_time gives highest weight to reading (0.9)
        assert profile.dominant == "reading"

    @pytest.mark.asyncio
    async def test_calculate_vark_profile_with_questionnaire(self):
        svc = self.mod.RevolutionaryFeaturesService()
        profile = await svc._calculate_vark_profile(
            {"video_watch_time": 50},
            questionnaire_responses=["görsel grafik şema"],
        )
        assert hasattr(profile, "dominant")

    # ---- _calculate_felder_profile ----

    @pytest.mark.asyncio
    async def test_calculate_felder_profile_empty_data(self):
        svc = self.mod.RevolutionaryFeaturesService()
        profile = await svc._calculate_felder_profile({})
        assert -1.0 <= profile.active_reflective <= 1.0
        assert isinstance(profile.preferences, list)

    @pytest.mark.asyncio
    async def test_calculate_felder_profile_group_heavy(self):
        svc = self.mod.RevolutionaryFeaturesService()
        profile = await svc._calculate_felder_profile(
            {
                "group_study_sessions": 100,
            }
        )
        # group sessions → active_reflective: +0.8 weight → positive
        assert profile.active_reflective > 0
        assert "active" in profile.preferences

    @pytest.mark.asyncio
    async def test_calculate_felder_profile_preferences_clamped(self):
        svc = self.mod.RevolutionaryFeaturesService()
        profile = await svc._calculate_felder_profile(
            {
                "group_study_sessions": 1000,
            }
        )
        # Clamped to [-1, 1]
        assert profile.active_reflective <= 1.0

    # ---- detect_hybrid_learning_style ----

    @pytest.mark.asyncio
    async def test_detect_hybrid_learning_style_basic(self):
        svc = self.mod.RevolutionaryFeaturesService()
        profile = await svc.detect_hybrid_learning_style(
            "student-1",
            {"video_watch_time": 60, "text_reading_time": 30},
        )
        assert profile.student_id == "student-1"
        assert "-" in profile.hybrid_code
        assert profile.data_points_used == 2

    @pytest.mark.asyncio
    async def test_detect_hybrid_learning_style_with_questionnaire(self):
        svc = self.mod.RevolutionaryFeaturesService()
        profile = await svc.detect_hybrid_learning_style(
            "student-2",
            {"interactive_engagement": 80},
            questionnaire_responses=["yaparak öğrenmeyi severim", "pratik uygulama"],
        )
        assert profile.confidence["score"] > 0.0

    # ---- _generate_reasoning ----

    def test_generate_reasoning_above_level(self):
        svc = self.mod.RevolutionaryFeaturesService()
        zpd_range = MagicMock()
        zpd_range.optimal_challenge = 2.0
        zpd_range.current_level = 1.0
        zpd_range.group_individual_balance = 0.3
        zpd_range.maarif_alignment = MagicMock()
        zpd_range.maarif_alignment.overall_alignment = 0.2
        learning_profile = MagicMock()
        learning_profile.vark_profile.dominant = "visual"

        reasoning = svc._generate_reasoning(
            zpd_range, learning_profile, "Türev öğrenmek"
        )
        assert "zorlayıcı" in reasoning.lower()

    def test_generate_reasoning_same_level(self):
        svc = self.mod.RevolutionaryFeaturesService()
        zpd_range = MagicMock()
        zpd_range.optimal_challenge = 1.2
        zpd_range.current_level = 1.0
        zpd_range.group_individual_balance = 0.5
        zpd_range.maarif_alignment = MagicMock()
        zpd_range.maarif_alignment.overall_alignment = 0.8
        learning_profile = MagicMock()
        learning_profile.vark_profile.dominant = "kinesthetic"

        reasoning = svc._generate_reasoning(
            zpd_range, learning_profile, "Pratik yapmak"
        )
        assert "pekiştirici" in reasoning.lower()
        assert "meb" in reasoning.lower()

    # ---- Global instance ----

    def test_global_instance_exists(self):
        assert self.mod.revolutionary_features_service is not None
        assert isinstance(
            self.mod.revolutionary_features_service,
            self.mod.RevolutionaryFeaturesService,
        )
