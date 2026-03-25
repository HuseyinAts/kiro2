"""
KIRO2 — FSRS Test Suite
========================
58 CAT+IRT test geçti. Şimdi FSRS:
  1. Temel formüller (R, S_0, D)
  2. Durum makinesi geçişleri
  3. Parametre güvenceleri
  4. Puan-yanıt dönüşümü
  5. Birleşik CAT+FSRS öncelik skoru
  6. Tekrarlı oturum simülasyonu
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.services.fsrs_engine import (
    DURUM_TEKRAR,
    DURUM_YENİ,
    DURUM_YENİDEN,
    DURUM_ÖĞRENME,
    PUAN_İYİ,
    PUAN_KOLAY,
    PUAN_TEKRAR,
    PUAN_ZOR,
    FSRSState,
    _initial_difficulty,
    _initial_stability,
    _interval_from_stability,
    _retrievability,
    answer_to_fsrs_rating,
    combined_priority_score,
    fsrs_update,
)


def _state(
    stability=4.0, difficulty=5.0, state=DURUM_TEKRAR, days_ago=4, reps=5, lapses=0
) -> FSRSState:
    """Test için FSRSState fabrikası."""
    now = datetime.now(UTC)
    return FSRSState(
        user_id="user-test",
        question_id="q-test",
        stability=stability,
        difficulty=difficulty,
        state=state,
        reps=reps,
        lapses=lapses,
        last_review=now - timedelta(days=days_ago),
        due_date=now - timedelta(days=max(0, days_ago - stability)),
    )


# ─── BÖLÜM 1: Temel Formüller ─────────────────────────────────────────────────


class TestRetrievability:
    def test_zero_days_elapsed(self):
        """t=0 → R=1 (yeni görüldü)."""
        assert abs(_retrievability(0.0, 10.0) - 1.0) < 1e-6

    def test_decreases_over_time(self):
        """Zaman geçtikçe R düşmeli."""
        s = 10.0
        r_early = _retrievability(1.0, s)
        r_mid = _retrievability(5.0, s)
        r_late = _retrievability(15.0, s)
        assert r_early > r_mid > r_late

    def test_high_stability_slower_decay(self):
        """Yüksek S → daha yavaş bozunma."""
        t = 10.0
        r_low = _retrievability(t, s=2.0)
        r_high = _retrievability(t, s=20.0)
        assert r_high > r_low

    def test_approx_90_at_interval(self):
        """S gün sonra R ≈ 0.90 olmalı (istenen hedef)."""
        s = 10.0
        interval = _interval_from_stability(s, desired_r=0.90)
        r_at_interval = _retrievability(float(interval), s)
        assert abs(r_at_interval - 0.90) < 0.05


class TestInitialParams:
    def test_easy_first_high_stability(self):
        """İlk görüşte KOLAY → yüksek S."""
        s_hard = _initial_stability(PUAN_TEKRAR)
        s_easy = _initial_stability(PUAN_KOLAY)
        assert s_easy > s_hard

    def test_easy_first_low_difficulty(self):
        """İlk görüşte KOLAY → düşük D."""
        d_hard = _initial_difficulty(PUAN_TEKRAR)
        d_easy = _initial_difficulty(PUAN_KOLAY)
        assert d_easy < d_hard

    def test_difficulty_in_bounds(self):
        for puan in (1, 2, 3, 4):
            d = _initial_difficulty(puan)
            assert 1.0 <= d <= 10.0, f"D sınır dışı puan={puan}: D={d}"


class TestIntervalCalculation:
    def test_higher_stability_longer_interval(self):
        """Yüksek S → uzun aralık."""
        i_low = _interval_from_stability(2.0)
        i_high = _interval_from_stability(20.0)
        assert i_high > i_low

    def test_minimum_interval_one_day(self):
        """Minimum aralık 1 gün."""
        assert _interval_from_stability(0.001) >= 1

    def test_target_r90_approximately(self):
        """desired_r=0.90 için üretilen aralıkta R ≈ 0.90."""
        for s in (1.0, 5.0, 14.0, 30.0):
            interval = _interval_from_stability(s, 0.90)
            r = _retrievability(float(interval), s)
            assert abs(r - 0.90) < 0.08, f"S={s}: R={r:.3f} @ {interval} gün"


# ─── BÖLÜM 2: Durum Makinesi ──────────────────────────────────────────────────


class TestStateMachine:
    """fsrs_update() durum geçişleri."""

    # ── YENİ ──────────────────────────────────────────────────────

    def test_new_good_goes_to_review(self):
        s = FSRSState("u", "q", state=DURUM_YENİ)
        r = fsrs_update(s, PUAN_İYİ)
        assert r.new_state.state == DURUM_TEKRAR

    def test_new_again_stays_learning(self):
        s = FSRSState("u", "q", state=DURUM_YENİ)
        r = fsrs_update(s, PUAN_TEKRAR)
        assert r.new_state.state == DURUM_ÖĞRENME

    def test_new_hard_goes_learning(self):
        s = FSRSState("u", "q", state=DURUM_YENİ)
        r = fsrs_update(s, PUAN_ZOR)
        assert r.new_state.state == DURUM_ÖĞRENME

    def test_new_easy_goes_review(self):
        s = FSRSState("u", "q", state=DURUM_YENİ)
        r = fsrs_update(s, PUAN_KOLAY)
        assert r.new_state.state == DURUM_TEKRAR

    # ── ÖĞRENME ───────────────────────────────────────────────────

    def test_learning_good_graduates(self):
        s = FSRSState("u", "q", state=DURUM_ÖĞRENME)
        r = fsrs_update(s, PUAN_İYİ)
        assert r.new_state.state == DURUM_TEKRAR

    def test_learning_again_stays(self):
        s = FSRSState("u", "q", state=DURUM_ÖĞRENME)
        r = fsrs_update(s, PUAN_TEKRAR)
        assert r.new_state.state == DURUM_ÖĞRENME

    # ── TEKRAR ────────────────────────────────────────────────────

    def test_review_good_stays_review(self):
        s = _state()
        r = fsrs_update(s, PUAN_İYİ)
        assert r.new_state.state == DURUM_TEKRAR

    def test_review_again_lapses(self):
        s = _state()
        r = fsrs_update(s, PUAN_TEKRAR)
        assert r.new_state.state == DURUM_YENİDEN
        assert r.new_state.lapses == s.lapses + 1

    def test_review_easy_longer_interval(self):
        s = _state()
        r_good = fsrs_update(s, PUAN_İYİ)
        r_easy = fsrs_update(s, PUAN_KOLAY)
        assert r_easy.interval_days >= r_good.interval_days

    def test_review_hard_shorter_interval(self):
        s = _state()
        r_hard = fsrs_update(s, PUAN_ZOR)
        r_good = fsrs_update(s, PUAN_İYİ)
        assert r_hard.interval_days <= r_good.interval_days

    # ── YENİDEN ÖĞRENME ───────────────────────────────────────────

    def test_relearning_good_returns_to_review(self):
        s = _state(state=DURUM_YENİDEN)
        r = fsrs_update(s, PUAN_İYİ)
        assert r.new_state.state == DURUM_TEKRAR

    def test_relearning_again_stays(self):
        s = _state(state=DURUM_YENİDEN)
        r = fsrs_update(s, PUAN_TEKRAR)
        assert r.new_state.state == DURUM_YENİDEN

    # ── Reps artımı ───────────────────────────────────────────────

    def test_reps_increments(self):
        s = _state(reps=3)
        r = fsrs_update(s, PUAN_İYİ)
        assert r.new_state.reps == 4


# ─── BÖLÜM 3: Parametreler ────────────────────────────────────────────────────


class TestParameterBounds:
    def test_stability_always_positive(self):
        for puan in (1, 2, 3, 4):
            for state_type in (DURUM_YENİ, DURUM_ÖĞRENME, DURUM_TEKRAR, DURUM_YENİDEN):
                s = _state(state=state_type)
                r = fsrs_update(s, puan)
                assert r.new_state.stability > 0, (
                    f"S≤0: puan={puan}, state={state_type}"
                )

    def test_difficulty_in_bounds(self):
        for puan in (1, 2, 3, 4):
            s = _state()
            r = fsrs_update(s, puan)
            assert 1.0 <= r.new_state.difficulty <= 10.0, (
                f"D sınır dışı: {r.new_state.difficulty}"
            )

    def test_interval_minimum_one(self):
        for puan in (1, 2, 3, 4):
            s = _state()
            r = fsrs_update(s, puan)
            assert r.interval_days >= 1


class TestDifficulty:
    def test_good_doesnt_change_much(self):
        """PUAN_İYİ (=3) difficulty'yi çok değiştirmemeli."""
        s = _state(difficulty=5.0)
        r = fsrs_update(s, PUAN_İYİ)
        assert abs(r.new_state.difficulty - 5.0) < 1.5

    def test_easy_decreases_difficulty(self):
        s = _state(difficulty=6.0)
        r = fsrs_update(s, PUAN_KOLAY)
        assert r.new_state.difficulty <= 6.0

    def test_hard_increases_difficulty(self):
        s = _state(difficulty=4.0)
        r = fsrs_update(s, PUAN_ZOR)
        assert r.new_state.difficulty >= 4.0


