"""
Diagnostic Test (Tanı Testi) Implementation
Task 61.1: Diagnostic Test
Requirements: REQ-49.33-49.36

Diagnostic Test özellikleri:
- REQ-49.33: Zayıf alanları tespit etmeye odaklanma
- REQ-49.34: Kapsamlı konu kapsama (comprehensive topic coverage)
- REQ-49.35: Konu bazlı detaylı geri bildirim
- REQ-49.36: Özel çalışma planı önerme
"""

import logging
from dataclasses import dataclass

import numpy as np

from services.test_types import BaseTestType, TestConfiguration

logger = logging.getLogger(__name__)


@dataclass
class WeakArea:
    """Zayıf alan bilgisi"""

    topic: str
    accuracy: float
    correct: int
    total: int
    severity: str  # 'critical', 'high', 'medium'
    improvement_priority: int


@dataclass
class TopicPerformance:
    """Konu performans bilgisi"""

    topic: str
    accuracy: float
    correct: int
    total: int
    status: str  # 'excellent', 'good', 'needs_improvement', 'critical'
    avg_response_time: float
    difficulty_distribution: dict[str, int]


class DiagnosticTest(BaseTestType):
    """
    Diagnostic Test (Tanı Testi)

    Zayıf alanları tespit etmek ve öğrenciye özel çalışma planı önermek
    için tasarlanmış kapsamlı test tipi.
    """

    def __init__(self):
        """Diagnostic Test başlat"""
        super().__init__()

        # Performans eşikleri
        self.excellent_threshold = 0.8  # %80+
        self.good_threshold = 0.6  # %60-80
        self.needs_improvement_threshold = 0.4  # %40-60
        # %40 altı critical

        self.logger.info("Diagnostic Test initialized")

    def get_configuration(self) -> TestConfiguration:
        """
        Diagnostic test konfigürasyonu.

        REQ-49.34: Comprehensive topic coverage - tüm konuları kapsamak

        Returns:
            Test konfigürasyonu
        """
        # Tüm konuları kapsamak için content constraints (REQ-49.34)
        content_constraints = {
            "matematik": 5,
            "geometri": 5,
            "fizik": 5,
            "kimya": 5,
            "biyoloji": 5,
            "turkce": 5,
            "edebiyat": 5,
            "tarih": 5,
            "cografya": 5,
            "felsefe": 5,
        }

        return TestConfiguration(
            test_type="diagnostic",
            target_length=50,  # Kapsamlı test
            min_length=30,
            max_length=50,
            precision_threshold=0.3,
            content_constraints=content_constraints,
            time_limit_minutes=90,
            immediate_feedback=False,  # Test sonunda feedback
            adaptive_difficulty=True,
            osym_format_compliance=False,
        )

    def identify_weak_areas(self, session_data: dict) -> list[WeakArea]:
        """
        Zayıf alanları tespit et.

        REQ-49.33: Weakness identification focus - zayıf alanları tespit etme

        Args:
            session_data: Test oturum verisi

        Returns:
            Zayıf alanlar listesi (öncelik sırasına göre)
        """
        responses = session_data.get("responses", [])

        if not responses:
            self.logger.warning("No responses found for weak area identification")
            return []

        # Konu bazlı performans hesapla
        topic_stats = {}

        for response in responses:
            topic = response.get("topic", "unknown")
            is_correct = response.get("is_correct", False)

            if topic not in topic_stats:
                topic_stats[topic] = {"correct": 0, "total": 0}

            topic_stats[topic]["total"] += 1
            if is_correct:
                topic_stats[topic]["correct"] += 1

        # Zayıf alanları belirle (%60 altı başarı)
        weak_areas = []

        for topic, stats in topic_stats.items():
            if stats["total"] == 0:
                continue

            accuracy = stats["correct"] / stats["total"]

            # %60 altı başarı gösteren konular zayıf alan
            if accuracy < 0.6:
                severity = self._determine_severity(accuracy)
                priority = self._calculate_priority(accuracy, stats["total"])

                weak_areas.append(
                    WeakArea(
                        topic=topic,
                        accuracy=accuracy,
                        correct=stats["correct"],
                        total=stats["total"],
                        severity=severity,
                        improvement_priority=priority,
                    )
                )

        # Öncelik sırasına göre sırala (en düşük accuracy en yüksek öncelik)
        weak_areas.sort(key=lambda x: (x.improvement_priority, x.accuracy))

        self.logger.info(
            f"Identified {len(weak_areas)} weak areas from {len(topic_stats)} topics"
        )

        return weak_areas

    def generate_feedback(self, session_data: dict) -> dict:
        """
        Konu bazlı detaylı geri bildirim oluştur.

        REQ-49.35: Detailed feedback generation - konu bazlı detaylı analiz

        Args:
            session_data: Test oturum verisi

        Returns:
            Detaylı geri bildirim
        """
        responses = session_data.get("responses", [])
        weak_areas = self.identify_weak_areas(session_data)

        # Konu bazlı detaylı analiz
        topic_analysis = self._analyze_topics(responses)

        # Her konu için detaylı feedback
        detailed_feedback = {}

        for topic, analysis in topic_analysis.items():
            accuracy = analysis["accuracy"]

            detailed_feedback[topic] = {
                "accuracy": accuracy,
                "correct": analysis["correct"],
                "total": analysis["total"],
                "status": self._get_performance_status(accuracy),
                "feedback_message": self._generate_topic_feedback_message(
                    topic, accuracy
                ),
                "avg_response_time": analysis["avg_response_time"],
                "difficulty_distribution": analysis["difficulty_distribution"],
                "improvement_areas": self._identify_improvement_areas(topic, analysis),
            }

        # Genel değerlendirme
        overall_assessment = self._generate_overall_assessment(
            session_data, weak_areas, topic_analysis
        )

        return {
            "test_type": "diagnostic",
            "weak_areas": [
                {
                    "topic": wa.topic,
                    "accuracy": wa.accuracy,
                    "correct": wa.correct,
                    "total": wa.total,
                    "severity": wa.severity,
                    "priority": wa.improvement_priority,
                }
                for wa in weak_areas
            ],
            "topic_analysis": detailed_feedback,
            "overall_assessment": overall_assessment,
            "total_questions": len(responses),
            "total_correct": sum(1 for r in responses if r.get("is_correct", False)),
            "overall_accuracy": sum(1 for r in responses if r.get("is_correct", False))
            / len(responses)
            if responses
            else 0.0,
        }

    def calculate_recommendations(self, session_data: dict) -> list[str]:
        """
        Özel çalışma planı öner.

        REQ-49.36: Özel çalışma planı önerme

        Args:
            session_data: Test oturum verisi

        Returns:
            Öneriler listesi
        """
        recommendations = []
        weak_areas = self.identify_weak_areas(session_data)

        if not weak_areas:
            recommendations.append(
                "🎉 Tebrikler! Tüm konularda yeterli performans gösterdiniz. "
                "Şimdi daha zor sorularla pratik yaparak kendinizi geliştirebilirsiniz."
            )
            return recommendations

        # Başlık
        recommendations.append(
            f"📊 Diagnostic Test Sonuçlarınıza Göre Özel Çalışma Planı\n" f"{'='*60}"
        )

        # Her zayıf alan için özel öneri (en fazla 5 alan)
        recommendations.append("\n🎯 Öncelikli Çalışma Alanları:\n")

        for i, area in enumerate(weak_areas[:5], 1):
            topic = area.topic
            accuracy = area.accuracy
            severity = area.severity

            if severity == "critical":
                icon = "🔴"
                urgency = "ACİL"
                study_time = "günde en az 45 dakika"
            elif severity == "high":
                icon = "🟠"
                urgency = "ÖNEMLİ"
                study_time = "günde 30 dakika"
            else:
                icon = "🟡"
                urgency = "GELİŞTİRİLMELİ"
                study_time = "haftada 3-4 gün, 20'şer dakika"

            recommendations.append(
                f"{i}. {icon} {topic.upper()} - {urgency}\n"
                f"   Başarı Oranı: %{accuracy*100:.1f}\n"
                f"   Önerilen Çalışma: {study_time}\n"
                f"   Strateji: {self._get_study_strategy(topic, accuracy)}\n"
            )

        # Genel çalışma planı
        recommendations.append(
            f"\n📚 4 Haftalık Çalışma Planı:\n"
            f"{'-'*60}\n"
            f"Hafta 1-2: Temel Kavramlar\n"
            f"  • En zayıf {min(3, len(weak_areas))} konuya odaklanın\n"
            f"  • Her gün düzenli çalışma yapın\n"
            f"  • Temel kavramları ve formülleri ezberleyin\n"
            f"  • Kolay seviye sorularla başlayın\n\n"
            f"Hafta 3: Pratik ve Pekiştirme\n"
            f"  • Orta seviye sorular çözün\n"
            f"  • Yanlış yaptığınız soruları tekrar edin\n"
            f"  • Konu anlatım videoları izleyin\n\n"
            f"Hafta 4: Değerlendirme\n"
            f"  • Yeni bir Diagnostic Test çözün\n"
            f"  • İlerlemenizi ölçün\n"
            f"  • Planı güncelleyin\n"
        )

        # Motivasyon mesajı
        recommendations.append(
            f"\n💪 Motivasyon:\n"
            f"Tespit edilen {len(weak_areas)} zayıf alan, gelişim fırsatlarınızdır! "
            f"Düzenli çalışma ile 4 hafta içinde bu alanlarda %30-40 gelişme "
            f"sağlayabilirsiniz. Başarılar!"
        )

        return recommendations

    # ==================== Helper Methods ====================

    def _determine_severity(self, accuracy: float) -> str:
        """Zayıflık şiddetini belirle"""
        if accuracy < 0.3:
            return "critical"
        if accuracy < 0.45:
            return "high"
        return "medium"

    def _calculate_priority(self, accuracy: float, question_count: int) -> int:
        """İyileştirme önceliğini hesapla (düşük sayı = yüksek öncelik)"""
        # Accuracy ne kadar düşükse öncelik o kadar yüksek (düşük sayı)
        # Soru sayısı da önemli (daha fazla soru = daha güvenilir veri = daha yüksek öncelik)
        base_priority = int(
            accuracy * 100
        )  # Düşük accuracy = düşük sayı = yüksek öncelik
        confidence_penalty = max(0, 10 - question_count)  # Az soru = ceza
        return base_priority + confidence_penalty

    def _analyze_topics(self, responses: list[dict]) -> dict[str, dict]:
        """Konuları detaylı analiz et"""
        topic_data = {}

        for response in responses:
            topic = response.get("topic", "unknown")
            is_correct = response.get("is_correct", False)
            response_time = response.get("response_time", 0)
            difficulty = response.get("difficulty", "medium")

            if topic not in topic_data:
                topic_data[topic] = {
                    "correct": 0,
                    "total": 0,
                    "response_times": [],
                    "difficulty_distribution": {"easy": 0, "medium": 0, "hard": 0},
                }

            topic_data[topic]["total"] += 1
            if is_correct:
                topic_data[topic]["correct"] += 1

            topic_data[topic]["response_times"].append(response_time)
            topic_data[topic]["difficulty_distribution"][difficulty] += 1

        # Özet istatistikler hesapla
        for topic, data in topic_data.items():
            data["accuracy"] = (
                data["correct"] / data["total"] if data["total"] > 0 else 0.0
            )
            data["avg_response_time"] = (
                np.mean(data["response_times"]) if data["response_times"] else 0.0
            )

        return topic_data

    def _get_performance_status(self, accuracy: float) -> str:
        """Performans durumunu belirle"""
        if accuracy >= self.excellent_threshold:
            return "excellent"
        if accuracy >= self.good_threshold:
            return "good"
        if accuracy >= self.needs_improvement_threshold:
            return "needs_improvement"
        return "critical"

    def _generate_topic_feedback_message(self, topic: str, accuracy: float) -> str:
        """Konu için feedback mesajı oluştur"""
        if accuracy >= 0.8:
            return f"{topic} konusunda çok başarılısınız! Bu seviyeyi koruyun ve daha zor sorularla kendinizi zorlayın."
        if accuracy >= 0.6:
            return f"{topic} konusunda iyi durumdasınız. Biraz daha pratikle mükemmel olabilirsiniz."
        if accuracy >= 0.4:
            return f"{topic} konusunda gelişmeye ihtiyacınız var. Temel kavramları tekrar edin ve düzenli pratik yapın."
        return f"{topic} konusunda ciddi eksiklikler var. Acil çalışma gerekli! Konu anlatımlarından başlayın."

    def _identify_improvement_areas(self, topic: str, analysis: dict) -> list[str]:
        """İyileştirme alanlarını belirle"""
        areas = []

        # Zorluk seviyesine göre analiz
        diff_dist = analysis["difficulty_distribution"]

        if diff_dist["easy"] > 0:
            easy_questions = [
                r
                for r in analysis.get("questions", [])
                if r.get("difficulty") == "easy"
            ]
            if easy_questions:
                easy_correct = sum(
                    1 for q in easy_questions if q.get("is_correct", False)
                )
                easy_accuracy = easy_correct / len(easy_questions)

                if easy_accuracy < 0.7:
                    areas.append("Temel kavramları pekiştirin")

        if diff_dist["medium"] > 0:
            medium_questions = [
                r
                for r in analysis.get("questions", [])
                if r.get("difficulty") == "medium"
            ]
            if medium_questions:
                medium_correct = sum(
                    1 for q in medium_questions if q.get("is_correct", False)
                )
                medium_accuracy = medium_correct / len(medium_questions)

                if medium_accuracy < 0.6:
                    areas.append("Orta seviye problem çözme becerilerini geliştirin")

        # Yanıt süresine göre
        avg_time = analysis["avg_response_time"]
        if avg_time > 120:  # 2 dakikadan fazla
            areas.append("Hız çalışması yapın - zaman yönetimini geliştirin")
        elif avg_time < 30:  # Çok hızlı
            areas.append("Soruları daha dikkatli okuyun")

        if not areas:
            areas.append("Düzenli pratik yaparak performansınızı koruyun")

        return areas

    def _generate_overall_assessment(
        self, session_data: dict, weak_areas: list[WeakArea], topic_analysis: dict
    ) -> str:
        """Genel değerlendirme oluştur"""
        responses = session_data.get("responses", [])

        if not responses:
            return "Test tamamlanmadı veya veri bulunamadı."

        total_correct = sum(1 for r in responses if r.get("is_correct", False))
        accuracy = total_correct / len(responses)

        # Genel performans değerlendirmesi
        if len(weak_areas) == 0:
            assessment = (
                f"🌟 Mükemmel Performans!\n"
                f"Tüm konularda yeterli seviyedesiniz (%{accuracy*100:.1f} başarı). "
                f"Şimdi daha ileri seviye çalışmalara geçebilirsiniz."
            )
        elif len(weak_areas) <= 3:
            assessment = (
                f"✅ İyi Performans\n"
                f"Genel başarı oranınız %{accuracy*100:.1f}. "
                f"{len(weak_areas)} konuda gelişme fırsatınız var. "
                f"Bu alanlara odaklanarak kısa sürede iyileşme sağlayabilirsiniz."
            )
        elif len(weak_areas) <= 6:
            assessment = (
                f"⚠️ Orta Seviye Performans\n"
                f"Genel başarı oranınız %{accuracy*100:.1f}. "
                f"{len(weak_areas)} konuda çalışma gerekiyor. "
                f"Düzenli bir çalışma planı ile 4-6 hafta içinde hedeflerinize ulaşabilirsiniz."
            )
        else:
            assessment = (
                f"🔴 Yoğun Çalışma Gerekli\n"
                f"Genel başarı oranınız %{accuracy*100:.1f}. "
                f"{len(weak_areas)} konuda ciddi eksiklikler tespit edildi. "
                f"Temel kavramlardan başlayarak sistematik bir çalışma planı uygulamanız önerilir. "
                f"Bir öğretmen veya mentor desteği almanız faydalı olabilir."
            )

        # Güçlü alanlar
        strong_topics = [
            topic
            for topic, analysis in topic_analysis.items()
            if analysis["accuracy"] >= 0.8
        ]

        if strong_topics:
            assessment += (
                f"\n\n💪 Güçlü Olduğunuz Konular: {', '.join(strong_topics[:5])}"
            )

        return assessment

    def _get_study_strategy(self, topic: str, accuracy: float) -> str:
        """Konu için çalışma stratejisi öner"""
        if accuracy < 0.3:
            return "Konu anlatım videoları izleyin, temel kavramları not alın, kolay sorularla başlayın"
        if accuracy < 0.45:
            return "Temel formülleri ezberleyin, örnek sorular çözün, yanlışlarınızı analiz edin"
        return "Orta seviye sorular çözün, hız çalışması yapın, farklı soru tipleriyle pratik yapın"
