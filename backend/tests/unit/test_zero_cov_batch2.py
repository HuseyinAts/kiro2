"""
Unit tests for zero-coverage backend files (Batch 2).

Targets:
1. services/goal_service.py        (253 stmts, 0%)
2. services/emotional_service.py   (220 stmts, 0%)
3. services/learning_journal_service.py (239 stmts, 0%)
4. core/unified/logging_system.py  (220 stmts, 0%)
"""

import importlib.util
import logging
import os
import sys
import types
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

# ---------------------------------------------------------------------------
# Cleanup stale MagicMock stubs from previous runs
# ---------------------------------------------------------------------------
_STALE_PREFIXES = (
    "models.diary",
    "models.database",
    "api.schemas.diary",
    "services.goal_service",
    "services.emotional_service",
    "services.learning_journal_service",
    "core.unified.logging_system",
    "networkx",
    "matplotlib",
)
for _k in list(sys.modules.keys()):
    if any(_k == p or _k.startswith(p + ".") for p in _STALE_PREFIXES):
        del sys.modules[_k]

# ---------------------------------------------------------------------------
# Heavy / external dependency stubs (must be set BEFORE any target import)
# ---------------------------------------------------------------------------
_BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---- networkx stub ----
_nx = types.ModuleType("networkx")


class _FakeGraph:
    def __init__(self):
        self._nodes: dict = {}
        self._edges: list = []

    def add_node(self, n, **attrs):
        self._nodes[n] = attrs

    def has_node(self, n):
        return n in self._nodes

    def add_edge(self, u, v, **attrs):
        self._edges.append((u, v, attrs))

    def number_of_nodes(self):
        return len(self._nodes)

    def number_of_edges(self):
        return len(self._edges)

    @property
    def nodes(self):
        return self._nodes


_nx.Graph = _FakeGraph
_nx.degree_centrality = lambda G: dict.fromkeys(G._nodes, 0.5)
_nx.density = lambda G: 0.1
_nx.number_connected_components = lambda G: 1
sys.modules.setdefault("networkx", _nx)

# ---- matplotlib stubs ----
_mpl = types.ModuleType("matplotlib")
_mpl.use = lambda *a, **kw: None
_mpl_pyplot = types.ModuleType("matplotlib.pyplot")
_fig_mock = MagicMock()
_ax_mock = MagicMock()
_mpl_pyplot.subplots = MagicMock(return_value=(_fig_mock, _ax_mock))
_mpl_pyplot.xticks = MagicMock()
_mpl_pyplot.tight_layout = MagicMock()
_mpl_pyplot.savefig = MagicMock()
_mpl_pyplot.close = MagicMock()
_mpl_dates = types.ModuleType("matplotlib.dates")
_mpl_dates.DateFormatter = MagicMock(return_value=MagicMock())
_mpl_dates.DayLocator = MagicMock(return_value=MagicMock())
sys.modules.setdefault("matplotlib", _mpl)
sys.modules.setdefault("matplotlib.pyplot", _mpl_pyplot)
sys.modules.setdefault("matplotlib.dates", _mpl_dates)

# ---- SQLAlchemy stubs (minimal, to avoid DB connection) ----
_sa = types.ModuleType("sqlalchemy")
_sa.select = MagicMock(return_value=MagicMock())
_sa.and_ = MagicMock(return_value=MagicMock())
_sa.desc = MagicMock(return_value=MagicMock())
_sa.Column = MagicMock()
_sa.String = MagicMock()
_sa.Integer = MagicMock()
_sa.Float = MagicMock()
_sa.Boolean = MagicMock()
_sa.ForeignKey = MagicMock()
_sa.Text = MagicMock()
_sa.Date = MagicMock()
_sa.Index = MagicMock()
_sa.Enum = MagicMock()
sys.modules.setdefault("sqlalchemy", _sa)

_sa_ext_async = types.ModuleType("sqlalchemy.ext.asyncio")
_AsyncSession = MagicMock()
_sa_ext_async.AsyncSession = _AsyncSession
sys.modules.setdefault("sqlalchemy.ext.asyncio", _sa_ext_async)

_sa_dialects_pg = types.ModuleType("sqlalchemy.dialects.postgresql")
_sa_dialects_pg.UUID = MagicMock()
_sa_dialects_pg.JSONB = MagicMock()
_sa_dialects_pg.ARRAY = MagicMock()
sys.modules.setdefault("sqlalchemy.dialects.postgresql", _sa_dialects_pg)

_sa_orm = types.ModuleType("sqlalchemy.orm")
_sa_orm.relationship = MagicMock()
sys.modules.setdefault("sqlalchemy.orm", _sa_orm)

_sa_sql = types.ModuleType("sqlalchemy.sql")
_sa_sql.func = MagicMock()
sys.modules.setdefault("sqlalchemy.sql", _sa_sql)

_sa_types = types.ModuleType("sqlalchemy.types")
_sa_types.DateTime = MagicMock()
sys.modules.setdefault("sqlalchemy.types", _sa_types)

# ---- models.database stub ----
_models_db = types.ModuleType("models.database")
_models_db.Base = MagicMock()
sys.modules.setdefault("models.database", _models_db)

# ---- models.diary stub ----
_models_diary = types.ModuleType("models.diary")


class _GoalStatus:
    ACTIVE = "active"
    COMPLETED = "completed"
    AT_RISK = "at_risk"
    CANCELLED = "cancelled"


class _ColExpr:
    """Returned at class level — supports all comparison operators by returning itself."""

    def __eq__(self, other):
        return MagicMock()

    def __ne__(self, other):
        return MagicMock()

    def __lt__(self, other):
        return MagicMock()

    def __le__(self, other):
        return MagicMock()

    def __gt__(self, other):
        return MagicMock()

    def __ge__(self, other):
        return MagicMock()

    def __bool__(self):
        return True


class _ColAttr:
    """Descriptor that acts as a SQLAlchemy column at the class level
    (supports == / != / >= comparisons) and as a normal value at instance level."""

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            # Class-level access: return a _ColExpr that accepts comparisons
            return _ColExpr()
        return obj.__dict__.get(self._name)

    def __set__(self, obj, value):
        obj.__dict__[self._name] = value


class _FakeGoal:
    # Class-level column descriptors for SQLAlchemy-style queries
    id = _ColAttr()
    user_id = _ColAttr()
    status = _ColAttr()
    category = _ColAttr()
    is_at_risk = _ColAttr()
    target_date = _ColAttr()
    created_at = _ColAttr()

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid4())
        self.user_id = kwargs.get("user_id", uuid4())
        self.title = kwargs.get("title", "Test Goal")
        self.description = kwargs.get("description", "")
        self.target_value = kwargs.get("target_value", 100.0)
        self.current_value = kwargs.get("current_value", 0.0)
        self.progress = kwargs.get("progress", 0)
        self.status = kwargs.get("status", _GoalStatus.ACTIVE)
        self.milestones = kwargs.get("milestones", [])
        self.milestone_celebrations = kwargs.get("milestone_celebrations", [])
        self.start_date = kwargs.get("start_date")
        self.target_date = kwargs.get("target_date")
        self.updated_at = kwargs.get("updated_at")
        self.completed_at = kwargs.get("completed_at")
        self.velocity = kwargs.get("velocity", 0.0)
        self.predicted_completion = kwargs.get("predicted_completion")
        self.is_at_risk = kwargs.get("is_at_risk", False)
        self.risk_factors = kwargs.get("risk_factors", [])
        self.adjustments = kwargs.get("adjustments", [])
        self.lessons_learned = kwargs.get("lessons_learned", [])
        self.success_factors = kwargs.get("success_factors", [])
        self.challenges_faced = kwargs.get("challenges_faced", [])
        self.category = kwargs.get("category")
        self.unit = kwargs.get("unit")
        self.priority = kwargs.get("priority", 2)
        self.specific = kwargs.get("specific")
        self.measurable = kwargs.get("measurable")
        self.achievable = kwargs.get("achievable")
        self.relevant = kwargs.get("relevant")
        self.time_bound = kwargs.get("time_bound")


