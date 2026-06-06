"""
Batch 1A: Pure-math algorithm core tests for IRT 3PL + BKT update.
Scope: services/irt_service_3pl.py, services/bkt_service.BKTService.update()
Out of scope: record_answer, FSRS, ZPDManager, select_next_question, validate_params, get_params

All tests are pure function tests — no DB, no mock, no fixture.
Uses parametrized inputs verified against actual runtime behavior.
"""

import pytest

# =============================================================================
# 1. IRTService3PL.icc() — 7 tests
# =============================================================================


class TestICCClip:
    """ICC clip branch coverage — verified with Python math."""

    @pytest.mark.parametrize(
        "theta,a,b,c,expected_p_is_1",
        [
            # Positive clip: theta=701 → exponent=-701 → clipped to -700 → exp(-700)≈0 → p≈1.0
            (701.0, 1.0, 0.0, 0.2, True),
            # Positive clip: theta=1000 → exponent=-1000 → clipped to -700
            (1000.0, 1.0, 0.0, 0.2, True),
            # No clip: theta=0 → exponent=0 → exp(0)=1 → p=0.2 + 0.8/2 = 0.6
            (0.0, 1.0, 0.0, 0.2, False),
        ],
    )
    def test_icc_positive_clip(self, theta, a, b, c, expected_p_is_1):
        from services.irt_service_3pl import IRTService3PL

        p = IRTService3PL.icc(theta, a, b, c)
        # Clip branch: exponent clipped to ±700 prevents overflow
        # After clip: exp(-700) ≈ 0 → p ≈ 1.0 for positive direction
        if expected_p_is_1:
            assert abs(p - 1.0) < 0.01, f"theta={theta} should approach 1.0, got {p}"
        else:
            assert 0.0 < p < 1.0, f"theta={theta} should be in (0,1), got {p}"

    @pytest.mark.parametrize(
        "theta,a,b,c,expected_p_is_c",
        [
            # Negative clip: theta=-701 → exponent=701 → clipped to 700 → exp(700)→∞ → p≈c
            (-701.0, 1.0, 0.0, 0.2, True),
            # Negative clip: theta=-1000 → exponent=1000 → clipped to 700
            (-1000.0, 1.0, 0.0, 0.2, True),
            # No clip: theta=-1 → exponent=1 → exp(1)≈2.718 → p=0.2 + 0.8/3.718≈0.415
            (-1.0, 1.0, 0.0, 0.2, False),
        ],
    )
    def test_icc_negative_clip(self, theta, a, b, c, expected_p_is_c):
        from services.irt_service_3pl import IRTService3PL

        p = IRTService3PL.icc(theta, a, b, c)
        # Negative clip: exponent clipped to +700 prevents overflow
        # After clip: exp(700)→∞ → p≈c (guessing asymptote)
        if expected_p_is_c:
            assert abs(p - c) < 0.01, f"theta={theta} should approach c={c}, got {p}"
        else:
            assert 0.0 < p < 1.0, f"theta={theta} should be in (0,1), got {p}"

    def test_icc_output_never_exceeds_1(self):
        from services.irt_service_3pl import IRTService3PL

        for theta in [-1000, -701, -100, -10, 0, 10, 100, 701, 1000]:
            for a in [0.2, 1.0, 2.5]:
                for b in [-3.0, 0.0, 3.0]:
                    for c in [0.0, 0.2, 0.35]:
                        p = IRTService3PL.icc(theta, a, b, c)
                        assert p <= 1.0, f"icc({theta},{a},{b},{c})={p} > 1.0"

    def test_icc_output_never_below_c(self):
        from services.irt_service_3pl import IRTService3PL

        for theta in [-1000, -701, -100, -10, 0, 10, 100, 701, 1000]:
            for a in [0.2, 1.0, 2.5]:
                for b in [-3.0, 0.0, 3.0]:
                    for c in [0.0, 0.2, 0.35]:
                        p = IRTService3PL.icc(theta, a, b, c)
                        assert p >= c, f"icc({theta},{a},{b},{c})={p} < c={c}"

    @pytest.mark.parametrize(
        "theta,a,b,c",
        [
            # theta << b: probability approaches c (guessing)
            (-50.0, 1.0, 0.0, 0.2),
            (-100.0, 1.0, 0.0, 0.2),
            (-50.0, 1.0, 0.0, 0.35),
        ],
    )
    def test_icc_at_theta_far_left_approaches_c(self, theta, a, b, c):
        from services.irt_service_3pl import IRTService3PL

        p = IRTService3PL.icc(theta, a, b, c)
        assert abs(p - c) < 0.001, f"theta={theta} should approach c={c}, got {p}"

    @pytest.mark.parametrize(
        "c,expected_midpoint",
        [
            (0.0, 0.5),
            (0.2, 0.6),
            (0.35, 0.675),
        ],
    )
    def test_icc_at_theta_equals_b_is_midpoint(self, c, expected_midpoint):
        from services.irt_service_3pl import IRTService3PL

        # At theta=b: exponent=0 → exp(0)=1 → p = c + (1-c)/2 = (1+c)/2
        p = IRTService3PL.icc(theta=0.0, a=1.0, b=0.0, c=c)
        assert abs(p - expected_midpoint) < 0.001, (
            f"at theta=b, p should be (1+c)/2={expected_midpoint}, got {p}"
        )


