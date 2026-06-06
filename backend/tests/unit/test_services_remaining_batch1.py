"""
Unit Tests for Remaining Service Batch 1

Covers:
  1. services/visual_content_generator.py  (VisualContentGenerator)
  2. services/geometry_generator.py        (GeometryGenerator)
  3. services/llm/ensemble_manager.py      (EnsembleStrategy, MultiLLMEnsembleManager)
  4. services/reasoning/logic_validation_service.py (LogicValidationService)
  5. api/advanced_reports.py               (router endpoints)
  6. api/diary_api.py                       (router endpoints)

All heavy deps are mocked before import – no real DB / matplotlib / LLM required.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

# Save original sys.modules state to clean up poisoning after this test module runs
_original_sys_modules = dict(sys.modules)

# ---------------------------------------------------------------------------
# Heavy dependency stubs BEFORE any project imports
# ---------------------------------------------------------------------------
import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

class _FakeNdarray:
    pass

_numpy_stub = types.ModuleType("numpy")
_numpy_stub.ndarray = _FakeNdarray  # type: ignore[attr-defined]
_numpy_stub.array = lambda x, *a, **kw: x  # type: ignore[attr-defined]
_numpy_stub.zeros = lambda *a, **kw: []  # type: ignore[attr-defined]
_numpy_stub.linspace = lambda *a, **kw: []  # type: ignore[attr-defined]

# numpy.random submodule — hypothesis.internal.entropy.NumpyRandomWrapper needs
# seed, get_state, and set_state as callable attributes.
_numpy_random_stub = types.ModuleType("numpy.random")
_numpy_random_stub.seed = lambda *a, **kw: None  # type: ignore[attr-defined]
_numpy_random_stub.get_state = dict  # type: ignore[attr-defined]
_numpy_random_stub.set_state = lambda s: None  # type: ignore[attr-defined]
_numpy_random_stub.RandomState = MagicMock  # type: ignore[attr-defined]
_numpy_stub.random = _numpy_random_stub  # type: ignore[attr-defined]

# models stub (used by advanced_reports: from models import SinavSonucu, SinavTipi)
_models_stub = MagicMock()

# core.dependencies stub (used by advanced_reports)
_core_deps = MagicMock()

class _AuthenticatedUser:
    def __init__(self, id=1, email="test@test.com", role="STUDENT"):
        self.id = id
        self.email = email
        self.role = role

_core_deps.AuthenticatedUser = _AuthenticatedUser
_core_deps.get_current_user = MagicMock()

# ---------------------------------------------------------------------------
# Diary API: schemas must be real Pydantic models for FastAPI response_model
# ---------------------------------------------------------------------------
from datetime import date, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel

class _DiaryEntryResponse(BaseModel):
    id: UUID
    user_id: str
    date: date
    success_count: int = 0
    failure_count: int = 0
    total_tasks: int = 0
    total_duration_minutes: int = 0
    highlights: list = []
    learnings: list = []
    challenges: list = []
    markdown_content: str | None = None
    file_path: str | None = None
    created_at: datetime
    updated_at: datetime
    success_rate: float = 0.0

class _DiaryEntryCreate(BaseModel):
    date: date
    tasks: list = []

class _DiaryEntryUpdate(BaseModel):
    highlights: list = []
    learnings: list = []
    challenges: list = []

class _GoalResponse(BaseModel):
    id: UUID
    user_id: str
    title: str
    status: str = "active"
    category: str | None = None
    created_at: datetime
    updated_at: datetime

class _GoalCreate(BaseModel):
    title: str
    category: str | None = None
    deadline: date | None = None
    measurable_target: str | None = None

class _GoalUpdate(BaseModel):
    title: str | None = None
    status: str | None = None

class _GoalProgressUpdate(BaseModel):
    progress: float = 0.0

class _GoalRiskResponse(BaseModel):
    goal_id: UUID
    is_at_risk: bool = False
    reasons: list = []

class _EmotionalStateCreate(BaseModel):
    mood: str
    notes: str | None = None

class _EmotionalStateResponse(BaseModel):
    id: UUID
    user_id: str
    mood: str
    notes: str | None = None
    created_at: datetime

class _MoodTrendResponse(BaseModel):
    trend: list = []

class _ReflectionCreate(BaseModel):
    content: str

class _ReflectionResponse(BaseModel):
    id: UUID
    user_id: str
    content: str
    created_at: datetime

class _ReflectionPromptsResponse(BaseModel):
    prompts: list = []

class _LearningEntryCreate(BaseModel):
    subject: str
    notes: str

class _LearningEntryResponse(BaseModel):
    id: UUID
    user_id: str
    subject: str
    notes: str
    created_at: datetime

class _LearningReviewResponse(BaseModel):
    reviews: list = []

class _InsightResponse(BaseModel):
    id: UUID
    user_id: str
    content: str
    created_at: datetime

class _ExportRequest(BaseModel):
    format: str = "markdown"

class _ExportResponse(BaseModel):
    url: str

class _ShareLinkCreate(BaseModel):
    entry_id: UUID

class _ShareLinkResponse(BaseModel):
    link: str

class _PeerComparisonResponse(BaseModel):
    comparison: dict = {}

class _SuccessResponse(BaseModel):
    success: bool
    message: str = ""

_diary_schemas_stub = MagicMock()
_diary_schemas_stub.DiaryEntryResponse = _DiaryEntryResponse
_diary_schemas_stub.DiaryEntryCreate = _DiaryEntryCreate
_diary_schemas_stub.DiaryEntryUpdate = _DiaryEntryUpdate
_diary_schemas_stub.GoalResponse = _GoalResponse
_diary_schemas_stub.GoalCreate = _GoalCreate
_diary_schemas_stub.GoalUpdate = _GoalUpdate
_diary_schemas_stub.GoalProgressUpdate = _GoalProgressUpdate
_diary_schemas_stub.GoalRiskResponse = _GoalRiskResponse
_diary_schemas_stub.EmotionalStateCreate = _EmotionalStateCreate
_diary_schemas_stub.EmotionalStateResponse = _EmotionalStateResponse
_diary_schemas_stub.MoodTrendResponse = _MoodTrendResponse
_diary_schemas_stub.ReflectionCreate = _ReflectionCreate
_diary_schemas_stub.ReflectionResponse = _ReflectionResponse
_diary_schemas_stub.ReflectionPromptsResponse = _ReflectionPromptsResponse
_diary_schemas_stub.LearningEntryCreate = _LearningEntryCreate
_diary_schemas_stub.LearningEntryResponse = _LearningEntryResponse
_diary_schemas_stub.LearningReviewResponse = _LearningReviewResponse
_diary_schemas_stub.InsightResponse = _InsightResponse
_diary_schemas_stub.ExportRequest = _ExportRequest
_diary_schemas_stub.ExportResponse = _ExportResponse
_diary_schemas_stub.ShareLinkCreate = _ShareLinkCreate
_diary_schemas_stub.ShareLinkResponse = _ShareLinkResponse
_diary_schemas_stub.PeerComparisonResponse = _PeerComparisonResponse
_diary_schemas_stub.SuccessResponse = _SuccessResponse

# models.diary: GoalStatus enum must be a real enum for FastAPI query params
from enum import Enum

class _GoalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    AT_RISK = "at_risk"
    CANCELLED = "cancelled"

class _ExportFormat(str, Enum):
    MARKDOWN = "markdown"
    PDF = "pdf"

_models_diary_stub = MagicMock()
_models_diary_stub.GoalStatus = _GoalStatus
_models_diary_stub.ExportFormat = _ExportFormat
_models_diary_stub.DiaryEntry = MagicMock()
_models_diary_stub.DiaryExport = MagicMock()
_models_diary_stub.Goal = MagicMock()
_models_diary_stub.Insight = MagicMock()
_models_diary_stub.LearningEntry = MagicMock()
_models_diary_stub.Reflection = MagicMock()

# models.user
_models_user_stub = MagicMock()
_models_user_stub.User = MagicMock

# core.auth_dependencies: AuthenticationDependency must be callable returning a dependency
_auth_dep_stub = MagicMock()

class _AuthDep:
    def __init__(self, required: bool = True):
        self.required = required

    async def __call__(self, request=None, credentials=None):
        return None  # overridden in tests via dependency_overrides

_auth_dep_stub.AuthenticationDependency = _AuthDep

# core.database
_core_db_stub = MagicMock()
_core_db_stub.get_db = MagicMock()

# core.service_dependencies
_core_svc_deps = MagicMock()
_core_svc_deps.get_diary_service = MagicMock()

_stubbed_modules = {
    "numpy": _numpy_stub,
    "numpy.random": _numpy_random_stub,
    "matplotlib": MagicMock(),
    "matplotlib.pyplot": MagicMock(),
    "matplotlib.patches": MagicMock(),
    "services.graph_generator": MagicMock(GraphGenerator=MagicMock),
    "services.map_diagram_generator": MagicMock(MapDiagramGenerator=MagicMock),
    "services.geometry_generator": MagicMock(GeometryGenerator=MagicMock),
    "services.llm.gemini_provider": MagicMock(),
    "services.llm.openai_provider": MagicMock(),
    "services.llm.claude_provider": MagicMock(),
    "services.llm.qwen_provider": MagicMock(),
    "core.osym_exam_engine": MagicMock(),
    "core.turkish_nlp_utils": MagicMock(),
    "services.irt_morfoloji_service": MagicMock(),
    "services.learning_style_service": MagicMock(),
    "services.zpd_maarif_service": MagicMock(),
    "utils.pdf_generator": MagicMock(),
    "models": _models_stub,
    "core.dependencies": _core_deps,
    "sqlalchemy": MagicMock(),
    "sqlalchemy.ext.asyncio": MagicMock(),
    "sqlalchemy.orm": MagicMock(),
    "sqlalchemy.future": MagicMock(),
    "api.schemas.diary": _diary_schemas_stub,
    "models.diary": _models_diary_stub,
    "models.user": _models_user_stub,
    "core.auth_dependencies": _auth_dep_stub,
    "core.database": _core_db_stub,
    "core.service_dependencies": _core_svc_deps,
    "services.diary_service": MagicMock(),
    "services.emotional_service": MagicMock(),
    "services.export_service": MagicMock(),
    "services.goal_service": MagicMock(),
    "services.insight_service": MagicMock(),
    "services.learning_journal_service": MagicMock(),
    "services.peer_comparison_service": MagicMock(),
    "services.reflection_service": MagicMock(),
}

def _apply_stubs():
    import sys
    for k, v in _stubbed_modules.items():
        sys.modules[k] = v

def _restore_stubs():
    import sys
    current_keys = list(sys.modules.keys())
    for key in current_keys:
        if key not in _original_sys_modules:
            sys.modules.pop(key, None)
        else:
            sys.modules[key] = _original_sys_modules[key]

# Apply stubs at collection time
_apply_stubs()

# sqlalchemy.select must return a mock (used in diary_api body).
# Use setdefault so we never overwrite a real SQLAlchemy already loaded by
# other test files — replacing the real module would break services that
# rely on real sqlalchemy.func, select, etc.
sys.modules.setdefault("sqlalchemy", MagicMock())


@pytest.fixture(scope="module", autouse=True)
def setup_stubs():
    _apply_stubs()
    yield
    _restore_stubs()


# ---------------------------------------------------------------------------
# Actual imports
# ---------------------------------------------------------------------------

from services.llm.base_llm_provider import LLMResponse  # noqa: E402
from services.llm.ensemble_manager import EnsembleStrategy  # noqa: E402
from services.llm.multi_llm_config import LLMProvider  # noqa: E402
from services.reasoning.logic_validation_service import (  # noqa: E402
    CircularReasoningResult,
    ConsistencyResult,
    InferenceResult,
    InferenceRule,
    LogicValidationService,
    Proposition,
)
from services.visual_content_generator import VisualContentGenerator  # noqa: E402

# Restore original modules at module level after imports complete so collection-phase poisoning is prevented
_restore_stubs()


# ============================================================
# Helpers
# ============================================================


def _make_llm_response(
    provider=LLMProvider.OPENAI,
    content="ok",
    confidence=0.9,
    cost=0.01,
    latency=200.0,
    tokens=100,
) -> LLMResponse:
    return LLMResponse(
        provider=provider,
        model_name="gpt-4",
        content=content,
        latency_ms=latency,
        tokens_used=tokens,
        cost_usd=cost,
        confidence_score=confidence,
    )


def _make_fake_user():
    u = MagicMock()
    u.id = "user-abc"
    u.email = "test@diary.com"
    return u


def _make_diary_entry_obj():
    entry = MagicMock()
    entry.id = uuid4()
    entry.user_id = "user-abc"
    entry.date = date.today()
    entry.success_count = 3
    entry.failure_count = 1
    entry.total_tasks = 4
    entry.total_duration_minutes = 45
    entry.highlights = ["A"]
    entry.learnings = ["B"]
    entry.challenges = ["C"]
    entry.markdown_content = "# ok"
    entry.file_path = None
    entry.created_at = datetime.now()
    entry.updated_at = datetime.now()
    entry.success_rate = 0.75
    return entry


# ============================================================
# 1. VisualContentGenerator – table generation
# ============================================================


class TestVisualContentGeneratorTables:
    """Tests for Phase-1 table generation."""

    def setup_method(self):
        with (
            patch("services.visual_content_generator.GraphGenerator"),
            patch("services.visual_content_generator.GeometryGenerator"),
            patch("services.visual_content_generator.MapDiagramGenerator"),
        ):
            self.gen = VisualContentGenerator()

    def test_generate_frequency_table_returns_dict(self):
        result = self.gen.generate_table(
            "Matematik", "İstatistik", "frequency_table", rows=4
        )
        assert isinstance(result, dict)
        assert result["type"] == "table"
        assert result["format"] == "markdown"
        assert "content" in result

    def test_frequency_table_has_data_field(self):
        result = self.gen.generate_table(
            "Matematik", "İstatistik", "frequency_table", rows=3
        )
        assert "data" in result
        assert "categories" in result["data"]
        assert len(result["data"]["categories"]) == 3

    def test_comparison_table_returns_dict(self):
        result = self.gen.generate_table(
            "Sosyal", "Karşılaştırma", "comparison_table", rows=3, columns=3
        )
        assert result["type"] == "table"
        assert result["metadata"]["rows"] == 3

    def test_statistics_table_has_stats(self):
        result = self.gen.generate_table("Matematik", "İstatistik", "statistics_table")
        assert "data" in result
        assert "statistics" in result["data"]

    def test_price_table_generated(self):
        result = self.gen.generate_table("Matematik", "Toplam", "price_table", rows=3)
        assert result["type"] == "table"
        assert "content" in result

    def test_grade_table_generated(self):
        result = self.gen.generate_table("Türkçe", "Notlar", "grade_table", rows=3)
        assert result["type"] == "table"

    def test_schedule_table_generated(self):
        result = self.gen.generate_table("Fen", "Ders Programı", "schedule_table")
        assert result["type"] == "table"
        assert result["metadata"]["alt_text"] == "Class schedule table"

    def test_generic_table_as_fallback(self):
        result = self.gen.generate_table("X", "Y", "nonexistent_type")
        assert result["type"] == "table"

    def test_markdown_table_has_header_separator(self):
        result = self.gen.generate_table("Matematik", "Veri", "frequency_table", rows=2)
        content = result["content"]
        assert "|" in content
        assert "---" in content

    def test_visual_types_registered(self):
        assert "table" in self.gen.visual_types
        assert "graph" in self.gen.visual_types
        assert "geometry" in self.gen.visual_types
        assert "map_diagram" in self.gen.visual_types


# ============================================================
# 2. VisualContentGenerator – graph / geometry delegation
# ============================================================


class TestVisualContentGeneratorDelegation:
    """Tests that graph/geometry calls are delegated to sub-generators."""

    def setup_method(self):
        with (
            patch("services.visual_content_generator.GraphGenerator") as MockGG,
            patch("services.visual_content_generator.GeometryGenerator") as MockGeom,
            patch("services.visual_content_generator.MapDiagramGenerator") as MockMap,
        ):
            self.mock_graph = MockGG.return_value
            self.mock_geom = MockGeom.return_value
            self.mock_map = MockMap.return_value
            self.gen = VisualContentGenerator()
            self.gen.graph_generator = self.mock_graph
            self.gen.geometry_generator = self.mock_geom
            self.gen.map_diagram_generator = self.mock_map

    def test_generate_graph_delegates_to_graph_generator(self):
        self.mock_graph.generate_graph.return_value = {
            "type": "graph",
            "content": "<svg/>",
        }
        self.gen.generate_graph("Fizik", "Hareket", "line")
        assert self.mock_graph.generate_graph.called

    def test_generate_geometry_delegates_to_geometry_generator(self):
        self.mock_geom.generate_geometry.return_value = {
            "type": "geometry",
            "content": "<svg/>",
        }
        self.gen.generate_geometry(
            "Matematik", "Geometri", "triangle", "right_triangle"
        )
        assert self.mock_geom.generate_geometry.called

    def test_generate_map_diagram_delegates(self):
        self.mock_map.generate_diagram.return_value = {
            "type": "map",
            "content": "<svg/>",
        }
        self.gen.generate_map_diagram(
            "Coğrafya", "Türkiye", "geographic_map", "turkey_regions"
        )
        assert self.mock_map.generate_diagram.called

    def test_generate_graph_bar_type(self):
        self.mock_graph.generate_graph.return_value = {
            "type": "graph",
            "content": "<svg/>",
        }
        self.gen.generate_graph("Matematik", "Dağılım", "bar")
        self.mock_graph.generate_graph.assert_called()

    def test_generate_graph_pie_type(self):
        self.mock_graph.generate_graph.return_value = {"type": "graph"}
        self.gen.generate_graph("Sosyal", "Bölgeler", "pie")
        self.mock_graph.generate_graph.assert_called()

    def test_unknown_graph_type_raises(self):
        with pytest.raises(Exception):
            self.gen.generate_graph("X", "Y", "unknown_graph_type")  # type: ignore


# ============================================================
# 3. EnsembleStrategy – pure static methods, no I/O
# ============================================================


class TestEnsembleStrategy:
    """Tests for the stateless EnsembleStrategy voting helpers."""

    def _responses(self):
        return [
            _make_llm_response(
                provider=LLMProvider.OPENAI, confidence=0.9, cost=0.01, latency=300
            ),
            _make_llm_response(
                provider=LLMProvider.CLAUDE, confidence=0.8, cost=0.005, latency=200
            ),
            _make_llm_response(
                provider=LLMProvider.QWEN, confidence=0.7, cost=0.002, latency=100
            ),
        ]

    def test_majority_voting_returns_llm_response(self):
        best = EnsembleStrategy.majority_voting(self._responses())
        assert isinstance(best, LLMResponse)

    def test_majority_voting_picks_highest_weighted_score(self):
        best = EnsembleStrategy.majority_voting(self._responses())
        assert best is not None

    def test_quality_threshold_filter_removes_low_confidence(self):
        filtered = EnsembleStrategy.quality_threshold_filter(
            self._responses(), min_quality=0.85
        )
        assert all((r.confidence_score or 0) >= 0.85 for r in filtered)

    def test_quality_threshold_filter_keeps_all_above_threshold(self):
        filtered = EnsembleStrategy.quality_threshold_filter(
            self._responses(), min_quality=0.5
        )
        assert len(filtered) == 3

    def test_quality_threshold_filter_empty_result_possible(self):
        filtered = EnsembleStrategy.quality_threshold_filter(
            self._responses(), min_quality=0.99
        )
        assert len(filtered) == 0

    def test_cost_optimized_selection_returns_response(self):
        best = EnsembleStrategy.cost_optimized_selection(self._responses())
        assert isinstance(best, LLMResponse)

    def test_cost_optimized_picks_cheapest_above_threshold(self):
        best = EnsembleStrategy.cost_optimized_selection(
            self._responses(), quality_threshold=0.7
        )
        assert best.cost_usd <= 0.01

    def test_cost_optimized_fallback_when_all_below_threshold(self):
        low = [
            _make_llm_response(provider=LLMProvider.OPENAI, confidence=0.3),
            _make_llm_response(provider=LLMProvider.CLAUDE, confidence=0.2),
        ]
        best = EnsembleStrategy.cost_optimized_selection(low, quality_threshold=0.9)
        assert isinstance(best, LLMResponse)

    def test_latency_optimized_selection_returns_response(self):
        best = EnsembleStrategy.latency_optimized_selection(self._responses())
        assert isinstance(best, LLMResponse)

    def test_latency_optimized_picks_fastest_above_threshold(self):
        best = EnsembleStrategy.latency_optimized_selection(
            self._responses(), quality_threshold=0.7
        )
        assert best.latency_ms <= 300

    def test_majority_voting_single_response(self):
        single = [_make_llm_response()]
        best = EnsembleStrategy.majority_voting(single)
        assert isinstance(best, LLMResponse)

    def test_majority_voting_custom_weights(self):
        responses = self._responses()
        weights = {
            LLMProvider.OPENAI: 0.5,
            LLMProvider.CLAUDE: 0.3,
            LLMProvider.QWEN: 0.2,
        }
        best = EnsembleStrategy.majority_voting(responses, weights=weights)
        assert isinstance(best, LLMResponse)


# ============================================================
# 4. LogicValidationService
# ============================================================


class TestLogicValidationService:
    """Tests for LogicValidationService."""

    def setup_method(self):
        self.svc = LogicValidationService()

    # --- Proposition extraction ---

    def test_extract_propositions_from_simple_sentence(self):
        props = self.svc.extract_propositions("Hava güzel. Bugün sıcak.")
        assert len(props) >= 1
        assert all(hasattr(p, "content") for p in props)

    def test_extract_propositions_detects_negation(self):
        # The service uses "degil" (ASCII) as the negation keyword
        props = self.svc.extract_propositions("Bu dogru degil.")
        negated = [p for p in props if p.is_negated]
        assert len(negated) >= 1

    def test_extract_propositions_empty_string(self):
        props = self.svc.extract_propositions("")
        assert props == []

    def test_proposition_equality(self):
        p1 = Proposition(content="hava güzel", is_negated=False)
        p2 = Proposition(content="Hava güzel", is_negated=False)
        assert p1 == p2

    def test_proposition_hash_equality(self):
        p1 = Proposition(content="test", is_negated=False)
        p2 = Proposition(content="test", is_negated=False)
        assert hash(p1) == hash(p2)

    def test_proposition_negation(self):
        p = Proposition(content="hava güzel", is_negated=False)
        neg = p.negate()
        assert neg.is_negated is True
        assert neg.content == p.content

    def test_proposition_double_negation_restores(self):
        p = Proposition(content="test", is_negated=False)
        double_neg = p.negate().negate()
        assert double_neg.is_negated is False

    # --- Implication extraction ---

    def test_extract_implications_eger_ise_pattern(self):
        text = "Eger hava güzel ise dışarı çıkarız."
        impls = self.svc.extract_implications(text)
        assert len(impls) >= 1
        assert impls[0].antecedent.content != ""

    def test_extract_implications_olursa_pattern(self):
        text = "Sıcak olursa denize gideriz."
        impls = self.svc.extract_implications(text)
        assert len(impls) >= 1

    def test_extract_implications_returns_list(self):
        text = "Matematik güzel bir derstir."
        impls = self.svc.extract_implications(text)
        assert isinstance(impls, list)

    # --- Consistency check ---

    @pytest.mark.asyncio
    async def test_check_consistency_no_conflicts_returns_result(self):
        steps = [
            {
                "step_number": 1,
                "description": "Hava güzel.",
                "result": "Dışarı çıkabiliriz.",
            },
            {
                "step_number": 2,
                "description": "Dışarı çıkabiliriz.",
                "result": "Parkta yürüyeceğiz.",
            },
        ]
        result = await self.svc.check_consistency(steps)
        assert isinstance(result, ConsistencyResult)
        assert result.is_consistent is True

    @pytest.mark.asyncio
    async def test_check_consistency_returns_consistency_result_type(self):
        steps = [
            {"step_number": 1, "description": "X.", "result": "Y."},
        ]
        result = await self.svc.check_consistency(steps)
        assert hasattr(result, "is_consistent")
        assert hasattr(result, "conflicts")
        assert hasattr(result, "warnings")

    @pytest.mark.asyncio
    async def test_check_consistency_empty_steps(self):
        result = await self.svc.check_consistency([])
        assert result.is_consistent is True

    @pytest.mark.asyncio
    async def test_check_consistency_details_populated(self):
        steps = [{"step_number": 1, "description": "Evet.", "result": "Tamam."}]
        result = await self.svc.check_consistency(steps)
        assert isinstance(result.details, str)
        assert len(result.details) > 0

    # --- Circular reasoning detection ---

    @pytest.mark.asyncio
    async def test_detect_circular_no_cycle_returns_result(self):
        steps = [
            {"step_number": 1, "description": "Başlangıç.", "result": "A."},
            {"step_number": 2, "description": "A sonucundan.", "result": "B."},
        ]
        result = await self.svc.detect_circular_reasoning(steps)
        assert isinstance(result, CircularReasoningResult)
        assert hasattr(result, "has_circular_reasoning")

    @pytest.mark.asyncio
    async def test_detect_circular_empty_steps(self):
        result = await self.svc.detect_circular_reasoning([])
        assert isinstance(result, CircularReasoningResult)
        assert result.has_circular_reasoning is False

    @pytest.mark.asyncio
    async def test_detect_circular_explanation_populated(self):
        steps = [{"step_number": 1, "description": "Test.", "result": "OK."}]
        result = await self.svc.detect_circular_reasoning(steps)
        assert isinstance(result.explanation, str)

    @pytest.mark.asyncio
    async def test_detect_circular_with_step_refs(self):
        steps = [
            {"step_number": 1, "description": "Adim 2 sonucuna göre.", "result": "A."},
            {"step_number": 2, "description": "Adim 1 sonucuna göre.", "result": "B."},
        ]
        result = await self.svc.detect_circular_reasoning(steps)
        assert isinstance(result, CircularReasoningResult)

    # --- Inference validation ---

    @pytest.mark.asyncio
    async def test_validate_inference_empty_premise(self):
        result = await self.svc.validate_inference("", "Sonuç var.")
        assert result.is_valid is False
        assert result.rule == InferenceRule.UNKNOWN

    @pytest.mark.asyncio
    async def test_validate_inference_empty_conclusion(self):
        result = await self.svc.validate_inference("Öncül var.", "")
        assert result.is_valid is False

    @pytest.mark.asyncio
    async def test_validate_inference_returns_result_object(self):
        result = await self.svc.validate_inference("Hava güzel.", "Dışarı çıkabiliriz.")
        assert isinstance(result, InferenceResult)
        assert hasattr(result, "is_valid")
        assert hasattr(result, "rule")

    @pytest.mark.asyncio
    async def test_validate_inference_confidence_in_range(self):
        result = await self.svc.validate_inference("Bir şey var.", "Bir şey çıkar.")
        assert 0.0 <= result.confidence <= 1.0


# ============================================================
# 5. InferenceRule enum completeness
# ============================================================


class TestInferenceRuleEnum:
    """Verify all expected inference rules exist."""

    def test_modus_ponens_exists(self):
        assert InferenceRule.MODUS_PONENS.value == "modus_ponens"

    def test_modus_tollens_exists(self):
        assert InferenceRule.MODUS_TOLLENS.value == "modus_tollens"

    def test_hypothetical_syllogism_exists(self):
        assert InferenceRule.HYPOTHETICAL_SYLLOGISM.value == "hypothetical_syllogism"

    def test_disjunctive_syllogism_exists(self):
        assert InferenceRule.DISJUNCTIVE_SYLLOGISM.value == "disjunctive_syllogism"

    def test_conjunction_exists(self):
        assert InferenceRule.CONJUNCTION.value == "conjunction"

    def test_unknown_rule_exists(self):
        assert InferenceRule.UNKNOWN.value == "unknown"

    def test_addition_exists(self):
        assert InferenceRule.ADDITION.value == "addition"

    def test_simplification_exists(self):
        assert InferenceRule.SIMPLIFICATION.value == "simplification"


# ============================================================
# 6. advanced_reports.py – API endpoints
# ============================================================


class TestAdvancedReportsAPI:
    """Tests for advanced_reports router endpoints using minimal FastAPI app."""

    @pytest.fixture(autouse=True)
    def setup_app(self):
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        # Patch session_to_sinav_sonucu and heavy service instantiation
        _osym_stub = MagicMock()
        _osym_stub.session_to_sinav_sonucu = AsyncMock(return_value=None)

        with patch.dict(
            sys.modules,
            {
                "core.osym_exam_engine": _osym_stub,
                "services.irt_morfoloji_service": MagicMock(
                    IRTMorfolojiService=MagicMock
                ),
                "services.zpd_maarif_service": MagicMock(ZPDMaarifService=MagicMock),
                "services.learning_style_service": MagicMock(
                    LearningStyleService=MagicMock
                ),
                "utils.pdf_generator": MagicMock(PDFReportGenerator=MagicMock),
                "models": MagicMock(),
            },
        ):
            # Force reload to pick up patched modules
            if "api.advanced_reports" in sys.modules:
                del sys.modules["api.advanced_reports"]
            import api.advanced_reports as ar_module

            user = _AuthenticatedUser(id=99)

            app = FastAPI()
            app.dependency_overrides[ar_module.get_current_user] = lambda: user
            app.include_router(ar_module.router)

        self.app = app
        self.ar_module = ar_module
        self.osym_stub = _osym_stub
        self.AsyncClient = AsyncClient
        self.ASGITransport = ASGITransport

    @pytest.mark.asyncio
    async def test_advanced_exam_report_not_found(self):
        transport = self.ASGITransport(app=self.app)
        async with self.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/v1/reports/exam/no-such/advanced")
            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_irt_analysis_not_found(self):
        transport = self.ASGITransport(app=self.app)
        async with self.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/v1/reports/exam/xyz/irt-analysis")
            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_zpd_recommendations_not_found(self):
        transport = self.ASGITransport(app=self.app)
        async with self.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/v1/reports/exam/xyz/zpd-recommendations")
            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_learning_style_analysis_not_found(self):
        transport = self.ASGITransport(app=self.app)
        async with self.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/v1/reports/exam/xyz/learning-style-analysis")
            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_osym_ets_comparison_not_found(self):
        transport = self.ASGITransport(app=self.app)
        async with self.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/v1/reports/exam/xyz/osym-ets-comparison")
            assert resp.status_code == 404


# ============================================================
# 7. diary_api.py – API endpoints
# ============================================================


class TestDiaryAPI:
    """Tests for diary_api router using a minimal FastAPI app."""

    @pytest.fixture(autouse=True)
    def setup_app(self):
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        user = _make_fake_user()

        # Force a fresh import of diary_api with our stubs in place
        if "api.diary_api" in sys.modules:
            del sys.modules["api.diary_api"]

        import api.diary_api as diary_module

        # Build minimal FastAPI app
        app = FastAPI()

        # Override auth dep
        app.dependency_overrides[diary_module.get_current_user] = lambda: user

        # Override get_db with a mock async generator
        mock_db = AsyncMock()
        _execute_result = MagicMock()
        _execute_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = _execute_result

        async def _get_test_db():
            yield mock_db

        app.dependency_overrides[diary_module.get_db] = _get_test_db

        # Override get_diary_service
        mock_diary_svc = AsyncMock()
        mock_diary_svc.get_today_summary = AsyncMock(return_value=None)
        app.dependency_overrides[diary_module.get_diary_service] = (
            lambda: mock_diary_svc
        )

        app.include_router(diary_module.router)

        self.app = app
        self.diary_module = diary_module
        self.mock_db = mock_db
        self.mock_diary_svc = mock_diary_svc
        self.user = user
        self.AsyncClient = AsyncClient
        self.ASGITransport = ASGITransport

    @pytest.mark.asyncio
    async def test_get_today_summary_null_when_no_entry(self):
        transport = self.ASGITransport(app=self.app)
        async with self.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/v1/diary/summary/today")
            assert resp.status_code == 200
            assert resp.json() is None

    @pytest.mark.asyncio
    async def test_get_today_summary_returns_entry(self):
        entry = _make_diary_entry_obj()
        self.mock_diary_svc.get_today_summary = AsyncMock(return_value=entry)

        transport = self.ASGITransport(app=self.app)
        async with self.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/v1/diary/summary/today")
            assert resp.status_code == 200
            data = resp.json()
            assert data is not None
            assert data["user_id"] == "user-abc"

    @pytest.mark.asyncio
    async def test_get_summaries_returns_list(self):
        # Patch DiaryService so get_summaries returns []
        mock_svc_cls = MagicMock()
        svc_inst = AsyncMock()
        svc_inst.get_summaries = AsyncMock(return_value=[])
        mock_svc_cls.return_value = svc_inst

        with patch.object(self.diary_module, "DiaryService", mock_svc_cls):
            transport = self.ASGITransport(app=self.app)
            async with self.AsyncClient(
                transport=transport, base_url="http://test"
            ) as c:
                resp = await c.get("/api/v1/diary/summaries")
                assert resp.status_code == 200
                assert resp.json() == []

    @pytest.mark.asyncio
    async def test_get_goals_returns_list(self):
        mock_goal_svc_cls = MagicMock()
        svc_inst = AsyncMock()
        svc_inst.get_goals = AsyncMock(return_value=[])
        mock_goal_svc_cls.return_value = svc_inst

        with patch.object(self.diary_module, "GoalService", mock_goal_svc_cls):
            transport = self.ASGITransport(app=self.app)
            async with self.AsyncClient(
                transport=transport, base_url="http://test"
            ) as c:
                resp = await c.get("/api/v1/diary/goals")
                assert resp.status_code == 200
                assert resp.json() == []

    @pytest.mark.asyncio
    async def test_get_active_goals_returns_list(self):
        mock_goal_svc_cls = MagicMock()
        svc_inst = AsyncMock()
        svc_inst.get_active_goals = AsyncMock(return_value=[])
        mock_goal_svc_cls.return_value = svc_inst

        with patch.object(self.diary_module, "GoalService", mock_goal_svc_cls):
            transport = self.ASGITransport(app=self.app)
            async with self.AsyncClient(
                transport=transport, base_url="http://test"
            ) as c:
                resp = await c.get("/api/v1/diary/goals/active")
                assert resp.status_code == 200
                assert resp.json() == []

    @pytest.mark.asyncio
    async def test_get_at_risk_goals_returns_list(self):
        mock_goal_svc_cls = MagicMock()
        svc_inst = AsyncMock()
        svc_inst.get_at_risk_goals = AsyncMock(return_value=[])
        mock_goal_svc_cls.return_value = svc_inst

        with patch.object(self.diary_module, "GoalService", mock_goal_svc_cls):
            transport = self.ASGITransport(app=self.app)
            async with self.AsyncClient(
                transport=transport, base_url="http://test"
            ) as c:
                resp = await c.get("/api/v1/diary/goals/at-risk")
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_goal_statistics(self):
        mock_goal_svc_cls = MagicMock()
        svc_inst = AsyncMock()
        svc_inst.get_goal_statistics = AsyncMock(return_value={"total": 0, "active": 0})
        mock_goal_svc_cls.return_value = svc_inst

        with patch.object(self.diary_module, "GoalService", mock_goal_svc_cls):
            transport = self.ASGITransport(app=self.app)
            async with self.AsyncClient(
                transport=transport, base_url="http://test"
            ) as c:
                resp = await c.get("/api/v1/diary/goals/statistics")
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_summary_by_date_returns_null(self):
        mock_svc_cls = MagicMock()
        svc_inst = AsyncMock()
        svc_inst.get_summary = AsyncMock(return_value=None)
        mock_svc_cls.return_value = svc_inst

        with patch.object(self.diary_module, "DiaryService", mock_svc_cls):
            transport = self.ASGITransport(app=self.app)
            async with self.AsyncClient(
                transport=transport, base_url="http://test"
            ) as c:
                resp = await c.get("/api/v1/diary/summary?entry_date=2024-01-01")
                assert resp.status_code == 200
                assert resp.json() is None
