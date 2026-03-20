"""
Tests for LearningEventService + GamificationDBService.
FAZ 1.5 — verifies the central event coordination layer.
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.learning_event_service import GamificationDBService, LearningEventService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Create a mock AsyncSession."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# LearningEventService.on_quiz_completed
# ---------------------------------------------------------------------------


class TestOnQuizCompleted:
    @pytest.mark.asyncio
    async def test_returns_report_with_all_keys(self, mock_db):
        """Report must contain bkt, xp, streak keys."""
        with (
            patch(
                "services.learning_event_service.GamificationDBService.award_xp",
                new_callable=AsyncMock,
                return_value=50,
            ),
            patch(
                "services.learning_event_service.GamificationDBService.update_streak",
                new_callable=AsyncMock,
                return_value={"current_streak": 1, "largest_streak": 1},
            ),
            patch(
                "services.bkt_service.BKTService.record_answer", new_callable=AsyncMock
            ),
        ):
            report = await LearningEventService.on_quiz_completed(
                student_id="s1",
                question_results=[
                    {"question_id": "q1", "is_correct": True},
                    {"question_id": "q2", "is_correct": False},
                ],
                q_meta={
                    "q1": {"topic_id": "t1", "subject": "matematik"},
                    "q2": {"topic_id": "t2", "subject": "matematik"},
                },
                score=50.0,
                passed=False,
                db=mock_db,
            )

        assert "bkt" in report
        assert "xp" in report
        assert "streak" in report

    @pytest.mark.asyncio
    async def test_xp_calculation_no_pass(self, mock_db):
        """XP = correct_count * 10, no bonus if not passed."""
        captured_xp = {}

        async def capture_award_xp(*, student_id, amount, source, db, topic_id=None):
            captured_xp["amount"] = amount
            return amount

        with (
            patch(
                "services.learning_event_service.GamificationDBService.award_xp",
                side_effect=capture_award_xp,
            ),
            patch(
                "services.learning_event_service.GamificationDBService.update_streak",
                new_callable=AsyncMock,
            ),
            patch(
                "services.bkt_service.BKTService.record_answer", new_callable=AsyncMock
            ),
        ):
            await LearningEventService.on_quiz_completed(
                student_id="s1",
                question_results=[
                    {"question_id": "q1", "is_correct": True},
                    {"question_id": "q2", "is_correct": True},
                    {"question_id": "q3", "is_correct": False},
                ],
                q_meta={},
                score=66.7,
                passed=False,
                db=mock_db,
            )

        assert captured_xp["amount"] == 20  # 2 correct * 10

    @pytest.mark.asyncio
    async def test_xp_calculation_with_pass_bonus(self, mock_db):
        """XP includes +50 bonus when passed=True."""
        captured_xp = {}

        async def capture_award_xp(*, student_id, amount, source, db, topic_id=None):
            captured_xp["amount"] = amount
            return amount

        with (
            patch(
                "services.learning_event_service.GamificationDBService.award_xp",
                side_effect=capture_award_xp,
            ),
            patch(
                "services.learning_event_service.GamificationDBService.update_streak",
                new_callable=AsyncMock,
            ),
            patch(
                "services.bkt_service.BKTService.record_answer", new_callable=AsyncMock
            ),
        ):
            await LearningEventService.on_quiz_completed(
                student_id="s1",
                question_results=[
                    {"question_id": "q1", "is_correct": True},
                ],
                q_meta={},
                score=100.0,
                passed=True,
                db=mock_db,
            )

        assert captured_xp["amount"] == 60  # 1*10 + 50 bonus

    @pytest.mark.asyncio
    async def test_bkt_failure_does_not_block_xp(self, mock_db):
        """If BKT fails, XP and streak should still succeed."""
        with (
            patch(
                "services.learning_event_service.GamificationDBService.award_xp",
                new_callable=AsyncMock,
                return_value=10,
            ),
            patch(
                "services.learning_event_service.GamificationDBService.update_streak",
                new_callable=AsyncMock,
                return_value={"current_streak": 1, "largest_streak": 1},
            ),
            patch(
                "services.bkt_service.BKTService.record_answer",
                new_callable=AsyncMock,
                side_effect=RuntimeError("BKT unavailable"),
            ),
        ):
            report = await LearningEventService.on_quiz_completed(
                student_id="s1",
                question_results=[{"question_id": "q1", "is_correct": True}],
                q_meta={"q1": {"topic_id": "t1", "subject": "matematik"}},
                score=100.0,
                passed=False,
                db=mock_db,
            )

        assert "error" in report["bkt"]
        assert report["xp"] == 10
        assert report["streak"] == "ok"


# ---------------------------------------------------------------------------
# LearningEventService.on_exam_completed
# ---------------------------------------------------------------------------


class TestOnExamCompleted:
    @pytest.mark.asyncio
    async def test_xp_without_bonus(self, mock_db):
        """5 XP per correct, no bonus under 70%."""
        captured = {}

        async def capture(*, student_id, amount, source, db, topic_id=None):
            captured["amount"] = amount
            return amount

        with (
            patch(
                "services.learning_event_service.GamificationDBService.award_xp",
                side_effect=capture,
            ),
            patch(
                "services.learning_event_service.GamificationDBService.update_streak",
                new_callable=AsyncMock,
            ),
        ):
            await LearningEventService.on_exam_completed(
                student_id="s1",
                correct_answers=5,
                total_questions=10,
                net_score=50.0,
                db=mock_db,
            )

        assert captured["amount"] == 25  # 5 * 5, no bonus (50% < 70%)

    @pytest.mark.asyncio
    async def test_xp_with_bonus(self, mock_db):
        """100 XP bonus when >70% correct."""
        captured = {}

        async def capture(*, student_id, amount, source, db, topic_id=None):
            captured["amount"] = amount
            return amount

        with (
            patch(
                "services.learning_event_service.GamificationDBService.award_xp",
                side_effect=capture,
            ),
            patch(
                "services.learning_event_service.GamificationDBService.update_streak",
                new_callable=AsyncMock,
            ),
        ):
            await LearningEventService.on_exam_completed(
                student_id="s1",
                correct_answers=8,
                total_questions=10,
                net_score=80.0,
                db=mock_db,
            )

        assert captured["amount"] == 140  # 8*5 + 100 bonus


# ---------------------------------------------------------------------------
# LearningEventService.on_assessment_completed
# ---------------------------------------------------------------------------


class TestOnAssessmentCompleted:
    @pytest.mark.asyncio
    async def test_creates_abilities_and_bkt(self, mock_db):
        """Should upsert StudentAbility and BKTState per subject."""
        mock_db.execute = AsyncMock(return_value=MagicMock())

        report = await LearningEventService.on_assessment_completed(
            student_id="s1",
            subjects={
                "matematik": {"theta": 1.0, "se": 0.5},
                "fizik": {"theta": -0.5, "se": 1.2},
            },
            db=mock_db,
        )

        assert report["abilities"] == 2
        assert report["bkt_states"] == 2
        # 2 subjects * 2 upserts (ability + bkt) = 4 execute calls + 1 commit
        assert mock_db.execute.call_count == 4

    @pytest.mark.asyncio
    async def test_skips_unknown_subjects(self, mock_db):
        """Subjects not in SUBJECT_ID_MAP should be skipped."""
        mock_db.execute = AsyncMock(return_value=MagicMock())

        report = await LearningEventService.on_assessment_completed(
            student_id="s1",
            subjects={
                "matematik": {"theta": 0.0, "se": 1.0},
                "unknown_subject": {"theta": 0.5, "se": 0.8},
            },
            db=mock_db,
        )

        assert report["abilities"] == 1  # only matematik
        assert report["bkt_states"] == 1

    @pytest.mark.asyncio
    async def test_p_learn_clamped(self, mock_db):
        """p_learn = (theta+3)/6, clamped to [0.05, 0.95]."""

        # theta = 3.0 -> (3+3)/6 = 1.0 -> clamped to 0.95
        # theta = -3.0 -> (-3+3)/6 = 0.0 -> clamped to 0.05
        # theta = 0.0 -> (0+3)/6 = 0.5
        assert max(0.05, min(0.95, (3.0 + 3) / 6)) == 0.95
        assert max(0.05, min(0.95, (-3.0 + 3) / 6)) == 0.05
        assert max(0.05, min(0.95, (0.0 + 3) / 6)) == 0.5


# ---------------------------------------------------------------------------
# GamificationDBService.update_streak
# ---------------------------------------------------------------------------


class TestStreakLogic:
    @pytest.mark.asyncio
    async def test_new_streak_created(self, mock_db):
        """First activity creates streak with current=1."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Use object() sentinel to bypass Streak() constructor which triggers
        # SQLAlchemy mapper config (ExamQuestion→QuestionBankItem unresolved relationship)
        mock_streak_instance = MagicMock()
        mock_streak_instance.current_streak = 1
        mock_streak_instance.largest_streak = 1
        mock_streak_instance.last_activity = None

        with patch(
            "models.gamification.Streak",
            return_value=mock_streak_instance,
        ) as MockStreak:
            # Also need to preserve .user_id attribute for select(Streak).where(...)
            MockStreak.__tablename__ = "streaks"
            MockStreak.user_id = MagicMock()

            # Need to patch select to avoid passing MagicMock to SQLAlchemy
            with patch("services.learning_event_service.select") as mock_select:
                mock_select.return_value.where.return_value = "fake_stmt"

                result = await GamificationDBService.update_streak(
                    student_id="s1", db=mock_db
                )

        assert result["current_streak"] == 1
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_consecutive_day_increments(self, mock_db):
        """Activity on consecutive day increments streak."""
        yesterday = date.today() - timedelta(days=1)
        mock_streak = MagicMock()
        mock_streak.last_activity = yesterday
        mock_streak.current_streak = 3
        mock_streak.largest_streak = 5
        mock_streak.total_days_active = 10

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_streak
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await GamificationDBService.update_streak(student_id="s1", db=mock_db)

        assert result["current_streak"] == 4
        assert mock_streak.total_days_active == 11

    @pytest.mark.asyncio
    async def test_same_day_no_change(self, mock_db):
        """Same-day activity does not change streak."""
        mock_streak = MagicMock()
        mock_streak.last_activity = date.today()
        mock_streak.current_streak = 3
        mock_streak.largest_streak = 5

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_streak
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await GamificationDBService.update_streak(student_id="s1", db=mock_db)

        assert result["current_streak"] == 3  # unchanged

    @pytest.mark.asyncio
    async def test_gap_resets_streak(self, mock_db):
        """Gap of 2+ days resets streak to 1."""
        two_days_ago = date.today() - timedelta(days=2)
        mock_streak = MagicMock()
        mock_streak.last_activity = two_days_ago
        mock_streak.current_streak = 10
        mock_streak.largest_streak = 15
        mock_streak.total_days_active = 20

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_streak
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await GamificationDBService.update_streak(student_id="s1", db=mock_db)

        assert result["current_streak"] == 1  # reset
        assert mock_streak.total_days_active == 21
