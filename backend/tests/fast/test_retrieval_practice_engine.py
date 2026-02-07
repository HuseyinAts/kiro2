"""Tests for Retrieval Practice Engine.

Bjork's Generation Effect + Interleaving + Testing Effect.
"""

from __future__ import annotations

from services.retrieval_practice_engine import (
    InterleavingStrategy,
    RetrievalItem,
    RetrievalPlan,
    RetrievalSession,
    RetrievalType,
    calculate_optimal_retrieval_time,
    calculate_retrieval_probability,
    create_retrieval_session,
    evaluate_retrieval_performance,
    generate_retrieval_schedule,
    recommend_interleaving_ratio,
)


class TestCalculateRetrievalProbability:
    """calculate_retrieval_probability tests."""

    def test_normal_retrieval_probability(self):
        """Normal FSRS retrieval probability calculation."""
        # R(t) = exp(-t/S), S=10, t=5 → exp(-0.5) ≈ 0.606
        prob = calculate_retrieval_probability(stability=10.0, days_since_review=5.0)
        assert 0.6 <= prob <= 0.61, f"Expected ~0.606, got {prob}"

    def test_zero_days_perfect_retention(self):
        """Zero days since review → 100% retention."""
        prob = calculate_retrieval_probability(stability=5.0, days_since_review=0.0)
        assert prob == 1.0

    def test_large_days_low_retention(self):
        """Large days → very low retention."""
        prob = calculate_retrieval_probability(stability=2.0, days_since_review=100.0)
        assert prob < 0.001, f"Expected near-zero, got {prob}"

    def test_zero_stability_zero_probability(self):
        """Zero stability → 0% probability (edge case)."""
        prob = calculate_retrieval_probability(stability=0.0, days_since_review=5.0)
        assert prob == 0.0

    def test_negative_stability_zero_probability(self):
        """Negative stability (invalid) → 0% probability."""
        prob = calculate_retrieval_probability(stability=-5.0, days_since_review=10.0)
        assert prob == 0.0


class TestCalculateOptimalRetrievalTime:
    """calculate_optimal_retrieval_time tests."""

    def test_standard_optimal_time(self):
        """Standard case: S=10, R=0.85 → t ≈ 1.625 days."""
        # t = -S * ln(R) = -10 * ln(0.85) ≈ 10 * 0.1625 ≈ 1.625
        t_opt = calculate_optimal_retrieval_time(stability=10.0, target_retention=0.85)
        assert 1.6 <= t_opt <= 1.7, f"Expected ~1.625, got {t_opt}"

    def test_high_retention_shorter_interval(self):
        """Higher retention target → shorter interval."""
        t_opt = calculate_optimal_retrieval_time(stability=10.0, target_retention=0.95)
        assert t_opt < 1.0, f"Expected <1 day, got {t_opt}"

    def test_low_retention_longer_interval(self):
        """Lower retention target → longer interval."""
        t_opt = calculate_optimal_retrieval_time(stability=10.0, target_retention=0.5)
        assert t_opt > 5.0, f"Expected >5 days, got {t_opt}"

    def test_zero_stability_returns_default(self):
        """Zero stability → default 1.0 day."""
        t_opt = calculate_optimal_retrieval_time(stability=0.0, target_retention=0.85)
        assert t_opt == 1.0

    def test_invalid_retention_zero_returns_default(self):
        """Invalid retention (0) → default 1.0 day."""
        t_opt = calculate_optimal_retrieval_time(stability=10.0, target_retention=0.0)
        assert t_opt == 1.0

    def test_invalid_retention_one_returns_default(self):
        """Invalid retention (1.0) → default 1.0 day."""
        t_opt = calculate_optimal_retrieval_time(stability=10.0, target_retention=1.0)
        assert t_opt == 1.0


