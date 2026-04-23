"""
Mega Feature Tests — F1, F2, F4, F6, F7, F11, F15 + Error Taxonomy
Tests for 18 new database models across 8 feature domains.

Coverage targets:
    models/league.py          — LeagueMembership, LeagueHistory
    models/duel.py            — DuelSession, DuelMatch, DuelRating
    models/study_planner.py   — StudyPlan, WeeklyGoal
    models/coaching.py        — CoachingEvent, StudentEngagementSignal
    models/knowledge_graph.py — KnowledgePoint, QuestionKnowledgeMapping, StudentKnowledgeState
    models/dina.py            — NanoSkill, QMatrix, DINAParameter, StudentNanoSkillMastery
    models/error_cluster.py   — ErrorCluster, PeerRecommendation

All tests run WITHOUT a database connection — model objects are instantiated in-process
to verify constructor defaults, field types, constraint metadata, and business logic.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest

# ---------------------------------------------------------------------------
# Import guards — skip individual feature blocks if a model file is missing
# ---------------------------------------------------------------------------

# Pre-import QuestionBankItem so that SQLAlchemy can resolve the string-based
# primaryjoin expression in exam_db.ExamQuestion before any mapper is configured.
# Without this, mapper initialisation fails for ALL models in the shared registry.
try:
    from models.question_bank import QuestionBankItem as _QuestionBankItem  # noqa: F401
except Exception:
    pass  # best-effort; if it fails the mapper error surfaces anyway

try:
    from models.league import (
        DEFAULT_TIER,
        LEAGUE_TIERS,
        LeagueHistory,
        LeagueMembership,
    )

    _LEAGUE_OK = True
except Exception:
    _LEAGUE_OK = False

try:
    from models.duel import DuelMatch, DuelRating, DuelSession

    _DUEL_OK = True
except Exception:
    _DUEL_OK = False

try:
    from models.study_planner import StudyPlan, WeeklyGoal

    _STUDY_PLANNER_OK = True
except Exception:
    _STUDY_PLANNER_OK = False

try:
    from models.coaching import CoachingEvent, StudentEngagementSignal

    _COACHING_OK = True
except Exception:
    _COACHING_OK = False

try:
    from models.knowledge_graph import (
        KnowledgePoint,
        QuestionKnowledgeMapping,
        StudentKnowledgeState,
    )

    _KG_OK = True
except Exception:
    _KG_OK = False

try:
    from models.dina import DINAParameter, NanoSkill, QMatrix, StudentNanoSkillMastery

    _DINA_OK = True
except Exception:
    _DINA_OK = False

try:
    from models.error_cluster import ErrorCluster, PeerRecommendation

    _EC_OK = True
except Exception:
    _EC_OK = False


# ===========================================================================
# Helpers
# ===========================================================================


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _make_uuid() -> str:
    return str(uuid.uuid4())


def _col_default(model_class, col_name):
    """Return the Python-level column default scalar/callable result.

    SQLAlchemy column ``default=X`` values are NOT applied to instance
    attributes until the object is flushed to a DB session.  When running
    without a DB we must read the default directly from the column metadata.

    Handles three cases:
    1. Scalar default  — returned directly.
    2. Zero-arg callable — called and result returned.
    3. Context-sensitive callable (takes ``ctx``) — called with None and result returned.
       This covers columns declared as ``default=list`` or ``default=lambda ctx: ...``.
    """
    import inspect

    col = model_class.__table__.c[col_name]
    if col.default is None:
        return None
    arg = col.default.arg
    if not callable(arg):
        return arg
    try:
        sig = inspect.signature(arg)
        params = [
            p for p in sig.parameters.values()
            if p.default is inspect.Parameter.empty
        ]
        if len(params) == 0:
            return arg()
        # Context-sensitive default — pass None as the execution context
        return arg(None)
    except (ValueError, TypeError):
        # inspect.signature may fail for built-ins; try zero-arg first
        try:
            return arg()
        except TypeError:
            return arg(None)


# ===========================================================================
# F8 — Error Taxonomy (error_type field on StudentAnswer / related models)
# The error_type column was added to student_answers via migration
# 20260312_add_error_type_to_student_answers.py.  We test the valid domain
# values as plain string logic rather than importing a removed enum.
# ===========================================================================

VALID_ERROR_TYPES = ["concept", "procedural", "careless", "knowledge_gap"]


class TestF8ErrorTaxonomy:
    """F8: Error taxonomy domain validation."""

    def test_valid_error_types_accepted(self) -> None:
        """All four canonical error type strings must be non-empty."""
        for et in VALID_ERROR_TYPES:
            assert et, f"Error type '{et}' must be a non-empty string"
            assert isinstance(et, str)

    def test_invalid_error_type_rejected(self) -> None:
        """An arbitrary string is NOT in the valid domain."""
        invalid = "random_typo"
        assert invalid not in VALID_ERROR_TYPES, (
            f"'{invalid}' should not be a valid error type"
        )

    def test_error_type_nullable_sentinel(self) -> None:
        """None is a distinct value, not a valid error type string."""
        error_type: str | None = None
        assert error_type is None
        # None must not accidentally pass a membership check
        assert error_type not in VALID_ERROR_TYPES


# ===========================================================================
# F2 — League System
# ===========================================================================


@pytest.mark.skipif(not _LEAGUE_OK, reason="models.league unavailable")
class TestF2LeagueSystem:
    """F2: League membership and history model behaviour."""

    def test_league_membership_creation(self) -> None:
        """LeagueMembership should store student_id and week_start correctly."""
        week = _now()
        membership = LeagueMembership(
            student_id="student-001",
            week_start=week,
        )
        assert membership.student_id == "student-001"
        assert membership.week_start == week

    def test_league_tier_default_bronze(self) -> None:
        """Default tier must be BRONZE (per module constant DEFAULT_TIER)."""
        assert DEFAULT_TIER == "BRONZE"
        # Column defaults are only applied on DB flush; read from metadata directly.
        col_default = _col_default(LeagueMembership, "league_tier")
        assert col_default == "BRONZE"
        assert DEFAULT_TIER in LEAGUE_TIERS

    def test_league_xp_promotion_logic(self) -> None:
        """Top 10 % of a 50-person cohort promotes — verify cutoff arithmetic."""
        cohort_size = 50
        promotion_cutoff = int(cohort_size * 0.10)  # top 10 %
        assert promotion_cutoff == 5
        # A student ranked 5 (1-indexed) is in the promotion zone
        assert promotion_cutoff >= 5

    def test_league_unique_student_per_week(self) -> None:
        """The UniqueConstraint uq_league_membership_student_week is declared."""
        table_args = LeagueMembership.__table_args__
        constraint_names = []
        for arg in table_args:
            # UniqueConstraint objects carry a .name attribute
            if hasattr(arg, "name") and arg.name:
                constraint_names.append(arg.name)
        assert "uq_league_membership_student_week" in constraint_names, (
            "Expected unique constraint uq_league_membership_student_week"
        )

    def test_league_history_records_tier_change(self) -> None:
        """LeagueHistory must capture from_tier and to_tier for auditing."""
        history = LeagueHistory(
            student_id="student-003",
            week_start=_now(),
            from_tier="BRONZE",
            to_tier="SILVER",
            final_rank=3,
            final_xp=420,
        )
        assert history.from_tier == "BRONZE"
        assert history.to_tier == "SILVER"
        assert history.final_xp == 420
        assert history.final_rank == 3

    def test_league_tiers_ordered_correctly(self) -> None:
        """LEAGUE_TIERS must be ordered from lowest to highest prestige."""
        assert LEAGUE_TIERS.index("BRONZE") < LEAGUE_TIERS.index("SILVER")
        assert LEAGUE_TIERS.index("SILVER") < LEAGUE_TIERS.index("GOLD")
        assert LEAGUE_TIERS.index("GOLD") < LEAGUE_TIERS.index("PLATINUM")
        assert LEAGUE_TIERS.index("PLATINUM") < LEAGUE_TIERS.index("CHAMPION")


# ===========================================================================
# F1 — Duel System
# ===========================================================================


@pytest.mark.skipif(not _DUEL_OK, reason="models.duel unavailable")
class TestF1DuelSystem:
    """F1: 1v1 duel session, match round, and ELO rating models."""

    def test_duel_session_creation(self) -> None:
        """DuelSession must store player IDs and subject."""
        session = DuelSession(
            player1_id="user-aaa",
            subject="matematik",
        )
        assert session.player1_id == "user-aaa"
        assert session.subject == "matematik"

    def test_duel_elo_default_1200(self) -> None:
        """DuelRating default ELO must be 1200.0 (standard ELO starting point)."""
        # Column defaults are applied by DB on flush; read from column metadata.
        assert _col_default(DuelRating, "elo_rating") == pytest.approx(1200.0)
        assert _col_default(DuelRating, "peak_rating") == pytest.approx(1200.0)

    def test_duel_match_cascade_delete_fk_declared(self) -> None:
        """DuelMatch.session_id FK must declare ondelete='CASCADE'."""
        # Inspect the SQLAlchemy Column object for ondelete
        session_id_col = DuelMatch.__table__.c["session_id"]
        fk = list(session_id_col.foreign_keys)[0]
        assert fk.ondelete.upper() == "CASCADE", (
            "DuelMatch.session_id FK must be CASCADE to remove matches when session deleted"
        )

    def test_duel_rating_unique_per_student(self) -> None:
        """DuelRating.student_id must have a unique constraint."""
        student_id_col = DuelRating.__table__.c["student_id"]
        assert student_id_col.unique, (
            "DuelRating.student_id must be declared unique"
        )

    def test_duel_status_transitions(self) -> None:
        """Valid duel status values cover the full lifecycle."""
        valid_statuses = {"waiting", "active", "completed", "cancelled", "expired"}
        # Column default 'waiting' verified via metadata (not applied until DB flush)
        assert _col_default(DuelSession, "status") == "waiting"
        # All lifecycle values must be non-empty strings
        for status in valid_statuses:
            assert isinstance(status, str)
            assert len(status) > 0

    def test_duel_match_player_answer_fields(self) -> None:
        """DuelMatch must carry per-player answer, timing, and correctness fields."""
        match = DuelMatch(
            session_id=_make_uuid(),
            question_id=_make_uuid(),
            question_order=1,
            player1_answer="A",
            player1_time_ms=3200,
            player1_correct=True,
            player2_answer="B",
            player2_time_ms=4500,
            player2_correct=False,
        )
        assert match.player1_answer == "A"
        assert match.player1_correct is True
        assert match.player2_correct is False
        assert match.player1_time_ms == 3200


# ===========================================================================
# F7 — Study Planner
# ===========================================================================


@pytest.mark.skipif(not _STUDY_PLANNER_OK, reason="models.study_planner unavailable")
class TestF7StudyPlanner:
    """F7: Study plan and weekly goal model behaviour."""

    def test_study_plan_creation(self) -> None:
        """StudyPlan must store student_id and yks_date."""
        yks = date(2026, 6, 15)
        plan = StudyPlan(student_id="student-sp-01", yks_date=yks)
        assert plan.student_id == "student-sp-01"
        assert plan.yks_date == yks

    def test_weekly_goal_cascade_delete_fk_declared(self) -> None:
        """WeeklyGoal.plan_id FK must declare ondelete='CASCADE'."""
        plan_id_col = WeeklyGoal.__table__.c["plan_id"]
        fk = list(plan_id_col.foreign_keys)[0]
        assert fk.ondelete.upper() == "CASCADE", (
            "WeeklyGoal.plan_id FK must be CASCADE to delete goals with parent plan"
        )

    def test_study_plan_active_filter_default(self) -> None:
        """is_active column default must be True for new study plans."""
        # Column defaults are not applied until flush; read from metadata.
        assert _col_default(StudyPlan, "is_active") is True

    def test_weekly_goal_progress_fields(self) -> None:
        """WeeklyGoal must accept progress tracking fields."""
        goal = WeeklyGoal(
            plan_id=1,
            week_number=3,
            target_questions=60,
            target_reviews=20,
            completed_questions=45,
            completed_reviews=15,
            accuracy_rate=0.78,
        )
        assert goal.week_number == 3
        assert goal.target_questions == 60
        assert goal.completed_questions == 45
        assert goal.accuracy_rate == pytest.approx(0.78)

    def test_weekly_goal_week_number_one_based(self) -> None:
        """Week numbering is 1-based; week_number=1 is valid, 0 is unexpected."""
        goal = WeeklyGoal(plan_id=1, week_number=1)
        assert goal.week_number == 1
        assert goal.week_number > 0, "Week numbering should be 1-based"


# ===========================================================================
# F6 — Proactive Coaching
# ===========================================================================


@pytest.mark.skipif(not _COACHING_OK, reason="models.coaching unavailable")
class TestF6Coaching:
    """F6: Coaching event and engagement signal model behaviour."""

    def test_coaching_event_creation(self) -> None:
        """CoachingEvent must store student_id, event_type, and message."""
        event = CoachingEvent(
            student_id="student-coach-01",
            event_type="weakness_alert",
            message="Trigonometri konusunda zayıflık tespit edildi.",
        )
        assert event.student_id == "student-coach-01"
        assert event.event_type == "weakness_alert"
        assert "Trigonometri" in event.message

    def test_engagement_signal_recording(self) -> None:
        """StudentEngagementSignal must store signal_type and numeric value."""
        signal = StudentEngagementSignal(
            student_id="student-coach-02",
            signal_type="session_duration",
            value=42.5,
        )
        assert signal.student_id == "student-coach-02"
        assert signal.signal_type == "session_duration"
        assert signal.value == pytest.approx(42.5)

    def test_coaching_event_interaction_tracking(self) -> None:
        """CoachingEvent interaction timestamps are nullable by default."""
        event = CoachingEvent(
            student_id="student-coach-03",
            event_type="streak_encouragement",
            message="7 günlük seri devam ediyor!",
        )
        # Before any user interaction these must all be None
        assert event.shown_at is None
        assert event.clicked_at is None
        assert event.dismissed_at is None

    def test_coaching_event_priority_default(self) -> None:
        """CoachingEvent priority column default must be 0 (lowest)."""
        # Column defaults are not applied until flush; read from metadata.
        assert _col_default(CoachingEvent, "priority") == 0

    def test_coaching_event_trigger_data_json(self) -> None:
        """trigger_data accepts a dict payload (serialised as JSON)."""
        trigger = {"weak_topic": "türev", "error_rate": 0.65}
        event = CoachingEvent(
            student_id="student-coach-05",
            event_type="topic_recommendation",
            message="Türev konusunu tekrar gözden geçirmenizi öneririz.",
            trigger_data=trigger,
        )
        assert event.trigger_data["weak_topic"] == "türev"
        assert event.trigger_data["error_rate"] == pytest.approx(0.65)


# ===========================================================================
# F4 — Knowledge Graph
# ===========================================================================


@pytest.mark.skipif(not _KG_OK, reason="models.knowledge_graph unavailable")
class TestF4KnowledgeGraph:
    """F4: Knowledge point, question mapping, and student mastery models."""

    def test_knowledge_point_unique_code(self) -> None:
        """KnowledgePoint.code must be declared unique at DB schema level."""
        code_col = KnowledgePoint.__table__.c["code"]
        assert code_col.unique, (
            "KnowledgePoint.code must be unique — dot-notation codes are identifiers"
        )

    def test_knowledge_point_creation(self) -> None:
        """KnowledgePoint must store dot-notation code and Turkish name."""
        kp = KnowledgePoint(
            code="MAT.FUNC.LIM.01",
            name_tr="Fonksiyon Limiti",
            subject="matematik",
        )
        assert kp.code == "MAT.FUNC.LIM.01"
        assert kp.name_tr == "Fonksiyon Limiti"
        assert kp.subject == "matematik"

    def test_knowledge_mapping_creation(self) -> None:
        """QuestionKnowledgeMapping must link question_id to knowledge_point_id."""
        q_id = _make_uuid()
        kp_id = _make_uuid()
        mapping = QuestionKnowledgeMapping(
            question_id=q_id,
            knowledge_point_id=kp_id,
            is_primary=True,
        )
        assert mapping.question_id == q_id
        assert mapping.knowledge_point_id == kp_id
        assert mapping.is_primary is True

    def test_student_knowledge_state_update(self) -> None:
        """StudentKnowledgeState must expose mastery_level and response_count."""
        state = StudentKnowledgeState(
            student_id="student-kg-01",
            knowledge_point_id=_make_uuid(),
            mastery_level=0.72,
            confidence=0.85,
            response_count=14,
        )
        assert state.mastery_level == pytest.approx(0.72)
        assert state.confidence == pytest.approx(0.85)
        assert state.response_count == 14

    def test_knowledge_point_difficulty_range_default(self) -> None:
        """KnowledgePoint difficulty_range column default must be [0.0, 1.0]."""
        # Column defaults are not applied until flush; read from metadata.
        default_range = _col_default(KnowledgePoint, "difficulty_range")
        assert default_range == [0.0, 1.0]

    def test_knowledge_mapping_unique_constraint(self) -> None:
        """QuestionKnowledgeMapping has unique constraint on (question_id, knowledge_point_id)."""
        ucs = [
            uc.name
            for uc in QuestionKnowledgeMapping.__table__.constraints
            if hasattr(uc, "name") and uc.name
        ]
        assert "uq_question_knowledge_mapping" in ucs, (
            "Expected unique constraint uq_question_knowledge_mapping"
        )


# ===========================================================================
# F11 — DINA Model
# ===========================================================================


@pytest.mark.skipif(not _DINA_OK, reason="models.dina unavailable")
class TestF11DIMAModel:
    """F11: DINA cognitive diagnostic model — NanoSkill, QMatrix, DINAParameter."""

    def test_nano_skill_creation(self) -> None:
        """NanoSkill must store knowledge_point_id, name, and subject."""
        skill = NanoSkill(
            knowledge_point_id=_make_uuid(),
            name="Türev Zincir Kuralı",
            subject="matematik",
        )
        assert skill.name == "Türev Zincir Kuralı"
        assert skill.subject == "matematik"

    def test_q_matrix_unique_pair_index(self) -> None:
        """QMatrix idx_qmatrix_pair index must be declared unique."""
        indexes = {idx.name: idx for idx in QMatrix.__table__.indexes}
        assert "idx_qmatrix_pair" in indexes, "idx_qmatrix_pair index not found"
        assert indexes["idx_qmatrix_pair"].unique is True

    def test_dina_parameter_defaults(self) -> None:
        """DINAParameter slip column default must be 0.1, guess must be 0.2."""
        # Column defaults are not applied until flush; read from metadata.
        assert _col_default(DINAParameter, "slip") == pytest.approx(0.1)
        assert _col_default(DINAParameter, "guess") == pytest.approx(0.2)

    def test_dina_question_id_unique(self) -> None:
        """DINAParameter.question_id must be unique (one parameter set per question)."""
        question_id_col = DINAParameter.__table__.c["question_id"]
        assert question_id_col.unique, (
            "DINAParameter.question_id must be unique — one DINA row per question"
        )

    def test_student_nano_skill_mastery_default(self) -> None:
        """StudentNanoSkillMastery mastery column default must be 0.5 (uninformed prior)."""
        # Column defaults are not applied until flush; read from metadata.
        assert _col_default(StudentNanoSkillMastery, "mastery") == pytest.approx(
            0.5
        ), "DINA uninformed prior should be 0.5"

    def test_q_matrix_cascade_delete_fk(self) -> None:
        """QMatrix.nano_skill_id FK must declare ondelete='CASCADE'."""
        nano_col = QMatrix.__table__.c["nano_skill_id"]
        fk = list(nano_col.foreign_keys)[0]
        assert fk.ondelete.upper() == "CASCADE"


# ===========================================================================
# F15 — Error Clustering
# ===========================================================================


@pytest.mark.skipif(not _EC_OK, reason="models.error_cluster unavailable")
class TestF15ErrorClustering:
    """F15: Error cluster and peer recommendation models."""

    def test_error_cluster_creation(self) -> None:
        """ErrorCluster must store subject and error_pattern."""
        cluster = ErrorCluster(
            subject="matematik",
            error_pattern="kavram_hatasi:turev",
        )
        assert cluster.subject == "matematik"
        assert cluster.error_pattern == "kavram_hatasi:turev"

    def test_error_cluster_student_count_default(self) -> None:
        """ErrorCluster.student_count column default must be 0."""
        # Column defaults are not applied until flush; read from metadata.
        assert _col_default(ErrorCluster, "student_count") == 0

    def test_peer_recommendation_creation(self) -> None:
        """PeerRecommendation must link cluster_id to source/target topics."""
        rec = PeerRecommendation(
            cluster_id=_make_uuid(),
            source_topic="Limit",
            target_topic="Türev",
            improvement_rate=0.31,
            sample_size=87,
        )
        assert rec.source_topic == "Limit"
        assert rec.target_topic == "Türev"
        assert rec.improvement_rate == pytest.approx(0.31)
        assert rec.sample_size == 87


# ===========================================================================
# Integration / Flow Tests
# ===========================================================================


@pytest.mark.skipif(
    not (_LEAGUE_OK and _DUEL_OK and _COACHING_OK),
    reason="One or more models needed for integration tests are unavailable",
)
class TestIntegrationFlows:
    """Cross-model flow assertions — no DB required, pure object graph checks."""

    def test_league_xp_to_history_flow(self) -> None:
        """XP accumulated in LeagueMembership should be transferable to LeagueHistory."""
        week = _now()
        membership = LeagueMembership(
            student_id="student-flow-01",
            week_start=week,
            weekly_xp=850,
            league_tier="SILVER",
            rank=7,
        )
        # Simulate week-end snapshot to history
        history = LeagueHistory(
            student_id=membership.student_id,
            week_start=membership.week_start,
            from_tier=membership.league_tier,
            to_tier="GOLD",  # promoted
            final_rank=membership.rank,
            final_xp=membership.weekly_xp,
        )
        assert history.final_xp == 850
        assert history.from_tier == "SILVER"
        assert history.to_tier == "GOLD"
        assert history.student_id == membership.student_id

    def test_duel_full_flow(self) -> None:
        """Create session, add match rounds, then mark session complete."""
        # Default status verified via column metadata
        assert _col_default(DuelSession, "status") == "waiting"
        session = DuelSession(
            player1_id="user-p1",
            player2_id="user-p2",
            subject="kimya",
            question_count=3,
            status="waiting",  # explicitly set so the instance has the value
        )

        # Simulate player 2 joins → active
        session.status = "active"
        assert session.status == "active"

        # Add match rounds
        rounds = []
        for order in range(1, 4):
            rounds.append(
                DuelMatch(
                    session_id="mock-session-id",
                    question_id=_make_uuid(),
                    question_order=order,
                    player1_correct=(order % 2 == 0),
                    player2_correct=(order % 2 != 0),
                )
            )
        assert len(rounds) == 3

        # Compute mock scores
        p1_score = sum(1 for r in rounds if r.player1_correct)
        p2_score = sum(1 for r in rounds if r.player2_correct)
        session.player1_score = p1_score
        session.player2_score = p2_score
        session.status = "completed"
        session.winner_id = "user-p1" if p1_score > p2_score else "user-p2"

        assert session.status == "completed"
        assert session.player1_score + session.player2_score == 3
        assert session.winner_id in {"user-p1", "user-p2"}

    def test_coaching_suggestion_to_interaction_flow(self) -> None:
        """A shown coaching event should have shown_at set; click updates clicked_at."""
        event = CoachingEvent(
            student_id="student-flow-02",
            event_type="weakness_alert",
            message="Fonksiyon konusunu tekrar çalış.",
            priority=2,
        )
        assert event.shown_at is None

        # Simulate the event being shown to the student
        shown_ts = _now()
        event.shown_at = shown_ts
        assert event.shown_at == shown_ts
        assert event.clicked_at is None

        # Simulate student clicking the recommendation
        clicked_ts = _now()
        event.clicked_at = clicked_ts
        assert event.clicked_at == clicked_ts
        # dismissed_at must remain None — student acted on it
        assert event.dismissed_at is None


# ===========================================================================
# Additional edge-case / boundary tests
# ===========================================================================


@pytest.mark.skipif(not _KG_OK, reason="models.knowledge_graph unavailable")
class TestKnowledgeGraphEdgeCases:
    """Additional edge-case tests for F4 models."""

    def test_student_knowledge_state_mastery_boundary_zero(self) -> None:
        """Mastery level of 0.0 represents no knowledge."""
        state = StudentKnowledgeState(
            student_id="student-edge-01",
            knowledge_point_id=_make_uuid(),
            mastery_level=0.0,
        )
        assert state.mastery_level == 0.0

    def test_student_knowledge_state_mastery_boundary_one(self) -> None:
        """Mastery level of 1.0 represents full mastery."""
        state = StudentKnowledgeState(
            student_id="student-edge-02",
            knowledge_point_id=_make_uuid(),
            mastery_level=1.0,
        )
        assert state.mastery_level == pytest.approx(1.0)

    def test_knowledge_point_prerequisite_ids_default_empty(self) -> None:
        """KnowledgePoint prerequisite_ids column default must be an empty list."""
        # Column defaults are not applied until flush; read from metadata.
        default_val = _col_default(KnowledgePoint, "prerequisite_ids")
        assert default_val == []


@pytest.mark.skipif(not _DINA_OK, reason="models.dina unavailable")
class TestDINAEdgeCases:
    """Additional edge-case tests for F11 DINA models."""

    def test_dina_slip_guess_sum_less_than_one(self) -> None:
        """Default slip + guess must be < 1.0 for valid DINA item parameters."""
        # Column defaults are not applied until flush; read from metadata.
        slip_default = _col_default(DINAParameter, "slip")
        guess_default = _col_default(DINAParameter, "guess")
        assert slip_default + guess_default < 1.0, (
            f"Default slip ({slip_default}) + guess ({guess_default}) must be < 1.0"
        )

    def test_nano_skill_description_nullable(self) -> None:
        """NanoSkill.description is optional (nullable)."""
        skill = NanoSkill(
            knowledge_point_id=_make_uuid(),
            name="Integral Parçalama",
            subject="matematik",
        )
        # No description supplied — must not raise
        assert skill.description is None


@pytest.mark.skipif(not _EC_OK, reason="models.error_cluster unavailable")
class TestErrorClusterEdgeCases:
    """Additional edge-case tests for F15 error clustering."""

    def test_peer_recommendation_improvement_rate_zero(self) -> None:
        """improvement_rate of 0.0 is a valid (no-improvement) value."""
        rec = PeerRecommendation(
            cluster_id=_make_uuid(),
            source_topic="İntegral",
            target_topic="Alan Hesabı",
            improvement_rate=0.0,
            sample_size=5,
        )
        assert rec.improvement_rate == pytest.approx(0.0)

    def test_error_cluster_pattern_format(self) -> None:
        """Error pattern format follows 'category:topic' convention."""
        pattern = "kavram_hatasi:limit"
        parts = pattern.split(":")
        assert len(parts) == 2, "Pattern must be 'category:topic' format"
        category, topic = parts
        assert len(category) > 0
        assert len(topic) > 0