# ─── BÖLÜM 4: Puan Dönüşümü ──────────────────────────────────────────────────


class TestAnswerToRating:
    def test_wrong_always_again(self):
        assert answer_to_fsrs_rating(False) == PUAN_TEKRAR
        assert answer_to_fsrs_rating(False, response_ms=1000) == PUAN_TEKRAR

    def test_correct_default_good(self):
        assert answer_to_fsrs_rating(True) == PUAN_İYİ

    def test_slow_correct_hard(self):
        """30sn'den uzun → ZOR."""
        assert answer_to_fsrs_rating(True, response_ms=35_000) == PUAN_ZOR

    def test_fast_easy_item_easy(self):
        """5sn'den kısa + kolay soru → KOLAY."""
        assert answer_to_fsrs_rating(True, response_ms=3_000, item_b=-1.5) == PUAN_KOLAY

    def test_fast_hard_item_still_good(self):
        """Zor soruyu hızlı doğru yaparsa → İYİ (kolay değil)."""
        assert answer_to_fsrs_rating(True, response_ms=3_000, item_b=1.5) == PUAN_İYİ


# ─── BÖLÜM 5: Urgency ve Birleşik Skor ───────────────────────────────────────


class TestUrgencyScore:
    def test_not_due_zero_urgency(self):
        s = FSRSState("u", "q", due_date=datetime.now(UTC) + timedelta(days=5))
        assert s.urgency_score == 0.0

    def test_overdue_positive_urgency(self):
        s = FSRSState(
            "u",
            "q",
            stability=5.0,
            due_date=datetime.now(UTC) - timedelta(days=3),
            last_review=datetime.now(UTC) - timedelta(days=3),
        )
        assert s.urgency_score > 0.0

    def test_more_overdue_higher_urgency(self):
        now = datetime.now(UTC)
        s1 = FSRSState(
            "u",
            "q1",
            stability=5.0,
            due_date=now - timedelta(days=1),
            last_review=now - timedelta(days=1),
        )
        s2 = FSRSState(
            "u",
            "q2",
            stability=5.0,
            due_date=now - timedelta(days=5),
            last_review=now - timedelta(days=5),
        )
        assert s2.urgency_score > s1.urgency_score

    def test_urgency_capped_at_3(self):
        """Urgency 3.0'dan büyük olmamalı."""
        s = FSRSState(
            "u",
            "q",
            stability=0.1,
            due_date=datetime.now(UTC) - timedelta(days=100),
            last_review=datetime.now(UTC) - timedelta(days=100),
        )
        assert s.urgency_score <= 3.0