class TestRecommendInterleavingRatio:
    """recommend_interleaving_ratio tests."""

    def test_low_ability_low_interleaving(self):
        """Low ability student → lower interleaving (blocked preference)."""
        ratio = recommend_interleaving_ratio(student_ability=-3.0, topic_count=2)
        assert ratio < 0.5, f"Expected <0.5 for very low ability, got {ratio}"

    def test_medium_ability_moderate_interleaving(self):
        """Medium ability → moderate interleaving."""
        ratio = recommend_interleaving_ratio(student_ability=0.0, topic_count=5)
        assert 0.5 <= ratio <= 0.8, f"Expected 0.5-0.8, got {ratio}"

    def test_high_ability_high_interleaving(self):
        """High ability → high interleaving (interleaved preference)."""
        ratio = recommend_interleaving_ratio(student_ability=3.0, topic_count=8)
        assert ratio > 0.75, f"Expected >0.75 for high ability, got {ratio}"

    def test_more_topics_increase_interleaving(self):
        """More topics → slight increase in interleaving."""
        ratio_few = recommend_interleaving_ratio(student_ability=0.0, topic_count=2)
        ratio_many = recommend_interleaving_ratio(student_ability=0.0, topic_count=10)
        assert ratio_many > ratio_few, "More topics should increase interleaving"

    def test_high_mastery_bonus(self):
        """High mastery → increases interleaving."""
        ratio_low_mastery = recommend_interleaving_ratio(
            student_ability=0.0, topic_count=5, avg_mastery=0.2
        )
        ratio_high_mastery = recommend_interleaving_ratio(
            student_ability=0.0, topic_count=5, avg_mastery=0.9
        )
        assert ratio_high_mastery > ratio_low_mastery

    def test_ratio_bounds_enforced(self):
        """Interleaving ratio clamped to [0.2, 0.95]."""
        ratio_extreme_low = recommend_interleaving_ratio(
            student_ability=-4.0, topic_count=1, avg_mastery=0.0
        )
        ratio_extreme_high = recommend_interleaving_ratio(
            student_ability=4.0, topic_count=20, avg_mastery=1.0
        )
        assert 0.2 <= ratio_extreme_low <= 0.95
        assert 0.2 <= ratio_extreme_high <= 0.95


class TestGenerateRetrievalSchedule:
    """generate_retrieval_schedule tests."""

    def test_basic_schedule_generation(self):
        """Basic retrieval plan generation."""
        questions = [
            {"id": f"q{i}", "topic": "algebra", "difficulty": 0.5, "fsrs_stability": 2.0}
            for i in range(30)
        ]
        plan = generate_retrieval_schedule(
            student_id="student123",
            subject="matematik",
            topics=["algebra"],
            available_questions=questions,
            student_ability=0.0,
            session_size=20,
        )

        assert plan.student_id == "student123"
        assert plan.subject == "matematik"
        assert len(plan.items) == 20
        assert plan.session_size == 20
        assert plan.interleaving_strategy in [
            InterleavingStrategy.BLOCKED,
            InterleavingStrategy.HYBRID,
            InterleavingStrategy.INTERLEAVED,
        ]

    def test_low_ability_low_interleaving_ratio(self):
        """Very low ability → very low interleaving ratio."""
        questions = [
            {"id": f"q{i}", "topic": "geometri", "difficulty": 0.0, "fsrs_stability": 1.0}
            for i in range(25)
        ]
        plan = generate_retrieval_schedule(
            student_id="beginner",
            subject="matematik",
            topics=["geometri"],
            available_questions=questions,
            student_ability=-4.0,  # Minimum ability
            session_size=15,
        )

        # Very low ability should result in low interleaving ratio
        assert plan.interleaving_ratio < 0.4, f"Expected ratio <0.4, got {plan.interleaving_ratio}"
        # Strategy should be BLOCKED or HYBRID (not INTERLEAVED)
        assert plan.interleaving_strategy != InterleavingStrategy.INTERLEAVED

    def test_high_ability_interleaved_strategy(self):
        """High ability → INTERLEAVED strategy."""
        questions = [
            {
                "id": f"q{i}",
                "topic": f"topic{i % 5}",
                "difficulty": 1.5,
                "fsrs_stability": 5.0,
            }
            for i in range(25)
        ]
        plan = generate_retrieval_schedule(
            student_id="advanced",
            subject="fizik",
            topics=["topic0", "topic1", "topic2", "topic3", "topic4"],
            available_questions=questions,
            student_ability=3.5,  # Very high
            session_size=20,
        )

        assert plan.interleaving_strategy == InterleavingStrategy.INTERLEAVED

    def test_retrieval_type_assignment(self):
        """Retrieval type based on FSRS stability."""
        questions = [
            {"id": "new", "topic": "test", "difficulty": 0.0, "fsrs_stability": 0.5},
            {"id": "medium", "topic": "test", "difficulty": 0.0, "fsrs_stability": 5.0},
            {"id": "well_known", "topic": "test", "difficulty": 0.0, "fsrs_stability": 15.0},
        ]
        plan = generate_retrieval_schedule(
            student_id="test",
            subject="test",
            topics=["test"],
            available_questions=questions,
            session_size=3,
        )

        items_by_id = {item.question_id: item for item in plan.items}

        # New item: RECOGNITION (easiest)
        assert items_by_id["new"].retrieval_type == RetrievalType.RECOGNITION

        # Medium stability: CUED_RECALL
        assert items_by_id["medium"].retrieval_type == RetrievalType.CUED_RECALL

        # Well-known: FREE_RECALL (hardest)
        assert items_by_id["well_known"].retrieval_type == RetrievalType.FREE_RECALL

    def test_empty_questions_empty_plan(self):
        """Empty question list → empty plan."""
        plan = generate_retrieval_schedule(
            student_id="empty",
            subject="test",
            topics=["topic1"],
            available_questions=[],
            session_size=20,
        )

        assert len(plan.items) == 0

    def test_fewer_questions_than_session_size(self):
        """Fewer questions than session_size → all included."""
        questions = [
            {"id": f"q{i}", "topic": "test", "difficulty": 0.0, "fsrs_stability": 2.0}
            for i in range(5)
        ]
        plan = generate_retrieval_schedule(
            student_id="small",
            subject="test",
            topics=["test"],
            available_questions=questions,
            session_size=20,
        )

        assert len(plan.items) == 5


