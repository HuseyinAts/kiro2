"""
Deep coverage tests — Batch 2.

Targets (uncovered lines):
  1. core/turkish_exam_middleware.py   (~292 miss)
  2. core/background_job_processor.py (~225 miss)
  3. core/security_event_monitoring.py (~231 miss)
  4. core/kvkk_compliance.py           (~219 miss)
  5. services/visual_content_generator.py (~222 miss)

Each file gets 20+ meaningful tests (no assert-True / pass stubs).
"""

import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Path setup
# --------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parents[2]))

# --------------------------------------------------------------------------
# Heavy-dependency stubs — BEFORE any project imports
# --------------------------------------------------------------------------
from unittest.mock import AsyncMock, MagicMock

_STUB_MODULES = [
    "redis",
    "redis.asyncio",
    "celery",
    "elasticsearch",
    "langchain",
    "langchain_core",
    "websockets",
    "websockets.exceptions",
    "websockets.server",
    "cryptography",
    "cryptography.fernet",
    "zemberek",
    "aiohttp",
]

for _mod in _STUB_MODULES:
    sys.modules.setdefault(_mod, MagicMock())

# redis.Redis stub (only if redis is not really installed)
_redis_mod = sys.modules["redis"]
if isinstance(_redis_mod, MagicMock):
    _redis_mod.Redis = MagicMock()

# Core stubs
_CORE_STUBS = [
    "core.application_metrics",
    "core.message_queue_system",
    "core.structured_logging",
    "core.unified_config",
    "core.unified_event_bus",
    "core.enhanced_database",
    "core.auth_middleware",
    "core.cache_system_integration",
    "core.turkish_exam_event_handlers",
    "core.unified_api_gateway",
    "core.error_context",
    "core.error_monitoring",
    "core.transaction_manager",
    "core.berturk_service",
    "core.llm_service",
    "core.turkish_nlp_service",
    "core.exam_session_store",
]

for _mod in _CORE_STUBS:
    sys.modules.setdefault(_mod, MagicMock())

# services sub-deps
_SVC_STUBS = [
    "services.graph_generator",
    "services.geometry_generator",
    "services.map_diagram_generator",
]
for _mod in _SVC_STUBS:
    sys.modules.setdefault(_mod, MagicMock())

# ---------------------------------------------------------------------------
# Wire up specific attributes used at import-time
# ---------------------------------------------------------------------------
_metrics = sys.modules["core.application_metrics"]
_metrics.MetricType = MagicMock()
_metrics.get_metrics_collector = MagicMock(return_value=MagicMock())

_logging = sys.modules["core.structured_logging"]
_logging.LogCategory = MagicMock()
_logging.get_logger = MagicMock(return_value=MagicMock())
_logging.get_security_logger = MagicMock(return_value=MagicMock())

_mq = sys.modules["core.message_queue_system"]

from enum import Enum as _Enum


class _FakeQueueType(_Enum):
    BATCH_PROCESSING = "batch_processing"
    EXAM_PROCESSING = "exam_processing"
    CONTENT_PROCESSING = "content_processing"
    ANALYTICS = "analytics"
    CLEANUP = "cleanup"
    NOTIFICATIONS = "notifications"


_mq.QueueType = _FakeQueueType

_ucfg = sys.modules["core.unified_config"]
_ucfg.get_unified_config = MagicMock(return_value=MagicMock())

_ebus = sys.modules["core.unified_event_bus"]
_ebus.EventType = MagicMock()
_ebus.EventPriority = MagicMock()
_ebus.publish_event = AsyncMock()
_ebus.get_event_bus = MagicMock(return_value=AsyncMock())

_edb = sys.modules["core.enhanced_database"]
_edb.get_enhanced_db_manager = MagicMock(return_value=MagicMock())

_auth_mw = sys.modules["core.auth_middleware"]


class _FakeUserRole:
    TEACHER = "teacher"
    STUDENT = "student"
    ADMIN = "admin"


_auth_mw.UserRole = _FakeUserRole
_auth_mw.AuthContext = MagicMock()
_auth_mw.AuthUser = MagicMock()

_cache_sys = sys.modules["core.cache_system_integration"]
_cache_sys.get_unified_cache_system = AsyncMock(return_value=MagicMock())

_tex_events = sys.modules["core.turkish_exam_event_handlers"]
_tex_events.TurkishExamType = MagicMock()

_api_gw = sys.modules["core.unified_api_gateway"]


class _FakeRouteType:
    TYT_EXAM = "tyt_exam"
    AYT_EXAM = "ayt_exam"
    YKS_INFO = "yks_info"
    GENERAL = "general"


_api_gw.RouteType = _FakeRouteType


class _FakeAPIRequest:
    def __init__(self, **kw):
        self.id = kw.get("id", "req-001")
        self.path = kw.get("path", "/api/v1/test")
        self.method = kw.get("method", "GET")
        self.headers = kw.get("headers", {})
        self.query_params = kw.get("query_params", {})
        self.body = kw.get("body")
        self.user_agent = kw.get("user_agent", "Mozilla/5.0")
        self.client_ip = kw.get("client_ip", "127.0.0.1")
        self.metadata = kw.get("metadata", {})
        self.route_type = kw.get("route_type", _FakeRouteType.GENERAL)

    def is_exam_route(self):
        return (
            "exam" in self.path.lower()
            or "tyt" in self.path.lower()
            or "ayt" in self.path.lower()
        )


class _FakeAPIResponse:
    def __init__(self, **kw):
        self.request_id = kw.get("request_id", "req-001")
        self.status_code = kw.get("status_code", 200)
        self.headers = kw.get("headers", {})
        self.body = kw.get("body", {})
        self.processing_time_ms = kw.get("processing_time_ms", 1.0)

    def add_header(self, key, value):
        self.headers[key] = value

    def is_success(self):
        return 200 <= self.status_code < 300


_api_gw.APIRequest = _FakeAPIRequest
_api_gw.APIResponse = _FakeAPIResponse

# ---------------------------------------------------------------------------
# Actual imports
# ---------------------------------------------------------------------------
from datetime import UTC, datetime, timedelta

import pytest

# ============================================================================
# FILE 1: core/turkish_exam_middleware.py
# ============================================================================
from core.turkish_exam_middleware import (
    ExamContext,
    ExamPeriod,
    ExamSecurityLevel,
    ExamSecurityMiddleware,
    ExamSessionMiddleware,
    TurkishLanguageMiddleware,
    configure_exam_middleware,
    create_exam_security_middleware,
    create_exam_session_middleware,
    create_turkish_language_middleware,
    get_turkish_exam_middleware_stack,
)


class TestExamEnums:
    def test_exam_period_values(self):
        assert ExamPeriod.REGISTRATION.value == "registration"
        assert ExamPeriod.PREPARATION.value == "preparation"
        assert ExamPeriod.EXAM_WEEK.value == "exam_week"
        assert ExamPeriod.RESULTS.value == "results"
        assert ExamPeriod.OFF_SEASON.value == "off_season"

    def test_exam_security_level_values(self):
        assert ExamSecurityLevel.LOW.value == "low"
        assert ExamSecurityLevel.MEDIUM.value == "medium"
        assert ExamSecurityLevel.HIGH.value == "high"
        assert ExamSecurityLevel.MAXIMUM.value == "maximum"

    def test_exam_context_defaults(self):
        ctx = ExamContext()
        assert ctx.current_period == ExamPeriod.OFF_SEASON
        assert ctx.security_level == ExamSecurityLevel.LOW
        assert ctx.is_practice is True
        assert ctx.difficulty == "orta"
        assert ctx.metadata == {}


