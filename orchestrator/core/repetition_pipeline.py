"""FSRS Repetition Pipeline - Aralıklı tekrar zamanlaması.

FSRS 4.5 tabanlı tekrar zamanlaması orkestrasyon katmanı:
- Kart durumu yönetimi (new → learning → review → relearning)
- Stability ve retrievability hesaplama
- Kültürel faktör düzeltmeleri (Ramazan, sınav dönemi, tatil)
- Günlük çalışma oturumu planlama
- Tekrar istatistikleri ve ilerleme takibi
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class CardState(Enum):
    """Kart durumları."""

    NEW = "new"
    LEARNING = "learning"
    REVIEW = "review"
    RELEARNING = "relearning"


class ReviewGrade(Enum):
    """Tekrar değerlendirme notları."""

    AGAIN = 1   # Başarısız, tekrar et
    HARD = 2    # Zorlandı
    GOOD = 3    # Başarılı
    EASY = 4    # Çok kolay


class CulturalPeriod(Enum):
    """Türk eğitim takvimi dönemleri."""

    NORMAL = "normal"
    RAMADAN = "ramadan"
    EXAM_SEASON = "exam_season"         # YKS dönemi (Haziran)
    SUMMER_BREAK = "summer_break"       # Yaz tatili
    WINTER_BREAK = "winter_break"       # Kış tatili (Sömestr)
    MIDTERM = "midterm"                 # Ara sınav
    RELIGIOUS_HOLIDAY = "religious_holiday"


# Kültürel dönem çarpanları (unutma hızı ayarı)
CULTURAL_MULTIPLIERS: dict[str, float] = {
    "normal": 1.0,
    "ramadan": 0.75,
    "exam_season": 1.35,
    "summer_break": 0.60,
    "winter_break": 0.70,
    "midterm": 1.20,
    "religious_holiday": 0.80,
}


@dataclass
class RepetitionCard:
    """Tekrar kartı."""

    card_id: str
    question_id: str
    student_id: str
    subject: str
    topic: str
    state: CardState = CardState.NEW
    difficulty: float = 5.0          # [1.0, 10.0] - FSRS difficulty
    stability: float = 0.0          # Hafıza kararlılığı (gün)
    retrievability: float = 1.0     # Hatırlama olasılığı [0, 1]
    elapsed_days: int = 0           # Son tekrardan bu yana geçen gün
    scheduled_days: int = 0         # Planlanan interval (gün)
    review_count: int = 0
    lapse_count: int = 0            # Başarısızlık sayısı
    last_review: str = ""
    due_date: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "card_id": self.card_id,
            "question_id": self.question_id,
            "student_id": self.student_id,
            "subject": self.subject,
            "topic": self.topic,
            "state": self.state.value,
            "difficulty": round(self.difficulty, 4),
            "stability": round(self.stability, 4),
            "retrievability": round(self.retrievability, 4),
            "elapsed_days": self.elapsed_days,
            "scheduled_days": self.scheduled_days,
            "review_count": self.review_count,
            "lapse_count": self.lapse_count,
            "due_date": self.due_date,
        }


@dataclass
class ReviewResult:
    """Bir tekrar sonucu."""

    card_id: str
    grade: ReviewGrade
    new_state: CardState = CardState.REVIEW
    new_stability: float = 0.0
    new_difficulty: float = 5.0
    new_interval_days: int = 1
    retrievability_before: float = 1.0
    cultural_multiplier: float = 1.0


@dataclass
class StudySession:
    """Günlük çalışma oturumu."""

    student_id: str
    date: str
    new_cards: list[RepetitionCard] = field(default_factory=list)
    review_cards: list[RepetitionCard] = field(default_factory=list)
    total_new: int = 0
    total_review: int = 0
    completed_new: int = 0
    completed_review: int = 0
    avg_retrievability: float = 0.0
    estimated_time_minutes: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "student_id": self.student_id,
            "date": self.date,
            "total_new": self.total_new,
            "total_review": self.total_review,
            "completed_new": self.completed_new,
            "completed_review": self.completed_review,
            "avg_retrievability": round(self.avg_retrievability, 3),
            "estimated_time_minutes": round(self.estimated_time_minutes, 1),
        }


@dataclass
class RepetitionStats:
    """Tekrar istatistikleri."""

    student_id: str
    total_cards: int = 0
    mature_cards: int = 0           # stability > 21 gün
    learning_cards: int = 0
    new_cards: int = 0
    avg_stability: float = 0.0
    avg_retrievability: float = 0.0
    retention_rate: float = 0.0     # Son 7 gün başarı oranı
    daily_review_load: int = 0      # Bugün tekrar edilecek kart sayısı
    streak_days: int = 0
    subject_breakdown: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "student_id": self.student_id,
            "total_cards": self.total_cards,
            "mature_cards": self.mature_cards,
            "learning_cards": self.learning_cards,
            "new_cards": self.new_cards,
            "avg_stability": round(self.avg_stability, 2),
            "avg_retrievability": round(self.avg_retrievability, 3),
            "retention_rate": round(self.retention_rate, 3),
            "daily_review_load": self.daily_review_load,
            "streak_days": self.streak_days,
            "subject_breakdown": self.subject_breakdown,
        }


@dataclass
class RepetitionConfig:
    """Pipeline konfigürasyonu."""

    # FSRS 4.5 parametreleri (Türk öğrenci verilerinden optimize edilmiş)
    w: list[float] = field(default_factory=lambda: [
        0.4072, 0.7186, 2.4063, 5.8145,  # w0-w3: initial stability
        4.9347, 0.9372, 0.8640, 0.0124,   # w4-w7: penalty/bonus
        1.4923, 0.1435, 0.9421, 2.1847,   # w8-w11: study factors
        0.0532, 0.3428, 1.2634, 0.2917,   # w12-w15: retention
        2.6158,                             # w16: overdue
    ])

    target_retention: float = 0.85       # Hedef hatırlama oranı
    max_interval_days: int = 365         # Maksimum interval
    max_new_cards_per_day: int = 20
    max_review_cards_per_day: int = 100
    minutes_per_new_card: float = 3.0
    minutes_per_review_card: float = 1.5
    mature_threshold_days: int = 21      # Bu üstü = olgun kart
    leech_threshold: int = 8             # Bu kadar lapse = leech


@dataclass
class RepetitionPipeline:
    """FSRS tabanlı aralıklı tekrar pipeline'ı.

    Tekrar zamanlaması orkestre eder:
    review → stability güncelle → interval hesapla → kültürel düzelt → planla.

    Example:
        >>> pipeline = RepetitionPipeline()
        >>> card = RepetitionCard(card_id="C1", question_id="Q1", student_id="S1",
        ...                       subject="Matematik", topic="Limit")
        >>> result = pipeline.review(card, ReviewGrade.GOOD)
        >>> print(card.scheduled_days, card.state)
    """

    config: RepetitionConfig = field(default_factory=RepetitionConfig)

    def review(
        self,
        card: RepetitionCard,
        grade: ReviewGrade,
        cultural_period: CulturalPeriod = CulturalPeriod.NORMAL,
    ) -> ReviewResult:
        """Kartı tekrar et ve zamanlamayı güncelle.

        Args:
            card: Tekrar edilecek kart.
            grade: Değerlendirme notu (AGAIN/HARD/GOOD/EASY).
            cultural_period: Mevcut kültürel dönem.

        Returns:
            ReviewResult with updated scheduling info.
        """
        result = ReviewResult(
            card_id=card.card_id,
            grade=grade,
            retrievability_before=card.retrievability,
        )

        # Kültürel çarpan
        multiplier = CULTURAL_MULTIPLIERS.get(cultural_period.value, 1.0)
        result.cultural_multiplier = multiplier

        # 1. Difficulty güncelle
        new_diff = self._update_difficulty(card.difficulty, grade)
        card.difficulty = new_diff
        result.new_difficulty = new_diff

        # 2. Stability güncelle
        if card.state == CardState.NEW:
            new_stability = self._initial_stability(grade)
        elif grade == ReviewGrade.AGAIN:
            new_stability = self._stability_after_failure(card)
        else:
            new_stability = self._stability_after_success(card, grade)

        # Kültürel düzeltme
        new_stability *= multiplier
        new_stability = max(0.1, new_stability)
        card.stability = new_stability
        result.new_stability = new_stability

        # 3. Interval hesapla
        interval = self._calculate_interval(new_stability)
        interval = min(interval, self.config.max_interval_days)
        interval = max(1, interval)
        card.scheduled_days = interval
        result.new_interval_days = interval

        # 4. Durum geçişi
        new_state = self._transition_state(card.state, grade)
        card.state = new_state
        result.new_state = new_state

        # 5. Kartı güncelle
        card.review_count += 1
        card.elapsed_days = 0
        card.retrievability = 1.0
        card.last_review = datetime.now(timezone.utc).isoformat()
        if grade == ReviewGrade.AGAIN:
            card.lapse_count += 1

        return result

    def calculate_retrievability(self, card: RepetitionCard, elapsed_days: int = 0) -> float:
        """Kartın mevcut retrievability değerini hesapla.

        FSRS formülü: R = (1 + elapsed / (9 * stability))^(-1)

        Args:
            card: Kart.
            elapsed_days: Geçen gün sayısı (0 = kart bilgisinden al).

        Returns:
            Retrievability [0, 1].
        """
        days = elapsed_days if elapsed_days > 0 else card.elapsed_days
        if card.stability <= 0:
            return 0.0
        return (1 + days / (9 * card.stability)) ** (-1)

    def plan_session(
        self,
        cards: list[RepetitionCard],
        student_id: str,
    ) -> StudySession:
        """Günlük çalışma oturumu planla.

        Args:
            cards: Öğrencinin tüm kartları.
            student_id: Öğrenci ID.

        Returns:
            StudySession with prioritized cards.
        """
        today = datetime.now(timezone.utc).date().isoformat()
        session = StudySession(student_id=student_id, date=today)

        new_cards: list[RepetitionCard] = []
        due_cards: list[RepetitionCard] = []

        for card in cards:
            if card.student_id != student_id:
                continue
            if card.state == CardState.NEW:
                new_cards.append(card)
            else:
                # Retrievability hesapla
                r = self.calculate_retrievability(card)
                card.retrievability = r
                if r < self.config.target_retention:
                    due_cards.append(card)

        # Sırala: en düşük retrievability önce
        due_cards.sort(key=lambda c: c.retrievability)

        session.new_cards = new_cards[: self.config.max_new_cards_per_day]
        session.review_cards = due_cards[: self.config.max_review_cards_per_day]
        session.total_new = len(session.new_cards)
        session.total_review = len(session.review_cards)

        # Tahmini süre
        session.estimated_time_minutes = (
            session.total_new * self.config.minutes_per_new_card
            + session.total_review * self.config.minutes_per_review_card
        )

        # Ortalama retrievability
        if session.review_cards:
            session.avg_retrievability = sum(
                c.retrievability for c in session.review_cards
            ) / len(session.review_cards)

        return session

    def get_stats(self, cards: list[RepetitionCard], student_id: str) -> RepetitionStats:
        """Öğrenci tekrar istatistiklerini hesapla.

        Args:
            cards: Tüm kartlar.
            student_id: Öğrenci ID.

        Returns:
            RepetitionStats.
        """
        stats = RepetitionStats(student_id=student_id)
        student_cards = [c for c in cards if c.student_id == student_id]
        stats.total_cards = len(student_cards)

        subject_data: dict[str, dict[str, Any]] = {}

        for card in student_cards:
            # Durum sayıları
            if card.state == CardState.NEW:
                stats.new_cards += 1
            elif card.stability >= self.config.mature_threshold_days:
                stats.mature_cards += 1
            else:
                stats.learning_cards += 1

            # Retrievability güncelle
            r = self.calculate_retrievability(card)

            # Konu bazlı
            subj = card.subject
            if subj not in subject_data:
                subject_data[subj] = {"total": 0, "mature": 0, "avg_stability": 0.0}
            subject_data[subj]["total"] += 1
            subject_data[subj]["avg_stability"] += card.stability
            if card.stability >= self.config.mature_threshold_days:
                subject_data[subj]["mature"] += 1

            # Due kontrolü
            if card.state != CardState.NEW and r < self.config.target_retention:
                stats.daily_review_load += 1

        # Ortalamalar
        reviewed = [c for c in student_cards if c.state != CardState.NEW]
        if reviewed:
            stats.avg_stability = sum(c.stability for c in reviewed) / len(reviewed)
            stats.avg_retrievability = sum(
                self.calculate_retrievability(c) for c in reviewed
            ) / len(reviewed)

        # Konu breakdown
        for subj, data in subject_data.items():
            total = data["total"]
            subject_data[subj]["avg_stability"] = round(data["avg_stability"] / max(total, 1), 2)
        stats.subject_breakdown = subject_data

        return stats

    # --- FSRS Core Calculations ---

    def _initial_stability(self, grade: ReviewGrade) -> float:
        """İlk tekrar sonrası stability (w0-w3)."""
        w = self.config.w
        idx = grade.value - 1  # 0, 1, 2, 3
        return max(0.1, w[idx])

    def _update_difficulty(self, current: float, grade: ReviewGrade) -> float:
        """Difficulty güncelle (FSRS formülü)."""
        w = self.config.w
        # D' = D - w6 * (grade - 3)
        new_diff = current - w[6] * (grade.value - 3)
        # Mean reversion: D = w5 * D_init + (1 - w5) * D'
        d_init = w[4] - math.exp(w[5] * (grade.value - 1)) + 1
        new_diff = w[6] * d_init + (1 - w[6]) * new_diff
        return max(1.0, min(10.0, new_diff))

    def _stability_after_success(
        self, card: RepetitionCard, grade: ReviewGrade,
    ) -> float:
        """Başarılı tekrar sonrası yeni stability."""
        w = self.config.w
        d = card.difficulty
        s = card.stability
        r = self.calculate_retrievability(card)

        # S' = S * (1 + exp(w8) * (11 - D) * S^(-w9) * (exp(w10 * (1 - R)) - 1))
        new_s = s * (
            1 + math.exp(w[8])
            * (11 - d)
            * s ** (-w[9])
            * (math.exp(w[10] * (1 - r)) - 1)
        )

        # Grade bonusu
        if grade == ReviewGrade.HARD:
            new_s *= w[14]
        elif grade == ReviewGrade.EASY:
            new_s *= w[15]

        return max(0.1, new_s)

    def _stability_after_failure(self, card: RepetitionCard) -> float:
        """Başarısız tekrar sonrası yeni stability."""
        w = self.config.w
        d = card.difficulty
        s = card.stability
        r = self.calculate_retrievability(card)

        # S' = w11 * D^(-w12) * ((S+1)^w13 - 1) * exp(w14 * (1 - R))
        new_s = (
            w[11]
            * d ** (-w[12])
            * ((s + 1) ** w[13] - 1)
            * math.exp(w[14] * (1 - r))
        )
        return max(0.1, min(new_s, s))  # Asla eski stability'den fazla olmamalı

    def _calculate_interval(self, stability: float) -> int:
        """Stability'den interval hesapla.

        I = 9 * S * (1/R - 1) where R = target_retention.
        """
        r = self.config.target_retention
        if r >= 1.0 or r <= 0.0:
            return 1
        interval = 9 * stability * (1 / r - 1)
        return max(1, round(interval))

    def _transition_state(self, current: CardState, grade: ReviewGrade) -> CardState:
        """Kart durumu geçişi."""
        if grade == ReviewGrade.AGAIN:
            if current in (CardState.REVIEW, CardState.RELEARNING):
                return CardState.RELEARNING
            return CardState.LEARNING
        if current in (CardState.NEW, CardState.LEARNING, CardState.RELEARNING):
            if grade == ReviewGrade.EASY:
                return CardState.REVIEW
            return CardState.LEARNING if grade == ReviewGrade.HARD else CardState.REVIEW
        return CardState.REVIEW
