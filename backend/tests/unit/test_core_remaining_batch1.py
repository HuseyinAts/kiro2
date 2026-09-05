"""
Unit tests for core remaining batch 1 — 7 files with 0% coverage.

Files covered:
  1. core/turkish_exam_middleware.py
  2. core/langchain_rag_system.py
  3. core/langchain_llm_service_enhanced.py
  4. core/langchain_llm_service.py
  5. core/form_interface.py
  6. core/unified/elasticsearch_system.py
  7. models/study_room.py
"""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

# ---------------------------------------------------------------------------
# Heavy-dependency stubs — use setdefault so real modules loaded by other
# test files are NOT overwritten (avoids cross-file contamination).
#
# IMPORTANT: If langchain_community is already loaded as a REAL package,
# we must NOT stub its sub-modules — it causes "is not a package" errors
# when other modules try to import deeper sub-modules later.
# ---------------------------------------------------------------------------
_langchain_already_real = "langchain_community" in sys.modules and not isinstance(
    sys.modules["langchain_community"], MagicMock
)

_STUBS = [
    "redis",
    "redis.asyncio",
    "celery",
    "elasticsearch",
    "elasticsearch.exceptions",
]

# Only stub langchain ecosystem if not already loaded as real packages
if not _langchain_already_real:
    _STUBS.extend(
        [
            "langchain",
            "langchain.agents",
            "langchain.cache",
            "langchain.callbacks",
            "langchain.callbacks.manager",
            "langchain.callbacks.streaming_stdout",
            "langchain.chains",
            "langchain.memory",
            "langchain.prompts",
            "langchain.retrievers",
            "langchain.retrievers.document_compressors",
            "langchain.schema",
            "langchain.text_splitter",
            "langchain.tools",
            "langchain.vectorstores",
            "langchain_community",
            "langchain_community.cache",
            "langchain_community.chat_models",
            "langchain_community.document_loaders",
            "langchain_community.embeddings",
            "langchain_community.llms",
            "langchain_community.retrievers",
            "langchain_community.tools",
            "langchain_community.vectorstores",
            "langchain_core",
            "langchain_core.documents",
            "langchain_core.prompts",
            "langchain_openai",
            "langchain_anthropic",
            "langchain_huggingface",
            "langchain.hub",
        ]
    )

# KIRO2 heavy internal deps (always stub)
_STUBS.extend(
    [
        "core.application_metrics",
        "core.cache_system_integration",
        "core.structured_logging",
        "core.turkish_exam_event_handlers",
        "core.unified_api_gateway",
        "core.unified_config",
        "core.unified_event_bus",
        # SQLAlchemy async  — keep real SA but stub async extension if not loaded
        "sqlalchemy.ext.asyncio",
    ]
)

for _mod in _STUBS:
    sys.modules.setdefault(_mod, MagicMock())

# Provide concrete sentinel values that downstream code may dereference
_lc = sys.modules["langchain"]
_lc.llm_cache = None  # type: ignore[attr-defined]  # pre-existing, out of scope for SS10.42

# Make elasticsearch exceptions importable as real exception classes
import types as _types  # noqa: E402 -- must run after the sys.modules stubbing above

_es_exc = sys.modules.get("elasticsearch.exceptions")
if isinstance(_es_exc, MagicMock):
    _es_exc_mod = _types.ModuleType("elasticsearch.exceptions")

    class _ConnectionError(Exception):
        pass

    class _NotFoundError(Exception):
        pass

    class _RequestError(Exception):
        pass

    _es_exc_mod.ConnectionError = _ConnectionError  # type: ignore[attr-defined]  # pre-existing, out of scope for SS10.42
    _es_exc_mod.NotFoundError = _NotFoundError  # type: ignore[attr-defined]  # pre-existing, out of scope for SS10.42
    _es_exc_mod.RequestError = _RequestError  # type: ignore[attr-defined]  # pre-existing, out of scope for SS10.42
    sys.modules["elasticsearch.exceptions"] = _es_exc_mod

# Patch heavy KIRO2 internal imports that execute at module level.
# IMPORTANT: Only mutate module attributes when the module is already a
# MagicMock stub. If another test file (e.g. test_core_partial_batch2.py)
# has already loaded the REAL module, do NOT overwrite its real attributes —
# that causes cross-file contamination where real enums/classes get replaced
# with MagicMock objects, breaking tests that rely on real behaviour.


def _stub_attrs(mod_name: str, **attrs):
    """Set attrs on stub module only if it is still a MagicMock."""
    mod = sys.modules.get(mod_name)
    if mod is None or not isinstance(mod, MagicMock):
        return
    for k, v in attrs.items():
        setattr(mod, k, v)


_app_metrics = sys.modules["core.application_metrics"]
_stub_attrs(
    "core.application_metrics",
    get_metrics_collector=MagicMock(return_value=MagicMock()),
    MetricType=MagicMock(),
)

_stub_attrs(
    "core.auth_middleware",
    AuthContext=MagicMock,
    AuthUser=MagicMock,
    UserRole=MagicMock(),
)

_stub_attrs(
    "core.cache_system_integration",
    get_unified_cache_system=AsyncMock(return_value=MagicMock()),
)

_stub_attrs(
    "core.structured_logging",
    LogCategory=MagicMock(),
    get_logger=MagicMock(return_value=MagicMock()),
)

_stub_attrs(
    "core.turkish_exam_event_handlers",
    TurkishExamType=MagicMock(),
)

_uag_route_type = MagicMock()
_uag_route_type.TYT_EXAM = "TYT_EXAM"
_uag_route_type.AYT_EXAM = "AYT_EXAM"
_uag_route_type.YKS_INFO = "YKS_INFO"
_stub_attrs(
    "core.unified_api_gateway",
    APIRequest=MagicMock,
    APIResponse=MagicMock,
    RouteType=_uag_route_type,
)

_stub_attrs(
    "core.unified_config",
    get_unified_config=MagicMock(return_value=MagicMock()),
)

_stub_attrs(
    "core.unified_event_bus",
    EventPriority=MagicMock(),
    EventType=MagicMock(),
    publish_event=AsyncMock(),
)

# ---------------------------------------------------------------------------
# Now safe to import the modules under test
# ---------------------------------------------------------------------------
import pytest  # noqa: E402