# =============================================================================
# 2. IRTService3PL.information() — 3 tests
# =============================================================================


class TestInformation:
    """Information zero-boundary branches — verified with Python math."""

    @pytest.mark.parametrize(
        "theta,a,b,c",
        [
            # c >= P branch: at theta=-50, P≈c with a=1,b=0,c=0.2
            (-50.0, 1.0, 0.0, 0.2),
            (-100.0, 1.0, 0.0, 0.25),
            (-100.0, 1.0, 0.0, 0.35),
        ],
    )
    def test_information_zero_when_c_equals_p(self, theta, a, b, c):
        from services.irt_service_3pl import IRTService3PL

        info = IRTService3PL.information(theta, a, b, c)
        assert info == 0.0, f"information at c>=P boundary should be 0.0, got {info}"

    @pytest.mark.parametrize(
        "theta,a,b,c",
        [
            # Q <= 1e-10 branch: at theta=30, P≈1.0 with a=1,b=0,c=0.2
            # Verified: theta=30 → Q=7.48e-14 < 1e-10
            (30.0, 1.0, 0.0, 0.2),
            (50.0, 1.0, 0.0, 0.2),
            (100.0, 1.0, 0.0, 0.25),
        ],
    )
    def test_information_zero_when_q_le_1e10(self, theta, a, b, c):
        from services.irt_service_3pl import IRTService3PL

        info = IRTService3PL.information(theta, a, b, c)
        assert info == 0.0, (
            f"information at Q<=1e-10 boundary should be 0.0, got {info}"
        )

    @pytest.mark.parametrize(
        "theta,a,b,c",
        [
            # Normal case: information should be positive
            (0.0, 1.0, 0.0, 0.2),
            (0.0, 1.5, 0.0, 0.2),
            (-1.0, 1.0, 0.0, 0.2),
            (1.0, 1.0, 0.0, 0.2),
            (0.0, 2.5, 0.0, 0.35),
        ],
    )
    def test_information_always_non_negative(self, theta, a, b, c):
        from services.irt_service_3pl import IRTService3PL

        info = IRTService3PL.information(theta, a, b, c)
        assert info >= 0.0, f"information should be >= 0, got {info}"


# =============================================================================
# 3. IRTService3PL.eap_theta() — 5 tests
# =============================================================================


