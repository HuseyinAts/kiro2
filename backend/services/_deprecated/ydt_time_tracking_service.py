"""
YDT Süre Takibi ve Uyarı Servisi
Türkiye Üniversite Sınavları Hazırlık Platformu

Bu modül YDT sınavları için süre takibi ve uyarı işlevlerini yönetir:
- Time management for passages (metinler için zaman yönetimi)
- Reading time suggestions (okuma süresi önerileri)
- Completion warnings (tamamlama uyarıları)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from core.structured_logger import get_logger

logger = get_logger("ydt_time_tracking_service")


class WarningLevel(Enum):
    """Uyarı seviyesi"""

    INFO = "info"  # Bilgilendirme
    WARNING = "warning"  # Uyarı
    CRITICAL = "critical"  # Kritik


@dataclass
class TimeWarning:
    """Zaman uyarısı modeli"""

    level: WarningLevel
    message: str
    timestamp: datetime
    remaining_minutes: int
    trigger_type: str  # time_based, completion_based, passage_based


@dataclass
class PassageTimeTracking:
    """Metin okuma süresi takibi"""

    passage_id: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    time_spent_seconds: float = 0.0
    suggested_time_minutes: int = 0
    questions_answered: int = 0
    total_questions: int = 0


@dataclass
class YDTTimeTracking:
    """YDT sınav süresi takibi"""

    exam_session_id: str
    student_id: str

    # Sınav süreleri
    total_duration_minutes: int = 120  # REQ-1.3: YDT 120 dakika
    started_at: datetime | None = None
    expected_end_time: datetime | None = None

    # Metin bazlı süre takibi
    passage_tracking: dict[str, PassageTimeTracking] = field(default_factory=dict)

    # Uyarılar
    warnings_sent: list[TimeWarning] = field(default_factory=list)

    # İstatistikler
    total_time_spent_seconds: float = 0.0
    average_time_per_question: float = 0.0
    questions_answered: int = 0


class YDTTimeTrackingService:
    """
    YDT Süre Takibi ve Uyarı Servisi

    Bu servis YDT sınavları için süre yönetimi işlevlerini sağlar:
    - Metin bazlı zaman yönetimi
    - Okuma süresi önerileri
    - Otomatik uyarılar
    """

    def __init__(self):
        # Uyarı eşikleri (dakika) - REQ-1.3, REQ-1.6
        self.warning_thresholds = {
            "critical": [5, 10],  # Son 5 ve 10 dakika
            "warning": [15, 30],  # 15 ve 30 dakika kala
            "info": [60, 90],  # 60 ve 90 dakika kala
        }

        # Okuma hızı varsayımları (kelime/dakika)
        self.reading_speeds = {
            "slow": 100,  # Yavaş okuyucu
            "average": 150,  # Ortalama okuyucu
            "fast": 200,  # Hızlı okuyucu
        }

        # Soru başına ortalama süre (dakika)
        self.time_per_question = {
            "reading_comprehension": 1.5,  # Okuma anlama
            "grammar": 1.0,  # Dilbilgisi
            "vocabulary": 0.8,  # Kelime bilgisi
        }

    def start_tracking(
        self, exam_session_id: str, student_id: str, duration_minutes: int = 120
    ) -> YDTTimeTracking:
        """
        Süre takibini başlat - REQ-1.3, REQ-1.6

        Args:
            exam_session_id: Sınav oturum ID
            student_id: Öğrenci ID
            duration_minutes: Sınav süresi (dakika)

        Returns:
            YDTTimeTracking: Süre takibi objesi
        """
        now = datetime.now()

        tracking = YDTTimeTracking(
            exam_session_id=exam_session_id,
            student_id=student_id,
            total_duration_minutes=duration_minutes,
            started_at=now,
            expected_end_time=now + timedelta(minutes=duration_minutes),
        )

        logger.info(
            "YDT süre takibi başlatıldı",
            extra_data={
                "exam_session_id": exam_session_id,
                "student_id": student_id,
                "duration_minutes": duration_minutes,
                "expected_end_time": tracking.expected_end_time.isoformat(),
            },
        )

        return tracking

    def calculate_remaining_time(self, tracking: YDTTimeTracking) -> int:
        """
        Kalan süreyi hesapla - REQ-1.3, REQ-1.6

        Args:
            tracking: Süre takibi objesi

        Returns:
            int: Kalan süre (dakika)
        """
        if not tracking.expected_end_time:
            return 0

        now = datetime.now()
        remaining = tracking.expected_end_time - now

        return max(0, int(remaining.total_seconds() / 60))

    def suggest_reading_time(
        self, word_count: int, questions_count: int, reading_speed: str = "average"
    ) -> int:
        """
        Okuma süresi önerisi hesapla - REQ-1.3, REQ-1.6

        Args:
            word_count: Kelime sayısı
            questions_count: Soru sayısı
            reading_speed: Okuma hızı (slow, average, fast)

        Returns:
            int: Önerilen süre (dakika)
        """
        speed = self.reading_speeds.get(reading_speed, self.reading_speeds["average"])

        # Metin okuma süresi
        reading_time = word_count / speed

        # Soru cevaplama süresi (okuma anlama soruları için)
        question_time = (
            questions_count * self.time_per_question["reading_comprehension"]
        )

        # Toplam önerilen süre
        total_time = reading_time + question_time

        # Minimum 5 dakika, maksimum 20 dakika
        return max(5, min(20, int(total_time)))

    def start_passage_tracking(
        self,
        tracking: YDTTimeTracking,
        passage_id: str,
        word_count: int,
        total_questions: int,
    ) -> PassageTimeTracking:
        """
        Metin okuma takibini başlat - REQ-1.3, REQ-1.6

        Args:
            tracking: Süre takibi objesi
            passage_id: Metin ID
            word_count: Kelime sayısı
            total_questions: Toplam soru sayısı

        Returns:
            PassageTimeTracking: Metin takibi objesi
        """
        suggested_time = self.suggest_reading_time(word_count, total_questions)

        passage_tracking = PassageTimeTracking(
            passage_id=passage_id,
            started_at=datetime.now(),
            suggested_time_minutes=suggested_time,
            total_questions=total_questions,
        )

        tracking.passage_tracking[passage_id] = passage_tracking

        logger.debug(
            f"Metin takibi başlatıldı: {passage_id}",
            extra_data={
                "word_count": word_count,
                "total_questions": total_questions,
                "suggested_time": suggested_time,
            },
        )

        return passage_tracking

    def complete_passage_tracking(
        self, tracking: YDTTimeTracking, passage_id: str, questions_answered: int
    ) -> PassageTimeTracking | None:
        """
        Metin okuma takibini tamamla - REQ-1.3, REQ-1.6

        Args:
            tracking: Süre takibi objesi
            passage_id: Metin ID
            questions_answered: Cevaplanan soru sayısı

        Returns:
            Optional[PassageTimeTracking]: Tamamlanan metin takibi
        """
        if passage_id not in tracking.passage_tracking:
            return None

        passage_tracking = tracking.passage_tracking[passage_id]
        passage_tracking.completed_at = datetime.now()
        passage_tracking.questions_answered = questions_answered

        if passage_tracking.started_at:
            time_spent = (
                passage_tracking.completed_at - passage_tracking.started_at
            ).total_seconds()
            passage_tracking.time_spent_seconds = time_spent

        logger.debug(
            f"Metin takibi tamamlandı: {passage_id}",
            extra_data={
                "time_spent_seconds": passage_tracking.time_spent_seconds,
                "questions_answered": questions_answered,
                "suggested_time": passage_tracking.suggested_time_minutes,
            },
        )

        return passage_tracking

    def check_and_generate_warnings(
        self, tracking: YDTTimeTracking, answered_count: int, total_questions: int = 80
    ) -> list[TimeWarning]:
        """
        Uyarıları kontrol et ve oluştur - REQ-1.3, REQ-1.6

        Args:
            tracking: Süre takibi objesi
            answered_count: Cevaplanan soru sayısı
            total_questions: Toplam soru sayısı

        Returns:
            List[TimeWarning]: Yeni uyarılar
        """
        new_warnings = []
        remaining_minutes = self.calculate_remaining_time(tracking)
        unanswered = total_questions - answered_count

        # Zaman bazlı uyarılar
        time_warnings = self._check_time_warnings(tracking, remaining_minutes)
        new_warnings.extend(time_warnings)

        # Tamamlanma bazlı uyarılar
        completion_warnings = self._check_completion_warnings(
            tracking, remaining_minutes, answered_count, unanswered
        )
        new_warnings.extend(completion_warnings)

        # Uyarıları kaydet
        tracking.warnings_sent.extend(new_warnings)

        return new_warnings

    def _check_time_warnings(
        self, tracking: YDTTimeTracking, remaining_minutes: int
    ) -> list[TimeWarning]:
        """
        Zaman bazlı uyarıları kontrol et - REQ-1.3, REQ-1.6

        Args:
            tracking: Süre takibi objesi
            remaining_minutes: Kalan süre (dakika)

        Returns:
            List[TimeWarning]: Uyarılar
        """
        warnings = []

        # Kritik uyarılar (5, 10 dakika)
        for threshold in self.warning_thresholds["critical"]:
            if remaining_minutes == threshold:
                # Bu uyarı daha önce gönderilmiş mi kontrol et
                if not self._warning_already_sent(tracking, f"time_{threshold}"):
                    warning = TimeWarning(
                        level=WarningLevel.CRITICAL,
                        message=f"🚨 UYARI: Son {threshold} dakika! Lütfen cevaplarınızı kontrol edin.",
                        timestamp=datetime.now(),
                        remaining_minutes=remaining_minutes,
                        trigger_type=f"time_{threshold}",
                    )
                    warnings.append(warning)

        # Uyarılar (15, 30 dakika)
        for threshold in self.warning_thresholds["warning"]:
            if remaining_minutes == threshold:
                if not self._warning_already_sent(tracking, f"time_{threshold}"):
                    warning = TimeWarning(
                        level=WarningLevel.WARNING,
                        message=f"⏰ {threshold} dakika kaldı. Zamanınızı iyi yönetin.",
                        timestamp=datetime.now(),
                        remaining_minutes=remaining_minutes,
                        trigger_type=f"time_{threshold}",
                    )
                    warnings.append(warning)

        # Bilgilendirme (60, 90 dakika)
        for threshold in self.warning_thresholds["info"]:
            if remaining_minutes == threshold:
                if not self._warning_already_sent(tracking, f"time_{threshold}"):
                    warning = TimeWarning(
                        level=WarningLevel.INFO,
                        message=f"📝 {threshold} dakika kaldı. İyi gidiyorsunuz!",
                        timestamp=datetime.now(),
                        remaining_minutes=remaining_minutes,
                        trigger_type=f"time_{threshold}",
                    )
                    warnings.append(warning)

        return warnings

    def _check_completion_warnings(
        self,
        tracking: YDTTimeTracking,
        remaining_minutes: int,
        answered_count: int,
        unanswered: int,
    ) -> list[TimeWarning]:
        """
        Tamamlanma bazlı uyarıları kontrol et - REQ-1.3, REQ-1.6

        Args:
            tracking: Süre takibi objesi
            remaining_minutes: Kalan süre (dakika)
            answered_count: Cevaplanan soru sayısı
            unanswered: Boş soru sayısı

        Returns:
            List[TimeWarning]: Uyarılar
        """
        warnings = []

        # Tüm sorular cevaplandı
        if unanswered == 0 and not self._warning_already_sent(
            tracking, "all_completed"
        ):
            warning = TimeWarning(
                level=WarningLevel.INFO,
                message="✅ Tüm soruları cevapladınız! İsterseniz cevaplarınızı gözden geçirebilirsiniz.",
                timestamp=datetime.now(),
                remaining_minutes=remaining_minutes,
                trigger_type="all_completed",
            )
            warnings.append(warning)

        # Son 10 dakika ve çok fazla boş soru
        if remaining_minutes <= 10 and unanswered > 10:
            if not self._warning_already_sent(tracking, "many_unanswered_10min"):
                warning = TimeWarning(
                    level=WarningLevel.CRITICAL,
                    message=f"⚠️ {unanswered} soru boş! Kalan süre: {remaining_minutes} dakika. Hızlı cevap vermeye çalışın.",
                    timestamp=datetime.now(),
                    remaining_minutes=remaining_minutes,
                    trigger_type="many_unanswered_10min",
                )
                warnings.append(warning)

        # Son 5 dakika ve boş soru var
        if remaining_minutes <= 5 and unanswered > 0:
            if not self._warning_already_sent(tracking, "unanswered_5min"):
                warning = TimeWarning(
                    level=WarningLevel.CRITICAL,
                    message=f"🚨 UYARI: {unanswered} soru boş! Son {remaining_minutes} dakika!",
                    timestamp=datetime.now(),
                    remaining_minutes=remaining_minutes,
                    trigger_type="unanswered_5min",
                )
                warnings.append(warning)

        # Yarı yolda ve çok yavaş ilerleme
        if remaining_minutes <= 60 and answered_count < 40:
            if not self._warning_already_sent(tracking, "slow_progress"):
                warning = TimeWarning(
                    level=WarningLevel.WARNING,
                    message=f"⏱️ Yarı süre geçti ama sadece {answered_count} soru cevaplandı. Hızlanmanız önerilir.",
                    timestamp=datetime.now(),
                    remaining_minutes=remaining_minutes,
                    trigger_type="slow_progress",
                )
                warnings.append(warning)

        return warnings

    def _warning_already_sent(
        self, tracking: YDTTimeTracking, trigger_type: str
    ) -> bool:
        """
        Uyarı daha önce gönderilmiş mi kontrol et

        Args:
            tracking: Süre takibi objesi
            trigger_type: Uyarı tetikleyici tipi

        Returns:
            bool: Daha önce gönderilmiş mi?
        """
        return any(
            warning.trigger_type == trigger_type for warning in tracking.warnings_sent
        )

    def get_time_management_suggestions(
        self, tracking: YDTTimeTracking, answered_count: int, total_questions: int = 80
    ) -> list[str]:
        """
        Zaman yönetimi önerileri getir - REQ-1.3, REQ-1.6

        Args:
            tracking: Süre takibi objesi
            answered_count: Cevaplanan soru sayısı
            total_questions: Toplam soru sayısı

        Returns:
            List[str]: Öneriler
        """
        suggestions = []
        remaining_minutes = self.calculate_remaining_time(tracking)
        unanswered = total_questions - answered_count

        if unanswered > 0:
            # Kalan soru başına ortalama süre
            time_per_question = remaining_minutes / unanswered if unanswered > 0 else 0

            if time_per_question < 1:
                suggestions.append(
                    f"⚡ Her soru için yaklaşık {time_per_question:.1f} dakika süreniz var. "
                    "Hızlı karar vermeye çalışın."
                )
            elif time_per_question < 1.5:
                suggestions.append(
                    f"⏱️ Her soru için yaklaşık {time_per_question:.1f} dakika süreniz var. "
                    "Dengeli bir tempo tutun."
                )
            else:
                suggestions.append(
                    f"✅ Her soru için yaklaşık {time_per_question:.1f} dakika süreniz var. "
                    "Rahat bir tempoda ilerleyebilirsiniz."
                )

        # Metin bazlı öneriler
        for passage_id, passage_tracking in tracking.passage_tracking.items():
            if passage_tracking.started_at and not passage_tracking.completed_at:
                elapsed = (
                    datetime.now() - passage_tracking.started_at
                ).total_seconds() / 60
                if elapsed > passage_tracking.suggested_time_minutes:
                    suggestions.append(
                        "📖 Mevcut metinde önerilen süreden fazla zaman harcıyorsunuz. "
                        "Sorulara geçmeyi düşünebilirsiniz."
                    )

        return suggestions

    def calculate_statistics(self, tracking: YDTTimeTracking) -> dict[str, any]:
        """
        Zaman istatistiklerini hesapla - REQ-1.3, REQ-1.6

        Args:
            tracking: Süre takibi objesi

        Returns:
            Dict: İstatistikler
        """
        if not tracking.started_at:
            return {}

        elapsed_time = (datetime.now() - tracking.started_at).total_seconds()
        remaining_minutes = self.calculate_remaining_time(tracking)

        stats = {
            "elapsed_minutes": int(elapsed_time / 60),
            "remaining_minutes": remaining_minutes,
            "total_duration_minutes": tracking.total_duration_minutes,
            "completion_percentage": (
                elapsed_time / (tracking.total_duration_minutes * 60)
            )
            * 100,
            "average_time_per_question": tracking.average_time_per_question,
            "questions_answered": tracking.questions_answered,
            "warnings_count": len(tracking.warnings_sent),
        }

        # Metin bazlı istatistikler
        passage_stats = []
        for passage_id, passage_tracking in tracking.passage_tracking.items():
            if passage_tracking.completed_at:
                passage_stats.append(
                    {
                        "passage_id": passage_id,
                        "time_spent_minutes": passage_tracking.time_spent_seconds / 60,
                        "suggested_time_minutes": passage_tracking.suggested_time_minutes,
                        "questions_answered": passage_tracking.questions_answered,
                        "total_questions": passage_tracking.total_questions,
                    }
                )

        stats["passage_statistics"] = passage_stats

        return stats


# Global YDT time tracking service instance
ydt_time_tracking_service = YDTTimeTrackingService()
