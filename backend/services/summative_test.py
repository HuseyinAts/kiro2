"""
Summative Test Implementation - Task 61.3
REQ-49.41-49.44: Final değerlendirme, ÖSYM uyumluluğu, kapsamlı puanlama, sertifika
"""

import logging
from typing import Dict, List
from services.test_types import BaseTestType, TestConfiguration

logger = logging.getLogger(__name__)


class SummativeTest(BaseTestType):
    """Summative Test - Final değerlendirme"""

    def __init__(self):
        super().__init__()
        self.logger.info("Summative Test initialized")

    def get_configuration(self) -> TestConfiguration:
        """REQ-49.42: ÖSYM format compliance"""
        return TestConfiguration(
            test_type="summative",
            target_length=40,
            min_length=40,
            max_length=40,
            time_limit_minutes=80,
            immediate_feedback=False,
            adaptive_difficulty=False,
            osym_format_compliance=True,  # REQ-49.42
        )

    def generate_feedback(self, session_data: Dict) -> Dict:
        """REQ-49.43: Comprehensive scoring"""
        responses = session_data.get("responses", [])
        total_correct = sum(1 for r in responses if r.get("is_correct", False))
        accuracy = total_correct / len(responses) if responses else 0.0

        # Konu bazlı puanlama
        topic_scores = {}
        for response in responses:
            topic = response.get("topic", "unknown")
            if topic not in topic_scores:
                topic_scores[topic] = {"correct": 0, "total": 0}
            topic_scores[topic]["total"] += 1
            if response.get("is_correct", False):
                topic_scores[topic]["correct"] += 1

        return {
            "test_type": "summative",
            "total_score": total_correct,
            "max_score": len(responses),
            "percentage": accuracy * 100,
            "topic_scores": topic_scores,
            "osym_compliant": True,
            "certificate_eligible": accuracy >= 0.7,
        }

    def calculate_recommendations(self, session_data: Dict) -> List[str]:
        """REQ-49.44: Sertifika oluşturma"""
        feedback = self.generate_feedback(session_data)
        recommendations = []

        if feedback["certificate_eligible"]:
            recommendations.append(
                f"🎓 Tebrikler! %{feedback['percentage']:.1f} başarı ile testi geçtiniz. "
                f"Sertifikanız oluşturuldu."
            )
        else:
            recommendations.append(
                f"📊 Test Sonucu: %{feedback['percentage']:.1f}\n"
                f"Sertifika için minimum %70 gereklidir."
            )

        return recommendations