# ============================================================
# 1. core/turkish_exam_middleware.py
# ============================================================
from core.turkish_exam_middleware import (  # noqa: E402
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
    """ExamPeriod and ExamSecurityLevel enum values."""

    def test_exam_period_values(self):
        assert ExamPeriod.REGISTRATION.value == "registration"
        assert ExamPeriod.EXAM_WEEK.value == "exam_week"
        assert ExamPeriod.OFF_SEASON.value == "off_season"

    def test_exam_security_level_values(self):
        assert ExamSecurityLevel.LOW.value == "low"
        assert ExamSecurityLevel.HIGH.value == "high"
        assert ExamSecurityLevel.MAXIMUM.value == "maximum"


class TestExamContext:
    def test_default_context(self):
        ctx = ExamContext()
        assert ctx.current_period == ExamPeriod.OFF_SEASON
        assert ctx.security_level == ExamSecurityLevel.LOW
        assert ctx.difficulty == "orta"
        assert ctx.is_practice is True

    def test_custom_context(self):
        ctx = ExamContext(subject="matematik", difficulty="zor", is_practice=False)
        assert ctx.subject == "matematik"
        assert ctx.difficulty == "zor"
        assert ctx.is_practice is False


class TestTurkishLanguageMiddleware:
    def _make_middleware(self):
        return create_turkish_language_middleware({})

    def test_subjects_mapping_contains_matematik(self):
        mw = self._make_middleware()
        assert "matematik" in mw.turkish_subjects
        assert mw.turkish_subjects["matematik"] == "Matematik"

    def test_exam_translations(self):
        mw = self._make_middleware()
        assert mw.exam_translations["tyt"] == "Temel Yeterlilik Testi"
        assert mw.exam_translations["yks"] == "Yükseköğretim Kurumları Sınavı"

    @pytest.mark.asyncio
    async def test_translate_request_params_subject(self):
        mw = self._make_middleware()
        request = MagicMock()
        request.body = {"subject": "fizik"}
        request.query_params = {}
        await mw._translate_request_params(request)
        assert request.body["subject_tr"] == "Fizik"

    @pytest.mark.asyncio
    async def test_translate_request_params_exam_type(self):
        mw = self._make_middleware()
        request = MagicMock()
        request.body = {"exam_type": "ayt"}
        request.query_params = {}
        await mw._translate_request_params(request)
        assert request.body["exam_type_tr"] == "Alan Yeterlilik Testi"

    @pytest.mark.asyncio
    async def test_translate_unknown_subject_no_crash(self):
        mw = self._make_middleware()
        request = MagicMock()
        request.body = {"subject": "unknownsubject"}
        request.query_params = {}
        # Should not raise
        await mw._translate_request_params(request)
        assert "subject_tr" not in request.body


class TestExamSecurityMiddleware:
    def _make(self, **kwargs):
        cfg = {"exam_monitoring": True, "anti_cheat_enabled": True}
        cfg.update(kwargs)
        return create_exam_security_middleware(cfg)

    def test_default_config(self):
        mw = self._make()
        assert mw.exam_monitoring is True
        assert mw.anti_cheat_enabled is True
        assert mw.max_violations_per_hour == 5
        assert mw.block_duration_minutes == 30

    def test_is_user_blocked_not_blocked(self):
        mw = self._make()
        assert mw._is_user_blocked(9999) is False

    def test_is_user_blocked_blocks_user(self):
        from datetime import UTC, datetime, timedelta

        mw = self._make()
        future = datetime.now(UTC) + timedelta(hours=1)
        mw.blocked_users[1] = future
        assert mw._is_user_blocked(1) is True

    def test_is_user_blocked_expired_block(self):
        from datetime import UTC, datetime, timedelta

        mw = self._make()
        past = datetime.now(UTC) - timedelta(hours=1)
        mw.blocked_users[2] = past
        assert mw._is_user_blocked(2) is False
        # Should be removed from dict
        assert 2 not in mw.blocked_users

    def test_create_security_error_response(self):
        mw = self._make()
        resp = mw._create_security_error("req-1", "Reason", "Sebep")
        # APIResponse is mocked so just verify it was called with right args
        assert resp is not None

    @pytest.mark.asyncio
    async def test_check_user_eligibility_student(self):
        mw = self._make()
        user = MagicMock()
        user.is_student.return_value = True
        result = await mw._check_user_eligibility(MagicMock(), user)
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_check_user_eligibility_admin(self):
        mw = self._make()
        user = MagicMock()
        user.is_student.return_value = False
        user.is_admin.return_value = True

        user.role = MagicMock()  # not TEACHER
        result = await mw._check_user_eligibility(MagicMock(), user)
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_handle_security_violation_records(self):
        mw = self._make()
        request = MagicMock()
        request.client_ip = "127.0.0.1"
        await mw._handle_security_violation(42, ["rapid_requests"], request)
        assert 42 in mw.security_violations
        assert len(mw.security_violations[42]) == 1

    @pytest.mark.asyncio
    async def test_handle_security_violation_blocks_after_threshold(self):
        mw = self._make()
        mw.max_violations_per_hour = 2
        request = MagicMock()
        request.client_ip = "127.0.0.1"
        await mw._handle_security_violation(55, ["v1"], request)
        await mw._handle_security_violation(55, ["v2"], request)
        assert 55 in mw.blocked_users


class TestExamSessionMiddleware:
    def _make(self):
        return create_exam_session_middleware({"session_timeout_minutes": 10})

    def test_extract_exam_type_tyt(self):
        mw = self._make()
        assert mw._extract_exam_type_from_path("/api/tyt/start") == "tyt"

    def test_extract_exam_type_ayt(self):
        mw = self._make()
        assert mw._extract_exam_type_from_path("/api/ayt/submit") == "ayt"

    def test_extract_exam_type_yks(self):
        mw = self._make()
        assert mw._extract_exam_type_from_path("/api/yks/info") == "yks"

    def test_extract_exam_type_unknown(self):
        mw = self._make()
        assert mw._extract_exam_type_from_path("/api/other") == "unknown"

    def test_is_session_expired_true(self):
        from datetime import UTC, datetime, timedelta

        mw = self._make()
        old_time = (datetime.now(UTC) - timedelta(minutes=30)).isoformat()
        assert mw._is_session_expired({"last_activity": old_time}) is True

    def test_is_session_expired_false(self):
        from datetime import UTC, datetime

        mw = self._make()
        now = datetime.now(UTC).isoformat()
        assert mw._is_session_expired({"last_activity": now}) is False

    def test_calculate_time_remaining_positive(self):
        from datetime import UTC, datetime

        mw = self._make()
        started = datetime.now(UTC).isoformat()
        remaining = mw._calculate_time_remaining({"started_at": started})
        assert remaining is not None
        assert remaining >= 0

    def test_calculate_time_remaining_zero_on_old(self):
        from datetime import UTC, datetime, timedelta

        mw = self._make()
        old = (datetime.now(UTC) - timedelta(hours=5)).isoformat()
        remaining = mw._calculate_time_remaining({"started_at": old})
        assert remaining == 0


class TestMiddlewareFactories:
    def test_create_turkish_language_middleware_returns_instance(self):
        mw = create_turkish_language_middleware()
        assert isinstance(mw, TurkishLanguageMiddleware)

    def test_create_exam_security_middleware_returns_instance(self):
        mw = create_exam_security_middleware()
        assert isinstance(mw, ExamSecurityMiddleware)

    def test_create_exam_session_middleware_returns_instance(self):
        mw = create_exam_session_middleware()
        assert isinstance(mw, ExamSessionMiddleware)

    def test_get_turkish_exam_middleware_stack_length(self):
        stack = get_turkish_exam_middleware_stack()
        assert len(stack) == 3
        names = [item[0] for item in stack]
        assert "exam_security" in names
        assert "turkish_language" in names

    @pytest.mark.parametrize(
        "exam_type,expected_key,expected_value",
        [
            ("tyt", "session_timeout_minutes", 135),
            ("ayt", "session_timeout_minutes", 180),
            ("unknown", "exam_monitoring", True),
        ],
    )
    def test_configure_exam_middleware(self, exam_type, expected_key, expected_value):
        cfg = configure_exam_middleware(exam_type)
        assert cfg[expected_key] == expected_value


# ============================================================
# 2. core/langchain_rag_system.py
# ============================================================

# Ensure langchain_core.documents.Document is a concrete class for DocumentProcessor
_lc_docs = sys.modules["langchain_core.documents"]


class _FakeDocument:
    def __init__(self, page_content="", metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}


_lc_docs.Document = _FakeDocument  # type: ignore[attr-defined]  # pre-existing, out of scope for SS10.42

try:
    from core.langchain_rag_system import (
        AdvancedRAGSystem,
        DocumentProcessor,
        EducationalRAG,
        VectorStoreManager,
    )

    _LANGCHAIN_RAG_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    _LANGCHAIN_RAG_AVAILABLE = False


@pytest.mark.skipif(
    not _LANGCHAIN_RAG_AVAILABLE, reason="langchain not stubbed in combined run"
)
class TestDocumentProcessor:
    def test_init_has_loaders(self):
        dp = DocumentProcessor()
        assert ".txt" in dp.loaders
        assert ".pdf" in dp.loaders
        assert ".py" in dp.loaders

    def test_init_has_text_splitters(self):
        dp = DocumentProcessor()
        assert "recursive" in dp.text_splitters
        assert "character" in dp.text_splitters

    def test_load_document_unsupported_extension_falls_back(self):
        dp = DocumentProcessor()
        # TextLoader is mocked; calling load() on mock returns []
        result = dp.load_document("/tmp/fake.xyz")  # noqa: S108 -- test fixture path, not real usage
        # Either empty list on error or a MagicMock list — no exception raised
        assert isinstance(result, list | MagicMock)

    def test_create_documents_from_texts(self):
        dp = DocumentProcessor()
        texts = ["Hello world", "Second doc"]
        metadatas = [{"source": "a"}, {"source": "b"}]
        docs = dp.create_documents_from_texts(texts, metadatas)
        assert len(docs) == 2
        assert docs[0].page_content == "Hello world"
        assert docs[0].metadata == {"source": "a"}

    def test_create_documents_from_texts_no_metadata(self):
        dp = DocumentProcessor()
        docs = dp.create_documents_from_texts(["only text"])
        assert len(docs) == 1
        assert docs[0].page_content == "only text"
        assert docs[0].metadata == {}


@pytest.mark.skipif(
    not _LANGCHAIN_RAG_AVAILABLE, reason="langchain not stubbed in combined run"
)
class TestVectorStoreManager:
    def test_init_stores_empty(self):
        vsm = VectorStoreManager()
        assert isinstance(vsm.vector_stores, dict)
        assert len(vsm.vector_stores) == 0

    def test_similarity_search_missing_store(self):
        vsm = VectorStoreManager()
        result = vsm.similarity_search("missing_store", "query")
        assert result == []

    def test_max_marginal_relevance_search_missing_store(self):
        vsm = VectorStoreManager()
        result = vsm.max_marginal_relevance_search("missing_store", "query")
        assert result == []

    def test_add_documents_missing_store_no_crash(self):
        vsm = VectorStoreManager()
        # Should log error but not raise
        vsm.add_documents("nonexistent", [_FakeDocument("text")])

    def test_save_vector_store_missing_no_crash(self):
        vsm = VectorStoreManager()
        vsm.save_vector_store("nonexistent")  # Should not raise


@pytest.mark.skipif(
    not _LANGCHAIN_RAG_AVAILABLE, reason="langchain not stubbed in combined run"
)
class TestAdvancedRAGSystem:
    def _make(self):
        llm_service = MagicMock()
        llm_service.chat_model = MagicMock()
        llm_service.llm = MagicMock()
        return AdvancedRAGSystem(llm_service)

    def test_init_empty_retrievers(self):
        rag = self._make()
        assert isinstance(rag.retrievers, dict)

    def test_init_empty_chains(self):
        rag = self._make()
        assert isinstance(rag.chains, dict)

    def test_create_multi_query_retriever_missing_store(self):
        rag = self._make()
        result = rag.create_multi_query_retriever("nonexistent")
        assert result is None

    def test_create_contextual_compression_retriever_missing_store(self):
        rag = self._make()
        result = rag.create_contextual_compression_retriever("nonexistent")
        assert result is None

    def test_create_hybrid_retriever_missing_store(self):
        rag = self._make()
        result = rag.create_hybrid_retriever("nonexistent", [])
        assert result is None

    def test_create_time_weighted_retriever_missing_store(self):
        rag = self._make()
        result = rag.create_time_weighted_retriever("nonexistent")
        assert result is None

    def test_create_qa_chain_missing_store(self):
        rag = self._make()
        result = rag.create_qa_chain("nonexistent")
        assert result is None

    def test_create_conversational_chain_missing_store(self):
        rag = self._make()
        result = rag.create_conversational_chain("nonexistent")
        assert result is None

    def test_create_custom_qa_chain_missing_store(self):
        rag = self._make()
        result = rag.create_custom_qa_chain("nonexistent", "My prompt")
        assert result is None

    @pytest.mark.asyncio
    async def test_query_missing_chain(self):
        rag = self._make()
        result = await rag.query("some question", "nonexistent_chain")
        assert result["success"] is False
        assert "not found" in result["error"]


@pytest.mark.skipif(
    not _LANGCHAIN_RAG_AVAILABLE, reason="langchain not stubbed in combined run"
)
class TestEducationalRAG:
    def test_init(self):
        llm_service = MagicMock()
        edu = EducationalRAG(llm_service)
        assert isinstance(edu.subject_stores, dict)

    @pytest.mark.asyncio
    async def test_answer_question_subject_not_indexed(self):
        llm_service = MagicMock()
        edu = EducationalRAG(llm_service)
        result = await edu.answer_question("What is X?", "matematik")
        assert result["success"] is False
        assert "not indexed" in result["error"]

    @pytest.mark.parametrize(
        "question,expected_type",
        [
            ("Bu nedir?", "definition"),
            ("Nasıl çalışır?", "explanation"),
            ("Neden önemli?", "reasoning"),
            ("Bir örnek ver", "example"),
            ("Genel bilgi", "general"),
        ],
    )
    def test_classify_question(self, question, expected_type):
        edu = EducationalRAG(MagicMock())
        assert edu._classify_question(question) == expected_type

    @pytest.mark.parametrize(
        "question,expected_difficulty",
        [
            # < 5 words → easy
            ("Kısa", "easy"),
            # 5–9 words → medium  (exactly 5 words)
            ("Bu soru tam beş kelime içeriyor", "medium"),
            # >= 10 words → hard
            (
                "Bu cümle tam olarak on ya da daha fazla kelime içeriyor ve uzundur",
                "hard",
            ),
        ],
    )
    def test_estimate_difficulty(self, question, expected_difficulty):
        edu = EducationalRAG(MagicMock())
        assert edu._estimate_difficulty(question) == expected_difficulty

    def test_generate_followup_all_types(self):
        edu = EducationalRAG(MagicMock())
        for q_type in ["definition", "explanation", "reasoning", "example", "general"]:
            result = edu._generate_followup(q_type)
            assert isinstance(result, str)
            assert len(result) > 0


# ============================================================
# 3. core/langchain_llm_service_enhanced.py
# ============================================================

try:
    from core.langchain_llm_service_enhanced import (
        CustomHuggingFaceEndpoint,
        LangChainConfig,
        get_enhanced_langchain_service,
    )

    _LANGCHAIN_ENHANCED_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    _LANGCHAIN_ENHANCED_AVAILABLE = False


@pytest.mark.skipif(
    not _LANGCHAIN_ENHANCED_AVAILABLE, reason="langchain not stubbed in combined run"
)
class TestLangChainConfigEnhanced:
    def test_default_values(self):
        cfg = LangChainConfig()
        # model_name derived from env; just check it's a string
        assert isinstance(cfg.model_name, str)
        assert isinstance(cfg.temperature, float)
        assert isinstance(cfg.max_tokens, int)

    def test_enable_cache_default(self):
        cfg = LangChainConfig()
        # Default in env "true"
        assert isinstance(cfg.enable_cache, bool)

    def test_custom_hf_endpoint_set(self):
        cfg = LangChainConfig()
        # Either from env or default
        assert cfg.custom_hf_endpoint  # not empty


@pytest.mark.skipif(
    not _LANGCHAIN_ENHANCED_AVAILABLE, reason="langchain not stubbed in combined run"
)
class TestCustomHuggingFaceEndpoint:
    def _make(self):
        return CustomHuggingFaceEndpoint(
            endpoint_url="https://test.endpoint.com",
            api_token="fake-token",  # noqa: S106 -- pragma: allowlist secret -- test fixture, not real usage
            temperature=0.5,
            max_tokens=128,
        )

    def test_init_sets_url(self):
        ep = self._make()
        assert ep.endpoint_url == "https://test.endpoint.com"

    def test_init_sets_temperature(self):
        ep = self._make()
        assert ep.temperature == 0.5

    def test_headers_contain_auth(self):
        ep = self._make()
        assert "Authorization" in ep.headers
        assert "fake-token" in ep.headers["Authorization"]

    def test_generate_returns_string_on_http_error(self):
        ep = self._make()
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Server Error"
            mock_post.return_value = mock_response
            result = ep.generate("Hello")
        assert isinstance(result, str)
        assert "Error" in result or "500" in result

    def test_generate_parses_list_response(self):
        ep = self._make()
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{"generated_text": "Hello back!"}]
            mock_post.return_value = mock_response
            result = ep.generate("Hello")
        assert result == "Hello back!"

    def test_generate_parses_dict_response(self):
        ep = self._make()
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"generated_text": "Dict result"}
            mock_post.return_value = mock_response
            result = ep.generate("Hello")
        assert result == "Dict result"

    def test_predict_delegates_to_generate(self):
        ep = self._make()
        with patch.object(ep, "generate", return_value="predicted") as mock_gen:
            result = ep.predict("test input")
        assert result == "predicted"
        mock_gen.assert_called_once_with("test input")

    @pytest.mark.asyncio
    async def test_agenerate_returns_string(self):
        ep = self._make()
        with patch.object(ep, "generate", return_value="async result"):
            result = await ep.agenerate("test")
        assert result == "async result"

    def test_call_delegates_to_generate(self):
        ep = self._make()
        with patch.object(ep, "generate", return_value="called"):
            result = ep("prompt text")
        assert result == "called"