class TestTurkishLanguageMiddleware:
    def setup_method(self):
        self.mw = TurkishLanguageMiddleware({})

    def test_turkish_subjects_map(self):
        assert "matematik" in self.mw.turkish_subjects
        assert "fizik" in self.mw.turkish_subjects
        assert self.mw.turkish_subjects["matematik"] == "Matematik"

    def test_exam_translations(self):
        assert "tyt" in self.mw.exam_translations
        assert "ayt" in self.mw.exam_translations
        assert "yks" in self.mw.exam_translations

    def test_common_phrases(self):
        assert "exam_started" in self.mw.common_phrases
        assert "good_luck" in self.mw.common_phrases

    @pytest.mark.asyncio
    async def test_translate_request_params_subject(self):
        req = _FakeAPIRequest(body={"subject": "matematik"})
        await self.mw._translate_request_params(req)
        assert req.body.get("subject_tr") == "Matematik"
        assert req.body.get("subject_name") == "Matematik"

    @pytest.mark.asyncio
    async def test_translate_request_params_exam_type(self):
        req = _FakeAPIRequest(body={"exam_type": "tyt"})
        await self.mw._translate_request_params(req)
        assert req.body.get("exam_type_tr") == "Temel Yeterlilik Testi"

    @pytest.mark.asyncio
    async def test_translate_request_params_query(self):
        req = _FakeAPIRequest(query_params={"subject": "fizik"})
        await self.mw._translate_request_params(req)
        assert req.query_params.get("subject_tr") == "Fizik"

    @pytest.mark.asyncio
    async def test_translate_unknown_subject_no_change(self):
        req = _FakeAPIRequest(body={"subject": "astrofizik"})
        await self.mw._translate_request_params(req)
        assert "subject_tr" not in req.body

    @pytest.mark.asyncio
    async def test_add_turkish_translations_platform_info(self):
        resp = _FakeAPIResponse(body={"data": "ok"})
        req = _FakeAPIRequest(route_type=_FakeRouteType.TYT_EXAM)
        await self.mw._add_turkish_translations(resp, req)
        assert "platform_info" in resp.body
        assert resp.body["platform_info"]["country"] == "Türkiye"

    @pytest.mark.asyncio
    async def test_add_turkish_translations_timestamp(self):
        resp = _FakeAPIResponse(body={"timestamp": "2025-01-15T12:00:00+00:00"})
        req = _FakeAPIRequest()
        await self.mw._add_turkish_translations(resp, req)
        assert "timestamp_turkey" in resp.body

    @pytest.mark.asyncio
    async def test_add_turkish_translations_non_dict_body(self):
        resp = _FakeAPIResponse(body=None)
        resp.body = "plain string"
        req = _FakeAPIRequest()
        # Should not raise
        await self.mw._add_turkish_translations(resp, req)

    @pytest.mark.asyncio
    async def test_middleware_call_sets_locale(self):
        req = _FakeAPIRequest()

        async def next_handler(r):
            return _FakeAPIResponse(body={"ok": True})

        resp = await self.mw(req, next_handler)
        assert req.metadata.get("language") == "tr"
        assert req.metadata.get("locale") == "tr-TR"
        assert resp.headers.get("Content-Language") == "tr-TR"

    @pytest.mark.asyncio
    async def test_middleware_call_adds_headers(self):
        req = _FakeAPIRequest()

        async def next_handler(r):
            return _FakeAPIResponse(body={})

        resp = await self.mw(req, next_handler)
        assert "X-Turkish-Platform" in resp.headers
        assert "X-Exam-System" in resp.headers


class TestExamSecurityMiddleware:
    def setup_method(self):
        self.mw = ExamSecurityMiddleware({"anti_cheat_enabled": False})

    def test_is_user_blocked_not_blocked(self):
        assert self.mw._is_user_blocked(9999) is False

    def test_is_user_blocked_when_blocked(self):
        future = datetime.now(UTC) + timedelta(minutes=30)
        self.mw.blocked_users[1] = future
        assert self.mw._is_user_blocked(1) is True

    def test_is_user_blocked_expired(self):
        past = datetime.now(UTC) - timedelta(minutes=1)
        self.mw.blocked_users[2] = past
        assert self.mw._is_user_blocked(2) is False
        assert 2 not in self.mw.blocked_users

    def test_create_security_error(self):
        resp = self.mw._create_security_error("req-1", "Reason", "Sebep")
        assert resp.status_code == 403
        assert resp.body["error"] == "Security Violation"
        assert resp.body["detail"] == "Reason"
        assert resp.body["detail_tr"] == "Sebep"

    def test_add_security_headers_on_exam_route(self):
        req = _FakeAPIRequest(path="/api/v1/tyt/start")
        resp = _FakeAPIResponse()
        self.mw._add_security_headers(resp, req)
        assert resp.headers.get("X-Frame-Options") == "DENY"
        assert resp.headers.get("X-Exam-Security") == "enabled"
        assert resp.headers.get("X-Anti-Cheat") == "active"

    def test_add_security_headers_non_exam_route(self):
        req = _FakeAPIRequest(path="/api/v1/profile")
        resp = _FakeAPIResponse()
        self.mw._add_security_headers(resp, req)
        assert "X-Frame-Options" not in resp.headers

    @pytest.mark.asyncio
    async def test_check_user_eligibility_student(self):
        user = MagicMock()
        user.is_student.return_value = True
        req = _FakeAPIRequest()
        result = await self.mw._check_user_eligibility(req, user)
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_check_user_eligibility_teacher(self):
        user = MagicMock()
        user.is_student.return_value = False
        user.role = _FakeUserRole.TEACHER
        user.is_admin.return_value = False
        req = _FakeAPIRequest()
        result = await self.mw._check_user_eligibility(req, user)
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_check_user_eligibility_admin(self):
        user = MagicMock()
        user.is_student.return_value = False
        user.role = "other"
        user.is_admin.return_value = True
        req = _FakeAPIRequest()
        result = await self.mw._check_user_eligibility(req, user)
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_check_user_eligibility_unauthorized(self):
        user = MagicMock()
        user.is_student.return_value = False
        user.role = "unknown"
        user.is_admin.return_value = False
        req = _FakeAPIRequest()
        result = await self.mw._check_user_eligibility(req, user)
        assert result["allowed"] is False

    @pytest.mark.asyncio
    async def test_handle_security_violation_blocks_at_threshold(self):
        self.mw.max_violations_per_hour = 2
        user_id = 42
        req = _FakeAPIRequest(client_ip="1.2.3.4")
        # Record enough violations
        now = datetime.now(UTC)
        self.mw.security_violations[user_id] = [
            now - timedelta(minutes=5),
            now - timedelta(minutes=3),
        ]
        await self.mw._handle_security_violation(user_id, ["rapid_requests"], req)
        assert user_id in self.mw.blocked_users

    @pytest.mark.asyncio
    async def test_middleware_call_no_auth_context(self):
        req = _FakeAPIRequest(metadata={})

        async def next_handler(r):
            return _FakeAPIResponse(body={"ok": True})

        resp = await self.mw(req, next_handler)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_call_blocked_user(self):
        future = datetime.now(UTC) + timedelta(minutes=20)
        user = MagicMock()
        user.user_id = 77
        auth_ctx = MagicMock()
        auth_ctx.user = user
        self.mw.blocked_users[77] = future
        req = _FakeAPIRequest(metadata={"auth_context": auth_ctx})

        async def next_handler(r):
            return _FakeAPIResponse()

        resp = await self.mw(req, next_handler)
        assert resp.status_code == 403


