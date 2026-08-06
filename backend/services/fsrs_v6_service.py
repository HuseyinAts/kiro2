"""
FSRS v6 Servisi (fsrs paketi kullanarak)

FAZ-1 Gorev 1.3 — Master Plan v2.0
py-fsrs yerine 'fsrs' paketi kullanilir (pip install fsrs).

Not: Detayli Turkce optimize FSRS icin fsrs_service.py kullanin.
Bu dosya master plan'in gerektirdigi sade fsrs wrapper.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

try:
    from fsrs import Card, Rating, Scheduler

    _FSRS_AVAILABLE = True
except ImportError:
    _FSRS_AVAILABLE = False
    logger.warning("fsrs paketi bulunamadi. pip install fsrs")

SCHEDULER = None
if _FSRS_AVAILABLE:
    SCHEDULER = Scheduler(
        desired_retention=0.90,
        maximum_interval=365,
    )

_RATING_MAP: dict[int, Any] = {}
if _FSRS_AVAILABLE:
    _RATING_MAP = {
        1: Rating.Again,
        2: Rating.Hard,
        3: Rating.Good,
        4: Rating.Easy,
    }


class FSRSService:
    """
    FSRS v6 soru tekrar zamanlama servisi.
    fsrs==6.3.1 paketi ile 3 yeniden yapilmistir.
    """

    @staticmethod
    def first_review(rating_int: int) -> tuple[float, float]:
        """
        Yeni kart icin ilk tekrar.

        Args:
            rating_int: 1=Again, 2=Hard, 3=Good, 4=Easy

        Returns:
            (stability, difficulty) tuple
        """
        if not _FSRS_AVAILABLE or SCHEDULER is None:
            return 2.3, 5.0

        rating = _RATING_MAP.get(rating_int, Rating.Good)
        card = Card()
        card, _ = SCHEDULER.review_card(card, rating)
        return card.stability, card.difficulty

    @staticmethod
    def review_card(
        stability: float | None,
        difficulty: float | None,
        due_date: datetime | None,
        rating_int: int,
        reps: int,
    ) -> dict[str, Any]:
        """
        Mevcut karti guncelle ve sonraki tekrar tarihini hesapla.

        Args:
            stability: Mevcut kart stabilitesi (None ise yeni kart)
            difficulty: Mevcut kart zorlugu (None ise yeni kart)
            due_date: Mevcut bitis tarihi (None ise simdi)
            rating_int: 1=Again, 2=Hard, 3=Good, 4=Easy
            reps: Tekrar sayisi

        Returns:
            {
                "stability": float,
                "difficulty": float,
                "due_date": datetime,
                "state": str,
                "reps": int,
                "lapses": int,
            }
        """
        if not _FSRS_AVAILABLE or SCHEDULER is None:
            # Fallback: kaba hesaplama
            days = {1: 1, 2: 3, 3: 7, 4: 14}.get(rating_int, 7)
            return {
                "stability": stability or 2.3,
                "difficulty": difficulty or 5.0,
                "due_date": datetime.now(UTC).replace(
                    hour=0, minute=0, second=0, microsecond=0
                ),
                "state": "review",
                "reps": reps + 1,
                "lapses": 0,
            }

        rating = _RATING_MAP.get(rating_int, Rating.Good)
        card = Card()

        # Mevcut kart durumunu restore et
        if stability is not None and stability > 0:
            card.stability = stability
        if difficulty is not None and difficulty > 0:
            card.difficulty = difficulty
        if due_date is not None:
            card.due = due_date
        # step: learning adımı (0=yeni kart, 1=ilk adım tamamlandı, sonrası Review'a geçer)
        # reps DB kolonunu step proxy olarak kullan — 2+ reps = Review state'e geçmiş kart
        card.step = min(reps, 1)

        card, _ = SCHEDULER.review_card(card, rating)

        return {
            "stability": card.stability,
            "difficulty": card.difficulty,
            "due_date": card.due,
            "state": card.state.name.lower(),
            "reps": card.step,  # step = learning adım sayacı (reps proxy)
            "lapses": 0,  # fsrs kütüphanesi lapses takip etmiyor
        }

    @staticmethod
    def retrievability(stability: float, days_elapsed: float) -> float:
        """
        Hatirlanabilirlik hesapla: R = (1 + days/S/9)^(-1)

        Args:
            stability: Kart stabilitesi (gun cinsinden)
            days_elapsed: Gecen gun sayisi

        Returns:
            Hatirlanabilirlik [0.0, 1.0]
        """
        if stability <= 0:
            return 0.0
        w20 = 0.1542
        factor = 0.9 ** (-1.0 / w20) - 1
        return (1 + factor * days_elapsed / stability) ** (-w20)

    @staticmethod
    def next_interval(stability: float) -> float:
        """
        Sonraki tekrar araliklarini hesapla (gun).

        Args:
            stability: Kart stabilitesi

        Returns:
            Gun sayisi (minimum 1)
        """
        w20 = 0.1542
        factor = 0.9 ** (-1.0 / w20) - 1
        return max(1, stability / factor * (0.9 ** (-1.0 / w20) - 1))