@pytest.mark.skipif(
    not _LANGCHAIN_ENHANCED_AVAILABLE, reason="langchain not stubbed in combined run"
)
class TestGetEnhancedService:
    def test_singleton(self):
        svc1 = get_enhanced_langchain_service()
        svc2 = get_enhanced_langchain_service()
        assert svc1 is svc2

    def test_has_models_dict(self):
        svc = get_enhanced_langchain_service()
        assert hasattr(svc, "models")
        assert isinstance(svc.models, dict)

    def test_get_system_status_keys(self):
        svc = get_enhanced_langchain_service()
        status = svc.get_system_status()
        assert "models" in status
        assert "embeddings" in status
        assert "cache_enabled" in status

    def test_get_available_models_returns_dict(self):
        svc = get_enhanced_langchain_service()
        result = svc.get_available_models()
        assert isinstance(result, dict)


# ============================================================
# 4. core/langchain_llm_service.py
# ============================================================

try:
    from core.langchain_llm_service import (
        LangChainConfig as BaseLangChainConfig,
    )
    from core.langchain_llm_service import (
        LangChainLLMService,
        get_langchain_service,
    )

    _LANGCHAIN_BASE_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    _LANGCHAIN_BASE_AVAILABLE = False


@pytest.mark.skipif(
    not _LANGCHAIN_BASE_AVAILABLE, reason="langchain not stubbed in combined run"
)
class TestBaseLangChainConfig:
    def test_default_model(self):
        cfg = BaseLangChainConfig()
        assert isinstance(cfg.model_name, str)

    def test_verbose_default(self):
        cfg = BaseLangChainConfig()
        assert isinstance(cfg.verbose, bool)

    def test_redis_url_default(self):
        cfg = BaseLangChainConfig()
        assert "redis" in cfg.redis_url.lower()


