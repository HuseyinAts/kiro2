"""
Motivasyon Destek Sistemi (Motivation Support System)
Task 63.3: Motivasyon desteği
Requirements: REQ-49.77-49.80

Bu modül adaptif test sırasında öğrenci motivasyonunu destekler:
- Başarı oranı izleme (%40-80 aralığında tutma)
- Teşvik mesajları (pozitif pekiştirme)
- Başarı kutlamaları (milestone'larda)
- Motivasyon düştüğünde destek mesajları
"""

import logging
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class MotivationLevel(Enum):
    """Motivasyon seviyeleri"""

    VERY_LOW = "very_low"  # < 30%
    LOW = "low"  # 30-40%
    OPTIMAL = "optimal"  # 40-80%
    HIGH = "high"  # 80-90%
    VERY_HIGH = "very_high"  # > 90%


class MessageType(Enum):
    """Mesaj tipleri"""

    ENCOURAGEMENT = "encouragement"  # Teşvik mesajı
    CELEBRATION = "celebration"  # Kutlama mesajı
    SUPPORT = "support"  # Destek mesajı
    MILESTONE = "milestone"  # Milestone mesajı


@dataclass
class MotivationMessage:
    """Motivasyon mesajı"""

    message_type: MessageType
    message: str
    emoji: str
    timestamp: datetime
    trigger_reason: str


@dataclass
class MotivationState:
    """Öğrenci motivasyon durumu"""

    student_id: str
    current_success_rate: float  # Mevcut başarı oranı (0-1)
    recent_success_rate: float  # Son 5 sorudaki başarı oranı
    consecutive_correct: int  # Ardışık doğru sayısı
    consecutive_incorrect: int  # Ardışık yanlış sayısı
    total_questions: int  # Toplam soru sayısı
    correct_answers: int  # Doğru cevap sayısı
    milestones_reached: List[str]  # Ulaşılan milestone'lar
    messages_shown: List[MotivationMessage]  # Gösterilen mesajlar
    last_message_time: Optional[datetime] = None
    motivation_level: MotivationLevel = MotivationLevel.OPTIMAL


