"""
TYT Sınav Sistemi - ÖSYM Formatına Tam Uyumlu
Türkiye Üniversite Sınavları Hazırlık Platformu

Bu modül TYT (Temel Yeterlilik Testi) sınavlarını yönetir:
- 120 soru, 165 dakika (REQ-1.1)
- Konu dağılımı: Türkçe:40, Matematik:40, Fen:20, Sosyal:20 (REQ-1.1, REQ-3.1)
- Optik form arayüzü desteği (REQ-1.1, REQ-1.6)
- Süre takibi ve uyarılar (REQ-1.1, REQ-1.6)
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy import and_, func, select

from core.database import get_db_session_context
from core.structured_logger import get_logger
from models.enums_db import ExamType
from models.question_bank import QuestionBankItem as Question

logger = get_logger("tyt_exam_service")


class TYTSubject(Enum):
    """TYT Konu Alanları"""

    TURKCE = "turkce"
    MATEMATIK = "matematik"
    FEN = "fen"
    SOSYAL = "sosyal"


@dataclass
class TYTExamConfig:
    """
    TYT Sınav Konfigürasyonu - ÖSYM Formatı

    REQ-1.1: 120 soru, 165 dakika
    REQ-3.1: Konu dağılımı kontrolü
    """

    total_questions: int = 120
    duration_minutes: int = 165
    subject_distribution: Dict[str, int] = None

    def __post_init__(self):
        """Varsayılan konu dağılımını ayarla"""
        if self.subject_distribution is None:
            self.subject_distribution = {
                TYTSubject.TURKCE.value: 40,
                TYTSubject.MATEMATIK.value: 40,
                TYTSubject.FEN.value: 20,
                TYTSubject.SOSYAL.value: 20,
            }

    def validate(self) -> bool:
        """
        Konfigürasyonu doğrula

        Returns:
            bool: Konfigürasyon geçerli mi?
        """
        # Toplam soru sayısı kontrolü
        if self.total_questions != 120:
            logger.error(
                f"TYT toplam soru sayısı 120 olmalı, mevcut: {self.total_questions}"
            )
            return False

        # Süre kontrolü
        if self.duration_minutes != 165:
            logger.error(
                f"TYT süresi 165 dakika olmalı, mevcut: {self.duration_minutes}"
            )
            return False

        # Konu dağılımı kontrolü
        total_from_distribution = sum(self.subject_distribution.values())
        if total_from_distribution != self.total_questions:
            logger.error(
                f"Konu dağılımı toplamı {self.total_questions} olmalı, "
                f"mevcut: {total_from_distribution}"
            )
            return False

        # Her konu için minimum soru kontrolü
        required_distribution = {
            TYTSubject.TURKCE.value: 40,
            TYTSubject.MATEMATIK.value: 40,
            TYTSubject.FEN.value: 20,
            TYTSubject.SOSYAL.value: 20,
        }

        for subject, required_count in required_distribution.items():
            actual_count = self.subject_distribution.get(subject, 0)
            if actual_count != required_count:
                logger.error(
                    f"{subject} konusu için {required_count} soru olmalı, "
                    f"mevcut: {actual_count}"
                )
                return False

        return True


@dataclass
class TYTTimer:
    """
    TYT Zamanlayıcı

    REQ-1.1: Dakika hassasiyetinde zamanlayıcı
    REQ-1.6: Süre takibi ve uyarılar
    """

    total_duration_minutes: int = 165
    started_at: Optional[datetime] = None
    warning_times_minutes: List[int] = None

    def __post_init__(self):
        """Varsayılan uyarı zamanlarını ayarla"""
        if self.warning_times_minutes is None:
            # Son 30, 10 ve 5 dakika uyarıları
            self.warning_times_minutes = [30, 10, 5]

    def start(self) -> None:
        """Zamanlayıcıyı başlat"""
        self.started_at = datetime.now()
        logger.info(
            "TYT zamanlayıcı başlatıldı",
            extra_data={
                "started_at": self.started_at.isoformat(),
                "duration_minutes": self.total_duration_minutes,
            },
        )

    def get_remaining_seconds(self) -> Optional[int]:
        """
        Kalan süreyi saniye cinsinden getir

        Returns:
            Optional[int]: Kalan süre (saniye) veya None
        """
        if not self.started_at:
            return None

        elapsed = datetime.now() - self.started_at
        total_duration = timedelta(minutes=self.total_duration_minutes)
        remaining = total_duration - elapsed

        return max(0, int(remaining.total_seconds()))

    def get_remaining_minutes(self) -> Optional[int]:
        """
        Kalan süreyi dakika cinsinden getir

        Returns:
            Optional[int]: Kalan süre (dakika) veya None
        """
        remaining_seconds = self.get_remaining_seconds()
        if remaining_seconds is None:
            return None

        return remaining_seconds // 60

    def should_show_warning(self) -> Optional[int]:
        """
        Uyarı gösterilmeli mi kontrol et

        Returns:
            Optional[int]: Uyarı süresi (dakika) veya None
        """
        remaining_minutes = self.get_remaining_minutes()
        if remaining_minutes is None:
            return None

        for warning_time in sorted(self.warning_times_minutes, reverse=True):
            if remaining_minutes <= warning_time:
                return warning_time

        return None

    def is_expired(self) -> bool:
        """
        Süre doldu mu?

        Returns:
            bool: Süre doldu mu?
        """
        remaining_seconds = self.get_remaining_seconds()
        return remaining_seconds is not None and remaining_seconds == 0

    def format_time(self) -> str:
        """
        Kalan süreyi formatla (HH:MM:SS)

        Returns:
            str: Formatlanmış süre
        """
        remaining_seconds = self.get_remaining_seconds()
        if remaining_seconds is None:
            return "Başlatılmadı"

        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        seconds = remaining_seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"


class TYTExamService:
    """
    TYT Sınav Servisi

    ÖSYM formatına tam uyumlu TYT sınavı yönetimi:
    - REQ-1.1: 120 soru, 165 dakika formatı
    - REQ-1.1, REQ-3.1: Konu dağılımı (Türkçe:40, Mat:40, Fen:20, Sosyal:20)
    - REQ-1.1, REQ-1.6: Optik form arayüzü desteği
    - REQ-1.1, REQ-1.6: Süre takibi ve uyarılar
    """

    def __init__(self):
        self.config = TYTExamConfig()
        self.timers: Dict[str, TYTTimer] = {}

    async def validate_tyt_format(self, session_id: str) -> bool:
        """
        TYT formatını doğrula

        Args:
            session_id: Sınav oturum ID'si

        Returns:
            bool: Format geçerli mi?
        """
        try:
            # Konfigürasyonu doğrula
            if not self.config.validate():
                return False

            # Veritabanından sınav bilgilerini kontrol et
            async with get_db_session_context() as db_session:
                from models.database import ExamSession

                result = await db_session.execute(
                    select(ExamSession).where(ExamSession.id == session_id)
                )
                exam_session = result.scalar_one_or_none()

                if not exam_session:
                    logger.error(f"Sınav oturumu bulunamadı: {session_id}")
                    return False

                # Sınav türü kontrolü
                if exam_session.exam_type != ExamType.TYT:
                    logger.error(
                        f"Sınav türü TYT olmalı, mevcut: {exam_session.exam_type}"
                    )
                    return False

                # Soru sayısı kontrolü
                if exam_session.total_questions != self.config.total_questions:
                    logger.error(
                        f"TYT soru sayısı {self.config.total_questions} olmalı, "
                        f"mevcut: {exam_session.total_questions}"
                    )
                    return False

                # Süre kontrolü
                if exam_session.duration_minutes != self.config.duration_minutes:
                    logger.error(
                        f"TYT süresi {self.config.duration_minutes} dakika olmalı, "
                        f"mevcut: {exam_session.duration_minutes}"
                    )
                    return False

            logger.info(
                "TYT format doğrulaması başarılı", extra_data={"session_id": session_id}
            )
            return True

        except Exception as e:
            logger.error(
                f"TYT format doğrulama hatası: {e}",
                extra_data={"session_id": session_id},
            )
            return False

    async def select_tyt_questions(self) -> List[Question]:
        """
        TYT soruları seç (konu dağılımına göre)

        REQ-1.1, REQ-3.1: Konu dağılımı kontrolü

        Returns:
            List[Question]: Seçilen sorular
        """
        try:
            selected_questions = []

            async with get_db_session_context() as db_session:
                for subject_str, count in self.config.subject_distribution.items():
                    # Soruları getir (question_bank UPPERCASE değerler saklar)
                    result = await db_session.execute(
                        select(Question)
                        .where(
                            and_(
                                Question.exam_type == ExamType.TYT.value.upper(),
                                Question.subject_area == subject_str.upper(),
                                Question.is_active.is_(True),
                            )
                        )
                        .order_by(func.random())
                        .limit(count)
                    )

                    questions = result.scalars().all()

                    if len(questions) < count:
                        logger.warning(
                            f"{subject_str} konusu için yeterli soru yok",
                            extra_data={"required": count, "available": len(questions)},
                        )

                    selected_questions.extend(questions)

            # Toplam soru sayısı kontrolü
            if len(selected_questions) != self.config.total_questions:
                logger.error(
                    f"TYT için {self.config.total_questions} soru seçilmeli, "
                    f"seçilen: {len(selected_questions)}"
                )
                raise ValueError("Yeterli TYT sorusu bulunamadı")

            logger.info(
                "TYT soruları seçildi",
                extra_data={
                    "total_questions": len(selected_questions),
                    "distribution": {
                        subject: len(
                            [
                                q
                                for q in selected_questions
                                if q.subject_area == subject.upper()
                            ]
                        )
                        for subject in self.config.subject_distribution.keys()
                    },
                },
            )

            return selected_questions

        except Exception as e:
            logger.error(f"TYT soru seçimi hatası: {e}")
            raise

    def start_timer(self, session_id: str) -> TYTTimer:
        """
        TYT zamanlayıcısını başlat

        REQ-1.1, REQ-1.6: Süre takibi

        Args:
            session_id: Sınav oturum ID'si

        Returns:
            TYTTimer: Başlatılan zamanlayıcı
        """
        timer = TYTTimer(total_duration_minutes=self.config.duration_minutes)
        timer.start()
        self.timers[session_id] = timer

        # Otomatik tamamlama task'ı başlat
        asyncio.create_task(self._auto_complete_on_timeout(session_id))

        return timer

    def get_timer(self, session_id: str) -> Optional[TYTTimer]:
        """
        Zamanlayıcıyı getir

        Args:
            session_id: Sınav oturum ID'si

        Returns:
            Optional[TYTTimer]: Zamanlayıcı veya None
        """
        return self.timers.get(session_id)

    async def _auto_complete_on_timeout(self, session_id: str) -> None:
        """
        Süre dolduğunda otomatik tamamla

        REQ-1.1, REQ-1.6: Otomatik tamamlama

        Args:
            session_id: Sınav oturum ID'si
        """
        try:
            timer = self.timers.get(session_id)
            if not timer:
                return

            # Süre dolana kadar bekle
            remaining_seconds = timer.get_remaining_seconds()
            if remaining_seconds and remaining_seconds > 0:
                await asyncio.sleep(remaining_seconds)

            # Sınavı otomatik tamamla
            from core.osym_exam_engine import osym_exam_engine

            await osym_exam_engine.complete_exam(session_id, manual_completion=False)

            logger.info(
                "TYT sınavı süre dolduğu için otomatik tamamlandı",
                extra_data={"session_id": session_id},
            )

        except Exception as e:
            logger.error(
                f"TYT otomatik tamamlama hatası: {e}",
                extra_data={"session_id": session_id},
            )

    def get_subject_distribution_info(self) -> Dict[str, Dict[str, int]]:
        """
        Konu dağılımı bilgisini getir

        REQ-1.1, REQ-3.1: Konu dağılımı

        Returns:
            Dict: Konu dağılımı bilgisi
        """
        return {
            "total_questions": self.config.total_questions,
            "duration_minutes": self.config.duration_minutes,
            "subject_distribution": self.config.subject_distribution,
            "subjects": {
                "turkce": {"name": "Türkçe", "question_count": 40, "percentage": 33.3},
                "matematik": {
                    "name": "Matematik",
                    "question_count": 40,
                    "percentage": 33.3,
                },
                "fen": {
                    "name": "Fen Bilimleri",
                    "question_count": 20,
                    "percentage": 16.7,
                },
                "sosyal": {
                    "name": "Sosyal Bilimler",
                    "question_count": 20,
                    "percentage": 16.7,
                },
            },
        }


# Global TYT servis instance
tyt_exam_service = TYTExamService()