class _FakeEmotionalState:
    # Class-level column descriptors
    id = _ColAttr()
    user_id = _ColAttr()
    timestamp = _ColAttr()
    frustration_score = _ColAttr()

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid4())
        self.user_id = kwargs.get("user_id", uuid4())
        self.timestamp = kwargs.get("timestamp", datetime.now())
        self.confidence_level = kwargs.get("confidence_level", 7)
        self.frustration_score = kwargs.get("frustration_score", 0.2)
        self.retry_count = kwargs.get("retry_count", 0)
        self.error_count = kwargs.get("error_count", 0)
        self.flow_state = kwargs.get("flow_state", False)
        self.productivity_score = kwargs.get("productivity_score", 0.5)
        self.tasks_completed = kwargs.get("tasks_completed", 2)
        self.task_type = kwargs.get("task_type")
        self.trigger_factors = kwargs.get("trigger_factors", {})
        self.self_awareness_score = kwargs.get("self_awareness_score", 50.0)
        self.context_notes = kwargs.get("context_notes")
        self.predicted_state = kwargs.get("predicted_state")
        self.actual_state = kwargs.get("actual_state")


class _FakeLearningEntry:
    # Class-level column descriptors
    id = _ColAttr()
    user_id = _ColAttr()
    domain = _ColAttr()
    next_review = _ColAttr()
    created_at = _ColAttr()

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid4())
        self.user_id = kwargs.get("user_id", uuid4())
        self.title = kwargs.get("title", "Test Entry")
        self.content = kwargs.get("content", "Test content here")
        self.summary = kwargs.get("summary")
        self.tags = kwargs.get("tags", [])
        self.domain = kwargs.get("domain")
        self.skill_type = kwargs.get("skill_type")
        self.related_concepts = kwargs.get("related_concepts", [])
        self.concept_links = kwargs.get("concept_links", [])
        self.importance = kwargs.get("importance", 1)
        self.source_type = kwargs.get("source_type")
        self.source_reference = kwargs.get("source_reference")
        self.next_review = kwargs.get("next_review", datetime.now() + timedelta(days=1))
        self.interval_days = kwargs.get("interval_days", 1)
        self.ease_factor = kwargs.get("ease_factor", 2.5)
        self.review_count = kwargs.get("review_count", 0)
        self.last_review = kwargs.get("last_review")
        self.retention_score = kwargs.get("retention_score", 0.5)
        self.mastery_level = kwargs.get("mastery_level", 0.3)


_models_diary.GoalStatus = _GoalStatus
_models_diary.Goal = _FakeGoal
_models_diary.EmotionalState = _FakeEmotionalState
_models_diary.LearningEntry = _FakeLearningEntry
sys.modules.setdefault("models.diary", _models_diary)

# ---- api.schemas.diary stub ----
_schemas_diary = types.ModuleType("api.schemas.diary")


class _GoalCreate:
    def __init__(self, **kwargs):
        self.title = kwargs.get("title", "My Goal Title Long")
        self.description = kwargs.get("description", "")
        self.target_value = kwargs.get("target_value", 100.0)
        self.target_date = kwargs.get(
            "target_date", datetime.now() + timedelta(days=30)
        )
        self.unit = kwargs.get("unit", "tasks")
        self.category = kwargs.get("category")
        self.priority = kwargs.get("priority", 2)
        self.milestones = kwargs.get("milestones", [])
        self.specific = kwargs.get("specific")
        self.measurable = kwargs.get("measurable")
        self.achievable = kwargs.get("achievable")
        self.relevant = kwargs.get("relevant")


class _GoalUpdate:
    def __init__(self, **kwargs):
        self._data = kwargs

    def model_dump(self, exclude_unset=False):
        return {k: v for k, v in self._data.items() if v is not None}


class _GoalProgressUpdate:
    def __init__(self, **kwargs):
        self.progress = kwargs.get("progress")
        self.current_value = kwargs.get("current_value")
        self.note = kwargs.get("note")


class _GoalRiskResponse:
    def __init__(self, **kwargs):
        self.goal_id = kwargs.get("goal_id")
        self.is_at_risk = kwargs.get("is_at_risk", False)
        self.risk_level = kwargs.get("risk_level", "low")
        self.risk_factors = kwargs.get("risk_factors", [])
        self.recommendations = kwargs.get("recommendations", [])
        self.predicted_completion = kwargs.get("predicted_completion")
        self.on_track = kwargs.get("on_track", True)


class _EmotionalStateCreate:
    def __init__(self, **kwargs):
        self.confidence_level = kwargs.get("confidence_level", 7)
        self.frustration_score = kwargs.get("frustration_score", 0.0)
        self.retry_count = kwargs.get("retry_count", 0)
        self.error_count = kwargs.get("error_count", 0)
        self.flow_state = kwargs.get("flow_state", False)
        self.productivity_score = kwargs.get("productivity_score", 0.5)
        self.tasks_completed = kwargs.get("tasks_completed", 2)
        self.task_type = kwargs.get("task_type")
        self.trigger_factors = kwargs.get("trigger_factors")
        self.context_notes = kwargs.get("context_notes")


class _MoodTrendResponse:
    def __init__(self, **kwargs):
        self.period_start = kwargs.get("period_start")
        self.period_end = kwargs.get("period_end")
        self.data_points = kwargs.get("data_points", [])
        self.average_confidence = kwargs.get("average_confidence", 0)
        self.flow_state_percentage = kwargs.get("flow_state_percentage", 0)
        self.frustration_events = kwargs.get("frustration_events", 0)


class _LearningEntryCreate:
    def __init__(self, **kwargs):
        self.title = kwargs.get("title", "Test Entry")
        self.content = kwargs.get("content", "Some content here for testing")
        self.summary = kwargs.get("summary")
        self.tags = kwargs.get("tags", [])
        self.domain = kwargs.get("domain")
        self.skill_type = kwargs.get("skill_type")
        self.related_concepts = kwargs.get("related_concepts")
        self.importance = kwargs.get("importance", 1)
        self.source_type = kwargs.get("source_type")
        self.source_reference = kwargs.get("source_reference")


class _LearningReviewRequest:
    def __init__(self, **kwargs):
        self.entry_id = kwargs.get("entry_id", uuid4())
        self.remembered = kwargs.get("remembered", True)
        self.quality = kwargs.get("quality", 4)


class _LearningReviewResponse:
    def __init__(self, **kwargs):
        self.entry_id = kwargs.get("entry_id")
        self.next_review = kwargs.get("next_review")
        self.new_interval_days = kwargs.get("new_interval_days")
        self.retention_score = kwargs.get("retention_score")
        self.mastery_level = kwargs.get("mastery_level")


_schemas_diary.GoalCreate = _GoalCreate
_schemas_diary.GoalUpdate = _GoalUpdate
_schemas_diary.GoalProgressUpdate = _GoalProgressUpdate
_schemas_diary.GoalRiskResponse = _GoalRiskResponse
_schemas_diary.EmotionalStateCreate = _EmotionalStateCreate
_schemas_diary.MoodTrendResponse = _MoodTrendResponse
_schemas_diary.LearningEntryCreate = _LearningEntryCreate
_schemas_diary.LearningReviewRequest = _LearningReviewRequest
_schemas_diary.LearningReviewResponse = _LearningReviewResponse
sys.modules.setdefault("api.schemas.diary", _schemas_diary)

