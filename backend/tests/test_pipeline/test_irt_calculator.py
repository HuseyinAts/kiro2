"""
IRT Calculator Tests
IRT parametreleri ve hesaplamaları için testler

Property Tests (design.md):
- Property 1: IRT Parameter Ranges
- Property 2: ZPD bounds
"""

import pytest
from hypothesis import given, strategies as st, settings

# Note: conftest.py adds backend dir to sys.path

from pipeline.tools.irt_calculator import IRTCalculator


class TestIRTCalculator:
    """IRT Calculator test sınıfı"""

    @pytest.fixture
    def calculator(self):
        """IRT Calculator fixture"""
        return IRTCalculator()

    # ============== Unit Tests ==============

    def test_calculate_probability_average_student(self, calculator):
        """Ortalama öğrenci için olasılık hesabı"""
        prob = calculator.calculate_probability(
            theta=0.0,
            difficulty=0.0,
            discrimination=1.0,
            guessing=0.25
        )

        # Ortalama öğrenci, ortalama zorluk -> ~0.625 olasılık
        assert 0.5 <= prob <= 0.75
        assert isinstance(prob, float)

    def test_calculate_probability_easy_question(self, calculator):
        """Kolay soru için olasılık hesabı"""
        prob = calculator.calculate_probability(
            theta=0.0,
            difficulty=-2.0,  # Kolay
            discrimination=1.0,
            guessing=0.25
        )

        # Kolay soru -> yüksek olasılık
        assert prob > 0.8

    def test_calculate_probability_hard_question(self, calculator):
        """Zor soru için olasılık hesabı"""
        prob = calculator.calculate_probability(
            theta=0.0,
            difficulty=2.0,  # Zor
            discrimination=1.0,
            guessing=0.25
        )

        # Zor soru -> düşük olasılık (ama guessing floor var)
        assert 0.25 <= prob <= 0.5

    def test_zpd_check_optimal(self, calculator):
        """Optimal ZPD kontrolü"""
        in_zpd, score, _ = calculator.check_zpd(
            difficulty=0.0,
            discrimination=1.0,
            guessing=0.25,
            theta=0.0
        )

        assert in_zpd is True
        assert score >= 0.8

    def test_zpd_check_too_easy(self, calculator):
        """Çok kolay soru ZPD kontrolü"""
        in_zpd, score, _ = calculator.check_zpd(
            difficulty=-3.0,  # Çok kolay
            discrimination=1.0,
            guessing=0.25,
            theta=0.0
        )

        # Çok kolay -> ZPD dışı olabilir
        # P > 0.85 olacak
        assert score <= 0.8

    def test_validate_parameters_valid(self, calculator):
        """Geçerli parametreler"""
        is_valid, errors = calculator.validate_parameters(
            difficulty=0.0,
            discrimination=1.0,
            guessing=0.25
        )

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_parameters_invalid_difficulty(self, calculator):
        """Geçersiz difficulty"""
        is_valid, errors = calculator.validate_parameters(
            difficulty=5.0,  # > 4.0
            discrimination=1.0,
            guessing=0.25
        )

        assert is_valid is False
        assert len(errors) > 0
        assert "difficulty" in errors[0].lower()

    def test_validate_parameters_invalid_discrimination(self, calculator):
        """Geçersiz discrimination"""
        is_valid, errors = calculator.validate_parameters(
            difficulty=0.0,
            discrimination=0.1,  # < 0.2
            guessing=0.25
        )

        assert is_valid is False
        assert len(errors) > 0

    def test_validate_parameters_invalid_guessing(self, calculator):
        """Geçersiz guessing"""
        is_valid, errors = calculator.validate_parameters(
            difficulty=0.0,
            discrimination=1.0,
            guessing=0.5  # > 0.35
        )

        assert is_valid is False
        assert len(errors) > 0

    def test_estimate_difficulty_from_text(self, calculator):
        """Metin tabanlı zorluk tahmini"""
        params = calculator.estimate_difficulty_from_text(
            "Bu basit bir soru",
            target_difficulty="kolay"
        )

        assert "difficulty" in params
        assert "discrimination" in params
        assert "guessing" in params
        assert -4.0 <= params["difficulty"] <= 4.0

    def test_find_optimal_difficulty(self, calculator):
        """Optimal zorluk bulma"""
        difficulty = calculator.find_optimal_difficulty(
            theta=0.0,
            target_probability=0.5
        )

        assert -4.0 <= difficulty <= 4.0

        # Verify: bu zorlukla olasılık ~0.5 olmalı
        prob = calculator.calculate_probability(
            theta=0.0,
            difficulty=difficulty,
            discrimination=1.0,
            guessing=0.25
        )
        assert 0.45 <= prob <= 0.55

    # ============== Property Tests ==============

    @given(
        difficulty=st.floats(min_value=-4.0, max_value=4.0, allow_nan=False),
        discrimination=st.floats(min_value=0.2, max_value=4.0, allow_nan=False),
        guessing=st.floats(min_value=0.0, max_value=0.35, allow_nan=False),
        theta=st.floats(min_value=-4.0, max_value=4.0, allow_nan=False)
    )
    @settings(max_examples=100)
    def test_property_probability_bounds(self, difficulty, discrimination, guessing, theta):
        """
        Property 1: Probability her zaman [guessing, 1.0] aralığında

        3PL modelde P(θ) >= c (guessing parameter)
        """
        calculator = IRTCalculator()
        prob = calculator.calculate_probability(theta, difficulty, discrimination, guessing)

        # Probability bounds
        assert guessing <= prob <= 1.0
        assert isinstance(prob, float)

    @given(
        difficulty=st.floats(min_value=-4.0, max_value=4.0, allow_nan=False),
        discrimination=st.floats(min_value=0.2, max_value=4.0, allow_nan=False),
        guessing=st.floats(min_value=0.0, max_value=0.35, allow_nan=False)
    )
    @settings(max_examples=100)
    def test_property_irt_parameter_ranges(self, difficulty, discrimination, guessing):
        """
        Property 1 (design.md): IRT Parameter Ranges

        For any question:
        - difficulty in [-4.0, 4.0]
        - discrimination in [0.2, 4.0]
        - guessing in [0.0, 0.35]
        """
        calculator = IRTCalculator()
        is_valid, errors = calculator.validate_parameters(difficulty, discrimination, guessing)

        # Parametreler verilen aralıkta ise valid olmalı
        assert is_valid is True
        assert len(errors) == 0

    @given(theta=st.floats(min_value=-4.0, max_value=4.0, allow_nan=False))
    @settings(max_examples=50)
    def test_property_zpd_score_bounds(self, theta):
        """
        Property 2 (design.md): ZPD Score Bounds

        ZPD score her zaman [0.0, 1.0] aralığında
        """
        calculator = IRTCalculator()
        _, score, _ = calculator.check_zpd(
            difficulty=0.0,
            discrimination=1.0,
            guessing=0.25,
            theta=theta
        )

        assert 0.0 <= score <= 1.0

    @given(
        theta1=st.floats(min_value=-4.0, max_value=4.0, allow_nan=False),
        theta2=st.floats(min_value=-4.0, max_value=4.0, allow_nan=False)
    )
    @settings(max_examples=50)
    def test_property_probability_monotonic(self, theta1, theta2):
        """
        Property: Probability theta'ya göre monoton artan

        θ1 > θ2 => P(θ1) >= P(θ2) (aynı soru için)
        """
        calculator = IRTCalculator()

        prob1 = calculator.calculate_probability(
            theta=theta1,
            difficulty=0.0,
            discrimination=1.0,
            guessing=0.25
        )
        prob2 = calculator.calculate_probability(
            theta=theta2,
            difficulty=0.0,
            discrimination=1.0,
            guessing=0.25
        )

        if theta1 > theta2:
            assert prob1 >= prob2
        elif theta2 > theta1:
            assert prob2 >= prob1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
