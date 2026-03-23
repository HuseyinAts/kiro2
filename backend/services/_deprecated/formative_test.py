"""
Formative Test (Biçimlendirici Test) Implementation
Task 61.2: Formative Test
Requirements: REQ-49.37-49.40

Formative Test özellikleri:
- REQ-49.37: Öğrenme ilerlemesini değerlendirme
- REQ-49.38: Adaptif zorluk ayarlama (performansa göre)
- REQ-49.39: Anında geri bildirim (her soru sonrası)
- REQ-49.40: Öğrenme önerileri sunma
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from services.test_types import BaseTestType, TestConfiguration

logger = logging.getLogger(__name__)


@dataclass
class LearningProgress:
    """Öğrenme ilerleme bilgisi"""

    topic: str
    initial_level: float
    current_level: float
    improvement: float
    trend: str  # 'improving', 'stable', 'declining'
    mastery_percentage: float


@dataclass
class ImmediateFeedback:
    """Anında geri bildirim"""

    question_id: str
    is_correct: bool
    correct_answer: str
    student_answer: str
    explanation: str
    difficulty_level: str
    next_difficulty_suggestion: str
    learning_tip: str


class FormativeTest(BaseTestType):
    """
    Formative Test (Biçimlendirici Test)

    Öğrenme sürecinde ilerlemeyi değerlendirmek ve anında geri bildirim
    vermek için tasarlanmış test tipi.
    """

    def __init__(self):
        """Formative Test başlat"""
        super().__init__()

        # Adaptif zorluk parametreleri
        self.difficulty_levels = ["easy", "medium", "hard"]
        self.success_threshold_up = 0.7  # %70+ başarı -> zorluk artır
        self.success_threshold_down = 0.4  # %40- başarı -> zorluk azalt

        # Mastery eşikleri
        self.mastery_threshold = 0.8  # %80+ mastery
        self.partial_mastery_threshold = 0.6  # %60-80 partial mastery

        self.logger.info("Formative Test initialized")

    def get_configuration(self) -> TestConfiguration:
        """
        Formative test konfigürasyonu.

        REQ-49.38: Adaptive difficulty adjustment
        REQ-49.39: Immediate feedback

        Returns:
            Test konfigürasyonu
        """
        return TestConfiguration(
            test_type="formative",
            target_length=20,  # Daha kısa, odaklı test
            min_length=10,
            max_length=30,
            precision_threshold=0.3,
            content_constraints=None,  # Belirli konulara odaklanabilir
            time_limit_minutes=45,
            immediate_feedback=True,  # Her soru sonrası feedback (REQ-49.39)
            adaptive_difficulty=True,  # Dinamik zorluk ayarlama (REQ-49.38)
            osym_format_compliance=False,
        )

    def assess_learning_progress(
        self, session_data: Dict, previous_sessions: Optional[List[Dict]] = None
    ) -> List[LearningProgress]:
        """
        Öğrenme ilerlemesini değerlendir.

        REQ-49.37: Learning progress assessment - öğrenme ilerlemesi değerlendirme

        Args:
            session_data: Mevcut test oturum verisi
            previous_sessions: Önceki test oturumları (opsiyonel)

        Returns:
            Konu bazlı öğrenme ilerleme listesi
        """
        responses = session_data.get("responses", [])

        if not responses:
            self.logger.warning("No responses found for progress assessment")
            return []

        # Konu bazlı performans hesapla
        topic_performance = {}

        for response in responses:
            topic = response.get("topic", "unknown")
            is_correct = response.get("is_correct", False)

            if topic not in topic_performance:
                topic_performance[topic] = {
                    "correct": 0,
                    "total": 0,
                    "recent_correct": [],  # Son 5 sorunun doğruluğu
                }

            topic_performance[topic]["total"] += 1
            if is_correct:
                topic_performance[topic]["correct"] += 1

            # Son 5 soru için tracking
            topic_performance[topic]["recent_correct"].append(is_correct)
            if len(topic_performance[topic]["recent_correct"]) > 5:
                topic_performance[topic]["recent_correct"].pop(0)

        # İlerleme analizi
        progress_list = []

        for topic, perf in topic_performance.items():
            current_level = (
                perf["correct"] / perf["total"] if perf["total"] > 0 else 0.0
            )

            # Önceki oturumlardan initial level al
            initial_level = self._get_initial_level(topic, previous_sessions)

            # İyileşme hesapla
            improvement = current_level - initial_level

            # Trend analizi (son 5 soruya göre)
            trend = self._analyze_trend(perf["recent_correct"])

            # Mastery yüzdesi
            mastery_percentage = current_level * 100

            progress_list.append(
                LearningProgress(
                    topic=topic,
                    initial_level=initial_level,
                    current_level=current_level,
                    improvement=improvement,
                    trend=trend,
                    mastery_percentage=mastery_percentage,
                )
            )

        self.logger.info(f"Assessed learning progress for {len(progress_list)} topics")

        return progress_list

    def adjust_difficulty(
        self, current_difficulty: str, recent_performance: List[bool]
    ) -> str:
        """
        Performansa göre zorluk seviyesini ayarla.

        REQ-49.38: Adaptive difficulty adjustment - performansa göre zorluk ayarlama

        Args:
            current_difficulty: Mevcut zorluk seviyesi
            recent_performance: Son N sorunun doğruluk listesi

        Returns:
            Yeni zorluk seviyesi
        """
        if not recent_performance:
            return current_difficulty

        # Son performansı hesapla
        success_rate = sum(recent_performance) / len(recent_performance)

        current_index = self.difficulty_levels.index(current_difficulty)

        # Zorluk artırma (REQ-49.38: Performance-based scaling)
        if success_rate >= self.success_threshold_up:
            # %70+ başarı -> zorluk artır
            if current_index < len(self.difficulty_levels) - 1:
                new_difficulty = self.difficulty_levels[current_index + 1]
                self.logger.info(
                    f"Increasing difficulty: {current_difficulty} -> {new_difficulty} "
                    f"(success rate: {success_rate:.2%})"
                )
                return new_difficulty

        # Zorluk azaltma
        elif success_rate < self.success_threshold_down:
            # %40- başarı -> zorluk azalt
            if current_index > 0:
                new_difficulty = self.difficulty_levels[current_index - 1]
                self.logger.info(
                    f"Decreasing difficulty: {current_difficulty} -> {new_difficulty} "
                    f"(success rate: {success_rate:.2%})"
                )
                return new_difficulty

        # Zorluk sabit kal
        return current_difficulty

    def generate_immediate_feedback(
        self, question_data: Dict, student_answer: str, is_correct: bool
    ) -> ImmediateFeedback:
        """
        Her soru için anında geri bildirim oluştur.

        REQ-49.39: Immediate feedback - her soru sonrası açıklama

        Args:
            question_data: Soru bilgileri
            student_answer: Öğrenci cevabı
            is_correct: Doğru mu?

        Returns:
            Anında geri bildirim
        """
        question_id = question_data.get("question_id", "unknown")
        correct_answer = question_data.get("correct_answer", "")
        difficulty = question_data.get("difficulty", "medium")
        topic = question_data.get("topic", "unknown")

        # Açıklama oluştur
        if is_correct:
            explanation = self._generate_correct_explanation(question_data)
            learning_tip = self._generate_reinforcement_tip(topic, difficulty)
            next_difficulty = self._suggest_next_difficulty(difficulty, True)
        else:
            explanation = self._generate_incorrect_explanation(
                question_data, student_answer
            )
            learning_tip = self._generate_improvement_tip(topic, difficulty)
            next_difficulty = self._suggest_next_difficulty(difficulty, False)

        return ImmediateFeedback(
            question_id=question_id,
            is_correct=is_correct,
            correct_answer=correct_answer,
            student_answer=student_answer,
            explanation=explanation,
            difficulty_level=difficulty,
            next_difficulty_suggestion=next_difficulty,
            learning_tip=learning_tip,
        )

    def generate_feedback(self, session_data: Dict) -> Dict:
        """
        Test için genel geri bildirim oluştur.

        REQ-49.37: Learning progress assessment
        REQ-49.40: Öğrenme önerileri

        Args:
            session_data: Test oturum verisi

        Returns:
            Geri bildirim
        """
        responses = session_data.get("responses", [])
        previous_sessions = session_data.get("previous_sessions", [])

        # Öğrenme ilerlemesini değerlendir
        progress = self.assess_learning_progress(session_data, previous_sessions)

        # Konu bazlı analiz
        topic_analysis = {}
        for prog in progress:
            status = self._get_mastery_status(prog.mastery_percentage)

            topic_analysis[prog.topic] = {
                "initial_level": prog.initial_level,
                "current_level": prog.current_level,
                "improvement": prog.improvement,
                "trend": prog.trend,
                "mastery_percentage": prog.mastery_percentage,
                "status": status,
                "feedback_message": self._generate_progress_message(prog),
            }

        return {
            "test_type": "formative",
            "learning_progress": [
                {
                    "topic": p.topic,
                    "initial_level": p.initial_level,
                    "current_level": p.current_level,
                    "improvement": p.improvement,
                    "trend": p.trend,
                    "mastery_percentage": p.mastery_percentage,
                }
                for p in progress
            ],
            "topic_analysis": topic_analysis,
            "total_questions": len(responses),
            "total_correct": sum(1 for r in responses if r.get("is_correct", False)),
            "overall_accuracy": sum(1 for r in responses if r.get("is_correct", False))
            / len(responses)
            if responses
            else 0.0,
        }

    def calculate_recommendations(self, session_data: Dict) -> List[str]:
        """
        Öğrenme önerileri oluştur.

        REQ-49.40: Öğrenme önerileri sunma

        Args:
            session_data: Test oturum verisi

        Returns:
            Öneriler listesi
        """
        recommendations = []
        progress = self.assess_learning_progress(
            session_data, session_data.get("previous_sessions", [])
        )

        if not progress:
            recommendations.append("Test tamamlanmadı veya yeterli veri yok.")
            return recommendations

        # Başlık
        recommendations.append(
            f"📈 Formative Test - Öğrenme İlerleme Raporu\n" f"{'='*60}"
        )

        # İlerleme özeti
        improving_topics = [p for p in progress if p.improvement > 0.1]
        declining_topics = [p for p in progress if p.improvement < -0.1]

        if improving_topics:
            recommendations.append(
                f"\n✅ Gelişen Konular ({len(improving_topics)} adet):"
            )
            for prog in improving_topics[:3]:
                recommendations.append(
                    f"  • {prog.topic}: %{prog.initial_level*100:.0f} → "
                    f"%{prog.current_level*100:.0f} "
                    f"(+%{prog.improvement*100:.0f})"
                )

        if declining_topics:
            recommendations.append(
                f"\n⚠️ Dikkat Gereken Konular ({len(declining_topics)} adet):"
            )
            for prog in declining_topics[:3]:
                recommendations.append(
                    f"  • {prog.topic}: %{prog.initial_level*100:.0f} → "
                    f"%{prog.current_level*100:.0f} "
                    f"(%{prog.improvement*100:.0f})"
                )

        # Mastery durumu
        recommendations.append("\n🎯 Mastery Durumu:")

        mastered = [p for p in progress if p.mastery_percentage >= 80]
        partial = [p for p in progress if 60 <= p.mastery_percentage < 80]
        needs_work = [p for p in progress if p.mastery_percentage < 60]

        if mastered:
            recommendations.append(
                f"  ✓ Mastered ({len(mastered)}): {', '.join([p.topic for p in mastered[:5]])}"
            )

        if partial:
            recommendations.append(
                f"  ◐ Partial Mastery ({len(partial)}): {', '.join([p.topic for p in partial[:5]])}"
            )

        if needs_work:
            recommendations.append(
                f"  ○ Needs Work ({len(needs_work)}): {', '.join([p.topic for p in needs_work[:5]])}"
            )

        # Öğrenme stratejileri
        recommendations.append("\n💡 Önerilen Öğrenme Stratejileri:\n")

        for prog in progress[:3]:  # İlk 3 konu için
            if prog.trend == "improving":
                recommendations.append(
                    f"  • {prog.topic}: Harika ilerleme! Mevcut stratejinizi sürdürün "
                    f"ve daha zor sorularla kendinizi zorlayın."
                )
            elif prog.trend == "declining":
                recommendations.append(
                    f"  • {prog.topic}: Performans düşüşü tespit edildi. "
                    f"Temel kavramları tekrar edin ve daha fazla pratik yapın."
                )
            else:
                recommendations.append(
                    f"  • {prog.topic}: Stabil performans. Farklı soru tipleriyle "
                    f"pratik yaparak çeşitlilik kazanın."
                )

        # Sonraki adımlar
        recommendations.append(
            "\n🎓 Sonraki Adımlar:\n"
            "  1. Mastered konularda ileri seviye çalışmaya geçin\n"
            "  2. Partial mastery konularda günlük 15-20 dakika pratik yapın\n"
            "  3. Needs work konularda temel kavramları pekiştirin\n"
            "  4. 1 hafta sonra yeni bir formative test çözün"
        )

        return recommendations

    # ==================== Helper Methods ====================

    def _get_initial_level(
        self, topic: str, previous_sessions: Optional[List[Dict]]
    ) -> float:
        """Önceki oturumlardan başlangıç seviyesini al"""
        if not previous_sessions:
            return 0.5  # Varsayılan orta seviye

        # En son oturumdaki performansı al
        for session in reversed(previous_sessions):
            responses = session.get("responses", [])
            topic_responses = [r for r in responses if r.get("topic") == topic]

            if topic_responses:
                correct = sum(1 for r in topic_responses if r.get("is_correct", False))
                return correct / len(topic_responses)

        return 0.5

    def _analyze_trend(self, recent_correct: List[bool]) -> str:
        """Son soruların trendini analiz et"""
        if len(recent_correct) < 3:
            return "stable"

        # İlk yarı vs ikinci yarı karşılaştırması
        mid = len(recent_correct) // 2
        first_half = sum(recent_correct[:mid]) / mid if mid > 0 else 0
        second_half = sum(recent_correct[mid:]) / (len(recent_correct) - mid)

        diff = second_half - first_half

        if diff > 0.2:
            return "improving"
        elif diff < -0.2:
            return "declining"
        else:
            return "stable"

    def _suggest_next_difficulty(self, current: str, is_correct: bool) -> str:
        """Sonraki soru için zorluk öner"""
        if is_correct and current != "hard":
            idx = self.difficulty_levels.index(current)
            return self.difficulty_levels[idx + 1]
        elif not is_correct and current != "easy":
            idx = self.difficulty_levels.index(current)
            return self.difficulty_levels[idx - 1]
        return current

    def _generate_correct_explanation(self, question_data: Dict) -> str:
        """Doğru cevap için açıklama"""
        topic = question_data.get("topic", "bu konu")
        return (
            f"✓ Doğru! {topic} konusunda bu soruyu başarıyla çözdünüz. "
            f"Bu tür soruları çözme beceriniz gelişiyor."
        )

    def _generate_incorrect_explanation(
        self, question_data: Dict, student_answer: str
    ) -> str:
        """Yanlış cevap için açıklama"""
        topic = question_data.get("topic", "bu konu")
        correct = question_data.get("correct_answer", "")

        return (
            f"✗ Yanlış. Doğru cevap: {correct}\n"
            f"{topic} konusunda bu kavramı tekrar gözden geçirmeniz önerilir. "
            f"Benzer sorularla daha fazla pratik yapın."
        )

    def _generate_reinforcement_tip(self, topic: str, difficulty: str) -> str:
        """Pekiştirme ipucu"""
        if difficulty == "hard":
            return f"Zor soruları çözebiliyorsunuz! {topic} konusunda ileri seviyeye geçebilirsiniz."
        elif difficulty == "medium":
            return f"İyi gidiyorsunuz! {topic} konusunda daha zor sorulara hazırsınız."
        else:
            return "Temel kavramları iyi anlıyorsunuz. Orta seviye sorulara geçebilirsiniz."

    def _generate_improvement_tip(self, topic: str, difficulty: str) -> str:
        """İyileştirme ipucu"""
        if difficulty == "easy":
            return f"{topic} konusunda temel kavramları tekrar edin. Konu anlatım videoları izleyin."
        elif difficulty == "medium":
            return (
                f"{topic} konusunda daha fazla örnek soru çözün. Formülleri pekiştirin."
            )
        else:
            return "Zor sorular için daha fazla pratik gerekli. Önce orta seviye soruları pekiştirin."

    def _get_mastery_status(self, mastery_percentage: float) -> str:
        """Mastery durumunu belirle"""
        if mastery_percentage >= self.mastery_threshold * 100:
            return "mastered"
        elif mastery_percentage >= self.partial_mastery_threshold * 100:
            return "partial_mastery"
        else:
            return "needs_work"

    def _generate_progress_message(self, progress: LearningProgress) -> str:
        """İlerleme mesajı oluştur"""
        if progress.trend == "improving":
            return (
                f"📈 Harika ilerleme! {progress.topic} konusunda "
                f"%{abs(progress.improvement)*100:.0f} gelişme gösterdiniz."
            )
        elif progress.trend == "declining":
            return (
                f"📉 Dikkat! {progress.topic} konusunda "
                f"%{abs(progress.improvement)*100:.0f} düşüş var. Tekrar çalışma gerekli."
            )
        else:
            return (
                f"➡️ {progress.topic} konusunda stabil performans gösteriyorsunuz. "
                f"Mevcut seviyeniz: %{progress.mastery_percentage:.0f}"
            )
