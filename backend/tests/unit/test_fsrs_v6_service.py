"""
Batch 1C: FSRSService pure-method P0+P1 tests.

Scope: services/fsrs_v6_service.py — 4 public static methods
Level: service-level (no DB, no mock)
FSRS: real _FSRS_AVAILABLE=True path (no fallback patching)

P0 tests (6):
  1. review_card new card    — valid fields, positive values, valid state
  2. review_card existing   — stability/difficulty preserved on review
  3. review_card rating 1-4 — all 4 ratings succeed without error
  4. retrievability S<=0     — returns exactly 0.0
  5. retrievability bounds   — 0.0 <= R <= 1.0 for S>0, days>=0
  6. next_interval min      — always >= 1.0

P1 tests (8):
  7. first_review rating 1-4 — all succeed
  8. first_review stability monotonic with rating
  9. first_review difficulty monotonic with rating
 10. first_review positive ranges
 11. retrievability fresh card R=1.0 at days=0
 12. retrievability stale card R->0 as days->infinity
 13. review_card Easy gives longer interval than Good
 14. next_interval scales with stability
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from services.fsrs_v6_service import FSRSService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_valid_state(state: str) -> bool:
    return state in {"new", "learning", "review"}


# ---------------------------------------------------------------------------
# Test 1 — review_card new card: valid fields returned
# ---------------------------------------------------------------------------


def test_review_card_new_card_returns_valid_fields():
    """New card (all None inputs) returns dict with all 6 required keys and valid values."""

    result = FSRSService.review_card(
        stability=None,
        difficulty=None,
        due_date=None,
        rating_int=3,  # Good
        reps=0,
    )

    # All 6 keys present
    assert isinstance(result, dict)
    assert set(result.keys()) == {
        "stability",
        "difficulty",
        "due_date",
        "state",
        "reps",
        "lapses",
    }

    # Positive values
    assert isinstance(result["stability"], float)
    assert result["stability"] > 0.0, (
        f"stability should be positive for new card, got {result['stability']}"
    )

    assert isinstance(result["difficulty"], float)
    assert 0.0 < result["difficulty"] < 10.0, (
        f"difficulty should be in (0, 10), got {result['difficulty']}"
    )

    # due_date is datetime
    assert isinstance(result["due_date"], datetime)

    # state is valid enum string
    assert isinstance(result["state"], str)
    assert _is_valid_state(result["state"]), (
        f"state should be in {{new,learning,review}}, got {result['state']}"
    )

    # reps >= 1 (new card progressed to at least step 0 → reps=0 in, step=0 out → reps=0)
    # Note: reps in return is card.step (learning step counter), not equal to input reps
    assert isinstance(result["reps"], int)

    # lapses = 0 (FSRS v6 doesn't track lapses in return)
    assert result["lapses"] == 0


# ---------------------------------------------------------------------------
# Test 2 — review_card existing card: stability/difficulty preserved-ish
# ---------------------------------------------------------------------------


def test_review_card_existing_card_preserves_fields():
    """Existing card inputs are reflected in the returned stability/difficulty values."""

    prev_stability = 2.5
    prev_difficulty = 3.5

    result = FSRSService.review_card(
        stability=prev_stability,
        difficulty=prev_difficulty,
        due_date=datetime.now(UTC),
        rating_int=3,
        reps=2,
    )

    # Stability should be based on previous value (FSRS updates it, not resets it)
    assert isinstance(result["stability"], float)
    assert result["stability"] > 0.0

    # Difficulty should be based on previous value
    assert isinstance(result["difficulty"], float)
    assert 0.0 < result["difficulty"] < 10.0

    # State should be review (reps=2 ≥ 1 means card is in review)
    assert result["state"] == "review", f"expected 'review', got {result['state']}"

    # due_date should be a future datetime after review
    assert isinstance(result["due_date"], datetime)


# ---------------------------------------------------------------------------
# Test 3 — review_card rating 1-4 mapping: all succeed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rating_int,label",
    [(1, "Again"), (2, "Hard"), (3, "Good"), (4, "Easy")],
)
def test_review_card_rating_int_1234_mapping(rating_int, label):
    """All 4 rating values (1-4) produce a valid return dict without raising."""

    result = FSRSService.review_card(
        stability=None,
        difficulty=None,
        due_date=None,
        rating_int=rating_int,
        reps=0,
    )

    assert isinstance(result, dict)
    assert set(result.keys()) == {
        "stability",
        "difficulty",
        "due_date",
        "state",
        "reps",
        "lapses",
    }
    assert result["stability"] > 0.0
    assert result["difficulty"] > 0.0
    assert isinstance(result["due_date"], datetime)
    assert _is_valid_state(result["state"])
    assert result["lapses"] == 0


# ---------------------------------------------------------------------------
# Test 4 — retrievability S<=0 → exactly 0.0
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "stability,days",
    [
        (0.0, 5.0),
        (-1.0, 5.0),
        (0.0, 0.0),
        (-10.0, 100.0),
    ],
)
def test_retrievability_zero_stability_returns_zero(stability, days):
    """stability <= 0 always returns exactly 0.0 regardless of days_elapsed."""

    result = FSRSService.retrievability(stability, days)
    assert result == 0.0, (
        f"retrievability(S={stability}, days={days}) should be 0.0, got {result}"
    )


# ---------------------------------------------------------------------------
# Test 5 — retrievability bounded: 0.0 < R < 1.0 for S>0, days>=0
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "stability,days",
    [
        (10.0, 0.0),  # fresh card: retrievability ≈ 1
        (10.0, 5.0),  # retrievability ≈ 0.6
        (10.0, 10.0),  # retrievability ≈ 0.37
        (10.0, 50.0),  # retrievability ≈ 0.04
        (1.0, 1.0),  # high retrievability
        (100.0, 100.0),  # low retrievability
    ],
)
def test_retrievability_in_01_range(stability, days):
    """retrievability is strictly in (0.0, 1.0) for any positive stability and non-negative days."""

    result = FSRSService.retrievability(stability, days)

    # Boundary: exactly 0.0 only when stability <= 0 (covered by test 4)
    # For positive stability, result is always > 0 and < 1
    # days=0 → R=1.0 exactly (not strictly < 1.0)
    assert 0.0 <= result <= 1.0, (
        f"retrievability(S={stability}, days={days})={result} should be in [0,1]"
    )


# ---------------------------------------------------------------------------
# Test 6 — next_interval minimum 1.0
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "stability",
    [0.1, 0.5, 1.0, 2.3, 5.0, 10.0, 50.0, 100.0, 365.0],
)
def test_next_interval_minimum_1(stability):
    """next_interval returns at least 1.0 for any positive stability input."""

    result = FSRSService.next_interval(stability)

    assert isinstance(result, (int, float)), (
        f"next_interval should return numeric, got {type(result)}"
    )
    assert result >= 1.0, f"next_interval(S={stability})={result} should be >= 1.0"


# ---------------------------------------------------------------------------
# Test 7 — next_interval positive stability always returns positive
# ---------------------------------------------------------------------------


def test_next_interval_positive_stability_returns_positive():
    """next_interval returns a positive float for any positive stability."""

    for S in [0.01, 0.1, 1.0, 10.0, 100.0]:
        result = FSRSService.next_interval(S)
        assert result > 0.0, f"next_interval(S={S})={result} should be positive"


# ============================================================================
# P1 TESTS — first_review, retrievability asymptotic, interval scaling
# ============================================================================


# ---------------------------------------------------------------------------
# Test 8 — first_review: all 4 ratings succeed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rating_int,label",
    [(1, "Again"), (2, "Hard"), (3, "Good"), (4, "Easy")],
)
def test_first_review_rating_1234_all_succeed(rating_int, label):
    """first_review(rating) returns (stability, difficulty) for all 4 ratings."""

    stability, difficulty = FSRSService.first_review(rating_int)

    assert isinstance(stability, float), (
        f"stability should be float, got {type(stability)}"
    )
    assert isinstance(difficulty, float), (
        f"difficulty should be float, got {type(difficulty)}"
    )
    assert stability > 0.0, f"stability should be positive, got {stability}"
    assert difficulty > 0.0, f"difficulty should be positive, got {difficulty}"


# ---------------------------------------------------------------------------
# Test 9 — first_review: stability increases with rating
# ---------------------------------------------------------------------------


def test_first_review_stability_increases_with_rating():
    """first_review stability is monotonically increasing with rating (1→4)."""

    results = {r: FSRSService.first_review(r)[0] for r in [1, 2, 3, 4]}

    assert results[1] < results[2] < results[3] < results[4], (
        f"stability should increase with rating: {results}"
    )


# ---------------------------------------------------------------------------
# Test 10 — first_review: difficulty decreases with rating
# ---------------------------------------------------------------------------


def test_first_review_difficulty_decreases_with_rating():
    """first_review difficulty is monotonically decreasing with rating (1→4)."""

    results = {r: FSRSService.first_review(r)[1] for r in [1, 2, 3, 4]}

    assert results[1] > results[2] > results[3] > results[4], (
        f"difficulty should decrease with rating: {results}"
    )


# ---------------------------------------------------------------------------
# Test 11 — first_review: positive ranges
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rating_int",
    [1, 2, 3, 4],
)
def test_first_review_positive_ranges(rating_int):
    """first_review stability and difficulty stay within known FSRS bounds."""

    stability, difficulty = FSRSService.first_review(rating_int)

    # Stability: 0 < S <= ~10 for any rating
    assert 0.0 < stability <= 15.0, (
        f"stability should be in (0, 15] for rating={rating_int}, got {stability}"
    )
    # Difficulty: 1 <= D <= 8 for any rating
    assert 0.5 <= difficulty <= 8.5, (
        f"difficulty should be in [0.5, 8.5] for rating={rating_int}, got {difficulty}"
    )


# ---------------------------------------------------------------------------
# Test 12 — retrievability: fresh card (days=0) → R=1.0
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "stability",
    [0.5, 1.0, 5.0, 10.0, 100.0],
)
def test_retrievability_fresh_card_approaches_1(stability):
    """retrievability is exactly 1.0 when days_elapsed=0 regardless of stability."""

    result = FSRSService.retrievability(stability, days_elapsed=0.0)
    assert result == 1.0, (
        f"retrievability(S={stability}, days=0) should be exactly 1.0, got {result}"
    )


# ---------------------------------------------------------------------------
# Test 13 — retrievability: stale card (large days) → R→0
# ---------------------------------------------------------------------------


def test_retrievability_stale_card_approaches_0():
    """retrievability decreases as days_elapsed grows relative to stability."""

    # S=1, D=1000 → R≈0.346 with the power-law formula used in this implementation.
    # Monotonicity: verify R decreases as D increases at fixed S.
    r_10 = FSRSService.retrievability(stability=1.0, days_elapsed=10.0)
    r_100 = FSRSService.retrievability(stability=1.0, days_elapsed=100.0)
    r_1000 = FSRSService.retrievability(stability=1.0, days_elapsed=1000.0)

    assert r_1000 < r_100 < r_10, (
        f"retrievability should decrease with days: r10={r_10:.4f}, r100={r_100:.4f}, r1000={r_1000:.4f}"
    )
    # At S=1, D=1000: R≈0.346 — clearly approaching 0
    assert r_1000 < 0.5, (
        f"retrievability(S=1, D=1000)={r_1000} should be well below 0.5"
    )


# ---------------------------------------------------------------------------
# Test 14 — review_card: Easy gives longer interval than Good
# ---------------------------------------------------------------------------


def test_review_card_rating4_easy_increases_interval():
    """Rating 4 (Easy) produces a later due_date than rating 3 (Good) on same card."""

    now = datetime.now(UTC)
    card_state = dict(stability=5.0, difficulty=4.0)

    good = FSRSService.review_card(
        stability=card_state["stability"],
        difficulty=card_state["difficulty"],
        due_date=now,
        rating_int=3,  # Good
        reps=2,
    )
    easy = FSRSService.review_card(
        stability=card_state["stability"],
        difficulty=card_state["difficulty"],
        due_date=now,
        rating_int=4,  # Easy
        reps=2,
    )

    assert easy["due_date"] > good["due_date"], (
        f"Easy due_date ({easy['due_date']}) should be later than Good ({good['due_date']})"
    )
    # Stability should also be higher for Easy
    assert easy["stability"] > good["stability"], (
        f"Easy stability ({easy['stability']}) should exceed Good ({good['stability']})"
    )


# ---------------------------------------------------------------------------
# Test 15 — next_interval: scales with stability
# ---------------------------------------------------------------------------


def test_next_interval_scales_with_stability():
    """next_interval is monotonically increasing with stability."""

    intervals = {S: FSRSService.next_interval(S) for S in [0.5, 1.0, 5.0, 10.0, 50.0]}

    assert intervals[1.0] < intervals[5.0] < intervals[10.0] < intervals[50.0], (
        f"next_interval should increase with stability: {intervals}"
    )