# Also expose under nested path
_api_schemas = types.ModuleType("api.schemas")
_api_schemas.diary = _schemas_diary
sys.modules.setdefault("api.schemas", _api_schemas)
_api_mod = types.ModuleType("api")
sys.modules.setdefault("api", _api_mod)
_models_mod = types.ModuleType("models")
sys.modules.setdefault("models", _models_mod)
_core_mod = types.ModuleType("core")
sys.modules.setdefault("core", _core_mod)
_core_unified = types.ModuleType("core.unified")
sys.modules.setdefault("core.unified", _core_unified)


# ---------------------------------------------------------------------------
# Module loader helper
# ---------------------------------------------------------------------------


def _mock_select(*args, **kwargs):
    """Intercept select() so it returns a chainable MagicMock."""
    m = MagicMock()
    m.where = MagicMock(return_value=m)
    m.order_by = MagicMock(return_value=m)
    m.limit = MagicMock(return_value=m)
    return m


def _mock_and_(*args, **kwargs):
    return MagicMock()


def _mock_desc(*args, **kwargs):
    return MagicMock()


def _load(name: str, rel_path: str):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(_BACKEND, rel_path)
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    # Patch the SQLAlchemy names that were bound at import time inside the module
    for _fn_name, _fn in [
        ("select", _mock_select),
        ("and_", _mock_and_),
        ("desc", _mock_desc),
    ]:
        if hasattr(mod, _fn_name):
            setattr(mod, _fn_name, _fn)
    return mod


# ---------------------------------------------------------------------------
# Load target modules
# ---------------------------------------------------------------------------

goal_mod = _load("services.goal_service", "services/goal_service.py")
emotional_mod = _load("services.emotional_service", "services/emotional_service.py")
journal_mod = _load(
    "services.learning_journal_service", "services/learning_journal_service.py"
)
logging_mod = _load("core.unified.logging_system", "core/unified/logging_system.py")

