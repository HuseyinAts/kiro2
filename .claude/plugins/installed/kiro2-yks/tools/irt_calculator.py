"""IRT 3PL Calculator - Madde Tepki Kuramı hesaplayıcı.

3 Parametreli Lojistik Model (3PL) ile:
- Başarı olasılığı hesaplama
- Madde bilgi fonksiyonu
- Standart hata tahmini
- Parametre doğrulama
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class IRTConfig:
    """IRT parametre sınırları."""

    difficulty_range: tuple[float, float] = (-4.0, 4.0)
    discrimination_range: tuple[float, float] = (0.2, 4.0)
    guessing_range: tuple[float, float] = (0.0, 0.35)


@dataclass
class IRTResult:
    """IRT hesaplama sonucu."""

    probability: float
    information: float
    standard_error: float
    is_zpd_optimal: bool
    zpd_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "probability": round(self.probability, 4),
            "information": round(self.information, 4),
            "standard_error": round(self.standard_error, 4),
            "is_zpd_optimal": self.is_zpd_optimal,
            "zpd_status": self.zpd_status,
        }


class IRTCalculator:
    """IRT 3PL Model hesaplayıcı.

    Example:
        >>> calc = IRTCalculator()
        >>> result = calc.calculate(theta=0.5, difficulty=0.0, discrimination=1.2, guessing=0.2)
        >>> print(result.probability)  # ~0.74
    """

    def __init__(self, config: IRTConfig | None = None) -> None:
        self.config = config or IRTConfig()

    def probability_3pl(
        self,
        theta: float,
        difficulty: float,
        discrimination: float,
        guessing: float,
    ) -> float:
        """3PL modelde basari olasiligi: P(theta) = c + (1-c) / (1 + exp(-Da(theta-b))).

        Args:
            theta: Ogrenci yetenek parametresi.
            difficulty: Madde zorluk parametresi (b).
            discrimination: Madde ayirt edicilik parametresi (a).
            guessing: Sanslı tahmın parametresi (c).

        Returns:
            Basari olasiligi [0, 1].
        """
        d = 1.7  # scaling constant
        exponent = -d * discrimination * (theta - difficulty)
        exponent = max(-500, min(500, exponent))  # overflow guard
        return guessing + (1.0 - guessing) / (1.0 + math.exp(exponent))

    def information(
        self,
        theta: float,
        difficulty: float,
        discrimination: float,
        guessing: float,
    ) -> float:
        """Madde bilgi fonksiyonu: I(theta).

        Args:
            theta: Ogrenci yetenek parametresi.
            difficulty: Madde zorluk parametresi (b).
            discrimination: Madde ayirt edicilik parametresi (a).
            guessing: Sansli tahmin parametresi (c).

        Returns:
            Bilgi miktari (>= 0).
        """
        p = self.probability_3pl(theta, difficulty, discrimination, guessing)
        q = 1.0 - p
        if p <= guessing or q <= 0:
            return 0.0
        d = 1.7
        p_star = (p - guessing) / (1.0 - guessing)
        return (d**2) * (discrimination**2) * (p_star**2) * q / max(p, 1e-10)

    def standard_error(
        self,
        theta: float,
        difficulty: float,
        discrimination: float,
        guessing: float,
    ) -> float:
        """Standart hata: SE(theta) = 1 / sqrt(I(theta)).

        Args:
            theta: Ogrenci yetenek parametresi.
            difficulty: Madde zorluk parametresi (b).
            discrimination: Madde ayirt edicilik parametresi (a).
            guessing: Sansli tahmin parametresi (c).

        Returns:
            Standart hata (>= 0).
        """
        info = self.information(theta, difficulty, discrimination, guessing)
        if info <= 0:
            return float("inf")
        return 1.0 / math.sqrt(info)

    def validate_params(
        self,
        difficulty: float,
        discrimination: float,
        guessing: float,
    ) -> tuple[bool, list[str]]:
        """IRT parametrelerini dogrula.

        Args:
            difficulty: Madde zorluk parametresi (b).
            discrimination: Madde ayirt edicilik parametresi (a).
            guessing: Sansli tahmin parametresi (c).

        Returns:
            (gecerli_mi, hata_listesi) tuple.
        """
        errors: list[str] = []
        d_min, d_max = self.config.difficulty_range
        a_min, a_max = self.config.discrimination_range
        c_min, c_max = self.config.guessing_range

        if not (d_min <= difficulty <= d_max):
            errors.append(f"difficulty {difficulty} aralik disi [{d_min}, {d_max}]")
        if not (a_min <= discrimination <= a_max):
            errors.append(f"discrimination {discrimination} aralik disi [{a_min}, {a_max}]")
        if not (c_min <= guessing <= c_max):
            errors.append(f"guessing {guessing} aralik disi [{c_min}, {c_max}]")

        return len(errors) == 0, errors

    def calculate(
        self,
        theta: float,
        difficulty: float,
        discrimination: float = 1.0,
        guessing: float = 0.2,
        zpd_min: float = 0.15,
        zpd_max: float = 0.85,
    ) -> IRTResult:
        """Tam IRT hesaplamasi: olasilik + bilgi + SE + ZPD kontrolu.

        Args:
            theta: Ogrenci yetenek parametresi.
            difficulty: Madde zorluk parametresi (b).
            discrimination: Madde ayirt edicilik parametresi (a).
            guessing: Sansli tahmin parametresi (c).
            zpd_min: ZPD alt sinir.
            zpd_max: ZPD ust sinir.

        Returns:
            IRTResult with all computed values.
        """
        prob = self.probability_3pl(theta, difficulty, discrimination, guessing)
        info = self.information(theta, difficulty, discrimination, guessing)
        se = self.standard_error(theta, difficulty, discrimination, guessing)

        is_optimal = zpd_min <= prob <= zpd_max
        if prob < zpd_min:
            zpd_status = "cok_zor"
        elif prob > zpd_max:
            zpd_status = "cok_kolay"
        else:
            zpd_status = "optimal"

        return IRTResult(
            probability=prob,
            information=info,
            standard_error=se,
            is_zpd_optimal=is_optimal,
            zpd_status=zpd_status,
        )

    def find_optimal_difficulty(
        self,
        theta: float,
        discrimination: float = 1.0,
        guessing: float = 0.2,
        target_probability: float = 0.5,
    ) -> float:
        """Hedef basari olasiligi icin optimal zorluk bul (bisection).

        Args:
            theta: Ogrenci yetenek parametresi.
            discrimination: Madde ayirt edicilik parametresi (a).
            guessing: Sansli tahmin parametresi (c).
            target_probability: Hedef basari olasiligi.

        Returns:
            Optimal difficulty parametresi.
        """
        lo, hi = self.config.difficulty_range
        for _ in range(50):
            mid = (lo + hi) / 2
            p = self.probability_3pl(theta, mid, discrimination, guessing)
            if p > target_probability:
                lo = mid
            else:
                hi = mid
        return round((lo + hi) / 2, 3)
