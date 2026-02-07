"""
IRT Parametre Validasyon Testleri

Boris Cherny Standards: Verification Feedback Loops
CLAUDE.md'den IRT parametre araliklari test edilir:
- difficulty: [-4.0, 4.0]
- discrimination: [0.2, 4.0]
- guessing: [0.0, 0.35]
- upper_asymptote: [0.0, 1.0]
- ZPD optimal: %15-85 basari olasiligi
"""

import pytest
from core.irt_validators import (
    validate_irt_difficulty,
    validate_irt_discrimination,
    validate_irt_guessing,
    validate_irt_upper_asymptote,
    validate_all_irt_params,
    is_in_zpd,
    IRTValidationError,
    IRT_DIFFICULTY_RANGE,
    IRT_DISCRIMINATION_RANGE,
    IRT_GUESSING_RANGE,
    IRT_UPPER_ASYMPTOTE_RANGE,
    ZPD_SUCCESS_PROBABILITY_RANGE,
    pydantic_difficulty_validator,
    pydantic_discrimination_validator,
    pydantic_guessing_validator,
    pydantic_upper_asymptote_validator,
)


class TestIRTValidationError:
    """IRTValidationError exception testleri."""

    def test_error_message_format(self):
        """Hata mesaji dogru formatta olmali."""
        error = IRTValidationError("difficulty", 5.0, -4.0, 4.0)
        assert "difficulty" in str(error)
        assert "[-4.0, 4.0]" in str(error)
        assert "5.0" in str(error)

    def test_error_attributes(self):
        """Hata objesinin attribute'lari dogru olmali."""
        error = IRTValidationError("discrimination", 0.1, 0.2, 4.0)
        assert error.param_name == "discrimination"
        assert error.value == 0.1
        assert error.min_val == 0.2
        assert error.max_val == 4.0


class TestValidateIRTDifficulty:
    """Difficulty (b) parametre validasyonu testleri."""

    @pytest.mark.parametrize("value", [-4.0, -2.0, 0.0, 2.0, 4.0])
    def test_valid_difficulty_values(self, value):
        """Gecerli difficulty degerleri kabul edilmeli."""
        result = validate_irt_difficulty(value)
        assert result == value

    @pytest.mark.parametrize("value", [-4.1, -5.0, -10.0])
    def test_invalid_difficulty_too_low_strict(self, value):
        """Cok dusuk difficulty degerleri strict modda hata vermeli."""
        with pytest.raises(IRTValidationError) as exc_info:
            validate_irt_difficulty(value, strict=True)
        assert exc_info.value.param_name == "difficulty"
        assert exc_info.value.value == value

    @pytest.mark.parametrize("value", [4.1, 5.0, 10.0])
    def test_invalid_difficulty_too_high_strict(self, value):
        """Cok yuksek difficulty degerleri strict modda hata vermeli."""
        with pytest.raises(IRTValidationError) as exc_info:
            validate_irt_difficulty(value, strict=True)
        assert exc_info.value.param_name == "difficulty"

    def test_invalid_difficulty_clamped_non_strict(self):
        """Non-strict modda degerler clamp edilmeli."""
        assert validate_irt_difficulty(-5.0, strict=False) == -4.0
        assert validate_irt_difficulty(5.0, strict=False) == 4.0
        assert validate_irt_difficulty(10.0, strict=False) == 4.0

    def test_boundary_values(self):
        """Sinir degerleri gecerli olmali."""
        assert validate_irt_difficulty(-4.0) == -4.0
        assert validate_irt_difficulty(4.0) == 4.0