GoalService = goal_mod.GoalService
EmotionalService = emotional_mod.EmotionalService
LearningJournalService = journal_mod.LearningJournalService
UnifiedLoggingManager = logging_mod.UnifiedLoggingManager
LoggerConfig = logging_mod.LoggerConfig
LogLevel = logging_mod.LogLevel
LogCategory = logging_mod.LogCategory
LogFormat = logging_mod.LogFormat
LogMetrics = logging_mod.LogMetrics
TurkishJSONFormatter = logging_mod.TurkishJSONFormatter
StructuredTextFormatter = logging_mod.StructuredTextFormatter
get_logging_manager = logging_mod.get_logging_manager
get_logger = logging_mod.get_logger


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture
def mock_db() -> AsyncMock:
    """Mock AsyncSession."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def goal_service(mock_db: AsyncMock) -> GoalService:
    return GoalService(db=mock_db)


@pytest.fixture
def emotional_service(mock_db: AsyncMock) -> EmotionalService:
    return EmotionalService(db=mock_db)


@pytest.fixture
def journal_service(mock_db: AsyncMock) -> LearningJournalService:
    return LearningJournalService(db=mock_db)


def _make_goal(**kwargs) -> _FakeGoal:
    return _FakeGoal(**kwargs)


def _make_entry(**kwargs) -> _FakeLearningEntry:
    return _FakeLearningEntry(**kwargs)


def _make_state(**kwargs) -> _FakeEmotionalState:
    return _FakeEmotionalState(**kwargs)


def _make_scalars_result(items: list):
    """Return a mock that mimics await db.execute() -> .scalars().all()"""
    result = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = items
    result.scalars.return_value = scalars
    result.scalar_one_or_none.return_value = items[0] if items else None
    return result


# ===========================================================================
# GoalService Tests
# ===========================================================================


class TestGoalServiceValidateSmart:
    """Tests for validate_smart method (REQ-6.1)."""

    def test_fully_valid_goal(self, goal_service):
        goal = _GoalCreate(
            title="Complete 100 problems",
            target_value=100.0,
            target_date=datetime.now() + timedelta(days=10),
            specific="Finish 100 math problems",
            measurable="Count of completed problems",
            achievable="Yes, 10 per day",
            relevant="Improve YKS score",
        )
        result = goal_service.validate_smart(goal)
        assert result["is_valid"] is True
        assert result["score"] >= 3
        assert result["max_score"] == 5
        assert isinstance(result["missing"], list)
        assert isinstance(result["warnings"], list)

    def test_missing_title_length(self, goal_service):
        goal = _GoalCreate(title="Short", target_value=50.0)
        result = goal_service.validate_smart(goal)
        assert result["is_valid"] is False
        assert any("Specific" in m for m in result["missing"])

    def test_missing_target_value(self, goal_service):
        goal = _GoalCreate(title="A long enough title here", target_value=0.0)
        result = goal_service.validate_smart(goal)
        assert any("Measurable" in m for m in result["missing"])

    def test_past_target_date(self, goal_service):
        goal = _GoalCreate(
            title="A long enough title here",
            target_value=50.0,
            target_date=datetime.now() - timedelta(days=1),
        )
        result = goal_service.validate_smart(goal)
        assert any("Time-bound" in m for m in result["missing"])

    def test_no_target_date(self, goal_service):
        goal = _GoalCreate(title="A long enough title here", target_value=50.0)
        goal.target_date = None
        result = goal_service.validate_smart(goal)
        assert any("Time-bound" in m for m in result["missing"])

    def test_missing_smart_fields_generate_warnings(self, goal_service):
        goal = _GoalCreate(
            title="A long enough title here",
            target_value=50.0,
            target_date=datetime.now() + timedelta(days=10),
        )
        result = goal_service.validate_smart(goal)
        assert len(result["warnings"]) > 0


class TestGoalServiceCalculateProgress:
    """Tests for calculate_progress."""

    def test_zero_target_returns_zero(self, goal_service):
        assert goal_service.calculate_progress(50.0, 0.0) == 0

    def test_normal_progress(self, goal_service):
        result = goal_service.calculate_progress(50.0, 100.0)
        assert result == 50

    def test_exceeds_100_capped(self, goal_service):
        result = goal_service.calculate_progress(150.0, 100.0)
        assert result == 100

    def test_zero_current_returns_zero(self, goal_service):
        assert goal_service.calculate_progress(0.0, 100.0) == 0

    def test_exact_100(self, goal_service):
        assert goal_service.calculate_progress(100.0, 100.0) == 100


class TestGoalServiceVelocity:
    """Tests for calculate_velocity and predict_completion."""

    def test_velocity_no_start_date(self, goal_service):
        goal = _make_goal(start_date=None)
        assert goal_service.calculate_velocity(goal) == 0.0

    def test_velocity_with_start_date(self, goal_service):
        goal = _make_goal(
            start_date=datetime.now(tz=None) - timedelta(days=10),
            progress=50,
        )
        # Fix tzinfo matching
        goal.start_date = datetime.now() - timedelta(days=10)
        velocity = goal_service.calculate_velocity(goal)
        assert velocity == 5.0

    def test_predict_completion_zero_velocity(self, goal_service):
        goal = _make_goal(start_date=None, progress=0)
        result = goal_service.predict_completion(goal)
        assert result is None

    def test_predict_completion_with_velocity(self, goal_service):
        goal = _make_goal(
            start_date=datetime.now() - timedelta(days=10),
            progress=50,
        )
        result = goal_service.predict_completion(goal)
        assert result is not None
        assert isinstance(result, datetime)
        # Should predict ~10 more days for remaining 50%
        assert result > datetime.now()


class TestGoalServiceMilestones:
    """Tests for check_milestones and _generate_celebration."""

    def test_no_milestones_reached(self, goal_service):
        goal = _make_goal(progress=10, milestones=[])
        result = goal_service.check_milestones(goal, 15)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_default_25_milestone_reached(self, goal_service):
        goal = _make_goal(progress=10, milestones=[])
        result = goal_service.check_milestones(goal, 30)
        assert len(result) == 1
        assert result[0]["percentage"] == 25

    def test_multiple_milestones_reached(self, goal_service):
        goal = _make_goal(progress=0, milestones=[])
        result = goal_service.check_milestones(goal, 60)
        percentages = [r["percentage"] for r in result]
        assert 25 in percentages
        assert 50 in percentages

    def test_celebration_messages(self, goal_service):
        for pct in [25, 50, 75, 100]:
            msg = goal_service._generate_celebration("test", pct)
            assert isinstance(msg, str)
            assert len(msg) > 0

    def test_celebration_custom_percentage(self, goal_service):
        msg = goal_service._generate_celebration("My milestone", 30)
        assert "My milestone" in msg

    def test_custom_milestone_in_list(self, goal_service):
        goal = _make_goal(
            progress=0,
            milestones=[{"percentage": 30, "title": "30% done", "achieved": False}],
        )
        result = goal_service.check_milestones(goal, 35)
        assert any(r["percentage"] == 30 for r in result)


class TestGoalServiceRiskDetection:
    """Tests for detect_risk."""

    def test_no_risk_goal(self, goal_service):
        goal = _make_goal(
            start_date=datetime.now() - timedelta(days=5),
            target_date=datetime.now() + timedelta(days=30),
            progress=50,
            updated_at=datetime.now(),
        )
        result = goal_service.detect_risk(goal)
        assert hasattr(result, "is_at_risk")
        assert hasattr(result, "risk_level")
        assert hasattr(result, "risk_factors")
        assert hasattr(result, "recommendations")

    def test_time_pressure_risk(self, goal_service):
        goal = _make_goal(
            start_date=datetime.now() - timedelta(days=20),
            target_date=datetime.now() + timedelta(days=3),
            progress=20,
            updated_at=datetime.now(),
        )
        result = goal_service.detect_risk(goal)
        assert result.is_at_risk is True

    def test_overdue_goal_risk(self, goal_service):
        goal = _make_goal(
            start_date=datetime.now() - timedelta(days=30),
            target_date=datetime.now() - timedelta(days=2),
            progress=50,
            updated_at=datetime.now(),
        )
        result = goal_service.detect_risk(goal)
        assert result.is_at_risk is True
        assert any("gecmis" in r.lower() for r in result.risk_factors)

    def test_stale_update_risk(self, goal_service):
        goal = _make_goal(
            start_date=datetime.now() - timedelta(days=30),
            target_date=datetime.now() + timedelta(days=30),
            progress=20,
            updated_at=datetime.now() - timedelta(days=10),
        )
        result = goal_service.detect_risk(goal)
        assert result.is_at_risk is True

    def test_risk_level_high_multiple_factors(self, goal_service):
        goal = _make_goal(
            start_date=datetime.now() - timedelta(days=30),
            target_date=datetime.now() - timedelta(days=1),
            progress=10,
            updated_at=datetime.now() - timedelta(days=15),
        )
        result = goal_service.detect_risk(goal)
        assert result.risk_level in ("medium", "high")

    def test_expected_velocity_no_dates(self, goal_service):
        goal = _make_goal(start_date=None, target_date=None)
        velocity = goal_service._calculate_expected_velocity(goal)
        assert velocity == 1.0


class TestGoalServiceCRUD:
    """Tests for async CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_goal_returns_none_when_not_found(self, goal_service, mock_db):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result_mock

        result = await goal_service.get_goal(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_goal_returns_goal(self, goal_service, mock_db):
        goal = _make_goal()
        mock_db.execute.return_value = _make_scalars_result([goal])
        result = await goal_service.get_goal(goal.id)
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_goals_empty(self, goal_service, mock_db):
        mock_db.execute.return_value = _make_scalars_result([])
        result = await goal_service.get_goals(uuid4())
        assert result == []

    @pytest.mark.asyncio
    async def test_get_goals_with_items(self, goal_service, mock_db):
        goals = [_make_goal(), _make_goal()]
        mock_db.execute.return_value = _make_scalars_result(goals)
        result = await goal_service.get_goals(uuid4())
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_delete_goal_not_found(self, goal_service, mock_db):
        mock_db.execute.return_value = _make_scalars_result([])
        result = await goal_service.delete_goal(uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_goal_success(self, goal_service, mock_db):
        goal = _make_goal()
        mock_db.execute.return_value = _make_scalars_result([goal])
        result = await goal_service.delete_goal(goal.id)
        assert result is True
        mock_db.delete.assert_called_once_with(goal)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_goal_success(self, goal_service, mock_db):
        user_id = uuid4()
        goal_data = _GoalCreate(
            title="Finish 100 problems",
            target_value=100.0,
            target_date=datetime.now() + timedelta(days=30),
        )

        created_goal = _make_goal(user_id=user_id, title=goal_data.title)
        mock_db.refresh.side_effect = lambda g: None

        # Patch the Goal class in the service module
        with patch.object(goal_mod, "Goal", side_effect=lambda **kw: created_goal):
            mock_db.refresh = AsyncMock(return_value=None)
            result = await goal_service.create_goal(user_id, goal_data)

        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_adjust_goal_not_found(self, goal_service, mock_db):
        mock_db.execute.return_value = _make_scalars_result([])
        result = await goal_service.adjust_goal(uuid4(), reason="test")
        assert result is None

    @pytest.mark.asyncio
    async def test_adjust_goal_updates_value(self, goal_service, mock_db):
        goal = _make_goal(target_value=100.0, current_value=30.0)
        mock_db.execute.return_value = _make_scalars_result([goal])
        result = await goal_service.adjust_goal(
            goal.id,
            reason="Too hard",
            new_target_value=80.0,
        )
        assert goal.target_value == 80.0
        assert len(goal.adjustments) == 1
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_retrospective_not_found(self, goal_service, mock_db):
        mock_db.execute.return_value = _make_scalars_result([])
        result = await goal_service.create_retrospective(
            uuid4(), lessons_learned=[], success_factors=[], challenges_faced=[]
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_goal_statistics(self, goal_service, mock_db):
        uid = uuid4()
        goals = [
            _make_goal(status=_GoalStatus.COMPLETED, is_at_risk=False, category="math"),
            _make_goal(status=_GoalStatus.ACTIVE, is_at_risk=True, category="math"),
            _make_goal(
                status=_GoalStatus.CANCELLED, is_at_risk=False, category="science"
            ),
        ]
        mock_db.execute.return_value = _make_scalars_result(goals)
        stats = await goal_service.get_goal_statistics(uid)

        assert stats["total_goals"] == 3
        assert stats["completed"] == 1
        assert stats["active"] == 1
        assert stats["cancelled"] == 1
        assert stats["at_risk"] == 1
        assert 0.0 <= stats["completion_rate"] <= 100.0
        assert "math" in stats["category_distribution"]


# ===========================================================================
# EmotionalService Tests
# ===========================================================================


class TestEmotionalServiceFrustration:
    """Tests for _calculate_frustration (REQ-5.2)."""

    def test_zero_frustration(self, emotional_service):
        score = emotional_service._calculate_frustration(0, 0, 0.0)
        assert score == 0.0

    def test_retry_contributes(self, emotional_service):
        score = emotional_service._calculate_frustration(3, 0, 0.0)
        assert score > 0
        assert score <= 1.0

    def test_error_contributes(self, emotional_service):
        score = emotional_service._calculate_frustration(0, 5, 0.0)
        assert score > 0
        assert score <= 1.0

    def test_user_score_contributes(self, emotional_service):
        score = emotional_service._calculate_frustration(0, 0, 1.0)
        assert score == pytest.approx(0.2, abs=0.01)

    def test_max_frustration_capped_at_1(self, emotional_service):
        score = emotional_service._calculate_frustration(100, 100, 1.0)
        assert score == 1.0

    def test_negative_values_clamped(self, emotional_service):
        score = emotional_service._calculate_frustration(0, 0, -1.0)
        assert score >= 0.0


class TestEmotionalServiceFlowState:
    """Tests for _identify_flow_state (REQ-5.3)."""

    def test_user_says_flow_is_true(self, emotional_service):
        result = emotional_service._identify_flow_state(3, 0.1, 0, True)
        assert result is True

    def test_auto_detect_flow_all_met(self, emotional_service):
        result = emotional_service._identify_flow_state(8, 0.8, 4, False)
        assert result is True

    def test_auto_detect_no_flow_low_confidence(self, emotional_service):
        result = emotional_service._identify_flow_state(5, 0.9, 5, False)
        assert result is False

    def test_auto_detect_no_flow_low_productivity(self, emotional_service):
        result = emotional_service._identify_flow_state(9, 0.5, 5, False)
        assert result is False

    def test_auto_detect_no_flow_few_tasks(self, emotional_service):
        result = emotional_service._identify_flow_state(9, 0.9, 1, False)
        assert result is False

    def test_boundary_values(self, emotional_service):
        # Exactly at threshold
        result = emotional_service._identify_flow_state(7, 0.7, 3, False)
        assert result is True


class TestEmotionalServiceFrustrationPatterns:
    """Tests for detect_frustration_patterns (REQ-5.2)."""

    @pytest.mark.asyncio
    async def test_no_data_returns_empty_response(self, emotional_service, mock_db):
        mock_db.execute.return_value = _make_scalars_result([])
        result = await emotional_service.detect_frustration_patterns(uuid4(), days=7)
        assert result["total_states"] == 0
        assert result["high_frustration_events"] == 0
        assert "recommendation" in result

    @pytest.mark.asyncio
    async def test_with_high_frustration_states(self, emotional_service, mock_db):
        states = [
            _make_state(frustration_score=0.8, task_type="coding"),
            _make_state(frustration_score=0.3, task_type="reading"),
            _make_state(frustration_score=0.9, task_type="coding"),
        ]
        mock_db.execute.return_value = _make_scalars_result(states)
        result = await emotional_service.detect_frustration_patterns(uuid4(), days=7)
        assert result["total_states"] == 3
        assert result["high_frustration_events"] == 2
        assert result["high_frustration_percentage"] == pytest.approx(66.7, abs=1.0)

    def test_generate_frustration_recommendation_no_events(self, emotional_service):
        msg = emotional_service._generate_frustration_recommendation([], [])
        assert "kontrol" in msg.lower() or "frustration" in msg.lower()

    def test_generate_frustration_recommendation_with_tasks(self, emotional_service):
        msg = emotional_service._generate_frustration_recommendation(
            [MagicMock()],
            [{"task_type": "coding"}],
        )
        assert "coding" in msg


class TestEmotionalServiceFlowStats:
    """Tests for get_flow_statistics (REQ-5.3)."""

    @pytest.mark.asyncio
    async def test_no_data_returns_zeros(self, emotional_service, mock_db):
        mock_db.execute.return_value = _make_scalars_result([])
        result = await emotional_service.get_flow_statistics(uuid4(), days=30)
        assert result["total_states"] == 0
        assert result["flow_count"] == 0

    @pytest.mark.asyncio
    async def test_flow_percentage_calculated(self, emotional_service, mock_db):
        states = [
            _make_state(flow_state=True, task_type="math"),
            _make_state(flow_state=True, task_type="math"),
            _make_state(flow_state=False, task_type="reading"),
            _make_state(flow_state=False, task_type="reading"),
        ]
        mock_db.execute.return_value = _make_scalars_result(states)
        result = await emotional_service.get_flow_statistics(uuid4(), days=30)
        assert result["flow_count"] == 2
        assert result["flow_percentage"] == 50.0


class TestEmotionalServiceEmotionalPatterns:
    """Tests for analyze_emotional_patterns (REQ-5.4)."""

    @pytest.mark.asyncio
    async def test_insufficient_data(self, emotional_service, mock_db):
        mock_db.execute.return_value = _make_scalars_result([_make_state()])
        result = await emotional_service.analyze_emotional_patterns(uuid4(), days=30)
        assert "insights" in result
        assert any("veri" in i.lower() for i in result["insights"])

    @pytest.mark.asyncio
    async def test_sufficient_data_returns_patterns(self, emotional_service, mock_db):
        states = [
            _make_state(
                confidence_level=8,
                task_type="coding",
                timestamp=datetime.now() - timedelta(days=i),
            )
            for i in range(6)
        ]
        mock_db.execute.return_value = _make_scalars_result(states)
        result = await emotional_service.analyze_emotional_patterns(uuid4(), days=30)
        assert "patterns" in result
        assert "total_states_analyzed" in result
        assert result["total_states_analyzed"] == 6


class TestEmotionalServiceMoodTrend:
    """Tests for get_mood_trend (REQ-5.5)."""

    @pytest.mark.asyncio
    async def test_empty_trend(self, emotional_service, mock_db):
        mock_db.execute.return_value = _make_scalars_result([])
        result = await emotional_service.get_mood_trend(uuid4(), days=30)
        assert result.average_confidence == 0
        assert result.flow_state_percentage == 0
        assert result.frustration_events == 0
        assert result.data_points == []

    @pytest.mark.asyncio
    async def test_trend_with_data(self, emotional_service, mock_db):
        states = [
            _make_state(
                confidence_level=8,
                frustration_score=0.2,
                flow_state=True,
                productivity_score=0.8,
            ),
            _make_state(
                confidence_level=5,
                frustration_score=0.7,
                flow_state=False,
                productivity_score=0.4,
            ),
        ]
        mock_db.execute.return_value = _make_scalars_result(states)
        result = await emotional_service.get_mood_trend(uuid4(), days=30)
        assert result.average_confidence == 6.5
        assert result.frustration_events == 1
        assert len(result.data_points) == 2


class TestEmotionalServiceSelfAwareness:
    """Tests for _calculate_self_awareness (REQ-5.6)."""

    @pytest.mark.asyncio
    async def test_insufficient_data_returns_default(self, emotional_service, mock_db):
        mock_db.execute.return_value = _make_scalars_result([_make_state()])
        score = await emotional_service._calculate_self_awareness(uuid4())
        assert score == 50.0

    @pytest.mark.asyncio
    async def test_with_prediction_accuracy(self, emotional_service, mock_db):
        states = [
            _make_state(predicted_state="high", actual_state="high"),
            _make_state(predicted_state="low", actual_state="high"),
            _make_state(predicted_state="high", actual_state="high"),
            _make_state(frustration_score=0.7),
            _make_state(frustration_score=0.3),
            _make_state(confidence_level=8),
        ]
        mock_db.execute.return_value = _make_scalars_result(states)
        score = await emotional_service._calculate_self_awareness(uuid4())
        assert 0 <= score <= 100


class TestEmotionalServiceCRUD:
    """Tests for async CRUD operations in EmotionalService."""

    @pytest.mark.asyncio
    async def test_get_states_empty(self, emotional_service, mock_db):
        mock_db.execute.return_value = _make_scalars_result([])
        result = await emotional_service.get_states(uuid4())
        assert result == []

    @pytest.mark.asyncio
    async def test_get_state_by_id_not_found(self, emotional_service, mock_db):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result_mock
        result = await emotional_service.get_state_by_id(uuid4(), uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_state_not_found(self, emotional_service, mock_db):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result_mock
        result = await emotional_service.delete_state(uuid4(), uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_state_success(self, emotional_service, mock_db):
        state = _make_state()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = state
        mock_db.execute.return_value = result_mock
        result = await emotional_service.delete_state(state.id, state.user_id)
        assert result is True
        mock_db.delete.assert_called_once_with(state)


# ===========================================================================
# LearningJournalService Tests
# ===========================================================================


class TestLearningJournalServiceAutoTag:
    """Tests for auto_tag method (REQ-4.2)."""

    def test_detects_backend_tag(self, journal_service):
        tags = journal_service.auto_tag("FastAPI REST server", "Backend Development")
        assert "backend" in tags

    def test_detects_frontend_tag(self, journal_service):
        tags = journal_service.auto_tag("React component with TypeScript", "UI dev")
        assert "frontend" in tags

    def test_detects_testing_tag(self, journal_service):
        tags = journal_service.auto_tag("pytest mock and coverage", "testing")
        assert "testing" in tags

    def test_detects_database_tag(self, journal_service):
        tags = journal_service.auto_tag("postgresql index optimization", "DB perf")
        assert "database" in tags

    def test_detects_security_tag(self, journal_service):
        tags = journal_service.auto_tag("jwt auth and oauth", "security")
        assert "security" in tags

    def test_returns_max_10_tags(self, journal_service):
        # Text that matches many categories
        text = "react fastapi postgresql docker jwt pytest git python javascript"
        tags = journal_service.auto_tag(text, text)
        assert len(tags) <= 10

    def test_no_match_returns_empty(self, journal_service):
        tags = journal_service.auto_tag("nothing relevant here", "random title")
        assert isinstance(tags, list)

    def test_python_skill_detected(self, journal_service):
        tags = journal_service.auto_tag("python virtualenv setup", "Python")
        assert "python" in tags

    def test_git_skill_detected(self, journal_service):
        tags = journal_service.auto_tag("git commit and merge strategy", "VCS")
        assert "git" in tags


class TestLearningJournalServiceGraphStats:
    """Tests for get_graph_statistics."""

    def test_empty_graph_returns_zeros(self, journal_service):
        G = _nx.Graph()
        result = journal_service.get_graph_statistics(G)
        assert result["node_count"] == 0
        assert result["edge_count"] == 0
        assert result["density"] == 0
        assert result["central_nodes"] == []

    def test_graph_with_nodes(self, journal_service):
        G = _nx.Graph()
        G.add_node("a", label="Entry A")
        G.add_node("b", label="Entry B")
        G.add_edge("a", "b")
        result = journal_service.get_graph_statistics(G)
        assert result["node_count"] == 2
        assert result["edge_count"] == 1
        assert "central_nodes" in result


class TestLearningJournalServiceSpacedRepetition:
    """Tests for record_review (REQ-4.4)."""

    @pytest.mark.asyncio
    async def test_record_review_not_found(self, journal_service, mock_db):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result_mock

        data = _LearningReviewRequest(entry_id=uuid4(), remembered=True, quality=4)
        result = await journal_service.record_review(uuid4(), data)
        assert result is None

    @pytest.mark.asyncio
    async def test_record_review_successful_extends_interval(
        self, journal_service, mock_db
    ):
        entry = _make_entry(
            interval_days=7,
            ease_factor=2.5,
            review_count=3,
            retention_score=0.7,
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = entry
        mock_db.execute.return_value = result_mock

        data = _LearningReviewRequest(entry_id=entry.id, remembered=True, quality=4)
        result = await journal_service.record_review(entry.user_id, data)
        assert result is not None
        assert result.new_interval_days > 7
        assert result.retention_score > 0.7

    @pytest.mark.asyncio
    async def test_record_review_failed_shortens_interval(
        self, journal_service, mock_db
    ):
        entry = _make_entry(
            interval_days=14,
            ease_factor=2.5,
            review_count=5,
            retention_score=0.8,
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = entry
        mock_db.execute.return_value = result_mock

        data = _LearningReviewRequest(entry_id=entry.id, remembered=False, quality=2)
        result = await journal_service.record_review(entry.user_id, data)
        assert result is not None
        assert result.new_interval_days < 14

    @pytest.mark.asyncio
    async def test_ease_factor_adjusted_up(self, journal_service, mock_db):
        entry = _make_entry(
            ease_factor=2.5, interval_days=7, review_count=0, retention_score=0.5
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = entry
        mock_db.execute.return_value = result_mock

        data = _LearningReviewRequest(entry_id=entry.id, remembered=True, quality=5)
        await journal_service.record_review(entry.user_id, data)
        assert entry.ease_factor > 2.5

    @pytest.mark.asyncio
    async def test_ease_factor_adjusted_down(self, journal_service, mock_db):
        entry = _make_entry(
            ease_factor=2.5, interval_days=7, review_count=0, retention_score=0.5
        )
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = entry
        mock_db.execute.return_value = result_mock

        data = _LearningReviewRequest(entry_id=entry.id, remembered=False, quality=1)
        await journal_service.record_review(entry.user_id, data)
        assert entry.ease_factor < 2.5


class TestLearningJournalServiceGapDetection:
    """Tests for detect_gaps (REQ-4.5)."""

    @pytest.mark.asyncio
    async def test_no_entries_returns_no_entries_gap(self, journal_service, mock_db):
        mock_db.execute.return_value = _make_scalars_result([])
        gaps = await journal_service.detect_gaps(uuid4())
        assert len(gaps) == 1
        assert gaps[0]["type"] == "no_entries"

    @pytest.mark.asyncio
    async def test_missing_domains_detected(self, journal_service, mock_db):
        # Only backend entries — other domains are gaps
        entries = [_make_entry(domain="backend") for _ in range(3)]
        mock_db.execute.return_value = _make_scalars_result(entries)
        gaps = await journal_service.detect_gaps(uuid4())
        gap_domains = [g.get("domain") for g in gaps if g["type"] == "missing_domain"]
        assert "frontend" in gap_domains

    @pytest.mark.asyncio
    async def test_low_retention_gap(self, journal_service, mock_db):
        entries = [
            _make_entry(retention_score=0.3, review_count=3, domain="backend"),
            _make_entry(retention_score=0.2, review_count=4, domain="backend"),
            _make_entry(retention_score=0.9, review_count=5, domain="backend"),
        ]
        mock_db.execute.return_value = _make_scalars_result(entries)
        gaps = await journal_service.detect_gaps(uuid4())
        gap_types = [g["type"] for g in gaps]
        assert "low_retention" in gap_types

    @pytest.mark.asyncio
    async def test_stale_knowledge_gap(self, journal_service, mock_db):
        old_date = datetime.now() - timedelta(days=70)
        entries = [
            _make_entry(last_review=old_date, domain="backend") for _ in range(6)
        ]
        mock_db.execute.return_value = _make_scalars_result(entries)
        gaps = await journal_service.detect_gaps(uuid4())
        gap_types = [g["type"] for g in gaps]
        assert "stale_knowledge" in gap_types


class TestLearningJournalServiceCRUD:
    """Tests for async CRUD and search operations."""

    @pytest.mark.asyncio
    async def test_get_entries_empty(self, journal_service, mock_db):
        mock_db.execute.return_value = _make_scalars_result([])
        result = await journal_service.get_entries(uuid4())
        assert result == []

    @pytest.mark.asyncio
    async def test_get_entries_with_tag_filter(self, journal_service, mock_db):
        entries = [
            _make_entry(tags=["python", "backend"]),
            _make_entry(tags=["javascript"]),
        ]
        mock_db.execute.return_value = _make_scalars_result(entries)
        result = await journal_service.get_entries(uuid4(), tag="python")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_entry_by_id_not_found(self, journal_service, mock_db):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result_mock
        result = await journal_service.get_entry_by_id(uuid4(), uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_entry_not_found(self, journal_service, mock_db):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result_mock
        result = await journal_service.delete_entry(uuid4(), uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_entry_success(self, journal_service, mock_db):
        entry = _make_entry()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = entry
        mock_db.execute.return_value = result_mock
        result = await journal_service.delete_entry(entry.id, entry.user_id)
        assert result is True
        assert journal_service._knowledge_graph is None

    @pytest.mark.asyncio
    async def test_link_concepts_not_found(self, journal_service, mock_db):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result_mock
        result = await journal_service.link_concepts(uuid4(), uuid4(), ["concept1"])
        assert result is None

    @pytest.mark.asyncio
    async def test_link_concepts_success(self, journal_service, mock_db):
        entry = _make_entry(related_concepts=["existing"], concept_links=[])
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = entry
        mock_db.execute.return_value = result_mock

        result = await journal_service.link_concepts(
            entry.id, entry.user_id, ["new_concept"]
        )
        assert "new_concept" in entry.related_concepts
        assert journal_service._knowledge_graph is None

    @pytest.mark.asyncio
    async def test_search_entries_by_title(self, journal_service, mock_db):
        entries = [
            _make_entry(title="Python Basics", content="Learn python programming"),
            _make_entry(title="JavaScript Intro", content="JS fundamentals"),
        ]
        mock_db.execute.return_value = _make_scalars_result(entries)
        result = await journal_service.search_entries(uuid4(), "python")
        assert len(result) == 1
        assert result[0].title == "Python Basics"

    @pytest.mark.asyncio
    async def test_search_entries_by_tag(self, journal_service, mock_db):
        entries = [
            _make_entry(title="Entry A", content="some content", tags=["api"]),
            _make_entry(title="Entry B", content="other content", tags=["ui"]),
        ]
        mock_db.execute.return_value = _make_scalars_result(entries)
        result = await journal_service.search_entries(uuid4(), "api")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_entries_no_match(self, journal_service, mock_db):
        entries = [_make_entry(title="Python", content="python stuff", tags=[])]
        mock_db.execute.return_value = _make_scalars_result(entries)
        result = await journal_service.search_entries(uuid4(), "zzznomatch")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_related_entries_not_found(self, journal_service, mock_db):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result_mock
        result = await journal_service.get_related_entries(uuid4(), uuid4())
        assert result == []

    @pytest.mark.asyncio
    async def test_get_knowledge_graph_uses_cache(self, journal_service, mock_db):
        cached_graph = _nx.Graph()
        journal_service._knowledge_graph = cached_graph
        result = await journal_service.get_knowledge_graph(uuid4())
        # Should return cache without hitting DB
        assert result is cached_graph
        mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_tags_not_found(self, journal_service, mock_db):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result_mock
        result = await journal_service.update_tags(uuid4(), uuid4(), ["tag1"])
        assert result is None


# ===========================================================================
# UnifiedLoggingManager / logging_system Tests
# ===========================================================================


class TestLogLevel:
    def test_all_levels_defined(self):
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.CRITICAL.value == "CRITICAL"


class TestLogCategory:
    def test_all_categories_defined(self):
        categories = [c.value for c in LogCategory]
        assert "api" in categories
        assert "auth" in categories
        assert "database" in categories
        assert "security" in categories
        assert "system" in categories


class TestLogMetrics:
    def test_initial_counts_are_zero(self):
        metrics = LogMetrics()
        assert all(v == 0 for v in metrics.counts.values())

    def test_increment_level(self):
        metrics = LogMetrics()
        metrics.increment("INFO")
        assert metrics.counts["INFO"] == 1

    def test_increment_category(self):
        metrics = LogMetrics()
        metrics.increment("ERROR", "api")
        assert metrics.categories["api"] == 1

    def test_increment_unknown_level_is_ignored(self):
        metrics = LogMetrics()
        metrics.increment("UNKNOWN_LEVEL")
        # No crash, no entry added
        assert "UNKNOWN_LEVEL" not in metrics.counts

    def test_add_error(self):
        metrics = LogMetrics()
        metrics.add_error({"message": "test error", "level": "ERROR"})
        assert len(metrics.errors) == 1
        assert "timestamp" in metrics.errors[0]

    def test_error_list_capped_at_100(self):
        metrics = LogMetrics()
        for i in range(110):
            metrics.add_error({"message": f"error {i}"})
        assert len(metrics.errors) == 100

    def test_get_summary_structure(self):
        metrics = LogMetrics()
        metrics.increment("INFO")
        metrics.increment("ERROR", "api")
        summary = metrics.get_summary()
        assert "total_logs" in summary
        assert "log_levels" in summary
        assert "categories" in summary
        assert "error_count" in summary
        assert "uptime_seconds" in summary
        assert summary["total_logs"] == 2


class TestTurkishJSONFormatter:
    def test_format_basic_record(self):
        formatter = TurkishJSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        import json

        data = json.loads(output)
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert "timestamp" in data
        assert "logger" in data

    def test_format_with_exception(self):
        formatter = TurkishJSONFormatter()
        try:
            raise ValueError("test exception")
        except ValueError:
            import sys as _sys

            exc_info = _sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        output = formatter.format(record)
        import json

        data = json.loads(output)
        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"

    def test_turkish_characters_preserved(self):
        formatter = TurkishJSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Türkçe karakter testi: İğüşçö",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        assert "Türkçe" in output
        assert "İğüşçö" in output


class TestStructuredTextFormatter:
    def test_format_info_record(self):
        formatter = StructuredTextFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=5,
            msg="Info message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        assert "INFO" in output
        assert "Info message" in output

    def test_format_debug_includes_location(self):
        formatter = StructuredTextFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=10,
            msg="Debug message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        assert "DEBUG" in output
        assert "10" in output  # lineno included for DEBUG

    def test_format_error_with_exception(self):
        formatter = StructuredTextFormatter()
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            import sys as _sys

            exc_info = _sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Something broke",
            args=(),
            exc_info=exc_info,
        )
        output = formatter.format(record)
        assert "boom" in output


class TestLoggerConfig:
    def test_default_config(self, tmp_path):
        config = LoggerConfig(log_dir=str(tmp_path / "logs"))
        assert config.name == "kiro2"
        assert config.level == LogLevel.INFO
        assert config.format_type == LogFormat.JSON
        assert config.enable_console is True
        assert config.enable_file is True

    def test_custom_config(self, tmp_path):
        config = LoggerConfig(
            name="test_logger",
            level=LogLevel.DEBUG,
            log_dir=str(tmp_path / "custom_logs"),
            format_type=LogFormat.STRUCTURED,
            enable_file=False,
        )
        assert config.name == "test_logger"
        assert config.level == LogLevel.DEBUG
        assert config.format_type == LogFormat.STRUCTURED
        assert config.enable_file is False

    def test_log_dir_created(self, tmp_path):
        log_dir = tmp_path / "new_logs"
        assert not log_dir.exists()
        config = LoggerConfig(log_dir=str(log_dir))
        assert log_dir.exists()


class TestUnifiedLoggingManager:
    def test_initialization(self, tmp_path):
        config = LoggerConfig(log_dir=str(tmp_path / "logs"), enable_file=False)
        manager = UnifiedLoggingManager(config=config)
        assert not manager._initialized
        manager.initialize()
        assert manager._initialized

    def test_initialize_idempotent(self, tmp_path):
        config = LoggerConfig(log_dir=str(tmp_path / "logs"), enable_file=False)
        manager = UnifiedLoggingManager(config=config)
        manager.initialize()
        first_count = len(manager.loggers)
        manager.initialize()  # Second call should be no-op
        assert len(manager.loggers) == first_count

    def test_get_logger_by_name(self, tmp_path):
        config = LoggerConfig(log_dir=str(tmp_path / "logs"), enable_file=False)
        manager = UnifiedLoggingManager(config=config)
        log = manager.get_logger(name="test_logger")
        assert isinstance(log, logging.Logger)

    def test_get_logger_by_category(self, tmp_path):
        config = LoggerConfig(log_dir=str(tmp_path / "logs"), enable_file=False)
        manager = UnifiedLoggingManager(config=config)
        log = manager.get_logger(category=LogCategory.AUTH)
        assert isinstance(log, logging.Logger)

    def test_get_logger_default(self, tmp_path):
        config = LoggerConfig(log_dir=str(tmp_path / "logs"), enable_file=False)
        manager = UnifiedLoggingManager(config=config)
        log = manager.get_logger()
        assert isinstance(log, logging.Logger)

    def test_log_structured_info(self, tmp_path):
        config = LoggerConfig(
            log_dir=str(tmp_path / "logs"),
            enable_file=False,
            enable_console=False,
        )
        manager = UnifiedLoggingManager(config=config)
        manager.initialize()
        # Should not raise
        manager.log_structured(LogLevel.INFO, "test message", LogCategory.API)
        assert manager.metrics.counts["INFO"] == 1
        assert manager.metrics.categories["api"] == 1

    def test_log_structured_error_tracked(self, tmp_path):
        config = LoggerConfig(
            log_dir=str(tmp_path / "logs"),
            enable_file=False,
            enable_console=False,
        )
        manager = UnifiedLoggingManager(config=config)
        manager.initialize()
        manager.log_structured(LogLevel.ERROR, "error occurred", LogCategory.SYSTEM)
        assert len(manager.metrics.errors) == 1

    def test_convenience_methods(self, tmp_path):
        config = LoggerConfig(
            log_dir=str(tmp_path / "logs"),
            enable_file=False,
            enable_console=False,
        )
        manager = UnifiedLoggingManager(config=config)
        manager.initialize()
        # All should not raise
        manager.debug("debug msg")
        manager.info("info msg")
        manager.warning("warning msg")
        manager.error("error msg", exc_info=False)
        manager.critical("critical msg", exc_info=False)
        assert manager.metrics.counts["DEBUG"] == 1
        assert manager.metrics.counts["INFO"] == 1
        assert manager.metrics.counts["WARNING"] == 1

    def test_log_execution_time_success(self, tmp_path):
        config = LoggerConfig(
            log_dir=str(tmp_path / "logs"),
            enable_file=False,
            enable_console=False,
        )
        manager = UnifiedLoggingManager(config=config)
        manager.initialize()
        with manager.log_execution_time("test_operation"):
            pass  # No exception
        # Should have logged the completion
        assert manager.metrics.counts["INFO"] >= 1

    def test_log_execution_time_failure(self, tmp_path):
        config = LoggerConfig(
            log_dir=str(tmp_path / "logs"),
            enable_file=False,
            enable_console=False,
        )
        manager = UnifiedLoggingManager(config=config)
        manager.initialize()
        # Patch manager.error to avoid exc_info LogRecord key collision in test env
        manager.error = MagicMock()
        with pytest.raises(ValueError):
            with manager.log_execution_time("failing_op"):
                raise ValueError("test failure")
        # Verify error was called (context manager re-raises and records)
        manager.error.assert_called_once()
        call_args = manager.error.call_args
        assert "failing_op" in call_args[0][0]

    def test_get_metrics(self, tmp_path):
        config = LoggerConfig(
            log_dir=str(tmp_path / "logs"),
            enable_file=False,
            enable_console=False,
        )
        manager = UnifiedLoggingManager(config=config)
        manager.initialize()
        manager.info("test")
        metrics = manager.get_metrics()
        assert "total_logs" in metrics
        assert metrics["total_logs"] >= 1

    def test_health_check(self, tmp_path):
        config = LoggerConfig(
            log_dir=str(tmp_path / "logs"),
            enable_file=False,
            enable_console=False,
        )
        manager = UnifiedLoggingManager(config=config)
        manager.initialize()
        health = manager.health_check()
        assert health["initialized"] is True
        assert "loggers_count" in health
        assert "log_directory_writable" in health
        assert health["log_directory_writable"] is True

    def test_cleanup_old_logs_no_files(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        config = LoggerConfig(
            log_dir=str(log_dir),
            enable_file=False,
            enable_console=False,
            retention_days=30,
        )
        manager = UnifiedLoggingManager(config=config)
        manager.initialize()
        removed = manager.cleanup_old_logs()
        assert removed == 0

    def test_cleanup_old_logs_retention_zero(self, tmp_path):
        config = LoggerConfig(
            log_dir=str(tmp_path / "logs"),
            enable_file=False,
            enable_console=False,
            retention_days=0,
        )
        manager = UnifiedLoggingManager(config=config)
        manager.initialize()
        removed = manager.cleanup_old_logs()
        assert removed == 0

    def test_structured_text_format_mode(self, tmp_path):
        config = LoggerConfig(
            log_dir=str(tmp_path / "logs"),
            enable_file=False,
            enable_console=False,
            format_type=LogFormat.STRUCTURED,
        )
        manager = UnifiedLoggingManager(config=config)
        manager.initialize()
        manager.info("structured text test")

    def test_backward_compat_aliases(self):
        assert logging_mod.LogConfig is LoggerConfig
        assert logging_mod.StructuredLogger is UnifiedLoggingManager
        assert logging_mod.LoggingConfig is UnifiedLoggingManager

    def test_get_logging_manager_returns_instance(self, tmp_path, monkeypatch):
        # Reset global state for this test
        monkeypatch.setattr(logging_mod, "_logging_manager", None)
        manager = get_logging_manager()
        assert isinstance(manager, UnifiedLoggingManager)
        assert manager._initialized

    def test_get_logger_convenience(self, tmp_path, monkeypatch):
        monkeypatch.setattr(logging_mod, "_logging_manager", None)
        log = get_logger(name="convenience_test")
        assert isinstance(log, logging.Logger)

    def test_with_file_handler(self, tmp_path):
        config = LoggerConfig(
            log_dir=str(tmp_path / "logs"),
            enable_file=True,
            enable_console=False,
            enable_rotation=True,
        )
        manager = UnifiedLoggingManager(config=config)
        manager.initialize()
        manager.info("file handler test")
        assert manager._initialized

    def test_with_file_handler_no_rotation(self, tmp_path):
        config = LoggerConfig(
            log_dir=str(tmp_path / "logs"),
            enable_file=True,
            enable_console=False,
            enable_rotation=False,
        )
        manager = UnifiedLoggingManager(config=config)
        manager.initialize()
        manager.info("no rotation test")
        assert manager._initialized