class TestCombinedScore:
    def test_overdue_card_higher_than_new(self):
        now = datetime.now(UTC)
        overdue = FSRSState(
            "u",
            "q1",
            stability=5.0,
            due_date=now - timedelta(days=3),
            last_review=now - timedelta(days=3),
        )
        fresh = FSRSState("u", "q2", stability=10.0, due_date=now + timedelta(days=7))
        score_overdue = combined_priority_score(overdue, irt_info=1.0)
        score_fresh = combined_priority_score(fresh, irt_info=1.0)
        assert score_overdue > score_fresh

    def test_weights_sum_effect(self):
        now = datetime.now(UTC)
        s = FSRSState(
            "u",
            "q",
            stability=5.0,
            due_date=now - timedelta(days=2),
            last_review=now - timedelta(days=2),
        )
        score = combined_priority_score(s, irt_info=1.5)
        assert score > 0.0


# ─── BÖLÜM 6: Simülasyon ─────────────────────────────────────────────────────


class TestSimulation:
    """Gerçekçi tekrar seansları simülasyonu."""

    def test_stability_grows_with_correct_reviews(self):
        """Ardışık doğru tekrarlar → stabilite artmalı."""
        s = FSRSState("u", "q", state=DURUM_YENİ)
        for _ in range(8):
            res = fsrs_update(s, PUAN_İYİ)
            s = res.new_state
            s.last_review = datetime.now(UTC) - timedelta(days=res.interval_days + 1)
            s.due_date = datetime.now(UTC)

        assert s.stability > 10.0, (
            f"8 doğru tekrar sonrası S={s.stability:.2f} — yeterince büyümeyen"
        )

    def test_lapse_resets_stability(self):
        """Unutma → stabilite düşmeli."""
        s = _state(stability=30.0)
        res = fsrs_update(s, PUAN_TEKRAR)
        assert res.new_state.stability < s.stability

    def test_interval_progression(self):
        """Aralıklar her seferinde artmalı."""
        s = FSRSState("u", "q", state=DURUM_YENİ)
        intervals = []
        for _ in range(5):
            res = fsrs_update(s, PUAN_İYİ)
            intervals.append(res.interval_days)
            s = res.new_state
            s.last_review = datetime.now(UTC) - timedelta(days=res.interval_days + 1)
            s.due_date = datetime.now(UTC)

        # En azından genel eğilim artış yönünde olmalı
        assert intervals[-1] > intervals[0], f"Aralık artmıyor: {intervals}"

    def test_is_due_detection(self):
        now = datetime.now(UTC)
        due = FSRSState("u", "q", due_date=now - timedelta(hours=1))
        notdue = FSRSState("u", "q", due_date=now + timedelta(days=5))
        assert due.is_due()
        assert not notdue.is_due()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