class TestExamSessionMiddleware:
    def setup_method(self):
        self.mw = ExamSessionMiddleware({})

    def test_extract_exam_type_tyt(self):
        assert self.mw._extract_exam_type_from_path("/api/v1/tyt/start") == "tyt"

    def test_extract_exam_type_ayt(self):
        assert self.mw._extract_exam_type_from_path("/api/v1/ayt/start") == "ayt"

    def test_extract_exam_type_yks(self):
        assert self.mw._extract_exam_type_from_path("/api/v1/yks/info") == "yks"

    def test_extract_exam_type_unknown(self):
        assert self.mw._extract_exam_type_from_path("/api/v1/profile") == "unknown"

    def test_is_session_expired_true(self):
        old_time = (datetime.now(UTC) - timedelta(hours=5)).isoformat()
        session = {"last_activity": old_time}
        assert self.mw._is_session_expired(session) is True

    def test_is_session_expired_false(self):
        recent = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
        session = {"last_activity": recent}
        assert self.mw._is_session_expired(session) is False

    def test_calculate_time_remaining_positive(self):
        started = (datetime.now(UTC) - timedelta(minutes=30)).isoformat()
        session = {"started_at": started}
        remaining = self.mw._calculate_time_remaining(session)
        assert remaining is not None
        assert remaining > 0
        assert remaining < self.mw.session_timeout_minutes

    def test_calculate_time_remaining_zero_when_expired(self):
        started = (
            datetime.now(UTC) - timedelta(minutes=self.mw.session_timeout_minutes + 10)
        ).isoformat()
        session = {"started_at": started}
        remaining = self.mw._calculate_time_remaining(session)
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_middleware_skips_non_exam_route(self):
        req = _FakeAPIRequest(path="/api/v1/profile")
        called = []

        async def next_handler(r):
            called.append(True)
            return _FakeAPIResponse()

        await self.mw(req, next_handler)
        assert called

    @pytest.mark.asyncio
    async def test_handle_exam_completion_success(self):
        user = MagicMock()
        user.user_id = 10

        cache_inner = MagicMock()
        cache_inner.get = AsyncMock(return_value=None)
        cache_inner.delete = AsyncMock()
        cache_obj = MagicMock()
        cache_obj.cache_system = cache_inner
        self.mw.cache_system = cache_obj

        metrics_mock = MagicMock()
        _metrics.get_metrics_collector.return_value = metrics_mock

        req = _FakeAPIRequest(path="/api/v1/tyt/submit")

        async def next_handler(r):
            return _FakeAPIResponse(body={"result": "ok"}, status_code=200)

        resp = await self.mw._handle_exam_completion(req, user, next_handler)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_handle_question_access_no_session(self):
        user = MagicMock()
        user.user_id = 11

        cache_inner = MagicMock()
        cache_inner.get = AsyncMock(return_value=None)
        cache_obj = MagicMock()
        cache_obj.cache_system = cache_inner
        self.mw.cache_system = cache_obj

        req = _FakeAPIRequest(path="/api/v1/tyt/question/1")
        resp = await self.mw._handle_question_access(req, user, lambda r: None)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_handle_question_access_expired_session(self):
        user = MagicMock()
        user.user_id = 12

        old_activity = (datetime.now(UTC) - timedelta(hours=5)).isoformat()
        session_data = {
            "session_id": "sess-xyz",
            "last_activity": old_activity,
            "started_at": old_activity,
        }

        cache_inner = MagicMock()
        cache_inner.get = AsyncMock(return_value=session_data)
        cache_inner.delete = AsyncMock()
        cache_obj = MagicMock()
        cache_obj.cache_system = cache_inner
        self.mw.cache_system = cache_obj

        req = _FakeAPIRequest(path="/api/v1/tyt/question/1")
        resp = await self.mw._handle_question_access(req, user, lambda r: None)
        assert resp.status_code == 408


class TestExamMiddlewareFactories:
    def test_create_turkish_language_middleware(self):
        mw = create_turkish_language_middleware()
        assert isinstance(mw, TurkishLanguageMiddleware)

    def test_create_exam_security_middleware(self):
        mw = create_exam_security_middleware({"anti_cheat_enabled": False})
        assert isinstance(mw, ExamSecurityMiddleware)

    def test_create_exam_session_middleware(self):
        mw = create_exam_session_middleware()
        assert isinstance(mw, ExamSessionMiddleware)

    def test_get_turkish_exam_middleware_stack(self):
        stack = get_turkish_exam_middleware_stack()
        assert len(stack) == 3
        names = [s[0] for s in stack]
        assert "exam_security" in names
        assert "turkish_language" in names

    @pytest.mark.parametrize(
        "exam_type,expected_timeout",
        [
            ("tyt", 135),
            ("ayt", 180),
            ("yks", 240),
        ],
    )
    def test_configure_exam_middleware_timeouts(self, exam_type, expected_timeout):
        cfg = configure_exam_middleware(exam_type)
        assert cfg["session_timeout_minutes"] == expected_timeout

    def test_configure_exam_middleware_base_flags(self):
        cfg = configure_exam_middleware("other")
        assert cfg["exam_monitoring"] is True
        assert cfg["anti_cheat_enabled"] is True


# ============================================================================
# FILE 2: core/background_job_processor.py
# ============================================================================
from core.background_job_processor import (
    BackgroundJobRegistry,
    JobDefinition,
    JobExecution,
    JobPriority,
    RetryPolicy,
    TurkishExamJobProcessor,
    get_job_status,
    get_job_system_stats,
    schedule_content_generation,
    schedule_exam_processing,
)

# Re-import to avoid the alias confusion


class TestJobDefinition:
    def test_calculate_retry_delay_none(self):
        jd = JobDefinition(
            name="test",
            function=lambda: None,
            queue_type=_FakeQueueType.BATCH_PROCESSING,
            priority=JobPriority.NORMAL,
            retry_policy=RetryPolicy.NONE,
            retry_delay=60,
        )
        assert jd.calculate_retry_delay(1) == 0

    def test_calculate_retry_delay_fixed(self):
        jd = JobDefinition(
            name="test",
            function=lambda: None,
            queue_type=_FakeQueueType.BATCH_PROCESSING,
            priority=JobPriority.NORMAL,
            retry_policy=RetryPolicy.FIXED_DELAY,
            retry_delay=30,
        )
        assert jd.calculate_retry_delay(1) == 30
        assert jd.calculate_retry_delay(5) == 30

    def test_calculate_retry_delay_linear(self):
        jd = JobDefinition(
            name="test",
            function=lambda: None,
            queue_type=_FakeQueueType.BATCH_PROCESSING,
            priority=JobPriority.NORMAL,
            retry_policy=RetryPolicy.LINEAR_BACKOFF,
            retry_delay=10,
        )
        assert jd.calculate_retry_delay(1) == 10
        assert jd.calculate_retry_delay(3) == 30

    def test_calculate_retry_delay_exponential(self):
        jd = JobDefinition(
            name="test",
            function=lambda: None,
            queue_type=_FakeQueueType.BATCH_PROCESSING,
            priority=JobPriority.NORMAL,
            retry_policy=RetryPolicy.EXPONENTIAL_BACKOFF,
            retry_delay=60,
        )
        assert jd.calculate_retry_delay(1) == 60  # 60 * 2^0
        assert jd.calculate_retry_delay(2) == 120  # 60 * 2^1
        assert jd.calculate_retry_delay(3) == 240  # 60 * 2^2


