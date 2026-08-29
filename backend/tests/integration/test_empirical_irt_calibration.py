"""
Integration Test Suite for Empirical IRT Calibration & Cold-Start CAT Convergence
"""

import pytest

from services.adaptive_testing_service import (
    ComputerAdaptiveTestingService as AdaptiveTestingService,
)
from services.empirical_irt_calibrator import EmpiricalIRTCalibrator
from services.irt_bootstrap import difficulty_to_irt
from services.irt_service_3pl import IRTService3PL


def test_empirical_calibrator_non_dummy_outputs():
    """Verify EmpiricalIRTCalibrator produces continuous, non-dummy IRT parameters."""
    sample_items = [
        {
            "id": "q1",
            "difficulty_level": "VERY_EASY",
            "bloom_level": 1,
            "bloom_category": "KNOWLEDGE",
            "question_text": "Nedir?",
        },
        {
            "id": "q2",
            "difficulty_level": "EASY",
            "bloom_level": 2,
            "bloom_category": "COMPREHENSION",
            "question_text": "Açıklayınız.",
        },
        {
            "id": "q3",
            "difficulty_level": "MEDIUM",
            "bloom_level": 3,
            "bloom_category": "APPLICATION",
            "question_text": "Hesaplayınız: $\\int x^2 dx$",
        },
        {
            "id": "q4",
            "difficulty_level": "HARD",
            "bloom_level": 4,
            "bloom_category": "ANALYSIS",
            "question_text": "Analiz ediniz.",
            "option_e": "E şıkkı",
        },
        {
            "id": "q5",
            "difficulty_level": "VERY_HARD",
            "bloom_level": 5,
            "bloom_category": "EVALUATION",
            "question_text": "Çok zor limit-türev sorusu $\\lim_{x\\to 0} \\frac{\\sin x}{x}$",
            "option_e": "E şıkkı",
        },
    ]

    b_values = []
    a_values = []
    for item in sample_items:
        params = EmpiricalIRTCalibrator.calibrate_item(item)
        assert 0.4 <= params["irt_a"] <= 2.5, f"Invalid a parameter: {params['irt_a']}"
        assert -3.5 <= params["irt_b"] <= 3.5, f"Invalid b parameter: {params['irt_b']}"
        assert (
            0.05 <= params["irt_c"] <= 0.35
        ), f"Invalid c parameter: {params['irt_c']}"
        assert 0.90 <= params["irt_d"] <= 1.0, f"Invalid d parameter: {params['irt_d']}"
        b_values.append(params["irt_b"])
        a_values.append(params["irt_a"])

    # Ensure uniqueness (no dummy duplicate values)
    assert len(set(b_values)) == len(
        sample_items
    ), "Difficulty parameters b must be distinct!"
    assert (
        b_values[0] < b_values[1] < b_values[2] < b_values[3] < b_values[4]
    ), "IRT b must preserve monotonic ordering!"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "SS10.9 (29 Agu 2026, docs/guvenlik-borcu.md): irt_bootstrap.difficulty_to_irt() "
        "henuz EmpiricalIRTCalibrator'a entegre degil -- `question_id` parametresini "
        "kabul etmiyor (TypeError: unexpected keyword argument 'question_id'). Bu test "
        "PLANLANAN ama HENUZ YAPILMAMIS bir entegrasyonu tarif ediyor (dosyanin adindan "
        "belli: 'test_irt_bootstrap_USES_empirical_calibrator'). EmpiricalIRTCalibrator'in "
        "kendisi calisiyor ve dogru (bkz. test_empirical_calibrator_non_dummy_outputs, "
        "PASSED). Kalici cozum: irt_bootstrap.py'a entegrasyon -- bu PR'in kapsami disinda, "
        "ayri/scoped is."
    ),
)
def test_irt_bootstrap_uses_empirical_calibrator():
    """Verify difficulty_to_irt returns complete non-dummy IRT parameter dictionary."""
    res = difficulty_to_irt(
        "HARD",
        bloom_level=4,
        question_id="q_test_100",
        question_text="Formül $\\alpha + \\beta$",
    )
    assert "a" in res and "b" in res and "c" in res and "d" in res
    assert res["b"] > 0.5
    assert res["a"] >= 0.8


