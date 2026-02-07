"""ZPD Analyzer - Zone of Proximal Development analizi.

Ogrenci yetenek seviyesine gore:
- Optimal zorluk araligi hesaplama
- Soru-ogrenci eslestirme
- Zorluk kademesi onerme
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from .irt_calculator import IRTCalculator


@dataclass
class ZPDZone:
    """ZPD bolge tanimlari."""

    lower_difficulty: float  # Kolay sinir
    upper_difficulty: float  # Zor sinir
    optimal_difficulty: float  # %50 basari noktasi
    theta: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "lower_difficulty": round(self.lower_difficulty, 3),
            "upper_difficulty": round(self.upper_difficulty, 3),
            "optimal_difficulty": round(self.optimal_difficulty, 3),
            "theta": round(self.theta, 3),
        }


@dataclass
class QuestionFit:
    """Bir sorunun ogrenci icin uygunluk analizi."""

    question_id: str
    difficulty: float
    probability: float
    information: float
    zpd_status: str  # "cok_kolay" | "optimal" | "cok_zor"
    fit_score: float  # 0-1, 1=mukemmel eslesme

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "difficulty": round(self.difficulty, 3),
            "probability": round(self.probability, 4),
            "information": round(self.information, 4),
            "zpd_status": self.zpd_status,
            "fit_score": round(self.fit_score, 3),
        }


@dataclass
class ZPDConfig:
    """ZPD konfigurasyonu."""

    optimal_min: float = 0.15   # Alt sinir basari olasiligi
    optimal_max: float = 0.85   # Ust sinir basari olasiligi
    target_probability: float = 0.50  # Ideal basari olasiligi
    discrimination_default: float = 1.0
    guessing_default: float = 0.2


class ZPDAnalyzer:
    """ZPD analizi ve soru-ogrenci eslestirme.

    Example:
        >>> analyzer = ZPDAnalyzer()
        >>> zone = analyzer.calculate_zpd(theta=1.0)
        >>> print(zone.optimal_difficulty)  # ~1.0
    """

    def __init__(self, config: ZPDConfig | None = None) -> None:
        self.config = config or ZPDConfig()
        self._irt = IRTCalculator()

    def calculate_zpd(
        self,
        theta: float,
        discrimination: float | None = None,
        guessing: float | None = None,
    ) -> ZPDZone:
        """Ogrenci icin ZPD bolgesi hesapla.

        Args:
            theta: Ogrenci yetenek parametresi.
            discrimination: Ayirt edicilik (default config'den).
            guessing: Sansli tahmin (default config'den).

        Returns:
            ZPDZone with difficulty bounds.
        """
        a = discrimination or self.config.discrimination_default
        c = guessing or self.config.guessing_default

        lower = self._irt.find_optimal_difficulty(
            theta, a, c, target_probability=self.config.optimal_max,
        )
        upper = self._irt.find_optimal_difficulty(
            theta, a, c, target_probability=self.config.optimal_min,
        )
        optimal = self._irt.find_optimal_difficulty(
            theta, a, c, target_probability=self.config.target_probability,
        )

        return ZPDZone(
            lower_difficulty=lower,
            upper_difficulty=upper,
            optimal_difficulty=optimal,
            theta=theta,
        )

    def analyze_question_fit(
        self,
        theta: float,
        question_id: str,
        difficulty: float,
        discrimination: float | None = None,
        guessing: float | None = None,
    ) -> QuestionFit:
        """Bir sorunun ogrenci ZPD'sine uygunlugunu analiz et.

        Args:
            theta: Ogrenci yetenek parametresi.
            question_id: Soru kimlik numarasi.
            difficulty: Soru zorluk parametresi.
            discrimination: Ayirt edicilik.
            guessing: Sansli tahmin.

        Returns:
            QuestionFit with compatibility analysis.
        """
        a = discrimination or self.config.discrimination_default
        c = guessing or self.config.guessing_default

        result = self._irt.calculate(
            theta, difficulty, a, c,
            zpd_min=self.config.optimal_min,
            zpd_max=self.config.optimal_max,
        )

        # Fit score: 1.0 = tam optimal, azalir uzaklastikca
        distance = abs(result.probability - self.config.target_probability)
        max_distance = max(
            self.config.target_probability - 0.0,
            1.0 - self.config.target_probability,
        )
        fit_score = max(0.0, 1.0 - distance / max_distance)

        return QuestionFit(
            question_id=question_id,
            difficulty=difficulty,
            probability=result.probability,
            information=result.information,
            zpd_status=result.zpd_status,
            fit_score=fit_score,
        )

    def rank_questions(
        self,
        theta: float,
        questions: list[dict[str, Any]],
        top_k: int = 10,
    ) -> list[QuestionFit]:
        """Soru listesini ZPD uygunluguna gore sirala.

        Args:
            theta: Ogrenci yetenek parametresi.
            questions: [{"question_id": str, "difficulty": float, ...}] listesi.
            top_k: En uygun kac soru donecek.

        Returns:
            Fit score'a gore sirali QuestionFit listesi.
        """
        fits: list[QuestionFit] = []
        for q in questions:
            fit = self.analyze_question_fit(
                theta=theta,
                question_id=q["question_id"],
                difficulty=q["difficulty"],
                discrimination=q.get("discrimination"),
                guessing=q.get("guessing"),
            )
            fits.append(fit)

        fits.sort(key=lambda f: f.fit_score, reverse=True)
        return fits[:top_k]

    def suggest_difficulty_ladder(
        self,
        theta: float,
        steps: int = 5,
    ) -> list[dict[str, Any]]:
        """Kademeli zorluk merdiveni oner (scaffold).

        Args:
            theta: Ogrenci yetenek parametresi.
            steps: Kademe sayisi.

        Returns:
            Kolay→zor sirali zorluk onerileri.
        """
        zone = self.calculate_zpd(theta)
        span = zone.upper_difficulty - zone.lower_difficulty
        if span <= 0:
            span = 2.0

        ladder: list[dict[str, Any]] = []
        for i in range(steps):
            ratio = i / max(steps - 1, 1)
            diff = zone.lower_difficulty + ratio * span
            prob = self._irt.probability_3pl(
                theta, diff,
                self.config.discrimination_default,
                self.config.guessing_default,
            )
            ladder.append({
                "step": i + 1,
                "difficulty": round(diff, 3),
                "expected_probability": round(prob, 3),
                "label": self._difficulty_label(prob),
            })
        return ladder

    @staticmethod
    def _difficulty_label(probability: float) -> str:
        """Basari olasiligina gore etiket."""
        if probability >= 0.80:
            return "kolay"
        if probability >= 0.60:
            return "orta-kolay"
        if probability >= 0.40:
            return "orta"
        if probability >= 0.20:
            return "orta-zor"
        return "zor"