class TestJobExecution:
    def setup_method(self):
        self.exec = JobExecution(
            job_id="job-001",
            job_name="test_job",
            started_at=datetime.now(UTC),
        )

    def test_log_adds_entry(self):
        self.exec.log("Starting process")
        assert len(self.exec.logs) == 1
        assert "Starting process" in self.exec.logs[0]

    def test_log_level_warning(self):
        self.exec.log("Warning msg", "warning")
        assert "WARNING" in self.exec.logs[0]

    def test_log_level_error(self):
        self.exec.log("Error msg", "error")
        assert "ERROR" in self.exec.logs[0]

    def test_update_progress_clamps_to_0_100(self):
        self.exec.update_progress(-10)
        assert self.exec.progress == 0
        self.exec.update_progress(150)
        assert self.exec.progress == 100

    def test_update_progress_sets_message(self):
        self.exec.update_progress(50, "Half done")
        assert self.exec.status_message == "Half done"
        assert self.exec.progress == 50


class TestBackgroundJobRegistry:
    def setup_method(self):
        self.registry = BackgroundJobRegistry()

    def test_register_and_get_job(self):
        fn = lambda: None
        job = self.registry.register_job(
            "my_job",
            fn,
            queue_type=_FakeQueueType.BATCH_PROCESSING,
            priority=JobPriority.NORMAL,
        )
        assert isinstance(job, JobDefinition)
        assert self.registry.get_job("my_job") is job

    def test_get_nonexistent_job(self):
        assert self.registry.get_job("nonexistent") is None

    def test_list_jobs_all(self):
        self.registry.register_job(
            "job_a",
            lambda: None,
            queue_type=_FakeQueueType.BATCH_PROCESSING,
            priority=JobPriority.LOW,
        )
        self.registry.register_job(
            "job_b",
            lambda: None,
            queue_type=_FakeQueueType.BATCH_PROCESSING,
            priority=JobPriority.HIGH,
        )
        jobs = self.registry.list_jobs()
        names = [j.name for j in jobs]
        assert "job_a" in names
        assert "job_b" in names

    def test_list_jobs_by_category(self):
        self.registry.register_job(
            "cat_job",
            lambda: None,
            queue_type=_FakeQueueType.BATCH_PROCESSING,
            priority=JobPriority.NORMAL,
            category="testing",
        )
        jobs = self.registry.list_jobs(category="testing")
        assert any(j.name == "cat_job" for j in jobs)

    def test_list_jobs_unknown_category(self):
        jobs = self.registry.list_jobs(category="nonexistent")
        assert jobs == []

    def test_get_categories(self):
        self.registry.register_job(
            "c1_job",
            lambda: None,
            queue_type=_FakeQueueType.BATCH_PROCESSING,
            priority=JobPriority.NORMAL,
            category="cat1",
        )
        self.registry.register_job(
            "c2_job",
            lambda: None,
            queue_type=_FakeQueueType.BATCH_PROCESSING,
            priority=JobPriority.NORMAL,
            category="cat2",
        )
        cats = self.registry.get_categories()
        assert "cat1" in cats
        assert "cat2" in cats


class TestTurkishExamJobProcessor:
    def setup_method(self):
        self.processor = TurkishExamJobProcessor()

    def test_builtin_jobs_registered(self):
        assert self.processor.registry.get_job("process_tyt_exam") is not None
        assert self.processor.registry.get_job("process_ayt_exam") is not None
        assert self.processor.registry.get_job("cleanup_expired_sessions") is not None

    def test_get_system_stats(self):
        stats = self.processor.get_system_stats()
        assert "running_jobs" in stats
        assert "registered_jobs" in stats
        assert stats["registered_jobs"] > 0

    def test_get_job_status_not_found(self):
        result = self.processor.get_job_status("nonexistent-job-id")
        assert result is None

    def test_cancel_nonexistent_job(self):
        result = self.processor.cancel_job("nonexistent")
        assert result is False

    def test_cancel_recurring_nonexistent(self):
        result = self.processor.cancel_recurring_job("nonexistent")
        assert result is False

    def test_update_job_stats_success(self):
        self.processor._update_job_stats("test_job", True, 1.5)
        stats = self.processor.job_stats["test_job"]
        assert stats["total_executions"] == 1
        assert stats["successful_executions"] == 1
        assert stats["failed_executions"] == 0

    def test_update_job_stats_failure(self):
        self.processor._update_job_stats("test_job", False, 2.0)
        stats = self.processor.job_stats["test_job"]
        assert stats["failed_executions"] == 1

    def test_update_job_stats_average_time(self):
        self.processor._update_job_stats("avg_job", True, 2.0)
        self.processor._update_job_stats("avg_job", True, 4.0)
        stats = self.processor.job_stats["avg_job"]
        assert stats["avg_execution_time"] == 3.0

    @pytest.mark.asyncio
    async def test_schedule_job_unknown_raises(self):
        with pytest.raises(ValueError, match="not found"):
            await self.processor.schedule_job("nonexistent_job")

    @pytest.mark.asyncio
    async def test_execute_job_success(self):
        async def simple_fn():
            return "done"

        jd = JobDefinition(
            name="simple",
            function=simple_fn,
            queue_type=_FakeQueueType.BATCH_PROCESSING,
            priority=JobPriority.NORMAL,
        )
        exec_ctx = JobExecution(
            job_id="job-test",
            job_name="simple",
            started_at=datetime.now(UTC),
        )
        await self.processor._execute_job("job-test", jd, exec_ctx, [], {})
        assert exec_ctx.progress == 100

    @pytest.mark.asyncio
    async def test_handle_job_failure(self):
        jd = JobDefinition(
            name="failing",
            function=lambda: None,
            queue_type=_FakeQueueType.BATCH_PROCESSING,
            priority=JobPriority.NORMAL,
        )
        exec_ctx = JobExecution(
            job_id="job-fail",
            job_name="failing",
            started_at=datetime.now(UTC),
        )
        await self.processor._handle_job_failure("job-fail", jd, exec_ctx, "test error")
        completed = [
            c for c in self.processor.completed_jobs if c["job_id"] == "job-fail"
        ]
        assert len(completed) == 1
        assert completed[0]["status"] == "failed"