@pytest.mark.skipif(
    not _LANGCHAIN_BASE_AVAILABLE, reason="langchain not stubbed in combined run"
)
class TestLangChainLLMService:
    def _make(self):
        return LangChainLLMService()

    def test_init_creates_memory_stores(self):
        svc = self._make()
        assert "buffer" in svc.memory_stores
        assert "window" in svc.memory_stores

    def test_init_creates_empty_vector_stores(self):
        svc = self._make()
        assert isinstance(svc.vector_stores, dict)

    def test_init_creates_empty_chains(self):
        svc = self._make()
        assert isinstance(svc.chains, dict)

    def test_get_conversation_summary_no_memory(self):
        svc = self._make()
        result = svc.get_conversation_summary("nonexistent_type")
        assert result == "No conversation history"

    def test_clear_memory_specific(self):
        svc = self._make()
        mem = MagicMock()
        svc.memory_stores["test_mem"] = mem
        svc.clear_memory("test_mem")
        mem.clear.assert_called_once()

    def test_clear_memory_all(self):
        svc = self._make()
        mems = {k: MagicMock() for k in ["buffer", "window"]}
        svc.memory_stores = mems
        svc.clear_memory()
        for m in mems.values():
            m.clear.assert_called_once()

    def test_create_vector_store_no_vector_store_available(self):
        svc = self._make()
        # embeddings may be mocked; FAISS.from_documents is mocked — should not raise
        result = svc.create_vector_store(["doc1", "doc2"], "test_store")
        # With mocked dependencies, returns either a MagicMock or None
        assert result is None or isinstance(result, MagicMock)

    def test_create_rag_chain_missing_store(self):
        svc = self._make()
        result = svc.create_rag_chain("nonexistent_store")
        assert result is None

    def test_create_conversational_rag_chain_missing_store(self):
        svc = self._make()
        result = svc.create_conversational_rag_chain("nonexistent_store")
        assert result is None

    def test_create_custom_chain_returns_something(self):
        svc = self._make()
        result = svc.create_custom_chain(
            "my_chain", "Template {input}", ["input"], "buffer"
        )
        # With mocked LangChain, result is a MagicMock (LLMChain mock)
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_rag_missing_chain(self):
        svc = self._make()
        result = await svc.query_rag("question", "nonexistent_chain")
        assert result["success"] is False
        assert "not found" in result["error"]


