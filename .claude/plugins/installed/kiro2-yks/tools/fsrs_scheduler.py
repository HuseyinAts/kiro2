"""FSRS Scheduler - Free Spaced Repetition Scheduler.

FSRS v4 algoritmasi:
- Stability (hafiza gucu) guncelleme
- Difficulty guncelleme
- Tekrar araligi hesaplama
- Geri cagirilabilirlik (retrievability) hesabi

Referans: https://github.com/open-spaced-repetition/fsrs4anki
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import IntEnum
from typing import Any


class Rating(IntEnum):
    """Kullanici degerlendirme notlari."""

    AGAIN = 1   # Hatirlanmadi
    HARD = 2    # Zor hatirlanma
    GOOD = 3    # Normal hatirlanma
    EASY = 4    # Kolay hatirlanma


class CardState(IntEnum):
    """Kart durumlari."""

    NEW = 0
    LEARNING = 1
    REVIEW = 2
    RELEARNING = 3


@dataclass
class FSRSConfig:
    """FSRS konfigurasyonu."""

    # FSRS v4 default weights
    w: list[float] = field(default_factory=lambda: [
        0.4, 0.6, 2.4, 5.8,   # initial stability per rating
        4.93, 0.94, 0.86, 0.01,  # difficulty
        1.49, 0.14, 0.94,       # stability after success
        2.18, 0.05, 0.34, 1.26,  # stability after fail
        0.29, 2.61,              # hard/easy penalty/bonus
    ])
    desired_retention: float = 0.9   # Hedef geri cagirilabilirlik
    maximum_interval: int = 3650     # Maksimum gun (10 yil)
    difficulty_range: tuple[float, float] = (1.0, 10.0)


@dataclass
class CardData:
    """Kart verisi."""

    card_id: str
    state: CardState = CardState.NEW
    difficulty: float = 5.0
    stability: float = 0.0
    elapsed_days: int = 0
    scheduled_days: int = 0
    reps: int = 0
    lapses: int = 0
    last_review: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "card_id": self.card_id,
            "state": self.state.name.lower(),
            "difficulty": round(self.difficulty, 2),
            "stability": round(self.stability, 2),
            "elapsed_days": self.elapsed_days,
            "scheduled_days": self.scheduled_days,
            "reps": self.reps,
            "lapses": self.lapses,
            "last_review": self.last_review.isoformat() if self.last_review else None,
        }


@dataclass
class ScheduleResult:
    """Zamanlama sonucu."""

    rating: Rating
    scheduled_days: int
    new_stability: float
    new_difficulty: float
    new_state: CardState
    retrievability: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "rating": self.rating.name.lower(),
            "scheduled_days": self.scheduled_days,
            "new_stability": round(self.new_stability, 2),
            "new_difficulty": round(self.new_difficulty, 2),
            "new_state": self.new_state.name.lower(),
            "retrievability": round(self.retrievability, 4),
        }


class FSRSScheduler:
    """FSRS v4 tekrar zamanlama motoru.

    Example:
        >>> scheduler = FSRSScheduler()
        >>> card = CardData(card_id="Q001")
        >>> result = scheduler.review(card, Rating.GOOD)
        >>> print(result.scheduled_days)  # 1 (yeni kart)
    """

    def __init__(self, config: FSRSConfig | None = None) -> None:
        self.config = config or FSRSConfig()
        self.w = self.config.w

    def review(self, card: CardData, rating: Rating) -> ScheduleResult:
        """Karti degerlendirip yeni zamanlama hesapla.

        Args:
            card: Mevcut kart verisi.
            rating: Kullanici degerlendirmesi (1-4).

        Returns:
            ScheduleResult with updated card parameters.
        """
        now = datetime.now(timezone.utc)

        if card.state == CardState.NEW:
            return self._review_new(card, rating, now)
        else:
            return self._review_existing(card, rating, now)

    def _review_new(
        self, card: CardData, rating: Rating, now: datetime,
    ) -> ScheduleResult:
        """Yeni kart icin ilk degerlendirme."""
        # Initial stability from weights
        s = self.w[rating.value - 1]
        d = self._init_difficulty(rating)

        interval = self._next_interval(s)
        new_state = CardState.LEARNING if rating == Rating.AGAIN else CardState.REVIEW

        card.stability = s
        card.difficulty = d
        card.state = new_state
        card.scheduled_days = interval
        card.reps = 1
        card.last_review = now
        if rating == Rating.AGAIN:
            card.lapses += 1

        return ScheduleResult(
            rating=rating,
            scheduled_days=interval,
            new_stability=s,
            new_difficulty=d,
            new_state=new_state,
            retrievability=1.0,
        )

    def _review_existing(
        self, card: CardData, rating: Rating, now: datetime,
    ) -> ScheduleResult:
        """Mevcut kart icin degerlendirme."""
        r = self.retrievability(card.stability, card.elapsed_days)

        if rating == Rating.AGAIN:
            new_s = self._stability_after_fail(card.difficulty, card.stability, r)
            new_state = CardState.RELEARNING
            card.lapses += 1
        else:
            new_s = self._stability_after_success(
                card.difficulty, card.stability, r, rating,
            )
            new_state = CardState.REVIEW

        new_d = self._next_difficulty(card.difficulty, rating)
        interval = self._next_interval(new_s)

        card.stability = new_s
        card.difficulty = new_d
        card.state = new_state
        card.scheduled_days = interval
        card.reps += 1
        card.last_review = now

        return ScheduleResult(
            rating=rating,
            scheduled_days=interval,
            new_stability=new_s,
            new_difficulty=new_d,
            new_state=new_state,
            retrievability=r,
        )

    def retrievability(self, stability: float, elapsed_days: int) -> float:
        """Geri cagirilabilirlik: R(t) = (1 + t / (9 * S))^(-1).

        Args:
            stability: Kart kararliligi.
            elapsed_days: Son tekrardan bu yana gecen gun.

        Returns:
            Geri cagirilabilirlik [0, 1].
        """
        if stability <= 0:
            return 0.0
        if elapsed_days <= 0:
            return 1.0
        return (1.0 + elapsed_days / (9.0 * stability)) ** -1

    def _next_interval(self, stability: float) -> int:
        """Hedef retention icin sonraki tekrar araligi.

        interval = S * (R^(-1) - 1) * 9

        Args:
            stability: Kart kararliligi.

        Returns:
            Gun cinsinden aralik.
        """
        r = self.config.desired_retention
        if r <= 0 or r >= 1:
            return 1
        interval = stability * 9.0 * (1.0 / r - 1.0)
        interval = max(1, min(int(round(interval)), self.config.maximum_interval))
        return interval

    def _init_difficulty(self, rating: Rating) -> float:
        """Yeni kart icin baslangic zorlugu."""
        d = self.w[4] - (rating.value - 3) * self.w[5]
        return self._clamp_difficulty(d)

    def _next_difficulty(self, d: float, rating: Rating) -> float:
        """Zorluk guncelleme: mean reversion ile."""
        delta = -(rating.value - 3) * self.w[6]
        new_d = d + delta
        # Mean reversion towards w[4]
        new_d = self.w[7] * self.w[4] + (1.0 - self.w[7]) * new_d
        return self._clamp_difficulty(new_d)

    def _stability_after_success(
        self, d: float, s: float, r: float, rating: Rating,
    ) -> float:
        """Basarili tekrar sonrasi stability."""
        new_s = s * (
            1.0
            + math.exp(self.w[8])
            * (11.0 - d)
            * s ** (-self.w[9])
            * (math.exp((1.0 - r) * self.w[10]) - 1.0)
        )
        # Hard/Easy modifiers
        if rating == Rating.HARD:
            new_s *= self.w[15]
        elif rating == Rating.EASY:
            new_s *= self.w[16]

        return max(0.1, new_s)

    def _stability_after_fail(self, d: float, s: float, r: float) -> float:
        """Basarisiz tekrar sonrasi stability."""
        new_s = (
            self.w[11]
            * d ** (-self.w[12])
            * ((s + 1.0) ** self.w[13] - 1.0)
            * math.exp((1.0 - r) * self.w[14])
        )
        return max(0.1, min(new_s, s))  # Fail sonrasi s artamaz

    def _clamp_difficulty(self, d: float) -> float:
        """Zorlugu araliga sinirla."""
        lo, hi = self.config.difficulty_range
        return max(lo, min(hi, round(d, 2)))

    def schedule_all_ratings(self, card: CardData) -> dict[str, ScheduleResult]:
        """Tum degerlendirmeler icin olasi sonuclari hesapla.

        Args:
            card: Mevcut kart verisi.

        Returns:
            {rating_name: ScheduleResult} dict.
        """
        import copy

        results: dict[str, ScheduleResult] = {}
        for rating in Rating:
            card_copy = copy.deepcopy(card)
            result = self.review(card_copy, rating)
            results[rating.name.lower()] = result
        return results