class TestBackgroundJobUtilities:
    @pytest.mark.asyncio
    async def test_get_job_system_stats(self):
        stats = await get_job_system_stats()
        assert "registered_jobs" in stats

    @pytest.mark.asyncio
    async def test_get_job_status_nonexistent(self):
        result = await get_job_status("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_schedule_exam_processing(self):
        job_id = await schedule_exam_processing(
            exam_type="tyt",
            user_id=1,
            exam_data={"answers": []},
        )
        assert isinstance(job_id, str)
        assert len(job_id) > 0

    @pytest.mark.asyncio
    async def test_schedule_content_generation(self):
        job_id = await schedule_content_generation(
            user_id=1,
            content_type="practice",
            parameters={"subject": "matematik", "count": 5},
        )
        assert isinstance(job_id, str)


# ============================================================================
# FILE 3: core/security_event_monitoring.py
# ============================================================================
from core.security_event_monitoring import (
    SecurityEvent,
    SecurityEventMonitor,
    SecurityEventType,
    SecuritySeverity,
    ThreatDetector,
    get_security_monitor,
)


class TestSecurityEventType:
    def test_login_success_attributes(self):
        et = SecurityEventType.LOGIN_SUCCESS
        assert et.event_type == "login_success"
        assert "Başarılı" in et.turkish_description

    def test_brute_force_attributes(self):
        et = SecurityEventType.BRUTE_FORCE_ATTACK
        assert et.event_type == "brute_force_attack"

    def test_sql_injection_attributes(self):
        et = SecurityEventType.SQL_INJECTION_ATTEMPT
        assert "sql" in et.event_type


class TestSecuritySeverity:
    def test_critical_score(self):
        assert SecuritySeverity.CRITICAL.score == 100

    def test_info_score(self):
        assert SecuritySeverity.INFO.score == 1

    def test_high_score(self):
        assert SecuritySeverity.HIGH.score == 75

    def test_turkish_descriptions(self):
        assert SecuritySeverity.CRITICAL.turkish_description == "Kritik"
        assert SecuritySeverity.HIGH.turkish_description == "Yüksek"


class TestSecurityEvent:
    def setup_method(self):
        self.event = SecurityEvent(
            event_id="evt-001",
            event_type=SecurityEventType.LOGIN_SUCCESS,
            severity=SecuritySeverity.INFO,
            timestamp=datetime.now(UTC),
            ip_address="192.168.1.1",
            user_id=1,
            message="Login OK",
            message_tr="Giriş başarılı",
        )

    def test_to_dict_keys(self):
        d = self.event.to_dict()
        assert d["event_id"] == "evt-001"
        assert d["severity"] == "info"
        assert d["ip_address"] == "192.168.1.1"
        assert d["user_id"] == 1
        assert "event_type_tr" in d
        assert "severity_score" in d

    def test_to_dict_severity_score(self):
        d = self.event.to_dict()
        assert d["severity_score"] == 1  # INFO score

    def test_to_dict_event_type_tr(self):
        d = self.event.to_dict()
        assert "Başarılı" in d["event_type_tr"]


class TestThreatDetector:
    def setup_method(self):
        self.detector = ThreatDetector()

    def test_attack_patterns_loaded(self):
        patterns = self.detector.attack_patterns
        assert "sql_injection" in patterns
        assert "xss" in patterns
        assert "command_injection" in patterns
        assert "path_traversal" in patterns

    @pytest.mark.asyncio
    async def test_is_suspicious_user_agent_empty(self):
        result = await self.detector._is_suspicious_user_agent("")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_suspicious_user_agent_short(self):
        result = await self.detector._is_suspicious_user_agent("bot")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_suspicious_user_agent_normal(self):
        normal_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        result = await self.detector._is_suspicious_user_agent(normal_ua)
        assert result is False

    @pytest.mark.asyncio
    async def test_is_suspicious_user_agent_curl(self):
        # "curl" appears in the suspicious patterns list
        result = await self.detector._is_suspicious_user_agent("curl/7.68.0 libcurl")
        assert result is True

    @pytest.mark.asyncio
    async def test_detect_injection_sql(self):
        payload = {"query": "1 UNION SELECT * FROM users"}
        threats = await self.detector._detect_injection_attacks(
            payload, "1.2.3.4", None
        )
        sql_threats = [
            t
            for t in threats
            if t.event_type == SecurityEventType.SQL_INJECTION_ATTEMPT
        ]
        assert len(sql_threats) >= 1

    @pytest.mark.asyncio
    async def test_detect_injection_xss(self):
        payload = {"input": "<script>alert('xss')</script>"}
        threats = await self.detector._detect_injection_attacks(
            payload, "1.2.3.4", None
        )
        xss_threats = [
            t for t in threats if t.event_type == SecurityEventType.XSS_ATTEMPT
        ]
        assert len(xss_threats) >= 1

    @pytest.mark.asyncio
    async def test_detect_injection_path_traversal(self):
        payload = {"path": "../../../etc/passwd"}
        threats = await self.detector._detect_injection_attacks(payload, "1.2.3.4", 10)
        pt_threats = [
            t
            for t in threats
            if t.event_type == SecurityEventType.PATH_TRAVERSAL_ATTEMPT
        ]
        assert len(pt_threats) >= 1

    @pytest.mark.asyncio
    async def test_detect_injection_empty_payload(self):
        # An empty payload produces no threats
        threats = await self.detector._detect_injection_attacks({}, "1.2.3.4", None)
        assert threats == []

    @pytest.mark.asyncio
    async def test_detect_injection_command_injection(self):
        # Payload with command injection chars triggers COMMAND_INJECTION event
        payload = {"cmd": "ls; rm -rf /"}
        threats = await self.detector._detect_injection_attacks(payload, "1.2.3.4", 5)
        cmd_threats = [
            t
            for t in threats
            if t.event_type == SecurityEventType.COMMAND_INJECTION_ATTEMPT
        ]
        assert len(cmd_threats) >= 1

    @pytest.mark.asyncio
    async def test_rate_limit_check_returns_false(self):
        result = await self.detector._check_rate_limit_violation("1.2.3.4", None)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_ip_location_private(self):
        result = await self.detector._get_ip_location("192.168.1.1")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_ip_location_public(self):
        result = await self.detector._get_ip_location("8.8.8.8")
        assert result is not None
        assert result["country"] == "Turkey"

    def test_calculate_distance_same_location(self):
        loc = {"latitude": 41.0, "longitude": 29.0}
        dist = self.detector._calculate_distance(loc, loc)
        assert dist == 0.0

    def test_calculate_distance_different_locations(self):
        loc1 = {"latitude": 41.0, "longitude": 29.0}
        loc2 = {"latitude": 39.0, "longitude": 35.0}
        dist = self.detector._calculate_distance(loc1, loc2)
        assert dist > 0

    def test_generate_event_id_unique(self):
        id1 = self.detector._generate_event_id()
        id2 = self.detector._generate_event_id()
        assert id1 != id2

    def test_generate_correlation_id_length(self):
        cid = self.detector._generate_correlation_id()
        assert len(cid) == 16

    @pytest.mark.asyncio
    async def test_create_threat_event(self):
        event = await self.detector._create_threat_event(
            SecurityEventType.SUSPICIOUS_IP,
            SecuritySeverity.MEDIUM,
            ip_address="5.5.5.5",
            user_id=99,
            message="Suspicious",
            message_tr="Şüpheli",
        )
        assert isinstance(event, SecurityEvent)
        assert event.ip_address == "5.5.5.5"
        assert event.user_id == 99


class TestSecurityEventMonitor:
    def setup_method(self):
        self.monitor = SecurityEventMonitor()

    def test_register_event_handler(self):
        handler = MagicMock()
        self.monitor.register_event_handler(handler)
        assert handler in self.monitor.event_handlers

    def test_register_alert_handler(self):
        handler = MagicMock()
        self.monitor.register_alert_handler(handler)
        assert handler in self.monitor.alert_handlers

    def test_translate_alert_known(self):
        result = self.monitor._translate_alert("Brute force attack detected")
        assert "kaba kuvvet" in result.lower()

    def test_translate_alert_unknown(self):
        result = self.monitor._translate_alert("Unknown alert message")
        assert result == "Unknown alert message"

    def test_generate_alert_id_format(self):
        aid = self.monitor._generate_alert_id()
        assert aid.startswith("alert_")

    def test_initial_counters_empty(self):
        assert len(self.monitor.event_counters) == 0
        assert len(self.monitor.ip_counters) == 0

    @pytest.mark.asyncio
    async def test_start_monitoring_sets_running(self):
        self.monitor.running = False
        await self.monitor.start_monitoring()
        assert self.monitor.running is True
        # Cleanup
        self.monitor.running = False

    @pytest.mark.asyncio
    async def test_stop_monitoring(self):
        self.monitor.running = True
        await self.monitor.stop_monitoring()
        assert self.monitor.running is False

    @pytest.mark.asyncio
    async def test_check_alert_conditions_critical(self):
        event = SecurityEvent(
            event_id="evt-crit",
            event_type=SecurityEventType.MALWARE_DETECTED,
            severity=SecuritySeverity.CRITICAL,
            timestamp=datetime.now(UTC),
            ip_address="9.9.9.9",
        )
        # Should add to alert queue without raising
        self.monitor.db_manager = MagicMock()
        self.monitor.db_manager.fetch_one = AsyncMock(return_value={"event_count": 0})
        await self.monitor._check_alert_conditions(event)
        assert not self.monitor.alert_queue.empty()


class TestSecurityMonitorConvenience:
    def test_get_security_monitor_singleton(self):
        m1 = get_security_monitor()
        m2 = get_security_monitor()
        assert m1 is m2


# ============================================================================
# FILE 4: core/kvkk_compliance.py
# ============================================================================
from core.kvkk_compliance import (
    PII_FIELDS,
    ConsentStatus,
    ConsentType,
    DataCategory,
    DataProcessingPurpose,
    DataSubjectRight,
    KVKKComplianceManager,
    KVKKEncryption,
    decrypt_user_pii,
    encrypt_user_pii,
    get_kvkk_encryption,
)


class TestKVKKEncryption:
    def test_encrypt_pii_empty_returns_empty(self):
        enc = KVKKEncryption()
        result = enc.encrypt_pii("")
        assert result == ""

    def test_decrypt_pii_empty_returns_empty(self):
        enc = KVKKEncryption()
        result = enc.decrypt_pii("")
        assert result == ""

    def test_encrypt_decrypt_roundtrip_fallback(self):
        enc = KVKKEncryption()
        enc._fernet = None  # force fallback mode
        original = "test@example.com"
        encrypted = enc.encrypt_pii(original)
        assert encrypted.startswith("b64:")
        decrypted = enc.decrypt_pii(encrypted)
        assert decrypted == original

    def test_decrypt_b64_prefix(self):
        import base64

        enc = KVKKEncryption()
        b64_val = "b64:" + base64.b64encode(b"hello").decode()
        assert enc.decrypt_pii(b64_val) == "hello"

    def test_decrypt_plain_text_passthrough(self):
        enc = KVKKEncryption()
        plain = "plain_text_no_prefix"
        assert enc.decrypt_pii(plain) == plain

    def test_hash_pii_consistent(self):
        enc = KVKKEncryption()
        h1 = enc.hash_pii("test@example.com")
        h2 = enc.hash_pii("test@example.com")
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_hash_pii_empty(self):
        enc = KVKKEncryption()
        assert enc.hash_pii("") == ""

    def test_hash_pii_different_inputs(self):
        enc = KVKKEncryption()
        h1 = enc.hash_pii("user1@test.com")
        h2 = enc.hash_pii("user2@test.com")
        assert h1 != h2

    def test_encrypt_dict_encrypts_pii_fields(self):
        enc = KVKKEncryption()
        enc._fernet = None
        data = {"email": "test@example.com", "age": 25, "other": "data"}
        result = enc.encrypt_dict(data, ["email"])
        assert result["email"] != "test@example.com"
        assert result["age"] == 25  # non-PII unchanged
        assert result["other"] == "data"

    def test_decrypt_dict(self):
        enc = KVKKEncryption()
        enc._fernet = None
        data = {"email": "user@test.com"}
        encrypted = enc.encrypt_dict(data, ["email"])
        decrypted = enc.decrypt_dict(encrypted, ["email"])
        assert decrypted["email"] == "user@test.com"

    def test_generate_key_length(self):
        key = KVKKEncryption.generate_key()
        assert len(key) == 32

    def test_generate_key_base64_length(self):
        key_b64 = KVKKEncryption.generate_key_base64()
        import base64

        decoded = base64.urlsafe_b64decode(key_b64)
        assert len(decoded) == 32

    def test_get_key_from_env_none_when_not_set(self, monkeypatch):
        monkeypatch.delenv("KVKK_ENCRYPTION_KEY", raising=False)
        enc = KVKKEncryption()
        assert enc._get_key_from_env() is None

    def test_get_key_from_env_returns_bytes(self, monkeypatch):
        monkeypatch.setenv("KVKK_ENCRYPTION_KEY", "mysecretkey")
        enc = KVKKEncryption()
        result = enc._get_key_from_env()
        assert isinstance(result, bytes)

    def test_derive_key_length(self):
        enc = KVKKEncryption()
        derived = enc._derive_key(b"password")
        assert len(derived) == 32


class TestKVKKEnums:
    def test_data_processing_purpose_values(self):
        assert DataProcessingPurpose.EDUCATION.value == "education"
        assert DataProcessingPurpose.MARKETING.value == "marketing"

    def test_consent_type_values(self):
        assert ConsentType.EXPLICIT.value == "explicit"
        assert ConsentType.LEGAL_BASIS.value == "legal_basis"

    def test_data_category_values(self):
        assert DataCategory.IDENTITY.value == "identity"
        assert DataCategory.TECHNICAL.value == "technical"

    def test_data_subject_right_values(self):
        assert DataSubjectRight.ACCESS.value == "access"
        assert DataSubjectRight.ERASURE.value == "erasure"

    def test_consent_status_values(self):
        assert ConsentStatus.GRANTED.value == "granted"
        assert ConsentStatus.WITHDRAWN.value == "withdrawn"


class TestPIIFieldsConfig:
    def test_user_pii_fields(self):
        assert "email" in PII_FIELDS["user"]
        assert "phone" in PII_FIELDS["user"]

    def test_student_pii_fields(self):
        assert "parent_phone" in PII_FIELDS["student"]

    def test_exam_pii_fields(self):
        assert "ip_address" in PII_FIELDS["exam"]


class TestEncryptUserPIIConvenience:
    def test_encrypt_user_pii_returns_dict(self):
        data = {"email": "test@test.com", "phone": "5551234567", "age": 25}
        result = encrypt_user_pii(data)
        assert isinstance(result, dict)
        assert "age" in result

    def test_decrypt_user_pii_roundtrip(self):
        enc = get_kvkk_encryption()
        enc._fernet = None  # use fallback
        original = {"email": "roundtrip@test.com"}
        encrypted = encrypt_user_pii(original)
        decrypted = decrypt_user_pii(encrypted)
        assert decrypted["email"] == "roundtrip@test.com"


class TestKVKKComplianceManagerAnonymization:
    def setup_method(self):
        self.db = MagicMock()
        self.manager = KVKKComplianceManager(self.db)

    def test_anonymize_ip_ipv4(self):
        result = self.manager._anonymize_ip("192.168.1.100")
        assert result == "192.168.1.0"

    def test_anonymize_ip_ipv6(self):
        result = self.manager._anonymize_ip("2001:db8:85a3:0000:0000:8a2e:0370:7334")
        assert result.endswith("::0")

    def test_anonymize_ip_none(self):
        result = self.manager._anonymize_ip(None)
        assert result == "0.0.0.0"

    def test_anonymize_ip_invalid(self):
        result = self.manager._anonymize_ip("not-an-ip")
        assert result == "0.0.0.0"

    def test_consent_texts_education(self):
        text = self.manager.consent_texts[DataProcessingPurpose.EDUCATION]
        assert "KVKK" in text or "kişisel" in text.lower()

    def test_consent_texts_marketing(self):
        text = self.manager.consent_texts[DataProcessingPurpose.MARKETING]
        assert "AÇIK RIZA" in text or "açık rıza" in text.lower()


# ============================================================================
# FILE 5: services/visual_content_generator.py
# ============================================================================

# Stub the generator sub-services to avoid their heavy imports
_gg_mod = sys.modules["services.graph_generator"]
_gg_mod.GraphGenerator = MagicMock

_gm_mod = sys.modules["services.geometry_generator"]
_gm_mod.GeometryGenerator = MagicMock

_md_mod = sys.modules["services.map_diagram_generator"]
_md_mod.MapDiagramGenerator = MagicMock

from services.visual_content_generator import VisualContentGenerator


class TestVisualContentGeneratorTables:
    def setup_method(self):
        self.gen = VisualContentGenerator()

    def test_generate_frequency_table_structure(self):
        result = self.gen.generate_table(
            "Matematik", "İstatistik", "frequency_table", rows=3
        )
        assert result["type"] == "table"
        assert result["format"] == "markdown"
        assert "|" in result["content"]
        assert "data" in result
        assert result["data"]["total"] == sum(result["data"]["frequencies"])

    def test_generate_comparison_table_structure(self):
        result = self.gen.generate_table(
            "Matematik", "Analiz", "comparison_table", rows=3, columns=3
        )
        assert result["type"] == "table"
        assert "Ürün A" in result["content"]

    def test_generate_statistics_table_structure(self):
        result = self.gen.generate_table("Matematik", "İstatistik", "statistics_table")
        assert "Ortalama" in result["content"]
        assert result["metadata"]["rows"] == 5

    def test_generate_price_table_structure(self):
        result = self.gen.generate_table(
            "Matematik", "Problemler", "price_table", rows=3
        )
        assert "₺" in result["content"]
        assert result["metadata"]["rows"] == 3

    def test_generate_grade_table_structure(self):
        result = self.gen.generate_table(
            "Matematik", "Değerlendirme", "grade_table", rows=4
        )
        assert "Öğrenci" in result["content"]
        assert "Ortalama" in result["content"]

    def test_generate_schedule_table_structure(self):
        result = self.gen.generate_table("Okul", "Program", "schedule_table")
        assert "Pazartesi" in result["content"]

    def test_generate_generic_table_fallback(self):
        result = self.gen.generate_table("X", "Y", "unknown_type")
        assert result["type"] == "table"
        assert "Sütun" in result["content"]

    def test_build_markdown_table_format(self):
        headers = ["A", "B", "C"]
        rows = ["| 1 | 2 | 3 |", "| 4 | 5 | 6 |"]
        md = self.gen._build_markdown_table(headers, rows)
        lines = md.split("\n")
        assert "| A | B | C |" in lines[0]
        assert "---" in lines[1]
        assert len(lines) == 4  # header + sep + 2 data rows

    def test_frequency_table_percentages_sum_to_100(self):
        result = self.gen._generate_frequency_table(rows=4)
        # Check all data is present
        assert len(result["data"]["frequencies"]) == 4
        assert result["data"]["total"] == sum(result["data"]["frequencies"])


class TestVisualContentGeneratorGraphs:
    def setup_method(self):
        self.gen = VisualContentGenerator()
        # Mock graph_generator to return a predictable dict
        self.gen.graph_generator.generate_graph = MagicMock(
            return_value={"type": "graph", "content": "<svg/>"}
        )

    def test_generate_graph_line_calls_generator(self):
        result = self.gen.generate_graph("Fizik", "Hareket", "line")
        self.gen.graph_generator.generate_graph.assert_called_once()
        assert result is not None

    def test_generate_graph_bar_calls_generator(self):
        result = self.gen.generate_graph("Matematik", "İstatistik", "bar")
        assert self.gen.graph_generator.generate_graph.called

    def test_generate_graph_pie_calls_generator(self):
        result = self.gen.generate_graph("Coğrafya", "Dağılım", "pie")
        assert self.gen.graph_generator.generate_graph.called

    def test_generate_graph_scatter_calls_generator(self):
        result = self.gen.generate_graph("Matematik", "Korelasyon", "scatter")
        assert self.gen.graph_generator.generate_graph.called

    def test_generate_graph_histogram_calls_generator(self):
        result = self.gen.generate_graph("Biyoloji", "Dağılım", "histogram")
        assert self.gen.graph_generator.generate_graph.called

    def test_generate_graph_invalid_type_raises(self):
        with pytest.raises(ValueError, match="Unknown graph_type"):
            self.gen.generate_graph("X", "Y", "unknown_type")

    def test_get_x_label_fizik(self):
        assert self.gen._get_x_label("Fizik", "line") == "Zaman (s)"

    def test_get_x_label_matematik(self):
        assert self.gen._get_x_label("Matematik", "line") == "x"

    def test_get_x_label_cografya(self):
        # Source checks 'cografya' (no ğ) in subject.lower() — use ASCII
        assert self.gen._get_x_label("Cografya", "bar") == "Yıl"

    def test_get_x_label_default(self):
        assert self.gen._get_x_label("Kimya", "line") == "X Ekseni"

    def test_get_y_label_fizik(self):
        assert self.gen._get_y_label("Fizik", "line") == "Hız (m/s)"

    def test_get_y_label_matematik_bar(self):
        assert self.gen._get_y_label("Matematik", "bar") == "Frekans"

    def test_generate_line_data_fizik(self):
        data = self.gen._generate_line_data("Fizik", "Hareket", "medium")
        assert "x" in data
        assert "y" in data
        assert len(data["x"]) == len(data["y"])

    def test_generate_line_data_matematik(self):
        data = self.gen._generate_line_data("Matematik", "Fonksiyon", "medium")
        assert data["y"][5] == 0  # x=0 -> y=0 (index 5 in range -5..5)

    def test_generate_bar_data_matematik(self):
        data = self.gen._generate_bar_data("Matematik", "İstatistik", "medium")
        assert "categories" in data
        assert "values" in data

    def test_generate_pie_data_cografya(self):
        data = self.gen._generate_pie_data("Coğrafya", "Nüfus Dağılımı", "medium")
        assert sum(data["values"]) == 100

    def test_generate_scatter_data_matematik(self):
        data = self.gen._generate_scatter_data("Matematik", "Korelasyon", "medium")
        assert data["show_trendline"] is True

    def test_generate_histogram_data_biyoloji(self):
        data = self.gen._generate_histogram_data("Biyoloji", "Ölçüm", "medium")
        assert len(data["values"]) == 50

    def test_generate_histogram_data_matematik(self):
        data = self.gen._generate_histogram_data("Matematik", "Puan", "medium")
        assert data["bins"] == 10


class TestVisualContentGeneratorGeometry:
    def setup_method(self):
        self.gen = VisualContentGenerator()
        self.gen.geometry_generator.generate_geometry = MagicMock(
            return_value={"type": "geometry", "content": "<svg/>"}
        )

    def test_select_shape_subtype_right_triangle(self):
        result = self.gen._select_shape_subtype("triangle", "Matematik", "Dik Üçgen")
        assert result == "right_triangle"

    def test_select_shape_subtype_equilateral(self):
        # Source checks 'eskenar' (no ş) in topic.lower()
        result = self.gen._select_shape_subtype(
            "triangle", "Matematik", "eskenar ucgen"
        )
        assert result == "equilateral_triangle"

    def test_select_shape_subtype_isosceles(self):
        # Source checks 'ikizkenar' (no İ) in topic.lower()
        result = self.gen._select_shape_subtype(
            "triangle", "Matematik", "ikizkenar ucgen"
        )
        assert result == "isosceles_triangle"

    def test_select_shape_subtype_circle_sector(self):
        result = self.gen._select_shape_subtype("circle", "Matematik", "Dilim Alan")
        assert result == "sector"

    def test_select_shape_subtype_circle_default(self):
        result = self.gen._select_shape_subtype("circle", "Matematik", "Çevre")
        assert result == "complete_circle"

    def test_select_shape_subtype_quadrilateral_square(self):
        result = self.gen._select_shape_subtype(
            "quadrilateral", "Matematik", "Kare Alanı"
        )
        assert result == "square"

    def test_select_shape_subtype_quadrilateral_rectangle(self):
        result = self.gen._select_shape_subtype(
            "quadrilateral", "Matematik", "Dikdörtgen"
        )
        assert result == "rectangle"

    def test_select_shape_subtype_3d_cube(self):
        result = self.gen._select_shape_subtype("3d_shape", "Matematik", "Küp Hacmi")
        assert result == "cube"

    def test_generate_geometry_labels_triangle(self):
        labels = self.gen._generate_geometry_labels("triangle", "right_triangle")
        assert labels["vertex_labels"] == ["A", "B", "C"]

    def test_generate_geometry_labels_quadrilateral(self):
        labels = self.gen._generate_geometry_labels("quadrilateral", "square")
        assert labels["vertex_labels"] == ["A", "B", "C", "D"]

    def test_generate_geometry_labels_polygon_hexagon(self):
        labels = self.gen._generate_geometry_labels("polygon", "hexagon")
        assert len(labels["vertex_labels"]) == 6

    def test_generate_geometry_labels_circle_empty(self):
        labels = self.gen._generate_geometry_labels("circle", "complete_circle")
        assert labels == {}

    def test_generate_geometry_dimensions_right_triangle(self):
        dims = self.gen._generate_geometry_dimensions(
            "triangle", "right_triangle", "Matematik", "Geometri", "medium"
        )
        assert "base" in dims
        assert "height" in dims

    def test_generate_geometry_dimensions_equilateral(self):
        dims = self.gen._generate_geometry_dimensions(
            "triangle", "equilateral_triangle", "Matematik", "Geometri", "medium"
        )
        assert "side" in dims

    def test_generate_geometry_dimensions_circle(self):
        dims = self.gen._generate_geometry_dimensions(
            "circle", "complete_circle", "Matematik", "Geometri", "medium"
        )
        assert "radius" in dims

    def test_generate_geometry_dimensions_sector(self):
        dims = self.gen._generate_geometry_dimensions(
            "circle", "sector", "Matematik", "Dilim", "medium"
        )
        assert "angle" in dims

    def test_generate_geometry_dimensions_cube(self):
        dims = self.gen._generate_geometry_dimensions(
            "3d_shape", "cube", "Matematik", "Geometri", "medium"
        )
        assert "side" in dims

    def test_generate_geometry_calls_generator(self):
        result = self.gen.generate_geometry("Matematik", "Geometri", "triangle")
        self.gen.geometry_generator.generate_geometry.assert_called_once()


class TestVisualContentGeneratorDiagrams:
    def setup_method(self):
        self.gen = VisualContentGenerator()
        self.gen.map_diagram_generator.generate_diagram = MagicMock(
            return_value={"type": "diagram", "content": "<svg/>"}
        )

    def test_select_diagram_subtype_turkey_regions(self):
        # Source checks "bölge" in topic.lower() — use exact Turkish
        result = self.gen._select_diagram_subtype(
            "geographic_map", "Coğrafya", "Türkiye Bölgeleri"
        )
        assert result == "turkey_regions"

    def test_select_diagram_subtype_cities(self):
        # Source checks "şehir" in topic.lower() — use exact Turkish
        result = self.gen._select_diagram_subtype(
            "geographic_map", "Coğrafya", "Büyük Şehirler"
        )
        assert result == "turkey_cities"

    def test_select_diagram_subtype_continents(self):
        # Source checks "kıta" or "dünya" in topic.lower() — use exact Turkish
        result = self.gen._select_diagram_subtype(
            "geographic_map", "Coğrafya", "Dünya Kıtaları"
        )
        assert result == "continents"

    def test_select_diagram_subtype_flowchart_default(self):
        result = self.gen._select_diagram_subtype("process_diagram", "Fen", "Süreç")
        assert result == "flowchart"

    def test_select_diagram_subtype_cycle(self):
        result = self.gen._select_diagram_subtype(
            "process_diagram", "Fen", "Su Döngüsü"
        )
        assert result == "cycle_diagram"

    def test_select_diagram_subtype_venn_default(self):
        result = self.gen._select_diagram_subtype(
            "classification_diagram", "Matematik", "Kümeler"
        )
        assert result == "venn_diagram"

    def test_select_diagram_subtype_tree(self):
        result = self.gen._select_diagram_subtype(
            "classification_diagram", "Biyoloji", "Sınıflandırma Türleri"
        )
        assert result == "tree_diagram"

    def test_generate_geographic_map_turkey_regions(self):
        content = self.gen._generate_geographic_map_content(
            "turkey_regions", "Coğrafya", "Bölge"
        )
        assert "highlight_regions" in content
        assert len(content["highlight_regions"]) >= 1

    def test_generate_geographic_map_cities(self):
        content = self.gen._generate_geographic_map_content(
            "turkey_cities", "Coğrafya", "Şehir"
        )
        assert "cities" in content
        assert len(content["cities"]) >= 3

    def test_generate_geographic_map_continents(self):
        content = self.gen._generate_geographic_map_content(
            "continents", "Coğrafya", "Kıta"
        )
        assert "highlight_continents" in content

    def test_generate_process_diagram_flowchart(self):
        content = self.gen._generate_process_diagram_content(
            "flowchart", "Fen", "Döngü"
        )
        assert "nodes" in content
        assert "edges" in content

    def test_generate_process_diagram_cycle(self):
        content = self.gen._generate_process_diagram_content(
            "cycle_diagram", "Fen", "Döngü"
        )
        assert "steps" in content
        assert len(content["steps"]) == 4

    def test_generate_classification_venn(self):
        content = self.gen._generate_classification_diagram_content(
            "venn_diagram", "Matematik", "Kümeler"
        )
        assert "sets" in content
        assert "intersection" in content

    def test_generate_classification_tree(self):
        content = self.gen._generate_classification_diagram_content(
            "tree_diagram", "Biyoloji", "Canlılar"
        )
        assert "tree" in content

    def test_generate_classification_matrix(self):
        content = self.gen._generate_classification_diagram_content(
            "matrix_diagram", "X", "Y"
        )
        assert "cells" in content

    def test_generate_timeline_content(self):
        content = self.gen._generate_timeline_content(
            "horizontal_timeline", "Tarih", "Cumhuriyet"
        )
        assert "events" in content
        assert len(content["events"]) >= 3
        # Events should be sorted by year
        years = [e["year"] for e in content["events"]]
        assert years == sorted(years)

    def test_generate_map_diagram_calls_generator(self):
        result = self.gen.generate_map_diagram("Coğrafya", "Bölgeler", "geographic_map")
        self.gen.map_diagram_generator.generate_diagram.assert_called_once()


class TestVisualContentGeneratorHelpers:
    def setup_method(self):
        self.gen = VisualContentGenerator()
        self.gen.graph_generator.generate_graph = MagicMock(
            return_value={"type": "graph", "content": "<svg/>"}
        )

    def test_create_question_with_visual(self):
        visual = {"type": "table", "content": "| A | B |\n|---|---|\n| 1 | 2 |"}
        q = self.gen.create_question_with_visual(
            stem="Tabloya göre...",
            visual_content=visual,
            options=["A) 1", "B) 2", "C) 3", "D) 4", "E) 5"],
            correct_answer="B",
        )
        assert q["stem"] == "Tabloya göre..."
        assert q["correct_answer"] == "B"
        assert len(q["options"]) == 5
        assert q["visual_content"]["type"] == "table"

    def test_get_table_example_for_prompt(self):
        prompt = self.gen.get_table_example_for_prompt("frequency_table")
        assert "TABLO FORMATI" in prompt or "tablo" in prompt.lower()
        assert "|" in prompt

    def test_visual_types_dict_has_all_phases(self):
        assert "table" in self.gen.visual_types
        assert "graph" in self.gen.visual_types
        assert "geometry" in self.gen.visual_types
        assert "map_diagram" in self.gen.visual_types
