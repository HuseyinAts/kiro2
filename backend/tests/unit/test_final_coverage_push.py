"""
Final coverage push tests.
Covers 8 modules:
  1. core/service_registry.py
  2. core/berturk_service.py
  3. core/unified/session_system.py
  4. services/llm/ensemble_manager.py
  5. core/query_builder.py
  6. core/realtime_notification_system.py
  7. core/background_job_processor.py
  8. core/kvkk_compliance.py
"""

import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Clean stale MagicMock stubs that may have been injected by other test files
# ---------------------------------------------------------------------------
_STUBS_TO_CLEAN = [
    "core.service_registry",
    "core.berturk_service",
    "core.unified.session_system",
    "services.llm.ensemble_manager",
    "core.query_builder",
    "core.realtime_notification_system",
    "core.background_job_processor",
    "core.kvkk_compliance",
]
for _mod in _STUBS_TO_CLEAN:
    _existing = sys.modules.get(_mod)
    if _existing is not None and isinstance(_existing, MagicMock):
        del sys.modules[_mod]


# ---------------------------------------------------------------------------
# Stub heavy / unavailable dependencies BEFORE importing the modules under
# test.  We use setdefault so we never overwrite a real module that was
# already imported by another test file.
# ---------------------------------------------------------------------------


def _stub(name: str, **attrs) -> MagicMock:
    """Create and register a stub module only if not already present."""
    if name not in sys.modules or isinstance(sys.modules[name], MagicMock):
        m = MagicMock(name=name)
        for k, v in attrs.items():
            setattr(m, k, v)
        sys.modules[name] = m
    return sys.modules[name]


# --- torch / transformers (berturk) ---
_torch = _stub("torch")
_torch.cuda.is_available.return_value = False
_torch.no_grad.return_value.__enter__ = lambda s: None
_torch.no_grad.return_value.__exit__ = lambda s, *a: None
_stub("transformers")
_stub("transformers.AutoModel")
_stub("transformers.AutoModelForSequenceClassification")
_stub("transformers.AutoTokenizer")

# --- httpx (service_registry) ---
if "httpx" not in sys.modules or isinstance(sys.modules.get("httpx"), MagicMock):
    _httpx = MagicMock(name="httpx")
    _httpx.AsyncClient = MagicMock
    _httpx.ConnectError = ConnectionError
    sys.modules.setdefault("httpx", _httpx)

# --- redis (session_system) ---
_redis_asyncio = MagicMock(name="redis.asyncio")
_redis_mod = MagicMock(name="redis")
_redis_mod.asyncio = _redis_asyncio
sys.modules.setdefault("redis", _redis_mod)
sys.modules.setdefault("redis.asyncio", _redis_asyncio)

# --- PyJWT (session_system) ---
if "jwt" not in sys.modules:
    try:
        import jwt as _jwt_real  # noqa: F401
    except ImportError:
        _stub("jwt")

# --- websockets (realtime_notification) ---
_ws_stub = _stub("websockets")
_ws_stub.exceptions = MagicMock()
_ws_stub.server = MagicMock()
_stub("websockets.exceptions")
_stub("websockets.server")

# --- SQLAlchemy declarative_base used in kvkk_compliance ---
if "sqlalchemy.ext.declarative" not in sys.modules:
    _sa_dec = MagicMock(name="sqlalchemy.ext.declarative")
    _sa_dec.declarative_base.return_value = MagicMock()
    sys.modules["sqlalchemy.ext.declarative"] = _sa_dec

# --- Cryptography (kvkk_compliance) ---
_crypto_fernet = MagicMock(name="cryptography.fernet")
_crypto_fernet.Fernet = MagicMock
sys.modules.setdefault("cryptography", MagicMock(name="cryptography"))
sys.modules.setdefault("cryptography.fernet", _crypto_fernet)

# --- Heavy internal deps for notification / job systems ---
for _dep in [
    "core.application_metrics",
    "core.message_queue_system",
    "core.structured_logging",
    "core.unified.auth_system",
    "core.unified_config",
    "core.unified_event_bus",
]:
    sys.modules.setdefault(_dep, MagicMock(name=_dep))

# Ensure get_unified_config returns something with attributes used at module level
_unified_cfg_mod = sys.modules["core.unified_config"]
_unified_cfg_mod.get_unified_config.return_value = MagicMock(
    websocket_host="localhost",
    websocket_port=8765,
)

# Ensure MetricType, QueueType etc. are proper enums or mocks
from enum import Enum as _Enum