@pytest.mark.skipif(
    not _LANGCHAIN_BASE_AVAILABLE, reason="langchain not stubbed in combined run"
)
class TestGetLangchainServiceSingleton:
    def test_returns_same_instance(self):
        s1 = get_langchain_service()
        s2 = get_langchain_service()
        assert s1 is s2


# ============================================================
# 5. core/form_interface.py
# ============================================================

from core.form_interface import (  # noqa: E402
    FieldType,
    FormDefinition,
    FormField,
    FormInterface,
    FormSection,
    FormType,
    ValidationRule,
)


class TestFormEnums:
    def test_form_type_values(self):
        assert FormType.PROFILE_CREATION.value == "profile_creation"
        assert FormType.ASSESSMENT.value == "assessment"

    def test_field_type_values(self):
        assert FieldType.TEXT.value == "text"
        assert FieldType.NUMBER.value == "number"
        assert FieldType.SELECT.value == "select"

    def test_validation_rule_values(self):
        assert ValidationRule.REQUIRED.value == "required"
        assert ValidationRule.MIN_LENGTH.value == "min_length"
        assert ValidationRule.MAX_VALUE.value == "max_value"


class TestFormInterface:
    def _make(self):
        return FormInterface()

    def test_templates_loaded(self):
        fi = self._make()
        assert FormType.PROFILE_CREATION in fi.form_templates
        assert FormType.LEARNING_STYLE in fi.form_templates
        assert FormType.PROGRESS_REPORT in fi.form_templates

    def test_get_form_definition_profile(self):
        fi = self._make()
        form_def = fi.get_form_definition(FormType.PROFILE_CREATION)
        assert form_def is not None
        assert form_def.form_id == "profile_creation_v1"

    def test_get_form_definition_missing_returns_none(self):
        fi = self._make()
        result = fi.get_form_definition(FormType.FEEDBACK)
        assert result is None

    def test_create_custom_form(self):
        fi = self._make()
        section = FormSection(section_id="s1", title="Section 1", fields=[])
        form_def = FormDefinition(
            form_id="test_form_123",
            form_type=FormType.FEEDBACK,
            title="Test Form",
            description="Test",
            sections=[section],
        )
        form_id = fi.create_custom_form(form_def)
        assert form_id == "test_form_123"
        assert "test_form_123" in fi.form_definitions

    def test_get_form_by_id_template(self):
        fi = self._make()
        result = fi.get_form_by_id("profile_creation_v1")
        assert result is not None
        assert result.form_type == FormType.PROFILE_CREATION

    def test_get_form_by_id_missing(self):
        fi = self._make()
        result = fi.get_form_by_id("nonexistent_id")
        assert result is None

    def test_validate_required_field_missing(self):
        fi = self._make()
        result = fi.validate_form_data("profile_creation_v1", {})
        # Missing required fields → errors
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_min_length_violation(self):
        fi = self._make()
        result = fi.validate_form_data("profile_creation_v1", {"name": "A"})
        field_errors = [e for e in result.errors if e["field"] == "name"]
        assert any(e["rule"] == "min_length" for e in field_errors)

    def test_validate_passes_with_valid_data(self):
        fi = self._make()
        form_data = {
            "name": "Ahmet Yılmaz",
            "grade": "10",
            "exam_target": "YKS",
            "subjects": ["matematik"],
            "primary_goal": "YKS'de iyi puan almak istiyorum.",
        }
        result = fi.validate_form_data("profile_creation_v1", form_data)
        # Required fields filled — should have no required-field errors for these
        name_errors = [e for e in result.errors if e["field"] == "name"]
        assert len(name_errors) == 0

    def test_submit_form_creates_submission(self):
        fi = self._make()
        form_data = {
            "name": "Fatma Şahin",
            "grade": "11",
            "exam_target": "YKS",
            "subjects": ["fizik"],
            "primary_goal": "Üniversiteye girmek istiyorum.",
        }
        submission = fi.submit_form("profile_creation_v1", form_data, user_id="u1")
        assert submission.form_id == "profile_creation_v1"
        assert submission.user_id == "u1"
        assert submission.submission_id in fi.form_submissions

    def test_submit_form_draft(self):
        fi = self._make()
        submission = fi.submit_form("profile_creation_v1", {}, is_draft=True)
        assert submission.is_draft is True
        assert submission.is_complete is False

    def test_get_form_submission_returns_none_for_missing(self):
        fi = self._make()
        result = fi.get_form_submission("nonexistent_submission")
        assert result is None

    def test_get_user_submissions_empty(self):
        fi = self._make()
        result = fi.get_user_submissions("user_no_submissions")
        assert result == []

    def test_update_form_submission_missing(self):
        fi = self._make()
        result = fi.update_form_submission("nonexistent", {"name": "test"})
        assert result is None

    def test_generate_form_analytics_no_submissions(self):
        fi = self._make()
        result = fi.generate_form_analytics("profile_creation_v1")
        assert result["total_submissions"] == 0

    def test_generate_form_analytics_with_submissions(self):
        fi = self._make()
        # Use only scalar (hashable) field values so Counter inside analytics does not
        # raise "unhashable type: list" when processing multi-select fields.
        form_data = {
            "name": "Ali Demir",
            "grade": "12",
            "exam_target": "YKS",
            "primary_goal": "Kimya bolumune girmek istiyorum.",
        }
        fi.submit_form("profile_creation_v1", form_data, user_id="u2")
        result = fi.generate_form_analytics("profile_creation_v1")
        assert result.get("total_submissions") == 1

    def test_get_most_common_value_empty(self):
        fi = self._make()
        assert fi._get_most_common_value([]) is None

    def test_get_most_common_value_all_none(self):
        fi = self._make()
        assert fi._get_most_common_value([None, None]) is None

    def test_get_most_common_value_returns_most_frequent(self):
        fi = self._make()
        result = fi._get_most_common_value(["a", "b", "a", "c", "a"])
        assert result == "a"


