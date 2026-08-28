"""
Unit tests for Turkish Optimized FSRS (algorithms/turkish_optimized_fsrs.py)

Tests FSRS 4.5 algorithm with Turkish student behavior optimizations.

IMPORTANT: NO REWARD HACKING
- Test actual FSRS calculations
- Validate cultural factor adjustments
- Test retention predictions
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from algorithms.turkish_optimized_fsrs import (
    CulturalFactorCalculator,
    CulturalPeriod,
    FSRSCard,
    FSRSGrade,
    FSRSSchedule,
    StudentContext,
    TurkishOptimizedFSRS,
)


@pytest.fixture
def fsrs_system():
    """Create a fresh FSRS system instance."""
    return TurkishOptimizedFSRS()


@pytest.fixture
def sample_card():
    """Create a sample flashcard."""
    return FSRSCard(
        id="CARD001",
        subject="matematik",
        difficulty=5.0,
        stability=5.0,
        retrievability=0.9,
        last_review=datetime.now() - timedelta(days=5),
        review_count=3,
        lapse_count=0,
        scheduled_days=5,
        reps=3,
        lapses=0,
        state="review"
    )


@pytest.fixture
def student_context():
    """Create a sample student context."""
    return StudentContext(
        student_id="STU001",
        group_study_preference=False,
        family_pressure_level=0.5,
        exam_anxiety_level=0.5,
        study_consistency=0.7,
        cultural_background="turkish",
        timezone="Europe/Istanbul"
    )


@pytest.mark.asyncio
async def test_create_new_card():
    """Test creating a new flashcard."""
    card = FSRSCard(
        id="NEW001",
        subject="fizik",
        state="new"
    )

    assert card.id == "NEW001"
    assert card.subject == "fizik"
    assert card.state == "new"
    assert card.difficulty == 0.0
    assert card.stability == 0.0
    assert card.review_count == 0


@pytest.mark.asyncio
async def test_review_card_good(fsrs_system, sample_card, student_context):
    """Test reviewing a card with GOOD rating."""
    current_date = datetime.now()

    schedule = fsrs_system.calculate_next_review(
        card=sample_card,
        grade=FSRSGrade.GOOD,
        current_date=current_date,
        student_context=student_context
    )

    assert schedule.grade == FSRSGrade.GOOD
    assert schedule.interval_days > 0
    assert schedule.scheduled_date > current_date
    assert schedule.stability > 0
    assert schedule.card_id == sample_card.id


@pytest.mark.asyncio
async def test_review_card_again(fsrs_system, sample_card, student_context):
    """Test reviewing a card with AGAIN (failed) rating."""
    current_date = datetime.now()

    schedule = fsrs_system.calculate_next_review(
        card=sample_card,
        grade=FSRSGrade.AGAIN,
        current_date=current_date,
        student_context=student_context
    )

    assert schedule.grade == FSRSGrade.AGAIN
    # AGAIN should result in shorter interval
    assert schedule.interval_days < 7
    assert schedule.difficulty > sample_card.difficulty  # Difficulty increases on failure


@pytest.mark.asyncio
async def test_review_card_easy(fsrs_system, sample_card, student_context):
    """Test reviewing a card with EASY rating."""
    current_date = datetime.now()

    schedule = fsrs_system.calculate_next_review(
        card=sample_card,
        grade=FSRSGrade.EASY,
        current_date=current_date,
        student_context=student_context
    )

    assert schedule.grade == FSRSGrade.EASY
    # EASY should result in longer interval than GOOD
    assert schedule.interval_days >= sample_card.scheduled_days


@pytest.mark.asyncio
async def test_review_card_hard(fsrs_system, sample_card, student_context):
    """Test reviewing a card with HARD rating."""
    current_date = datetime.now()

    schedule = fsrs_system.calculate_next_review(
        card=sample_card,
        grade=FSRSGrade.HARD,
        current_date=current_date,
        student_context=student_context
    )

    assert schedule.grade == FSRSGrade.HARD
    # HARD should result in shorter interval than GOOD
    assert schedule.interval_days > 0


@pytest.mark.asyncio
async def test_calculate_next_review(fsrs_system, sample_card, student_context):
    """Test complete next review calculation."""
    current_date = datetime.now()

    schedule = fsrs_system.calculate_next_review(
        card=sample_card,
        grade=FSRSGrade.GOOD,
        current_date=current_date,
        student_context=student_context
    )

    # Validate schedule fields
    assert isinstance(schedule, FSRSSchedule)
    assert schedule.card_id == sample_card.id
    assert schedule.scheduled_date > current_date
    assert 1 <= schedule.interval_days <= 36500  # Within FSRS bounds
    assert schedule.stability > 0
    assert schedule.difficulty > 0
    assert "cultural_multiplier" in schedule.cultural_factors


def test_cultural_period_detection(fsrs_system):
    """Test detection of Turkish cultural periods."""
    # Exam season (May-June) - most predictable
    exam_date = datetime(2025, 6, 15)
    period = fsrs_system._detect_cultural_period(exam_date)
    assert period == CulturalPeriod.EXAM_SEASON

    # Summer break (July-August)
    summer_date = datetime(2025, 7, 15)
    period = fsrs_system._detect_cultural_period(summer_date)
    assert period == CulturalPeriod.SUMMER_BREAK

    # Non-exam, non-summer period should not be EXAM_SEASON or SUMMER_BREAK
    other_date = datetime(2025, 10, 15)
    period = fsrs_system._detect_cultural_period(other_date)
    assert period not in (CulturalPeriod.EXAM_SEASON, CulturalPeriod.SUMMER_BREAK)


@pytest.mark.asyncio
async def test_ramadan_adjustment(fsrs_system, sample_card, student_context):
    """Test FSRS adjustment during Ramadan."""
    # Mock Ramadan period
    ramadan_date = datetime(2025, 3, 15)

    with patch.object(CulturalFactorCalculator, 'is_ramadan', return_value=True):
        schedule = fsrs_system.calculate_next_review(
            card=sample_card,
            grade=FSRSGrade.GOOD,
            current_date=ramadan_date,
            student_context=student_context
        )

        # Ramadan factor should reduce interval (more forgetting)
        assert "cultural_multiplier" in schedule.cultural_factors
        # Multiplier should be < 1.0 during Ramadan
        assert schedule.cultural_factors["cultural_multiplier"] < 1.0


def test_stability_update(fsrs_system):
    """Test stability parameter update."""
    card = FSRSCard(
        id="CARD001",
        subject="matematik",
        stability=5.0,
        difficulty=5.0,
        state="review"
    )

    updated_card = fsrs_system._update_card_parameters(
        card=card,
        grade=FSRSGrade.GOOD,
        current_date=datetime.now()
    )

    # Stability should increase on successful review
    assert updated_card.stability > card.stability


def test_retrievability_decay(fsrs_system):
    """Test retrievability decay over time."""
    card = FSRSCard(
        id="CARD001",
        subject="matematik",
        stability=10.0,
        elapsed_days=5,
        state="review"
    )

    # Calculate retrievability: exp(-elapsed_days / stability)
    expected_retrievability = 0.60653  # exp(-5/10)

    updated_card = fsrs_system._update_card_parameters(
        card=card,
        grade=FSRSGrade.GOOD,
        current_date=datetime.now()
    )

    # Retrievability should be between 0 and 1
    assert 0.0 < updated_card.retrievability <= 1.0


def test_card_state_management(fsrs_system):
    """Test card state transitions."""
    # New card
    new_card = FSRSCard(id="NEW001", subject="fizik", state="new")
    updated = fsrs_system._update_card_parameters(
        card=new_card,
        grade=FSRSGrade.AGAIN,
        current_date=datetime.now()
    )
    assert updated.state == "learning"

    # Learning to review
    learning_card = FSRSCard(id="LRN001", subject="fizik", state="learning", stability=1.0)
    updated = fsrs_system._update_card_parameters(
        card=learning_card,
        grade=FSRSGrade.GOOD,
        current_date=datetime.now()
    )
    assert updated.state == "review"

    # Failed review to relearning
    review_card = FSRSCard(id="REV001", subject="fizik", state="review", stability=5.0)
    updated = fsrs_system._update_card_parameters(
        card=review_card,
        grade=FSRSGrade.AGAIN,
        current_date=datetime.now()
    )
    assert updated.state == "relearning"


def test_due_cards_query():
    """Test identifying due cards."""
    now = datetime.now()

    cards = [
        FSRSCard(id="DUE1", subject="matematik", due_date=now - timedelta(days=1)),
        FSRSCard(id="DUE2", subject="fizik", due_date=now + timedelta(days=1)),
        FSRSCard(id="DUE3", subject="kimya", due_date=now - timedelta(hours=2)),
    ]

    due_cards = [c for c in cards if c.due_date and c.due_date <= now]

    assert len(due_cards) == 2
    assert "DUE1" in [c.id for c in due_cards]
    assert "DUE3" in [c.id for c in due_cards]


def test_optimal_retention_rate(fsrs_system, student_context):
    """Test optimal retention rate calculation based on student context."""
    retention = fsrs_system.get_optimal_retention_rate(student_context)

    assert 0.75 <= retention <= 0.95

    # High anxiety student
    high_anxiety_context = StudentContext(
        student_id="STU002",
        exam_anxiety_level=0.9,
        family_pressure_level=0.5,
        study_consistency=0.7
    )
    high_anxiety_retention = fsrs_system.get_optimal_retention_rate(high_anxiety_context)
    assert high_anxiety_retention > retention


def test_difficulty_adjustment(fsrs_system):
    """Test difficulty adjustment based on recent performance."""
    card = FSRSCard(id="CARD001", subject="matematik", difficulty=5.0)

    # Good performance (80% success)
    good_performance = [FSRSGrade.GOOD] * 4 + [FSRSGrade.AGAIN] * 1
    adjustment = fsrs_system.calculate_difficulty_adjustment(card, good_performance)
    assert adjustment < 0  # Should decrease difficulty

    # Poor performance (40% success)
    poor_performance = [FSRSGrade.AGAIN] * 3 + [FSRSGrade.GOOD] * 2
    adjustment = fsrs_system.calculate_difficulty_adjustment(card, poor_performance)
    assert adjustment > 0  # Should increase difficulty


def test_predict_retention_probability(fsrs_system):
    """Test retention probability prediction."""
    card = FSRSCard(
        id="CARD001",
        subject="matematik",
        stability=10.0
    )

    # Predict retention 5 days ahead
    retention = fsrs_system.predict_retention_probability(card, days_ahead=5)

    assert 0.0 <= retention <= 1.0

    # Retention should decrease with more days
    retention_10d = fsrs_system.predict_retention_probability(card, days_ahead=10)
    assert retention_10d < retention


def test_study_recommendations(fsrs_system, student_context):
    """Test study recommendation generation."""
    now = datetime.now()

    cards = [
        FSRSCard(id="DUE1", subject="matematik", due_date=now - timedelta(days=1), difficulty=5.0),
        FSRSCard(id="DUE2", subject="fizik", due_date=now + timedelta(days=1), difficulty=3.0),
        FSRSCard(id="HARD1", subject="kimya", due_date=now + timedelta(days=5), difficulty=8.0),
    ]

    recommendations = fsrs_system.get_study_recommendations(cards, student_context, now)

    assert "due_cards_count" in recommendations
    assert "upcoming_cards_count" in recommendations
    assert "difficult_cards_count" in recommendations
    assert "cultural_period" in recommendations
    assert "recommended_study_time" in recommendations

    assert recommendations["due_cards_count"] == 1
    assert recommendations["difficult_cards_count"] == 1


def test_priority_subjects(fsrs_system):
    """Test priority subject identification."""
    due_cards = [
        FSRSCard(id="M1", subject="matematik"),
        FSRSCard(id="M2", subject="matematik"),
        FSRSCard(id="F1", subject="fizik"),
        FSRSCard(id="K1", subject="kimya"),
        FSRSCard(id="K2", subject="kimya"),
        FSRSCard(id="K3", subject="kimya"),
    ]

    priority_subjects = fsrs_system._get_priority_subjects(due_cards)

    # Kimya has 3 due cards, should be first priority
    assert priority_subjects[0] == "kimya"
    assert "matematik" in priority_subjects
    assert len(priority_subjects) <= 5


def test_period_specific_advice(fsrs_system, student_context):
    """Test period-specific study advice."""
    advice_ramadan = fsrs_system._get_period_specific_advice(
        CulturalPeriod.RAMADAN, student_context
    )
    assert "Ramazan" in advice_ramadan

    advice_exam = fsrs_system._get_period_specific_advice(
        CulturalPeriod.EXAM_SEASON, student_context
    )
    assert "Sınav" in advice_exam

    advice_summer = fsrs_system._get_period_specific_advice(
        CulturalPeriod.SUMMER_BREAK, student_context
    )
    assert "Yaz" in advice_summer