class TestValidateIRTDiscrimination:
    """Discrimination (a) parametre validasyonu testleri."""

    @pytest.mark.parametrize("value", [0.2, 0.5, 1.0, 2.0, 4.0])
    def test_valid_discrimination_values(self, value):
        """Gecerli discrimination degerleri kabul edilmeli."""
        result = validate_irt_discrimination(value)
        assert result == value

    @pytest.mark.parametrize("value", [0.0, 0.1, 0.19])
    def test_invalid_discrimination_too_low_strict(self, value):
        """Cok dusuk discrimination degerleri strict modda hata vermeli."""
        with pytest.raises(IRTValidationError) as exc_info:
            validate_irt_discrimination(value, strict=True)
        assert exc_info.value.param_name == "discrimination"

    @pytest.mark.parametrize("value", [4.1, 5.0, 10.0])
    def test_invalid_discrimination_too_high_strict(self, value):
        """Cok yuksek discrimination degerleri strict modda hata vermeli."""
        with pytest.raises(IRTValidationError) as exc_info:
            validate_irt_discrimination(value, strict=True)
        assert exc_info.value.param_name == "discrimination"

    def test_invalid_discrimination_clamped_non_strict(self):
        """Non-strict modda degerler clamp edilmeli."""
        assert validate_irt_discrimination(0.1, strict=False) == 0.2
        assert validate_irt_discrimination(5.0, strict=False) == 4.0

    def test_boundary_values(self):
        """Sinir degerleri gecerli olmali."""
        assert validate_irt_discrimination(0.2) == 0.2
        assert validate_irt_discrimination(4.0) == 4.0


class TestValidateIRTGuessing:
    """Guessing (c) parametre validasyonu testleri."""

    @pytest.mark.parametrize("value", [0.0, 0.1, 0.2, 0.25, 0.35])
    def test_valid_guessing_values(self, value):
        """Gecerli guessing degerleri kabul edilmeli."""
        result = validate_irt_guessing(value)
        assert result == value

    @pytest.mark.parametrize("value", [-0.1, -0.5, -1.0])
    def test_invalid_guessing_negative_strict(self, value):
        """Negatif guessing degerleri strict modda hata vermeli."""
        with pytest.raises(IRTValidationError) as exc_info:
            validate_irt_guessing(value, strict=True)
        assert exc_info.value.param_name == "guessing"

    @pytest.mark.parametrize("value", [0.36, 0.5, 1.0])
    def test_invalid_guessing_too_high_strict(self, value):
        """Cok yuksek guessing degerleri strict modda hata vermeli."""
        with pytest.raises(IRTValidationError) as exc_info:
            validate_irt_guessing(value, strict=True)
        assert exc_info.value.param_name == "guessing"

    def test_invalid_guessing_clamped_non_strict(self):
        """Non-strict modda degerler clamp edilmeli."""
        assert validate_irt_guessing(-0.1, strict=False) == 0.0
        assert validate_irt_guessing(0.5, strict=False) == 0.35

    def test_typical_mcq_guessing(self):
        """4 secenekli MCQ icin tipik guessing degeri (0.25)."""
        assert validate_irt_guessing(0.25) == 0.25


class TestValidateIRTUpperAsymptote:
    """Upper asymptote (d) parametre validasyonu testleri."""

    @pytest.mark.parametrize("value", [0.0, 0.5, 0.9, 0.97, 1.0])
    def test_valid_upper_asymptote_values(self, value):
        """Gecerli upper_asymptote degerleri kabul edilmeli."""
        result = validate_irt_upper_asymptote(value)
        assert result == value

    @pytest.mark.parametrize("value", [-0.1, -0.5, -1.0])
    def test_invalid_upper_asymptote_negative_strict(self, value):
        """Negatif upper_asymptote degerleri strict modda hata vermeli."""
        with pytest.raises(IRTValidationError) as exc_info:
            validate_irt_upper_asymptote(value, strict=True)
        assert exc_info.value.param_name == "upper_asymptote"

    @pytest.mark.parametrize("value", [1.1, 1.5, 2.0])
    def test_invalid_upper_asymptote_too_high_strict(self, value):
        """1'den buyuk upper_asymptote degerleri strict modda hata vermeli."""
        with pytest.raises(IRTValidationError) as exc_info:
            validate_irt_upper_asymptote(value, strict=True)
        assert exc_info.value.param_name == "upper_asymptote"

    def test_invalid_upper_asymptote_clamped_non_strict(self):
        """Non-strict modda degerler clamp edilmeli."""
        assert validate_irt_upper_asymptote(-0.1, strict=False) == 0.0
        assert validate_irt_upper_asymptote(1.5, strict=False) == 1.0


