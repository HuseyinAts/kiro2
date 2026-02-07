"""kiro2-yks Plugin - YKS soru uretim ve analiz araclari.

Bu plugin IRT hesaplama, ZPD analizi ve FSRS tekrar zamanlama
toollarini saglar.
"""

from __future__ import annotations

from typing import Any

from .tools import (
    IRTCalculator,
    ZPDAnalyzer,
    FSRSScheduler,
    CardData,
    Rating,
)


class KiroYKSPlugin:
    """KIRO2 YKS Plugin ana sinifi."""

    def __init__(self) -> None:
        self.irt = IRTCalculator()
        self.zpd = ZPDAnalyzer()
        self.fsrs = FSRSScheduler()

    def calculate_irt(
        self,
        theta: float,
        difficulty: float,
        discrimination: float = 1.0,
        guessing: float = 0.2,
    ) -> dict[str, Any]:
        """IRT hesapla ve ZPD kontrolu yap."""
        result = self.irt.calculate(theta, difficulty, discrimination, guessing)
        return result.to_dict()

    def analyze_zpd(self, theta: float) -> dict[str, Any]:
        """Ogrenci icin ZPD bolgesi hesapla."""
        zone = self.zpd.calculate_zpd(theta)
        ladder = self.zpd.suggest_difficulty_ladder(theta)
        return {
            "zone": zone.to_dict(),
            "ladder": ladder,
        }

    def schedule_review(
        self,
        card_id: str,
        rating: int,
        stability: float = 0.0,
        difficulty: float = 5.0,
        elapsed_days: int = 0,
        reps: int = 0,
    ) -> dict[str, Any]:
        """FSRS tekrar zamanlama."""
        from .tools.fsrs_scheduler import CardState

        state = CardState.NEW if reps == 0 else CardState.REVIEW
        card = CardData(
            card_id=card_id,
            state=state,
            stability=stability,
            difficulty=difficulty,
            elapsed_days=elapsed_days,
            reps=reps,
        )
        result = self.fsrs.review(card, Rating(rating))
        return {
            "schedule": result.to_dict(),
            "card": card.to_dict(),
        }
