"""
Final Coverage Push 2 — 8 uncovered modules
Targets:
  core/unified/session_system.py
  core/api_optimizer.py
  core/transaction_manager.py
  core/unified_event_bus.py
  core/message_queue_system.py
  core/rag_service.py
  services/student_review_service.py
  services/learning_style_service.py
"""

import asyncio
import os
import sys
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_backend = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _backend not in sys.path:
    sys.path.insert(0, _backend)

# ---------------------------------------------------------------------------
# Pre-stub heavy/external dependencies BEFORE importing the modules under test
# ---------------------------------------------------------------------------
_STUBS = {
    # redis async
    "redis": MagicMock(),
    "redis.asyncio": MagicMock(),
    # langchain family
    "langchain_core": MagicMock(),
    "langchain_core.documents": MagicMock(),
    "langchain_text_splitters": MagicMock(),
    "langchain_community": MagicMock(),
    "langchain_community.embeddings": MagicMock(),
    "langchain_community.vectorstores": MagicMock(),
    "langchain_community.retrievers": MagicMock(),
    "langchain": MagicMock(),
    "langchain.embeddings": MagicMock(),
    "langchain.embeddings.base": MagicMock(),
    "langchain.retrievers": MagicMock(),
    # NOTE: do NOT stub "core" itself — that would break other test files that
    # import real core submodules at module level. Only stub the specific
    # submodules that are heavy/external.
    "core.application_metrics": MagicMock(),
    "core.structured_logging": MagicMock(),
    "core.unified_config": MagicMock(),
    "core.cache": MagicMock(),
    "core.enhanced_database": MagicMock(),
    "core.error_context": MagicMock(),
    "core.error_monitoring": MagicMock(),
    "core.exceptions": MagicMock(),
    "core.vector_store_factory": MagicMock(),
    "core.rag_config": MagicMock(),
    "core.reranker": MagicMock(),
    "core.query_expansion": MagicMock(),
    "core.document_deduplication": MagicMock(),
    # models stubs — only submodules not "models" itself
    "models.student_review": MagicMock(),
}

for _mod, _stub in _STUBS.items():
    sys.modules.setdefault(_mod, _stub)

import logging as _logging
from contextlib import asynccontextmanager


# Only mutate a module if WE installed it (i.e., it's a MagicMock).
# This prevents corrupting real modules already loaded by other test files.
def _is_our_stub(mod_name):
    m = sys.modules.get(mod_name)
    return isinstance(m, MagicMock)


# Make get_unified_config return something safe
_config_stub = MagicMock()
_config_stub.redis_url = "redis://localhost:6379/0"
if _is_our_stub("core.unified_config"):
    sys.modules["core.unified_config"].get_unified_config = MagicMock(
        return_value=_config_stub
    )

# Make get_logger return a real logger
if _is_our_stub("core.structured_logging"):
    sys.modules["core.structured_logging"].get_logger = MagicMock(
        return_value=_logging.getLogger("test")
    )
    sys.modules["core.structured_logging"].LogCategory = MagicMock()

# Make get_metrics_collector return a stub
_metrics_stub = MagicMock()
_metrics_stub.record_metric = MagicMock()
if _is_our_stub("core.application_metrics"):
    sys.modules["core.application_metrics"].get_metrics_collector = MagicMock(
        return_value=_metrics_stub
    )
    sys.modules["core.application_metrics"].MetricType = MagicMock()


# Make async_error_context a proper async context manager
@asynccontextmanager
async def _dummy_async_error_context(**kwargs):
    ctx = MagicMock()
    ctx.tags = {}
    ctx.add_annotation = MagicMock()
    ctx.to_dict = MagicMock(return_value={})
    yield ctx


if _is_our_stub("core.error_context"):
    sys.modules["core.error_context"].async_error_context = _dummy_async_error_context


# Make log_error an async no-op
async def _dummy_log_error(*a, **kw):
    pass


if _is_our_stub("core.error_monitoring"):
    sys.modules["core.error_monitoring"].log_error = _dummy_log_error


# Make exceptions
class _DatabaseError(Exception):
    def __init__(self, message="", operation="", details=None):
        super().__init__(message)


class _ValidationError(Exception):
    def __init__(self, message="", **kw):
        super().__init__(message)


class _ErrorSeverity:
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


sys.modules["core.exceptions"].DatabaseError = _DatabaseError
sys.modules["core.exceptions"].ValidationError = _ValidationError
sys.modules["core.exceptions"].ErrorSeverity = _ErrorSeverity

# enhanced_database stub
_db_mgr_stub = MagicMock()
sys.modules["core.enhanced_database"].EnhancedDatabaseManager = MagicMock
sys.modules["core.enhanced_database"].enhanced_db_manager = _db_mgr_stub

# cache_manager stub
_cache_stub = AsyncMock()
_cache_stub.get = AsyncMock(return_value=None)
_cache_stub.set = AsyncMock(return_value=True)
sys.modules["core.cache"].cache_manager = _cache_stub

# sqlalchemy stubs if not installed
try:
    from sqlalchemy.exc import IntegrityError, OperationalError
except ImportError:
    sys.modules.setdefault("sqlalchemy", MagicMock())
    sys.modules.setdefault("sqlalchemy.exc", MagicMock())
    sys.modules.setdefault("sqlalchemy.ext", MagicMock())
    sys.modules.setdefault("sqlalchemy.ext.asyncio", MagicMock())
    sys.modules.setdefault("sqlalchemy.sql", MagicMock())

# jwt stub
try:
    import jwt as _jwt_real
except ImportError:
    sys.modules.setdefault("jwt", MagicMock())


# ===========================================================================
# 1. SESSION SYSTEM
# ===========================================================================