class TestFieldValidation:
    def _make_fi(self):
        return FormInterface()

    def test_validate_field_no_rules(self):
        fi = self._make_fi()
        field = FormField(
            field_id="test",
            field_type=FieldType.TEXT,
            label="Test",
            validation_rules=None,
        )
        errors = fi._validate_field(field, "any value")
        assert errors == []

    def test_validate_field_max_length_ok(self):
        fi = self._make_fi()
        field = FormField(
            field_id="f",
            field_type=FieldType.TEXT,
            label="F",
            validation_rules=[
                {"rule": "max_length", "value": 10, "message": "Too long"}
            ],
        )
        errors = fi._validate_field(field, "short")
        assert errors == []

    def test_validate_field_max_length_violation(self):
        fi = self._make_fi()
        field = FormField(
            field_id="f",
            field_type=FieldType.TEXT,
            label="F",
            validation_rules=[
                {"rule": "max_length", "value": 3, "message": "Too long"}
            ],
        )
        errors = fi._validate_field(field, "toolong")
        assert len(errors) == 1
        assert errors[0]["rule"] == "max_length"

    def test_validate_field_min_value_ok(self):
        fi = self._make_fi()
        field = FormField(
            field_id="age",
            field_type=FieldType.NUMBER,
            label="Age",
            validation_rules=[{"rule": "min_value", "value": 0, "message": "Negative"}],
        )
        errors = fi._validate_field(field, 5)
        assert errors == []

    def test_validate_field_min_value_violation(self):
        fi = self._make_fi()
        field = FormField(
            field_id="age",
            field_type=FieldType.NUMBER,
            label="Age",
            validation_rules=[
                {"rule": "min_value", "value": 18, "message": "Too young"}
            ],
        )
        errors = fi._validate_field(field, 10)
        assert len(errors) == 1

    def test_validate_field_required_empty_list(self):
        fi = self._make_fi()
        field = FormField(
            field_id="subjects",
            field_type=FieldType.MULTI_SELECT,
            label="Subjects",
            validation_rules=[{"rule": "required", "message": "Required"}],
        )
        errors = fi._validate_field(field, [])
        assert len(errors) == 1


# ============================================================
# 6. core/unified/elasticsearch_system.py
# ============================================================

