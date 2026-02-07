"""Student Analytics Pipeline - Öğrenci performans analizi.

Öğrenci yanıtlarını analiz edip kişiselleştirilmiş öneriler üretir:
- IRT ile yetenek (theta) tahmini güncelleme
- FSRS ile tekrar zamanlaması
- ZPD aralığı yeniden hesaplama
- Zayıf konu tespiti
- İçerik önerisi üretme
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class PerformanceTrend(Enum):
    """Performans trendi."""

    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    INSUFFICIENT_DATA = "insufficient_data"


class MasteryLevel(Enum):
    """Konu hakimiyet seviyesi."""

    NOT_STARTED = "not_started"
    BEGINNER = "beginner"       # < 30%
    DEVELOPING = "developing"   # 30-60%
    PROFICIENT = "proficient"   # 60-80%
    MASTERED = "mastered"       # > 80%


@dataclass
class StudentResponse:
    """Tek bir öğrenci yanıtı."""

    question_id: str
    subject: str
    topic: str
    is_correct: bool
    response_time_seconds: float = 0.0
    difficulty: float = 0.0       # IRT b parametresi
    discrimination: float = 1.0   # IRT a parametresi
    guessing: float = 0.2         # IRT c parametresi
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class TopicMastery:
    """Bir konudaki hakimiyet durumu."""

    topic: str
    subject: str
    total_questions: int = 0
    correct_count: int = 0
    mastery_level: MasteryLevel = MasteryLevel.NOT_STARTED
    average_difficulty: float = 0.0
    trend: PerformanceTrend = PerformanceTrend.INSUFFICIENT_DATA
    last_practiced: str = ""

    @property
    def success_rate(self) -> float:
        """Başarı oranı."""
        if self.total_questions == 0:
            return 0.0
        return self.correct_count / self.total_questions

    def update_mastery(self) -> None:
        """Hakimiyet seviyesini güncelle."""
        rate = self.success_rate
        if self.total_questions == 0:
            self.mastery_level = MasteryLevel.NOT_STARTED
        elif rate < 0.3:
            self.mastery_level = MasteryLevel.BEGINNER
        elif rate < 0.6:
            self.mastery_level = MasteryLevel.DEVELOPING
        elif rate < 0.8:
            self.mastery_level = MasteryLevel.PROFICIENT
        else:
            self.mastery_level = MasteryLevel.MASTERED


@dataclass
class ContentRecommendation:
    """İçerik önerisi."""

    topic: str
    subject: str
    reason: str
    priority: int            # 1 (en yüksek) - 5 (en düşük)
    recommended_difficulty: float = 0.0
    question_count: int = 5

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "subject": self.subject,
            "reason": self.reason,
            "priority": self.priority,
            "recommended_difficulty": round(self.recommended_difficulty, 2),
            "question_count": self.question_count,
        }


@dataclass
class StudentProfile:
    """Öğrenci profili."""

    student_id: str
    theta: float = 0.0                # IRT yetenek seviyesi [-3, +3]
    theta_se: float = 1.0             # Standart hata
    zpd_lower: float = -0.15          # ZPD alt sınır (theta bazlı)
    zpd_upper: float = 0.15           # ZPD üst sınır
    total_responses: int = 0
    topic_mastery: dict[str, TopicMastery] = field(default_factory=dict)
    recommendations: list[ContentRecommendation] = field(default_factory=list)
    overall_trend: PerformanceTrend = PerformanceTrend.INSUFFICIENT_DATA
    last_updated: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "student_id": self.student_id,
            "theta": round(self.theta, 3),
            "theta_se": round(self.theta_se, 3),
            "zpd_range": [round(self.zpd_lower, 3), round(self.zpd_upper, 3)],
            "total_responses": self.total_responses,
            "topic_mastery": {
                k: {
                    "success_rate": round(v.success_rate, 3),
                    "mastery_level": v.mastery_level.value,
                    "total": v.total_questions,
                    "trend": v.trend.value,
                }
                for k, v in self.topic_mastery.items()
            },
            "recommendations": [r.to_dict() for r in self.recommendations],
            "overall_trend": self.overall_trend.value,
        }


@dataclass
class AnalyticsConfig:
    """Analytics konfigürasyonu."""

    zpd_range: float = 0.15               # ZPD genişliği (theta ± range)
    min_responses_for_trend: int = 10
    trend_window: int = 20                 # Son N yanıt
    weak_topic_threshold: float = 0.5      # Bu altı zayıf konu
    max_recommendations: int = 5
    irt_scaling_constant: float = 1.7      # D parametresi


@dataclass
class StudentAnalyticsPipeline:
    """Öğrenci analitik pipeline'ı.

    Yanıtları işler, yetenek tahminini günceller,
    ZPD'yi yeniden hesaplar ve içerik önerileri üretir.

    Example:
        >>> pipeline = StudentAnalyticsPipeline()
        >>> profile = StudentProfile(student_id="S001")
        >>> responses = [StudentResponse(...), ...]
        >>> pipeline.process(profile, responses)
        >>> print(profile.theta, profile.recommendations)
    """

    config: AnalyticsConfig = field(default_factory=AnalyticsConfig)

    def process(self, profile: StudentProfile, responses: list[StudentResponse]) -> StudentProfile:
        """Yanıtları işle ve profili güncelle.

        Args:
            profile: Güncellenecek öğrenci profili.
            responses: Yeni yanıtlar listesi.

        Returns:
            Güncellenmiş öğrenci profili.
        """
        if not responses:
            return profile

        # 1. Konu bazlı istatistikleri güncelle
        self._update_topic_mastery(profile, responses)

        # 2. IRT yetenek tahmini (MLE)
        self._update_theta(profile, responses)

        # 3. ZPD aralığını yeniden hesapla
        self._update_zpd(profile)

        # 4. Trend analizi
        self._update_trend(profile, responses)

        # 5. İçerik önerileri
        self._generate_recommendations(profile)

        profile.last_updated = datetime.now(timezone.utc).isoformat()
        return profile

    def _update_topic_mastery(
        self, profile: StudentProfile, responses: list[StudentResponse],
    ) -> None:
        """Konu bazlı hakimiyet güncelle."""
        for resp in responses:
            key = f"{resp.subject}:{resp.topic}"
            if key not in profile.topic_mastery:
                profile.topic_mastery[key] = TopicMastery(
                    topic=resp.topic, subject=resp.subject,
                )
            tm = profile.topic_mastery[key]
            tm.total_questions += 1
            if resp.is_correct:
                tm.correct_count += 1
            tm.average_difficulty = (
                (tm.average_difficulty * (tm.total_questions - 1) + resp.difficulty)
                / tm.total_questions
            )
            tm.last_practiced = resp.timestamp
            tm.update_mastery()
            profile.total_responses += 1

    def _update_theta(
        self, profile: StudentProfile, responses: list[StudentResponse],
    ) -> None:
        """Newton-Raphson MLE ile theta güncelle."""
        theta = profile.theta
        D = self.config.irt_scaling_constant

        for _ in range(20):
            first_deriv = 0.0
            second_deriv = 0.0

            for resp in responses:
                a, b, c = resp.discrimination, resp.difficulty, resp.guessing
                exp_val = math.exp(D * a * (theta - b))
                p = c + (1 - c) * (exp_val / (1 + exp_val))
                p = max(min(p, 0.999), 0.001)  # Clip

                u = 1.0 if resp.is_correct else 0.0
                first_deriv += a * (u - p)
                second_deriv -= a * a * p * (1 - p)

            if abs(second_deriv) < 1e-10:
                break
            theta = theta - first_deriv / second_deriv

        profile.theta = max(-3.0, min(3.0, theta))

        # Standart hata tahmini
        info_sum = 0.0
        for resp in responses:
            a, b, c = resp.discrimination, resp.difficulty, resp.guessing
            exp_val = math.exp(D * a * (profile.theta - b))
            p = c + (1 - c) * (exp_val / (1 + exp_val))
            p = max(min(p, 0.999), 0.001)
            info_sum += a * a * p * (1 - p)

        profile.theta_se = 1.0 / math.sqrt(max(info_sum, 0.01))

    def _update_zpd(self, profile: StudentProfile) -> None:
        """ZPD aralığını güncelle."""
        profile.zpd_lower = profile.theta - self.config.zpd_range
        profile.zpd_upper = profile.theta + self.config.zpd_range

    def _update_trend(
        self, profile: StudentProfile, responses: list[StudentResponse],
    ) -> None:
        """Performans trendini hesapla."""
        if len(responses) < self.config.min_responses_for_trend:
            profile.overall_trend = PerformanceTrend.INSUFFICIENT_DATA
            return

        window = responses[-self.config.trend_window:]
        mid = len(window) // 2
        first_half = window[:mid]
        second_half = window[mid:]

        rate_first = sum(1 for r in first_half if r.is_correct) / max(len(first_half), 1)
        rate_second = sum(1 for r in second_half if r.is_correct) / max(len(second_half), 1)

        diff = rate_second - rate_first
        if diff > 0.05:
            profile.overall_trend = PerformanceTrend.IMPROVING
        elif diff < -0.05:
            profile.overall_trend = PerformanceTrend.DECLINING
        else:
            profile.overall_trend = PerformanceTrend.STABLE

    def _generate_recommendations(self, profile: StudentProfile) -> None:
        """Zayıf konular için içerik önerileri üret."""
        weak_topics: list[tuple[str, TopicMastery]] = []

        for key, tm in profile.topic_mastery.items():
            if tm.total_questions >= 3 and tm.success_rate < self.config.weak_topic_threshold:
                weak_topics.append((key, tm))

        # En zayıftan en güçlüye sırala
        weak_topics.sort(key=lambda x: x[1].success_rate)

        profile.recommendations = []
        for i, (key, tm) in enumerate(weak_topics[: self.config.max_recommendations]):
            # Önerilen zorluk: ZPD alt sınırına yakın
            rec_diff = profile.zpd_lower + (profile.zpd_upper - profile.zpd_lower) * 0.3
            profile.recommendations.append(ContentRecommendation(
                topic=tm.topic,
                subject=tm.subject,
                reason=f"Başarı oranı düşük ({tm.success_rate:.0%})",
                priority=i + 1,
                recommended_difficulty=rec_diff,
            ))