class TestValidateAllIRTParams:
    """Tum IRT parametrelerinin birlikte validasyonu testleri."""

    def test_all_valid_params(self):
        """Tum parametreler gecerli oldugunda tuple donmeli."""
        result = validate_all_irt_params(
            difficulty=0.0,
            discrimination=1.0,
            guessing=0.25,
            upper_asymptote=0.97,
        )
        assert result == (0.0, 1.0, 0.25, 0.97)

    def test_invalid_difficulty_raises(self):
        """Gecersiz difficulty hataya neden olmali."""
        with pytest.raises(IRTValidationError) as exc_info:
            validate_all_irt_params(
                difficulty=5.0,  # Invalid
                discrimination=1.0,
                guessing=0.25,
            )
        assert exc_info.value.param_name == "difficulty"

    def test_invalid_discrimination_raises(self):
        """Gecersiz discrimination hataya neden olmali."""
        with pytest.raises(IRTValidationError) as exc_info:
            validate_all_irt_params(
                difficulty=0.0,
                discrimination=0.1,  # Invalid
                guessing=0.25,
            )
        assert exc_info.value.param_name == "discrimination"

    def test_invalid_guessing_raises(self):
        """Gecersiz guessing hataya neden olmali."""
        with pytest.raises(IRTValidationError) as exc_info:
            validate_all_irt_params(
                difficulty=0.0,
                discrimination=1.0,
                guessing=0.5,  # Invalid
            )
        assert exc_info.value.param_name == "guessing"

    def test_all_clamped_non_strict(self):
        """Non-strict modda tum degerler clamp edilmeli."""
        result = validate_all_irt_params(
            difficulty=10.0,
            discrimination=0.1,
            guessing=0.5,
            upper_asymptote=1.5,
            strict=False,
        )
        assert result == (4.0, 0.2, 0.35, 1.0)


class TestIsInZPD:
    """Zone of Proximal Development (ZPD) kontrolu testleri."""

    @pytest.mark.parametrize("prob", [0.15, 0.3, 0.5, 0.7, 0.85])
    def test_probability_in_zpd(self, prob):
        """ZPD icindeki olasiliklar True donmeli."""
        assert is_in_zpd(prob) is True

    @pytest.mark.parametrize("prob", [0.0, 0.1, 0.14])
    def test_probability_below_zpd(self, prob):
        """ZPD altindaki olasiliklar False donmeli."""
        assert is_in_zpd(prob) is False

    @pytest.mark.parametrize("prob", [0.86, 0.9, 1.0])
    def test_probability_above_zpd(self, prob):
        """ZPD ustundeki olasiliklar False donmeli."""
        assert is_in_zpd(prob) is False

    def test_custom_zpd_range(self):
        """Ozel ZPD araligi kullanilabilmeli."""
        assert is_in_zpd(0.1, min_prob=0.05, max_prob=0.20) is True
        assert is_in_zpd(0.1, min_prob=0.15, max_prob=0.85) is False

    def test_boundary_values(self):
        """Sinir degerleri ZPD icinde olmali."""
        assert is_in_zpd(0.15) is True  # Alt sinir
        assert is_in_zpd(0.85) is True  # Ust sinir