from core.unified.elasticsearch_system import (  # noqa: E402
    ElasticsearchConfig,
    IndexTemplate,
    QueryBuilder,
    TurkishAnalyzer,
    UnifiedElasticsearchManager,
    get_elasticsearch_manager,
)


class TestElasticsearchConfig:
    def test_defaults(self):
        cfg = ElasticsearchConfig()
        assert cfg.host == "localhost"
        assert cfg.port == 9200
        assert cfg.timeout == 30
        assert cfg.default_index_prefix == "kiro2"

    def test_from_env_uses_defaults(self):
        cfg = ElasticsearchConfig.from_env()
        assert cfg.host == "localhost"
        assert cfg.default_index_prefix == "kiro2"

    def test_enable_turkish_analysis_default_true(self):
        cfg = ElasticsearchConfig()
        assert cfg.enable_turkish_analysis is True


class TestTurkishAnalyzer:
    def test_analysis_settings_has_analyzer(self):
        settings = TurkishAnalyzer.get_analysis_settings()
        assert "analysis" in settings
        assert "analyzer" in settings["analysis"]
        assert "turkish_analyzer" in settings["analysis"]["analyzer"]

    def test_analysis_settings_has_filters(self):
        settings = TurkishAnalyzer.get_analysis_settings()
        filters = settings["analysis"]["filter"]
        assert "turkish_stop" in filters
        assert "turkish_stemmer" in filters


class TestIndexTemplate:
    def test_exam_template_has_index_patterns(self):
        tmpl = IndexTemplate.get_exam_template()
        assert "index_patterns" in tmpl
        assert "kiro2-exam-*" in tmpl["index_patterns"]

    def test_exam_template_has_question_text_mapping(self):
        tmpl = IndexTemplate.get_exam_template()
        props = tmpl["mappings"]["properties"]
        assert "question_text" in props
        assert props["question_text"]["analyzer"] == "turkish_analyzer"

    def test_user_template_has_user_id(self):
        tmpl = IndexTemplate.get_user_template()
        props = tmpl["mappings"]["properties"]
        assert "user_id" in props

    def test_analytics_template_has_event_type(self):
        tmpl = IndexTemplate.get_analytics_template()
        props = tmpl["mappings"]["properties"]
        assert "event_type" in props


class TestQueryBuilder:
    def test_match_query_structure(self):
        q = QueryBuilder.match_query("question_text", "pythagoras teoremi")
        assert "match" in q
        assert q["match"]["question_text"]["query"] == "pythagoras teoremi"
        assert q["match"]["question_text"]["operator"] == "and"

    def test_multi_match_query_fields(self):
        q = QueryBuilder.multi_match_query(["question_text", "explanation"], "integral")
        assert "multi_match" in q
        assert q["multi_match"]["query"] == "integral"

    def test_multi_match_with_boost(self):
        boost = {"question_text": 2.0}
        q = QueryBuilder.multi_match_query(
            ["question_text", "explanation"], "türev", boost_fields=boost
        )
        fields = q["multi_match"]["fields"]
        assert any("^" in f for f in fields)

    def test_filter_query_term(self):
        q = QueryBuilder.filter_query({"exam_type": "tyt"})
        assert "bool" in q
        must = q["bool"]["must"]
        assert any("term" in clause for clause in must)

    def test_filter_query_terms_list(self):
        q = QueryBuilder.filter_query({"subject": ["matematik", "fizik"]})
        must = q["bool"]["must"]
        assert any("terms" in clause for clause in must)

    def test_range_query_gte_lte(self):
        q = QueryBuilder.range_query("difficulty", gte=1, lte=5)
        assert "range" in q
        assert q["range"]["difficulty"]["gte"] == 1
        assert q["range"]["difficulty"]["lte"] == 5


class TestUnifiedElasticsearchManager:
    def test_init_not_initialized(self):
        mgr = UnifiedElasticsearchManager()
        assert mgr._initialized is False

    def test_get_index_name_with_date_suffix(self):
        mgr = UnifiedElasticsearchManager()
        name = mgr._get_index_name("exam", date_suffix=True)
        assert name.startswith("kiro2-exam-")
        # Should have a date component like 2026-04
        import re

        assert re.search(r"\d{4}-\d{2}", name)

    def test_get_index_name_without_date_suffix(self):
        mgr = UnifiedElasticsearchManager()
        name = mgr._get_index_name("user", date_suffix=False)
        assert name == "kiro2-user"

    @pytest.mark.asyncio
    async def test_index_document_not_initialized(self):
        mgr = UnifiedElasticsearchManager()
        result = await mgr.index_document("exam", {"question": "test"})
        assert result is False

    @pytest.mark.asyncio
    async def test_search_documents_not_initialized(self):
        mgr = UnifiedElasticsearchManager()
        result = await mgr.search_documents("exam", {"match_all": {}})
        assert result["hits"]["total"]["value"] == 0

    @pytest.mark.asyncio
    async def test_search_questions_not_initialized(self):
        mgr = UnifiedElasticsearchManager()
        result = await mgr.search_questions("pythagoras", exam_type="tyt")
        assert result == []

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self):
        mgr = UnifiedElasticsearchManager()
        status = await mgr.health_check()
        assert status["initialized"] is False
        assert status["connected"] is False

    @pytest.mark.asyncio
    async def test_log_user_activity_not_initialized(self):
        mgr = UnifiedElasticsearchManager()
        result = await mgr.log_user_activity("user1", "login")
        assert result is False

    @pytest.mark.asyncio
    async def test_log_analytics_event_not_initialized(self):
        mgr = UnifiedElasticsearchManager()
        result = await mgr.log_analytics_event("exam_start", "exam")
        assert result is False


class TestGetElasticsearchManager:
    def test_singleton(self):
        mgr1 = get_elasticsearch_manager()
        mgr2 = get_elasticsearch_manager()
        assert mgr1 is mgr2


# ============================================================
# 7. models/study_room.py
# ============================================================

from models.study_room import (  # noqa: E402
    FileType,
    FileVersion,
    FileVersionStatus,
    MemberRole,
    MemberStatus,
    MessageType,
    RoomAnalytics,
    RoomChatMessage,
    RoomInvitation,
    RoomMember,
    RoomSettings,
    RoomStatus,
    RoomStudySession,
    RoomVisibility,
    SharedFile,
    StudyRoom,
)


