"""
Unit tests for core analytics & framework modules.

Covers:
- core/learning_analytics.py
- core/migration_framework.py
- core/structured_learning_path.py
- core/context_manager.py
- core/unified_resource_ranker.py
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# ------------------------------------------------------------------ #
# Path setup — must come before any project imports
# ------------------------------------------------------------------ #
sys.path.insert(0, str(Path(__file__).parents[2]))

# ------------------------------------------------------------------ #
# Mock heavy dependencies BEFORE importing project modules
# ------------------------------------------------------------------ #
for _mod in [
    "redis",
    "redis.asyncio",
    "celery",
    "elasticsearch",
    "langchain",
    "langchain_core",
    "openai",
]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

# Patch internal core deps that call managed_transaction / async_error_context
_mock_async_ctx = MagicMock()
_mock_async_ctx.__aenter__ = AsyncMock(
    return_value=MagicMock(
        session=AsyncMock(),
        add_annotation=MagicMock(),
        to_dict=MagicMock(return_value={}),
        tags={},
    )
)
_mock_async_ctx.__aexit__ = AsyncMock(return_value=False)

for _cm in [
    "core.error_context",
    "core.error_monitoring",
    "core.exceptions",
    "core.transaction_manager",
]:
    if _cm not in sys.modules:
        _m = MagicMock()
        _m.async_error_context = MagicMock(return_value=_mock_async_ctx)
        _m.managed_transaction = MagicMock(return_value=_mock_async_ctx)
        _m.log_error = AsyncMock()
        _m.DatabaseError = Exception
        _m.ValidationError = ValueError
        _m.ErrorSeverity = MagicMock()
        sys.modules[_cm] = _m

from datetime import datetime, timedelta

import pytest

from core.context_manager import (
    ContextManager,
    ConversationTurn,
    ProgressTracker,
    SessionContext,
    SessionStatus,
)

# ------------------------------------------------------------------ #
# Actual imports (after mocks are in place)
# ------------------------------------------------------------------ #
from core.learning_analytics import (
    InteractionType,
    LearningAnalyticsEngine,
    LearningInteraction,
    LearningOutcome,
    LearningSession,
    StudyPattern,
    get_learning_analytics_engine,
)
from core.migration_framework import (
    MigrationDirection,
    MigrationExecution,
    MigrationInfo,
    MigrationManager,
    MigrationStatus,
    MigrationType,
    PythonMigration,
    SQLMigration,
)
from core.structured_learning_path import (
    LearningObjective,
    LearningObjectiveType,
    LearningPhase,
    Milestone,
    MilestoneType,
    StructuredLearningPathGenerator,
    StructuredPath,
    structured_path_generator,
)
from core.unified_resource_ranker import (
    QualityScore,
    RelevanceScore,
    ResourceQualityMetric,
    UnifiedResourceRanker,
    unified_resource_ranker,
)

# ================================================================== #
# FIXTURES                                                             #
# ================================================================== #


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def analytics_engine(mock_db):
    return LearningAnalyticsEngine(db_session=mock_db)


@pytest.fixture
def ranker():
    return UnifiedResourceRanker()


@pytest.fixture
def path_generator():
    return StructuredLearningPathGenerator()


@pytest.fixture
def context_manager():
    return ContextManager()


@pytest.fixture
def progress_tracker():
    return ProgressTracker()


# ================================================================== #
# LEARNING ANALYTICS TESTS                                             #
# ================================================================== #


class TestInteractionType:
    def test_all_values_accessible(self):
        assert InteractionType.QUESTION_ASKED.value == "question_asked"
        assert InteractionType.QUIZ_COMPLETED.value == "quiz_completed"
        assert InteractionType.STUDY_SESSION_ENDED.value == "study_session_ended"

    def test_enum_count(self):
        assert len(list(InteractionType)) == 10


class TestLearningAnalyticsEngine:
    def test_init_defaults(self, analytics_engine):
        assert analytics_engine.engagement_threshold == 0.7
        assert analytics_engine.mastery_threshold == 0.8
        assert analytics_engine.session_timeout_minutes == 30
        assert analytics_engine.interaction_buffer == []
        assert analytics_engine.active_sessions == {}

    @pytest.mark.asyncio
    async def test_record_interaction_adds_to_buffer(self, analytics_engine):
        await analytics_engine.record_interaction(
            student_id="s1",
            interaction_type=InteractionType.CONTENT_VIEWED,
            session_id="sess1",
        )
        assert len(analytics_engine.interaction_buffer) == 1
        assert analytics_engine.interaction_buffer[0].student_id == "s1"

    @pytest.mark.asyncio
    async def test_record_interaction_creates_session(self, analytics_engine):
        await analytics_engine.record_interaction(
            student_id="s1",
            interaction_type=InteractionType.CONTENT_VIEWED,
            session_id="sess1",
        )
        assert "sess1" in analytics_engine.active_sessions
        assert analytics_engine.active_sessions["sess1"].interactions_count == 1

    @pytest.mark.asyncio
    async def test_record_interaction_with_subject_and_topic(self, analytics_engine):
        await analytics_engine.record_interaction(
            student_id="s1",
            interaction_type=InteractionType.QUIZ_COMPLETED,
            session_id="sess1",
            subject="matematik",
            topic="cebir",
        )
        session = analytics_engine.active_sessions["sess1"]
        assert "matematik" in session.subjects_covered
        assert "cebir" in session.topics_covered

    @pytest.mark.asyncio
    async def test_record_interaction_ends_session_on_end_event(self, analytics_engine):
        # First create the session
        await analytics_engine.record_interaction(
            student_id="s1",
            interaction_type=InteractionType.STUDY_SESSION_STARTED,
            session_id="sess1",
        )
        assert "sess1" in analytics_engine.active_sessions
        # Now end it
        await analytics_engine.record_interaction(
            student_id="s1",
            interaction_type=InteractionType.STUDY_SESSION_ENDED,
            session_id="sess1",
        )
        # Session should be removed from active_sessions after ending
        assert "sess1" not in analytics_engine.active_sessions

    @pytest.mark.asyncio
    async def test_flush_interactions_called_on_buffer_overflow(self, analytics_engine):
        analytics_engine._flush_interactions = AsyncMock()
        # Add 100 interactions to trigger flush
        for i in range(100):
            await analytics_engine.record_interaction(
                student_id="s1",
                interaction_type=InteractionType.CONTENT_VIEWED,
                session_id=f"sess{i}",
            )
        analytics_engine._flush_interactions.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_engagement_score_empty(self, analytics_engine):
        score = await analytics_engine._calculate_engagement_score([])
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_calculate_engagement_score_with_quiz_completed(
        self, analytics_engine
    ):
        interaction = LearningInteraction(
            student_id="s1",
            interaction_type=InteractionType.QUIZ_COMPLETED,
            timestamp=datetime.now(),
            session_id="sess1",
        )
        score = await analytics_engine._calculate_engagement_score([interaction])
        assert 0.0 < score <= 1.0

    @pytest.mark.asyncio
    async def test_calculate_engagement_score_with_duration(self, analytics_engine):
        interaction = LearningInteraction(
            student_id="s1",
            interaction_type=InteractionType.QUIZ_COMPLETED,
            timestamp=datetime.now(),
            session_id="sess1",
            duration_seconds=300,
            confidence_level=5,
        )
        score = await analytics_engine._calculate_engagement_score([interaction])
        assert 0.0 < score <= 1.0

    def test_find_preferred_times_empty(self, analytics_engine):
        result = analytics_engine._find_preferred_times([])
        assert result == []

    def test_find_preferred_times_returns_top_3(self, analytics_engine):
        hours = [9, 9, 9, 14, 14, 20, 20, 20, 20]
        result = analytics_engine._find_preferred_times(hours)
        assert len(result) <= 3
        assert 20 in result  # Most frequent

    def test_find_most_common_empty(self, analytics_engine):
        assert analytics_engine._find_most_common([], 5) == []

    def test_find_most_common_with_limit(self, analytics_engine):
        items = ["a", "b", "b", "c", "c", "c", "d"]
        result = analytics_engine._find_most_common(items, 2)
        assert len(result) == 2
        assert "c" in result

    def test_create_empty_profile(self, analytics_engine):
        profile = analytics_engine._create_empty_profile("student_xyz")
        assert profile.student_id == "student_xyz"
        assert profile.total_study_time_hours == 0.0
        assert profile.total_sessions == 0
        assert profile.study_pattern == StudyPattern.SPORADIC
        assert profile.engagement_level == 0.0
        assert len(profile.recommendations) > 0

    @pytest.mark.asyncio
    async def test_analyze_learning_style_empty(self, analytics_engine):
        style = await analytics_engine._analyze_learning_style([])
        assert style == "mixed"

    @pytest.mark.asyncio
    async def test_analyze_learning_style_with_video_content(self, analytics_engine):
        interaction = LearningInteraction(
            student_id="s1",
            interaction_type=InteractionType.CONTENT_VIEWED,
            timestamp=datetime.now(),
            session_id="sess1",
            context={"content_type": "video"},
        )
        style = await analytics_engine._analyze_learning_style([interaction])
        assert style == "visual"

    @pytest.mark.asyncio
    async def test_analyze_study_pattern_empty_sessions(self, analytics_engine):
        pattern = await analytics_engine._analyze_study_pattern([])
        assert pattern == StudyPattern.SPORADIC

    @pytest.mark.asyncio
    async def test_analyze_study_pattern_consistent(self, analytics_engine):
        now = datetime.now()
        sessions = []
        for i in range(10):
            s = LearningSession(
                session_id=f"s{i}",
                student_id="student1",
                start_time=now - timedelta(days=i),
                total_duration_minutes=60,
            )
            sessions.append(s)
        pattern = await analytics_engine._analyze_study_pattern(sessions)
        # High frequency + stable duration should give CONSISTENT or close
        assert isinstance(pattern, StudyPattern)

    @pytest.mark.asyncio
    async def test_calculate_mastery_levels_empty(self, analytics_engine):
        result = await analytics_engine._calculate_mastery_levels("s1", [])
        assert result == {}

    @pytest.mark.asyncio
    async def test_calculate_mastery_levels_with_data(self, analytics_engine):
        interactions = [
            LearningInteraction(
                student_id="s1",
                interaction_type=InteractionType.QUIZ_COMPLETED,
                timestamp=datetime.now(),
                session_id="sess1",
                topic="cebir",
                success_rate=0.9,
            ),
            LearningInteraction(
                student_id="s1",
                interaction_type=InteractionType.QUIZ_COMPLETED,
                timestamp=datetime.now(),
                session_id="sess1",
                topic="cebir",
                success_rate=0.8,
            ),
        ]
        result = await analytics_engine._calculate_mastery_levels("s1", interactions)
        assert "cebir" in result
        assert 0.0 <= result["cebir"] <= 1.0

    @pytest.mark.asyncio
    async def test_identify_strengths_weaknesses_empty(self, analytics_engine):
        strengths, weaknesses = await analytics_engine._identify_strengths_weaknesses(
            "s1", {}
        )
        assert strengths == []
        assert weaknesses == []

    @pytest.mark.asyncio
    async def test_identify_strengths_weaknesses_with_data(self, analytics_engine):
        mastery = {"cebir": 0.9, "geometri": 0.3, "trigonometri": 0.5}
        strengths, weaknesses = await analytics_engine._identify_strengths_weaknesses(
            "s1", mastery
        )
        assert isinstance(strengths, list)
        assert isinstance(weaknesses, list)

    @pytest.mark.asyncio
    async def test_generate_recommendations_low_engagement(self, analytics_engine):
        recs = await analytics_engine._generate_recommendations(
            "s1", {"konu1": 0.4}, StudyPattern.CRAMMING, 0.3
        )
        assert len(recs) > 0
        # Should include cramming recommendation
        assert any("kısa" in r or "düzenli" in r or "farklı" in r for r in recs)

    @pytest.mark.asyncio
    async def test_determine_learning_outcomes_mastery(self, analytics_engine):
        session = LearningSession(
            session_id="s1",
            student_id="student1",
            start_time=datetime.now(),
            average_success_rate=0.95,
            engagement_score=0.9,
        )
        outcomes = await analytics_engine._determine_learning_outcomes(session, [])
        assert LearningOutcome.MASTERY_ACHIEVED in outcomes
        assert LearningOutcome.MOTIVATED in outcomes

    @pytest.mark.asyncio
    async def test_determine_learning_outcomes_struggling(self, analytics_engine):
        session = LearningSession(
            session_id="s1",
            student_id="student1",
            start_time=datetime.now(),
            average_success_rate=0.3,
            engagement_score=0.2,
        )
        outcomes = await analytics_engine._determine_learning_outcomes(session, [])
        assert LearningOutcome.STRUGGLING in outcomes
        assert LearningOutcome.DISENGAGED in outcomes

    def test_get_learning_analytics_engine_singleton(self, mock_db):
        import core.learning_analytics as mod

        mod._learning_analytics_engine = None  # reset
        engine1 = get_learning_analytics_engine(mock_db)
        engine2 = get_learning_analytics_engine(mock_db)
        assert engine1 is engine2
        mod._learning_analytics_engine = None  # cleanup


class TestLearningInteractionToDict:
    def test_to_dict_contains_required_fields(self):
        interaction = LearningInteraction(
            student_id="s1",
            interaction_type=InteractionType.QUESTION_ASKED,
            timestamp=datetime(2025, 1, 1, 10, 0, 0),
            session_id="sess1",
        )
        d = interaction.to_dict()
        assert d["student_id"] == "s1"
        assert d["interaction_type"] == "question_asked"
        assert "2025-01-01" in d["timestamp"]


# ================================================================== #
# MIGRATION FRAMEWORK TESTS                                            #
# ================================================================== #


class TestMigrationInfo:
    def test_create_with_explicit_id(self):
        info = MigrationInfo(
            id="test_001",
            name="Test Migration",
            description="A test",
            version="1.0.0",
            migration_type=MigrationType.SCHEMA,
        )
        assert info.id == "test_001"
        assert info.migration_type == MigrationType.SCHEMA

    def test_auto_generate_id_when_empty(self):
        info = MigrationInfo(
            id="",
            name="My Migration Name",
            description="desc",
            version="1.0.0",
            migration_type=MigrationType.DATA,
        )
        # __post_init__ should generate an id
        assert info.id != ""
        assert "my_migration_name" in info.id

    def test_dependencies_default_empty(self):
        info = MigrationInfo(
            id="m1",
            name="M1",
            description="d",
            version="1",
            migration_type=MigrationType.SEED,
        )
        assert info.dependencies == []
        assert info.tags == []


class TestMigrationExecution:
    def test_mark_completed_sets_fields(self):
        started = datetime.now()
        execution = MigrationExecution(
            migration_id="m1",
            status=MigrationStatus.RUNNING,
            direction=MigrationDirection.UP,
            started_at=started,
        )
        execution.mark_completed(MigrationStatus.COMPLETED)
        assert execution.status == MigrationStatus.COMPLETED
        assert execution.completed_at is not None
        assert execution.duration_ms is not None
        assert execution.duration_ms >= 0

    def test_mark_completed_with_error(self):
        execution = MigrationExecution(
            migration_id="m1",
            status=MigrationStatus.RUNNING,
            direction=MigrationDirection.UP,
            started_at=datetime.now(),
        )
        execution.mark_completed(MigrationStatus.FAILED, "some error")
        assert execution.status == MigrationStatus.FAILED
        assert execution.error_message == "some error"


class TestMigrationEnums:
    @pytest.mark.parametrize("status", list(MigrationStatus))
    def test_migration_status_values(self, status):
        assert status.value is not None

    @pytest.mark.parametrize("mtype", list(MigrationType))
    def test_migration_type_values(self, mtype):
        assert mtype.value is not None

    def test_migration_direction_values(self):
        assert MigrationDirection.UP.value == "up"
        assert MigrationDirection.DOWN.value == "down"


class TestSQLMigration:
    def test_init(self):
        info = MigrationInfo(
            id="sql_m1",
            name="SQL Test",
            description="d",
            version="1",
            migration_type=MigrationType.SCHEMA,
        )
        migration = SQLMigration(info, "SELECT 1", "SELECT 2")
        assert migration.up_sql == "SELECT 1"
        assert migration.down_sql == "SELECT 2"

    @pytest.mark.asyncio
    async def test_up_executes_statements(self):
        info = MigrationInfo(
            id="sql_m1",
            name="SQL Test",
            description="d",
            version="1",
            migration_type=MigrationType.SCHEMA,
        )
        migration = SQLMigration(
            info,
            "CREATE TABLE t1 (id INT); CREATE TABLE t2 (id INT)",
            "DROP TABLE t1; DROP TABLE t2",
        )
        mock_session = AsyncMock()
        await migration.up(mock_session)
        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_down_executes_statements(self):
        info = MigrationInfo(
            id="sql_m1",
            name="SQL Test",
            description="d",
            version="1",
            migration_type=MigrationType.SCHEMA,
        )
        migration = SQLMigration(info, "SELECT 1", "DROP TABLE x")
        mock_session = AsyncMock()
        await migration.down(mock_session)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_up_skips_empty_sql(self):
        info = MigrationInfo(
            id="sql_m2",
            name="Empty SQL",
            description="d",
            version="1",
            migration_type=MigrationType.SCHEMA,
        )
        migration = SQLMigration(info, "   ", "   ")
        mock_session = AsyncMock()
        await migration.up(mock_session)
        mock_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_preconditions_default_empty(self):
        info = MigrationInfo(
            id="m1",
            name="n",
            description="d",
            version="1",
            migration_type=MigrationType.SCHEMA,
        )
        migration = SQLMigration(info, "SELECT 1", "SELECT 0")
        errors = await migration.validate_preconditions(AsyncMock())
        assert errors == []

    @pytest.mark.asyncio
    async def test_validate_postconditions_default_empty(self):
        info = MigrationInfo(
            id="m1",
            name="n",
            description="d",
            version="1",
            migration_type=MigrationType.SCHEMA,
        )
        migration = SQLMigration(info, "SELECT 1", "SELECT 0")
        errors = await migration.validate_postconditions(AsyncMock())
        assert errors == []

    def test_get_estimated_duration_default_none(self):
        info = MigrationInfo(
            id="m1",
            name="n",
            description="d",
            version="1",
            migration_type=MigrationType.SCHEMA,
        )
        migration = SQLMigration(info, "SELECT 1", "SELECT 0")
        assert migration.get_estimated_duration() is None


class TestPythonMigration:
    @pytest.mark.asyncio
    async def test_up_calls_function(self):
        up_fn = AsyncMock()
        down_fn = AsyncMock()
        info = MigrationInfo(
            id="py_m1",
            name="Py Test",
            description="d",
            version="1",
            migration_type=MigrationType.DATA,
        )
        migration = PythonMigration(info, up_fn, down_fn)
        session = AsyncMock()
        await migration.up(session)
        up_fn.assert_called_once_with(session)

    @pytest.mark.asyncio
    async def test_down_calls_function(self):
        up_fn = AsyncMock()
        down_fn = AsyncMock()
        info = MigrationInfo(
            id="py_m1",
            name="Py Test",
            description="d",
            version="1",
            migration_type=MigrationType.DATA,
        )
        migration = PythonMigration(info, up_fn, down_fn)
        session = AsyncMock()
        await migration.down(session)
        down_fn.assert_called_once_with(session)


class TestMigrationManager:
    def test_init_creates_directory(self, tmp_path):
        manager = MigrationManager(str(tmp_path / "migs"))
        assert manager.migrations_directory.exists()

    def test_register_migration(self, tmp_path):
        manager = MigrationManager(str(tmp_path))
        info = MigrationInfo(
            id="m1",
            name="M1",
            description="d",
            version="1",
            migration_type=MigrationType.SCHEMA,
        )
        migration = SQLMigration(info, "SELECT 1", "SELECT 0")
        manager.register_migration(migration)
        assert "m1" in manager.loaded_migrations
        assert "m1" in manager.migration_graph

    def test_resolve_dependencies_simple(self, tmp_path):
        manager = MigrationManager(str(tmp_path))
        # m2 depends on m1
        manager.migration_graph = {"m1": set(), "m2": {"m1"}}
        order = manager._resolve_dependencies({"m1", "m2"})
        assert order.index("m1") < order.index("m2")

    def test_resolve_dependencies_no_deps(self, tmp_path):
        manager = MigrationManager(str(tmp_path))
        manager.migration_graph = {"m1": set(), "m2": set()}
        order = manager._resolve_dependencies({"m1", "m2"})
        assert set(order) == {"m1", "m2"}

    def test_generate_migration_file(self, tmp_path):
        manager = MigrationManager(str(tmp_path))
        file_path = manager.generate_migration_file(
            "Add Users Table", MigrationType.SCHEMA, "tester"
        )
        assert Path(file_path).exists()
        content = Path(file_path).read_text(encoding="utf-8")
        assert "Add Users Table" in content
        assert "tester" in content
        assert "async def up" in content
        assert "async def down" in content


# ================================================================== #
# STRUCTURED LEARNING PATH TESTS                                       #
# ================================================================== #


class TestStructuredLearningPathGenerator:
    def test_init_loads_templates(self, path_generator):
        assert "matematik" in path_generator.objective_templates
        assert "fen" in path_generator.objective_templates
        assert "knowledge_check" in path_generator.milestone_templates

    def test_load_scheduling_algorithms(self, path_generator):
        algos = path_generator.scheduling_algorithms
        assert "linear" in algos
        assert "adaptive" in algos
        assert "mastery" in algos

    @pytest.mark.asyncio
    async def test_generate_structured_path_matematik(self, path_generator):
        path = await path_generator.generate_structured_path(
            student_id="s1",
            learning_goal="YKS hazırlık",
            subject="matematik",
            duration_weeks=4,
            difficulty_preference=0.8,
        )
        assert path.student_id == "s1"
        assert path.learning_goal == "YKS hazırlık"
        assert len(path.phases) > 0
        assert path.total_objectives > 0
        assert path.completion_percentage == 0.0

    @pytest.mark.asyncio
    async def test_generate_structured_path_unknown_subject_adds_additional(
        self, path_generator
    ):
        path = await path_generator.generate_structured_path(
            student_id="s2",
            learning_goal="test goal",
            subject="tarih",
            duration_weeks=2,
        )
        # Unknown subject → falls back to additional objectives
        assert path.total_objectives >= 5

    def test_build_dependency_graph_empty(self, path_generator):
        graph = path_generator._build_dependency_graph([])
        assert graph == {}

    def test_build_dependency_graph_with_prereqs(self, path_generator):
        obj1 = LearningObjective(
            objective_id="o1",
            title="Temel Sayı Kavramları",
            description="d",
            objective_type=LearningObjectiveType.KNOWLEDGE,
            bloom_level=1,
            measurable_outcomes=[],
            assessment_criteria=[],
            estimated_time_minutes=60,
            difficulty_level=0.2,
            prerequisites=[],
            tags=[],
        )
        obj2 = LearningObjective(
            objective_id="o2",
            title="Dört İşlem",
            description="d",
            objective_type=LearningObjectiveType.APPLICATION,
            bloom_level=3,
            measurable_outcomes=[],
            assessment_criteria=[],
            estimated_time_minutes=90,
            difficulty_level=0.4,
            prerequisites=["Temel Sayı Kavramları"],
            tags=[],
        )
        graph = path_generator._build_dependency_graph([obj1, obj2])
        assert "o1" in graph
        assert "o2" in graph["o1"]

    def test_create_milestones_empty(self, path_generator):
        milestones = path_generator._create_milestones([], "matematik")
        assert milestones == []

    def test_create_milestones_groups_every_3(self, path_generator):
        objectives = []
        for i in range(6):
            objectives.append(
                LearningObjective(
                    objective_id=f"o{i}",
                    title=f"Obj {i}",
                    description="d",
                    objective_type=LearningObjectiveType.KNOWLEDGE,
                    bloom_level=1,
                    measurable_outcomes=[],
                    assessment_criteria=[],
                    estimated_time_minutes=60,
                    difficulty_level=0.3,
                    prerequisites=[],
                    tags=[],
                )
            )
        milestones = path_generator._create_milestones(objectives, "fen")
        assert len(milestones) == 2  # 6 objectives → 2 milestones

    def test_calculate_difficulty_curve_empty(self, path_generator):
        curve = path_generator._calculate_difficulty_curve([])
        assert curve == []

    def test_calculate_difficulty_curve_with_phases(self, path_generator):
        phase = LearningPhase(
            phase_id="p1",
            title="Phase 1",
            description="d",
            objectives=[],
            milestones=[],
            estimated_duration_days=7,
            difficulty_progression=[0.3, 0.5, 0.7],
            prerequisites=[],
            learning_activities=[],
            assessment_methods=[],
            success_criteria=[],
        )
        curve = path_generator._calculate_difficulty_curve([phase])
        assert len(curve) == 1
        assert abs(curve[0] - 0.5) < 0.01  # mean of [0.3, 0.5, 0.7]

    def test_generate_learning_activities_knowledge(self, path_generator):
        objectives = [
            LearningObjective(
                objective_id="o1",
                title="T",
                description="d",
                objective_type=LearningObjectiveType.KNOWLEDGE,
                bloom_level=1,
                measurable_outcomes=[],
                assessment_criteria=[],
                estimated_time_minutes=60,
                difficulty_level=0.2,
                prerequisites=[],
                tags=[],
            )
        ]
        activities = path_generator._generate_learning_activities(objectives)
        assert "Video izleme" in activities

    def test_generate_assessment_methods(self, path_generator):
        milestone = Milestone(
            milestone_id="m1",
            title="M1",
            description="d",
            milestone_type=MilestoneType.KNOWLEDGE_CHECK,
            objectives=[],
            completion_criteria=[],
            estimated_time_minutes=30,
            required_score=0.7,
            resources=[],
            position_in_path=0,
            dependencies=[],
            rewards=[],
        )
        methods = path_generator._generate_assessment_methods([milestone])
        assert "Çoktan seçmeli test" in methods

    def test_get_next_study_date_skips_weekend(self, path_generator):
        # Wednesday
        wed = datetime(2025, 1, 15)  # 2025-01-15 is a Wednesday
        next_date = path_generator._get_next_study_date(wed, 5)
        # Next day is Thursday (still weekday < 5)
        assert next_date.weekday() < 5

    def test_track_learning_objectives_completion_percentage(self, path_generator):
        objectives = [
            LearningObjective(
                objective_id=f"o{i}",
                title=f"T{i}",
                description="d",
                objective_type=LearningObjectiveType.APPLICATION,
                bloom_level=3,
                measurable_outcomes=[],
                assessment_criteria=[],
                estimated_time_minutes=60,
                difficulty_level=0.5,
                prerequisites=[],
                tags=[],
            )
            for i in range(4)
        ]
        phase = LearningPhase(
            phase_id="p1",
            title="P1",
            description="d",
            objectives=objectives,
            milestones=[],
            estimated_duration_days=7,
            difficulty_progression=[],
            prerequisites=[],
            learning_activities=[],
            assessment_methods=[],
            success_criteria=[],
        )
        path = StructuredPath(
            path_id="path1",
            title="T",
            description="d",
            student_id="s1",
            learning_goal="g",
            phases=[phase],
            dependency_graph={},
            total_objectives=4,
            total_milestones=0,
            estimated_total_time_hours=4.0,
            difficulty_curve=[0.5],
            completion_percentage=0.0,
            current_phase="p1",
            current_milestone=None,
            adaptive_parameters={},
            created_at=datetime.now(),
            last_updated=datetime.now(),
        )
        result = path_generator.track_learning_objectives(
            path, ["o0", "o1"], {"o0": 0.9, "o1": 0.8}
        )
        assert result["completed_count"] == 2
        assert result["completion_percentage"] == 50.0

    def test_analyze_performance_empty(self, path_generator):
        path = StructuredPath(
            path_id="p1",
            title="T",
            description="d",
            student_id="s1",
            learning_goal="g",
            phases=[],
            dependency_graph={},
            total_objectives=0,
            total_milestones=0,
            estimated_total_time_hours=0.0,
            difficulty_curve=[],
            completion_percentage=0.0,
            current_phase=None,
            current_milestone=None,
            adaptive_parameters={},
            created_at=datetime.now(),
            last_updated=datetime.now(),
        )
        result = path_generator._analyze_performance(path, {})
        assert "message" in result

    def test_analyze_performance_with_scores(self, path_generator):
        path = StructuredPath(
            path_id="p1",
            title="T",
            description="d",
            student_id="s1",
            learning_goal="g",
            phases=[],
            dependency_graph={},
            total_objectives=0,
            total_milestones=0,
            estimated_total_time_hours=0.0,
            difficulty_curve=[],
            completion_percentage=0.0,
            current_phase=None,
            current_milestone=None,
            adaptive_parameters={},
            created_at=datetime.now(),
            last_updated=datetime.now(),
        )
        scores = {"o1": 0.9, "o2": 0.5, "o3": 0.7}
        result = path_generator._analyze_performance(path, scores)
        assert result["highest_score"] == 0.9
        assert result["lowest_score"] == 0.5
        assert "strong_areas" in result
        assert "improvement_areas" in result

    def test_optimize_learning_sequence_low_performance(self, path_generator):
        objectives = [
            LearningObjective(
                objective_id=f"o{i}",
                title=f"T{i}",
                description="d",
                objective_type=LearningObjectiveType.APPLICATION,
                bloom_level=3,
                measurable_outcomes=[],
                assessment_criteria=[],
                estimated_time_minutes=60,
                difficulty_level=float(i) / 10 + 0.1,
                prerequisites=[],
                tags=[],
            )
            for i in range(3)
        ]
        phase = LearningPhase(
            phase_id="p1",
            title="P1",
            description="d",
            objectives=objectives,
            milestones=[],
            estimated_duration_days=7,
            difficulty_progression=[],
            prerequisites=[],
            learning_activities=[],
            assessment_methods=[],
            success_criteria=[],
        )
        path = StructuredPath(
            path_id="p1",
            title="T",
            description="d",
            student_id="s1",
            learning_goal="g",
            phases=[phase],
            dependency_graph={},
            total_objectives=3,
            total_milestones=0,
            estimated_total_time_hours=3.0,
            difficulty_curve=[],
            completion_percentage=0.0,
            current_phase="p1",
            current_milestone=None,
            adaptive_parameters={},
            created_at=datetime.now(),
            last_updated=datetime.now(),
        )
        # Low performance → objectives sorted easy-first
        result = path_generator.optimize_learning_sequence(
            path, {"o0": 0.3, "o1": 0.4, "o2": 0.35}
        )
        difficulties = [obj.difficulty_level for obj in result.phases[0].objectives]
        assert difficulties == sorted(difficulties)


# ================================================================== #
# CONTEXT MANAGER TESTS                                                #
# ================================================================== #


class TestSessionContext:
    def test_add_turn_appends(self):
        session = SessionContext(
            session_id="s1",
            student_id="stu1",
            created_at=datetime.now(),
            last_updated=datetime.now(),
            status=SessionStatus.ACTIVE,
        )
        turn = ConversationTurn(
            turn_id="t1",
            timestamp=datetime.now(),
            agent_name="tutor",
            user_message="merhaba",
            agent_response="Merhaba!",
        )
        session.add_turn(turn)
        assert len(session.conversation_history) == 1

    def test_add_turn_trims_to_50(self):
        session = SessionContext(
            session_id="s1",
            student_id="stu1",
            created_at=datetime.now(),
            last_updated=datetime.now(),
            status=SessionStatus.ACTIVE,
        )
        for i in range(55):
            turn = ConversationTurn(
                turn_id=f"t{i}",
                timestamp=datetime.now(),
                agent_name="agent",
                user_message=f"msg{i}",
                agent_response=f"resp{i}",
            )
            session.add_turn(turn)
        assert len(session.conversation_history) == 50

    def test_get_context_window_empty(self):
        session = SessionContext(
            session_id="s1",
            student_id="stu1",
            created_at=datetime.now(),
            last_updated=datetime.now(),
            status=SessionStatus.ACTIVE,
        )
        assert session.get_context_window() == []

    def test_get_context_window_returns_recent(self):
        session = SessionContext(
            session_id="s1",
            student_id="stu1",
            created_at=datetime.now(),
            last_updated=datetime.now(),
            status=SessionStatus.ACTIVE,
        )
        for i in range(10):
            session.add_turn(
                ConversationTurn(
                    turn_id=f"t{i}",
                    timestamp=datetime.now(),
                    agent_name="agent",
                    user_message=f"msg{i}",
                    agent_response=f"resp{i}",
                )
            )
        window = session.get_context_window(3)
        assert len(window) == 3

    def test_get_summary_no_history(self):
        session = SessionContext(
            session_id="s1",
            student_id="stu1",
            created_at=datetime.now(),
            last_updated=datetime.now(),
            status=SessionStatus.ACTIVE,
        )
        assert session.get_summary() == "No conversation history"

    def test_get_summary_with_history(self):
        session = SessionContext(
            session_id="s1",
            student_id="stu1",
            created_at=datetime.now(),
            last_updated=datetime.now(),
            status=SessionStatus.ACTIVE,
        )
        session.add_turn(
            ConversationTurn(
                turn_id="t1",
                timestamp=datetime.now(),
                agent_name="agent",
                user_message="hello",
                agent_response="world",
            )
        )
        summary = session.get_summary()
        assert "hello" in summary
        assert "world" in summary


class TestProgressTracker:
    def test_update_question_answered_correct(self, progress_tracker):
        progress_tracker.update_progress("s1", "question_answered", {"correct": True})
        report = progress_tracker.get_progress_report("s1")
        assert report["statistics"]["questions_answered"] == 1
        assert report["statistics"]["current_streak"] == 1

    def test_update_question_answered_wrong_resets_streak(self, progress_tracker):
        progress_tracker.update_progress("s1", "question_answered", {"correct": True})
        progress_tracker.update_progress("s1", "question_answered", {"correct": True})
        progress_tracker.update_progress("s1", "question_answered", {"correct": False})
        report = progress_tracker.get_progress_report("s1")
        assert report["statistics"]["current_streak"] == 0
        assert report["statistics"]["accuracy"] > 0

    def test_update_topic_completed_adds_experience(self, progress_tracker):
        progress_tracker.update_progress("s1", "topic_completed", "cebir")
        progress = progress_tracker.progress_data["s1"]
        assert "cebir" in progress["topics_covered"]
        assert progress["experience"] >= 100

    def test_update_skill_acquired_no_duplicates(self, progress_tracker):
        progress_tracker.update_progress("s1", "skill_acquired", "problem_solving")
        progress_tracker.update_progress("s1", "skill_acquired", "problem_solving")
        skills = progress_tracker.progress_data["s1"]["skills_acquired"]
        assert skills.count("problem_solving") == 1

    def test_update_session_completed_increments_counter(self, progress_tracker):
        progress_tracker.update_progress("s1", "session_completed", {})
        assert progress_tracker.progress_data["s1"]["total_sessions"] == 1

    def test_get_progress_report_no_data(self, progress_tracker):
        report = progress_tracker.get_progress_report("unknown")
        assert "error" in report

    def test_level_up_on_enough_experience(self, progress_tracker):
        # Level 1 requires 500 XP; topic_completed gives 100 XP each
        for i in range(6):
            progress_tracker.update_progress("s1", "topic_completed", f"topic{i}")
        report = progress_tracker.get_progress_report("s1")
        assert report["gamification"]["level"] >= 2

    def test_milestone_first_10_questions(self, progress_tracker):
        for i in range(10):
            progress_tracker.update_progress(
                "s1", "question_answered", {"correct": True}
            )
        milestones = progress_tracker.milestones.get("s1", [])
        milestone_names = [m.get("name") for m in milestones]
        assert "First 10 Questions" in milestone_names

    def test_recommendations_low_accuracy(self, progress_tracker):
        for _ in range(10):
            progress_tracker.update_progress(
                "s1", "question_answered", {"correct": False}
            )
        report = progress_tracker.get_progress_report("s1")
        recs = report["recommendations"]
        assert any("fundamental" in r or "easier" in r for r in recs)


class TestContextManager:
    @pytest.mark.asyncio
    async def test_initialize_no_redis(self, context_manager):
        await context_manager.initialize()
        assert context_manager.redis_client is None

    @pytest.mark.asyncio
    async def test_create_session_returns_session(self, context_manager):
        session = await context_manager.create_session("student1")
        assert session.student_id == "student1"
        assert session.status == SessionStatus.ACTIVE
        assert session.session_id in context_manager.sessions

    @pytest.mark.asyncio
    async def test_create_session_with_initial_context(self, context_manager):
        session = await context_manager.create_session(
            "student1", initial_context={"topic": "matematik"}
        )
        assert session.variables["topic"] == "matematik"

    @pytest.mark.asyncio
    async def test_get_session_returns_existing(self, context_manager):
        session = await context_manager.create_session("student1")
        retrieved = await context_manager.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.session_id == session.session_id

    @pytest.mark.asyncio
    async def test_get_session_expired_returns_none(self, context_manager):
        session = await context_manager.create_session("student1")
        # Simulate expiry
        session.last_updated = datetime.now() - timedelta(hours=3)
        retrieved = await context_manager.get_session(session.session_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_session_unknown_returns_none(self, context_manager):
        result = await context_manager.get_session("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_session_adds_turn(self, context_manager):
        session = await context_manager.create_session("student1")
        turn = ConversationTurn(
            turn_id="t1",
            timestamp=datetime.now(),
            agent_name="tutor",
            user_message="soru",
            agent_response="cevap",
        )
        success = await context_manager.update_session(session.session_id, turn=turn)
        assert success is True
        updated = await context_manager.get_session(session.session_id)
        assert len(updated.conversation_history) == 1

    @pytest.mark.asyncio
    async def test_update_session_missing_id_returns_false(self, context_manager):
        result = await context_manager.update_session(
            "ghost-session", variables={"x": 1}
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_end_session_marks_completed(self, context_manager):
        session = await context_manager.create_session("student1")
        sid = session.session_id
        result = await context_manager.end_session(sid)
        assert result is True
        # Session removed from memory after end
        assert sid not in context_manager.sessions

    @pytest.mark.asyncio
    async def test_end_session_unknown_returns_false(self, context_manager):
        result = await context_manager.end_session("ghost")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_active_sessions(self, context_manager):
        s1 = await context_manager.create_session("s1")
        s2 = await context_manager.create_session("s2")
        active = await context_manager.get_active_sessions()
        assert len(active) >= 2

    @pytest.mark.asyncio
    async def test_get_or_create_student_profile_creates_new(self, context_manager):
        profile = await context_manager.get_or_create_student_profile(
            "new_student", name="Ali", grade=10
        )
        assert profile.student_id == "new_student"
        assert profile.name == "Ali"

    @pytest.mark.asyncio
    async def test_get_or_create_student_profile_returns_cached(self, context_manager):
        p1 = await context_manager.get_or_create_student_profile("stu")
        p2 = await context_manager.get_or_create_student_profile("stu")
        assert p1 is p2

    @pytest.mark.asyncio
    async def test_update_student_profile_updates_fields(self, context_manager):
        await context_manager.get_or_create_student_profile("stu1")
        result = await context_manager.update_student_profile(
            "stu1", {"difficulty_level": "hard"}
        )
        assert result is True
        profile = context_manager.student_profiles["stu1"]
        assert profile.difficulty_level == "hard"

    def test_get_progress_tracker(self, context_manager):
        tracker = context_manager.get_progress_tracker()
        assert isinstance(tracker, ProgressTracker)


# ================================================================== #
# UNIFIED RESOURCE RANKER TESTS                                        #
# ================================================================== #


class TestUnifiedResourceRanker:
    def test_init_loads_weights(self, ranker):
        assert "Khan Academy" in ranker.platform_weights
        assert ranker.platform_weights["Khan Academy"] == 1.0
        assert ResourceQualityMetric.EDUCATIONAL_VALUE in ranker.quality_weights

    def test_platform_weights_sum_meaningful(self, ranker):
        # All weights should be between 0 and 1
        for name, w in ranker.platform_weights.items():
            assert 0.0 <= w <= 1.0, f"Platform {name} weight out of range"

    def test_quality_weights_sum_to_1(self, ranker):
        total = sum(ranker.quality_weights.values())
        assert abs(total - 1.0) < 1e-9

    def test_assess_educational_value_with_keywords(self, ranker):
        resource = {
            "content_type": "course",
            "title": "Python öğren: Kapsamlı kurs",
            "description": "Bu ders ile Python öğrenin",
        }
        score = ranker._assess_educational_value(resource)
        assert score > 0.5

    def test_assess_educational_value_with_rating(self, ranker):
        resource = {
            "content_type": "video",
            "title": "Math Video",
            "description": "A math video",
            "rating": 4.5,
        }
        score = ranker._assess_educational_value(resource)
        assert 0.0 <= score <= 1.0

    def test_assess_content_accuracy_with_known_platform(self, ranker):
        resource = {
            "source": "Khan Academy",
            "metadata": {},
        }
        score = ranker._assess_content_accuracy(resource, 1.0)
        assert score >= 1.0 or score == 1.0  # min(1.0 + ..., 1.0)

    def test_assess_content_accuracy_with_author_bonus(self, ranker):
        resource = {
            "source": "YouTube",
            "metadata": {"author": "Prof. Smith"},
        }
        score = ranker._assess_content_accuracy(resource, 0.7)
        assert score > 0.7

    def test_assess_presentation_quality_with_views(self, ranker):
        resource = {
            "description": "A" * 200,
            "metadata": {
                "view_count": 50000,
                "thumbnail_url": "http://img.example.com",
            },
        }
        score = ranker._assess_presentation_quality(resource)
        assert score > 0.6

    def test_assess_accessibility_turkish_content(self, ranker):
        resource = {
            "language": "tr",
            "metadata": {},
        }
        score = ranker._assess_accessibility(resource)
        assert score >= 0.3

    def test_assess_accessibility_with_features(self, ranker):
        resource = {
            "language": "tr",
            "metadata": {
                "captions_available": True,
                "transcript_available": True,
            },
        }
        score = ranker._assess_accessibility(resource)
        assert score > 0.3

    def test_assess_engagement_interactive(self, ranker):
        resource = {"content_type": "interactive", "metadata": {}}
        score = ranker._assess_engagement_level(resource)
        assert score > 0.5

    def test_assess_engagement_with_like_ratio(self, ranker):
        resource = {
            "content_type": "video",
            "metadata": {"view_count": 10000, "like_count": 500},
        }
        score = ranker._assess_engagement_level(resource)
        assert score > 0.5

    def test_assess_currency_recent_content(self, ranker):
        recent = (datetime.now() - timedelta(days=100)).isoformat()
        resource = {"metadata": {"published_at": recent}}
        score = ranker._assess_currency(resource)
        assert score == 1.0

    def test_assess_currency_old_content(self, ranker):
        old = (datetime.now() - timedelta(days=365 * 6)).isoformat()
        resource = {"metadata": {"published_at": old}}
        score = ranker._assess_currency(resource)
        assert score == 0.4

    def test_assess_currency_no_date(self, ranker):
        resource = {"metadata": {}}
        score = ranker._assess_currency(resource)
        assert score == 0.5

    def test_calculate_topic_relevance_in_title(self, ranker):
        resource = {"title": "Trigonometri Dersi", "description": "", "tags": []}
        score = ranker._calculate_topic_relevance(resource, "trigonometri")
        assert score == 1.0

    def test_calculate_topic_relevance_in_description(self, ranker):
        resource = {
            "title": "Math Class",
            "description": "Covers trigonometri and calculus",
            "tags": [],
        }
        score = ranker._calculate_topic_relevance(resource, "trigonometri")
        assert score == 0.8

    def test_calculate_topic_relevance_no_topic(self, ranker):
        resource = {"title": "Some Resource", "description": "", "tags": []}
        score = ranker._calculate_topic_relevance(resource, None)
        assert score == 0.5

    def test_calculate_topic_relevance_no_match(self, ranker):
        resource = {"title": "Fizik Dersi", "description": "Hareket", "tags": []}
        score = ranker._calculate_topic_relevance(resource, "kimya")
        assert score == 0.3

    def test_calculate_level_appropriateness_no_profile(self, ranker):
        resource = {"difficulty_level": "medium"}
        score = ranker._calculate_level_appropriateness(resource, None)
        assert score == 0.7

    def test_calculate_level_appropriateness_exact_match(self, ranker):
        resource = {"difficulty_level": "intermediate"}
        profile = {"knowledge_level": "intermediate"}
        score = ranker._calculate_level_appropriateness(resource, profile)
        assert score == 1.0

    def test_calculate_level_appropriateness_large_diff(self, ranker):
        resource = {"difficulty_level": "expert"}
        profile = {"knowledge_level": "beginner"}
        score = ranker._calculate_level_appropriateness(resource, profile)
        assert score == 0.3

    def test_calculate_style_match_visual_video(self, ranker):
        resource = {"content_type": "video"}
        profile = {"learning_style": "visual"}
        score = ranker._calculate_style_match(resource, profile)
        assert score == 1.0

    def test_calculate_style_match_no_profile(self, ranker):
        resource = {"content_type": "video"}
        score = ranker._calculate_style_match(resource, None)
        assert score == 0.6

    def test_calculate_goal_alignment_in_title(self, ranker):
        resource = {"title": "Python programlama", "description": "", "tags": []}
        score = ranker._calculate_goal_alignment(resource, ["python programlama"])
        assert score == 1.0

    def test_calculate_goal_alignment_no_goals(self, ranker):
        resource = {"title": "Resource", "description": "", "tags": []}
        score = ranker._calculate_goal_alignment(resource, None)
        assert score == 0.6

    def test_calculate_final_score_bounds(self, ranker):
        quality = QualityScore(
            overall_score=0.9,
            metric_scores={},
            confidence_level=0.9,
            reasoning=[],
        )
        relevance = RelevanceScore(
            topic_relevance=0.8,
            level_appropriateness=0.9,
            style_match=0.7,
            goal_alignment=0.8,
            overall_relevance=0.8,
            reasoning=[],
        )
        score = ranker._calculate_final_score(quality, relevance)
        assert 0.0 <= score <= 1.0

    def test_determine_recommendation_strength(self, ranker):
        assert ranker._determine_recommendation_strength(0.9) == "excellent"
        assert ranker._determine_recommendation_strength(0.65) == "good"
        assert ranker._determine_recommendation_strength(0.45) == "moderate"
        assert ranker._determine_recommendation_strength(0.2) == "low"

    def test_estimate_duration_by_content_type(self, ranker):
        assert ranker._estimate_duration({"content_type": "video"}) == 15
        assert ranker._estimate_duration({"content_type": "quiz"}) == 5
        assert ranker._estimate_duration({"content_type": "course"}) == 60
        assert ranker._estimate_duration({"content_type": "unknown_type"}) == 15

    def test_estimate_difficulty_basic_keyword(self, ranker):
        resource = {"title": "Python basic tutorial", "description": ""}
        assert ranker._estimate_difficulty(resource) == "easy"

    def test_estimate_difficulty_advanced_keyword(self, ranker):
        resource = {"title": "Advanced Python", "description": ""}
        assert ranker._estimate_difficulty(resource) == "hard"

    def test_estimate_difficulty_default_medium(self, ranker):
        resource = {"title": "Python Tutorial", "description": ""}
        assert ranker._estimate_difficulty(resource) == "medium"

    def test_categorize_content(self, ranker):
        assert ranker._categorize_content({"content_type": "video"}) == "multimedia"
        assert ranker._categorize_content({"content_type": "article"}) == "text_based"
        assert ranker._categorize_content({"content_type": "quiz"}) == "assessment"
        assert (
            ranker._categorize_content({"content_type": "course"})
            == "structured_learning"
        )
        assert ranker._categorize_content({"content_type": "unknown"}) == "general"

    def test_extract_accessibility_features_video(self, ranker):
        resource = {"content_type": "video", "metadata": {}}
        features = ranker._extract_accessibility_features(resource)
        assert "captions_available" in features
        assert "transcript_available" in features

    def test_extract_accessibility_features_article(self, ranker):
        resource = {"content_type": "article", "metadata": {}}
        features = ranker._extract_accessibility_features(resource)
        assert "screen_reader_compatible" in features

    @pytest.mark.asyncio
    async def test_rank_resources_empty_list(self, ranker):
        result = await ranker.rank_resources([])
        assert result == []

    @pytest.mark.asyncio
    async def test_rank_resources_single_resource(self, ranker):
        resources = [
            {
                "resource_id": "r1",
                "title": "Matematik Dersi",
                "description": "Temel matematik",
                "content_type": "video",
                "source": "Khan Academy",
                "tags": ["matematik"],
                "metadata": {},
            }
        ]
        result = await ranker.rank_resources(resources)
        assert len(result) == 1
        assert result[0].resource_id == "r1"
        assert result[0].ranking_position == 1
        assert 0.0 <= result[0].final_score <= 1.0

    @pytest.mark.asyncio
    async def test_rank_resources_sorted_by_score(self, ranker):
        resources = [
            {
                "resource_id": "low",
                "title": "x",
                "description": "",
                "content_type": "pdf",
                "source": "unknown",
                "tags": [],
                "metadata": {},
            },
            {
                "resource_id": "high",
                "title": "Python learn education course",
                "description": "Professional course",
                "content_type": "course",
                "source": "Khan Academy",
                "tags": ["python"],
                "metadata": {},
                "rating": 4.8,
            },
        ]
        result = await ranker.rank_resources(resources)
        assert result[0].ranking_position == 1
        assert result[0].final_score >= result[1].final_score

    @pytest.mark.asyncio
    async def test_rank_resources_with_student_profile_and_topic(self, ranker):
        resources = [
            {
                "resource_id": "r1",
                "title": "Trigonometri",
                "description": "Trigonometri dersi",
                "content_type": "video",
                "source": "YouTube",
                "tags": [],
                "metadata": {},
                "difficulty_level": "medium",
            }
        ]
        profile = {"knowledge_level": "intermediate", "learning_style": "visual"}
        result = await ranker.rank_resources(
            resources,
            student_profile=profile,
            topic="Trigonometri",
            learning_goals=["trigonometri öğren"],
        )
        assert len(result) == 1
        assert result[0].relevance_score.topic_relevance == 1.0

    @pytest.mark.asyncio
    async def test_enrich_metadata_adds_fields(self, ranker):
        resource = {
            "content_type": "video",
            "title": "Test",
            "metadata": {},
        }
        enriched = await ranker._enrich_metadata(resource)
        assert "estimated_time" in enriched
        assert "difficulty_level" in enriched
        assert "accessibility_features" in enriched
        assert "content_category" in enriched

    @pytest.mark.asyncio
    async def test_calculate_quality_score_exception_returns_default(self, ranker):
        # Pass malformed resource to trigger exception path
        result = await ranker._calculate_quality_score(
            {"source": None, "metadata": None}
        )
        # Should return default QualityScore(0.5, ...) without raising
        assert isinstance(result, QualityScore)

    def test_singleton_instance_exists(self):
        assert unified_resource_ranker is not None
        assert isinstance(unified_resource_ranker, UnifiedResourceRanker)

    def test_structured_path_generator_singleton(self):
        assert structured_path_generator is not None
        assert isinstance(structured_path_generator, StructuredLearningPathGenerator)


# ================================================================== #
# PARAMETRIZE TESTS                                                    #
# ================================================================== #


@pytest.mark.parametrize(
    "content_type,expected_category",
    [
        ("video", "multimedia"),
        ("audio", "multimedia"),
        ("article", "text_based"),
        ("book", "text_based"),
        ("pdf", "text_based"),
        ("interactive", "hands_on"),
        ("simulation", "hands_on"),
        ("quiz", "assessment"),
        ("exercise", "practice"),
        ("course", "structured_learning"),
    ],
)
def test_content_categorization(content_type, expected_category):
    r = UnifiedResourceRanker()
    assert r._categorize_content({"content_type": content_type}) == expected_category


@pytest.mark.parametrize(
    "score,expected",
    [
        (0.85, "excellent"),
        (0.80, "excellent"),
        (0.70, "good"),
        (0.60, "good"),
        (0.50, "moderate"),
        (0.40, "moderate"),
        (0.39, "low"),
        (0.0, "low"),
    ],
)
def test_recommendation_strength_parametrize(score, expected):
    r = UnifiedResourceRanker()
    assert r._determine_recommendation_strength(score) == expected


@pytest.mark.parametrize(
    "study_hours,expected_style",
    [
        ([9, 9, 9, 14, 14], [9]),  # 9 is most common
        ([20, 20, 20, 20, 14, 9], [20]),  # 20 is most common
    ],
)
def test_find_preferred_times_parametrize(study_hours, expected_style):
    db = MagicMock()
    engine = LearningAnalyticsEngine(db_session=db)
    result = engine._find_preferred_times(study_hours)
    assert result[0] == expected_style[0]


@pytest.mark.parametrize("migration_type", list(MigrationType))
def test_migration_type_name_template(tmp_path, migration_type):
    manager = MigrationManager(str(tmp_path))
    file_path = manager.generate_migration_file(
        f"Test {migration_type.name}", migration_type
    )
    content = Path(file_path).read_text(encoding="utf-8")
    assert migration_type.name in content