class TestEAPTheta:
    """EAP theta estimation — convergence direction + prior shift."""

    def test_eap_theta_empty_input_returns_zero_tuple(self):
        from services.irt_service_3pl import IRTService3PL

        theta, se = IRTService3PL.eap_theta([], [])
        assert theta == 0.0
        assert se == 1.0

    def test_eap_theta_all_correct_increases_theta(self):
        from services.irt_service_3pl import IRTService3PL

        items = [{"irt_a": 1.0, "irt_b": 0.0, "irt_c": 0.2}] * 5
        theta_all_correct, _ = IRTService3PL.eap_theta(items, [True] * 5)
        assert theta_all_correct > 0.0, (
            f"all-correct theta should be > 0, got {theta_all_correct}"
        )

    def test_eap_theta_all_wrong_decreases_theta(self):
        from services.irt_service_3pl import IRTService3PL

        items = [{"irt_a": 1.0, "irt_b": 0.0, "irt_c": 0.2}] * 5
        theta_all_wrong, _ = IRTService3PL.eap_theta(items, [False] * 5)
        assert theta_all_wrong < 0.0, (
            f"all-wrong theta should be < 0, got {theta_all_wrong}"
        )

    def test_eap_theta_theta_bounded_by_range(self):
        from services.irt_service_3pl import IRTService3PL

        items = [{"irt_a": 1.0, "irt_b": 0.0, "irt_c": 0.2}] * 20
        for responses in [[True] * 20, [False] * 20]:
            theta, _ = IRTService3PL.eap_theta(items, responses)
            assert -4.0 <= theta <= 4.0, f"theta {theta} outside [-4,4]"

    @pytest.mark.parametrize(
        "prior_mean,shift_direction",
        [
            # positive prior_mean should shift theta upward (all-correct)
            (2.0, "up"),
            # negative prior_mean should shift theta downward (all-correct)
            (-2.0, "down"),
        ],
    )
    def test_eap_theta_prior_mean_shifts_theta(self, prior_mean, shift_direction):
        from services.irt_service_3pl import IRTService3PL

        items = [{"irt_a": 1.0, "irt_b": 0.0, "irt_c": 0.2}] * 5
        responses = [True] * 5
        # With positive prior: theta shifted up
        theta_shifted, _ = IRTService3PL.eap_theta(
            items, responses, prior_mean=prior_mean
        )
        # With default prior (0): theta baseline
        theta_baseline, _ = IRTService3PL.eap_theta(items, responses, prior_mean=0.0)
        if shift_direction == "up":
            assert theta_shifted > theta_baseline, (
                f"positive prior should increase theta: {theta_shifted} vs baseline {theta_baseline}"
            )
        else:
            assert theta_shifted < theta_baseline, (
                f"negative prior should decrease theta: {theta_shifted} vs baseline {theta_baseline}"
            )


# =============================================================================
# 4. BKTService.update() — 7 tests
# =============================================================================


class TestBKTUpdate:
    """BKT pure Bayesian update — boundary chain + denom fallback."""

    def test_correct_increases_p_learn(self):
        from services.bkt_service import BKTService

        for p_before in [0.1, 0.3, 0.5, 0.7, 0.9]:
            p_after = BKTService.update(p_before, correct=True)
            assert p_after > p_before, (
                f"correct should increase p_L: {p_before} -> {p_after}"
            )

    def test_wrong_decreases_p_learn(self):
        from services.bkt_service import BKTService

        for p_before in [0.3, 0.5, 0.7, 0.9, 1.0]:
            p_after = BKTService.update(p_before, correct=False)
            assert p_after < p_before, (
                f"wrong should decrease p_L: {p_before} -> {p_after}"
            )

    def test_output_never_exceeds_0_999(self):
        from services.bkt_service import BKTService

        for p_before in [0.0, 0.1, 0.5, 0.9, 0.999, 1.0]:
            for _ in range(20):  # many correct answers in a row
                p_before = BKTService.update(p_before, correct=True)
            assert p_before <= 0.999, f"p_L should never exceed 0.999, got {p_before}"

    def test_zero_mastery_correct_increases(self):
        from services.bkt_service import BKTService

        p_after = BKTService.update(0.0, correct=True)
        assert p_after > 0.0, (
            f"from p_L=0, correct should increase to positive: {p_after}"
        )

    def test_one_mastery_wrong_decreases(self):
        from services.bkt_service import BKTService

        p_after = BKTService.update(1.0, correct=False)
        assert p_after < 1.0, f"from p_L=1, wrong should decrease: {p_after}"

    def test_denom_zero_fallback_returns_unchanged(self):
        from services.bkt_service import BKTService

        # When p_learn=0, p_S=0, p_G=0 → denom≈0 → returns p_learn unchanged (0.0)
        p_after = BKTService.update(0.0, correct=False, p_T=0.0, p_G=0.0, p_S=0.0)
        assert p_after == 0.001, (
            f"denom→0 fallback should return p_learn clamped to floor: {p_after}"
        )
        # Note: p_learn=1.0 hits ceiling min(1.0, 0.999)=0.999 so we test only the fallback
        # using a value below ceiling threshold
        p_after = BKTService.update(0.5, correct=False, p_T=0.0, p_G=1.0, p_S=0.0)
        assert p_after == 0.5, (
            f"denom→0 fallback should return p_learn unchanged: {p_after}"
        )

    def test_p_learn_ceiling_at_0_999_no_overshoot(self):
        from services.bkt_service import BKTService

        # p_L=0.999 + correct → after ceiling round(min(new_p_L, 0.999))
        p = BKTService.update(0.999, correct=True)
        assert p == 0.999, f"p_L=0.999 ceiling should hold, got {p}"
        # Also test p_L=0.999 + wrong → should decrease
        p = BKTService.update(0.999, correct=False)
        assert p < 0.999, f"from p_L=0.999, wrong should decrease: {p}"
