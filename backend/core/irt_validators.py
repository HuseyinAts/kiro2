"""
IRT (Item Response Theory) Parameter Validators

CLAUDE.md'den IRT parametre araliklari:
- difficulty: [-4.0, 4.0]
- discrimination: [0.2, 4.0]
- guessing: [0.0, 0.35]
- ZPD optimal: %15-85 basari olasiligi

Bu modul tum IRT parametrelerinin CLAUDE.md'de belirtilen
araliklarda olmasini garanti eder.

Boris Cherny Standards: Verification Feedback Loops
"""

from typing import Tuple, Optional


# CLAUDE.md'den IRT parametre araliklari (satir 55-57)
IRT_DIFFICULTY_RANGE: Tuple[float, float] = (-4.0, 4.0)
IRT_DISCRIMINATION_RANGE: Tuple[float, float] = (0.2, 4.0)
IRT_GUESSING_RANGE: Tuple[float, float] = (0.0, 0.35)
IRT_UPPER_ASYMPTOTE_RANGE: Tuple[float, float] = (0.0, 1.0)

# ZPD (Zone of Proximal Development) optimal araligi
ZPD_SUCCESS_PROBABILITY_RANGE: Tuple[float, float] = (0.15, 0.85)


class IRTValidationError(ValueError):
    """IRT parametre validasyon hatasi."""

    def __init__(
        self,
        param_name: str,
        value: float,
        min_val: float,
        max_val: float,
    ) -> None:
        self.param_name = param_name
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        super().__init__(
            f"IRT {param_name} must be in [{min_val}, {max_val}], got {value}"
        )


def validate_irt_difficulty(
    value: float,
    strict: bool = True,
) -> float:
    """
    IRT difficulty (b) parametresini dogrula.

    Args:
        value: Zorluk degeri
        strict: True ise ValueError, False ise clamp

    Returns:
        Dogrulanmis zorluk degeri

    Raises:
        IRTValidationError: Deger aralik disindaysa ve strict=True
    """
    min_val, max_val = IRT_DIFFICULTY_RANGE

    if not min_val <= value <= max_val:
        if strict:
            raise IRTValidationError("difficulty", value, min_val, max_val)
        # Clamp to valid range
        return max(min_val, min(max_val, value))

    return value


def validate_irt_discrimination(
    value: float,
    strict: bool = True,
) -> float:
    """
    IRT discrimination (a) parametresini dogrula.

    Args:
        value: Ayirt edicilik degeri
        strict: True ise ValueError, False ise clamp

    Returns:
        Dogrulanmis ayirt edicilik degeri

    Raises:
        IRTValidationError: Deger aralik disindaysa ve strict=True
    """
    min_val, max_val = IRT_DISCRIMINATION_RANGE

    if not min_val <= value <= max_val:
        if strict:
            raise IRTValidationError("discrimination", value, min_val, max_val)
        return max(min_val, min(max_val, value))

    return value


def validate_irt_guessing(
    value: float,
    strict: bool = True,
) -> float:
    """
    IRT guessing (c) parametresini dogrula.

    Args:
        value: Tahmin parametresi (4 secenekli MCQ icin genelde 0.25)
        strict: True ise ValueError, False ise clamp

    Returns:
        Dogrulanmis tahmin degeri

    Raises:
        IRTValidationError: Deger aralik disindaysa ve strict=True
    """
    min_val, max_val = IRT_GUESSING_RANGE

    if not min_val <= value <= max_val:
        if strict:
            raise IRTValidationError("guessing", value, min_val, max_val)
        return max(min_val, min(max_val, value))

    return value


def validate_irt_upper_asymptote(
    value: float,
    strict: bool = True,
) -> float:
    """
    IRT upper asymptote (d) parametresini dogrula.

    Args:
        value: Ust asimptot degeri (genelde 1.0 veya 0.97-0.99)
        strict: True ise ValueError, False ise clamp

    Returns:
        Dogrulanmis ust asimptot degeri

    Raises:
        IRTValidationError: Deger aralik disindaysa ve strict=True
    """
    min_val, max_val = IRT_UPPER_ASYMPTOTE_RANGE

    if not min_val <= value <= max_val:
        if strict:
            raise IRTValidationError("upper_asymptote", value, min_val, max_val)
        return max(min_val, min(max_val, value))

    return value


def validate_all_irt_params(
    difficulty: float,
    discrimination: float,
    guessing: float,
    upper_asymptote: float = 1.0,
    strict: bool = True,
) -> Tuple[float, float, float, float]:
    """
    Tum IRT parametrelerini tek seferde dogrula.

    Args:
        difficulty: Zorluk parametresi (b)
        discrimination: Ayirt edicilik parametresi (a)
        guessing: Tahmin parametresi (c)
        upper_asymptote: Ust asimptot parametresi (d)
        strict: True ise ValueError, False ise clamp

    Returns:
        Dogrulanmis (difficulty, discrimination, guessing, upper_asymptote) tuple

    Raises:
        IRTValidationError: Herhangi bir parametre aralik disindaysa ve strict=True
    """
    return (
        validate_irt_difficulty(difficulty, strict),
        validate_irt_discrimination(discrimination, strict),
        validate_irt_guessing(guessing, strict),
        validate_irt_upper_asymptote(upper_asymptote, strict),
    )


def is_in_zpd(
    success_probability: float,
    min_prob: Optional[float] = None,
    max_prob: Optional[float] = None,
) -> bool:
    """
    Basari olasiliginin ZPD (Zone of Proximal Development) icinde olup
    olmadigini kontrol et.

    CLAUDE.md: ZPD optimal: %15-85 basari olasiligi

    Args:
        success_probability: Hesaplanan basari olasiligi [0, 1]
        min_prob: Minimum ZPD siniri (varsayilan 0.15)
        max_prob: Maksimum ZPD siniri (varsayilan 0.85)

    Returns:
        True eger olasilik ZPD icindeyse
    """
    min_val = min_prob if min_prob is not None else ZPD_SUCCESS_PROBABILITY_RANGE[0]
    max_val = max_prob if max_prob is not None else ZPD_SUCCESS_PROBABILITY_RANGE[1]

    return min_val <= success_probability <= max_val


# Pydantic field validator olarak kullanilabilecek wrapper'lar
def pydantic_difficulty_validator(value: float) -> float:
    """Pydantic field_validator icin difficulty wrapper."""
    return validate_irt_difficulty(value, strict=True)


def pydantic_discrimination_validator(value: float) -> float:
    """Pydantic field_validator icin discrimination wrapper."""
    return validate_irt_discrimination(value, strict=True)


def pydantic_guessing_validator(value: float) -> float:
    """Pydantic field_validator icin guessing wrapper."""
    return validate_irt_guessing(value, strict=True)


def pydantic_upper_asymptote_validator(value: float) -> float:
    """Pydantic field_validator icin upper_asymptote wrapper."""
    return validate_irt_upper_asymptote(value, strict=True)