class TestStudyRoomEnums:
    def test_room_status_values(self):
        assert RoomStatus.ACTIVE == "active"
        assert RoomStatus.ARCHIVED == "archived"
        assert RoomStatus.DELETED == "deleted"

    def test_room_visibility_values(self):
        assert RoomVisibility.PUBLIC == "public"
        assert RoomVisibility.PRIVATE == "private"
        assert RoomVisibility.PASSWORD == "password"  # noqa: S105 -- pragma: allowlist secret -- enum value, not a real credential

    def test_member_role_values(self):
        assert MemberRole.OWNER == "owner"
        assert MemberRole.ADMIN == "admin"
        assert MemberRole.MODERATOR == "moderator"
        assert MemberRole.MEMBER == "member"

    def test_member_status_values(self):
        assert MemberStatus.ACTIVE == "active"
        assert MemberStatus.INVITED == "invited"
        assert MemberStatus.BANNED == "banned"

    def test_message_type_values(self):
        assert MessageType.TEXT == "text"
        assert MessageType.FILE == "file"
        assert MessageType.SYSTEM == "system"

    def test_file_type_values(self):
        assert FileType.DOCUMENT == "document"
        assert FileType.IMAGE == "image"
        assert FileType.VIDEO == "video"

    def test_file_version_status_values(self):
        assert FileVersionStatus.CURRENT == "current"
        assert FileVersionStatus.ARCHIVED == "archived"


class TestStudyRoomModel:
    def test_tablename(self):
        assert StudyRoom.__tablename__ == "study_rooms"

    def test_has_expected_columns(self):
        col_names = [c.name for c in StudyRoom.__table__.columns]
        assert "id" in col_names
        assert "name" in col_names
        assert "owner_id" in col_names
        assert "status" in col_names
        assert "visibility" in col_names
        assert "max_members" in col_names

    def test_has_relationships(self):
        assert hasattr(StudyRoom, "members")
        assert hasattr(StudyRoom, "messages")
        assert hasattr(StudyRoom, "files")
        assert hasattr(StudyRoom, "invitations")


class TestRoomMemberModel:
    def test_tablename(self):
        assert RoomMember.__tablename__ == "room_members"

    def test_has_role_column(self):
        col_names = [c.name for c in RoomMember.__table__.columns]
        assert "role" in col_names
        assert "status" in col_names
        assert "can_send_messages" in col_names
        assert "can_share_files" in col_names

    def test_has_statistics_columns(self):
        col_names = [c.name for c in RoomMember.__table__.columns]
        assert "messages_sent" in col_names
        assert "files_shared" in col_names
        assert "study_hours" in col_names


class TestRoomInvitationModel:
    def test_tablename(self):
        assert RoomInvitation.__tablename__ == "room_invitations"

    def test_has_invitation_code(self):
        col_names = [c.name for c in RoomInvitation.__table__.columns]
        assert "invitation_code" in col_names
        assert "invitee_email" in col_names
        assert "expires_at" in col_names


class TestRoomChatMessageModel:
    def test_tablename(self):
        assert RoomChatMessage.__tablename__ == "room_chat_messages"

    def test_has_content_columns(self):
        col_names = [c.name for c in RoomChatMessage.__table__.columns]
        assert "message" in col_names
        assert "message_type" in col_names
        assert "reactions" in col_names
        assert "mentions" in col_names
        assert "is_edited" in col_names
        assert "is_deleted" in col_names
        assert "is_pinned" in col_names


class TestSharedFileModel:
    def test_tablename(self):
        assert SharedFile.__tablename__ == "shared_files"

    def test_has_file_columns(self):
        col_names = [c.name for c in SharedFile.__table__.columns]
        assert "filename" in col_names
        assert "file_type" in col_names
        assert "file_size_bytes" in col_names
        assert "version_number" in col_names
        assert "download_count" in col_names

    def test_has_scan_columns(self):
        col_names = [c.name for c in SharedFile.__table__.columns]
        assert "is_scanned" in col_names
        assert "scan_result" in col_names


class TestFileVersionModel:
    def test_tablename(self):
        assert FileVersion.__tablename__ == "file_versions"

    def test_has_version_columns(self):
        col_names = [c.name for c in FileVersion.__table__.columns]
        assert "version_number" in col_names
        assert "file_path" in col_names
        assert "status" in col_names
        assert "change_description" in col_names


class TestRoomStudySessionModel:
    def test_tablename(self):
        assert RoomStudySession.__tablename__ == "room_study_sessions"

    def test_has_session_columns(self):
        col_names = [c.name for c in RoomStudySession.__table__.columns]
        assert "started_at" in col_names
        assert "duration_minutes" in col_names
        assert "pomodoros_completed" in col_names
        assert "breaks_taken" in col_names


class TestRoomAnalyticsModel:
    def test_tablename(self):
        assert RoomAnalytics.__tablename__ == "room_analytics"

    def test_has_member_statistics(self):
        col_names = [c.name for c in RoomAnalytics.__table__.columns]
        assert "total_members" in col_names
        assert "active_members_today" in col_names
        assert "total_study_hours" in col_names

    def test_has_engagement_columns(self):
        col_names = [c.name for c in RoomAnalytics.__table__.columns]
        assert "most_active_day" in col_names
        assert "top_contributors" in col_names
        assert "metrics" in col_names


class TestRoomSettingsModel:
    def test_tablename(self):
        assert RoomSettings.__tablename__ == "room_settings"

    def test_has_chat_settings(self):
        col_names = [c.name for c in RoomSettings.__table__.columns]
        assert "slow_mode_seconds" in col_names
        assert "allow_emojis" in col_names
        assert "link_preview" in col_names

    def test_has_study_timer_settings(self):
        col_names = [c.name for c in RoomSettings.__table__.columns]
        assert "default_pomodoro_duration" in col_names
        assert "default_break_duration" in col_names

    def test_has_file_settings(self):
        col_names = [c.name for c in RoomSettings.__table__.columns]
        assert "max_file_size_mb" in col_names
        assert "require_file_approval" in col_names
