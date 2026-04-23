"""
Adaptif Öğrenme Algoritması
Multi-Armed Bandit ile İçerik Seçimi
Teknofest 2025 - Eğitim Eylemci Projesi
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BanditAlgorithm(Enum):
    """Bandit algoritma tipleri"""

    EPSILON_GREEDY = "epsilon_greedy"
    UCB = "ucb"  # Upper Confidence Bound
    THOMPSON_SAMPLING = "thompson_sampling"
    EXP3 = "exp3"  # Exponential-weight algorithm for Exploration and Exploitation


@dataclass
class Arm:
    """Bandit kolu (içerik/strateji)"""

    arm_id: str
    name: str
    content_type: str  # video, article, quiz, etc.
    difficulty: str
    features: dict[str, Any]
    metadata: dict[str, Any]


@dataclass
class ArmStatistics:
    """Kol istatistikleri"""

    arm_id: str
    pulls: int  # Kaç kez seçildi
    rewards: float  # Toplam ödül
    successes: int  # Başarılı sonuçlar
    avg_reward: float  # Ortalama ödül
    confidence: float  # Güven aralığı
    last_pulled: datetime | None = None


class MultiArmedBandit:
    """Multi-Armed Bandit algoritması"""

    def __init__(
        self,
        algorithm: BanditAlgorithm = BanditAlgorithm.UCB,
        epsilon: float = 0.1,
        c: float = 2.0,
        gamma: float = 0.1,
    ):
        """
        Args:
            algorithm: Kullanılacak algoritma
            epsilon: Epsilon-greedy için keşif oranı
            c: UCB için güven parametresi
            gamma: EXP3 için öğrenme oranı
        """
        self.algorithm = algorithm
        self.epsilon = epsilon
        self.c = c
        self.gamma = gamma

        self.arms = {}  # arm_id -> Arm
        self.statistics = {}  # arm_id -> ArmStatistics
        self.total_pulls = 0
        self.history = []

    def add_arm(self, arm: Arm):
        """Yeni kol ekle"""
        self.arms[arm.arm_id] = arm
        self.statistics[arm.arm_id] = ArmStatistics(
            arm_id=arm.arm_id,
            pulls=0,
            rewards=0,
            successes=0,
            avg_reward=0,
            confidence=float("inf"),
        )
        logger.info(f"Arm added: {arm.arm_id}")

    def select_arm(self, context: dict[str, Any] | None = None) -> str:
        """
        Kol seç

        Args:
            context: Bağlam bilgisi (kullanıcı özellikleri, zaman, vs.)

        Returns:
            Seçilen kol ID'si
        """
        if not self.arms:
            raise ValueError("No arms available")

        if self.algorithm == BanditAlgorithm.EPSILON_GREEDY:
            return self._epsilon_greedy_select()
        if self.algorithm == BanditAlgorithm.UCB:
            return self._ucb_select()
        if self.algorithm == BanditAlgorithm.THOMPSON_SAMPLING:
            return self._thompson_sampling_select()
        if self.algorithm == BanditAlgorithm.EXP3:
            return self._exp3_select()
        return self._random_select()

    def _epsilon_greedy_select(self) -> str:
        """Epsilon-greedy algoritması ile seçim"""
        if np.random.random() < self.epsilon:
            # Keşif: Rastgele seç
            return np.random.choice(list(self.arms.keys()))
        # Sömürü: En iyi kolu seç
        best_arm = max(self.statistics.values(), key=lambda s: s.avg_reward)
        return best_arm.arm_id

    def _ucb_select(self) -> str:
        """Upper Confidence Bound algoritması ile seçim"""
        # İlk turda tüm kolları dene
        for arm_id, stats in self.statistics.items():
            if stats.pulls == 0:
                return arm_id

        # UCB değerlerini hesapla
        ucb_values = {}
        for arm_id, stats in self.statistics.items():
            # UCB = avg_reward + c * sqrt(ln(total) / pulls)
            exploration_term = self.c * np.sqrt(np.log(self.total_pulls) / stats.pulls)
            ucb_values[arm_id] = stats.avg_reward + exploration_term

        # En yüksek UCB değerine sahip kolu seç
        return max(ucb_values, key=ucb_values.get)

    def _thompson_sampling_select(self) -> str:
        """Thompson Sampling algoritması ile seçim"""
        samples = {}

        for arm_id, stats in self.statistics.items():
            # Beta dağılımından örnekle
            alpha = stats.successes + 1
            beta = stats.pulls - stats.successes + 1
            samples[arm_id] = np.random.beta(alpha, beta)

        # En yüksek örnek değerine sahip kolu seç
        return max(samples, key=samples.get)

    def _exp3_select(self) -> str:
        """EXP3 algoritması ile seçim"""
        # Ağırlıkları hesapla
        weights = {}
        total_weight = 0

        for arm_id in self.arms.keys():
            stats = self.statistics[arm_id]
            # Ağırlık = exp(gamma * rewards / pulls)
            if stats.pulls > 0:
                weight = np.exp(self.gamma * stats.rewards / stats.pulls)
            else:
                weight = 1.0
            weights[arm_id] = weight
            total_weight += weight

        # Olasılıkları normalize et
        probabilities = {
            arm_id: weight / total_weight for arm_id, weight in weights.items()
        }

        # Olasılıklara göre seç
        arms = list(probabilities.keys())
        probs = list(probabilities.values())
        return np.random.choice(arms, p=probs)

    def _random_select(self) -> str:
        """Rastgele seçim"""
        return np.random.choice(list(self.arms.keys()))

    def update(self, arm_id: str, reward: float, success: bool = None):
        """
        Kol istatistiklerini güncelle

        Args:
            arm_id: Kol ID'si
            reward: Alınan ödül (0-1 arası)
            success: Başarılı mı? (Thompson Sampling için)
        """
        if arm_id not in self.statistics:
            logger.warning(f"Unknown arm: {arm_id}")
            return

        stats = self.statistics[arm_id]
        stats.pulls += 1
        stats.rewards += reward
        if success is not None and success:
            stats.successes += 1
        stats.avg_reward = stats.rewards / stats.pulls
        stats.last_pulled = datetime.now()

        self.total_pulls += 1

        # Geçmişe ekle
        self.history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "arm_id": arm_id,
                "reward": reward,
                "success": success,
                "total_pulls": self.total_pulls,
            }
        )

        logger.info(
            f"Updated arm {arm_id}: reward={reward:.2f}, avg={stats.avg_reward:.2f}"
        )

    def get_statistics(self) -> dict[str, ArmStatistics]:
        """Tüm kol istatistiklerini getir"""
        return self.statistics.copy()

    def get_best_arm(self) -> str:
        """En iyi performans gösteren kolu getir"""
        if not self.statistics:
            return None

        best = max(self.statistics.values(), key=lambda s: s.avg_reward)
        return best.arm_id

    def reset(self):
        """İstatistikleri sıfırla"""
        for stats in self.statistics.values():
            stats.pulls = 0
            stats.rewards = 0
            stats.successes = 0
            stats.avg_reward = 0
            stats.confidence = float("inf")
            stats.last_pulled = None

        self.total_pulls = 0
        self.history = []
        logger.info("Bandit statistics reset")


class ContextualBandit(MultiArmedBandit):
    """Bağlamsal Multi-Armed Bandit"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context_features = []
        self.context_weights = {}

    def learn_context_weights(self, history: list[dict[str, Any]]):
        """
        Geçmiş veriden bağlam ağırlıklarını öğren

        Args:
            history: Geçmiş etkileşimler
        """
        # Basit bir yaklaşım: Her bağlam özelliği için ortalama ödül
        context_rewards = defaultdict(lambda: defaultdict(list))

        for entry in history:
            context = entry.get("context", {})
            reward = entry.get("reward", 0)
            arm_id = entry.get("arm_id")

            for feature, value in context.items():
                context_rewards[arm_id][f"{feature}:{value}"].append(reward)

        # Ağırlıkları hesapla
        self.context_weights = {}
        for arm_id, features in context_rewards.items():
            self.context_weights[arm_id] = {}
            for feature_value, rewards in features.items():
                self.context_weights[arm_id][feature_value] = np.mean(rewards)

        logger.info("Context weights learned")

    def select_arm_with_context(self, context: dict[str, Any]) -> str:
        """
        Bağlam bilgisi ile kol seç

        Args:
            context: Bağlam (kullanıcı özellikleri, zaman, vs.)

        Returns:
            Seçilen kol ID'si
        """
        # Bağlam skorlarını hesapla
        context_scores = {}

        for arm_id in self.arms.keys():
            score = 0
            arm_weights = self.context_weights.get(arm_id, {})

            for feature, value in context.items():
                feature_key = f"{feature}:{value}"
                if feature_key in arm_weights:
                    score += arm_weights[feature_key]

            context_scores[arm_id] = score

        # Bağlam skorlarını normal skorlarla birleştir
        combined_scores = {}
        for arm_id, stats in self.statistics.items():
            base_score = stats.avg_reward
            context_score = context_scores.get(arm_id, 0)

            # Ağırlıklı kombinasyon
            combined_scores[arm_id] = 0.7 * base_score + 0.3 * context_score

        # Exploration-exploitation dengesi
        if np.random.random() < self.epsilon:
            # Keşif
            return np.random.choice(list(self.arms.keys()))
        # Sömürü
        return max(combined_scores, key=combined_scores.get)