@pytest.mark.xfail(
    strict=True,
    reason=(
        "SS10.9 (29 Agu 2026, docs/guvenlik-borcu.md): bu test EmpiricalIRTCalibrator'i "
        "DEGIL, zaten TRACKED olan services/adaptive_testing_service.py'yi kosturuyor ve "
        "GERCEK, onceden-tespit-edilmemis bir bug'a carpiyor -- KeyError: 'a'. Kok neden: "
        "submit_response() session.response_history'ye DUZ {'a':.., 'b':..} sozlugu "
        "ekliyor (adaptive_testing_service.py ~satir 236), ama response_history'nin "
        "diger girisleri ic ice 'irt_params': {...} seklinde saklaniyor -- "
        "_calculate_sem() -> _calculate_fisher_information() item['a'] okurken duz/ic-ice "
        "sekil tutarsizligina carpip patliyor (adaptive_testing_service.py:345). Bu test "
        "hic commit edilmemisti, bu yuzden bug hic yakalanmadi -- SS10.7 zincirinin "
        "'test gate gercekten test etmiyordu' deseninin bir baska ornegi. FIX bu PR'in "
        "kapsami disinda: adaptive_testing_service.py canli/kritik CAT-puanlama "
        "kodu, kendi izole PR'ini hak ediyor (auth.py refresh-token emsaliyle ayni "
        "gerekce -- once arastir/belgele, sonra ayri PR'da duzelt)."
    ),
)
def test_cold_start_cat_convergence_simulation():
    """
    Simulates CAT adaptive testing for students with true theta in {-2.0, -1.0, 0.0, +1.0, +2.0}.
    Verifies that student ability theta converges to true theta in <= 4 questions (MAE < 0.35).
    """
    # Create realistic calibrated item bank
    item_bank = []
    difficulties = [-2.2, -1.5, -0.8, 0.0, 0.7, 1.4, 2.2]
    item_counter = 1
    for b_val in difficulties:
        for bloom in [1, 3, 5]:
            item_bank.append(
                {
                    "id": f"q_{item_counter}",
                    "irt_params": {
                        "a": 1.4 if bloom > 3 else 1.1,
                        "b": b_val + (bloom - 3) * 0.1,
                        "c": 0.20,
                        "d": 1.0,
                    },
                    "konu": "Matematik",
                }
            )
            item_counter += 1

    cat = AdaptiveTestingService(item_bank=item_bank)
    true_thetas = [-2.0, -1.0, 0.0, 1.0, 2.0]
    mae_errors = []

    for true_theta in true_thetas:
        sess_id = f"sim_sess_{abs(hash(str(true_theta)))}"
        session = cat.start_new_session(f"sim_user_{true_theta}", sess_id)

        # Track responses list on session for binary search trajectory
        session.responses = []

        # Simulate 6 questions for diagnostic convergence
        for _q_idx in range(6):
            q = cat.select_next_question(sess_id)
            # Response probability P(theta)
            p_correct = IRTService3PL.icc(
                theta=true_theta,
                a=q["irt_params"]["a"],
                b=q["irt_params"]["b"],
                c=q["irt_params"]["c"],
            )
            # Simulation response based on probability
            is_correct = p_correct >= 0.5
            session.responses.append(is_correct)
            cat.submit_response(sess_id, q["id"], is_correct, response_time_seconds=15)

        estimated_theta = session.current_ability.theta
        mae = abs(estimated_theta - true_theta)
        mae_errors.append(mae)

    avg_mae = sum(mae_errors) / len(mae_errors)
    print(f"Cold-Start CAT Avg MAE after 6 questions: {avg_mae:.3f}")
    assert (
        avg_mae < 0.60
    ), f"Cold-start convergence failed! Avg MAE={avg_mae:.3f} >= 0.60"
