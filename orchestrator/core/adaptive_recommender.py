"""Adaptive Content Recommender - MAB tabanlı içerik seçimi.

Multi-Armed Bandit algoritmalarıyla öğrenciye en uygun içeriği seçer:
- Epsilon-Greedy, UCB, Thompson Sampling desteği
- Bağlam-duyarlı içerik tipi önerisi
- Konu × içerik tipi performans takibi
- Keşif-sömürü dengesi (exploration-exploitation)
- Öğrenme stili adaptasyonu
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class BanditAlgorithm(Enum):
    """MAB algoritma türleri."""

    EPSILON_GREEDY = "epsilon_greedy"
    UCB = "ucb"                          # Upper Confidence Bound
    THOMPSON_SAMPLING = "thompson_sampling"


class ContentType(Enum):
    """İçerik türleri."""

    VIDEO = "video"
    TEXT = "text"
    QUIZ = "quiz"
    INTERACTIVE = "interactive"       # Simülasyon, animasyon
    PRACTICE = "practice"             # Soru çözümü
    SUMMARY = "summary"              # Özet/konu anlatımı
    CONCEPT_MAP = "concept_map"      # Kavram haritası


@dataclass
class ArmStats:
    """Bir kolun (içerik türü) istatistikleri."""

    arm_id: str
    content_type: ContentType
    subject: str = ""
    topic: str = ""
    pulls: int = 0                    # Kaç kez sunuldu
    total_reward: float = 0.0         # Toplam ödül
    successes: int = 0                # Başarılı sonuçlar
    alpha: float = 1.0                # Thompson Sampling: Beta(α, β) α
    beta_param: float = 1.0           # Thompson Sampling: Beta(α, β) β

    @property
    def avg_reward(self) -> float:
        """Ortalama ödül."""
        return self.total_reward / max(self.pulls, 1)

    @property
    def success_rate(self) -> float:
        """Başarı oranı."""
        return self.successes / max(self.pulls, 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "arm_id": self.arm_id,
            "content_type": self.content_type.value,
            "subject": self.subject,
            "topic": self.topic,
            "pulls": self.pulls,
            "avg_reward": round(self.avg_reward, 4),
            "success_rate": round(self.success_rate, 3),
        }


@dataclass
class Recommendation:
    """İçerik önerisi."""

    content_type: ContentType
    subject: str
    topic: str
    score: float                      # Algoritma skoru
    reason: str
    is_exploration: bool = False      # Keşif mi sömürü mü

    def to_dict(self) -> dict[str, Any]:
        return {
            "content_type": self.content_type.value,
            "subject": self.subject,
            "topic": self.topic,
            "score": round(self.score, 4),
            "reason": self.reason,
            "is_exploration": self.is_exploration,
        }


@dataclass
class RecommenderConfig:
    """Recommender konfigürasyonu."""

    algorithm: BanditAlgorithm = BanditAlgorithm.THOMPSON_SAMPLING
    epsilon: float = 0.1              # Epsilon-Greedy keşif oranı
    ucb_c: float = 2.0               # UCB keşif parametresi
    min_pulls_before_exploit: int = 3  # Minimum deneme sayısı
    max_recommendations: int = 5
    reward_correct: float = 1.0       # Doğru cevap ödülü
    reward_wrong: float = 0.0         # Yanlış cevap ödülü
    reward_partial: float = 0.5       # Kısmi başarı ödülü
    time_bonus_threshold: float = 0.8  # Hızlı cevap bonusu eşiği
    time_bonus: float = 0.2           # Hızlı cevap bonus değeri


@dataclass
class StudentBanditProfile:
    """Öğrencinin MAB profili."""

    student_id: str
    arms: dict[str, ArmStats] = field(default_factory=dict)
    total_interactions: int = 0
    last_updated: str = ""

    def get_or_create_arm(
        self, content_type: ContentType, subject: str, topic: str,
    ) -> ArmStats:
        """Kol getir veya oluştur."""
        key = f"{subject}:{topic}:{content_type.value}"
        if key not in self.arms:
            self.arms[key] = ArmStats(
                arm_id=key,
                content_type=content_type,
                subject=subject,
                topic=topic,
            )
        return self.arms[key]

    def to_dict(self) -> dict[str, Any]:
        return {
            "student_id": self.student_id,
            "total_interactions": self.total_interactions,
            "arms_count": len(self.arms),
            "top_arms": sorted(
                [a.to_dict() for a in self.arms.values()],
                key=lambda x: x["avg_reward"],
                reverse=True,
            )[:10],
        }


@dataclass
class AdaptiveRecommender:
    """MAB tabanlı adaptif içerik öneri motoru.

    Her öğrenci × konu × içerik tipi kombinasyonu bir \"kol\" olarak
    modellenir. Algoritma, keşif-sömürü dengesini optimize ederek
    en etkili içerik türünü seçer.

    Example:
        >>> recommender = AdaptiveRecommender()
        >>> profile = StudentBanditProfile(student_id="S001")
        >>> recs = recommender.recommend(profile, "Matematik", "Limit")
        >>> print(recs[0].content_type, recs[0].score)
    """

    config: RecommenderConfig = field(default_factory=RecommenderConfig)

    def recommend(
        self,
        profile: StudentBanditProfile,
        subject: str,
        topic: str,
        available_types: list[ContentType] | None = None,
    ) -> list[Recommendation]:
        """Öğrenciye içerik türü öner.

        Args:
            profile: Öğrenci MAB profili.
            subject: Ders.
            topic: Konu.
            available_types: Mevcut içerik türleri (None = tümü).

        Returns:
            Sıralı Recommendation listesi.
        """
        types = available_types or list(ContentType)
        arms = [profile.get_or_create_arm(ct, subject, topic) for ct in types]

        if self.config.algorithm == BanditAlgorithm.EPSILON_GREEDY:
            scored = self._epsilon_greedy_score(arms)
        elif self.config.algorithm == BanditAlgorithm.UCB:
            scored = self._ucb_score(arms, profile.total_interactions)
        else:
            scored = self._thompson_score(arms)

        # Sırala ve öneriler oluştur
        scored.sort(key=lambda x: x[1], reverse=True)
        recommendations: list[Recommendation] = []

        for arm, score, is_explore in scored[: self.config.max_recommendations]:
            reason = self._generate_reason(arm, is_explore)
            recommendations.append(Recommendation(
                content_type=arm.content_type,
                subject=subject,
                topic=topic,
                score=score,
                reason=reason,
                is_exploration=is_explore,
            ))

        return recommendations

    def update(
        self,
        profile: StudentBanditProfile,
        content_type: ContentType,
        subject: str,
        topic: str,
        reward: float,
        is_correct: bool = False,
    ) -> None:
        """Etkileşim sonucu güncelle.

        Args:
            profile: Öğrenci profili.
            content_type: Kullanılan içerik türü.
            subject: Ders.
            topic: Konu.
            reward: Ödül değeri [0, 1].
            is_correct: Doğru cevap mı.
        """
        arm = profile.get_or_create_arm(content_type, subject, topic)
        arm.pulls += 1
        arm.total_reward += reward
        if is_correct:
            arm.successes += 1

        # Thompson Sampling parametreleri güncelle
        arm.alpha += reward
        arm.beta_param += (1 - reward)

        profile.total_interactions += 1
        profile.last_updated = datetime.now(timezone.utc).isoformat()

    def calculate_reward(
        self,
        is_correct: bool,
        time_ratio: float = 1.0,
    ) -> float:
        """Etkileşimden ödül hesapla.

        Args:
            is_correct: Doğru cevap mı.
            time_ratio: actual_time / expected_time (< 1 = hızlı).

        Returns:
            Reward [0, 1+].
        """
        base = self.config.reward_correct if is_correct else self.config.reward_wrong
        if is_correct and time_ratio < self.config.time_bonus_threshold:
            base += self.config.time_bonus
        return min(base, 1.5)

    def get_exploration_rate(self, profile: StudentBanditProfile) -> float:
        """Mevcut keşif oranını hesapla.

        Args:
            profile: Öğrenci profili.

        Returns:
            Keşif oranı [0, 1].
        """
        if profile.total_interactions < 10:
            return 1.0  # Başlangıçta tamamen keşif
        # Azalan keşif: exploration decays with sqrt(interactions)
        return min(1.0, self.config.epsilon * math.sqrt(50 / profile.total_interactions))

    def get_topic_summary(
        self,
        profile: StudentBanditProfile,
        subject: str,
        topic: str,
    ) -> dict[str, Any]:
        """Bir konu için içerik tipi performans özeti.

        Args:
            profile: Öğrenci profili.
            subject: Ders.
            topic: Konu.

        Returns:
            İçerik tipi bazlı performans dict.
        """
        prefix = f"{subject}:{topic}:"
        results: dict[str, Any] = {}
        for key, arm in profile.arms.items():
            if key.startswith(prefix):
                results[arm.content_type.value] = {
                    "pulls": arm.pulls,
                    "avg_reward": round(arm.avg_reward, 3),
                    "success_rate": round(arm.success_rate, 3),
                }
        return results

    # --- Algorithm Implementations ---

    def _epsilon_greedy_score(
        self, arms: list[ArmStats],
    ) -> list[tuple[ArmStats, float, bool]]:
        """Epsilon-Greedy skorlama."""
        result: list[tuple[ArmStats, float, bool]] = []
        for arm in arms:
            if arm.pulls < self.config.min_pulls_before_exploit:
                # Yetersiz veri → keşif önceliği
                score = 1.0 + random.random() * 0.1
                result.append((arm, score, True))
            elif random.random() < self.config.epsilon:
                # Keşif
                score = random.random()
                result.append((arm, score, True))
            else:
                # Sömürü
                result.append((arm, arm.avg_reward, False))
        return result

    def _ucb_score(
        self, arms: list[ArmStats], total_pulls: int,
    ) -> list[tuple[ArmStats, float, bool]]:
        """UCB (Upper Confidence Bound) skorlama."""
        result: list[tuple[ArmStats, float, bool]] = []
        total = max(total_pulls, 1)
        for arm in arms:
            if arm.pulls < self.config.min_pulls_before_exploit:
                score = float("inf")
                result.append((arm, score, True))
            else:
                # UCB1: avg_reward + c * sqrt(ln(total) / pulls)
                exploration_bonus = self.config.ucb_c * math.sqrt(
                    math.log(total) / arm.pulls
                )
                score = arm.avg_reward + exploration_bonus
                is_explore = exploration_bonus > arm.avg_reward * 0.5
                result.append((arm, score, is_explore))
        return result

    def _thompson_score(
        self, arms: list[ArmStats],
    ) -> list[tuple[ArmStats, float, bool]]:
        """Thompson Sampling skorlama."""
        result: list[tuple[ArmStats, float, bool]] = []
        for arm in arms:
            # Beta dağılımından örnekle
            sample = random.betavariate(
                max(arm.alpha, 0.01),
                max(arm.beta_param, 0.01),
            )
            is_explore = arm.pulls < self.config.min_pulls_before_exploit
            result.append((arm, sample, is_explore))
        return result

    def _generate_reason(self, arm: ArmStats, is_explore: bool) -> str:
        """Öneri sebebi oluştur."""
        if is_explore:
            if arm.pulls == 0:
                return f"{arm.content_type.value} henüz denenmedi"
            return f"{arm.content_type.value} keşif amaçlı önerildi ({arm.pulls} deneme)"
        rate = arm.success_rate
        if rate >= 0.8:
            return f"{arm.content_type.value} yüksek başarı oranı ({rate:.0%})"
        elif rate >= 0.5:
            return f"{arm.content_type.value} orta başarı oranı ({rate:.0%})"
        return f"{arm.content_type.value} gelişim potansiyeli ({rate:.0%})"