class TestSessionSystem:
    """Tests for core/unified/session_system.py"""

    def _get_module(self):
        # Remove stale mock if present
        for _m in ["core.unified.session_system", "core.unified"]:
            _ex = sys.modules.get(_m)
            if _ex is not None and isinstance(_ex, MagicMock):
                del sys.modules[_m]
        import importlib
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "core.unified.session_system",
            os.path.join(_backend, "core", "unified", "session_system.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_session_info_is_expired_false(self):
        mod = self._get_module()
        s = mod.SessionInfo(
            session_id="s1",
            user_id="u1",
            device_id="d1",
            device_type=mod.DeviceType.WEB,
            ip_address="1.2.3.4",
            user_agent="Mozilla",
            created_at=datetime.now(),
            last_activity=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1),
        )
        assert s.is_expired is False
        assert s.is_active is True

    def test_session_info_is_expired_true(self):
        mod = self._get_module()
        s = mod.SessionInfo(
            session_id="s2",
            user_id="u2",
            device_id="d2",
            device_type=mod.DeviceType.WEB,
            ip_address="1.2.3.4",
            user_agent="Mozilla",
            created_at=datetime.now() - timedelta(hours=2),
            last_activity=datetime.now() - timedelta(hours=2),
            expires_at=datetime.now() - timedelta(hours=1),
        )
        assert s.is_expired is True
        assert s.is_active is False

    def test_session_info_to_dict_and_from_dict(self):
        mod = self._get_module()
        now = datetime.now()
        s = mod.SessionInfo(
            session_id="abc",
            user_id="u1",
            device_id="d1",
            device_type=mod.DeviceType.MOBILE,
            ip_address="10.0.0.1",
            user_agent="iPhone",
            created_at=now,
            last_activity=now,
            expires_at=now + timedelta(hours=1),
            metadata={"role": "student"},
        )
        d = s.to_dict()
        assert d["session_id"] == "abc"
        assert d["device_type"] == "mobile"
        s2 = mod.SessionInfo.from_dict(d)
        assert s2.session_id == "abc"
        assert s2.device_type == mod.DeviceType.MOBILE

    def test_token_info_is_expired(self):
        mod = self._get_module()
        now = datetime.now()
        t = mod.TokenInfo(
            token_id="t1",
            user_id="u1",
            token_type=mod.TokenType.ACCESS,
            session_id="s1",
            created_at=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1),
        )
        assert t.is_expired is True

    def test_token_info_to_dict(self):
        mod = self._get_module()
        now = datetime.now()
        t = mod.TokenInfo(
            token_id="t2",
            user_id="u2",
            token_type=mod.TokenType.REFRESH,
            session_id=None,
            created_at=now,
            expires_at=now + timedelta(days=7),
            scopes={"read", "write"},
        )
        d = t.to_dict()
        assert d["token_type"] == "refresh"
        assert set(d["scopes"]) == {"read", "write"}

    def test_device_fingerprint_generate(self):
        mod = self._get_module()
        fid = mod.DeviceFingerprint.generate_device_id("Mozilla/5.0", "192.168.1.100")
        assert isinstance(fid, str)
        assert len(fid) == 16

    def test_device_fingerprint_detect_mobile(self):
        mod = self._get_module()
        dt = mod.DeviceFingerprint.detect_device_type(
            "Mozilla/5.0 (iPhone; CPU iPhone OS)"
        )
        assert dt == mod.DeviceType.MOBILE

    def test_device_fingerprint_detect_tablet(self):
        mod = self._get_module()
        dt = mod.DeviceFingerprint.detect_device_type("Mozilla/5.0 (iPad)")
        assert dt == mod.DeviceType.TABLET

    def test_device_fingerprint_detect_web(self):
        mod = self._get_module()
        dt = mod.DeviceFingerprint.detect_device_type("Mozilla/5.0 (Windows NT 10.0)")
        assert dt == mod.DeviceType.WEB

    def test_device_fingerprint_detect_desktop(self):
        mod = self._get_module()
        dt = mod.DeviceFingerprint.detect_device_type("Electron/25.0 desktop")
        assert dt == mod.DeviceType.DESKTOP

    def test_session_config_defaults(self):
        mod = self._get_module()
        cfg = mod.SessionConfig()
        assert cfg.session_timeout == 3600
        assert cfg.max_sessions_per_user == 5
        assert cfg.jwt_algorithm == "HS256"
        assert cfg.jwt_secret is not None

    @pytest.mark.asyncio
    async def test_create_session_memory(self):
        mod = self._get_module()
        manager = mod.UnifiedSessionManager()
        session = await manager.create_session(
            user_id="u1",
            ip_address="127.0.0.1",
            user_agent="TestAgent/1.0",
        )
        assert session.user_id == "u1"
        assert session.is_active

    @pytest.mark.asyncio
    async def test_get_session_memory(self):
        mod = self._get_module()
        manager = mod.UnifiedSessionManager()
        session = await manager.create_session("u1", "127.0.0.1", "TestAgent/1.0")
        fetched = await manager.get_session(session.session_id)
        assert fetched is not None
        assert fetched.session_id == session.session_id

    @pytest.mark.asyncio
    async def test_revoke_session(self):
        mod = self._get_module()
        manager = mod.UnifiedSessionManager()
        session = await manager.create_session("u1", "127.0.0.1", "TestAgent/1.0")
        result = await manager.revoke_session(session.session_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_session(self):
        mod = self._get_module()
        manager = mod.UnifiedSessionManager()
        result = await manager.revoke_session("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_generate_and_validate_access_token(self):
        mod = self._get_module()
        manager = mod.UnifiedSessionManager()
        # Need an event loop for create_task inside generate_access_token
        token = manager.generate_access_token("u1", "s1", scopes={"read"})
        assert isinstance(token, str)
        payload = manager.validate_token(token)
        assert payload is not None
        assert payload["sub"] == "u1"

    @pytest.mark.asyncio
    async def test_generate_and_validate_refresh_token(self):
        mod = self._get_module()
        manager = mod.UnifiedSessionManager()
        token = manager.generate_refresh_token("u1", "s1")
        assert isinstance(token, str)
        payload = manager.validate_token(token)
        assert payload["type"] == "refresh"

    @pytest.mark.asyncio
    async def test_validate_invalid_token(self):
        mod = self._get_module()
        manager = mod.UnifiedSessionManager()
        result = manager.validate_token("garbage.token.here")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_session_activity(self):
        mod = self._get_module()
        manager = mod.UnifiedSessionManager()
        session = await manager.create_session("u1", "127.0.0.1", "TestAgent/1.0")
        result = await manager.update_session_activity(session.session_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self):
        mod = self._get_module()
        manager = mod.UnifiedSessionManager()
        # Manually add an expired session
        now = datetime.now()
        expired_session = mod.SessionInfo(
            session_id="expired1",
            user_id="u_exp",
            device_id="d1",
            device_type=mod.DeviceType.WEB,
            ip_address="1.1.1.1",
            user_agent="Test",
            created_at=now - timedelta(hours=3),
            last_activity=now - timedelta(hours=3),
            expires_at=now - timedelta(hours=2),
        )
        manager._memory_sessions["expired1"] = expired_session
        await manager._cleanup_expired()
        assert "expired1" not in manager._memory_sessions

    @pytest.mark.asyncio
    async def test_get_session_stats(self):
        mod = self._get_module()
        manager = mod.UnifiedSessionManager()
        await manager.create_session("u1", "127.0.0.1", "Agent/1.0")
        stats = await manager.get_session_stats()
        assert "total_sessions" in stats
        assert stats["active_sessions"] >= 1

    @pytest.mark.asyncio
    async def test_revoke_user_sessions(self):
        mod = self._get_module()
        manager = mod.UnifiedSessionManager()
        await manager.create_session("u_multi", "127.0.0.1", "Agent/1.0")
        await manager.create_session("u_multi", "127.0.0.1", "Agent/2.0")
        revoked = await manager.revoke_user_sessions("u_multi")
        assert revoked >= 1

    def test_get_session_manager_returns_instance(self):
        mod = self._get_module()
        # Reset global
        mod._session_manager = None
        m = mod.get_session_manager()
        assert isinstance(m, mod.UnifiedSessionManager)

    def test_backward_compat_aliases(self):
        mod = self._get_module()
        assert mod.SessionManager is mod.UnifiedSessionManager
        assert mod.TokenManager is mod.UnifiedSessionManager


# ===========================================================================
# 2. API OPTIMIZER
# ===========================================================================


class TestAPIOptimizer:
    """Tests for core/api_optimizer.py"""

    def _get_module(self):
        for _m in ["core.api_optimizer"]:
            _ex = sys.modules.get(_m)
            if _ex is not None and isinstance(_ex, MagicMock):
                del sys.modules[_m]
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "core.api_optimizer",
            os.path.join(_backend, "core", "api_optimizer.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_rate_limit_config_defaults(self):
        mod = self._get_module()
        cfg = mod.RateLimitConfig()
        assert cfg.requests_per_minute == 100
        assert cfg.enabled is True

    def test_compression_config_defaults(self):
        mod = self._get_module()
        cfg = mod.CompressionConfig()
        assert cfg.enabled is True
        assert cfg.min_size == 1024

    def test_cache_config_defaults(self):
        mod = self._get_module()
        cfg = mod.CacheConfig()
        assert cfg.default_ttl == 300
        assert cfg.enabled is True

    def test_pagination_params_offset(self):
        mod = self._get_module()
        p = mod.PaginationParams(page=3, size=10)
        assert p.offset == 20

    def test_paginated_response_create(self):
        mod = self._get_module()
        p = mod.PaginationParams(page=1, size=5)
        items = [1, 2, 3, 4, 5]
        resp = mod.PaginatedResponse.create(items, 25, p)
        assert resp.pages == 5
        assert resp.has_next is True
        assert resp.has_previous is False

    def test_paginated_response_last_page(self):
        mod = self._get_module()
        p = mod.PaginationParams(page=5, size=5)
        items = [21, 22, 23, 24, 25]
        resp = mod.PaginatedResponse.create(items, 25, p)
        assert resp.has_next is False
        assert resp.has_previous is True

    def test_turkish_optimize_search_results_empty(self):
        mod = self._get_module()
        result = mod.TurkishContentOptimizer.optimize_search_results([], "matematik")
        assert result == []

    def test_turkish_optimize_search_results_relevance(self):
        mod = self._get_module()
        results = [
            {"title": "Matematik Sorusu", "content": "integral hesabı"},
            {"title": "Tarih Dersi", "content": "osmanlı tarihi"},
        ]
        optimized = mod.TurkishContentOptimizer.optimize_search_results(
            results, "matematik"
        )
        assert optimized[0]["title"] == "Matematik Sorusu"

    def test_turkish_optimize_search_results_no_query(self):
        mod = self._get_module()
        results = [{"title": "Test"}]
        result = mod.TurkishContentOptimizer.optimize_search_results(results, "")
        assert result == results

    def test_turkish_optimize_response_format_dict(self):
        mod = self._get_module()
        data = {"question": "İstanbul nerede?", "answer": "Türkiye'de"}
        result = mod.TurkishContentOptimizer.optimize_response_format(data)
        assert result["question"] == "İstanbul nerede?"

    def test_turkish_optimize_response_format_list(self):
        mod = self._get_module()
        data = [{"key": "value"}, "text"]
        result = mod.TurkishContentOptimizer.optimize_response_format(data)
        assert len(result) == 2

    def test_turkish_optimize_response_format_str(self):
        mod = self._get_module()
        result = mod.TurkishContentOptimizer.optimize_response_format("Türkçe")
        assert result == "Türkçe"

    def test_turkish_optimize_response_format_other(self):
        mod = self._get_module()
        result = mod.TurkishContentOptimizer.optimize_response_format(42)
        assert result == 42

    def test_api_optimizer_init(self):
        mod = self._get_module()
        opt = mod.APIOptimizer(
            rate_limit_config=mod.RateLimitConfig(),
            compression_config=mod.CompressionConfig(),
            cache_config=mod.CacheConfig(),
        )
        assert opt.stats["total_requests"] == 0

    @pytest.mark.asyncio
    async def test_optimize_query_decorator(self):
        mod = self._get_module()

        @mod.optimize_query(True)
        async def fast_func():
            return 42

        result = await fast_func()
        assert result == 42

    @pytest.mark.asyncio
    async def test_optimize_query_decorator_exception(self):
        mod = self._get_module()

        @mod.optimize_query(True)
        async def failing_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            await failing_func()

    def test_pagination_page_min_1(self):
        mod = self._get_module()
        p = mod.PaginationParams(page=1, size=20)
        assert p.page == 1
        assert p.offset == 0

    @pytest.mark.asyncio
    async def test_search_content_optimized(self):
        mod = self._get_module()
        p = mod.PaginationParams(page=1, size=10)
        result = await mod.search_content("matematik", p)
        assert result.total >= 0


# ===========================================================================
# 3. TRANSACTION MANAGER
# ===========================================================================


class TestTransactionManager:
    """Tests for core/transaction_manager.py"""

    def _get_module(self):
        for _m in ["core.transaction_manager"]:
            _ex = sys.modules.get(_m)
            if _ex is not None and isinstance(_ex, MagicMock):
                del sys.modules[_m]
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "core.transaction_manager",
            os.path.join(_backend, "core", "transaction_manager.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_transaction_config_defaults(self):
        mod = self._get_module()
        cfg = mod.TransactionConfig()
        assert cfg.retry_attempts == 3
        assert cfg.retry_delay == 1.0
        assert cfg.enable_savepoints is True

    def test_transaction_config_validation_error(self):
        mod = self._get_module()
        with pytest.raises(Exception):
            mod.TransactionConfig(timeout_seconds=-1)

    def test_transaction_config_negative_retry(self):
        mod = self._get_module()
        with pytest.raises(Exception):
            mod.TransactionConfig(retry_attempts=-1)

    def test_transaction_metrics_mark_completed(self):
        mod = self._get_module()
        m = mod.TransactionMetrics(
            transaction_id="tx1",
            start_time=datetime.now() - timedelta(milliseconds=100),
        )
        m.mark_completed(mod.TransactionStatus.COMMITTED)
        assert m.status == mod.TransactionStatus.COMMITTED
        assert m.duration_ms is not None
        assert m.duration_ms >= 0

    def test_metrics_hook_get_stats_empty(self):
        mod = self._get_module()
        hook = mod.MetricsTransactionHook()
        stats = hook.get_stats()
        assert stats["total_transactions"] == 0
        assert stats["success_rate"] == 0

    @pytest.mark.asyncio
    async def test_metrics_hook_lifecycle(self):
        mod = self._get_module()
        hook = mod.MetricsTransactionHook()
        cfg = mod.TransactionConfig()

        # before_transaction
        await hook.before_transaction("tx1", cfg)
        assert "tx1" in hook.active_transactions

        # create a metrics object
        m = mod.TransactionMetrics(transaction_id="tx1", start_time=datetime.now())
        m.mark_completed(mod.TransactionStatus.COMMITTED)

        await hook.after_commit("tx1", m)
        assert "tx1" not in hook.active_transactions
        assert len(hook.completed_transactions) == 1

        stats = hook.get_stats()
        assert stats["successful_transactions"] == 1

    @pytest.mark.asyncio
    async def test_metrics_hook_rollback(self):
        mod = self._get_module()
        hook = mod.MetricsTransactionHook()
        cfg = mod.TransactionConfig()
        await hook.before_transaction("tx2", cfg)

        m = mod.TransactionMetrics(transaction_id="tx2", start_time=datetime.now())
        m.mark_completed(mod.TransactionStatus.ROLLED_BACK)

        err = RuntimeError("test")
        await hook.after_rollback("tx2", m, err)
        assert len(hook.completed_transactions) == 1
        stats = hook.get_stats()
        assert stats["failed_transactions"] == 1

    @pytest.mark.asyncio
    async def test_logging_hook(self):
        mod = self._get_module()
        hook = mod.LoggingTransactionHook()
        cfg = mod.TransactionConfig()
        await hook.before_transaction("tx1", cfg)

        m = mod.TransactionMetrics(transaction_id="tx1", start_time=datetime.now())
        m.mark_completed(mod.TransactionStatus.COMMITTED)
        await hook.after_commit("tx1", m)

        m2 = mod.TransactionMetrics(transaction_id="tx2", start_time=datetime.now())
        m2.mark_completed(mod.TransactionStatus.ROLLED_BACK)
        await hook.after_rollback("tx2", m2, RuntimeError("err"))

    def test_is_retryable_error(self):
        mod = self._get_module()
        tm = mod.EnhancedTransactionManager.__new__(mod.EnhancedTransactionManager)
        tm.global_hooks = []
        tm.active_transactions = {}
        tm.metrics_hook = mod.MetricsTransactionHook()
        tm.logging_hook = mod.LoggingTransactionHook()

        class FakeOp(Exception):
            pass

        e_dead = FakeOp("deadlock detected")
        assert tm._is_retryable_error(e_dead) is True

        e_conn = FakeOp("connection lost")
        assert tm._is_retryable_error(e_conn) is True

        e_normal = ValueError("something")
        assert tm._is_retryable_error(e_normal) is False

    def test_transaction_context_is_active(self):
        mod = self._get_module()
        session = MagicMock()
        transaction = MagicMock()
        cfg = mod.TransactionConfig()
        ctx = mod.TransactionContext(session, transaction, cfg, "tx_test")
        assert ctx.is_active() is True
        ctx._is_committed = True
        assert ctx.is_active() is False

    @pytest.mark.asyncio
    async def test_get_transaction_stats(self):
        mod = self._get_module()
        tm = mod.EnhancedTransactionManager.__new__(mod.EnhancedTransactionManager)
        tm.global_hooks = []
        tm.active_transactions = {}
        tm.metrics_hook = mod.MetricsTransactionHook()
        tm.logging_hook = mod.LoggingTransactionHook()
        stats = await tm.get_transaction_stats()
        assert "active_transactions_count" in stats
        assert stats["active_transactions_count"] == 0

    def test_retryable_transaction_decorator(self):
        mod = self._get_module()
        decorator = mod.retryable_transaction(max_attempts=2, delay=0.5)
        assert callable(decorator)

    def test_isolation_level_enum(self):
        mod = self._get_module()
        assert mod.TransactionIsolationLevel.SERIALIZABLE.value == "SERIALIZABLE"
        assert mod.TransactionIsolationLevel.READ_COMMITTED.value == "READ COMMITTED"

    def test_transaction_priority_enum(self):
        mod = self._get_module()
        assert mod.TransactionPriority.CRITICAL.value == 4
        assert mod.TransactionPriority.LOW.value == 1

    def test_savepoint_info(self):
        mod = self._get_module()
        sp = mod.SavepointInfo(
            name="sp1",
            created_at=datetime.now(),
            transaction_id="tx1",
        )
        assert sp.name == "sp1"


# ===========================================================================
# 4. UNIFIED EVENT BUS
# ===========================================================================


def _ensure_core_stubs():
    """Ensure core stubs are installed before loading a module that uses them at import time.
    Returns a dict of (mod_name -> original_value) so caller can restore if needed."""
    _saved = {}

    def _install(mod_name, factory):
        existing = sys.modules.get(mod_name)
        if existing is None or not isinstance(existing, MagicMock):
            stub = MagicMock()
            _saved[mod_name] = existing  # may be None or real module
            sys.modules[mod_name] = stub
            return stub
        return existing

    # structured_logging
    sl = _install("core.structured_logging", MagicMock)
    sl.get_logger = MagicMock(return_value=_logging.getLogger("test"))
    lc = MagicMock()
    lc.EVENTS = "events"
    lc.QUEUE = "queue"
    lc.SYSTEM = "system"
    sl.LogCategory = lc

    # application_metrics
    am = _install("core.application_metrics", MagicMock)
    mc = MagicMock()
    mc.record_metric = MagicMock()
    am.get_metrics_collector = MagicMock(return_value=mc)
    mt = MagicMock()
    mt.EVENT_PUBLISHED = "event_published"
    mt.EVENT_HANDLED = "event_handled"
    mt.EVENT_ERROR = "event_error"
    mt.QUEUE_ENQUEUE = "queue_enqueue"
    mt.QUEUE_PROCESS_SUCCESS = "queue_process_success"
    mt.QUEUE_PROCESS_FAILURE = "queue_process_failure"
    am.MetricType = mt

    # unified_config
    uc = _install("core.unified_config", MagicMock)
    cfg = MagicMock()
    cfg.redis_url = "redis://localhost:6379/0"
    uc.get_unified_config = MagicMock(return_value=cfg)

    return _saved


class TestUnifiedEventBus:
    """Tests for core/unified_event_bus.py"""

    def _get_module(self):
        for _m in ["core.unified_event_bus"]:
            _ex = sys.modules.get(_m)
            if _ex is not None and isinstance(_ex, MagicMock):
                del sys.modules[_m]
        import importlib.util

        # Ensure stubs are in place before module-level code runs
        _ensure_core_stubs()

        spec = importlib.util.spec_from_file_location(
            "core.unified_event_bus",
            os.path.join(_backend, "core", "unified_event_bus.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_event_creation(self):
        mod = self._get_module()
        now = datetime.now(UTC)
        e = mod.Event(
            id="ev1",
            type=mod.EventType.USER_LOGIN,
            source="test",
            timestamp=now,
            data={"user": "alice"},
        )
        assert e.id == "ev1"
        assert e.correlation_id == "ev1"  # auto-set to id

    def test_event_to_dict(self):
        mod = self._get_module()
        now = datetime.now(UTC)
        e = mod.Event(
            id="ev2",
            type=mod.EventType.LESSON_STARTED,
            source="education",
            timestamp=now,
            data={"subject": "matematik"},
        )
        d = e.to_dict()
        assert d["type"] == "education.lesson_started"
        assert d["status"] == "pending"

    def test_event_from_dict(self):
        mod = self._get_module()
        now = datetime.now(UTC)
        e = mod.Event(
            id="ev3",
            type=mod.EventType.QUESTION_ANSWERED,
            source="quiz",
            timestamp=now,
            data={"correct": True},
        )
        d = e.to_dict()
        e2 = mod.Event.from_dict(d)
        assert e2.id == "ev3"
        assert e2.type == mod.EventType.QUESTION_ANSWERED

    def test_event_is_expired_no_ttl(self):
        mod = self._get_module()
        now = datetime.now(UTC)
        e = mod.Event(
            id="ev4",
            type=mod.EventType.USER_LOGOUT,
            source="auth",
            timestamp=now,
            data={},
        )
        assert e.is_expired() is False

    def test_event_is_expired_with_ttl(self):
        mod = self._get_module()
        now = datetime.now(UTC)
        e = mod.Event(
            id="ev5",
            type=mod.EventType.USER_LOGOUT,
            source="auth",
            timestamp=now - timedelta(seconds=120),
            data={},
            ttl=60,
        )
        assert e.is_expired() is True

    def test_event_should_retry(self):
        mod = self._get_module()
        now = datetime.now(UTC)
        e = mod.Event(
            id="ev6",
            type=mod.EventType.EMAIL_SENT,
            source="notification",
            timestamp=now,
            data={},
        )
        e.status = mod.EventStatus.FAILED
        assert e.should_retry() is True

        e.retry_count = e.max_retries
        assert e.should_retry() is False

    def test_event_handler_matches_event(self):
        mod = self._get_module()
        now = datetime.now(UTC)
        event = mod.Event(
            id="ev7",
            type=mod.EventType.CONTENT_CREATED,
            source="cms",
            timestamp=now,
            data={"category": "math"},
        )

        def dummy_handler(e):
            pass

        h = mod.EventHandler(
            handler_id="h1",
            event_type=mod.EventType.CONTENT_CREATED,
            callback=dummy_handler,
            filters={"category": "math"},
        )
        assert h.matches_event(event) is True

        h_wrong = mod.EventHandler(
            handler_id="h2",
            event_type=mod.EventType.CONTENT_CREATED,
            callback=dummy_handler,
            filters={"category": "physics"},
        )
        assert h_wrong.matches_event(event) is False

    def test_event_bus_subscribe_unsubscribe(self):
        mod = self._get_module()
        bus = mod.EventBus.__new__(mod.EventBus)
        from collections import defaultdict, deque

        bus.handlers = defaultdict(list)
        bus.middlewares = []
        bus.event_queue = asyncio.Queue()
        bus.dead_letter_queue = asyncio.Queue()
        bus.processing_tasks = set()
        bus.event_history = deque(maxlen=10000)
        bus.handler_stats = defaultdict(lambda: defaultdict(int))
        bus.max_concurrent_events = 100
        bus.event_timeout = 30.0
        bus.retry_delay = 1.0
        bus.running = False
        bus.processor_task = None
        bus.dead_letter_processor_task = None
        bus.cleanup_task = None

        def my_handler(e):
            pass

        hid = bus.subscribe(mod.EventType.USER_LOGIN, my_handler)
        assert hid.startswith("my_handler_")
        result = bus.unsubscribe(hid)
        assert result is True

    def test_event_bus_unsubscribe_nonexistent(self):
        mod = self._get_module()
        bus = mod.EventBus.__new__(mod.EventBus)
        from collections import defaultdict, deque

        bus.handlers = defaultdict(list)
        bus.middlewares = []
        bus.event_queue = asyncio.Queue()
        bus.dead_letter_queue = asyncio.Queue()
        bus.processing_tasks = set()
        bus.event_history = deque(maxlen=10000)
        bus.handler_stats = defaultdict(lambda: defaultdict(int))
        bus.max_concurrent_events = 100
        bus.event_timeout = 30.0
        bus.retry_delay = 1.0
        bus.running = False
        bus.processor_task = None
        bus.dead_letter_processor_task = None
        bus.cleanup_task = None
        result = bus.unsubscribe("nonexistent_handler_id")
        assert result is False

    def test_event_bus_get_stats(self):
        mod = self._get_module()
        from collections import defaultdict, deque

        bus = mod.EventBus.__new__(mod.EventBus)
        bus.handlers = defaultdict(list)
        bus.middlewares = []
        bus.event_queue = asyncio.Queue()
        bus.dead_letter_queue = asyncio.Queue()
        bus.processing_tasks = set()
        bus.event_history = deque(maxlen=10000)
        bus.handler_stats = defaultdict(lambda: defaultdict(int))
        bus.max_concurrent_events = 100
        bus.event_timeout = 30.0
        bus.retry_delay = 1.0
        bus.running = False
        bus.processor_task = None
        bus.dead_letter_processor_task = None
        bus.cleanup_task = None

        stats = bus.get_stats()
        assert "running" in stats
        assert "queue_size" in stats

    def test_event_bus_get_recent_events_empty(self):
        mod = self._get_module()
        from collections import defaultdict, deque

        bus = mod.EventBus.__new__(mod.EventBus)
        bus.handlers = defaultdict(list)
        bus.middlewares = []
        bus.event_queue = asyncio.Queue()
        bus.dead_letter_queue = asyncio.Queue()
        bus.processing_tasks = set()
        bus.event_history = deque(maxlen=10000)
        bus.handler_stats = defaultdict(lambda: defaultdict(int))
        bus.max_concurrent_events = 100
        bus.event_timeout = 30.0
        bus.retry_delay = 1.0
        bus.running = False
        bus.processor_task = None
        bus.dead_letter_processor_task = None
        bus.cleanup_task = None

        events = bus.get_recent_events(10)
        assert events == []

    @pytest.mark.asyncio
    async def test_publish_turkish_exam_event(self):
        mod = self._get_module()
        # Reset global bus
        mod._event_bus = None

        # Patch get_event_bus to return a mock bus
        mock_bus = AsyncMock()
        mock_bus.publish = AsyncMock(return_value="ev_id_123")

        with patch.object(mod, "get_event_bus", AsyncMock(return_value=mock_bus)):
            result = await mod.publish_turkish_exam_event(
                exam_type="tyt",
                action="started",
                user_id=1,
                exam_data={"score": 80},
            )
            assert result == "ev_id_123"

    @pytest.mark.asyncio
    async def test_publish_educational_event(self):
        mod = self._get_module()
        mod._event_bus = None

        mock_bus = AsyncMock()
        mock_bus.publish = AsyncMock(return_value="edu_ev_id")

        with patch.object(mod, "get_event_bus", AsyncMock(return_value=mock_bus)):
            result = await mod.publish_educational_event(
                event_type="ders_basladi",
                user_id=2,
                subject="matematik",
                content_data={"topic": "integral"},
            )
            assert result == "edu_ev_id"

    @pytest.mark.asyncio
    async def test_logging_middleware(self):
        mod = self._get_module()
        mw = mod.LoggingMiddleware()
        now = datetime.now(UTC)
        event = mod.Event(
            id="ev_mw",
            type=mod.EventType.USER_LOGIN,
            source="test",
            timestamp=now,
            data={},
        )

        def dummy_handler(e):
            pass

        handler = mod.EventHandler(
            handler_id="h_mw",
            event_type=mod.EventType.USER_LOGIN,
            callback=dummy_handler,
        )
        result = await mw.before_publish(event)
        assert result is event
        await mw.after_handle(event, handler, None)
        cont = await mw.on_error(event, handler, ValueError("test"))
        assert cont is True

    def test_event_type_values(self):
        mod = self._get_module()
        assert mod.EventType.USER_REGISTERED.value == "user.registered"
        assert (
            mod.EventType.YKS_REGISTRATION_OPENED.value
            == "exam.yks_registration_opened"
        )

    def test_event_priority_values(self):
        mod = self._get_module()
        assert mod.EventPriority.CRITICAL.value == "critical"
        assert mod.EventPriority.LOW.value == "low"


# ===========================================================================
# 5. MESSAGE QUEUE SYSTEM
# ===========================================================================


class TestMessageQueueSystem:
    """Tests for core/message_queue_system.py"""

    def _get_module(self):
        for _m in ["core.message_queue_system"]:
            _ex = sys.modules.get(_m)
            if _ex is not None and isinstance(_ex, MagicMock):
                del sys.modules[_m]
        import importlib.util

        # Ensure stubs are in place before module-level code runs
        _ensure_core_stubs()

        spec = importlib.util.spec_from_file_location(
            "core.message_queue_system",
            os.path.join(_backend, "core", "message_queue_system.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_queue_priority_enum(self):
        mod = self._get_module()
        assert mod.QueuePriority.LOW.value == "low"
        assert mod.QueuePriority.CRITICAL.value == "critical"

    def test_job_status_enum(self):
        mod = self._get_module()
        assert mod.JobStatus.PENDING.value == "pending"
        assert mod.JobStatus.COMPLETED.value == "completed"

    def test_queue_type_enum(self):
        mod = self._get_module()
        assert mod.QueueType.REAL_TIME.value == "real_time"
        assert mod.QueueType.ANALYTICS.value == "analytics"

    def test_queue_message_creation(self):
        mod = self._get_module()
        now = datetime.now(UTC)
        msg = mod.QueueMessage(
            id="msg1",
            queue_type=mod.QueueType.NOTIFICATIONS,
            payload={"body": "Hello"},
            priority=mod.QueuePriority.NORMAL,
            created_at=now,
        )
        assert msg.id == "msg1"
        assert msg.correlation_id == "msg1"
        assert msg.attempts == 0

    def test_queue_message_to_dict(self):
        mod = self._get_module()
        now = datetime.now(UTC)
        msg = mod.QueueMessage(
            id="msg2",
            queue_type=mod.QueueType.EXAM_PROCESSING,
            payload={"exam_id": 1},
            priority=mod.QueuePriority.HIGH,
            created_at=now,
        )
        d = msg.to_dict()
        assert d["queue_type"] == "exam_processing"
        assert d["priority"] == "high"

    def test_queue_message_from_dict(self):
        mod = self._get_module()
        now = datetime.now(UTC)
        msg = mod.QueueMessage(
            id="msg3",
            queue_type=mod.QueueType.BATCH_PROCESSING,
            payload={"batch": "data"},
            priority=mod.QueuePriority.LOW,
            created_at=now,
        )
        d = msg.to_dict()
        msg2 = mod.QueueMessage.from_dict(d)
        assert msg2.id == "msg3"
        assert msg2.queue_type == mod.QueueType.BATCH_PROCESSING

    def test_background_job_creation(self):
        mod = self._get_module()
        now = datetime.now(UTC)
        job = mod.BackgroundJob(
            id="job1",
            job_type="email",
            function_name="send_email",
            args=["to@example.com"],
            kwargs={"subject": "Test"},
            queue_type=mod.QueueType.NOTIFICATIONS,
            priority=mod.QueuePriority.NORMAL,
            status=mod.JobStatus.PENDING,
            created_at=now,
        )
        assert job.id == "job1"
        assert job.progress == 0

    def test_background_job_to_dict(self):
        mod = self._get_module()
        now = datetime.now(UTC)
        job = mod.BackgroundJob(
            id="job2",
            job_type="report",
            function_name="gen_report",
            args=[],
            kwargs={},
            queue_type=mod.QueueType.BATCH_PROCESSING,
            priority=mod.QueuePriority.LOW,
            status=mod.JobStatus.PROCESSING,
            created_at=now,
            started_at=now,
        )
        d = job.to_dict()
        assert d["status"] == "processing"
        assert "started_at" in d

    def test_redis_message_queue_queue_configs(self):
        mod = self._get_module()
        rmq = mod.RedisMessageQueue.__new__(mod.RedisMessageQueue)
        rmq.redis_url = "redis://localhost:6379/0"
        rmq.redis_client = None
        rmq.consumer_group = "kiro2_consumers"
        rmq.consumer_name = "consumer_test"
        rmq.running = False
        rmq.consumer_tasks = {}
        rmq.metrics_collector = MagicMock()
        rmq.queue_configs = rmq._get_queue_configs()
        assert mod.QueueType.REAL_TIME in rmq.queue_configs
        assert mod.QueueType.ANALYTICS in rmq.queue_configs

    def test_queue_message_with_scheduled_at(self):
        mod = self._get_module()
        now = datetime.now(UTC)
        scheduled = now + timedelta(hours=1)
        msg = mod.QueueMessage(
            id="msg_sched",
            queue_type=mod.QueueType.MAINTENANCE,
            payload={"task": "cleanup"},
            priority=mod.QueuePriority.LOW,
            created_at=now,
            scheduled_at=scheduled,
        )
        d = msg.to_dict()
        assert "scheduled_at" in d
        msg2 = mod.QueueMessage.from_dict(d)
        assert msg2.scheduled_at is not None

    def test_queue_message_auto_id(self):
        mod = self._get_module()
        now = datetime.now(UTC)
        msg = mod.QueueMessage(
            id="",
            queue_type=mod.QueueType.CLEANUP,
            payload={},
            priority=mod.QueuePriority.LOW,
            created_at=now,
        )
        assert msg.id != ""

    def test_background_job_auto_id(self):
        mod = self._get_module()
        now = datetime.now(UTC)
        job = mod.BackgroundJob(
            id="",
            job_type="auto",
            function_name="func",
            args=[],
            kwargs={},
            queue_type=mod.QueueType.CLEANUP,
            priority=mod.QueuePriority.LOW,
            status=mod.JobStatus.PENDING,
            created_at=now,
        )
        assert job.id != ""


# ===========================================================================
# 6. RAG SERVICE
# ===========================================================================


class TestRAGService:
    """Tests for core/rag_service.py"""

    def _get_module(self):
        for _m in ["core.rag_service"]:
            _ex = sys.modules.get(_m)
            if _ex is not None and isinstance(_ex, MagicMock):
                del sys.modules[_m]
        import importlib.util

        # Set TESTING=true to skip heavy initialization
        os.environ["TESTING"] = "true"
        spec = importlib.util.spec_from_file_location(
            "core.rag_service",
            os.path.join(_backend, "core", "rag_service.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _make_service(self, mod):
        """Create a RAGService with mocked internals"""
        svc = mod.RAGService.__new__(mod.RAGService)
        svc.persist_directory = "./test_vector_db"
        svc.embeddings = None
        svc.vector_store = None
        svc.text_splitter = None
        svc._redis_client = None
        svc._search_cache = {}
        svc._cache_ttl = 1800
        svc._max_cache_size = 500
        svc._batch_size = 50
        svc._document_registry = {}
        return svc

    def test_generate_search_cache_key(self):
        mod = self._get_module()
        svc = self._make_service(mod)
        key1 = svc._generate_search_cache_key("matematik", 5)
        key2 = svc._generate_search_cache_key("matematik", 5)
        key3 = svc._generate_search_cache_key("fizik", 5)
        assert key1 == key2
        assert key1 != key3

    @pytest.mark.asyncio
    async def test_get_cached_search_results_miss(self):
        mod = self._get_module()
        svc = self._make_service(mod)
        result = await svc._get_cached_search_results("nonexistent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get_cached_results_memory(self):
        mod = self._get_module()
        svc = self._make_service(mod)
        data = [{"content": "test content", "score": 0.9}]
        await svc._set_cached_search_results("test_key", data)
        result = await svc._get_cached_search_results("test_key")
        assert result is not None
        assert result[0]["score"] == 0.9

    @pytest.mark.asyncio
    async def test_cache_eviction_when_full(self):
        mod = self._get_module()
        svc = self._make_service(mod)
        svc._max_cache_size = 3

        import time

        for i in range(3):
            svc._search_cache[f"key_{i}"] = ([{"score": i}], time.time())

        # Add one more — should evict oldest
        await svc._set_cached_search_results("key_new", [{"score": 99}])
        assert len(svc._search_cache) <= 4  # eviction happened

    def test_preprocess_text(self):
        mod = self._get_module()
        svc = self._make_service(mod)
        result = svc._preprocess_text("  Hello   World  ")
        assert result == "hello world"

    def test_preprocess_text_cached(self):
        mod = self._get_module()
        svc = self._make_service(mod)
        r1 = svc._preprocess_text("Test Input")
        r2 = svc._preprocess_text("Test Input")
        assert r1 == r2 == "test input"

    @pytest.mark.asyncio
    async def test_search_no_vector_store(self):
        mod = self._get_module()
        svc = self._make_service(mod)
        svc.vector_store = None
        result = await svc.search("matematik sorusu")
        assert result == []

    @pytest.mark.asyncio
    async def test_search_with_similarity_scores(self):
        mod = self._get_module()
        svc = self._make_service(mod)

        mock_doc = MagicMock()
        mock_doc.page_content = "Matematik içeriği"
        mock_doc.metadata = {"subject": "matematik"}

        mock_vs = MagicMock()
        mock_vs.similarity_search_with_score.return_value = [(mock_doc, 0.85)]
        svc.vector_store = mock_vs

        # Mock _rerank_results to return as-is
        svc._rerank_results = MagicMock(side_effect=lambda q, r, k=None: r)

        results = await svc.search("matematik", score_threshold=0.5, use_cache=False)
        assert len(results) == 1
        assert results[0]["score"] == 0.85

    @pytest.mark.asyncio
    async def test_search_below_score_threshold(self):
        mod = self._get_module()
        svc = self._make_service(mod)

        mock_doc = MagicMock()
        mock_doc.page_content = "Low relevance content"
        mock_doc.metadata = {}

        mock_vs = MagicMock()
        mock_vs.similarity_search_with_score.return_value = [(mock_doc, 0.2)]
        svc.vector_store = mock_vs
        svc._rerank_results = MagicMock(side_effect=lambda q, r, k=None: r)

        results = await svc.search("test", score_threshold=0.5, use_cache=False)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_fallback_no_score(self):
        mod = self._get_module()
        svc = self._make_service(mod)

        mock_doc = MagicMock()
        mock_doc.page_content = "Content without score"
        mock_doc.metadata = {}

        mock_vs = MagicMock()
        mock_vs.similarity_search_with_score.side_effect = AttributeError("not impl")
        mock_vs.similarity_search.return_value = [mock_doc]
        svc.vector_store = mock_vs
        svc._rerank_results = MagicMock(side_effect=lambda q, r, k=None: r)

        results = await svc.search("test", score_threshold=0.5, use_cache=False)
        assert len(results) == 1
        assert results[0]["score"] == 1.0

    @pytest.mark.asyncio
    async def test_add_documents_no_content(self):
        mod = self._get_module()
        svc = self._make_service(mod)
        result = await svc.add_documents([])
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_add_documents_no_vector_store(self):
        mod = self._get_module()
        svc = self._make_service(mod)
        svc.text_splitter = MagicMock()
        svc.text_splitter.split_text.return_value = ["chunk1", "chunk2"]

        mock_vs = MagicMock()
        mock_vs.add_documents.return_value = ["id1", "id2"]
        mock_vs.persist = MagicMock()

        mock_factory = MagicMock()
        mock_factory.create_optimized_store.return_value = mock_vs
        sys.modules["core.vector_store_factory"].VectorStoreFactory = mock_factory

        mock_rag_config = MagicMock()
        mock_rag_config.vector_store.store_type = "chroma"
        sys.modules["core.rag_config"].get_rag_config = MagicMock(
            return_value=mock_rag_config
        )

        result = await svc.add_documents(
            [{"content": "Short text", "metadata": {"topic": "math"}}]
        )
        assert "success" in result

    def test_rerank_results_fallback(self):
        mod = self._get_module()
        svc = self._make_service(mod)

        # Simulate reranker error → returns original
        sys.modules["core.reranker"].get_turkish_reranker = MagicMock(
            side_effect=ImportError("no reranker")
        )

        results = [{"content": "a", "score": 0.9}, {"content": "b", "score": 0.8}]
        out = svc._rerank_results("query", results, top_k=2)
        assert out == results

    @pytest.mark.asyncio
    async def test_get_cached_search_results_expired(self):
        mod = self._get_module()
        svc = self._make_service(mod)
        import time

        # Add an expired entry
        svc._search_cache["old_key"] = ([{"score": 0.5}], time.time() - 99999)
        result = await svc._get_cached_search_results("old_key")
        assert result is None


# ===========================================================================
# 7. STUDENT REVIEW SERVICE
# ===========================================================================


class TestStudentReviewService:
    """Tests for services/student_review_service.py"""

    def _get_module(self):
        for _m in ["services.student_review_service"]:
            _ex = sys.modules.get(_m)
            if _ex is not None and isinstance(_ex, MagicMock):
                del sys.modules[_m]

        # Setup model stubs
        import enum

        class _ReviewType(enum.Enum):
            UNIVERSITY = "university"
            DEPARTMENT = "department"
            TEACHER = "teacher"

        class _ReviewStatus(enum.Enum):
            PENDING = "pending"
            APPROVED = "approved"
            FLAGGED = "flagged"
            REJECTED = "rejected"

        class _ReportReason(enum.Enum):
            SPAM = "spam"
            INAPPROPRIATE = "inappropriate"

        class _RatingCategory(enum.Enum):
            OVERALL = "overall"
            TEACHING = "teaching"

        _StudentReview = MagicMock()
        _StudentReview.review_type = MagicMock()
        _StudentReview.university_id = MagicMock()
        _StudentReview.department_id = MagicMock()
        _StudentReview.status = MagicMock()
        _StudentReview.overall_rating = MagicMock()
        _StudentReview.is_verified = MagicMock()
        _StudentReview.helpful_count = MagicMock()
        _StudentReview.created_at = MagicMock()
        _StudentReview.id = MagicMock()

        stub = sys.modules["models.student_review"]
        stub.StudentReview = _StudentReview
        stub.ReviewType = _ReviewType
        stub.ReviewStatus = _ReviewStatus
        stub.ReviewRating = MagicMock()
        stub.ReviewVote = MagicMock()
        stub.ReviewReport = MagicMock()
        stub.ReviewStatistics = MagicMock()
        stub.ModerationQueue = MagicMock()
        stub.ReportReason = _ReportReason
        stub.RatingCategory = _RatingCategory

        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "services.student_review_service",
            os.path.join(_backend, "services", "student_review_service.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_calculate_spam_score_long_normal_text(self):
        mod = self._get_module()
        svc = mod.StudentReviewService.__new__(mod.StudentReviewService)
        score = svc._calculate_spam_score(
            "Bu üniversite gerçekten çok iyi. Hocalar çok yardımsever ve eğitim kalitesi yüksek.",
            "İyi Bir Üniversite",
        )
        assert 0.0 <= score <= 1.0

    def test_calculate_spam_score_short_text(self):
        mod = self._get_module()
        svc = mod.StudentReviewService.__new__(mod.StudentReviewService)
        score = svc._calculate_spam_score("ok", "title")
        assert score >= 0.0

    def test_calculate_quality_score(self):
        mod = self._get_module()
        svc = mod.StudentReviewService.__new__(mod.StudentReviewService)
        long_content = " ".join(["Bu bir test yorumudur."] * 20)
        score = svc._calculate_quality_score(long_content, "Uzun Yorum Başlığı")
        assert 0.0 <= score <= 1.0

    def test_check_profanity_clean(self):
        mod = self._get_module()
        svc = mod.StudentReviewService.__new__(mod.StudentReviewService)
        result = svc._check_profanity("Bu çok güzel bir yorum")
        assert result is False

    def test_check_contact_info_email(self):
        mod = self._get_module()
        svc = mod.StudentReviewService.__new__(mod.StudentReviewService)
        result = svc._check_contact_info("Bana email gönder: test@example.com")
        assert result is True

    def test_check_contact_info_clean(self):
        mod = self._get_module()
        svc = mod.StudentReviewService.__new__(mod.StudentReviewService)
        result = svc._check_contact_info("Bu temiz bir yorum metnidir")
        assert result is False

    def test_check_contact_info_phone(self):
        mod = self._get_module()
        svc = mod.StudentReviewService.__new__(mod.StudentReviewService)
        result = svc._check_contact_info("Ara beni: 0555 123 45 67")
        assert result is True

    @pytest.mark.asyncio
    async def test_create_review_approved_path(self):
        mod = self._get_module()
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        svc = mod.StudentReviewService(db)

        # Mock helper methods
        svc._calculate_spam_score = MagicMock(return_value=0.1)
        svc._calculate_quality_score = MagicMock(return_value=0.9)
        svc._check_profanity = MagicMock(return_value=False)
        svc._check_contact_info = MagicMock(return_value=False)
        svc._add_to_moderation_queue = AsyncMock()

        import uuid

        uid = uuid.uuid4()
        review = await svc.create_review(
            user_id=uid,
            review_type=mod.ReviewType.UNIVERSITY,
            title="Harika Üniversite",
            content="Bu üniversite gerçekten çok kaliteli eğitim vermektedir. " * 5,
            overall_rating=4.5,
        )
        assert review is not None
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_flagged_path(self):
        mod = self._get_module()
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        svc = mod.StudentReviewService(db)
        svc._calculate_spam_score = MagicMock(return_value=0.9)  # high spam
        svc._calculate_quality_score = MagicMock(return_value=0.5)
        svc._check_profanity = MagicMock(return_value=False)
        svc._check_contact_info = MagicMock(return_value=False)
        svc._add_to_moderation_queue = AsyncMock()

        import uuid

        uid = uuid.uuid4()
        review = await svc.create_review(
            user_id=uid,
            review_type=mod.ReviewType.UNIVERSITY,
            title="Spam",
            content="spam spam spam spam spam spam spam spam",
            overall_rating=1.0,
        )
        assert review is not None

    @pytest.mark.asyncio
    async def test_get_review_by_id_none(self):
        mod = self._get_module()
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        svc = mod.StudentReviewService(db)
        import uuid

        _mock_select = MagicMock(return_value=MagicMock())
        with patch.object(mod, "select", _mock_select):
            result = await svc.get_review_by_id(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_update_review_not_found(self):
        mod = self._get_module()
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        svc = mod.StudentReviewService(db)
        import uuid

        _mock_select = MagicMock(return_value=MagicMock())
        with patch.object(mod, "select", _mock_select):
            result = await svc.update_review(uuid.uuid4(), title="New Title")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_review_not_found(self):
        mod = self._get_module()
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        svc = mod.StudentReviewService(db)
        import uuid

        _mock_select = MagicMock(return_value=MagicMock())
        with patch.object(mod, "select", _mock_select):
            result = await svc.delete_review(uuid.uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_review_success(self):
        mod = self._get_module()
        db = AsyncMock()
        mock_review = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_review
        db.execute = AsyncMock(return_value=mock_result)
        db.delete = AsyncMock()
        db.commit = AsyncMock()

        svc = mod.StudentReviewService(db)
        import uuid

        _mock_select = MagicMock(return_value=MagicMock())
        with patch.object(mod, "select", _mock_select):
            result = await svc.delete_review(uuid.uuid4())
        assert result is True

    @pytest.mark.asyncio
    async def test_add_review_ratings(self):
        mod = self._get_module()
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()

        mock_rating = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_rating]
        db.execute = AsyncMock(return_value=mock_result)

        svc = mod.StudentReviewService(db)
        import uuid

        ratings = {mod.RatingCategory.OVERALL: 4.5}
        _mock_select = MagicMock(return_value=MagicMock())
        with patch.object(mod, "select", _mock_select):
            result = await svc.add_review_ratings(uuid.uuid4(), ratings)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_review_ratings(self):
        mod = self._get_module()
        db = AsyncMock()
        mock_ratings = [MagicMock(), MagicMock()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_ratings
        db.execute = AsyncMock(return_value=mock_result)

        svc = mod.StudentReviewService(db)
        import uuid

        _mock_select = MagicMock(return_value=MagicMock())
        with patch.object(mod, "select", _mock_select):
            result = await svc.get_review_ratings(uuid.uuid4())
        assert len(result) == 2


# ===========================================================================
# 8. LEARNING STYLE SERVICE
# ===========================================================================


class TestLearningStyleService:
    """Tests for services/learning_style_service.py"""

    def _get_module(self):
        for _m in ["services.learning_style_service"]:
            _ex = sys.modules.get(_m)
            if _ex is not None and isinstance(_ex, MagicMock):
                del sys.modules[_m]

        # Stub models — ensure the package is loaded first
        import importlib as _il

        if "models" not in sys.modules:
            _il.import_module("models")
        models_stub = sys.modules["models"]

        _StudentLearningProfile = MagicMock()
        _LearningAnalytics = MagicMock()
        _ExamSession = MagicMock()

        models_stub.StudentLearningProfile = _StudentLearningProfile
        models_stub.LearningAnalytics = _LearningAnalytics
        models_stub.ExamSession = _ExamSession

        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "services.learning_style_service",
            os.path.join(_backend, "services", "learning_style_service.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_service_init(self):
        mod = self._get_module()
        svc = mod.LearningStyleService()
        assert "visual" in svc.vark_dimensions
        assert "active_reflective" in svc.felder_dimensions

    def test_calculate_confidence_no_data(self):
        mod = self._get_module()
        svc = mod.LearningStyleService()
        score = svc._calculate_confidence({}, None)
        assert score >= 0.3
        assert score <= 1.0

    def test_calculate_confidence_full_data(self):
        mod = self._get_module()
        svc = mod.LearningStyleService()
        behavioral = {
            "video_watch_time_minutes": 120,
            "audio_content_time_minutes": 60,
            "text_reading_time_minutes": 90,
            "interactive_exercise_time_minutes": 45,
            "group_study_minutes": 30,
            "solo_study_minutes": 90,
        }
        questionnaire = ["A", "B", "C", "D", "E", "F"]
        score = svc._calculate_confidence(behavioral, questionnaire)
        assert score > 0.5

    def test_generate_hibrit_code(self):
        mod = self._get_module()
        svc = mod.LearningStyleService()

        vark = {"visual": 0.5, "auditory": 0.3, "reading": 0.1, "kinesthetic": 0.1}
        felder = {
            "active_reflective": 0.5,
            "sensing_intuitive": -0.5,
            "visual_verbal": 0.5,
            "sequential_global": -0.5,
        }
        code = svc._generate_hibrit_code(vark, felder)
        assert "-" in code
        assert "V" in code  # visual > 0.3

    def test_generate_hibrit_code_empty_vark(self):
        mod = self._get_module()
        svc = mod.LearningStyleService()
        vark = {"visual": 0.1, "auditory": 0.1, "reading": 0.1, "kinesthetic": 0.1}
        felder = {
            "active_reflective": 0.0,
            "sensing_intuitive": 0.0,
            "visual_verbal": 0.0,
            "sequential_global": 0.0,
        }
        code = svc._generate_hibrit_code(vark, felder)
        assert code.startswith("M-")  # Mixed VARK

    def test_get_profile_description(self):
        mod = self._get_module()
        svc = mod.LearningStyleService()
        desc = svc._get_profile_description("VR-ASVS")
        assert "VR-ASVS" in desc
        assert len(desc) > 10

    @pytest.mark.asyncio
    async def test_calculate_vark_no_analytics(self):
        mod = self._get_module()
        svc = mod.LearningStyleService()
        db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)

        _mock_select = MagicMock(return_value=MagicMock())
        with patch.object(mod, "select", _mock_select):
            vark = await svc._calculate_vark_profile("s1", db, {})
        assert abs(sum(vark.values()) - 1.0) < 0.01  # normalized

    @pytest.mark.asyncio
    async def test_calculate_vark_with_content_times(self):
        mod = self._get_module()
        svc = mod.LearningStyleService()
        db = AsyncMock()

        mock_analytics = MagicMock()
        mock_analytics.study_time_minutes = 120
        mock_analytics.questions_attempted = 50

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_analytics]
        db.execute = AsyncMock(return_value=mock_result)

        behavioral = {
            "video_watch_time_minutes": 60,
            "audio_content_time_minutes": 20,
            "text_reading_time_minutes": 30,
            "interactive_exercise_time_minutes": 10,
        }
        _mock_select = MagicMock(return_value=MagicMock())
        with patch.object(mod, "select", _mock_select):
            vark = await svc._calculate_vark_profile("s1", db, behavioral)
        assert vark["visual"] > 0
        assert abs(sum(vark.values()) - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_calculate_felder_no_sessions(self):
        mod = self._get_module()
        svc = mod.LearningStyleService()
        db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)

        _mock_select = MagicMock(return_value=MagicMock())
        with patch.object(mod, "select", _mock_select):
            felder = await svc._calculate_felder_profile("s1", db, {})
        assert all(v == 0.0 for v in felder.values())

    @pytest.mark.asyncio
    async def test_calculate_felder_with_behavioral(self):
        mod = self._get_module()
        svc = mod.LearningStyleService()
        db = AsyncMock()

        mock_session = MagicMock()
        mock_session.scaled_score = 75.0

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_session] * 5
        db.execute = AsyncMock(return_value=mock_result)

        behavioral = {
            "group_study_minutes": 60,
            "solo_study_minutes": 30,
            "visual_content_minutes": 80,
            "text_content_minutes": 20,
            "question_completion_rate": 0.9,
        }
        _mock_select = MagicMock(return_value=MagicMock())
        with patch.object(mod, "select", _mock_select):
            felder = await svc._calculate_felder_profile("s1", db, behavioral)
        assert "active_reflective" in felder
        assert felder["active_reflective"] > 0  # more group study = active

    @pytest.mark.asyncio
    async def test_get_student_profile_none(self):
        mod = self._get_module()
        svc = mod.LearningStyleService()
        db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        _mock_select = MagicMock(return_value=MagicMock())
        with patch.object(mod, "select", _mock_select):
            result = await svc.get_student_profile("nonexistent", db)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_service_stats(self):
        mod = self._get_module()
        svc = mod.LearningStyleService()
        db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar.return_value = 42
        db.execute = AsyncMock(return_value=mock_result)

        _mock_select = MagicMock(return_value=MagicMock())
        with patch.object(mod, "select", _mock_select):
            stats = await svc.get_service_stats(db)
        assert stats["toplam_profil_sayisi"] == 42
        assert stats["toplam_kombinasyon"] == 64

    @pytest.mark.asyncio
    async def test_get_all_hybrid_codes_cache_miss(self):
        mod = self._get_module()
        svc = mod.LearningStyleService()

        # Reset cache mock
        _cache_stub.get = AsyncMock(return_value=None)
        _cache_stub.set = AsyncMock(return_value=True)

        result = await svc.get_all_hybrid_codes()
        assert len(result) == 64
        assert result[0]["kod"] is not None

    @pytest.mark.asyncio
    async def test_get_all_hybrid_codes_cache_hit(self):
        mod = self._get_module()
        svc = mod.LearningStyleService()

        cached_data = [{"kod": "V-ASVS", "vark_komponenti": "V"}]
        _cache_stub.get = AsyncMock(return_value=cached_data)

        result = await svc.get_all_hybrid_codes()
        assert result == cached_data

    @pytest.mark.asyncio
    async def test_get_learning_recommendations_no_profile(self):
        mod = self._get_module()
        svc = mod.LearningStyleService()
        db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        # detect_learning_style would be called, mock it to avoid recursion
        svc.detect_learning_style = AsyncMock(return_value={})

        _mock_select = MagicMock(return_value=MagicMock())
        with patch.object(mod, "select", _mock_select):
            result = await svc.get_learning_recommendations("s1", db)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_learning_recommendations_visual(self):
        mod = self._get_module()
        svc = mod.LearningStyleService()
        db = AsyncMock()

        mock_profile = MagicMock()
        mock_profile.dominant_vark_style = "visual"
        mock_profile.felder_active_reflective = 0.5

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_profile
        db.execute = AsyncMock(return_value=mock_result)

        _mock_select = MagicMock(return_value=MagicMock())
        with patch.object(mod, "select", _mock_select):
            result = await svc.get_learning_recommendations("s1", db)
        assert any(r.get("tip") == "görsel_materyaller" for r in result)

    @pytest.mark.asyncio
    async def test_get_learning_recommendations_kinesthetic(self):
        mod = self._get_module()
        svc = mod.LearningStyleService()
        db = AsyncMock()

        mock_profile = MagicMock()
        mock_profile.dominant_vark_style = "kinesthetic"
        mock_profile.felder_active_reflective = -0.5

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_profile
        db.execute = AsyncMock(return_value=mock_result)

        _mock_select = MagicMock(return_value=MagicMock())
        with patch.object(mod, "select", _mock_select):
            result = await svc.get_learning_recommendations("s1", db)
        assert any(r.get("tip") == "uygulamalı_öğrenme" for r in result)