class _MetricType(_Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class _QueueType(_Enum):
    EXAM_PROCESSING = "exam_processing"
    BATCH_PROCESSING = "batch_processing"
    CONTENT_PROCESSING = "content_processing"
    ANALYTICS = "analytics"
    CLEANUP = "cleanup"
    NOTIFICATIONS = "notifications"


class _EventType(_Enum):
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"


class _LogCategory(_Enum):
    REALTIME = "realtime"
    JOBS = "jobs"
    GENERAL = "general"


sys.modules["core.application_metrics"].MetricType = _MetricType
sys.modules["core.application_metrics"].get_metrics_collector = MagicMock(
    return_value=MagicMock()
)
sys.modules["core.message_queue_system"].QueueType = _QueueType
sys.modules["core.message_queue_system"].get_message_queue = MagicMock(
    return_value=MagicMock()
)
sys.modules["core.structured_logging"].LogCategory = _LogCategory
sys.modules["core.structured_logging"].get_logger = MagicMock(return_value=MagicMock())
sys.modules["core.unified.auth_system"].get_auth_system = MagicMock(
    return_value=MagicMock()
)


class _EventBusEvent:
    pass


sys.modules["core.unified_event_bus"].Event = _EventBusEvent
sys.modules["core.unified_event_bus"].EventType = _EventType
sys.modules["core.unified_event_bus"].get_event_bus = MagicMock(
    return_value=MagicMock()
)

# Also stub error context/monitoring used by query_builder
for _dep2 in [
    "core.error_context",
    "core.error_monitoring",
    "core.exceptions",
]:
    sys.modules.setdefault(_dep2, MagicMock(name=_dep2))


# Ensure ValidationError and DatabaseError are real Exception subclasses
class _ValidationError(Exception):
    pass


class _DatabaseError(Exception):
    pass


class _ErrorSeverity(_Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


sys.modules["core.exceptions"].ValidationError = _ValidationError
sys.modules["core.exceptions"].DatabaseError = _DatabaseError
sys.modules["core.exceptions"].ErrorSeverity = _ErrorSeverity
sys.modules["core.error_monitoring"].log_error = MagicMock()
sys.modules["core.error_context"].async_error_context = MagicMock(
    return_value=MagicMock(__aenter__=AsyncMock(), __aexit__=AsyncMock())
)

# Stub LLM sub-deps
for _dep3 in [
    "services.llm.base_llm_provider",
    "services.llm.multi_llm_config",
    "services.llm.sequential_thinking_mixin",
    "services.llm.gemini_provider",
    "services.llm.openai_provider",
    "services.llm.claude_provider",
    "services.llm.qwen_provider",
]:
    sys.modules.setdefault(_dep3, MagicMock(name=_dep3))

# Provide real-ish LLMProvider enum and LLMCapability for ensemble tests
from enum import Enum as _E2


class _LLMProvider(str, _E2):
    OPENAI = "openai"
    CLAUDE = "claude"
    QWEN = "qwen"
    GEMINI = "gemini"


class _LLMCapability(str, _E2):
    QUESTION_GENERATION = "question_generation"
    SEQUENTIAL_THINKING = "sequential_thinking"
    MATH_REASONING = "math_reasoning"
    STEP_BY_STEP = "step_by_step"


class _LLMRequest:
    def __init__(
        self, prompt="", system_prompt=None, max_tokens=None, temperature=None
    ):
        self.prompt = prompt
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature


class _LLMResponse:
    def __init__(
        self,
        provider=None,
        model_name="test",
        content="",
        latency_ms=100.0,
        tokens_used=10,
        cost_usd=0.001,
        confidence_score=0.9,
    ):
        self.provider = provider
        self.model_name = model_name
        self.content = content
        self.latency_ms = latency_ms
        self.tokens_used = tokens_used
        self.cost_usd = cost_usd
        self.confidence_score = confidence_score


class _BaseLLMProvider:
    async def generate(self, request):
        raise NotImplementedError

    async def check_health(self):
        return True

    def get_metrics(self):
        return {}


class _ReasoningResult:
    def to_dict(self):
        return {"steps": [], "final_answer": "ok"}


# Inject into stubs
sys.modules["services.llm.base_llm_provider"].BaseLLMProvider = _BaseLLMProvider
sys.modules["services.llm.base_llm_provider"].LLMRequest = _LLMRequest
sys.modules["services.llm.base_llm_provider"].LLMResponse = _LLMResponse
sys.modules["services.llm.multi_llm_config"].LLMProvider = _LLMProvider
sys.modules["services.llm.multi_llm_config"].LLMCapability = _LLMCapability
sys.modules["services.llm.sequential_thinking_mixin"].ReasoningResult = _ReasoningResult


# Build a minimal MultiLLMConfig stub
class _MultiLLMConfig:
    OPENAI_CONFIG = MagicMock()
    CLAUDE_CONFIG = MagicMock()
    QWEN_CONFIG = MagicMock()
    GEMINI_CONFIG = MagicMock()
    ENSEMBLE_STRATEGY = {
        "voting": {
            "weights": {
                _LLMProvider.OPENAI: 0.4,
                _LLMProvider.CLAUDE: 0.35,
                _LLMProvider.QWEN: 0.25,
                _LLMProvider.GEMINI: 0.3,
            }
        },
        "fallback_order": [_LLMProvider.OPENAI, _LLMProvider.CLAUDE, _LLMProvider.QWEN],
    }

    @classmethod
    def get_best_provider_for_capability(cls, capability, prefer_cost_effective=False):
        return _LLMProvider.OPENAI


sys.modules["services.llm.multi_llm_config"].MultiLLMConfig = _MultiLLMConfig
sys.modules["services.llm.multi_llm_config"].LLMModelConfig = MagicMock()

# ---------------------------------------------------------------------------
# NOW import the modules under test
# ---------------------------------------------------------------------------

from core.events import ServiceName  # noqa: E402

# ======================== 1. SERVICE REGISTRY ========================


class TestServiceRegistryModule:
    """Tests for core/service_registry.py"""

    def _get_module(self):
        from core import service_registry as sr

        return sr

    def test_service_status_enum_values(self):
        sr = self._get_module()
        assert sr.ServiceStatus.HEALTHY.value == "healthy"
        assert sr.ServiceStatus.UNHEALTHY.value == "unhealthy"
        assert sr.ServiceStatus.DEGRADED.value == "degraded"
        assert sr.ServiceStatus.UNKNOWN.value == "unknown"
        assert sr.ServiceStatus.STARTING.value == "starting"
        assert sr.ServiceStatus.STOPPING.value == "stopping"

    def test_service_instance_base_url(self):
        sr = self._get_module()
        inst = sr.ServiceInstance(
            service_name=ServiceName.GATEWAY,
            host="localhost",
            port=8000,
        )
        assert inst.base_url == "http://localhost:8000"

    def test_service_instance_health_url(self):
        sr = self._get_module()
        inst = sr.ServiceInstance(
            service_name=ServiceName.GATEWAY,
            host="myhost",
            port=9000,
            health_endpoint="/api/health",
        )
        assert inst.health_url == "http://myhost:9000/api/health"

    def test_service_instance_to_dict(self):
        sr = self._get_module()
        inst = sr.ServiceInstance(
            service_name=ServiceName.EXAM,
            host="localhost",
            port=8001,
        )
        d = inst.to_dict()
        assert d["service_name"] == ServiceName.EXAM.value
        assert d["host"] == "localhost"
        assert d["port"] == 8001
        assert d["status"] == sr.ServiceStatus.UNKNOWN.value
        assert d["last_health_check"] is None

    def test_service_instance_to_dict_with_last_check(self):
        sr = self._get_module()
        inst = sr.ServiceInstance(
            service_name=ServiceName.AI,
            host="ai-host",
            port=8004,
        )
        from datetime import UTC

        inst.last_health_check = datetime.now(UTC)
        d = inst.to_dict()
        assert d["last_health_check"] is not None

    def test_circuit_breaker_initial_state(self):
        sr = self._get_module()
        cb = sr.CircuitBreaker(failure_threshold=3, recovery_timeout=10.0)
        assert not cb.is_open("svc-a")

    def test_circuit_breaker_opens_after_threshold(self):
        sr = self._get_module()
        cb = sr.CircuitBreaker(failure_threshold=3)
        cb.record_failure("svc-a")
        cb.record_failure("svc-a")
        assert not cb.is_open("svc-a")
        cb.record_failure("svc-a")
        assert cb.is_open("svc-a")

    def test_circuit_breaker_closes_on_success(self):
        sr = self._get_module()
        cb = sr.CircuitBreaker(failure_threshold=2)
        cb.record_failure("svc-b")
        cb.record_failure("svc-b")
        assert cb.is_open("svc-b")
        cb.record_success("svc-b")
        assert not cb.is_open("svc-b")

    def test_circuit_breaker_half_open_after_timeout(self):
        sr = self._get_module()
        # Use a large recovery_timeout so circuit stays open immediately after failure
        cb = sr.CircuitBreaker(failure_threshold=1, recovery_timeout=9999.0)
        cb.record_failure("svc-c")
        assert cb.is_open("svc-c")
        # Now simulate the timeout has passed by backdating last_failure_time
        from datetime import UTC

        cb.last_failure_time["svc-c"] = datetime.now(UTC) - timedelta(seconds=10000)
        assert not cb.is_open("svc-c")

    @pytest.mark.asyncio
    async def test_service_registry_register_and_get(self):
        sr = self._get_module()
        registry = sr.ServiceRegistry()
        instance = sr.ServiceInstance(
            service_name=ServiceName.GATEWAY,
            host="localhost",
            port=8000,
            status=sr.ServiceStatus.HEALTHY,
        )
        result = await registry.register(instance)
        assert result is True
        instances = await registry.get_all_instances(ServiceName.GATEWAY)
        assert len(instances) == 1

    @pytest.mark.asyncio
    async def test_service_registry_get_service_returns_healthy(self):
        sr = self._get_module()
        registry = sr.ServiceRegistry()
        instance = sr.ServiceInstance(
            service_name=ServiceName.EXAM,
            host="localhost",
            port=8001,
            status=sr.ServiceStatus.HEALTHY,
        )
        await registry.register(instance)
        found = await registry.get_service(ServiceName.EXAM)
        assert found is not None
        assert found.host == "localhost"

    @pytest.mark.asyncio
    async def test_service_registry_get_service_returns_none_when_empty(self):
        sr = self._get_module()
        registry = sr.ServiceRegistry()
        result = await registry.get_service(ServiceName.IRT)
        assert result is None

    @pytest.mark.asyncio
    async def test_service_registry_get_service_no_healthy(self):
        sr = self._get_module()
        registry = sr.ServiceRegistry()
        instance = sr.ServiceInstance(
            service_name=ServiceName.AI,
            host="localhost",
            port=8004,
            status=sr.ServiceStatus.UNHEALTHY,
        )
        await registry.register(instance)
        # No healthy, no degraded — returns None
        result = await registry.get_service(ServiceName.AI)
        assert result is None

    @pytest.mark.asyncio
    async def test_service_registry_get_service_falls_back_to_degraded(self):
        sr = self._get_module()
        registry = sr.ServiceRegistry()
        instance = sr.ServiceInstance(
            service_name=ServiceName.QUESTION,
            host="localhost",
            port=8002,
            status=sr.ServiceStatus.DEGRADED,
        )
        await registry.register(instance)
        result = await registry.get_service(ServiceName.QUESTION)
        assert result is not None

    @pytest.mark.asyncio
    async def test_service_registry_deregister(self):
        sr = self._get_module()
        registry = sr.ServiceRegistry()
        instance = sr.ServiceInstance(
            service_name=ServiceName.GATEWAY,
            host="localhost",
            port=8000,
            status=sr.ServiceStatus.HEALTHY,
        )
        await registry.register(instance)
        removed = await registry.deregister(ServiceName.GATEWAY, "localhost", 8000)
        assert removed is True
        instances = await registry.get_all_instances(ServiceName.GATEWAY)
        assert len(instances) == 0

    @pytest.mark.asyncio
    async def test_service_registry_deregister_nonexistent(self):
        sr = self._get_module()
        registry = sr.ServiceRegistry()
        result = await registry.deregister(ServiceName.LEARNING_PATH, "no-host", 9999)
        assert result is False

    @pytest.mark.asyncio
    async def test_service_registry_update_existing(self):
        sr = self._get_module()
        registry = sr.ServiceRegistry()
        inst1 = sr.ServiceInstance(
            service_name=ServiceName.GATEWAY,
            host="localhost",
            port=8000,
            status=sr.ServiceStatus.UNKNOWN,
        )
        await registry.register(inst1)
        inst2 = sr.ServiceInstance(
            service_name=ServiceName.GATEWAY,
            host="localhost",
            port=8000,
            status=sr.ServiceStatus.HEALTHY,
            version="2.0.0",
        )
        await registry.register(inst2)
        instances = await registry.get_all_instances(ServiceName.GATEWAY)
        assert len(instances) == 1
        assert instances[0].status == sr.ServiceStatus.HEALTHY

    def test_get_status_summary(self):
        sr = self._get_module()
        registry = sr.ServiceRegistry()
        summary = registry.get_status_summary()
        assert "total_services" in summary
        assert summary["total_services"] == 0

    @pytest.mark.asyncio
    async def test_service_registry_get_service_url(self):
        sr = self._get_module()
        registry = sr.ServiceRegistry()
        instance = sr.ServiceInstance(
            service_name=ServiceName.EXAM,
            host="exam-host",
            port=8001,
            status=sr.ServiceStatus.HEALTHY,
        )
        await registry.register(instance)
        url = await registry.get_service_url(ServiceName.EXAM, "/api/v1/exams")
        assert url == "http://exam-host:8001/api/v1/exams"

    @pytest.mark.asyncio
    async def test_service_registry_get_service_url_none_when_missing(self):
        sr = self._get_module()
        registry = sr.ServiceRegistry()
        url = await registry.get_service_url(ServiceName.IRT, "/irt")
        assert url is None


# ======================== 2. BERTURK SERVICE ========================


# Force-load the real berturk_service module, bypassing any MagicMock stub
# that other test files may have injected.
def _get_real_berturk_class():
    """Return the real BERTurkService class by importing directly from file."""
    import importlib.util
    import pathlib

    src = pathlib.Path(__file__).parent.parent.parent / "core" / "berturk_service.py"
    spec = importlib.util.spec_from_file_location("_berturk_real", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.BERTurkService


class TestBERTurkService:
    """Tests for core/berturk_service.py"""

    def _make_service(self):
        BERTurkService = _get_real_berturk_class()
        svc = BERTurkService()
        # Do not call initialize() — models would try to download
        return svc

    def test_berturk_service_initial_state(self):
        svc = self._make_service()
        assert svc.session_cache == {}
        assert svc.max_cache_size == 1000
        assert svc.performance_stats["total_analyses"] == 0

    def test_preprocess_text_strips_whitespace(self):
        svc = self._make_service()
        result = svc._preprocess_text("  hello world  ")
        assert result == "hello world"

    def test_preprocess_text_collapses_spaces(self):
        svc = self._make_service()
        result = svc._preprocess_text("hello   world")
        assert result == "hello world"

    def test_preprocess_text_empty(self):
        svc = self._make_service()
        assert svc._preprocess_text("") == ""
        assert svc._preprocess_text(None) == ""

    def test_determine_main_sentiment(self):
        svc = self._make_service()
        scores = {"positive": 0.7, "neutral": 0.2, "negative": 0.1}
        assert svc._determine_main_sentiment(scores) == "positive"

    def test_add_to_cache_and_evict(self):
        svc = self._make_service()
        svc.max_cache_size = 3
        svc._add_to_cache("k1", "v1")
        svc._add_to_cache("k2", "v2")
        svc._add_to_cache("k3", "v3")
        assert len(svc.session_cache) == 3
        svc._add_to_cache("k4", "v4")
        assert len(svc.session_cache) == 3
        assert "k4" in svc.session_cache

    def test_create_empty_sentiment_result(self):
        svc = self._make_service()
        result = svc._create_empty_sentiment_result("test text")
        assert result.text == "test text"
        assert result.sentiment == "neutral"
        assert result.confidence == 0.0

    def test_create_empty_motivation_assessment(self):
        svc = self._make_service()
        result = svc._create_empty_motivation_assessment("student-123")
        assert result.student_id == "student-123"
        assert result.motivation_level == 0.5
        assert not result.support_needed

    def test_create_empty_intent_result(self):
        svc = self._make_service()
        result = svc._create_empty_intent_result("some text")
        assert result.intent == "general"
        assert result.confidence == 0.0
        assert result.urgency_level == "low"

    def test_create_empty_contextual_result(self):
        svc = self._make_service()
        result = svc._create_empty_contextual_result("text")
        assert result.main_topic == "genel"
        assert result.academic_domain == "general"

    def test_generate_motivation_recommendations_low_motivation(self):
        svc = self._make_service()
        recs = svc._generate_motivation_recommendations(0.2, 0.5, 0.3, 0.5)
        assert any("motivasyon" in r.lower() for r in recs)

    def test_generate_motivation_recommendations_high_frustration(self):
        svc = self._make_service()
        recs = svc._generate_motivation_recommendations(0.5, 0.5, 0.8, 0.5)
        assert any("zorluk" in r.lower() or "mola" in r.lower() for r in recs)

    def test_generate_motivation_recommendations_low_confidence(self):
        svc = self._make_service()
        recs = svc._generate_motivation_recommendations(0.5, 0.5, 0.3, 0.1)
        assert any("güven" in r.lower() or "geri bildirim" in r.lower() for r in recs)

    def test_generate_motivation_recommendations_all_good(self):
        svc = self._make_service()
        recs = svc._generate_motivation_recommendations(0.7, 0.7, 0.2, 0.7)
        assert len(recs) == 1
        assert "genel olarak iyi" in recs[0].lower()

    def test_extract_main_topic(self):
        svc = self._make_service()
        topic = svc._extract_main_topic("matematik matematik matematik fizik")
        assert topic == "matematik"

    def test_extract_main_topic_empty(self):
        svc = self._make_service()
        topic = svc._extract_main_topic("")
        assert topic == "genel"

    def test_assess_text_difficulty_empty(self):
        svc = self._make_service()
        diff = svc._assess_text_difficulty("")
        assert diff == 0.0

    def test_assess_text_difficulty_simple(self):
        svc = self._make_service()
        diff = svc._assess_text_difficulty("a b c d")
        assert 0.0 <= diff <= 1.0

    def test_assess_text_difficulty_complex(self):
        svc = self._make_service()
        complex_text = "differentiation integration calculus trigonometry"
        diff = svc._assess_text_difficulty(complex_text)
        assert 0.0 <= diff <= 1.0

    def test_classify_academic_domain_math(self):
        svc = self._make_service()
        domain = svc._classify_academic_domain("matematik sayı hesap")
        assert domain == "mathematics"

    def test_classify_academic_domain_general(self):
        svc = self._make_service()
        domain = svc._classify_academic_domain("bir şeyler hakkında")
        assert domain == "general"

    def test_determine_context_category_academic(self):
        svc = self._make_service()
        cat = svc._determine_context_category("bu ders için ödev yapmam gerekiyor")
        assert cat == "academic"

    def test_determine_urgency_complaint_intent(self):
        svc = self._make_service()
        urgency = svc._determine_urgency_level("bir sorun var", "complaint")
        assert urgency == "high"

    def test_determine_urgency_help_request(self):
        svc = self._make_service()
        urgency = svc._determine_urgency_level("yardım lazım", "help_request")
        assert urgency == "medium"

    def test_determine_urgency_low(self):
        svc = self._make_service()
        urgency = svc._determine_urgency_level("tamam", "general")
        assert urgency == "low"

    def test_extract_simple_entities_numbers(self):
        svc = self._make_service()
        entities = svc._extract_simple_entities("3 tane matematik sorusu var 42")
        nums = [e for e in entities if e["type"] == "number"]
        assert len(nums) >= 2

    def test_extract_key_concepts_academic(self):
        svc = self._make_service()
        concepts = svc._extract_key_concepts("fizik kimya biyoloji matematik")
        # Words in academic_domains with len >= 5
        assert isinstance(concepts, list)

    @pytest.mark.asyncio
    async def test_analyze_detailed_emotions_empty_text(self):
        svc = self._make_service()
        result = await svc._analyze_detailed_emotions("")
        assert result["joy"] == 0.0
        assert result["anger"] == 0.0

    @pytest.mark.asyncio
    async def test_analyze_detailed_emotions_with_joy(self):
        svc = self._make_service()
        result = await svc._analyze_detailed_emotions("mutlu sevinçli keyifli")
        assert result["joy"] > 0.0

    @pytest.mark.asyncio
    async def test_analyze_educational_context_empty(self):
        svc = self._make_service()
        result = await svc._analyze_educational_context("")
        assert all(v == 0.0 for v in result.values())

    @pytest.mark.asyncio
    async def test_analyze_educational_context_motivation(self):
        svc = self._make_service()
        result = await svc._analyze_educational_context("heyecanlı istekli kararlı")
        assert result["motivation"] > 0.0

    @pytest.mark.asyncio
    async def test_get_performance_stats_initial(self):
        svc = self._make_service()
        stats = await svc.get_performance_stats()
        assert stats["total_analyses"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_hit_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        svc = self._make_service()
        svc.session_cache["key"] = "value"
        await svc.clear_cache()
        assert svc.session_cache == {}

    @pytest.mark.asyncio
    async def test_assess_student_motivation_no_texts(self):
        svc = self._make_service()
        result = await svc.assess_student_motivation("s-1", [])
        assert result.student_id == "s-1"
        assert result.motivation_level == 0.5

    @pytest.mark.asyncio
    async def test_detect_intent_empty_text(self):
        svc = self._make_service()
        result = await svc.detect_intent("")
        assert result.intent == "general"

    @pytest.mark.asyncio
    async def test_extract_contextual_meaning_empty(self):
        svc = self._make_service()
        result = await svc.extract_contextual_meaning("")
        assert result.main_topic == "genel"

    @pytest.mark.asyncio
    async def test_extract_contextual_meaning_math_text(self):
        svc = self._make_service()
        result = await svc.extract_contextual_meaning("matematik ve sayılar üzerine")
        assert result.academic_domain in ("mathematics", "general")
        assert 0.0 <= result.difficulty_level <= 1.0

    def test_extract_subtopics(self):
        svc = self._make_service()
        subtopics = svc._extract_subtopics("biyoloji fizik matematik")
        assert isinstance(subtopics, list)


# ======================== 3. UNIFIED SESSION SYSTEM ========================


class TestUnifiedSessionSystem:
    """Tests for core/unified/session_system.py"""

    def _get_manager(self):
        from core.unified.session_system import SessionConfig, UnifiedSessionManager

        cfg = SessionConfig(
            session_timeout=3600,
            jwt_secret="test-secret-key",
            redis_url="redis://localhost:6379/99",
            enable_cleanup=False,
        )
        manager = UnifiedSessionManager(config=cfg)
        manager.redis_client = None  # force memory mode
        return manager

    def test_session_config_defaults(self):
        from core.unified.session_system import SessionConfig

        cfg = SessionConfig()
        assert cfg.session_timeout == 3600
        assert cfg.max_sessions_per_user == 5
        assert cfg.jwt_algorithm == "HS256"

    def test_device_fingerprint_generate(self):
        from core.unified.session_system import DeviceFingerprint

        device_id = DeviceFingerprint.generate_device_id("Mozilla/5.0", "192.168.1.100")
        assert len(device_id) == 16

    def test_device_fingerprint_same_network(self):
        from core.unified.session_system import DeviceFingerprint

        id1 = DeviceFingerprint.generate_device_id("UA1", "192.168.1.1")
        id2 = DeviceFingerprint.generate_device_id("UA1", "192.168.1.2")
        # Same network segment -> same device_id
        assert id1 == id2

    def test_detect_device_type_mobile(self):
        from core.unified.session_system import DeviceFingerprint, DeviceType

        dt = DeviceFingerprint.detect_device_type("Mozilla/5.0 (iPhone; CPU iPhone OS)")
        assert dt == DeviceType.MOBILE

    def test_detect_device_type_tablet(self):
        from core.unified.session_system import DeviceFingerprint, DeviceType

        dt = DeviceFingerprint.detect_device_type("Mozilla/5.0 (iPad; CPU OS)")
        assert dt == DeviceType.TABLET

    def test_detect_device_type_desktop(self):
        from core.unified.session_system import DeviceFingerprint, DeviceType

        dt = DeviceFingerprint.detect_device_type("Electron desktop app")
        assert dt == DeviceType.DESKTOP

    def test_detect_device_type_web(self):
        from core.unified.session_system import DeviceFingerprint, DeviceType

        dt = DeviceFingerprint.detect_device_type("Mozilla/5.0 Chrome")
        assert dt == DeviceType.WEB

    def test_session_info_is_expired(self):
        from core.unified.session_system import DeviceType, SessionInfo

        now = datetime.now()
        session = SessionInfo(
            session_id="s1",
            user_id="u1",
            device_id="d1",
            device_type=DeviceType.WEB,
            ip_address="127.0.0.1",
            user_agent="test",
            created_at=now - timedelta(hours=2),
            last_activity=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1),
        )
        assert session.is_expired is True
        assert session.is_active is False

    def test_session_info_is_active(self):
        from core.unified.session_system import DeviceType, SessionInfo

        now = datetime.now()
        session = SessionInfo(
            session_id="s2",
            user_id="u2",
            device_id="d2",
            device_type=DeviceType.WEB,
            ip_address="127.0.0.1",
            user_agent="test",
            created_at=now,
            last_activity=now,
            expires_at=now + timedelta(hours=1),
        )
        assert session.is_active is True

    def test_session_info_to_dict(self):
        from core.unified.session_system import DeviceType, SessionInfo

        now = datetime.now()
        session = SessionInfo(
            session_id="s3",
            user_id="u3",
            device_id="d3",
            device_type=DeviceType.MOBILE,
            ip_address="10.0.0.1",
            user_agent="Mobile",
            created_at=now,
            last_activity=now,
            expires_at=now + timedelta(hours=1),
        )
        d = session.to_dict()
        assert d["session_id"] == "s3"
        assert d["device_type"] == "mobile"

    def test_session_info_from_dict(self):
        from core.unified.session_system import DeviceType, SessionInfo

        now = datetime.now()
        session = SessionInfo(
            session_id="s4",
            user_id="u4",
            device_id="d4",
            device_type=DeviceType.API,
            ip_address="1.2.3.4",
            user_agent="API",
            created_at=now,
            last_activity=now,
            expires_at=now + timedelta(hours=1),
        )
        d = session.to_dict()
        restored = SessionInfo.from_dict(d)
        assert restored.session_id == "s4"
        assert restored.device_type == DeviceType.API

    def test_token_info_is_expired(self):
        from core.unified.session_system import TokenInfo, TokenType

        now = datetime.now()
        token = TokenInfo(
            token_id="t1",
            user_id="u1",
            token_type=TokenType.ACCESS,
            session_id="s1",
            created_at=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1),
        )
        assert token.is_expired is True

    def test_token_info_to_dict(self):
        from core.unified.session_system import TokenInfo, TokenType

        now = datetime.now()
        token = TokenInfo(
            token_id="t2",
            user_id="u2",
            token_type=TokenType.REFRESH,
            session_id="s2",
            created_at=now,
            expires_at=now + timedelta(days=7),
            scopes={"read", "write"},
        )
        d = token.to_dict()
        assert d["token_type"] == "refresh"
        assert set(d["scopes"]) == {"read", "write"}

    def test_make_redis_key(self):
        mgr = self._get_manager()
        key = mgr._make_redis_key("session", "abc123")
        assert key == "kiro2:session:session:abc123"

    @pytest.mark.asyncio
    async def test_generate_access_token_returns_string(self):
        mgr = self._get_manager()
        token = mgr.generate_access_token("user-1", "session-1", {"read"})
        assert isinstance(token, str)
        assert len(token) > 20

    @pytest.mark.asyncio
    async def test_generate_refresh_token_returns_string(self):
        mgr = self._get_manager()
        token = mgr.generate_refresh_token("user-2", "session-2")
        assert isinstance(token, str)

    @pytest.mark.asyncio
    async def test_validate_token_valid(self):
        mgr = self._get_manager()
        token = mgr.generate_access_token("user-3", "session-3")
        payload = mgr.validate_token(token)
        assert payload is not None
        assert payload["sub"] == "user-3"

    def test_validate_token_invalid(self):
        mgr = self._get_manager()
        payload = mgr.validate_token("not.a.valid.token")
        assert payload is None

    @pytest.mark.asyncio
    async def test_create_session_memory(self):
        mgr = self._get_manager()
        session = await mgr.create_session(
            user_id="u1",
            ip_address="127.0.0.1",
            user_agent="TestBrowser",
        )
        assert session.user_id == "u1"
        assert session.is_active

    @pytest.mark.asyncio
    async def test_get_session_memory(self):
        mgr = self._get_manager()
        session = await mgr.create_session("u2", "127.0.0.1", "UA")
        fetched = await mgr.get_session(session.session_id)
        assert fetched is not None
        assert fetched.session_id == session.session_id

    @pytest.mark.asyncio
    async def test_get_session_not_found(self):
        mgr = self._get_manager()
        result = await mgr.get_session("nonexistent-session-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_revoke_session(self):
        mgr = self._get_manager()
        session = await mgr.create_session("u3", "127.0.0.1", "UA")
        revoked = await mgr.revoke_session(session.session_id)
        assert revoked is True
        gone = await mgr.get_session(session.session_id)
        assert gone is None

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_session(self):
        mgr = self._get_manager()
        result = await mgr.revoke_session("no-such-session")
        assert result is False

    @pytest.mark.asyncio
    async def test_update_session_activity(self):
        mgr = self._get_manager()
        session = await mgr.create_session("u4", "127.0.0.1", "UA")
        old_activity = session.last_activity
        result = await mgr.update_session_activity(session.session_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_session_stats(self):
        mgr = self._get_manager()
        await mgr.create_session("u5", "127.0.0.1", "UA")
        stats = await mgr.get_session_stats()
        assert "total_sessions" in stats
        assert stats["memory_sessions"] >= 1

    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        mgr = self._get_manager()
        session = await mgr.create_session("u6", "127.0.0.1", "UA")
        # Force expiry
        session.expires_at = datetime.now() - timedelta(hours=1)
        mgr._memory_sessions[session.session_id] = session
        await mgr._cleanup_expired()
        assert session.session_id not in mgr._memory_sessions

    @pytest.mark.asyncio
    async def test_revoke_user_sessions(self):
        mgr = self._get_manager()
        s1 = await mgr.create_session("u7", "127.0.0.1", "UA")
        s2 = await mgr.create_session("u7", "127.0.0.2", "UA2")
        count = await mgr.revoke_user_sessions("u7")
        assert count == 2

    def test_get_session_manager_singleton(self):
        from core.unified.session_system import get_session_manager

        mgr1 = get_session_manager()
        mgr2 = get_session_manager()
        assert mgr1 is mgr2


# ======================== 4. LLM ENSEMBLE MANAGER ========================


class TestLLMEnsembleManager:
    """Tests for services/llm/ensemble_manager.py"""

    def _make_mock_provider(
        self, provider_type, content="OK", latency=100.0, cost=0.001, confidence=0.9
    ):
        provider = MagicMock(spec=_BaseLLMProvider)
        provider.provider = provider_type
        resp = _LLMResponse(
            provider=provider_type,
            content=content,
            latency_ms=latency,
            cost_usd=cost,
            confidence_score=confidence,
        )
        provider.generate = AsyncMock(return_value=resp)
        provider.check_health = AsyncMock(return_value=True)
        provider.get_metrics = MagicMock(return_value={"calls": 1})
        return provider

    def _make_manager_with_mocks(self):
        """Create ensemble manager bypassing real provider init."""
        from services.llm.ensemble_manager import MultiLLMEnsembleManager

        mgr = object.__new__(MultiLLMEnsembleManager)
        mgr.providers = {
            _LLMProvider.OPENAI: self._make_mock_provider(
                _LLMProvider.OPENAI, content="OpenAI answer", latency=200.0
            ),
            _LLMProvider.CLAUDE: self._make_mock_provider(
                _LLMProvider.CLAUDE, content="Claude answer", latency=100.0
            ),
        }
        return mgr

    def test_ensemble_strategy_majority_voting(self):
        from services.llm.ensemble_manager import EnsembleStrategy

        responses = [
            _LLMResponse(
                provider=_LLMProvider.OPENAI,
                content="A",
                latency_ms=200,
                cost_usd=0.01,
                confidence_score=0.9,
            ),
            _LLMResponse(
                provider=_LLMProvider.CLAUDE,
                content="B",
                latency_ms=100,
                cost_usd=0.005,
                confidence_score=0.8,
            ),
        ]
        best = EnsembleStrategy.majority_voting(responses)
        assert isinstance(best, _LLMResponse)

    def test_ensemble_strategy_quality_threshold_filter(self):
        from services.llm.ensemble_manager import EnsembleStrategy

        responses = [
            _LLMResponse(
                provider=_LLMProvider.OPENAI,
                content="A",
                latency_ms=200,
                cost_usd=0.01,
                confidence_score=0.9,
            ),
            _LLMResponse(
                provider=_LLMProvider.CLAUDE,
                content="B",
                latency_ms=100,
                cost_usd=0.005,
                confidence_score=0.3,
            ),
        ]
        filtered = EnsembleStrategy.quality_threshold_filter(responses, min_quality=0.7)
        assert len(filtered) == 1
        assert filtered[0].content == "A"

    def test_ensemble_strategy_cost_optimized(self):
        from services.llm.ensemble_manager import EnsembleStrategy

        responses = [
            _LLMResponse(
                provider=_LLMProvider.OPENAI,
                content="Expensive",
                latency_ms=200,
                cost_usd=0.05,
                confidence_score=0.9,
            ),
            _LLMResponse(
                provider=_LLMProvider.CLAUDE,
                content="Cheap",
                latency_ms=300,
                cost_usd=0.001,
                confidence_score=0.85,
            ),
        ]
        best = EnsembleStrategy.cost_optimized_selection(
            responses, quality_threshold=0.8
        )
        assert best.content == "Cheap"

    def test_ensemble_strategy_cost_optimized_no_quality(self):
        from services.llm.ensemble_manager import EnsembleStrategy

        responses = [
            _LLMResponse(
                provider=_LLMProvider.OPENAI,
                content="Low",
                latency_ms=200,
                cost_usd=0.001,
                confidence_score=0.4,
            ),
        ]
        best = EnsembleStrategy.cost_optimized_selection(
            responses, quality_threshold=0.9
        )
        assert best.content == "Low"

    def test_ensemble_strategy_latency_optimized(self):
        from services.llm.ensemble_manager import EnsembleStrategy

        responses = [
            _LLMResponse(
                provider=_LLMProvider.OPENAI,
                content="Slow",
                latency_ms=500,
                cost_usd=0.01,
                confidence_score=0.9,
            ),
            _LLMResponse(
                provider=_LLMProvider.CLAUDE,
                content="Fast",
                latency_ms=50,
                cost_usd=0.01,
                confidence_score=0.85,
            ),
        ]
        best = EnsembleStrategy.latency_optimized_selection(responses)
        assert best.content == "Fast"

    @pytest.mark.asyncio
    async def test_generate_with_ensemble_majority(self):
        mgr = self._make_manager_with_mocks()
        from services.llm.ensemble_manager import MultiLLMEnsembleManager

        request = _LLMRequest(prompt="test")
        result = await MultiLLMEnsembleManager.generate_with_ensemble(
            mgr, request, strategy="majority_voting"
        )
        assert isinstance(result, _LLMResponse)

    @pytest.mark.asyncio
    async def test_generate_with_ensemble_cost_optimized(self):
        mgr = self._make_manager_with_mocks()
        from services.llm.ensemble_manager import MultiLLMEnsembleManager

        request = _LLMRequest(prompt="test")
        result = await MultiLLMEnsembleManager.generate_with_ensemble(
            mgr, request, strategy="cost_optimized"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_generate_with_ensemble_latency_optimized(self):
        mgr = self._make_manager_with_mocks()
        from services.llm.ensemble_manager import MultiLLMEnsembleManager

        request = _LLMRequest(prompt="test")
        result = await MultiLLMEnsembleManager.generate_with_ensemble(
            mgr, request, strategy="latency_optimized"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_generate_with_ensemble_unknown_strategy(self):
        mgr = self._make_manager_with_mocks()
        from services.llm.ensemble_manager import MultiLLMEnsembleManager

        request = _LLMRequest(prompt="test")
        result = await MultiLLMEnsembleManager.generate_with_ensemble(
            mgr, request, strategy="unknown"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_generate_with_fallback(self):
        mgr = self._make_manager_with_mocks()
        from services.llm.ensemble_manager import MultiLLMEnsembleManager

        request = _LLMRequest(prompt="test")
        result = await MultiLLMEnsembleManager.generate_with_fallback(mgr, request)
        assert result is not None

    @pytest.mark.asyncio
    async def test_generate_with_fallback_preferred_provider(self):
        mgr = self._make_manager_with_mocks()
        from services.llm.ensemble_manager import MultiLLMEnsembleManager

        request = _LLMRequest(prompt="test")
        result = await MultiLLMEnsembleManager.generate_with_fallback(
            mgr, request, preferred_provider=_LLMProvider.CLAUDE
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_check_health_all(self):
        mgr = self._make_manager_with_mocks()
        from services.llm.ensemble_manager import MultiLLMEnsembleManager

        health = await MultiLLMEnsembleManager.check_health_all(mgr)
        assert _LLMProvider.OPENAI in health
        assert health[_LLMProvider.OPENAI] is True

    def test_get_metrics_all(self):
        mgr = self._make_manager_with_mocks()
        from services.llm.ensemble_manager import MultiLLMEnsembleManager

        metrics = MultiLLMEnsembleManager.get_metrics_all(mgr)
        assert _LLMProvider.OPENAI in metrics

    def test_get_best_provider_for_capability(self):
        mgr = self._make_manager_with_mocks()
        from services.llm.ensemble_manager import MultiLLMEnsembleManager

        provider = MultiLLMEnsembleManager.get_best_provider_for_capability(
            mgr, _LLMCapability.SEQUENTIAL_THINKING
        )
        # May return None if best_provider_type not in providers, that's fine
        # Just ensure no crash

    def test_repr(self):
        mgr = self._make_manager_with_mocks()
        r = repr(mgr)
        assert "MultiLLMEnsembleManager" in r

    def test_vote_on_reasoning_results_single(self):
        mgr = self._make_manager_with_mocks()
        results = [{"steps": [1, 2, 3], "final_answer": "42", "provider": "openai"}]
        best = mgr._vote_on_reasoning_results(results)
        assert best["final_answer"] == "42"

    def test_vote_on_reasoning_results_multiple(self):
        mgr = self._make_manager_with_mocks()
        results = [
            {
                "steps": [1, 2, 3, 4],
                "final_answer": "A",
                "provider": "openai",
                "confidence": 0.9,
                "latency_ms": 1000,
            },
            {
                "steps": [1],
                "final_answer": "B",
                "provider": "claude",
                "confidence": 0.5,
                "latency_ms": 5000,
            },
        ]
        best = mgr._vote_on_reasoning_results(results)
        assert "voting_winner" in best

    def test_vote_on_reasoning_results_empty_raises(self):
        mgr = self._make_manager_with_mocks()
        with pytest.raises(ValueError):
            mgr._vote_on_reasoning_results([])

    @pytest.mark.asyncio
    async def test_generate_with_thinking_prompt(self):
        mgr = self._make_manager_with_mocks()
        provider = mgr.providers[_LLMProvider.OPENAI]
        result = await mgr._generate_with_thinking_prompt(provider, "What is 2+2?", 5)
        assert "problem" in result
        assert "final_answer" in result


# ======================== 5. QUERY BUILDER ========================


class TestQueryBuilder:
    """Tests for core/query_builder.py (enum and dataclass-level tests)."""

    def test_sort_order_values(self):
        from core.query_builder import SortOrder

        assert SortOrder.ASC.value == "asc"
        assert SortOrder.DESC.value == "desc"

    def test_join_type_values(self):
        from core.query_builder import JoinType

        assert JoinType.INNER.value == "inner"
        assert JoinType.LEFT.value == "left"

    def test_comparison_operator_values(self):
        from core.query_builder import ComparisonOperator

        assert ComparisonOperator.EQ.value == "eq"
        assert ComparisonOperator.LIKE.value == "like"
        assert ComparisonOperator.BETWEEN.value == "between"

    def test_query_filter_dataclass(self):
        from core.query_builder import ComparisonOperator, QueryFilter

        f = QueryFilter(field="name", operator=ComparisonOperator.EQ, value="test")
        assert f.field == "name"
        assert f.case_sensitive is True

    def test_query_sort_dataclass(self):
        from core.query_builder import QuerySort, SortOrder

        s = QuerySort(field="created_at", order=SortOrder.DESC)
        assert s.field == "created_at"
        assert s.order == SortOrder.DESC

    def test_query_filter_between_non_pair_raises(self):
        from core.query_builder import ComparisonOperator, QueryFilter

        f = QueryFilter(field="score", operator=ComparisonOperator.BETWEEN, value=[1])

        class FakeModel:
            score = MagicMock()
            score.between = MagicMock(return_value=True)

        with pytest.raises(Exception):
            f.to_sql_condition(FakeModel)

    def test_query_filter_unknown_field_raises(self):
        from core.query_builder import ComparisonOperator, QueryFilter

        f = QueryFilter(field="no_such_field", operator=ComparisonOperator.EQ, value=1)

        class EmptyModel:
            __name__ = "EmptyModel"

        with pytest.raises(Exception):
            f.to_sql_condition(EmptyModel)

    @pytest.mark.parametrize(
        "operator,value",
        [
            ("eq", 1),
            ("ne", 1),
            ("lt", 5),
            ("le", 5),
            ("gt", 0),
            ("ge", 0),
            ("in", [1, 2]),
            ("not_in", [3]),
            ("is_null", None),
            ("is_not_null", None),
        ],
    )
    def test_query_filter_operators(self, operator, value):
        from core.query_builder import ComparisonOperator, QueryFilter

        op_map = {
            "eq": ComparisonOperator.EQ,
            "ne": ComparisonOperator.NE,
            "lt": ComparisonOperator.LT,
            "le": ComparisonOperator.LE,
            "gt": ComparisonOperator.GT,
            "ge": ComparisonOperator.GE,
            "in": ComparisonOperator.IN,
            "not_in": ComparisonOperator.NOT_IN,
            "is_null": ComparisonOperator.IS_NULL,
            "is_not_null": ComparisonOperator.IS_NOT_NULL,
        }
        col_mock = MagicMock()
        col_mock.__eq__ = MagicMock(return_value=True)
        col_mock.__ne__ = MagicMock(return_value=True)
        col_mock.__lt__ = MagicMock(return_value=True)
        col_mock.__le__ = MagicMock(return_value=True)
        col_mock.__gt__ = MagicMock(return_value=True)
        col_mock.__ge__ = MagicMock(return_value=True)
        col_mock.in_ = MagicMock(return_value=True)
        col_mock.is_ = MagicMock(return_value=True)
        col_mock.is_not = MagicMock(return_value=True)

        class FakeModel:
            __name__ = "FakeModel"

        FakeModel.some_field = col_mock
        f = QueryFilter(
            field="some_field",
            operator=op_map[operator],
            value=value,
        )
        result = f.to_sql_condition(FakeModel)
        # We just ensure no crash

    def test_query_filter_like_case_insensitive(self):
        from core.query_builder import ComparisonOperator, QueryFilter

        col_mock = MagicMock()
        col_mock.ilike = MagicMock(return_value=True)

        class FakeModel:
            __name__ = "FakeModel"

        FakeModel.title = col_mock
        f = QueryFilter(
            field="title",
            operator=ComparisonOperator.LIKE,
            value="test",
            case_sensitive=False,
        )
        f.to_sql_condition(FakeModel)
        col_mock.ilike.assert_called_once()

    def test_query_filter_starts_with(self):
        from core.query_builder import ComparisonOperator, QueryFilter

        col_mock = MagicMock()
        col_mock.like = MagicMock(return_value=True)

        class FakeModel:
            __name__ = "FakeModel"

        FakeModel.name = col_mock
        f = QueryFilter(
            field="name",
            operator=ComparisonOperator.STARTS_WITH,
            value="pre",
        )
        f.to_sql_condition(FakeModel)
        col_mock.like.assert_called_once_with("pre%")

    def test_query_filter_ends_with(self):
        from core.query_builder import ComparisonOperator, QueryFilter

        col_mock = MagicMock()
        col_mock.like = MagicMock(return_value=True)

        class FakeModel:
            __name__ = "FakeModel"

        FakeModel.suffix = col_mock
        f = QueryFilter(
            field="suffix",
            operator=ComparisonOperator.ENDS_WITH,
            value="suf",
        )
        f.to_sql_condition(FakeModel)
        col_mock.like.assert_called_once_with("%suf")

    def test_query_filter_ilike(self):
        from core.query_builder import ComparisonOperator, QueryFilter

        col_mock = MagicMock()
        col_mock.ilike = MagicMock(return_value=True)

        class FakeModel:
            __name__ = "FakeModel"

        FakeModel.text = col_mock
        f = QueryFilter(field="text", operator=ComparisonOperator.ILIKE, value="match")
        f.to_sql_condition(FakeModel)
        col_mock.ilike.assert_called()

    def test_query_filter_between_valid(self):
        from core.query_builder import ComparisonOperator, QueryFilter

        col_mock = MagicMock()
        col_mock.between = MagicMock(return_value=True)

        class FakeModel:
            __name__ = "FakeModel"

        FakeModel.score = col_mock
        f = QueryFilter(
            field="score",
            operator=ComparisonOperator.BETWEEN,
            value=[1, 100],
        )
        f.to_sql_condition(FakeModel)
        col_mock.between.assert_called_once_with(1, 100)


# ======================== 6. REALTIME NOTIFICATION SYSTEM ========================


class TestRealtimeNotificationSystem:
    """Tests for core/realtime_notification_system.py"""

    def test_notification_type_values(self):
        from core.realtime_notification_system import NotificationType

        assert NotificationType.EXAM_STARTED.value == "exam_started"
        assert NotificationType.ACHIEVEMENT_UNLOCKED.value == "achievement_unlocked"
        assert NotificationType.YKS_ANNOUNCEMENT.value == "yks_announcement"

    def test_notification_priority_values(self):
        from core.realtime_notification_system import NotificationPriority

        assert NotificationPriority.LOW.value == "low"
        assert NotificationPriority.URGENT.value == "urgent"

    def test_connection_status_values(self):
        from core.realtime_notification_system import ConnectionStatus

        assert ConnectionStatus.CONNECTED.value == "connected"
        assert ConnectionStatus.DISCONNECTED.value == "disconnected"

    def test_notification_message_auto_id(self):
        from core.realtime_notification_system import (
            NotificationMessage,
            NotificationType,
        )

        msg = NotificationMessage(
            id="",
            type=NotificationType.SYSTEM_ANNOUNCEMENT,
            title="Test",
            message="Hello",
        )
        assert len(msg.id) > 0

    def test_notification_message_to_dict(self):
        from core.realtime_notification_system import (
            NotificationMessage,
            NotificationPriority,
            NotificationType,
        )

        msg = NotificationMessage(
            id="msg-1",
            type=NotificationType.EXAM_COMPLETED,
            title="Exam Done",
            message="Your exam is complete.",
            priority=NotificationPriority.HIGH,
        )
        d = msg.to_dict()
        assert d["type"] == "exam_completed"
        assert d["priority"] == "high"
        assert "created_at" in d

    def test_notification_message_is_expired_no_expiry(self):
        from core.realtime_notification_system import (
            NotificationMessage,
            NotificationType,
        )

        msg = NotificationMessage(
            id="msg-2",
            type=NotificationType.STUDY_STREAK,
            title="Streak!",
            message="7 days!",
        )
        assert msg.is_expired() is False

    def test_notification_message_is_expired_past(self):
        from datetime import UTC

        from core.realtime_notification_system import (
            NotificationMessage,
            NotificationType,
        )

        msg = NotificationMessage(
            id="msg-3",
            type=NotificationType.TYT_REMINDER,
            title="TYT",
            message="Tomorrow!",
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        assert msg.is_expired() is True

    def test_notification_message_is_not_expired_future(self):
        from datetime import UTC

        from core.realtime_notification_system import (
            NotificationMessage,
            NotificationType,
        )

        msg = NotificationMessage(
            id="msg-4",
            type=NotificationType.AYT_REMINDER,
            title="AYT",
            message="Next week",
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        assert msg.is_expired() is False

    def test_notification_message_tags_in_dict(self):
        from core.realtime_notification_system import (
            NotificationMessage,
            NotificationType,
        )

        msg = NotificationMessage(
            id="msg-5",
            type=NotificationType.NEW_CONTENT_AVAILABLE,
            title="New!",
            message="Content",
            tags={"math", "yks"},
        )
        d = msg.to_dict()
        assert set(d["tags"]) == {"math", "yks"}

    def test_websocket_connection_matches_filters_no_filter(self):
        from core.realtime_notification_system import (
            NotificationMessage,
            NotificationType,
            WebSocketConnection,
        )

        conn = WebSocketConnection(
            id="conn-1",
            websocket=None,
            user_id=None,
            session_id=None,
            connected_at=datetime.now(),
            last_ping=datetime.now(),
        )
        msg = NotificationMessage(
            id="m",
            type=NotificationType.SYSTEM_ANNOUNCEMENT,
            title="X",
            message="Y",
        )
        assert conn.matches_filters(msg) is True

    def test_websocket_connection_matches_filters_user_mismatch(self):
        from core.realtime_notification_system import (
            NotificationMessage,
            NotificationType,
            WebSocketConnection,
        )

        conn = WebSocketConnection(
            id="conn-2",
            websocket=None,
            user_id=10,
            session_id=None,
            connected_at=datetime.now(),
            last_ping=datetime.now(),
        )
        msg = NotificationMessage(
            id="m",
            type=NotificationType.EXAM_STARTED,
            title="X",
            message="Y",
            user_id=20,
        )
        assert conn.matches_filters(msg) is False

    def test_websocket_connection_matches_filters_priority(self):
        from core.realtime_notification_system import (
            NotificationMessage,
            NotificationPriority,
            NotificationType,
            WebSocketConnection,
        )

        conn = WebSocketConnection(
            id="conn-3",
            websocket=None,
            user_id=None,
            session_id=None,
            connected_at=datetime.now(),
            last_ping=datetime.now(),
            subscription_filters={"min_priority": "high"},
        )
        low_msg = NotificationMessage(
            id="low",
            type=NotificationType.LESSON_PROGRESS,
            title="X",
            message="Y",
            priority=NotificationPriority.LOW,
        )
        assert conn.matches_filters(low_msg) is False

        high_msg = NotificationMessage(
            id="high",
            type=NotificationType.EXAM_TIME_WARNING,
            title="X",
            message="Y",
            priority=NotificationPriority.URGENT,
        )
        assert conn.matches_filters(high_msg) is True

    def test_websocket_connection_matches_filters_tags(self):
        from core.realtime_notification_system import (
            NotificationMessage,
            NotificationType,
            WebSocketConnection,
        )

        conn = WebSocketConnection(
            id="conn-4",
            websocket=None,
            user_id=None,
            session_id=None,
            connected_at=datetime.now(),
            last_ping=datetime.now(),
            subscription_filters={"tags": ["math", "yks"]},
        )
        msg_no_tag = NotificationMessage(
            id="n",
            type=NotificationType.FRIEND_REQUEST,
            title="X",
            message="Y",
            tags={"social"},
        )
        assert conn.matches_filters(msg_no_tag) is False

        msg_with_tag = NotificationMessage(
            id="m",
            type=NotificationType.FRIEND_REQUEST,
            title="X",
            message="Y",
            tags={"math", "other"},
        )
        assert conn.matches_filters(msg_with_tag) is True

    def test_websocket_manager_init(self):
        from core.realtime_notification_system import WebSocketManager

        mgr = WebSocketManager()
        assert mgr.connections == {}
        assert mgr.running is False
        assert mgr.ping_interval == 30

    @pytest.mark.asyncio
    async def test_websocket_connection_send_message_no_websocket(self):
        from core.realtime_notification_system import WebSocketConnection

        conn = WebSocketConnection(
            id="c1",
            websocket=None,
            user_id=None,
            session_id=None,
            connected_at=datetime.now(),
            last_ping=datetime.now(),
        )
        result = await conn.send_message({"type": "test"})
        assert result is False


# ======================== 7. BACKGROUND JOB PROCESSOR ========================


def _get_real_bjp_module():
    """Load the real background_job_processor module directly, bypassing sys.modules stubs."""
    import importlib.util
    import pathlib

    src = (
        pathlib.Path(__file__).parent.parent.parent
        / "core"
        / "background_job_processor.py"
    )
    spec = importlib.util.spec_from_file_location("_bjp_real", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestBackgroundJobProcessor:
    """Tests for core/background_job_processor.py"""

    @pytest.fixture(autouse=True)
    def _load_module(self):
        self._bjp = _get_real_bjp_module()

    def test_job_priority_values(self):
        assert self._bjp.JobPriority.LOW.value == "low"
        assert self._bjp.JobPriority.CRITICAL.value == "critical"

    def test_retry_policy_values(self):
        assert self._bjp.RetryPolicy.NONE.value == "none"
        assert self._bjp.RetryPolicy.EXPONENTIAL_BACKOFF.value == "exponential_backoff"

    def test_job_definition_calculate_retry_delay_none(self):
        job = self._bjp.JobDefinition(
            name="test",
            function=lambda: None,
            queue_type=_QueueType.BATCH_PROCESSING,
            priority=self._bjp.JobPriority.NORMAL,
            retry_policy=self._bjp.RetryPolicy.NONE,
            retry_delay=60,
        )
        assert job.calculate_retry_delay(1) == 0

    def test_job_definition_calculate_retry_delay_fixed(self):
        job = self._bjp.JobDefinition(
            name="test",
            function=lambda: None,
            queue_type=_QueueType.BATCH_PROCESSING,
            priority=self._bjp.JobPriority.NORMAL,
            retry_policy=self._bjp.RetryPolicy.FIXED_DELAY,
            retry_delay=30,
        )
        assert job.calculate_retry_delay(5) == 30

    @pytest.mark.parametrize(
        "attempt,expected",
        [
            (1, 60),
            (2, 120),
            (3, 180),
        ],
    )
    def test_job_definition_calculate_retry_delay_linear(self, attempt, expected):
        job = self._bjp.JobDefinition(
            name="test",
            function=lambda: None,
            queue_type=_QueueType.BATCH_PROCESSING,
            priority=self._bjp.JobPriority.NORMAL,
            retry_policy=self._bjp.RetryPolicy.LINEAR_BACKOFF,
            retry_delay=60,
        )
        assert job.calculate_retry_delay(attempt) == expected

    @pytest.mark.parametrize(
        "attempt,expected",
        [
            (1, 60),
            (2, 120),
            (3, 240),
        ],
    )
    def test_job_definition_calculate_retry_delay_exponential(self, attempt, expected):
        job = self._bjp.JobDefinition(
            name="test",
            function=lambda: None,
            queue_type=_QueueType.BATCH_PROCESSING,
            priority=self._bjp.JobPriority.NORMAL,
            retry_policy=self._bjp.RetryPolicy.EXPONENTIAL_BACKOFF,
            retry_delay=60,
        )
        assert job.calculate_retry_delay(attempt) == expected

    def test_job_execution_log(self):
        exec_ = self._bjp.JobExecution(
            job_id="j1",
            job_name="my_job",
            started_at=datetime.now(),
        )
        exec_.log("Starting", "info")
        assert len(exec_.logs) == 1
        assert "Starting" in exec_.logs[0]

    def test_job_execution_update_progress(self):
        exec_ = self._bjp.JobExecution(
            job_id="j2",
            job_name="my_job",
            started_at=datetime.now(),
        )
        exec_.update_progress(50, "halfway")
        assert exec_.progress == 50
        assert exec_.status_message == "halfway"

    def test_job_execution_update_progress_clamps(self):
        exec_ = self._bjp.JobExecution(
            job_id="j3",
            job_name="my_job",
            started_at=datetime.now(),
        )
        exec_.update_progress(150)
        assert exec_.progress == 100
        exec_.update_progress(-10)
        assert exec_.progress == 0

    def test_background_job_registry_register_and_get(self):
        registry = self._bjp.BackgroundJobRegistry()
        job_def = registry.register_job(
            name="my_test_job",
            function=lambda: "ok",
            queue_type=_QueueType.BATCH_PROCESSING,
            priority=self._bjp.JobPriority.NORMAL,
            category="test_cat",
        )
        assert job_def.name == "my_test_job"
        fetched = registry.get_job("my_test_job")
        assert fetched is not None

    def test_background_job_registry_get_missing(self):
        registry = self._bjp.BackgroundJobRegistry()
        result = registry.get_job("nonexistent")
        assert result is None

    def test_background_job_registry_list_jobs(self):
        registry = self._bjp.BackgroundJobRegistry()
        registry.register_job(
            name="job_a",
            function=lambda: None,
            queue_type=_QueueType.BATCH_PROCESSING,
            priority=self._bjp.JobPriority.HIGH,
            category="cat_a",
        )
        registry.register_job(
            name="job_b",
            function=lambda: None,
            queue_type=_QueueType.BATCH_PROCESSING,
            priority=self._bjp.JobPriority.LOW,
            category="cat_b",
        )
        all_jobs = registry.list_jobs()
        assert len(all_jobs) == 2

    def test_background_job_registry_list_by_category(self):
        registry = self._bjp.BackgroundJobRegistry()
        registry.register_job(
            name="job_x",
            function=lambda: None,
            queue_type=_QueueType.ANALYTICS,
            priority=self._bjp.JobPriority.NORMAL,
            category="analytics",
        )
        analytics_jobs = registry.list_jobs(category="analytics")
        assert len(analytics_jobs) == 1

    def test_background_job_registry_get_categories(self):
        registry = self._bjp.BackgroundJobRegistry()
        registry.register_job(
            name="j1",
            function=lambda: None,
            queue_type=_QueueType.CLEANUP,
            priority=self._bjp.JobPriority.LOW,
            category="maintenance",
        )
        cats = registry.get_categories()
        assert "maintenance" in cats


# ======================== 8. KVKK COMPLIANCE ========================


class TestKVKKCompliance:
    """Tests for core/kvkk_compliance.py"""

    def test_kvkk_encryption_hash_pii(self):
        from core.kvkk_compliance import KVKKEncryption

        enc = KVKKEncryption(key=None)
        h1 = enc.hash_pii("test@example.com")
        h2 = enc.hash_pii("test@example.com")
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_kvkk_encryption_hash_empty(self):
        from core.kvkk_compliance import KVKKEncryption

        enc = KVKKEncryption(key=None)
        assert enc.hash_pii("") == ""

    def test_kvkk_encryption_fallback_encrypt_decrypt(self):
        from core.kvkk_compliance import KVKKEncryption

        enc = KVKKEncryption(key=None)
        enc._fernet = None  # Force fallback
        encrypted = enc.encrypt_pii("sensitive data")
        assert encrypted.startswith("b64:")
        decrypted = enc.decrypt_pii(encrypted)
        assert decrypted == "sensitive data"

    def test_kvkk_encryption_fallback_empty(self):
        from core.kvkk_compliance import KVKKEncryption

        enc = KVKKEncryption(key=None)
        enc._fernet = None
        assert enc.encrypt_pii("") == ""
        assert enc.decrypt_pii("") == ""

    def test_kvkk_encryption_plain_text_passthrough(self):
        from core.kvkk_compliance import KVKKEncryption

        enc = KVKKEncryption(key=None)
        result = enc.decrypt_pii("plain_text_no_prefix")
        assert result == "plain_text_no_prefix"

    def test_kvkk_encryption_dict_encrypt_decrypt(self):
        from core.kvkk_compliance import KVKKEncryption

        enc = KVKKEncryption(key=None)
        enc._fernet = None
        data = {"email": "user@test.com", "name": "Test User", "age": 25}
        encrypted = enc.encrypt_dict(data, ["email"])
        assert encrypted["email"].startswith("b64:")
        assert encrypted["name"] == "Test User"
        assert encrypted["age"] == 25
        decrypted = enc.decrypt_dict(encrypted, ["email"])
        assert decrypted["email"] == "user@test.com"

    def test_kvkk_encryption_generate_key(self):
        from core.kvkk_compliance import KVKKEncryption

        key = KVKKEncryption.generate_key()
        assert len(key) == 32

    def test_kvkk_encryption_generate_key_base64(self):
        import base64

        from core.kvkk_compliance import KVKKEncryption

        key_b64 = KVKKEncryption.generate_key_base64()
        decoded = base64.urlsafe_b64decode(key_b64)
        assert len(decoded) == 32

    def test_data_processing_purpose_enum(self):
        from core.kvkk_compliance import DataProcessingPurpose

        assert DataProcessingPurpose.EDUCATION.value == "education"
        assert DataProcessingPurpose.MARKETING.value == "marketing"

    def test_consent_type_enum(self):
        from core.kvkk_compliance import ConsentType

        assert ConsentType.EXPLICIT.value == "explicit"
        assert ConsentType.LEGAL_BASIS.value == "legal_basis"

    def test_data_category_enum(self):
        from core.kvkk_compliance import DataCategory

        assert DataCategory.IDENTITY.value == "identity"
        assert DataCategory.BIOMETRIC.value == "biometric"

    def test_data_subject_right_enum(self):
        from core.kvkk_compliance import DataSubjectRight

        assert DataSubjectRight.ERASURE.value == "erasure"
        assert DataSubjectRight.PORTABILITY.value == "portability"

    def test_consent_status_enum(self):
        from core.kvkk_compliance import ConsentStatus

        assert ConsentStatus.GRANTED.value == "granted"
        assert ConsentStatus.WITHDRAWN.value == "withdrawn"

    def test_pii_fields_dict(self):
        from core.kvkk_compliance import PII_FIELDS

        assert "user" in PII_FIELDS
        assert "email" in PII_FIELDS["user"]
        assert "tc_kimlik_no" in PII_FIELDS["user"]

    def test_encrypt_user_pii_convenience(self):
        from core.kvkk_compliance import decrypt_user_pii, encrypt_user_pii

        data = {
            "email": "test@example.com",
            "phone": "555-1234",
            "tc_kimlik_no": "12345678901",
            "full_name": "Test User",
            "address": "Istanbul",
        }
        encrypted = encrypt_user_pii(data)
        assert encrypted["email"] != data["email"] or encrypted["email"].startswith(
            "b64:"
        )
        decrypted = decrypt_user_pii(encrypted)
        assert decrypted["email"] == data["email"]

    def test_get_kvkk_encryption_singleton(self):
        from core.kvkk_compliance import get_kvkk_encryption

        enc1 = get_kvkk_encryption()
        enc2 = get_kvkk_encryption()
        assert enc1 is enc2

    def test_consent_request_model(self):
        from core.kvkk_compliance import (
            ConsentRequest,
            ConsentType,
            DataProcessingPurpose,
        )

        req = ConsentRequest(
            user_id=1,
            purpose=DataProcessingPurpose.EDUCATION,
            consent_text="I agree.",
        )
        assert req.user_id == 1
        assert req.consent_type == ConsentType.EXPLICIT

    def test_data_breach_report_model(self):
        from core.kvkk_compliance import DataBreachReport, DataCategory

        report = DataBreachReport(
            severity="high",
            description="Data leak",
            affected_users_count=100,
            data_categories=[DataCategory.IDENTITY],
            detected_at=datetime.now(),
        )
        assert report.severity == "high"
        assert report.affected_users_count == 100

    def test_data_subject_request_model(self):
        from core.kvkk_compliance import DataSubjectRequestModel, DataSubjectRight

        req = DataSubjectRequestModel(
            user_id=42,
            request_type=DataSubjectRight.ERASURE,
            description="Please delete my data",
        )
        assert req.user_id == 42

    def test_kvkk_encryption_derive_key(self):
        from core.kvkk_compliance import KVKKEncryption

        enc = KVKKEncryption(key=None)
        derived = enc._derive_key(b"test-password")
        assert len(derived) == 32

    def test_kvkk_encryption_with_32byte_key(self):
        import os

        from core.kvkk_compliance import KVKKEncryption

        key = os.urandom(32)
        enc = KVKKEncryption(key=key)
        # Should not raise even if fernet is mocked
        assert enc._key == key