class AdaptiveLearningSystem:
    """Adaptif öğrenme sistemi"""

    def __init__(self):
        self.bandits = {}  # Her öğrenci için ayrı bandit
        self.content_arms = {}  # İçerik kolları
        self.performance_history = defaultdict(list)

    def initialize_student_bandit(
        self, student_id: str, algorithm: BanditAlgorithm = BanditAlgorithm.UCB
    ) -> ContextualBandit:
        """
        Öğrenci için bandit başlat

        Args:
            student_id: Öğrenci ID
            algorithm: Kullanılacak algoritma

        Returns:
            Contextual bandit instance
        """
        bandit = ContextualBandit(algorithm=algorithm)

        # İçerik tiplerini kol olarak ekle
        content_types = [
            Arm("video", "Video İçerik", "video", "medium", {"engagement": "high"}, {}),
            Arm("article", "Makale", "article", "medium", {"depth": "high"}, {}),
            Arm("quiz", "Quiz", "quiz", "medium", {"interaction": "high"}, {}),
            Arm(
                "interactive",
                "İnteraktif İçerik",
                "interactive",
                "medium",
                {"engagement": "very_high"},
                {},
            ),
            Arm(
                "flashcard",
                "Bilgi Kartları",
                "flashcard",
                "easy",
                {"repetition": "high"},
                {},
            ),
        ]

        for arm in content_types:
            bandit.add_arm(arm)

        self.bandits[student_id] = bandit
        logger.info(f"Initialized bandit for student {student_id}")

        return bandit

    def select_content_type(self, student_id: str, context: dict[str, Any]) -> str:
        """
        Öğrenci için içerik tipi seç

        Args:
            student_id: Öğrenci ID
            context: Bağlam bilgisi

        Returns:
            Seçilen içerik tipi
        """
        if student_id not in self.bandits:
            self.initialize_student_bandit(student_id)

        bandit = self.bandits[student_id]

        # Bağlam bilgisi ekle
        enhanced_context = context.copy()
        enhanced_context.update(
            {
                "time_of_day": self._get_time_period(),
                "session_number": len(self.performance_history[student_id]) + 1,
                "recent_performance": self._get_recent_performance(student_id),
            }
        )

        # İçerik tipi seç
        selected_arm = bandit.select_arm_with_context(enhanced_context)

        logger.info(f"Selected {selected_arm} for student {student_id}")
        return selected_arm

    def update_performance(
        self, student_id: str, content_type: str, performance_data: dict[str, Any]
    ):
        """
        Performans güncellemesi

        Args:
            student_id: Öğrenci ID
            content_type: İçerik tipi
            performance_data: Performans verisi
        """
        if student_id not in self.bandits:
            return

        bandit = self.bandits[student_id]

        # Ödülü hesapla
        reward = self._calculate_reward(performance_data)
        success = performance_data.get("completed", False)

        # Bandit'i güncelle
        bandit.update(content_type, reward, success)

        # Geçmişe ekle
        self.performance_history[student_id].append(
            {
                "timestamp": datetime.now().isoformat(),
                "content_type": content_type,
                "performance": performance_data,
                "reward": reward,
            }
        )

        logger.info(
            f"Updated performance for {student_id}: {content_type} -> {reward:.2f}"
        )

    def _calculate_reward(self, performance_data: dict[str, Any]) -> float:
        """
        Performans verisinden ödül hesapla

        Args:
            performance_data: Performans verisi

        Returns:
            Ödül (0-1 arası)
        """
        # Farklı metrikleri birleştir
        score = performance_data.get("score", 0) / 100  # 0-1'e normalize
        completion = 1.0 if performance_data.get("completed", False) else 0.5
        engagement = performance_data.get("engagement_time", 0) / 60  # Dakika başına
        engagement = min(engagement, 1.0)  # Max 1

        # Ağırlıklı ortalama
        reward = 0.4 * score + 0.3 * completion + 0.3 * engagement

        return min(max(reward, 0), 1)  # 0-1 arasında tut

    def _get_time_period(self) -> str:
        """Günün zamanını belirle"""
        hour = datetime.now().hour
        if hour < 6:
            return "night"
        if hour < 12:
            return "morning"
        if hour < 18:
            return "afternoon"
        return "evening"

    def _get_recent_performance(self, student_id: str) -> str:
        """Son performansı özetle"""
        history = self.performance_history[student_id]
        if not history:
            return "no_data"

        recent = history[-5:]  # Son 5 etkileşim
        avg_reward = np.mean([h["reward"] for h in recent])

        if avg_reward > 0.7:
            return "high"
        if avg_reward > 0.4:
            return "medium"
        return "low"

    def get_recommendations(self, student_id: str, n: int = 3) -> list[dict[str, Any]]:
        """
        Öğrenci için içerik önerileri

        Args:
            student_id: Öğrenci ID
            n: Öneri sayısı

        Returns:
            Öneri listesi
        """
        if student_id not in self.bandits:
            self.initialize_student_bandit(student_id)

        bandit = self.bandits[student_id]
        stats = bandit.get_statistics()

        # İstatistiklere göre sırala
        sorted_arms = sorted(stats.values(), key=lambda s: s.avg_reward, reverse=True)

        recommendations = []
        for arm_stat in sorted_arms[:n]:
            arm = bandit.arms[arm_stat.arm_id]
            recommendations.append(
                {
                    "content_type": arm.content_type,
                    "name": arm.name,
                    "avg_performance": arm_stat.avg_reward,
                    "times_used": arm_stat.pulls,
                    "confidence": 1 / (arm_stat.confidence + 1),
                    "reasoning": f"Bu içerik tipi sizin için %{arm_stat.avg_reward*100:.0f} başarı oranına sahip",
                }
            )

        return recommendations


# Singleton instance
adaptive_learning = AdaptiveLearningSystem()
