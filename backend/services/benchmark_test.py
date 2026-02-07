"""
Benchmark Test Implementation - Task 61.4
REQ-49.45-49.48: Ulusal ortalama karşılaştırma, percentile ranking, performans tahmini
"""

import logging
from typing import Dict, List
from services.test_types import BaseTestType, TestConfiguration

logger = logging.getLogger(__name__)


class BenchmarkTest(BaseTestType):
    """Benchmark Test - Ulusal ortalama ile karşılaştırma"""

    def __init__(self):
        super().__init__()
        # Ulusal ortalama verileri (örnek)
        self.national_average = 0.65  # %65
        self.national_std = 0.15
        self.logger.info("Benchmark Test initialized")

    def get_configuration(self) -> TestConfiguration:
        return TestConfiguration(
            test_type="benchmark",
            target_length=30,
            min_length=30,
            max_length=30,
            time_limit_minutes=60,
            immediate_feedback=False,
            adaptive_difficulty=False,
            osym_format_compliance=True,
        )

    def calculate_percentile(self, score: float) -> float:
        """REQ-49.46: Percentile ranking hesaplama"""
        # Z-score hesapla
        z_score = (score - self.national_average) / self.national_std
        # Percentile'a çevir (normal dağılım varsayımı)
        from scipy.stats import norm

        percentile = norm.cdf(z_score) * 100
        return percentile

    def predict_performance(self, current_score: float) -> Dict:
        """REQ-49.47: Performance prediction"""
        percentile = self.calculate_percentile(current_score)

        # Basit tahmin modeli
        if percentile >= 90:
            prediction = "Mükemmel! Gerçek sınavda üst %10'da yer alabilirsiniz."
        elif percentile >= 75:
            prediction = "Çok iyi! Gerçek sınavda üst %25'te yer alabilirsiniz."
        elif percentile >= 50:
            prediction = "İyi! Ortalamanın üstündesiniz."
        else:
            prediction = "Daha fazla çalışma gerekli."

        return {
            "percentile": percentile,
            "prediction": prediction,
            "estimated_rank": f"Üst %{100-percentile:.0f}",
        }

    def generate_feedback(self, session_data: Dict) -> Dict:
        """REQ-49.45: National average comparison"""
        responses = session_data.get("responses", [])
        total_correct = sum(1 for r in responses if r.get("is_correct", False))
        accuracy = total_correct / len(responses) if responses else 0.0

        percentile = self.calculate_percentile(accuracy)
        performance_pred = self.predict_performance(accuracy)

        # Konu bazlı güçlü/zayıf alanlar (REQ-49.48)
        topic_performance = {}
        for response in responses:
            topic = response.get("topic", "unknown")
            if topic not in topic_performance:
                topic_performance[topic] = {"correct": 0, "total": 0}
            topic_performance[topic]["total"] += 1
            if response.get("is_correct", False):
                topic_performance[topic]["correct"] += 1

        strong_topics = [
            t for t, p in topic_performance.items() if p["correct"] / p["total"] >= 0.7
        ]
        weak_topics = [
            t for t, p in topic_performance.items() if p["correct"] / p["total"] < 0.5
        ]

        return {
            "test_type": "benchmark",
            "your_score": accuracy * 100,
            "national_average": self.national_average * 100,
            "percentile_rank": percentile,
            "performance_prediction": performance_pred,
            "strong_topics": strong_topics,
            "weak_topics": weak_topics,
        }

    def calculate_recommendations(self, session_data: Dict) -> List[str]:
        """Öneriler"""
        feedback = self.generate_feedback(session_data)
        recommendations = []

        recommendations.append(
            f"📊 Benchmark Test Sonuçları\n"
            f"{'='*60}\n"
            f"Sizin Puanınız: %{feedback['your_score']:.1f}\n"
            f"Ulusal Ortalama: %{feedback['national_average']:.1f}\n"
            f"Yüzdelik Dilim: %{feedback['percentile_rank']:.0f}\n"
            f"Tahmin: {feedback['performance_prediction']['prediction']}"
        )

        if feedback["weak_topics"]:
            recommendations.append(
                f"\n⚠️ Zayıf Alanlar: {', '.join(feedback['weak_topics'])}"
            )

        if feedback["strong_topics"]:
            recommendations.append(
                f"\n✅ Güçlü Alanlar: {', '.join(feedback['strong_topics'])}"
            )

        return recommendations