class TestCreateRetrievalSession:
    """create_retrieval_session tests."""

    def test_session_creation(self):
        """Valid session creation from plan."""
        items = [
            RetrievalItem(
                question_id=f"q{i}",
                topic="algebra",
                subject="matematik",
                difficulty=0.5,
                retrieval_type=RetrievalType.RECOGNITION,
            )
            for i in range(10)
        ]
        plan = RetrievalPlan(
            student_id="student_xyz",
            subject="matematik",
            topics=["algebra"],
            items=items,
        )

        session = create_retrieval_session(plan)

        assert session.student_id == "student_xyz"
        assert len(session.items) == 10
        assert session.current_index == 0
        assert session.completed is False
        assert "student_xyz" in session.plan_id


class TestEvaluateRetrievalPerformance:
    """evaluate_retrieval_performance tests."""

    def test_all_correct_high_success_rate(self):
        """All correct answers → 100% success rate."""
        items = [
            RetrievalItem(
                question_id=f"q{i}",
                topic="test",
                subject="test",
                difficulty=0.0,
                retrieval_type=RetrievalType.RECOGNITION,
                fsrs_stability=2.0,
            )
            for i in range(10)
        ]
        session = RetrievalSession(
            plan_id="test_plan",
            student_id="student",
            items=items,
        )
        responses = [{"question_id": f"q{i}", "correct": True} for i in range(10)]

        metrics = evaluate_retrieval_performance(session, responses)

        assert metrics.total_items == 10
        assert metrics.correct == 10
        assert metrics.incorrect == 0
        assert metrics.retrieval_success_rate == 1.0

    def test_all_incorrect_zero_success_rate(self):
        """All incorrect answers → 0% success rate."""
        items = [
            RetrievalItem(
                question_id=f"q{i}",
                topic="test",
                subject="test",
                difficulty=1.0,
                retrieval_type=RetrievalType.FREE_RECALL,
                fsrs_stability=5.0,
            )
            for i in range(8)
        ]
        session = RetrievalSession(
            plan_id="test_fail",
            student_id="student",
            items=items,
        )
        responses = [{"question_id": f"q{i}", "correct": False} for i in range(8)]

        metrics = evaluate_retrieval_performance(session, responses)

        assert metrics.total_items == 8
        assert metrics.correct == 0
        assert metrics.incorrect == 8
        assert metrics.retrieval_success_rate == 0.0

    def test_mixed_performance(self):
        """Mixed correct/incorrect → accurate success rate."""
        items = [
            RetrievalItem(
                question_id=f"q{i}",
                topic="test",
                subject="test",
                difficulty=0.5,
                retrieval_type=RetrievalType.CUED_RECALL,
                fsrs_stability=3.0,
            )
            for i in range(10)
        ]
        session = RetrievalSession(
            plan_id="test_mixed",
            student_id="student",
            items=items,
        )
        # 7 correct, 3 incorrect
        responses = [
            {"question_id": f"q{i}", "correct": i < 7} for i in range(10)
        ]

        metrics = evaluate_retrieval_performance(session, responses)

        assert metrics.total_items == 10
        assert metrics.correct == 7
        assert metrics.incorrect == 3
        assert metrics.retrieval_success_rate == 0.7

    def test_empty_responses_zero_metrics(self):
        """Empty responses → zero metrics."""
        session = RetrievalSession(
            plan_id="empty",
            student_id="student",
            items=[],
        )

        metrics = evaluate_retrieval_performance(session, [])

        assert metrics.total_items == 0
        assert metrics.correct == 0
        assert metrics.incorrect == 0
        assert metrics.retrieval_success_rate == 0.0
        assert metrics.avg_difficulty == 0.0

    def test_fsrs_stability_updates_on_success(self):
        """Successful retrieval increases FSRS stability."""
        items = [
            RetrievalItem(
                question_id="q1",
                topic="test",
                subject="test",
                difficulty=1.0,
                retrieval_type=RetrievalType.RECOGNITION,
                fsrs_stability=5.0,
            )
        ]
        session = RetrievalSession(
            plan_id="stability_test",
            student_id="student",
            items=items,
        )
        responses = [{"question_id": "q1", "correct": True}]

        metrics = evaluate_retrieval_performance(session, responses)

        assert "q1" in metrics.fsrs_updates
        new_stability = metrics.fsrs_updates["q1"]
        assert new_stability > 5.0, f"Expected stability >5.0, got {new_stability}"

    def test_fsrs_stability_updates_on_failure(self):
        """Failed retrieval decreases FSRS stability."""
        items = [
            RetrievalItem(
                question_id="q2",
                topic="test",
                subject="test",
                difficulty=0.5,
                retrieval_type=RetrievalType.FREE_RECALL,
                fsrs_stability=10.0,
            )
        ]
        session = RetrievalSession(
            plan_id="fail_test",
            student_id="student",
            items=items,
        )
        responses = [{"question_id": "q2", "correct": False}]

        metrics = evaluate_retrieval_performance(session, responses)

        assert "q2" in metrics.fsrs_updates
        new_stability = metrics.fsrs_updates["q2"]
        assert new_stability < 10.0, f"Expected stability <10.0, got {new_stability}"
        # Failed: multiply by 0.5 → ~5.0
        assert 4.9 <= new_stability <= 5.1

    def test_retention_boost_optimal_difficulty(self):
        """70% success rate → maximum retention boost."""
        items = [
            RetrievalItem(
                question_id=f"q{i}",
                topic="test",
                subject="test",
                difficulty=0.0,
                retrieval_type=RetrievalType.RECOGNITION,
                fsrs_stability=2.0,
            )
            for i in range(10)
        ]
        session = RetrievalSession(
            plan_id="optimal",
            student_id="student",
            items=items,
        )
        # Exactly 7/10 correct (70%)
        responses = [{"question_id": f"q{i}", "correct": i < 7} for i in range(10)]

        metrics = evaluate_retrieval_performance(session, responses)

        # At 70% success, difficulty_bonus = 1.0 - abs(0.7 - 0.7) * 2 = 1.0
        # estimated_boost = 0.15 * (0.5 + 0.5 * 1.0) = 0.15
        assert metrics.estimated_retention_boost == 0.15

    def test_avg_difficulty_calculation(self):
        """Average difficulty computed correctly."""
        items = [
            RetrievalItem(
                question_id="q1",
                topic="test",
                subject="test",
                difficulty=-2.0,
                retrieval_type=RetrievalType.RECOGNITION,
            ),
            RetrievalItem(
                question_id="q2",
                topic="test",
                subject="test",
                difficulty=2.0,
                retrieval_type=RetrievalType.FREE_RECALL,
            ),
        ]
        session = RetrievalSession(
            plan_id="diff_test",
            student_id="student",
            items=items,
        )
        responses = [
            {"question_id": "q1", "correct": True},
            {"question_id": "q2", "correct": False},
        ]

        metrics = evaluate_retrieval_performance(session, responses)

        # Average: (-2.0 + 2.0) / 2 = 0.0
        assert metrics.avg_difficulty == 0.0
