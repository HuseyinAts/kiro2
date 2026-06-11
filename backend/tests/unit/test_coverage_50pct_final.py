"""
Coverage push to 50% — final sprint.

Targets:
  1. core/turkish_exam_middleware.py  (292 miss)
  2. core/message_queue_system.py     (284 miss)
  3. core/background_job_processor.py (225 miss)
  4. core/security_event_monitoring.py(231 miss)
  5. core/auth_middleware.py          (225 miss)
  6. services/visual_content_generator.py (222 miss)
  7. api/diary_api.py                 (233 miss)

Rules:
- NEVER `from main import app`
- importlib.util for clean module loading
- sys.modules.setdefault() for stubs
- No assert True / pass
"""

import sys
import types
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

# ─────────────────────────────────────────────────────────────────
# Shared stub helpers — install before any target module imports
# ─────────────────────────────────────────────────────────────────


def _make_stub(name: str, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


def _install_core_stubs():
    """Install lightweight stubs for heavy core dependencies."""

    # structured_logging
    mock_logger = MagicMock()
    mock_logger.info = MagicMock()
    mock_logger.debug = MagicMock()
    mock_logger.warning = MagicMock()
    mock_logger.error = MagicMock()

    class FakeLogCategory:
        EXAM = "exam"
        AUTH = "auth"
        QUEUE = "queue"
        JOBS = "jobs"
        SECURITY = "security"
        EVENTS = "events"
        SYSTEM = "system"
        API = "api"
        DB = "db"
        CACHE = "cache"
        NLP = "nlp"

    sl = _make_stub(
        "core.structured_logging",
        get_logger=lambda *a, **kw: mock_logger,
        get_security_logger=lambda *a, **kw: mock_logger,
        LogCategory=FakeLogCategory,
    )
    sys.modules.setdefault("core.structured_logging", sl)

    # unified_config
    cfg_obj = MagicMock()
    cfg_obj.redis_url = "redis://localhost:6379/0"
    uc = _make_stub("core.unified_config", get_unified_config=lambda: cfg_obj)
    sys.modules.setdefault("core.unified_config", uc)

    # application_metrics
    class FakeMetricType:
        QUEUE_ENQUEUE = "queue_enqueue"
        QUEUE_PROCESS_SUCCESS = "queue_process_success"
        QUEUE_PROCESS_FAILURE = "queue_process_failure"
        EXAM_COMPLETED = "exam_completed"
        JOB_COMPLETED = "job_completed"
        JOB_FAILED = "job_failed"

    mock_collector = MagicMock()
    mock_collector.record_metric = MagicMock()
    am = _make_stub(
        "core.application_metrics",
        MetricType=FakeMetricType,
        get_metrics_collector=lambda: mock_collector,
    )
    sys.modules.setdefault("core.application_metrics", am)

    # unified_event_bus — install a MagicMock()-based stub (same strategy as
    # test_deep_coverage_batch1.py) so test_core_partial_batch2.py's TestEvent
    # tests stay green regardless of which file runs first.
    # Our target modules only need EventType, EventPriority, publish_event attributes.
    _ueb_mock = MagicMock()
    _ueb_mock.publish_event = AsyncMock(return_value=None)
    _ueb_mock.get_event_bus = AsyncMock(return_value=MagicMock())
    # Provide named enum-like attrs used by our target modules
    _ueb_mock.EventType.SECURITY_ALERT = "security_alert"
    _ueb_mock.EventType.USER_LOGIN = "user_login"
    _ueb_mock.EventPriority.HIGH = "high"
    _ueb_mock.EventPriority.NORMAL = "normal"
    sys.modules.setdefault("core.unified_event_bus", _ueb_mock)

    # cache_system_integration
    mock_cache_inner = MagicMock()
    mock_cache_inner.get = AsyncMock(return_value=None)
    mock_cache_inner.set = AsyncMock(return_value=True)
    mock_cache_inner.delete = AsyncMock(return_value=True)
    mock_cache_obj = MagicMock()
    mock_cache_obj.cache_system = mock_cache_inner
    csi = _make_stub(
        "core.cache_system_integration",
        get_unified_cache_system=AsyncMock(return_value=mock_cache_obj),
    )
    sys.modules.setdefault("core.cache_system_integration", csi)

    # turkish_exam_event_handlers
    class FakeTurkishExamType:
        TYT = "tyt"
        AYT = "ayt"
        YKS = "yks"

    teeh = _make_stub(
        "core.turkish_exam_event_handlers",
        TurkishExamType=FakeTurkishExamType,
    )
    sys.modules.setdefault("core.turkish_exam_event_handlers", teeh)

    # unified_api_gateway
    class FakeRouteType:
        TYT_EXAM = "tyt_exam"
        AYT_EXAM = "ayt_exam"
        YKS_INFO = "yks_info"
        GENERAL = "general"

    class FakeHTTPMethod:
        GET = "GET"
        POST = "POST"

    uag = _make_stub(
        "core.unified_api_gateway",
        RouteType=FakeRouteType,
        HTTPMethod=FakeHTTPMethod,
        APIRequest=MagicMock,
        APIResponse=MagicMock,
    )
    sys.modules.setdefault("core.unified_api_gateway", uag)

    # session_auth_caching
    mock_sac = MagicMock()
    mock_sac.cache_system = mock_cache_inner
    sac = _make_stub(
        "core.session_auth_caching",
        get_session_auth_cache=AsyncMock(return_value=mock_sac),
    )
    sys.modules.setdefault("core.session_auth_caching", sac)

    # enhanced_database — only install stub if the real module isn't loaded yet
    # (avoids stripping EnhancedDatabaseManager that downstream imports need)
    if "core.enhanced_database" not in sys.modules:
        mock_db_mgr = MagicMock()
        mock_db_mgr.fetch_one = AsyncMock(return_value=None)
        mock_db_mgr.fetch_all = AsyncMock(return_value=[])

        # Include the class name so `from .enhanced_database import EnhancedDatabaseManager`
        # does not fail when our stub is the only thing in sys.modules.
        class _FakeEnhancedDBManager:
            pass

        edb = _make_stub(
            "core.enhanced_database",
            get_enhanced_db_manager=lambda: mock_db_mgr,
            enhanced_db_manager=mock_db_mgr,
            EnhancedDatabaseManager=_FakeEnhancedDBManager,
        )
        sys.modules["core.enhanced_database"] = edb

    # redis.asyncio
    fake_redis_mod = types.ModuleType("redis")
    fake_redis_async = types.ModuleType("redis.asyncio")
    fake_redis_async.Redis = MagicMock
    fake_redis_async.from_url = MagicMock(return_value=AsyncMock())
    fake_redis_mod.asyncio = fake_redis_async
    sys.modules.setdefault("redis", fake_redis_mod)
    sys.modules.setdefault("redis.asyncio", fake_redis_async)

    # jwt
    try:
        import jwt  # noqa: F401
    except ImportError:
        fake_jwt = _make_stub(
            "jwt",
            encode=lambda *a, **kw: "fake.token",
            decode=lambda *a, **kw: {},
            ExpiredSignatureError=Exception,
            InvalidTokenError=Exception,
        )
        sys.modules.setdefault("jwt", fake_jwt)

    # graph/geometry/map stubs for visual_content_generator
    gg_stub = _make_stub("services.graph_generator", GraphGenerator=MagicMock)
    geom_stub = _make_stub("services.geometry_generator", GeometryGenerator=MagicMock)
    map_stub = _make_stub(
        "services.map_diagram_generator", MapDiagramGenerator=MagicMock
    )
    sys.modules.setdefault("services.graph_generator", gg_stub)
    sys.modules.setdefault("services.geometry_generator", geom_stub)
    sys.modules.setdefault("services.map_diagram_generator", map_stub)


_install_core_stubs()


# ─────────────────────────────────────────────────────────────────
# Import target modules after stubs are in place
# ─────────────────────────────────────────────────────────────────

import importlib.util
import os

BACKEND_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


def _load(rel_path):
    full = os.path.join(BACKEND_DIR, rel_path)
    spec = importlib.util.spec_from_file_location(
        rel_path.replace(os.sep, ".").rstrip(".py"), full
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


turkish_exam_mw = _load("core/turkish_exam_middleware.py")
msg_queue = _load("core/message_queue_system.py")
bg_job_proc = _load("core/background_job_processor.py")
auth_mw = _load("core/auth_middleware.py")
visual_gen = _load("services/visual_content_generator.py")

# security_event_monitoring — may fail if redis (sync) missing; handle gracefully
try:
    sec_mon = _load("core/security_event_monitoring.py")
    _HAS_SEC_MON = True
except Exception:
    sec_mon = None
    _HAS_SEC_MON = False


# ─────────────────────────────────────────────────────────────────
# ─── SECTION 1: core/turkish_exam_middleware.py ──────────────────
# ─────────────────────────────────────────────────────────────────


class TestExamPeriodEnum:
    def test_all_values_present(self):
        EP = turkish_exam_mw.ExamPeriod
        assert EP.REGISTRATION.value == "registration"
        assert EP.PREPARATION.value == "preparation"
        assert EP.EXAM_WEEK.value == "exam_week"
        assert EP.RESULTS.value == "results"
        assert EP.OFF_SEASON.value == "off_season"


class TestExamSecurityLevelEnum:
    def test_levels_ordered(self):
        ESL = turkish_exam_mw.ExamSecurityLevel
        assert ESL.LOW.value == "low"
        assert ESL.MAXIMUM.value == "maximum"


class TestExamContext:
    def test_defaults(self):
        ctx = turkish_exam_mw.ExamContext()
        assert ctx.is_practice is True
        assert ctx.difficulty == "orta"
        assert ctx.current_period == turkish_exam_mw.ExamPeriod.OFF_SEASON

    def test_custom_values(self):
        ctx = turkish_exam_mw.ExamContext(
            session_id="abc",
            security_level=turkish_exam_mw.ExamSecurityLevel.HIGH,
            time_remaining=120,
        )
        assert ctx.session_id == "abc"
        assert ctx.time_remaining == 120


class TestTurkishLanguageMiddleware:
    def _make(self):
        return turkish_exam_mw.TurkishLanguageMiddleware({})

    def test_init_subjects_populated(self):
        m = self._make()
        assert "matematik" in m.turkish_subjects
        assert "biyoloji" in m.turkish_subjects

    def test_exam_translations_populated(self):
        m = self._make()
        assert "tyt" in m.exam_translations
        assert m.exam_translations["tyt"] == "Temel Yeterlilik Testi"

    def test_common_phrases_has_exam_started(self):
        m = self._make()
        assert "exam_started" in m.common_phrases

    @pytest.mark.asyncio
    async def test_translate_request_params_subject(self):
        m = self._make()

        req = MagicMock()
        req.body = {"subject": "matematik", "exam_type": "tyt"}
        req.query_params = {}
        await m._translate_request_params(req)
        assert req.body["subject_tr"] == "Matematik"
        assert req.body["exam_type_tr"] == "Temel Yeterlilik Testi"

    @pytest.mark.asyncio
    async def test_translate_request_params_unknown(self):
        m = self._make()
        req = MagicMock()
        req.body = {"subject": "unknown_subject"}
        req.query_params = {}
        # should not raise
        await m._translate_request_params(req)
        assert "subject_tr" not in req.body

    @pytest.mark.asyncio
    async def test_translate_query_params_subject(self):
        m = self._make()
        req = MagicMock()
        req.body = {}
        req.query_params = {"subject": "fizik"}
        await m._translate_request_params(req)
        assert req.query_params["subject_tr"] == "Fizik"

    @pytest.mark.asyncio
    async def test_add_turkish_translations_non_dict_body(self):
        m = self._make()
        resp = MagicMock()
        resp.body = "not a dict"
        req = MagicMock()
        # Should return without error
        await m._add_turkish_translations(resp, req)

    @pytest.mark.asyncio
    async def test_add_turkish_translations_timestamp(self):
        m = self._make()
        resp = MagicMock()
        ts = datetime.now(UTC).isoformat()
        resp.body = {"timestamp": ts}
        req = MagicMock()
        req.route_type = "general"
        await m._add_turkish_translations(resp, req)
        assert "timestamp_turkey" in resp.body

    @pytest.mark.asyncio
    async def test_add_turkish_translations_exam_route(self):
        """Platform info added for TYT/AYT/YKS routes."""
        from core.unified_api_gateway import RouteType  # our stub

        m = self._make()
        resp = MagicMock()
        resp.body = {}
        req = MagicMock()
        req.route_type = RouteType.TYT_EXAM
        await m._add_turkish_translations(resp, req)
        assert "platform_info" in resp.body


class TestExamSecurityMiddleware:
    def _make(self, **cfg):
        return turkish_exam_mw.ExamSecurityMiddleware(cfg)

    def test_defaults(self):
        m = self._make()
        assert m.max_violations_per_hour == 5
        assert m.block_duration_minutes == 30

    def test_is_user_blocked_not_blocked(self):
        m = self._make()
        assert m._is_user_blocked(999) is False

    def test_is_user_blocked_active_block(self):
        m = self._make()
        m.blocked_users[1] = datetime.now(UTC) + timedelta(minutes=10)
        assert m._is_user_blocked(1) is True

    def test_is_user_blocked_expired_removes_entry(self):
        m = self._make()
        m.blocked_users[1] = datetime.now(UTC) - timedelta(minutes=1)
        assert m._is_user_blocked(1) is False
        assert 1 not in m.blocked_users

    def test_create_security_error_returns_403(self):
        m = self._make()
        # APIResponse is a MagicMock-based stub; build response manually
        resp = m._create_security_error("req-1", "test reason", "test reason TR")
        # The returned object is an APIResponse instance (our stub returns a MagicMock call result)
        assert resp is not None

    def test_add_security_headers_exam_route(self):
        m = self._make()
        resp = MagicMock()
        req = MagicMock()
        req.is_exam_route.return_value = True
        m._add_security_headers(resp, req)
        # add_header should have been called at least once
        resp.add_header.assert_called()

    def test_add_security_headers_non_exam_route(self):
        m = self._make()
        resp = MagicMock()
        req = MagicMock()
        req.is_exam_route.return_value = False
        m._add_security_headers(resp, req)
        resp.add_header.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_security_violation_records(self):
        m = self._make()
        req = MagicMock()
        req.client_ip = "1.2.3.4"
        await m._handle_security_violation(1, ["rapid_requests"], req)
        assert 1 in m.security_violations
        assert len(m.security_violations[1]) == 1

    @pytest.mark.asyncio
    async def test_handle_security_violation_blocks_on_threshold(self):
        m = self._make()
        req = MagicMock()
        req.client_ip = "1.2.3.4"
        # Pre-fill violations up to threshold - 1
        now = datetime.now(UTC)
        m.security_violations[42] = [now] * (m.max_violations_per_hour - 1)
        await m._handle_security_violation(42, ["automated_tool"], req)
        assert 42 in m.blocked_users

    @pytest.mark.asyncio
    async def test_get_daily_attempts_returns_zero_on_miss(self):
        m = self._make()
        result = await m._get_daily_attempts(1)
        assert result == 0

    @pytest.mark.asyncio
    async def test_check_user_eligibility_student(self):
        m = self._make()
        user = MagicMock()
        user.is_student.return_value = True
        user.is_admin.return_value = False
        user.role = "student"
        req = MagicMock()
        result = await m._check_user_eligibility(req, user)
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_check_user_eligibility_admin(self):
        m = self._make()
        user = MagicMock()
        user.is_student.return_value = False
        user.is_admin.return_value = True
        user.role = "admin"
        req = MagicMock()
        result = await m._check_user_eligibility(req, user)
        assert result["allowed"] is True


class TestExamSessionMiddleware:
    def _make(self):
        return turkish_exam_mw.ExamSessionMiddleware({})

    def test_extract_exam_type_tyt(self):
        m = self._make()
        assert m._extract_exam_type_from_path("/api/v1/tyt/start") == "tyt"

    def test_extract_exam_type_ayt(self):
        m = self._make()
        assert m._extract_exam_type_from_path("/api/ayt/submit") == "ayt"

    def test_extract_exam_type_yks(self):
        m = self._make()
        assert m._extract_exam_type_from_path("/api/yks/info") == "yks"

    def test_extract_exam_type_unknown(self):
        m = self._make()
        assert m._extract_exam_type_from_path("/api/v1/other") == "unknown"

    def test_is_session_expired_not_expired(self):
        m = self._make()
        session = {"last_activity": datetime.now(UTC).isoformat()}
        assert m._is_session_expired(session) is False

    def test_is_session_expired_expired(self):
        m = self._make()
        old = (datetime.now(UTC) - timedelta(hours=10)).isoformat()
        assert m._is_session_expired({"last_activity": old}) is True

    def test_calculate_time_remaining_positive(self):
        m = self._make()
        started = (datetime.now(UTC) - timedelta(minutes=10)).isoformat()
        result = m._calculate_time_remaining({"started_at": started})
        assert isinstance(result, int)
        assert result >= 0

    def test_calculate_time_remaining_zero_if_past(self):
        m = self._make()
        started = (datetime.now(UTC) - timedelta(hours=10)).isoformat()
        result = m._calculate_time_remaining({"started_at": started})
        assert result == 0


class TestFactoryFunctions:
    def test_create_turkish_language_middleware(self):
        mw = turkish_exam_mw.create_turkish_language_middleware()
        assert isinstance(mw, turkish_exam_mw.TurkishLanguageMiddleware)

    def test_create_exam_security_middleware(self):
        mw = turkish_exam_mw.create_exam_security_middleware()
        assert isinstance(mw, turkish_exam_mw.ExamSecurityMiddleware)

    def test_create_exam_session_middleware(self):
        mw = turkish_exam_mw.create_exam_session_middleware()
        assert isinstance(mw, turkish_exam_mw.ExamSessionMiddleware)

    def test_configure_exam_middleware_tyt(self):
        cfg = turkish_exam_mw.configure_exam_middleware("tyt")
        assert cfg["session_timeout_minutes"] == 135

    def test_configure_exam_middleware_ayt(self):
        cfg = turkish_exam_mw.configure_exam_middleware("ayt")
        assert cfg["session_timeout_minutes"] == 180

    def test_configure_exam_middleware_default(self):
        cfg = turkish_exam_mw.configure_exam_middleware("yks")
        assert cfg["session_timeout_minutes"] == 240

    def test_get_middleware_stack_returns_list(self):
        stack = turkish_exam_mw.get_turkish_exam_middleware_stack()
        assert isinstance(stack, list)
        assert len(stack) == 3
        names = [item[0] for item in stack]
        assert "exam_security" in names
        assert "turkish_language" in names


# ─────────────────────────────────────────────────────────────────
# ─── SECTION 2: core/message_queue_system.py ─────────────────────
# ─────────────────────────────────────────────────────────────────


class TestQueueEnums:
    def test_queue_priority_values(self):
        QP = msg_queue.QueuePriority
        assert QP.LOW.value == "low"
        assert QP.CRITICAL.value == "critical"

    def test_job_status_values(self):
        JS = msg_queue.JobStatus
        assert JS.PENDING.value == "pending"
        assert JS.COMPLETED.value == "completed"
        assert JS.FAILED.value == "failed"

    def test_queue_type_values(self):
        QT = msg_queue.QueueType
        assert QT.REAL_TIME.value == "real_time"
        assert QT.EXAM_PROCESSING.value == "exam_processing"
        assert QT.MAINTENANCE.value == "maintenance"


class TestQueueMessage:
    def _make(self, **kwargs):
        defaults = dict(
            id=str(uuid.uuid4()),
            queue_type=msg_queue.QueueType.NOTIFICATIONS,
            payload={"key": "value"},
            priority=msg_queue.QueuePriority.NORMAL,
            created_at=datetime.now(UTC),
        )
        defaults.update(kwargs)
        return msg_queue.QueueMessage(**defaults)

    def test_to_dict_has_required_keys(self):
        m = self._make()
        d = m.to_dict()
        assert "id" in d
        assert "queue_type" in d
        assert d["priority"] == "normal"

    def test_from_dict_roundtrip(self):
        m = self._make()
        d = m.to_dict()
        m2 = msg_queue.QueueMessage.from_dict(d)
        assert m2.id == m.id
        assert m2.queue_type == m.queue_type

    def test_correlation_id_auto_set(self):
        m = msg_queue.QueueMessage(
            id="",
            queue_type=msg_queue.QueueType.ANALYTICS,
            payload={},
            priority=msg_queue.QueuePriority.LOW,
            created_at=datetime.now(UTC),
        )
        assert m.id  # auto-generated
        assert m.correlation_id == m.id

    def test_scheduled_at_serialization(self):
        m = self._make(scheduled_at=datetime.now(UTC))
        d = m.to_dict()
        assert d["scheduled_at"] is not None


class TestBackgroundJob:
    def _make(self):
        return msg_queue.BackgroundJob(
            id=str(uuid.uuid4()),
            job_type="test_job",
            function_name="test_func",
            args=[],
            kwargs={},
            queue_type=msg_queue.QueueType.BATCH_PROCESSING,
            priority=msg_queue.QueuePriority.NORMAL,
            status=msg_queue.JobStatus.PENDING,
            created_at=datetime.now(UTC),
        )

    def test_to_dict_has_status(self):
        j = self._make()
        d = j.to_dict()
        assert d["status"] == "pending"
        assert "created_at" in d

    def test_to_dict_with_timestamps(self):
        j = self._make()
        j.started_at = datetime.now(UTC)
        j.completed_at = datetime.now(UTC)
        d = j.to_dict()
        assert d["started_at"] is not None
        assert d["completed_at"] is not None


class TestRedisMessageQueue:
    def _make(self):
        return msg_queue.RedisMessageQueue(redis_url="redis://localhost:6379/0")

    def test_queue_configs_contains_all_types(self):
        q = self._make()
        for qt in msg_queue.QueueType:
            assert qt in q.queue_configs

    def test_real_time_queue_has_low_batch_size(self):
        q = self._make()
        assert q.queue_configs[msg_queue.QueueType.REAL_TIME]["batch_size"] == 1

    def test_analytics_queue_has_large_batch(self):
        q = self._make()
        assert q.queue_configs[msg_queue.QueueType.ANALYTICS]["batch_size"] == 20

    @pytest.mark.asyncio
    async def test_enqueue_returns_false_when_redis_fails(self):
        q = self._make()
        mock_client = AsyncMock()
        mock_client.xadd = AsyncMock(side_effect=Exception("connection refused"))
        q.redis_client = mock_client
        m = msg_queue.QueueMessage(
            id=str(uuid.uuid4()),
            queue_type=msg_queue.QueueType.NOTIFICATIONS,
            payload={},
            priority=msg_queue.QueuePriority.NORMAL,
            created_at=datetime.now(UTC),
        )
        result = await q.enqueue(m)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_queue_stats_with_no_redis(self):
        q = self._make()
        mock_client = MagicMock()
        mock_client.xinfo_stream = AsyncMock(side_effect=Exception("not available"))
        q.redis_client = mock_client
        stats = await q.get_queue_stats()
        assert "queue_stats" in stats

    @pytest.mark.asyncio
    async def test_stop_consumers_clears_tasks(self):
        q = self._make()
        q.running = True
        q.consumer_tasks = {}
        await q.stop_consumers()
        assert q.running is False


class TestQueueMessageHandlers:
    def _make_queue(self):
        q = msg_queue.RedisMessageQueue(redis_url="redis://localhost:6379/0")
        return q

    def _make_message(self, queue_type, action):
        return msg_queue.QueueMessage(
            id=str(uuid.uuid4()),
            queue_type=queue_type,
            payload={"action": action, "exam_type": "tyt"},
            priority=msg_queue.QueuePriority.NORMAL,
            created_at=datetime.now(UTC),
            user_id=1,
        )

    @pytest.mark.asyncio
    async def test_handle_real_time_message_websocket_broadcast(self):
        q = self._make_queue()
        m = self._make_message(msg_queue.QueueType.REAL_TIME, "websocket_broadcast")
        result = await q._handle_real_time_message(m)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_real_time_message_live_exam_update(self):
        q = self._make_queue()
        m = self._make_message(msg_queue.QueueType.REAL_TIME, "live_exam_update")
        result = await q._handle_real_time_message(m)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_auth_message_user_login(self):
        q = self._make_queue()
        m = self._make_message(msg_queue.QueueType.AUTHENTICATION, "user_login")
        result = await q._handle_auth_message(m)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_auth_message_token_refresh(self):
        q = self._make_queue()
        m = self._make_message(msg_queue.QueueType.AUTHENTICATION, "token_refresh")
        result = await q._handle_auth_message(m)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_exam_message_process_submission(self):
        q = self._make_queue()
        m = self._make_message(
            msg_queue.QueueType.EXAM_PROCESSING, "process_exam_submission"
        )
        result = await q._handle_exam_message(m)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_exam_message_calculate_results(self):
        q = self._make_queue()
        m = self._make_message(
            msg_queue.QueueType.EXAM_PROCESSING, "calculate_exam_results"
        )
        result = await q._handle_exam_message(m)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_notification_email(self):
        q = self._make_queue()
        m = msg_queue.QueueMessage(
            id=str(uuid.uuid4()),
            queue_type=msg_queue.QueueType.NOTIFICATIONS,
            payload={"type": "email"},
            priority=msg_queue.QueuePriority.NORMAL,
            created_at=datetime.now(UTC),
        )
        result = await q._handle_notification_message(m)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_notification_exam_reminder(self):
        q = self._make_queue()
        m = msg_queue.QueueMessage(
            id=str(uuid.uuid4()),
            queue_type=msg_queue.QueueType.NOTIFICATIONS,
            payload={"type": "exam_reminder"},
            priority=msg_queue.QueuePriority.HIGH,
            created_at=datetime.now(UTC),
        )
        result = await q._handle_notification_message(m)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_content_generate_questions(self):
        q = self._make_queue()
        m = self._make_message(
            msg_queue.QueueType.CONTENT_PROCESSING, "generate_questions"
        )
        result = await q._handle_content_message(m)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_analytics_calculate(self):
        q = self._make_queue()
        m = self._make_message(
            msg_queue.QueueType.ANALYTICS, "calculate_learning_analytics"
        )
        result = await q._handle_analytics_message(m)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_batch_monthly_reports(self):
        q = self._make_queue()
        m = self._make_message(
            msg_queue.QueueType.BATCH_PROCESSING, "generate_monthly_reports"
        )
        result = await q._handle_batch_message(m)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_cleanup_expired_sessions(self):
        q = self._make_queue()
        m = self._make_message(msg_queue.QueueType.CLEANUP, "clean_expired_sessions")
        result = await q._handle_cleanup_message(m)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_maintenance_health_check(self):
        q = self._make_queue()
        m = self._make_message(msg_queue.QueueType.MAINTENANCE, "system_health_check")
        result = await q._handle_maintenance_message(m)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_message_by_type_unknown(self):
        q = self._make_queue()
        # Create a fake queue type not in the handler map
        m = MagicMock()
        m.payload = {}
        result = await q._handle_message_by_type(m, "unknown_type")
        assert result is False


class TestBackgroundJobProcessor:
    def _make(self):
        mock_queue = MagicMock()
        mock_queue.enqueue = AsyncMock(return_value=True)
        return msg_queue.BackgroundJobProcessor(mock_queue)

    def test_register_and_get_handler(self):
        proc = self._make()
        handler = MagicMock()
        proc.register_job_handler("my_job", handler)
        assert proc.job_handlers["my_job"] == handler

    @pytest.mark.asyncio
    async def test_schedule_job_immediate(self):
        proc = self._make()
        job_id = await proc.schedule_job(
            "test_job",
            "test_func",
            args=[1, 2],
            queue_type=msg_queue.QueueType.BATCH_PROCESSING,
            priority=msg_queue.QueuePriority.NORMAL,
        )
        assert job_id in proc.jobs
        job = proc.jobs[job_id]
        assert job.job_type == "test_job"

    @pytest.mark.asyncio
    async def test_schedule_job_with_delay(self):
        proc = self._make()
        job_id = await proc.schedule_job(
            "delayed_job",
            "delayed_func",
            delay_seconds=3600,  # 1 hour
        )
        assert job_id in proc.jobs
        # Should create a scheduled task
        assert job_id in proc.scheduled_jobs
        proc.cancel_job(job_id)

    def test_get_job_status_existing(self):
        proc = self._make()
        # Manually insert a job
        fake_job = MagicMock()
        proc.jobs["j1"] = fake_job
        assert proc.get_job_status("j1") == fake_job

    def test_get_job_status_missing(self):
        proc = self._make()
        assert proc.get_job_status("nonexistent") is None

    def test_cancel_job_scheduled(self):
        proc = self._make()
        mock_task = MagicMock()
        proc.scheduled_jobs["j1"] = mock_task
        proc.jobs["j1"] = MagicMock()
        result = proc.cancel_job("j1")
        assert result is True
        mock_task.cancel.assert_called_once()
        assert proc.jobs["j1"].status == msg_queue.JobStatus.CANCELLED

    def test_cancel_job_not_scheduled(self):
        proc = self._make()
        result = proc.cancel_job("nonexistent")
        assert result is False

    def test_get_job_stats_empty(self):
        proc = self._make()
        stats = proc.get_job_stats()
        assert "total_jobs" in stats
        assert stats["total_jobs"] == 0

    def test_get_job_stats_with_jobs(self):
        proc = self._make()
        j = MagicMock()
        j.status = msg_queue.JobStatus.COMPLETED
        proc.jobs["j1"] = j
        stats = proc.get_job_stats()
        assert stats["total_jobs"] == 1


# ─────────────────────────────────────────────────────────────────
# ─── SECTION 3: core/background_job_processor.py ─────────────────
# ─────────────────────────────────────────────────────────────────


class TestJobPriorityEnum:
    def test_values(self):
        JP = bg_job_proc.JobPriority
        assert JP.LOW.value == "low"
        assert JP.CRITICAL.value == "critical"


class TestRetryPolicy:
    def test_calculate_retry_delay_fixed(self):
        from core.message_queue_system import QueueType as QT

        jd = bg_job_proc.JobDefinition(
            name="x",
            function=lambda: None,
            queue_type=QT.BATCH_PROCESSING,
            priority=bg_job_proc.JobPriority.NORMAL,
            retry_policy=bg_job_proc.RetryPolicy.FIXED_DELAY,
            retry_delay=30,
        )
        assert jd.calculate_retry_delay(1) == 30
        assert jd.calculate_retry_delay(5) == 30

    def test_calculate_retry_delay_exponential(self):
        from core.message_queue_system import QueueType as QT

        jd = bg_job_proc.JobDefinition(
            name="x",
            function=lambda: None,
            queue_type=QT.BATCH_PROCESSING,
            priority=bg_job_proc.JobPriority.NORMAL,
            retry_policy=bg_job_proc.RetryPolicy.EXPONENTIAL_BACKOFF,
            retry_delay=10,
        )
        assert jd.calculate_retry_delay(1) == 10  # 10 * 2^0
        assert jd.calculate_retry_delay(2) == 20  # 10 * 2^1
        assert jd.calculate_retry_delay(3) == 40  # 10 * 2^2

    def test_calculate_retry_delay_linear(self):
        from core.message_queue_system import QueueType as QT

        jd = bg_job_proc.JobDefinition(
            name="x",
            function=lambda: None,
            queue_type=QT.BATCH_PROCESSING,
            priority=bg_job_proc.JobPriority.NORMAL,
            retry_policy=bg_job_proc.RetryPolicy.LINEAR_BACKOFF,
            retry_delay=5,
        )
        assert jd.calculate_retry_delay(3) == 15

    def test_calculate_retry_delay_none(self):
        from core.message_queue_system import QueueType as QT

        jd = bg_job_proc.JobDefinition(
            name="x",
            function=lambda: None,
            queue_type=QT.BATCH_PROCESSING,
            priority=bg_job_proc.JobPriority.NORMAL,
            retry_policy=bg_job_proc.RetryPolicy.NONE,
            retry_delay=10,
        )
        assert jd.calculate_retry_delay(5) == 0


class TestJobExecution:
    def _make(self):
        return bg_job_proc.JobExecution(
            job_id=str(uuid.uuid4()),
            job_name="test_job",
            started_at=datetime.now(UTC),
        )

    def test_log_appends_entry(self):
        ex = self._make()
        ex.log("hello")
        assert len(ex.logs) == 1
        assert "hello" in ex.logs[0]

    def test_log_error_level(self):
        ex = self._make()
        ex.log("error msg", "error")
        assert "ERROR" in ex.logs[0]

    def test_update_progress_clamps(self):
        ex = self._make()
        ex.update_progress(150)
        assert ex.progress == 100
        ex.update_progress(-10)
        assert ex.progress == 0

    def test_update_progress_sets_message(self):
        ex = self._make()
        ex.update_progress(50, "halfway")
        assert ex.status_message == "halfway"
        assert "halfway" in ex.logs[-1]


class TestBackgroundJobRegistry:
    def test_register_and_get(self):
        reg = bg_job_proc.BackgroundJobRegistry()
        from core.message_queue_system import QueueType as QT

        def handler():
            pass

        jd = reg.register_job(
            "my_job",
            handler,
            queue_type=QT.BATCH_PROCESSING,
            priority=bg_job_proc.JobPriority.NORMAL,
        )
        assert jd.name == "my_job"
        assert reg.get_job("my_job") == jd

    def test_list_jobs_all(self):
        reg = bg_job_proc.BackgroundJobRegistry()
        from core.message_queue_system import QueueType as QT

        reg.register_job(
            "job1",
            lambda: None,
            queue_type=QT.CLEANUP,
            priority=bg_job_proc.JobPriority.LOW,
        )
        reg.register_job(
            "job2",
            lambda: None,
            queue_type=QT.CLEANUP,
            priority=bg_job_proc.JobPriority.LOW,
        )
        jobs = reg.list_jobs()
        assert len(jobs) == 2

    def test_list_jobs_by_category(self):
        reg = bg_job_proc.BackgroundJobRegistry()
        from core.message_queue_system import QueueType as QT

        reg.register_job(
            "j1",
            lambda: None,
            queue_type=QT.CLEANUP,
            priority=bg_job_proc.JobPriority.LOW,
            category="cat_a",
        )
        reg.register_job(
            "j2",
            lambda: None,
            queue_type=QT.CLEANUP,
            priority=bg_job_proc.JobPriority.LOW,
            category="cat_b",
        )
        assert len(reg.list_jobs("cat_a")) == 1

    def test_get_categories(self):
        reg = bg_job_proc.BackgroundJobRegistry()
        from core.message_queue_system import QueueType as QT

        reg.register_job(
            "j1",
            lambda: None,
            queue_type=QT.CLEANUP,
            priority=bg_job_proc.JobPriority.LOW,
            category="cats",
        )
        cats = reg.get_categories()
        assert "cats" in cats


class TestTurkishExamJobProcessor:
    def _make(self):
        return bg_job_proc.TurkishExamJobProcessor()

    def test_init_registers_builtin_jobs(self):
        proc = self._make()
        jobs = proc.registry.list_jobs()
        names = [j.name for j in jobs]
        assert "process_tyt_exam" in names
        assert "process_ayt_exam" in names
        assert "cleanup_expired_sessions" in names

    def test_get_job_stats_empty(self):
        proc = self._make()
        stats = proc.job_stats
        # defaultdict — accessing a key creates it
        assert isinstance(stats, dict)

    def test_update_job_stats_success(self):
        proc = self._make()
        proc._update_job_stats("process_tyt_exam", True, 1.5)
        s = proc.job_stats["process_tyt_exam"]
        assert s["total_executions"] == 1
        assert s["successful_executions"] == 1

    def test_update_job_stats_failure(self):
        proc = self._make()
        proc._update_job_stats("process_ayt_exam", False, 2.0)
        s = proc.job_stats["process_ayt_exam"]
        assert s["failed_executions"] == 1

    def test_update_job_stats_avg_time(self):
        proc = self._make()
        proc._update_job_stats("job_x", True, 2.0)
        proc._update_job_stats("job_x", True, 4.0)
        s = proc.job_stats["job_x"]
        assert s["avg_execution_time"] == 3.0

    @pytest.mark.asyncio
    async def test_schedule_job_unknown_raises(self):
        proc = self._make()
        with pytest.raises(ValueError, match="not found in registry"):
            await proc.schedule_job("nonexistent_job")

    @pytest.mark.asyncio
    async def test_schedule_job_valid(self):
        proc = self._make()
        # Mock the actual execution to avoid running async jobs
        proc._enqueue_job_execution = AsyncMock()
        job_id = await proc.schedule_job("cleanup_expired_sessions")
        assert job_id  # non-empty string UUID


# ─────────────────────────────────────────────────────────────────
# ─── SECTION 4: core/security_event_monitoring.py ────────────────
# ─────────────────────────────────────────────────────────────────


@pytest.mark.skipif(not _HAS_SEC_MON, reason="security_event_monitoring not importable")
class TestSecurityEventType:
    def test_event_type_attribute(self):
        SET = sec_mon.SecurityEventType
        assert SET.LOGIN_SUCCESS.event_type == "login_success"
        assert SET.BRUTE_FORCE_ATTACK.event_type == "brute_force_attack"

    def test_turkish_description(self):
        SET = sec_mon.SecurityEventType
        assert SET.LOGIN_FAILURE.turkish_description == "Başarısız Giriş"


@pytest.mark.skipif(not _HAS_SEC_MON, reason="security_event_monitoring not importable")
class TestSecuritySeverity:
    def test_score_levels(self):
        SS = sec_mon.SecuritySeverity
        assert SS.INFO.score == 1
        assert SS.CRITICAL.score == 100
        assert SS.MEDIUM.score == 50


@pytest.mark.skipif(not _HAS_SEC_MON, reason="security_event_monitoring not importable")
class TestSecurityEvent:
    def _make(self):
        return sec_mon.SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=sec_mon.SecurityEventType.LOGIN_SUCCESS,
            severity=sec_mon.SecuritySeverity.INFO,
            timestamp=datetime.now(UTC),
            ip_address="127.0.0.1",
            user_id=1,
        )

    def test_to_dict_has_required_keys(self):
        ev = self._make()
        d = ev.to_dict()
        assert "event_id" in d
        assert "event_type" in d
        assert "severity_score" in d
        assert d["severity_score"] == 1

    def test_to_dict_type_values(self):
        ev = self._make()
        d = ev.to_dict()
        assert d["event_type"] == "login_success"
        assert d["event_type_tr"] == "Başarılı Giriş"


@pytest.mark.skipif(not _HAS_SEC_MON, reason="security_event_monitoring not importable")
class TestThreatDetector:
    def _make(self):
        return sec_mon.ThreatDetector()

    def test_attack_patterns_loaded(self):
        td = self._make()
        assert "sql_injection" in td.attack_patterns
        assert "xss" in td.attack_patterns
        assert "path_traversal" in td.attack_patterns

    @pytest.mark.asyncio
    async def test_is_suspicious_user_agent_empty(self):
        td = self._make()
        assert await td._is_suspicious_user_agent("") is True

    @pytest.mark.asyncio
    async def test_is_suspicious_user_agent_short(self):
        td = self._make()
        assert await td._is_suspicious_user_agent("bot") is True

    @pytest.mark.asyncio
    async def test_is_suspicious_user_agent_crawler(self):
        td = self._make()
        assert await td._is_suspicious_user_agent("Googlebot/2.1") is True

    @pytest.mark.asyncio
    async def test_is_suspicious_user_agent_normal(self):
        td = self._make()
        normal_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        assert await td._is_suspicious_user_agent(normal_ua) is False

    @pytest.mark.asyncio
    async def test_check_rate_limit_violation_returns_false(self):
        td = self._make()
        # Simplified: always returns False
        result = await td._check_rate_limit_violation("1.2.3.4", None)
        assert result is False

    @pytest.mark.asyncio
    async def test_detect_threats_clean_request(self):
        td = self._make()
        request_data = {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "payload": {"name": "Ali", "age": 20},
            "headers": {},
            "endpoint": "/api/v1/profile",
            "method": "GET",
        }
        threats = await td.detect_threats(request_data)
        assert isinstance(threats, list)

    @pytest.mark.asyncio
    async def test_detect_injection_attacks_sql(self):
        td = self._make()
        payload = {"query": "' OR 1=1 --"}
        threats = await td._detect_injection_attacks(payload, "1.2.3.4", None)
        # Should detect SQL injection
        assert any(
            t.event_type == sec_mon.SecurityEventType.SQL_INJECTION_ATTEMPT
            for t in threats
        )

    @pytest.mark.asyncio
    async def test_detect_injection_attacks_xss(self):
        td = self._make()
        payload = {"content": "<script>alert('xss')</script>"}
        threats = await td._detect_injection_attacks(payload, "1.2.3.4", 1)
        assert any(
            t.event_type == sec_mon.SecurityEventType.XSS_ATTEMPT for t in threats
        )

    @pytest.mark.asyncio
    async def test_detect_injection_attacks_path_traversal(self):
        td = self._make()
        payload = {"file": "../../../etc/passwd"}
        threats = await td._detect_injection_attacks(payload, "1.2.3.4", None)
        assert any(
            t.event_type == sec_mon.SecurityEventType.PATH_TRAVERSAL_ATTEMPT
            for t in threats
        )

    @pytest.mark.asyncio
    async def test_brute_force_no_db_returns_false(self):
        td = self._make()
        result = await td._detect_brute_force("5.5.5.5", None)
        # DB call returns None → should return False
        assert result is False


# ─────────────────────────────────────────────────────────────────
# ─── SECTION 5: core/auth_middleware.py ──────────────────────────
# ─────────────────────────────────────────────────────────────────


class TestUserRole:
    def test_role_values(self):
        UR = auth_mw.UserRole
        assert UR.STUDENT == "student"
        assert UR.TEACHER == "teacher"
        assert UR.ADMIN == "admin"


class TestAuthUser:
    def _make(self, role=None, perms=None):
        return auth_mw.AuthUser(
            user_id=1,
            username="test_user",
            email="test@example.com",
            role=role or auth_mw.UserRole.STUDENT,
            permissions=perms or {auth_mw.Permission.TAKE_TYT_EXAM},
        )

    def test_has_permission_true(self):
        u = self._make(perms={auth_mw.Permission.TAKE_TYT_EXAM})
        assert u.has_permission(auth_mw.Permission.TAKE_TYT_EXAM) is True

    def test_has_permission_false(self):
        u = self._make(perms=set())
        assert u.has_permission(auth_mw.Permission.MANAGE_USERS) is False

    def test_is_student(self):
        u = self._make(role=auth_mw.UserRole.STUDENT)
        assert u.is_student() is True

    def test_is_not_student(self):
        u = self._make(role=auth_mw.UserRole.ADMIN)
        assert u.is_student() is False

    def test_is_admin_admin_role(self):
        u = self._make(role=auth_mw.UserRole.ADMIN)
        assert u.is_admin() is True

    def test_is_admin_system_role(self):
        u = self._make(role=auth_mw.UserRole.SYSTEM)
        assert u.is_admin() is True

    def test_is_admin_student_role(self):
        u = self._make(role=auth_mw.UserRole.STUDENT)
        assert u.is_admin() is False

    def test_has_role_match(self):
        u = self._make(role=auth_mw.UserRole.TEACHER)
        assert u.has_role(auth_mw.UserRole.TEACHER) is True

    def test_has_role_no_match(self):
        u = self._make(role=auth_mw.UserRole.STUDENT)
        assert u.has_role(auth_mw.UserRole.ADMIN) is False

    def test_can_take_exam_tyt(self):
        u = self._make(perms={auth_mw.Permission.TAKE_TYT_EXAM})
        assert u.can_take_exam("tyt") is True

    def test_can_take_exam_ayt_missing_perm(self):
        u = self._make(perms={auth_mw.Permission.TAKE_TYT_EXAM})
        assert u.can_take_exam("ayt") is False

    def test_can_take_exam_unknown_type(self):
        u = self._make(perms={auth_mw.Permission.TAKE_TYT_EXAM})
        # Unknown exam type: required_permission is None → falsy (None, not False)
        assert not u.can_take_exam("xyz")


class TestPermission:
    def test_exam_permissions_present(self):
        P = auth_mw.Permission
        assert P.TAKE_TYT_EXAM.value == "take_tyt_exam"
        assert P.VIEW_EXAM_RESULTS.value == "view_exam_results"
        assert P.MANAGE_USERS.value == "manage_users"


class TestAuthContext:
    def test_defaults(self):
        ctx = auth_mw.AuthContext()
        assert ctx.authenticated is False
        assert ctx.user is None

    def test_with_user(self):
        user = MagicMock()
        ctx = auth_mw.AuthContext(user=user, authenticated=True)
        assert ctx.authenticated is True
        assert ctx.user is user


class TestJWTManager:
    def _make(self):
        return auth_mw.JWTManager(
            {
                "jwt_secret_key": "test-secret-key",
                "jwt_algorithm": "HS256",
                "access_token_expire_minutes": 30,
                "refresh_token_expire_days": 7,
                "jwt_issuer": "test-issuer",
            }
        )

    def _make_user(self):
        return auth_mw.AuthUser(
            user_id=42,
            username="ali",
            email="ali@example.com",
            role=auth_mw.UserRole.STUDENT,
            permissions={auth_mw.Permission.TAKE_TYT_EXAM},
            session_id="sess-1",
        )

    def test_generate_access_token_returns_string(self):
        mgr = self._make()
        user = self._make_user()
        token = mgr.generate_access_token(user)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_refresh_token_returns_string(self):
        mgr = self._make()
        user = self._make_user()
        token = mgr.generate_refresh_token(user)
        assert isinstance(token, str)

    def test_validate_token_valid(self):
        mgr = self._make()
        user = self._make_user()
        token = mgr.generate_access_token(user)
        payload = mgr.validate_token(token)
        assert payload["sub"] == "42"

    def test_validate_token_invalid_raises(self):
        mgr = self._make()
        with pytest.raises(ValueError):
            mgr.validate_token("not.a.real.token")

    def test_validate_token_expired_raises(self):
        import jwt as _jwt

        mgr = self._make()
        # Manually create expired token
        past = datetime.now(UTC) - timedelta(hours=1)
        payload = {
            "sub": "1",
            "exp": past.timestamp(),
            "iss": "test-issuer",
            "iat": past.timestamp(),
        }
        expired_token = _jwt.encode(payload, "test-secret-key", algorithm="HS256")
        with pytest.raises(ValueError):
            mgr.validate_token(expired_token)


class TestAuthenticationMethod:
    def test_values_present(self):
        AM = auth_mw.AuthenticationMethod
        assert AM.JWT_TOKEN.value == "jwt_token"
        assert AM.API_KEY.value == "api_key"


# ─────────────────────────────────────────────────────────────────
# ─── SECTION 6: services/visual_content_generator.py ─────────────
# ─────────────────────────────────────────────────────────────────


class TestVisualContentGenerator:
    def _make(self):
        vcg = visual_gen.VisualContentGenerator()
        # Stub out sub-generators
        vcg.graph_generator = MagicMock()
        vcg.graph_generator.generate_graph = MagicMock(
            return_value={"type": "graph", "content": "<svg/>"}
        )
        vcg.geometry_generator = MagicMock()
        vcg.geometry_generator.generate_geometry = MagicMock(
            return_value={"type": "geometry", "content": "<svg/>"}
        )
        vcg.map_diagram_generator = MagicMock()
        vcg.map_diagram_generator.generate_map_diagram = MagicMock(
            return_value={"type": "map", "content": "<svg/>"}
        )
        return vcg

    def test_init_visual_types(self):
        vcg = self._make()
        assert "table" in vcg.visual_types
        assert "graph" in vcg.visual_types
        assert "geometry" in vcg.visual_types
        assert "map_diagram" in vcg.visual_types

    # ── Phase 1: Tables ──

    def test_generate_table_frequency(self):
        vcg = self._make()
        result = vcg.generate_table("Matematik", "İstatistik", "frequency_table")
        assert result["type"] == "table"
        assert "content" in result
        assert "data" in result

    def test_generate_table_comparison(self):
        vcg = self._make()
        result = vcg.generate_table("Fen", "Karşılaştırma", "comparison_table")
        assert result["type"] == "table"

    def test_generate_table_statistics(self):
        vcg = self._make()
        result = vcg.generate_table("Matematik", "İstatistik", "statistics_table")
        assert "statistics" in result["data"]

    def test_generate_table_price(self):
        vcg = self._make()
        result = vcg.generate_table("Matematik", "Oran Orantı", "price_table")
        assert result["type"] == "table"

    def test_generate_table_grade(self):
        vcg = self._make()
        result = vcg.generate_table("Türkçe", "Değerlendirme", "grade_table")
        assert result["type"] == "table"

    def test_generate_table_schedule(self):
        vcg = self._make()
        result = vcg.generate_table("Genel", "Program", "schedule_table")
        assert result["type"] == "table"

    def test_generate_table_unknown_falls_back_to_generic(self):
        vcg = self._make()
        result = vcg.generate_table("Genel", "Konu", "nonexistent_type")
        assert result["type"] == "table"

    def test_build_markdown_table_format(self):
        vcg = self._make()
        headers = ["A", "B"]
        rows = ["| x | y |"]
        md = vcg._build_markdown_table(headers, rows)
        assert "| A | B |" in md
        assert "---" in md

    def test_frequency_table_has_percentages(self):
        vcg = self._make()
        result = vcg._generate_frequency_table(3)
        assert "total" in result["data"]
        assert result["data"]["total"] > 0

    def test_statistics_table_has_mean(self):
        vcg = self._make()
        result = vcg._generate_statistics_table()
        assert "Ortalama" in result["data"]["statistics"]

    def test_grade_table_rows_correct_count(self):
        vcg = self._make()
        result = vcg._generate_grade_table(4)
        assert result["metadata"]["rows"] == 4

    # ── Phase 2: Graphs ──

    def test_generate_graph_line(self):
        vcg = self._make()
        result = vcg.generate_graph("Fizik", "Hareket", "line")
        vcg.graph_generator.generate_graph.assert_called_once()

    def test_generate_graph_bar(self):
        vcg = self._make()
        result = vcg.generate_graph("Matematik", "İstatistik", "bar")
        vcg.graph_generator.generate_graph.assert_called_once()

    def test_generate_graph_pie(self):
        vcg = self._make()
        result = vcg.generate_graph("Coğrafya", "Nüfus", "pie")
        args = vcg.graph_generator.generate_graph.call_args
        assert args[1]["graph_type"] == "pie"

    def test_generate_graph_scatter(self):
        vcg = self._make()
        result = vcg.generate_graph("Matematik", "Korelasyon", "scatter")
        vcg.graph_generator.generate_graph.assert_called_once()

    def test_generate_graph_histogram(self):
        vcg = self._make()
        result = vcg.generate_graph("Biyoloji", "Dağılım", "histogram")
        vcg.graph_generator.generate_graph.assert_called_once()

    def test_generate_graph_unknown_type_raises(self):
        vcg = self._make()
        with pytest.raises(ValueError, match="Unknown graph_type"):
            vcg.generate_graph("Fizik", "Konu", "unknown_type")

    def test_generate_line_data_fizik(self):
        vcg = self._make()
        data = vcg._generate_line_data("fizik", "hareket", "medium")
        assert "x" in data and "y" in data
        assert len(data["x"]) == len(data["y"])

    def test_generate_line_data_matematik(self):
        vcg = self._make()
        data = vcg._generate_line_data("matematik", "fonksiyon", "medium")
        assert data["y"][5] == 0  # x=0 → x^2 = 0

    def test_generate_bar_data_matematik(self):
        vcg = self._make()
        data = vcg._generate_bar_data("matematik", "istatistik", "medium")
        assert "categories" in data

    def test_generate_pie_data_cografya(self):
        vcg = self._make()
        data = vcg._generate_pie_data("cografya", "nufus", "medium")
        assert sum(data["values"]) == 100

    def test_generate_scatter_data_matematik(self):
        vcg = self._make()
        data = vcg._generate_scatter_data("matematik", "korelasyon", "medium")
        assert data["show_trendline"] is True

    def test_generate_histogram_data_biyoloji(self):
        vcg = self._make()
        data = vcg._generate_histogram_data("biyoloji", "olcum", "medium")
        assert "values" in data
        assert len(data["values"]) == 50

    def test_get_x_label_fizik(self):
        vcg = self._make()
        assert vcg._get_x_label("fizik", "line") == "Zaman (s)"

    def test_get_x_label_default(self):
        vcg = self._make()
        assert vcg._get_x_label("tarih", "bar") == "X Ekseni"

    def test_get_y_label_fizik(self):
        vcg = self._make()
        assert vcg._get_y_label("fizik", "line") == "Hız (m/s)"

    def test_get_y_label_matematik_bar(self):
        vcg = self._make()
        assert vcg._get_y_label("matematik", "bar") == "Frekans"
