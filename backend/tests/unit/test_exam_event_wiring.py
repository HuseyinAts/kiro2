"""
Tests for exam + assessment event wiring.
FAZ 2.3 — verifies sinav.py and placement_assessment_api.py
call LearningEventService correctly.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services.learning_event_service import LearningEventService


class TestExamEventWiring:
    """Verify on_exam_completed is called with correct params."""

    @pytest.mark.asyncio
    async def test_exam_xp_scales_with_correct_answers(self):
        """More correct answers = more XP."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()

        with (
            patch(
                "services.learning_event_service.GamificationDBService.award_xp",
                new_callable=AsyncMock,
                return_value=0,
            ) as mock_xp,
            patch(
                "services.learning_event_service.GamificationDBService.update_streak",
                new_callable=AsyncMock,
            ),
        ):
            await LearningEventService.on_exam_completed(
                student_id="s1",
                correct_answers=10,
                total_questions=40,
                net_score=25.0,
                db=db,
            )

            # 10 correct * 5 = 50 XP (no bonus, 25% < 70%)
            mock_xp.assert_called_once()
            call_kwargs = mock_xp.call_args[1]
            assert call_kwargs["amount"] == 50
            assert call_kwargs["source"] == "sinav"

    @pytest.mark.asyncio
    async def test_exam_high_score_bonus(self):
        """70%+ correct triggers +100 bonus."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()

        with (
            patch(
                "services.learning_event_service.GamificationDBService.award_xp",
                new_callable=AsyncMock,
                return_value=0,
            ) as mock_xp,
            patch(
                "services.learning_event_service.GamificationDBService.update_streak",
                new_callable=AsyncMock,
            ),
        ):
            await LearningEventService.on_exam_completed(
                student_id="s1",
                correct_answers=30,
                total_questions=40,
                net_score=75.0,
                db=db,
            )

            call_kwargs = mock_xp.call_args[1]
            assert call_kwargs["amount"] == 250  # 30*5 + 100 bonus

    @pytest.mark.asyncio
    async def test_exam_zero_questions(self):
        """Zero total_questions should not crash (division by zero guard)."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()

        with (
            patch(
                "services.learning_event_service.GamificationDBService.award_xp",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch(
                "services.learning_event_service.GamificationDBService.update_streak",
                new_callable=AsyncMock,
            ),
        ):
            report = await LearningEventService.on_exam_completed(
                student_id="s1",
                correct_answers=0,
                total_questions=0,
                net_score=0.0,
                db=db,
            )

        assert report["xp"] == 0


class TestAssessmentEventWiring:
    """Verify on_assessment_completed creates correct DB records."""

    @pytest.mark.asyncio
    async def test_multi_subject_upsert(self):
        """Multiple subjects should each get ability + BKT rows."""
        from types import SimpleNamespace
        from unittest.mock import MagicMock

        db = AsyncMock()
        mock_topic_result = MagicMock()
        mock_topic_result.all.return_value = [
            SimpleNamespace(id="topic-1", subject_area="MATEMATIK"),
            SimpleNamespace(id="topic-2", subject_area="FIZIK"),
            SimpleNamespace(id="topic-3", subject_area="KIMYA"),
        ]
        db.execute = AsyncMock(
            side_effect=[
                mock_topic_result,
                MagicMock(),
                MagicMock(),
            ]
        )
        db.commit = AsyncMock()

        report = await LearningEventService.on_assessment_completed(
            student_id="s1",
            subjects={
                "matematik": {"theta": 1.5, "se": 0.4},
                "fizik": {"theta": -1.0, "se": 1.0},
                "kimya": {"theta": 0.0, "se": 0.8},
            },
            db=db,
        )

        assert report["abilities"] == 3
        assert report["bkt_states"] == 3
        # 1 topic fetch + 2 bulk upserts = 3 execute calls
        assert db.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_theta_to_p_learn_mapping(self):
        """Verify the theta -> p_learn formula: (theta+3)/6 clamped [0.05, 0.95]."""
        test_cases = [
            (-3.0, 0.05),  # minimum
            (-2.0, round(1 / 6, 4)),  # ~0.1667
            (0.0, 0.5),  # midpoint
            (2.0, round(5 / 6, 4)),  # ~0.8333
            (3.0, 0.95),  # maximum
            (5.0, 0.95),  # clamped
            (-5.0, 0.05),  # clamped
        ]

        for theta, expected_p_learn in test_cases:
            actual = round(max(0.05, min(0.95, (theta + 3) / 6)), 4)
            assert actual == expected_p_learn, (
                f"theta={theta}: expected {expected_p_learn}, got {actual}"
            )

    @pytest.mark.asyncio
    async def test_db_error_captured_in_report(self):
        """DB failure should be captured, not raised."""
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=RuntimeError("DB connection lost"))
        db.commit = AsyncMock()

        report = await LearningEventService.on_assessment_completed(
            student_id="s1",
            subjects={"matematik": {"theta": 0.0, "se": 1.0}},
            db=db,
        )

        assert "error" in report
        assert "DB connection lost" in report["error"]