class TestPydanticValidators:
    """Pydantic field validator wrapper testleri."""

    def test_pydantic_difficulty_valid(self):
        """Gecerli difficulty Pydantic validator'dan gecmeli."""
        assert pydantic_difficulty_validator(0.0) == 0.0
        assert pydantic_difficulty_validator(-4.0) == -4.0
        assert pydantic_difficulty_validator(4.0) == 4.0

    def test_pydantic_difficulty_invalid(self):
        """Gecersiz difficulty Pydantic validator'da hata vermeli."""
        with pytest.raises(IRTValidationError):
            pydantic_difficulty_validator(5.0)

    def test_pydantic_discrimination_valid(self):
        """Gecerli discrimination Pydantic validator'dan gecmeli."""
        assert pydantic_discrimination_validator(1.0) == 1.0

    def test_pydantic_discrimination_invalid(self):
        """Gecersiz discrimination Pydantic validator'da hata vermeli."""
        with pytest.raises(IRTValidationError):
            pydantic_discrimination_validator(0.1)

    def test_pydantic_guessing_valid(self):
        """Gecerli guessing Pydantic validator'dan gecmeli."""
        assert pydantic_guessing_validator(0.25) == 0.25

    def test_pydantic_guessing_invalid(self):
        """Gecersiz guessing Pydantic validator'da hata vermeli."""
        with pytest.raises(IRTValidationError):
            pydantic_guessing_validator(0.5)

    def test_pydantic_upper_asymptote_valid(self):
        """Gecerli upper_asymptote Pydantic validator'dan gecmeli."""
        assert pydantic_upper_asymptote_validator(0.97) == 0.97

    def test_pydantic_upper_asymptote_invalid(self):
        """Gecersiz upper_asymptote Pydantic validator'da hata vermeli."""
        with pytest.raises(IRTValidationError):
            pydantic_upper_asymptote_validator(1.5)


class TestConstantRanges:
    """CLAUDE.md'den alinan sabit araliklarin testleri."""

    def test_difficulty_range(self):
        """Difficulty araligi [-4.0, 4.0] olmali."""
        assert IRT_DIFFICULTY_RANGE == (-4.0, 4.0)

    def test_discrimination_range(self):
        """Discrimination araligi [0.2, 4.0] olmali."""
        assert IRT_DISCRIMINATION_RANGE == (0.2, 4.0)

    def test_guessing_range(self):
        """Guessing araligi [0.0, 0.35] olmali."""
        assert IRT_GUESSING_RANGE == (0.0, 0.35)

    def test_upper_asymptote_range(self):
        """Upper asymptote araligi [0.0, 1.0] olmali."""
        assert IRT_UPPER_ASYMPTOTE_RANGE == (0.0, 1.0)

    def test_zpd_range(self):
        """ZPD araligi [0.15, 0.85] olmali."""
        assert ZPD_SUCCESS_PROBABILITY_RANGE == (0.15, 0.85)


class TestIRTItemIntegration:
    """IRTItem dataclass ile entegrasyon testleri."""

    def test_irtitem_valid_creation(self):
        """Gecerli parametrelerle IRTItem olusturulabilmeli."""
        from algorithms.irt_model import IRTItem

        item = IRTItem(
            item_id="test_001",
            discrimination=1.5,
            difficulty=0.0,
            guessing=0.25,
            upper_asymptote=0.97,
        )
        assert item.item_id == "test_001"
        assert item.discrimination == 1.5
        assert item.difficulty == 0.0
        assert item.guessing == 0.25
        assert item.upper_asymptote == 0.97

    def test_irtitem_invalid_difficulty_raises(self):
        """Gecersiz difficulty ile IRTItem olusturulmamali."""
        from algorithms.irt_model import IRTItem

        with pytest.raises(IRTValidationError):
            IRTItem(
                item_id="test_002",
                discrimination=1.0,
                difficulty=5.0,  # Invalid
                guessing=0.25,
            )

    def test_irtitem_invalid_discrimination_raises(self):
        """Gecersiz discrimination ile IRTItem olusturulmamali."""
        from algorithms.irt_model import IRTItem

        with pytest.raises(IRTValidationError):
            IRTItem(
                item_id="test_003",
                discrimination=0.1,  # Invalid
                difficulty=0.0,
                guessing=0.25,
            )

    def test_irtitem_validation_skip(self):
        """_validate=False ile validasyon atlanabilmeli."""
        from algorithms.irt_model import IRTItem

        # Legacy data icin validasyon atlama
        item = IRTItem(
            item_id="legacy_001",
            discrimination=0.1,  # Normally invalid
            difficulty=10.0,  # Normally invalid
            guessing=0.5,  # Normally invalid
            _validate=False,
        )
        # Nesne olusturuldu, validasyon hatasi yok
        assert item.discrimination == 0.1
        assert item.difficulty == 10.0
        assert item.guessing == 0.5
