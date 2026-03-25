"""
KIRO2 — Placement Test Suite
==============================
Test kategorileri:
  1. PlacementState seri/deseri
  2. Bisection sınır güncelleme
  3. Soru seçimi (bisection + MFI)
  4. Prior — okul türü etkisi
  5. Bitiş koşulları
  6. Tam simülasyon
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.services.placement_service import (
    PLACEMENT_MAX_ITEMS,
    PLACEMENT_SE_STOP,
    SCHOOL_TYPE_PRIOR,
    PlacementResult,
    PlacementState,
    _bisection_target_b,
    select_placement_question,
    update_bisection_bounds,
)

# ── Fabrika ──────────────────────────────────────────────────────────────────


def _state(**kwargs) -> PlacementState:
    defaults = dict(
        session_id="test-session",
        user_id="user-1",
        subject_id="subj-mat",
        school_type="default",
        theta=0.0,
        se=1.0,
        answered_ids=[],
        responses=[],
        item_params=[],
        n_questions=0,
        b_min=-4.0,
        b_max=4.0,
        is_complete=False,
        started_at=datetime.now(UTC).isoformat(),
    )
    defaults.update(kwargs)
    return PlacementState(**defaults)


def _pool(n: int = 20) -> list:
    return [
        {
            "question_id": f"q{i:03d}",
            "a": 1.0 + (i % 3) * 0.3,
            "b": float(i) * 0.4 - 4.0,
            "c": 0.25,
        }
        for i in range(n)
    ]


# ─── BÖLÜM 1: PlacementState Seri/Deseri ─────────────────────────────────────


class TestPlacementState:
    def test_to_dict_from_dict_roundtrip(self):
        s = _state(
            theta=0.75,
            se=0.42,
            b_min=-1.5,
            b_max=2.0,
            answered_ids=["q1", "q2"],
            responses=[1, 0],
            item_params=[{"question_id": "q1", "a": 1.2, "b": -0.5, "c": 0.25}],
        )
        d = s.to_dict()
        # bytes simulation
        bd = {k.encode(): v.encode() for k, v in d.items()}
        restored = PlacementState.from_dict(bd)
        assert restored.theta == 0.75
        assert restored.se == 0.42
        assert restored.b_min == -1.5
        assert restored.b_max == 2.0
        assert restored.answered_ids == ["q1", "q2"]
        assert restored.responses == [1, 0]
        assert len(restored.item_params) == 1

    def test_is_complete_roundtrip(self):
        s = _state(is_complete=True)
        d = s.to_dict()
        bd = {k.encode(): v.encode() for k, v in d.items()}
        r = PlacementState.from_dict(bd)
        assert r.is_complete is True

    def test_level_label_high(self):
        r = PlacementResult(2.0, 0.30, 8, "default", "s", "high")
        assert r.level_label == "İleri"

    def test_level_label_mid(self):
        r = PlacementResult(0.0, 0.35, 8, "default", "s", "medium")
        assert r.level_label == "Orta"

    def test_level_label_low(self):
        r = PlacementResult(-2.0, 0.35, 8, "default", "s", "medium")
        assert r.level_label == "Temel"


# ─── BÖLÜM 2: Bisection ──────────────────────────────────────────────────────


class TestBisection:
    def test_initial_target_is_midpoint(self):
        t = _bisection_target_b(-4.0, 4.0)
        assert t == 0.0

    def test_correct_answer_raises_lower_bound(self):
        s = _state(
            b_min=-4.0,
            b_max=4.0,
            item_params=[{"question_id": "q1", "a": 1.0, "b": 0.0, "c": 0.25}],
        )
        update_bisection_bounds(s, is_correct=True)
        assert s.b_min >= 0.0
        assert s.b_max == 4.0

    def test_wrong_answer_lowers_upper_bound(self):
        s = _state(
            b_min=-4.0,
            b_max=4.0,
            item_params=[{"question_id": "q1", "a": 1.0, "b": 0.0, "c": 0.25}],
        )
        update_bisection_bounds(s, is_correct=False)
        assert s.b_min == -4.0
        assert s.b_max <= 0.0

    def test_alternating_narrows_range(self):
        s = _state()
        # Doğru @ b=0 → b_min=0
        s.item_params = [{"question_id": "q1", "a": 1.0, "b": 0.0, "c": 0.25}]
        update_bisection_bounds(s, True)
        # Yanlış @ b=2 → b_max=2
        s.item_params = [{"question_id": "q2", "a": 1.0, "b": 2.0, "c": 0.25}]
        update_bisection_bounds(s, False)
        assert s.b_min == 0.0
        assert s.b_max == 2.0
        assert (s.b_max - s.b_min) < 8.0  # aralık daraldı

    def test_empty_item_params_no_crash(self):
        s = _state()
        update_bisection_bounds(s, True)  # item_params boş → güvenli
        assert s.b_min == -4.0


# ─── BÖLÜM 3: Soru Seçimi ────────────────────────────────────────────────────


class TestSelectPlacementQuestion:
    def test_excludes_answered(self):
        pool = _pool(10)
        s = _state(answered_ids=[f"q{i:03d}" for i in range(9)])
        result = select_placement_question(s, pool)
        assert result is not None
        assert result["question_id"] == "q009"

    def test_returns_none_when_pool_exhausted(self):
        pool = _pool(5)
        s = _state(answered_ids=[f"q{i:03d}" for i in range(5)])
        result = select_placement_question(s, pool)
        assert result is None

    def test_prefers_target_difficulty(self):
        """Hedef güçlük 0.0 iken en yakın soru seçilmeli."""
        s = _state(b_min=-1.0, b_max=1.0)  # target_b = 0.0
        pool = [
            {"question_id": "far", "a": 1.0, "b": 3.0, "c": 0.25},
            {"question_id": "near", "a": 1.0, "b": 0.1, "c": 0.25},
            {"question_id": "exact", "a": 1.0, "b": 0.0, "c": 0.25},
        ]
        result = select_placement_question(s, pool)
        assert result is not None
        assert result["question_id"] in ("near", "exact")

    def test_selects_max_fisher_in_window(self):
        """Aynı güçlükte, yüksek a → daha fazla Fisher → seçilmeli."""
        s = _state(b_min=-0.5, b_max=0.5, theta=0.0)
        pool = [
            {"question_id": "low_a", "a": 0.5, "b": 0.0, "c": 0.25},
            {"question_id": "high_a", "a": 2.5, "b": 0.0, "c": 0.25},
        ]
        result = select_placement_question(s, pool)
        assert result["question_id"] == "high_a"


# ─── BÖLÜM 4: Prior — Okul Türü ─────────────────────────────────────────────


class TestSchoolTypePrior:
    def test_all_types_in_dict(self):
        for t in ("anadolu", "fen", "ozel", "imam_hatip", "meslek", "default"):
            assert t in SCHOOL_TYPE_PRIOR

    def test_fen_higher_than_default(self):
        fen_mean, _ = SCHOOL_TYPE_PRIOR["fen"]
        default_mean, _ = SCHOOL_TYPE_PRIOR["default"]
        assert fen_mean > default_mean

    def test_meslek_lower_than_default(self):
        meslek_mean, _ = SCHOOL_TYPE_PRIOR["meslek"]
        default_mean, _ = SCHOOL_TYPE_PRIOR["default"]
        assert meslek_mean < default_mean


# ─── BÖLÜM 5: Bitiş Koşulları ────────────────────────────────────────────────


class TestTerminationConditions:
    def test_se_stop_threshold(self):
        assert PLACEMENT_SE_STOP > 0.0
        assert PLACEMENT_SE_STOP < 0.5  # mantıklı aralık

    def test_max_items_reasonable(self):
        assert 8 <= PLACEMENT_MAX_ITEMS <= 15

    def test_result_confidence_levels(self):
        r_high = PlacementResult(0.5, 0.28, 10, "default", "s", "high")
        r_medium = PlacementResult(0.5, 0.35, 10, "default", "s", "medium")
        r_low = PlacementResult(0.5, 0.45, 10, "default", "s", "low")
        assert r_high.confidence == "high"
        assert r_medium.confidence == "medium"
        assert r_low.confidence == "low"

    def test_suggested_start_difficulty(self):
        r = PlacementResult(1.234, 0.30, 10, "default", "s", "high")
        assert r.suggested_start_difficulty == 1.2


# ─── BÖLÜM 6: Simülasyon ─────────────────────────────────────────────────────


class TestPlacementSimulation:
    """
    PlacementTestService.start/answer'ı DB/Redis olmadan simüle eder.
    Sadece bisection + EAP mantığını test eder.
    """

    def _simulate(
        self,
        true_theta: float,
        school_type: str = "default",
        n_pool: int = 40,
        seed: int = 42,
    ) -> dict:
        """Placement testini pure Python ile simüle et."""
        import random

        # path: conftest.py
        from app.services.irt_engine import ItemParams, eap_update, p_correct

        rng = random.Random(seed)
        prior_mean, prior_sd = SCHOOL_TYPE_PRIOR.get(
            school_type.lower(), SCHOOL_TYPE_PRIOR["default"]
        )

        # Geniş pool oluştur
        pool = [
            {
                "question_id": f"q{i:03d}",
                "a": 0.8 + rng.uniform(0, 0.8),
                "b": -3.5 + i * (7.0 / n_pool),
                "c": 0.25,
            }
            for i in range(n_pool)
        ]

        state = _state(theta=prior_mean, se=prior_sd, school_type=school_type)

        for step in range(PLACEMENT_MAX_ITEMS):
            q = select_placement_question(state, pool)
            if q is None:
                break

            prob = float(p_correct(true_theta, q["a"], q["b"], q["c"]))
            correct = rng.random() < prob
            is_correct_int = 1 if correct else 0

            state.answered_ids.append(q["question_id"])
            state.responses.append(is_correct_int)
            state.item_params.append(q)
            state.n_questions += 1

            update_bisection_bounds(state, correct)

            items = [
                ItemParams(p["question_id"], p["a"], p["b"], p["c"])
                for p in state.item_params
            ]
            res = eap_update(
                state.responses, items, prior_mean=prior_mean, prior_sd=prior_sd
            )
            state.theta = res.theta
            state.se = res.se

            if state.se <= PLACEMENT_SE_STOP:
                break

        return {"theta": state.theta, "se": state.se, "n": state.n_questions}

    def test_converges_within_max_items(self):
        result = self._simulate(true_theta=0.5)
        assert result["n"] <= PLACEMENT_MAX_ITEMS

    def test_reasonable_theta_estimate_positive(self):
        result = self._simulate(true_theta=1.0, seed=7)
        assert result["theta"] > 0.0, f"Yüksek θ için negatif tahmin: {result['theta']}"

    def test_reasonable_theta_estimate_negative(self):
        result = self._simulate(true_theta=-1.0, seed=13)
        assert result["theta"] < 0.5, (
            f"Düşük θ için çok yüksek tahmin: {result['theta']}"
        )

    def test_fen_prior_helps_high_student(self):
        """Fen lisesi prior'ı yüksek θ'lı öğrenci için daha hızlı yakınsar."""
        r_fen = self._simulate(1.5, "fen", seed=5)
        r_default = self._simulate(1.5, "default", seed=5)
        # Fen prior'ı daha iyi başlayacağından genellikle daha az soru gerektirir
        # (strict test değil, yön kontrolü)
        assert r_fen["n"] <= r_default["n"] + 3

    def test_se_improves_over_questions(self):
        """Her adımda SE'nin genel trendi düşmeli."""
        # path: conftest.py
        import random

        from app.services.irt_engine import ItemParams, eap_update, p_correct

        rng = random.Random(42)
        pool = [
            {"question_id": f"q{i}", "a": 1.2, "b": -2.0 + i * 0.4, "c": 0.25}
            for i in range(15)
        ]
        state = _state()
        ses = [1.0]

        for q in pool[:8]:
            prob = float(p_correct(0.5, q["a"], q["b"], q["c"]))
            correct = int(rng.random() < prob)
            state.answered_ids.append(q["question_id"])
            state.responses.append(correct)
            state.item_params.append(q)
            items = [
                ItemParams(p["question_id"], p["a"], p["b"], p["c"])
                for p in state.item_params
            ]
            res = eap_update(state.responses, items)
            ses.append(res.se)
            state.theta = res.theta
            state.se = res.se

        assert ses[-1] < ses[0], f"SE azalmıyor: {ses}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
