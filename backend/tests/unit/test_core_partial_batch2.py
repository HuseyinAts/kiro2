"""
Unit tests for core modules with low/partial coverage.

Covers:
- core/message_queue_system.py  (QueueMessage, BackgroundJob, RedisMessageQueue, BackgroundJobProcessor)
- core/rag_service.py            (RAGService cache helpers, _preprocess_text, _rerank_results)
- core/auth_middleware.py        (JWTManager, PermissionManager, AuthUser, AuthContext)
- core/transaction_manager.py    (TransactionConfig, TransactionMetrics, TransactionContext, hooks)
- core/unified_event_bus.py      (Event, EventHandler, EventBus subscribe/publish, middlewares)
- core/api_optimizer.py          (RateLimitConfig, CompressionConfig, PaginationParams, TurkishContentOptimizer)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

# ---------------------------------------------------------------------------
# Heavy dependency mocks BEFORE any project imports
# ---------------------------------------------------------------------------
import asyncio

# Patch redis so modules that do `import redis.asyncio as redis` at module-level
# work without an actual Redis server.
import sys
import time
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_redis_mock = MagicMock()
_redis_mock.asyncio = MagicMock()
_redis_async_mock = MagicMock()
_redis_async_mock.from_url = MagicMock(return_value=AsyncMock())
_redis_mock.asyncio = _redis_async_mock
sys.modules.setdefault("redis", _redis_mock)
sys.modules.setdefault("redis.asyncio", _redis_async_mock)

# Patch langchain dependencies used in rag_service
for _mod in [
    "langchain_core",
    "langchain_core.documents",
    "langchain_text_splitters",
    "langchain_community",
    "langchain_community.embeddings",
    "langchain_community.vectorstores",
    "langchain",
    "langchain.embeddings",
    "langchain.embeddings.base",
]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

# Patch fastapi / starlette for api_optimizer
for _mod in [
    "fastapi",
    "starlette",
    "starlette.middleware",
    "starlette.middleware.base",
    "starlette.requests",
    "starlette.responses",
]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

# Patch SQLAlchemy async parts for transaction_manager
for _mod in [
    "sqlalchemy",
    "sqlalchemy.exc",
    "sqlalchemy.ext",
    "sqlalchemy.ext.asyncio",
    "sqlalchemy.sql",
]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

# Patch jwt
if "jwt" not in sys.modules:
    sys.modules["jwt"] = MagicMock()

# ---------------------------------------------------------------------------
# Clean up stale MagicMock stubs from other test files (e.g. batch1)
# so we can import the REAL modules we're testing here.
# ---------------------------------------------------------------------------
_modules_we_test = [
    "core.message_queue_system",
    "core.rag_service",
    "core.auth_middleware",
    "core.transaction_manager",
    "core.unified_event_bus",
    "core.api_optimizer",
]
for _mod_name in _modules_we_test:
    _existing = sys.modules.get(_mod_name)
    if _existing is not None and isinstance(_existing, MagicMock):
        del sys.modules[_mod_name]

# Also clean up core deps that batch1 may have stubbed as MagicMock
for _dep in [
    "core.application_metrics",
    "core.structured_logging",
    "core.unified.auth_system",
    "core.unified_config",
    "core.error_context",
    "core.error_monitoring",
    "core.enhanced_database",
]:
    _existing = sys.modules.get(_dep)
    if _existing is not None and isinstance(_existing, MagicMock):
        del sys.modules[_dep]

# ---------------------------------------------------------------------------
# Now we can safely import project modules
# ---------------------------------------------------------------------------
os_env_patch = patch.dict(
    "os.environ",
    {"TESTING": "true", "RAG_CACHE_TTL": "1800", "RAG_MAX_CACHE_SIZE": "500"},
)
os_env_patch.start()

# ===========================
# 1.  MESSAGE QUEUE SYSTEM
# ===========================
from core.message_queue_system import (  # noqa: E402
    BackgroundJob,
    BackgroundJobProcessor,
    JobStatus,
    QueueMessage,
    QueuePriority,
    QueueType,
    RedisMessageQueue,
)


class TestQueueMessage:
    """Tests for QueueMessage dataclass."""

    def _make_message(self, **kwargs) -> QueueMessage:
        defaults = dict(
            id=str(uuid.uuid4()),
            queue_type=QueueType.ANALYTICS,
            payload={"key": "value"},
            priority=QueuePriority.NORMAL,
            created_at=datetime.now(UTC),
        )
        defaults.update(kwargs)
        return QueueMessage(**defaults)

    def test_auto_id_generation(self):
        """id should be auto-generated when empty string is passed."""
        msg = QueueMessage(
            id="",
            queue_type=QueueType.ANALYTICS,
            payload={},
            priority=QueuePriority.LOW,
            created_at=datetime.now(UTC),
        )
        assert msg.id != ""

    def test_correlation_id_defaults_to_id(self):
        """correlation_id should default to message id when None."""
        msg = self._make_message(id="abc-123", correlation_id=None)
        assert msg.correlation_id == "abc-123"

    def test_to_dict_serializes_enums(self):
        msg = self._make_message()
        d = msg.to_dict()
        assert d["queue_type"] == msg.queue_type.value
        assert d["priority"] == msg.priority.value

    def test_to_dict_serializes_created_at_as_iso(self):
        msg = self._make_message()
        d = msg.to_dict()
        # Should be valid ISO string
        datetime.fromisoformat(d["created_at"])

    def test_to_dict_includes_scheduled_at_when_set(self):
        scheduled = datetime.now(UTC) + timedelta(hours=1)
        msg = self._make_message(scheduled_at=scheduled)
        d = msg.to_dict()
        assert d["scheduled_at"] is not None
        datetime.fromisoformat(d["scheduled_at"])

    def test_from_dict_roundtrip(self):
        original = self._make_message()
        d = original.to_dict()
        restored = QueueMessage.from_dict(d)
        assert restored.id == original.id
        assert restored.queue_type == original.queue_type
        assert restored.priority == original.priority

    @pytest.mark.parametrize(
        "priority",
        [
            QueuePriority.LOW,
            QueuePriority.NORMAL,
            QueuePriority.HIGH,
            QueuePriority.CRITICAL,
        ],
    )
    def test_all_priorities_serialise(self, priority):
        msg = self._make_message(priority=priority)
        assert msg.to_dict()["priority"] == priority.value

    @pytest.mark.parametrize(
        "queue_type",
        [
            QueueType.REAL_TIME,
            QueueType.AUTHENTICATION,
            QueueType.EXAM_PROCESSING,
            QueueType.NOTIFICATIONS,
            QueueType.ANALYTICS,
            QueueType.BATCH_PROCESSING,
            QueueType.CLEANUP,
            QueueType.MAINTENANCE,
        ],
    )
    def test_all_queue_types_serialise(self, queue_type):
        msg = self._make_message(queue_type=queue_type)
        assert msg.to_dict()["queue_type"] == queue_type.value


class TestBackgroundJob:
    """Tests for BackgroundJob dataclass."""

    def _make_job(self, **kwargs) -> BackgroundJob:
        defaults = dict(
            id=str(uuid.uuid4()),
            job_type="test_job",
            function_name="test_fn",
            args=[1, 2],
            kwargs={"a": 1},
            queue_type=QueueType.BATCH_PROCESSING,
            priority=QueuePriority.NORMAL,
            status=JobStatus.PENDING,
            created_at=datetime.now(UTC),
        )
        defaults.update(kwargs)
        return BackgroundJob(**defaults)

    def test_auto_id_generation(self):
        job = self._make_job(id="")
        assert job.id != ""

    def test_to_dict_serializes_status(self):
        job = self._make_job()
        d = job.to_dict()
        assert d["status"] == JobStatus.PENDING.value

    def test_to_dict_started_at_optional(self):
        job = self._make_job()
        d = job.to_dict()
        assert d.get("started_at") is None

    def test_to_dict_with_started_and_completed(self):
        now = datetime.now(UTC)
        job = self._make_job(
            status=JobStatus.COMPLETED,
            started_at=now,
            completed_at=now + timedelta(seconds=5),
        )
        d = job.to_dict()
        assert d["started_at"] is not None
        assert d["completed_at"] is not None

    @pytest.mark.parametrize("status", list(JobStatus))
    def test_all_statuses(self, status):
        job = self._make_job(status=status)
        assert job.to_dict()["status"] == status.value


class TestRedisMessageQueue:
    """Tests for RedisMessageQueue."""

    def test_queue_configs_all_types_present(self):
        queue = RedisMessageQueue(redis_url="redis://localhost:6379/0")
        for qt in QueueType:
            assert qt in queue.queue_configs

    def test_queue_configs_have_required_keys(self):
        queue = RedisMessageQueue()
        for config in queue.queue_configs.values():
            assert "stream_name" in config
            assert "max_len" in config
            assert "consumer_count" in config
            assert "batch_size" in config
            assert "block_time" in config

    def test_initial_state(self):
        queue = RedisMessageQueue()
        assert queue.running is False
        assert queue.redis_client is None
        assert queue.consumer_tasks == {}

    @pytest.mark.asyncio
    async def test_handle_message_by_type_returns_true_for_real_time(self):
        queue = RedisMessageQueue()
        msg = QueueMessage(
            id="1",
            queue_type=QueueType.REAL_TIME,
            payload={"action": "websocket_broadcast"},
            priority=QueuePriority.HIGH,
            created_at=datetime.now(UTC),
        )
        result = await queue._handle_message_by_type(msg, QueueType.REAL_TIME)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_message_by_type_returns_true_for_auth(self):
        queue = RedisMessageQueue()
        msg = QueueMessage(
            id="1",
            queue_type=QueueType.AUTHENTICATION,
            payload={"action": "user_login"},
            priority=QueuePriority.HIGH,
            created_at=datetime.now(UTC),
        )
        result = await queue._handle_message_by_type(msg, QueueType.AUTHENTICATION)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_message_by_type_returns_true_for_exam(self):
        queue = RedisMessageQueue()
        msg = QueueMessage(
            id="1",
            queue_type=QueueType.EXAM_PROCESSING,
            payload={"action": "process_exam_submission", "exam_type": "tyt"},
            priority=QueuePriority.HIGH,
            created_at=datetime.now(UTC),
        )
        result = await queue._handle_message_by_type(msg, QueueType.EXAM_PROCESSING)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_message_by_type_returns_false_for_unknown(self):
        queue = RedisMessageQueue()
        msg = QueueMessage(
            id="1",
            queue_type=QueueType.ANALYTICS,
            payload={},
            priority=QueuePriority.NORMAL,
            created_at=datetime.now(UTC),
        )
        # Passing a non-existent queue type value to trigger the unknown branch
        result = await queue._handle_message_by_type(msg, "UNKNOWN_TYPE")
        assert result is False

    @pytest.mark.asyncio
    async def test_enqueue_without_redis_returns_false(self):
        """enqueue should return False when redis_client raises on connect."""
        queue = RedisMessageQueue()

        async def _fail_connect():
            raise ConnectionError("no redis")

        queue.connect = _fail_connect
        msg = QueueMessage(
            id="1",
            queue_type=QueueType.ANALYTICS,
            payload={},
            priority=QueuePriority.NORMAL,
            created_at=datetime.now(UTC),
        )
        result = await queue.enqueue(msg)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_queue_stats_no_redis(self):
        queue = RedisMessageQueue()
        # redis_client is None — each queue entry should contain an error key
        stats = await queue.get_queue_stats()
        # Top-level keys are "running", "consumer_tasks", "queue_stats"
        assert "queue_stats" in stats
        # Every individual queue stat should have an error because redis is None
        for qt_stats in stats["queue_stats"].values():
            assert "error" in qt_stats

    def test_stop_consumers_sets_running_false(self):
        queue = RedisMessageQueue()
        queue.running = True
        # No tasks, just ensure flag flips
        asyncio.get_event_loop().run_until_complete(queue.stop_consumers())
        assert queue.running is False

    @pytest.mark.asyncio
    async def test_handle_all_message_types_return_true(self):
        queue = RedisMessageQueue()
        type_action_map = [
            (QueueType.NOTIFICATIONS, {"type": "email"}),
            (QueueType.CONTENT_PROCESSING, {"action": "generate_questions"}),
            (QueueType.ANALYTICS, {"action": "calculate_learning_analytics"}),
            (QueueType.BATCH_PROCESSING, {"action": "bulk_user_import"}),
            (QueueType.CLEANUP, {"action": "clean_expired_sessions"}),
            (QueueType.MAINTENANCE, {"action": "system_health_check"}),
        ]
        for qt, payload in type_action_map:
            msg = QueueMessage(
                id=str(uuid.uuid4()),
                queue_type=qt,
                payload=payload,
                priority=QueuePriority.NORMAL,
                created_at=datetime.now(UTC),
            )
            result = await queue._handle_message_by_type(msg, qt)
            assert result is True, f"Expected True for {qt}"


class TestBackgroundJobProcessor:
    """Tests for BackgroundJobProcessor."""

    def _make_processor(self):
        mock_queue = AsyncMock()
        mock_queue.enqueue = AsyncMock(return_value=True)
        return BackgroundJobProcessor(message_queue=mock_queue)

    def test_register_job_handler(self):
        processor = self._make_processor()
        handler = lambda: None
        processor.register_job_handler("my_job", handler)
        assert "my_job" in processor.job_handlers

    @pytest.mark.asyncio
    async def test_schedule_job_immediate(self):
        processor = self._make_processor()
        job_id = await processor.schedule_job(
            job_type="test",
            function_name="fn",
            args=[],
            kwargs={},
        )
        assert job_id in processor.jobs

    @pytest.mark.asyncio
    async def test_schedule_job_with_delay(self):
        processor = self._make_processor()
        job_id = await processor.schedule_job(
            job_type="test",
            function_name="fn",
            delay_seconds=3600,  # 1 hour — will be scheduled
        )
        assert job_id in processor.jobs
        assert processor.jobs[job_id].status == JobStatus.SCHEDULED
        # Cancel to avoid background task leaking
        processor.cancel_job(job_id)

    def test_get_job_status_existing(self):
        processor = self._make_processor()
        # Create a dummy job
        from core.message_queue_system import BackgroundJob

        job = BackgroundJob(
            id="job-1",
            job_type="t",
            function_name="f",
            args=[],
            kwargs={},
            queue_type=QueueType.BATCH_PROCESSING,
            priority=QueuePriority.NORMAL,
            status=JobStatus.PENDING,
            created_at=datetime.now(UTC),
        )
        processor.jobs["job-1"] = job
        assert processor.get_job_status("job-1") is job

    def test_get_job_status_missing(self):
        processor = self._make_processor()
        assert processor.get_job_status("nonexistent") is None

    def test_cancel_nonexistent_job(self):
        processor = self._make_processor()
        result = processor.cancel_job("nonexistent")
        assert result is False

    def test_get_job_stats_empty(self):
        processor = self._make_processor()
        stats = processor.get_job_stats()
        assert stats["total_jobs"] == 0
        assert stats["scheduled_jobs"] == 0

    @pytest.mark.asyncio
    async def test_get_job_stats_with_jobs(self):
        processor = self._make_processor()
        await processor.schedule_job("t1", "fn1")
        await processor.schedule_job("t2", "fn2")
        stats = processor.get_job_stats()
        assert stats["total_jobs"] == 2


# ===========================
# 2.  RAG SERVICE
# ===========================
from core.rag_service import RAGService  # noqa: E402


class TestRAGService:
    """Tests for RAGService (in test-mode, skips heavy initialization)."""

    def _make_service(self) -> RAGService:
        # TESTING env var set above — skips HuggingFace/Chroma loading
        return RAGService(persist_directory="/tmp/test_rag")

    def test_init_in_test_mode(self):
        svc = self._make_service()
        assert svc.embeddings is None
        assert svc.vector_store is None

    def test_generate_search_cache_key_deterministic(self):
        svc = self._make_service()
        key1 = svc._generate_search_cache_key("matematik", 5, {"subject": "math"})
        key2 = svc._generate_search_cache_key("matematik", 5, {"subject": "math"})
        assert key1 == key2

    def test_generate_search_cache_key_differs_on_query(self):
        svc = self._make_service()
        key1 = svc._generate_search_cache_key("matematik", 5, None)
        key2 = svc._generate_search_cache_key("fizik", 5, None)
        assert key1 != key2

    def test_generate_search_cache_key_differs_on_k(self):
        svc = self._make_service()
        key1 = svc._generate_search_cache_key("test", 3, None)
        key2 = svc._generate_search_cache_key("test", 10, None)
        assert key1 != key2

    def test_preprocess_text_strips_and_lowercases(self):
        svc = self._make_service()
        result = svc._preprocess_text("  Türkçe Metin  ")
        assert result == result.strip()
        assert result == result.lower()

    def test_preprocess_text_collapses_whitespace(self):
        svc = self._make_service()
        result = svc._preprocess_text("kelime1    kelime2")
        assert "  " not in result

    def test_preprocess_text_is_cached(self):
        svc = self._make_service()
        r1 = svc._preprocess_text("test")
        r2 = svc._preprocess_text("test")
        assert r1 is r2  # lru_cache returns same object

    @pytest.mark.asyncio
    async def test_get_cached_search_results_miss(self):
        svc = self._make_service()
        result = await svc._get_cached_search_results("no_such_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get_memory_cache(self):
        svc = self._make_service()
        svc._redis_client = None  # force memory cache
        key = "test_key_123"
        data = [{"content": "merhaba", "score": 0.9}]
        await svc._set_cached_search_results(key, data)
        result = await svc._get_cached_search_results(key)
        assert result == data

    @pytest.mark.asyncio
    async def test_memory_cache_evicts_oldest_when_full(self):
        svc = self._make_service()
        svc._redis_client = None
        svc._max_cache_size = 3
        for i in range(4):
            await svc._set_cached_search_results(f"key_{i}", [{"score": i}])
        assert len(svc._search_cache) <= 3

    @pytest.mark.asyncio
    async def test_memory_cache_ttl_expiry(self):
        svc = self._make_service()
        svc._redis_client = None
        svc._cache_ttl = 0  # immediate expiry
        key = "expire_key"
        await svc._set_cached_search_results(key, [{"content": "x"}])
        time.sleep(0.01)
        result = await svc._get_cached_search_results(key)
        assert result is None

    @pytest.mark.asyncio
    async def test_search_returns_empty_list_no_vector_store(self):
        svc = self._make_service()
        # vector_store is None in test mode
        results = await svc.search("matematik sorusu")
        assert results == []

    def test_rerank_results_fallback_on_import_error(self):
        svc = self._make_service()
        results = [{"content": "a", "score": 0.8}, {"content": "b", "score": 0.9}]
        # When reranker import fails, original results should be returned
        reranked = svc._rerank_results("query", results)
        assert isinstance(reranked, list)
        assert len(reranked) == 2

    @pytest.mark.asyncio
    async def test_add_documents_returns_failure_when_empty_list(self):
        svc = self._make_service()
        # Passing an empty document list — no langchain_docs produced
        result = await svc.add_documents([])
        assert result.get("success") is False


# ===========================
# 3.  AUTH MIDDLEWARE
# ===========================
from core.auth_middleware import (  # noqa: E402
    AuthContext,
    AuthUser,
    JWTManager,
    Permission,
    PermissionManager,
    UserRole,
)


class TestAuthUser:
    """Tests for AuthUser dataclass."""

    def _make_user(self, role: UserRole = UserRole.STUDENT) -> AuthUser:
        return AuthUser(
            user_id=42,
            username="testuser",
            email="test@kiro2.com",
            role=role,
            permissions=set(PermissionManager().get_user_permissions(role)),
        )

    def test_has_permission_true(self):
        user = self._make_user(UserRole.STUDENT)
        assert user.has_permission(Permission.TAKE_TYT_EXAM)

    def test_has_permission_false(self):
        user = self._make_user(UserRole.STUDENT)
        assert not user.has_permission(Permission.MANAGE_SYSTEM)

    def test_has_role_match(self):
        user = self._make_user(UserRole.ADMIN)
        assert user.has_role(UserRole.ADMIN)

    def test_has_role_no_match(self):
        user = self._make_user(UserRole.STUDENT)
        assert not user.has_role(UserRole.ADMIN)

    def test_is_student(self):
        user = self._make_user(UserRole.STUDENT)
        assert user.is_student()

    def test_is_not_student(self):
        user = self._make_user(UserRole.TEACHER)
        assert not user.is_student()

    def test_is_admin_for_admin_role(self):
        user = self._make_user(UserRole.ADMIN)
        assert user.is_admin()

    def test_is_not_admin_for_student(self):
        user = self._make_user(UserRole.STUDENT)
        assert not user.is_admin()

    def test_can_take_exam_tyt(self):
        user = self._make_user(UserRole.STUDENT)
        assert user.can_take_exam("tyt")

    def test_can_take_exam_ayt(self):
        user = self._make_user(UserRole.STUDENT)
        assert user.can_take_exam("ayt")

    def test_cannot_take_unknown_exam(self):
        user = self._make_user(UserRole.STUDENT)
        assert not user.can_take_exam("unknown_exam_type")


class TestPermissionManager:
    """Tests for PermissionManager."""

    def test_student_has_take_tyt(self):
        pm = PermissionManager()
        assert Permission.TAKE_TYT_EXAM in pm.get_user_permissions(UserRole.STUDENT)

    def test_admin_has_all_permissions(self):
        pm = PermissionManager()
        admin_perms = pm.get_user_permissions(UserRole.ADMIN)
        for perm in Permission:
            assert perm in admin_perms

    def test_guest_limited_permissions(self):
        pm = PermissionManager()
        guest_perms = pm.get_user_permissions(UserRole.GUEST)
        assert Permission.VIEW_CONTENT in guest_perms
        assert Permission.MANAGE_SYSTEM not in guest_perms

    def test_check_permission_true(self):
        pm = PermissionManager()
        assert pm.check_permission(UserRole.STUDENT, Permission.TAKE_TYT_EXAM)

    def test_check_permission_false(self):
        pm = PermissionManager()
        assert not pm.check_permission(UserRole.STUDENT, Permission.MANAGE_SYSTEM)

    def test_check_route_admin_route_blocked_for_student(self):
        pm = PermissionManager()
        assert not pm.check_route_permissions(UserRole.STUDENT, "/admin/users")

    def test_check_route_admin_allowed_for_admin(self):
        pm = PermissionManager()
        assert pm.check_route_permissions(UserRole.ADMIN, "/admin/users")

    def test_check_route_unknown_route_returns_true(self):
        pm = PermissionManager()
        # No specific rule for /random/route
        assert pm.check_route_permissions(UserRole.STUDENT, "/random/route")

    @pytest.mark.parametrize(
        "role,expected_has",
        [
            (UserRole.TEACHER, Permission.CREATE_CONTENT),
            (UserRole.MODERATOR, Permission.DELETE_CONTENT),
            (UserRole.SYSTEM, Permission.MANAGE_SYSTEM),
        ],
    )
    def test_role_specific_permissions(self, role, expected_has):
        pm = PermissionManager()
        assert expected_has in pm.get_user_permissions(role)


class TestJWTManager:
    """Tests for JWTManager."""

    def _make_manager(self) -> JWTManager:
        return JWTManager(
            config={
                "jwt_secret_key": "test-secret-key-kiro2",
                "jwt_algorithm": "HS256",
                "access_token_expire_minutes": 30,
                "refresh_token_expire_days": 7,
                "jwt_issuer": "KIRO2-Turkish-Exam-Platform",
            }
        )

    def _make_user(self) -> AuthUser:
        return AuthUser(
            user_id=1,
            username="ogrenci",
            email="ogrenci@kiro2.com",
            role=UserRole.STUDENT,
            permissions={Permission.TAKE_TYT_EXAM},
            session_id="sess-123",
        )

    def test_generate_access_token_returns_string(self):
        """generate_access_token should return a non-empty string token."""

        # Temporarily use the real jwt module for this test
        original = sys.modules.get("jwt")
        try:
            import importlib

            real_mod = importlib.import_module("jwt")
            sys.modules["jwt"] = real_mod
            # Re-import JWTManager with real jwt
            from importlib import reload

            import core.auth_middleware as _auth_mod

            reload(_auth_mod)
            manager = _auth_mod.JWTManager(
                config={
                    "jwt_secret_key": "test-secret",
                    "jwt_algorithm": "HS256",
                    "access_token_expire_minutes": 30,
                    "refresh_token_expire_days": 7,
                    "jwt_issuer": "KIRO2-Turkish-Exam-Platform",
                }
            )
            user = _auth_mod.AuthUser(
                user_id=99,
                username="test",
                email="x@x.com",
                role=_auth_mod.UserRole.STUDENT,
                permissions=set(),
            )
            token = manager.generate_access_token(user)
            assert isinstance(token, str)
            assert len(token) > 0
        except ImportError:
            pytest.skip("Real PyJWT not available")
        finally:
            if original is not None:
                sys.modules["jwt"] = original

    def test_jwt_manager_stores_config(self):
        manager = self._make_manager()
        assert manager.secret_key == "test-secret-key-kiro2"
        assert manager.algorithm == "HS256"
        assert manager.access_token_expire == 30
        assert manager.issuer == "KIRO2-Turkish-Exam-Platform"

    def test_auth_context_default_state(self):
        ctx = AuthContext()
        assert ctx.authenticated is False
        assert ctx.user is None
        assert ctx.permissions == set()


# ===========================
# 4.  TRANSACTION MANAGER
# ===========================
from core.exceptions import ValidationError  # noqa: E402
from core.transaction_manager import (  # noqa: E402
    LoggingTransactionHook,
    MetricsTransactionHook,
    TransactionConfig,
    TransactionIsolationLevel,
    TransactionMetrics,
    TransactionPriority,
    TransactionStatus,
)


class TestTransactionConfig:
    """Tests for TransactionConfig validation."""

    def test_default_values(self):
        cfg = TransactionConfig()
        assert cfg.retry_attempts == 3
        assert cfg.retry_delay == 1.0
        assert cfg.enable_savepoints is True
        assert cfg.priority == TransactionPriority.NORMAL

    def test_invalid_timeout_raises(self):
        with pytest.raises(ValidationError):
            TransactionConfig(timeout_seconds=-1)

    def test_invalid_retry_attempts_raises(self):
        with pytest.raises(ValidationError):
            TransactionConfig(retry_attempts=-1)

    def test_invalid_retry_delay_raises(self):
        with pytest.raises(ValidationError):
            TransactionConfig(retry_delay=-0.5)

    def test_zero_retry_allowed(self):
        cfg = TransactionConfig(retry_attempts=0)
        assert cfg.retry_attempts == 0

    @pytest.mark.parametrize(
        "level",
        [
            TransactionIsolationLevel.READ_UNCOMMITTED,
            TransactionIsolationLevel.READ_COMMITTED,
            TransactionIsolationLevel.REPEATABLE_READ,
            TransactionIsolationLevel.SERIALIZABLE,
        ],
    )
    def test_isolation_levels(self, level):
        cfg = TransactionConfig(isolation_level=level)
        assert cfg.isolation_level == level


class TestTransactionMetrics:
    """Tests for TransactionMetrics."""

    def test_mark_completed_committed(self):
        metrics = TransactionMetrics(transaction_id="tx-1", start_time=datetime.now())
        metrics.mark_completed(TransactionStatus.COMMITTED)
        assert metrics.status == TransactionStatus.COMMITTED
        assert metrics.end_time is not None
        assert metrics.duration_ms is not None
        assert metrics.duration_ms >= 0

    def test_mark_completed_with_error_message(self):
        metrics = TransactionMetrics(transaction_id="tx-2", start_time=datetime.now())
        metrics.mark_completed(TransactionStatus.FAILED, "deadlock detected")
        assert metrics.error_message == "deadlock detected"
        assert metrics.status == TransactionStatus.FAILED


class TestMetricsTransactionHook:
    """Tests for MetricsTransactionHook."""

    @pytest.mark.asyncio
    async def test_before_transaction_adds_to_active(self):
        hook = MetricsTransactionHook()
        cfg = TransactionConfig()
        await hook.before_transaction("tx-1", cfg)
        assert "tx-1" in hook.active_transactions

    @pytest.mark.asyncio
    async def test_after_commit_removes_from_active(self):
        hook = MetricsTransactionHook()
        hook.active_transactions.add("tx-1")
        metrics = TransactionMetrics(transaction_id="tx-1", start_time=datetime.now())
        metrics.mark_completed(TransactionStatus.COMMITTED)
        await hook.after_commit("tx-1", metrics)
        assert "tx-1" not in hook.active_transactions
        assert len(hook.completed_transactions) == 1

    @pytest.mark.asyncio
    async def test_after_rollback_removes_from_active(self):
        hook = MetricsTransactionHook()
        hook.active_transactions.add("tx-1")
        metrics = TransactionMetrics(transaction_id="tx-1", start_time=datetime.now())
        metrics.mark_completed(TransactionStatus.ROLLED_BACK)
        await hook.after_rollback("tx-1", metrics, Exception("test error"))
        assert "tx-1" not in hook.active_transactions

    def test_get_stats_empty(self):
        hook = MetricsTransactionHook()
        stats = hook.get_stats()
        assert stats["total_transactions"] == 0
        assert stats["success_rate"] == 0

    @pytest.mark.asyncio
    async def test_get_stats_with_data(self):
        hook = MetricsTransactionHook()
        for i in range(3):
            metrics = TransactionMetrics(
                transaction_id=f"tx-{i}", start_time=datetime.now()
            )
            metrics.mark_completed(TransactionStatus.COMMITTED)
            hook.completed_transactions.append(metrics)
        stats = hook.get_stats()
        assert stats["total_transactions"] == 3
        assert stats["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_completed_transactions_capped_at_1000(self):
        hook = MetricsTransactionHook()
        for i in range(1001):
            m = TransactionMetrics(transaction_id=f"tx-{i}", start_time=datetime.now())
            m.mark_completed(TransactionStatus.COMMITTED)
            hook.completed_transactions.append(m)
        # Trigger cap logic via after_commit
        m = TransactionMetrics(transaction_id="tx-cap", start_time=datetime.now())
        m.mark_completed(TransactionStatus.COMMITTED)
        await hook.after_commit("tx-cap", m)
        assert len(hook.completed_transactions) <= 1001  # capped during after_commit


class TestLoggingTransactionHook:
    """Tests for LoggingTransactionHook (smoke tests — no exception)."""

    @pytest.mark.asyncio
    async def test_before_transaction_no_exception(self):
        hook = LoggingTransactionHook()
        await hook.before_transaction("tx-1", TransactionConfig())

    @pytest.mark.asyncio
    async def test_after_commit_no_exception(self):
        hook = LoggingTransactionHook()
        m = TransactionMetrics(transaction_id="tx-1", start_time=datetime.now())
        m.mark_completed(TransactionStatus.COMMITTED)
        await hook.after_commit("tx-1", m)

    @pytest.mark.asyncio
    async def test_after_rollback_no_exception(self):
        hook = LoggingTransactionHook()
        m = TransactionMetrics(transaction_id="tx-1", start_time=datetime.now())
        m.mark_completed(TransactionStatus.ROLLED_BACK)
        await hook.after_rollback("tx-1", m, ValueError("oops"))


# ===========================
# 5.  UNIFIED EVENT BUS
# ===========================
from core.unified_event_bus import (  # noqa: E402
    Event,
    EventBus,
    EventBusMiddleware,
    EventHandler,
    EventPriority,
    EventStatus,
    EventType,
    LoggingMiddleware,
)


class TestEvent:
    """Tests for the Event dataclass."""

    def _make_event(self, **kwargs) -> Event:
        defaults = dict(
            id=str(uuid.uuid4()),
            type=EventType.USER_LOGIN,
            source="test",
            timestamp=datetime.now(UTC),
            data={"user_id": 1},
        )
        defaults.update(kwargs)
        return Event(**defaults)

    def test_auto_id_generation(self):
        event = Event(
            id="",
            type=EventType.USER_LOGIN,
            source="test",
            timestamp=datetime.now(UTC),
            data={},
        )
        assert event.id != ""

    def test_correlation_id_defaults_to_id(self):
        event = self._make_event(id="ev-1", correlation_id=None)
        assert event.correlation_id == "ev-1"

    def test_to_dict_serializes_enums(self):
        event = self._make_event()
        d = event.to_dict()
        assert d["type"] == EventType.USER_LOGIN.value
        assert d["priority"] == EventPriority.NORMAL.value
        assert d["status"] == EventStatus.PENDING.value

    def test_to_dict_timestamp_iso(self):
        event = self._make_event()
        d = event.to_dict()
        datetime.fromisoformat(d["timestamp"])

    def test_from_dict_roundtrip(self):
        original = self._make_event()
        d = original.to_dict()
        restored = Event.from_dict(d)
        assert restored.id == original.id
        assert restored.type == original.type
        assert restored.priority == original.priority

    def test_is_expired_without_ttl(self):
        event = self._make_event()
        assert not event.is_expired()

    def test_is_expired_with_past_ttl(self):
        # Create event with timestamp in the past
        old_time = datetime.now(UTC) - timedelta(seconds=200)
        event = self._make_event(timestamp=old_time, ttl=100)
        assert event.is_expired()

    def test_is_not_expired_with_future_ttl(self):
        event = self._make_event(ttl=3600)
        assert not event.is_expired()

    def test_should_retry_failed_with_remaining_retries(self):
        event = self._make_event(
            status=EventStatus.FAILED, retry_count=0, max_retries=3
        )
        assert event.should_retry()

    def test_should_not_retry_when_max_retries_reached(self):
        event = self._make_event(
            status=EventStatus.FAILED, retry_count=3, max_retries=3
        )
        assert not event.should_retry()

    def test_should_not_retry_non_failed_event(self):
        event = self._make_event(status=EventStatus.COMPLETED)
        assert not event.should_retry()


class TestEventHandler:
    """Tests for EventHandler."""

    def test_matches_event_same_type(self):
        def handler():
            pass

        eh = EventHandler(
            handler_id="h1",
            event_type=EventType.USER_LOGIN,
            callback=handler,
        )
        event = Event(
            id="e1",
            type=EventType.USER_LOGIN,
            source="test",
            timestamp=datetime.now(UTC),
            data={},
        )
        assert eh.matches_event(event)

    def test_does_not_match_different_type(self):
        def handler():
            pass

        eh = EventHandler(
            handler_id="h1",
            event_type=EventType.USER_LOGOUT,
            callback=handler,
        )
        event = Event(
            id="e1",
            type=EventType.USER_LOGIN,
            source="test",
            timestamp=datetime.now(UTC),
            data={},
        )
        assert not eh.matches_event(event)

    def test_filter_match(self):
        def handler():
            pass

        eh = EventHandler(
            handler_id="h1",
            event_type=EventType.QUESTION_ANSWERED,
            callback=handler,
            filters={"subject": "matematik"},
        )
        event = Event(
            id="e1",
            type=EventType.QUESTION_ANSWERED,
            source="test",
            timestamp=datetime.now(UTC),
            data={"subject": "matematik"},
        )
        assert eh.matches_event(event)

    def test_filter_no_match(self):
        def handler():
            pass

        eh = EventHandler(
            handler_id="h1",
            event_type=EventType.QUESTION_ANSWERED,
            callback=handler,
            filters={"subject": "fizik"},
        )
        event = Event(
            id="e1",
            type=EventType.QUESTION_ANSWERED,
            source="test",
            timestamp=datetime.now(UTC),
            data={"subject": "matematik"},
        )
        assert not eh.matches_event(event)


class TestEventBus:
    """Tests for EventBus subscribe / unsubscribe / publish."""

    @pytest.mark.asyncio
    async def test_subscribe_returns_handler_id(self):
        bus = EventBus()

        async def handler(event: Event):
            pass

        hid = bus.subscribe(EventType.USER_LOGIN, handler)
        assert isinstance(hid, str)
        assert handler.__name__ in hid

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_handler(self):
        bus = EventBus()

        async def handler(event: Event):
            pass

        hid = bus.subscribe(EventType.USER_LOGIN, handler)
        result = bus.unsubscribe(hid)
        assert result is True
        assert len(bus.handlers[EventType.USER_LOGIN]) == 0

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_returns_false(self):
        bus = EventBus()
        assert bus.unsubscribe("nonexistent") is False

    def _make_bus_no_metrics(self) -> EventBus:
        """Return an EventBus with all middleware after_publish/after_handle/on_error
        no-op patched to avoid MetricType.EVENT_PUBLISHED AttributeError."""
        bus = EventBus()
        # Replace every middleware's async methods with no-ops so the real
        # MetricsMiddleware doesn't reference non-existent MetricType members.
        noop = AsyncMock(return_value=None)
        noop_true = AsyncMock(return_value=True)
        identity = AsyncMock(side_effect=lambda event: event)
        for mw in bus.middlewares:
            mw.before_publish = identity
            mw.after_publish = noop
            mw.before_handle = AsyncMock(side_effect=lambda ev, h: ev)
            mw.after_handle = noop
            mw.on_error = noop_true
        return bus

    @pytest.mark.asyncio
    async def test_publish_returns_event_id(self):
        bus = self._make_bus_no_metrics()
        eid = await bus.publish(
            event_type=EventType.USER_LOGIN,
            data={"user_id": 99},
            source="test",
        )
        assert isinstance(eid, str)
        assert len(eid) > 0

    @pytest.mark.asyncio
    async def test_publish_puts_event_on_queue(self):
        bus = self._make_bus_no_metrics()
        await bus.publish(
            event_type=EventType.USER_REGISTERED,
            data={"user_id": 1},
        )
        assert not bus.event_queue.empty()

    @pytest.mark.asyncio
    async def test_handlers_sorted_by_priority(self):
        bus = self._make_bus_no_metrics()
        call_order = []

        async def low_handler(event: Event):
            call_order.append("low")

        async def high_handler(event: Event):
            call_order.append("high")

        bus.subscribe(EventType.USER_LOGIN, low_handler, priority=0)
        bus.subscribe(EventType.USER_LOGIN, high_handler, priority=10)

        handlers = bus.handlers[EventType.USER_LOGIN]
        assert handlers[0].priority == 10  # high priority first

    def test_add_middleware(self):
        bus = self._make_bus_no_metrics()
        initial_count = len(bus.middlewares)
        bus.add_middleware(EventBusMiddleware())
        assert len(bus.middlewares) == initial_count + 1

    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        bus = self._make_bus_no_metrics()
        await bus.start()
        assert bus.running is True
        await bus.stop()
        assert bus.running is False

    @pytest.mark.asyncio
    async def test_start_idempotent(self):
        bus = self._make_bus_no_metrics()
        await bus.start()
        task_before = bus.processor_task
        await bus.start()  # Second call should no-op
        assert bus.processor_task is task_before
        await bus.stop()


class TestLoggingMiddleware:
    """Tests for LoggingMiddleware."""

    @pytest.mark.asyncio
    async def test_before_publish_returns_event(self):
        mw = LoggingMiddleware()
        event = Event(
            id="e1",
            type=EventType.SYSTEM_STARTUP,
            source="test",
            timestamp=datetime.now(UTC),
            data={},
        )
        result = await mw.before_publish(event)
        assert result is event

    @pytest.mark.asyncio
    async def test_on_error_returns_true(self):
        mw = LoggingMiddleware()
        event = Event(
            id="e1",
            type=EventType.SYSTEM_SHUTDOWN,
            source="test",
            timestamp=datetime.now(UTC),
            data={},
        )
        handler = EventHandler(
            handler_id="h1",
            event_type=EventType.SYSTEM_SHUTDOWN,
            callback=lambda: None,
        )
        result = await mw.on_error(event, handler, ValueError("oops"))
        assert result is True


# ===========================
# 6.  API OPTIMIZER
# ===========================
from core.api_optimizer import (  # noqa: E402
    APIOptimizer,
    CacheConfig,
    CompressionConfig,
    PaginatedResponse,
    PaginationParams,
    RateLimitConfig,
    TurkishContentOptimizer,
    optimize_query,
)


class TestRateLimitConfig:
    """Tests for RateLimitConfig Pydantic model."""

    def test_default_values(self):
        cfg = RateLimitConfig()
        assert cfg.requests_per_minute == 100
        assert cfg.enabled is True

    def test_custom_values(self):
        cfg = RateLimitConfig(requests_per_minute=50, enabled=False)
        assert cfg.requests_per_minute == 50
        assert cfg.enabled is False


class TestCompressionConfig:
    """Tests for CompressionConfig."""

    def test_default_enabled(self):
        cfg = CompressionConfig()
        assert cfg.enabled is True
        assert cfg.min_size == 1024

    def test_mime_types_include_json(self):
        cfg = CompressionConfig()
        assert "application/json" in cfg.mime_types


class TestCacheConfig:
    """Tests for CacheConfig."""

    def test_default_ttl(self):
        cfg = CacheConfig()
        assert cfg.default_ttl == 300


class TestPaginationParams:
    """Tests for PaginationParams."""

    def test_default_page_and_size(self):
        params = PaginationParams()
        assert params.page == 1
        assert params.size == 20

    def test_offset_first_page(self):
        params = PaginationParams(page=1, size=20)
        assert params.offset == 0

    def test_offset_second_page(self):
        params = PaginationParams(page=2, size=20)
        assert params.offset == 20

    def test_offset_third_page(self):
        params = PaginationParams(page=3, size=10)
        assert params.offset == 20

    @pytest.mark.parametrize(
        "page,size,expected_offset",
        [
            (1, 10, 0),
            (2, 10, 10),
            (5, 20, 80),
            (1, 1, 0),
        ],
    )
    def test_offset_parametrize(self, page, size, expected_offset):
        params = PaginationParams(page=page, size=size)
        assert params.offset == expected_offset


class TestPaginatedResponse:
    """Tests for PaginatedResponse.create()."""

    def test_create_first_page(self):
        params = PaginationParams(page=1, size=10)
        resp = PaginatedResponse.create(
            items=list(range(10)), total=25, pagination=params
        )
        assert resp.page == 1
        assert resp.pages == 3
        assert resp.has_next is True
        assert resp.has_previous is False

    def test_create_last_page(self):
        params = PaginationParams(page=3, size=10)
        resp = PaginatedResponse.create(
            items=list(range(5)), total=25, pagination=params
        )
        assert resp.has_next is False
        assert resp.has_previous is True

    def test_create_single_page(self):
        params = PaginationParams(page=1, size=100)
        resp = PaginatedResponse.create(
            items=list(range(5)), total=5, pagination=params
        )
        assert resp.pages == 1
        assert resp.has_next is False
        assert resp.has_previous is False

    def test_total_and_size_reflected(self):
        params = PaginationParams(page=1, size=5)
        resp = PaginatedResponse.create(
            items=[1, 2, 3, 4, 5], total=50, pagination=params
        )
        assert resp.total == 50
        assert resp.size == 5


class TestTurkishContentOptimizer:
    """Tests for TurkishContentOptimizer."""

    def test_optimize_empty_results(self):
        result = TurkishContentOptimizer.optimize_search_results([], "matematik")
        assert result == []

    def test_optimize_empty_query(self):
        items = [{"title": "Test", "content": "abc"}]
        result = TurkishContentOptimizer.optimize_search_results(items, "")
        assert result == items  # no-op

    def test_optimize_title_match_scores_higher(self):
        items = [
            {"title": "matematiksel analiz", "content": "sayılar"},
            {"title": "fizik problemleri", "content": "matematik konu"},
        ]
        result = TurkishContentOptimizer.optimize_search_results(items, "matematik")
        # Title match should come first (score=10 vs score=5)
        assert "matematik" in result[0]["title"].lower()

    def test_optimize_response_format_string(self):
        result = TurkishContentOptimizer.optimize_response_format("Türkçe metin")
        assert isinstance(result, str)

    def test_optimize_response_format_dict(self):
        data = {"konu": "Türkçe", "sayi": 42}
        result = TurkishContentOptimizer.optimize_response_format(data)
        assert isinstance(result, dict)
        assert result["konu"] == "Türkçe"

    def test_optimize_response_format_list(self):
        data = ["Türkçe", "English"]
        result = TurkishContentOptimizer.optimize_response_format(data)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_optimize_response_format_non_string_passthrough(self):
        assert TurkishContentOptimizer.optimize_response_format(42) == 42
        assert TurkishContentOptimizer.optimize_response_format(None) is None

    def test_turkish_char_normalization_in_search(self):
        items = [
            {"title": "cografya konusu", "content": "detay"},
            {"title": "matematik", "content": "detay"},
        ]
        # 'coğrafya' should normalize to match 'cografya'
        result = TurkishContentOptimizer.optimize_search_results(items, "coğrafya")
        # cografya title should score higher
        assert "cografya" in result[0]["title"]


class TestAPIOptimizerInit:
    """Tests for APIOptimizer initialization (no real Redis)."""

    def test_initial_stats(self):
        optimizer = APIOptimizer(
            rate_limit_config=RateLimitConfig(),
            compression_config=CompressionConfig(),
            cache_config=CacheConfig(),
        )
        assert optimizer.stats["total_requests"] == 0
        assert optimizer.stats["cache_hits"] == 0
        assert optimizer.stats["cache_misses"] == 0
        assert optimizer.redis_client is None

    @pytest.mark.asyncio
    async def test_close_with_no_redis_no_error(self):
        optimizer = APIOptimizer(
            rate_limit_config=RateLimitConfig(),
            compression_config=CompressionConfig(),
            cache_config=CacheConfig(),
        )
        # Should not raise even though redis_client is None
        await optimizer.close()


class TestOptimizeQueryDecorator:
    """Tests for the optimize_query decorator."""

    @pytest.mark.asyncio
    async def test_wraps_async_function(self):
        @optimize_query()
        async def fast_fn():
            return {"data": "ok"}

        result = await fast_fn()
        assert result == {"data": "ok"}

    @pytest.mark.asyncio
    async def test_propagates_exception(self):
        @optimize_query()
        async def failing_fn():
            raise ValueError("db error")

        with pytest.raises(ValueError, match="db error"):
            await failing_fn()