class MotivationSupportSystem:
    """
    Motivasyon Destek Sistemi

    REQ-49.77: Success rate monitoring - başarı oranını %40-80 aralığında tutma
    REQ-49.78: Encouragement messages - pozitif pekiştirme sunma
    REQ-49.79: Achievement celebrations - milestone'larda kutlama gösterme
    REQ-49.80: Support messages - motivasyon düştüğünde destek mesajları gösterme
    """

    def __init__(self):
        """Motivasyon Destek Sistemi başlat"""
        # Başarı oranı hedefleri (REQ-49.77)
        self.target_success_rate_min = 0.40  # %40
        self.target_success_rate_max = 0.80  # %80

        # Mesaj gösterme sıklığı (spam önleme)
        self.min_message_interval_seconds = 30  # En az 30 saniye ara

        # Milestone tanımları
        self.milestones = {
            5: "İlk 5 soruyu tamamladın!",
            10: "10 soru tamamlandı! Harika gidiyorsun!",
            20: "20 soru! Yarı yoldasın!",
            30: "30 soru! Mükemmel bir performans!",
            40: "40 soru! Neredeyse bitti!",
            50: "50 soru tamamlandı! İnanılmaz bir başarı!",
        }

        # Ardışık başarı milestone'ları
        self.streak_milestones = {
            3: "3 doğru üst üste! Harika!",
            5: "5 doğru üst üste! Muhteşem!",
            7: "7 doğru üst üste! İnanılmaz!",
            10: "10 doğru üst üste! Efsanesin!",
        }

        logger.info("Motivation Support System başlatıldı")

    # ==================== REQ-49.77: Success Rate Monitoring ====================

    def monitor_success_rate(
        self, state: MotivationState, is_correct: bool
    ) -> MotivationState:
        """
        Başarı oranını izle ve motivasyon seviyesini güncelle.

        REQ-49.77: Success rate monitoring - başarı oranını %40-80 aralığında tutma

        Args:
            state: Motivasyon durumu
            is_correct: Son yanıt doğru mu?

        Returns:
            Güncellenmiş motivasyon durumu
        """
        # Yanıtı kaydet
        state.total_questions += 1
        if is_correct:
            state.correct_answers += 1
            state.consecutive_correct += 1
            state.consecutive_incorrect = 0
        else:
            state.consecutive_incorrect += 1
            state.consecutive_correct = 0

        # Genel başarı oranını hesapla
        if state.total_questions > 0:
            state.current_success_rate = state.correct_answers / state.total_questions

        # Son 5 sorudaki başarı oranını hesapla (daha güncel durum)
        recent_window = 5
        if state.total_questions >= recent_window:
            # Son 5 soruya bak (basitleştirilmiş - gerçekte response history'den alınır)
            # Burada consecutive correct/incorrect'ten tahmin ediyoruz
            if state.consecutive_correct >= recent_window:
                state.recent_success_rate = 1.0
            elif state.consecutive_incorrect >= recent_window:
                state.recent_success_rate = 0.0
            else:
                # Genel oranı kullan
                state.recent_success_rate = state.current_success_rate
        else:
            state.recent_success_rate = state.current_success_rate

        # Motivasyon seviyesini belirle (REQ-49.77)
        state.motivation_level = self._determine_motivation_level(
            state.recent_success_rate
        )

        logger.debug(
            f"Success rate monitored - Student: {state.student_id}, "
            f"Overall: {state.current_success_rate:.2%}, "
            f"Recent: {state.recent_success_rate:.2%}, "
            f"Level: {state.motivation_level.value}"
        )

        return state

    def _determine_motivation_level(self, success_rate: float) -> MotivationLevel:
        """
        Başarı oranına göre motivasyon seviyesini belirle.

        REQ-49.77: Success rate monitoring

        Args:
            success_rate: Başarı oranı (0-1)

        Returns:
            Motivasyon seviyesi
        """
        if success_rate < 0.30:
            return MotivationLevel.VERY_LOW
        elif success_rate < 0.40:
            return MotivationLevel.LOW
        elif success_rate <= 0.80:
            return MotivationLevel.OPTIMAL  # Hedef aralık
        elif success_rate <= 0.90:
            return MotivationLevel.HIGH
        else:
            return MotivationLevel.VERY_HIGH

    def is_success_rate_optimal(self, state: MotivationState) -> bool:
        """
        Başarı oranı optimal aralıkta mı kontrol et.

        REQ-49.77: Success rate monitoring - %40-80 aralığında tutma

        Args:
            state: Motivasyon durumu

        Returns:
            Optimal aralıkta mı?
        """
        return (
            self.target_success_rate_min
            <= state.recent_success_rate
            <= self.target_success_rate_max
        )

    # ==================== REQ-49.78: Encouragement Messages ====================

    def generate_encouragement_message(
        self, state: MotivationState, is_correct: bool
    ) -> Optional[MotivationMessage]:
        """
        Teşvik mesajı oluştur (pozitif pekiştirme).

        REQ-49.78: Encouragement messages - pozitif pekiştirme sunma

        Args:
            state: Motivasyon durumu
            is_correct: Son yanıt doğru mu?

        Returns:
            Teşvik mesajı veya None
        """
        # Mesaj spam önleme
        if not self._should_show_message(state):
            return None

        # Doğru cevap için teşvik mesajları
        if is_correct:
            messages = [
                "Harika! Doğru cevap! 🎉",
                "Mükemmel! Böyle devam! ⭐",
                "Süper! Çok iyi gidiyorsun! 👏",
                "Bravo! Doğru bildin! 🌟",
                "Aferin! Harika bir cevap! 💪",
                "Tebrikler! Doğru! 🎊",
                "Muhteşem! Tam isabet! 🎯",
                "Çok iyi! Devam et! 🚀",
                "Harikasın! Doğru cevap! ✨",
                "Süpersin! Böyle devam! 🏆",
            ]

            message_text = random.choice(messages)
            emoji = "🎉"
            trigger = "correct_answer"

        # Yanlış cevap için nazik teşvik
        else:
            messages = [
                "Sorun değil! Bir sonrakinde başarırsın! 💪",
                "Önemli değil! Öğrenmeye devam! 📚",
                "Her hata bir öğrenme fırsatı! 🌱",
                "Pes etme! Başarabilirsin! 🎯",
                "Yanlış oldu ama öğrendin! 💡",
                "Bir sonraki soruda başarırsın! ⭐",
                "Öğrenme sürecinin bir parçası! 🚀",
                "Devam et! Başarıya yakınsın! 🌟",
            ]

            message_text = random.choice(messages)
            emoji = "💪"
            trigger = "incorrect_answer"

        message = MotivationMessage(
            message_type=MessageType.ENCOURAGEMENT,
            message=message_text,
            emoji=emoji,
            timestamp=datetime.now(),
            trigger_reason=trigger,
        )

        state.messages_shown.append(message)
        state.last_message_time = datetime.now()

        logger.info(
            f"Encouragement message generated - Student: {state.student_id}, "
            f"Message: {message_text}"
        )

        return message

    # ==================== REQ-49.79: Achievement Celebrations ====================

    def check_and_celebrate_milestones(
        self, state: MotivationState
    ) -> Optional[MotivationMessage]:
        """
        Milestone'ları kontrol et ve kutla.

        REQ-49.79: Achievement celebrations - milestone'larda kutlama gösterme

        Args:
            state: Motivasyon durumu

        Returns:
            Kutlama mesajı veya None
        """
        # Soru sayısı milestone'ları
        if state.total_questions in self.milestones:
            milestone_key = f"questions_{state.total_questions}"

            if milestone_key not in state.milestones_reached:
                state.milestones_reached.append(milestone_key)

                message = MotivationMessage(
                    message_type=MessageType.MILESTONE,
                    message=self.milestones[state.total_questions],
                    emoji="🏆",
                    timestamp=datetime.now(),
                    trigger_reason=f"milestone_{state.total_questions}_questions",
                )

                state.messages_shown.append(message)
                state.last_message_time = datetime.now()

                logger.info(
                    f"Milestone celebration - Student: {state.student_id}, "
                    f"Milestone: {state.total_questions} questions"
                )

                return message

        # Ardışık doğru milestone'ları
        if state.consecutive_correct in self.streak_milestones:
            streak_key = f"streak_{state.consecutive_correct}"

            if streak_key not in state.milestones_reached:
                state.milestones_reached.append(streak_key)

                message = MotivationMessage(
                    message_type=MessageType.CELEBRATION,
                    message=self.streak_milestones[state.consecutive_correct],
                    emoji="🔥",
                    timestamp=datetime.now(),
                    trigger_reason=f"streak_{state.consecutive_correct}_correct",
                )

                state.messages_shown.append(message)
                state.last_message_time = datetime.now()

                logger.info(
                    f"Streak celebration - Student: {state.student_id}, "
                    f"Streak: {state.consecutive_correct} correct"
                )

                return message

        # Başarı oranı milestone'ları
        if state.total_questions >= 10:  # En az 10 soru sonra
            success_rate_pct = int(state.current_success_rate * 100)

            # %75, %80, %85, %90, %95 başarı oranları
            for threshold in [75, 80, 85, 90, 95]:
                if success_rate_pct >= threshold:
                    rate_key = f"success_rate_{threshold}"

                    if rate_key not in state.milestones_reached:
                        state.milestones_reached.append(rate_key)

                        messages = {
                            75: "Başarı oranın %75'i geçti! Harika! 🌟",
                            80: "Başarı oranın %80! Mükemmel! ⭐",
                            85: "Başarı oranın %85! Muhteşem! 💫",
                            90: "Başarı oranın %90! İnanılmaz! 🏆",
                            95: "Başarı oranın %95! Efsanesin! 👑",
                        }

                        message = MotivationMessage(
                            message_type=MessageType.CELEBRATION,
                            message=messages[threshold],
                            emoji="🎊",
                            timestamp=datetime.now(),
                            trigger_reason=f"success_rate_{threshold}_percent",
                        )

                        state.messages_shown.append(message)
                        state.last_message_time = datetime.now()

                        logger.info(
                            f"Success rate celebration - Student: {state.student_id}, "
                            f"Rate: {threshold}%"
                        )

                        return message

        return None

    # ==================== REQ-49.80: Support Messages ====================

    def generate_support_message(
        self, state: MotivationState
    ) -> Optional[MotivationMessage]:
        """
        Motivasyon düştüğünde destek mesajı oluştur.

        REQ-49.80: Support messages - motivasyon düştüğünde destek mesajları gösterme

        Args:
            state: Motivasyon durumu

        Returns:
            Destek mesajı veya None
        """
        # Mesaj spam önleme
        if not self._should_show_message(state):
            return None

        # Motivasyon düşük mü kontrol et
        if state.motivation_level in [MotivationLevel.VERY_LOW, MotivationLevel.LOW]:
            # Ardışık yanlışlar için özel mesajlar
            if state.consecutive_incorrect >= 3:
                messages = [
                    "Zorlanıyorsun gibi görünüyor. Bir mola vermek ister misin? ☕",
                    "Biraz zor geldi mi? Sakin ol, başarabilirsin! 🌈",
                    "Her zorluk geçicidir. Devam et! 💪",
                    "Yanlışlar öğrenmenin bir parçası. Pes etme! 🌟",
                    "Zorlandığın konuları not al, sonra tekrar et! 📝",
                    "Başarı sabır ister. Sen yapabilirsin! 🎯",
                    "Bir adım geri, iki adım ileri! Devam! 🚀",
                ]

            # Düşük başarı oranı için genel destek
            else:
                messages = [
                    "Başarı oranın biraz düşük. Ama endişelenme, toparlanırsın! 💪",
                    "Zorlanıyorsun ama öğreniyorsun! Bu önemli! 📚",
                    "Her öğrenci zorlanır. Sen de başarabilirsin! 🌟",
                    "Yavaş yavaş ilerliyorsun. Sabırlı ol! 🐢",
                    "Önemli olan pes etmemek. Devam et! 🎯",
                    "Zorluklarla karşılaşmak normaldir. Güçlüsün! 💪",
                    "Başarı yolunda engeller olur. Aşabilirsin! 🚀",
                ]

            message_text = random.choice(messages)

            message = MotivationMessage(
                message_type=MessageType.SUPPORT,
                message=message_text,
                emoji="🤗",
                timestamp=datetime.now(),
                trigger_reason=f"low_motivation_{state.motivation_level.value}",
            )

            state.messages_shown.append(message)
            state.last_message_time = datetime.now()

            logger.info(
                f"Support message generated - Student: {state.student_id}, "
                f"Motivation: {state.motivation_level.value}, "
                f"Message: {message_text}"
            )

            return message

        return None

    # ==================== Helper Methods ====================

    def _should_show_message(self, state: MotivationState) -> bool:
        """
        Mesaj gösterilmeli mi kontrol et (spam önleme).

        Args:
            state: Motivasyon durumu

        Returns:
            Mesaj gösterilmeli mi?
        """
        if state.last_message_time is None:
            return True

        elapsed_seconds = (datetime.now() - state.last_message_time).total_seconds()
        return elapsed_seconds >= self.min_message_interval_seconds

    def initialize_motivation_state(self, student_id: str) -> MotivationState:
        """
        Motivasyon durumunu başlat.

        Args:
            student_id: Öğrenci ID'si

        Returns:
            Başlangıç motivasyon durumu
        """
        return MotivationState(
            student_id=student_id,
            current_success_rate=0.0,
            recent_success_rate=0.0,
            consecutive_correct=0,
            consecutive_incorrect=0,
            total_questions=0,
            correct_answers=0,
            milestones_reached=[],
            messages_shown=[],
            last_message_time=None,
            motivation_level=MotivationLevel.OPTIMAL,
        )

    def process_response(self, state: MotivationState, is_correct: bool) -> Dict:
        """
        Yanıtı işle ve tüm motivasyon mesajlarını oluştur.

        Args:
            state: Motivasyon durumu
            is_correct: Yanıt doğru mu?

        Returns:
            Mesajlar ve güncellenmiş durum
        """
        # Başarı oranını izle (REQ-49.77)
        state = self.monitor_success_rate(state, is_correct)

        messages = []

        # Milestone kutlamaları kontrol et (REQ-49.79)
        milestone_msg = self.check_and_celebrate_milestones(state)
        if milestone_msg:
            messages.append(milestone_msg)

        # Teşvik mesajı oluştur (REQ-49.78)
        encouragement_msg = self.generate_encouragement_message(state, is_correct)
        if encouragement_msg:
            messages.append(encouragement_msg)

        # Destek mesajı kontrol et (REQ-49.80)
        support_msg = self.generate_support_message(state)
        if support_msg:
            messages.append(support_msg)

        return {
            "state": state,
            "messages": messages,
            "success_rate": state.current_success_rate,
            "recent_success_rate": state.recent_success_rate,
            "motivation_level": state.motivation_level.value,
            "is_optimal": self.is_success_rate_optimal(state),
        }

    def get_motivation_summary(self, state: MotivationState) -> Dict:
        """
        Motivasyon özetini al.

        Args:
            state: Motivasyon durumu

        Returns:
            Motivasyon özeti
        """
        return {
            "student_id": state.student_id,
            "total_questions": state.total_questions,
            "correct_answers": state.correct_answers,
            "current_success_rate": state.current_success_rate,
            "recent_success_rate": state.recent_success_rate,
            "motivation_level": state.motivation_level.value,
            "consecutive_correct": state.consecutive_correct,
            "consecutive_incorrect": state.consecutive_incorrect,
            "milestones_reached": state.milestones_reached,
            "total_messages_shown": len(state.messages_shown),
            "is_optimal_range": self.is_success_rate_optimal(state),
        }
