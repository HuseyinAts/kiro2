"""
ÖSYM Uyumlu Sınav Motoru - Ana Motor Sınıfı
Türkiye Üniversite Sınavları Hazırlık Platformu

Bu modül ÖSYM formatında TYT/AYT/YDT sınavlarını yönetir:
- Sınav oturumu yönetimi ve otomatik kaydetme
- Performans analizi ve konu bazlı puanlama
- Gerçek zamanlı sınav takibi
- IRT tabanlı soru analizi
"""

import asyncio
import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import and_, func, or_, select, update

from core.database import get_db_session_context
from core.structured_logger import get_logger
from models.database import (
    ExamQuestion,
    ExamSession,
    ExamType,
    StudentAnswer,
)
from models.question_bank import QuestionBankItem as Question

logger = get_logger("osym_exam_engine")


class ExamStatus(Enum):
    """Sınav durumu enum'u"""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    EXPIRED = "expired"


class AYTFieldType(Enum):
    """AYT alan türleri"""

    SAYISAL = "sayisal"  # Sayısal Alan (Mat, Fizik, Kimya, Biyoloji)
    SOZEL = "sozel"  # Sözel Alan (Edebiyat, Tarih, Coğrafya, Felsefe, Din)
    ESIT_AGIRLIK = "esit_agirlik"  # Eşit Ağırlık (Dengeli dağılım)
    DIL = "dil"  # Dil Alan (Yabancı Dil ağırlıklı)


class YDTLanguage(Enum):
    """YDT dil seçenekleri - REQ-1.3"""

    ENGLISH = "english"  # İngilizce
    GERMAN = "german"  # Almanca
    FRENCH = "french"  # Fransızca


@dataclass
class OSYMExamConfig:
    """ÖSYM sınav konfigürasyonu"""

    exam_type: ExamType
    total_questions: int
    duration_minutes: int
    subject_distribution: dict[str, int]
    auto_save_interval: int = 30  # saniye
    warning_time_minutes: int = 15  # son 15 dakika uyarısı
    ayt_field_type: AYTFieldType | None = None  # AYT için alan türü
    ydt_language: YDTLanguage | None = None  # YDT için dil seçimi - REQ-1.3
    difficulty: str | None = None  # "kolay", "orta", "zor", "cok_zor"


@dataclass
class ExamPerformanceMetrics:
    """Sınav performans metrikleri"""

    total_questions: int
    answered_questions: int
    correct_answers: int
    wrong_answers: int
    empty_answers: int
    net_score: float
    raw_score: float
    percentile: float | None = None
    estimated_ability: float = 0.0
    confidence_level: float = 0.0


@dataclass
class SubjectPerformance:
    """Konu bazlı performans"""

    subject: str
    total_questions: int
    correct_answers: int
    wrong_answers: int
    empty_answers: int
    success_rate: float
    average_response_time: float
    difficulty_level: float


@dataclass
class ExamSessionData:
    """Sınav oturum verisi"""

    session_id: str
    student_id: str
    exam_config: OSYMExamConfig
    status: ExamStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    current_question_index: int = 0
    questions: list[str] = field(default_factory=list)
    answers: dict[str, str] = field(default_factory=dict)
    flagged_questions: list[str] = field(default_factory=list)
    time_spent_per_question: dict[str, float] = field(default_factory=dict)
    last_auto_save: datetime | None = None
    performance_metrics: ExamPerformanceMetrics | None = None


class OSYMExamEngine:
    """
    ÖSYM Uyumlu Sınav Motoru

    Bu sınıf ÖSYM formatında sınavları yönetir ve aşağıdaki özellikleri sağlar:
    - TYT/AYT/YDT format desteği
    - Otomatik kaydetme ve oturum yönetimi
    - Performans analizi ve konu bazlı puanlama
    - IRT tabanlı soru seçimi ve analizi
    """

    def __init__(self):
        self.active_sessions: dict[str, ExamSessionData] = {}
        self.auto_save_tasks: dict[str, asyncio.Task] = {}

        # ÖSYM sınav konfigürasyonları
        # subject_distribution keys MUST match question_bank.subject_area (UPPERCASE)
        # DB aktif soru dağılımı (Mart 2026):
        #   TYT: MATEMATIK 11593, TURKCE 10885, GEOMETRI 8709, FIZIK 4139,
        #        KIMYA 3520, BIYOLOJI 1520, TARIH 1593, SOSYAL 1188, COGRAFYA 396
        #   AYT: MATEMATIK 6845, EDEBIYAT 3707, KIMYA 2525, FIZIK 2399,
        #        BIYOLOJI 998, GEOMETRI 785, TARIH 783
        self.exam_configs = {
            ExamType.TYT: OSYMExamConfig(
                exam_type=ExamType.TYT,
                total_questions=120,
                duration_minutes=165,
                subject_distribution={
                    # Türkçe (40 soru)
                    "TURKCE": 40,
                    # Matematik (40 soru = 26 mat + 14 geo)
                    "MATEMATIK": 26,
                    "GEOMETRI": 14,
                    # Fen Bilimleri (20 soru = fizik + kimya + biyoloji)
                    "FIZIK": 7,
                    "KIMYA": 7,
                    "BIYOLOJI": 6,
                    # Sosyal Bilimler (20 soru = tarih + coğrafya + sosyal)
                    "TARIH": 10,
                    "COGRAFYA": 3,
                    "SOSYAL": 7,
                },
            ),
            ExamType.AYT: OSYMExamConfig(
                exam_type=ExamType.AYT,
                total_questions=160,  # REQ-1.2: AYT 160 soru
                duration_minutes=210,  # REQ-1.2: AYT 210 dakika (3.5 saat)
                subject_distribution={
                    # Sayısal Alan (80 soru)
                    "MATEMATIK": 30,
                    "GEOMETRI": 10,
                    "FIZIK": 14,
                    "KIMYA": 13,
                    "BIYOLOJI": 13,
                    # Sözel Alan (80 soru)
                    # NOT: DB'de FELSEFE/DIN/INGILIZCE yok, COGRAFYA az (AYT'de 0)
                    # TARIH_1+TARIH_2 → TARIH, redistribution yapıldı
                    "EDEBIYAT": 38,
                    "TARIH": 42,
                },
                ayt_field_type=AYTFieldType.ESIT_AGIRLIK,  # Varsayılan: Eşit Ağırlık
            ),
            ExamType.YDT: OSYMExamConfig(
                exam_type=ExamType.YDT,
                total_questions=80,  # REQ-1.3: YDT 80 soru
                duration_minutes=120,  # REQ-1.3: YDT 120 dakika (2 saat)
                # YDT devre dışı: DB'de INGILIZCE sorusu yok
                # Sınav başlatıldığında _select_questions 0 soru döner
                subject_distribution={"INGILIZCE": 80},  # Varsayılan: İngilizce
            ),
        }

        # YDT dil bazlı konfigürasyonlar - REQ-1.3
        # ÖSYM Resmi YDT Formatı: 80 soru, 120 dakika
        self.ydt_language_configs = {
            YDTLanguage.ENGLISH: {
                "INGILIZCE": 80,  # İngilizce (Reading comprehension, Grammar, Vocabulary)
            },
            YDTLanguage.GERMAN: {
                "ALMANCA": 80,  # Almanca (Reading comprehension, Grammar, Vocabulary)
            },
            YDTLanguage.FRENCH: {
                "FRANSIZCA": 80,  # Fransızca (Reading comprehension, Grammar, Vocabulary)
            },
        }

        # AYT alan bazlı konfigürasyonlar - REQ-1.2, REQ-3.1
        # ÖSYM Resmi AYT Formatı: 160 soru (Sayısal 80 + Sözel 80)
        # AYT alan bazlı konfigürasyonlar - REQ-1.2, REQ-3.1
        # Keys MUST match question_bank.subject_area (UPPERCASE)
        # DB'de AYT: MATEMATIK 6845, EDEBIYAT 3707, KIMYA 2525, FIZIK 2399,
        #            BIYOLOJI 998, GEOMETRI 785, TARIH 783
        # NOT: FELSEFE, DIN, COGRAFYA AYT'de yok → redistribution yapıldı
        self.ayt_field_configs = {
            AYTFieldType.SAYISAL: {
                # Sayısal bölüm (80 soru)
                "MATEMATIK": 30,
                "GEOMETRI": 10,
                "FIZIK": 14,
                "KIMYA": 13,
                "BIYOLOJI": 13,
                # Sözel'den sadece Edebiyat
                "EDEBIYAT": 24,
            },  # Toplam: 104 soru
            AYTFieldType.SOZEL: {
                # Sözel bölüm (80 soru) — FELSEFE/DIN yok, redistribution
                "EDEBIYAT": 38,
                "TARIH": 42,
                # Sayısal'dan Matematik (40 soru)
                "MATEMATIK": 30,
                "GEOMETRI": 10,
            },  # Toplam: 120 soru
            AYTFieldType.ESIT_AGIRLIK: {
                # Tüm sorular (160 soru) — matches exam_configs[AYT]
                "MATEMATIK": 30,
                "GEOMETRI": 10,
                "FIZIK": 14,
                "KIMYA": 13,
                "BIYOLOJI": 13,
                "EDEBIYAT": 38,
                "TARIH": 42,
            },  # Toplam: 160 soru
            AYTFieldType.DIL: {
                # Sadece Edebiyat (24 soru)
                # YDT ayrı oturum (80 soru)
                "EDEBIYAT": 24,
            },  # Toplam: 24 soru (AYT kısmı)
        }

    async def create_exam_session(
        self,
        student_id: str,
        exam_type: ExamType,
        custom_config: dict[str, Any] | None = None,
    ) -> str:
        """
        Yeni sınav oturumu oluştur

        Args:
            student_id: Öğrenci ID'si
            exam_type: Sınav türü (TYT/AYT/YDT)
            custom_config: Özel sınav konfigürasyonu
                - ayt_field_type: AYT alan türü (sayisal/sozel/esit_agirlik/dil)
                - duration_minutes: Özel süre
                - subject_distribution: Özel konu dağılımı

        Returns:
            str: Sınav oturum ID'si
        """
        try:
            session_id = str(uuid.uuid4())

            # Sınav konfigürasyonunu al (deepcopy — shared config'i korumak icin)
            exam_config = copy.deepcopy(self.exam_configs[exam_type])

            # AYT için alan türüne göre konfigürasyon seç - REQ-1.2, REQ-3.1
            if (
                exam_type == ExamType.AYT
                and custom_config
                and "ayt_field_type" in custom_config
            ):
                field_type_str = custom_config["ayt_field_type"]
                try:
                    field_type = AYTFieldType(field_type_str)
                    exam_config.ayt_field_type = field_type
                    exam_config.subject_distribution = self.ayt_field_configs[
                        field_type
                    ].copy()

                    logger.info(
                        f"AYT alan türü seçildi: {field_type.value}",
                        extra_data={
                            "session_id": session_id,
                            "student_id": student_id,
                            "field_type": field_type.value,
                        },
                    )
                except ValueError:
                    logger.warning(
                        f"Geçersiz AYT alan türü: {field_type_str}, varsayılan kullanılıyor",
                        extra_data={"student_id": student_id},
                    )

            # YDT için dil seçimine göre konfigürasyon seç - REQ-1.3
            if (
                exam_type == ExamType.YDT
                and custom_config
                and "ydt_language" in custom_config
            ):
                language_str = custom_config["ydt_language"]
                try:
                    language = YDTLanguage(language_str)
                    exam_config.ydt_language = language
                    exam_config.subject_distribution = self.ydt_language_configs[
                        language
                    ].copy()

                    logger.info(
                        f"YDT dil seçildi: {language.value}",
                        extra_data={
                            "session_id": session_id,
                            "student_id": student_id,
                            "language": language.value,
                        },
                    )
                except ValueError:
                    logger.warning(
                        f"Geçersiz YDT dil: {language_str}, varsayılan (İngilizce) kullanılıyor",
                        extra_data={"student_id": student_id},
                    )

            # Özel konfigürasyonları uygula
            if custom_config:
                if "duration_minutes" in custom_config:
                    exam_config.duration_minutes = custom_config["duration_minutes"]
                if "time_limit" in custom_config:
                    exam_config.duration_minutes = custom_config["time_limit"]
                if "question_count" in custom_config:
                    total = custom_config["question_count"]
                    # Soru dağılımını oransal olarak yeniden hesapla
                    old_total = sum(exam_config.subject_distribution.values())
                    if old_total > 0:
                        exam_config.subject_distribution = {
                            subj: max(1, round(cnt * total / old_total))
                            for subj, cnt in exam_config.subject_distribution.items()
                        }
                    exam_config.total_questions = total
                if "subject" in custom_config:
                    # Tek ders sınavı: sadece seçilen dersten soru al
                    subject_key = str(custom_config["subject"]).upper()
                    SUBJECT_MAP = {
                        "MATEMATIK": "MATEMATIK",
                        "GEOMETRI": "GEOMETRI",
                        "TURKCE": "TURKCE",
                        "TÜRKÇE": "TURKCE",
                        "FEN BILIMLERI": "FEN",
                        "FEN": "FEN",
                        "FIZIK": "FIZIK",
                        "KIMYA": "KIMYA",
                        "BIYOLOJI": "BIYOLOJI",
                        "SOSYAL BILIMLER": "SOSYAL",
                        "SOSYAL": "SOSYAL",
                        "TARIH": "TARIH",
                        "COGRAFYA": "COGRAFYA",
                        "EDEBIYAT": "EDEBIYAT",
                        "INGILIZCE": "INGILIZCE",
                    }
                    mapped = SUBJECT_MAP.get(subject_key, subject_key)
                    q_count = custom_config.get(
                        "question_count", exam_config.total_questions
                    )
                    exam_config.subject_distribution = {mapped: q_count}
                    exam_config.total_questions = q_count
                if "subject_distribution" in custom_config:
                    exam_config.subject_distribution.update(
                        custom_config["subject_distribution"]
                    )
                if "difficulty" in custom_config:
                    difficulty_val = str(custom_config["difficulty"]).lower()
                    valid_difficulties = {"kolay", "orta", "zor", "cok_zor"}
                    if difficulty_val in valid_difficulties:
                        exam_config.difficulty = difficulty_val
                    else:
                        logger.warning(f"Gecersiz zorluk seviyesi: {difficulty_val}")

            # Soruları seç
            questions = await self._select_questions(exam_config)

            if len(questions) < exam_config.total_questions:
                raise ValueError(
                    f"Yeterli soru bulunamadı. Gerekli: {exam_config.total_questions}, "
                    f"Mevcut: {len(questions)}"
                )

            # Sınav oturumu oluştur
            session_data = ExamSessionData(
                session_id=session_id,
                student_id=str(student_id),
                exam_config=exam_config,
                status=ExamStatus.NOT_STARTED,
                questions=[q.id for q in questions],
            )

            # Veritabanına kaydet
            async with get_db_session_context() as db_session:
                db_exam_session = ExamSession(
                    id=session_id,
                    student_id=str(student_id),
                    exam_type=exam_type,
                    exam_name=f"{exam_type.value.upper()} Denemesi",
                    total_questions=exam_config.total_questions,
                    duration_minutes=exam_config.duration_minutes,
                    status=ExamStatus.NOT_STARTED.value,
                )

                db_session.add(db_exam_session)

                # Sınav sorularını kaydet
                for index, question in enumerate(questions):
                    exam_question = ExamQuestion(
                        exam_session_id=session_id,
                        question_id=question.id,
                        question_order=index + 1,
                    )
                    db_session.add(exam_question)

                await db_session.commit()

            # Aktif oturumlara ekle
            self.active_sessions[session_id] = session_data

            # Redis L2 persist (survives restart)
            from core.exam_session_store import persist_session

            await persist_session(session_data)

            logger.info(
                "Sınav oturumu oluşturuldu",
                extra_data={
                    "session_id": session_id,
                    "student_id": student_id,
                    "exam_type": exam_type.value,
                    "total_questions": len(questions),
                },
            )

            return session_id

        except Exception as e:
            logger.error(
                f"Sınav oturumu oluşturma hatası: {e}",
                extra_data={"student_id": student_id, "exam_type": exam_type.value},
            )
            raise

    async def start_exam(self, session_id: str) -> ExamSessionData:
        """
        Sınavı başlat

        Args:
            session_id: Sınav oturum ID'si

        Returns:
            ExamSessionData: Güncellenmiş sınav oturum verisi
        """
        try:
            if session_id not in self.active_sessions:
                raise ValueError("Sınav oturumu bulunamadı")

            session_data = self.active_sessions[session_id]

            if session_data.status != ExamStatus.NOT_STARTED:
                raise ValueError("Sınav zaten başlatılmış veya tamamlanmış")

            # Sınavı başlat
            session_data.status = ExamStatus.IN_PROGRESS
            session_data.started_at = datetime.now()

            # Veritabanını güncelle
            async with get_db_session_context() as db_session:
                await db_session.execute(
                    update(ExamSession)
                    .where(ExamSession.id == session_id)
                    .values(
                        status=ExamStatus.IN_PROGRESS.value,
                        started_at=session_data.started_at,
                    )
                )
                await db_session.commit()

            # Redis L2 persist
            from core.exam_session_store import persist_session

            await persist_session(session_data)

            # Otomatik kaydetme task'ını başlat
            self.auto_save_tasks[session_id] = asyncio.create_task(
                self._auto_save_task(session_id)
            )

            # Otomatik tamamlama task'ını başlat
            asyncio.create_task(self._auto_complete_task(session_id))

            logger.info(
                "Sınav başlatıldı",
                extra_data={
                    "session_id": session_id,
                    "student_id": session_data.student_id,
                    "started_at": session_data.started_at.isoformat(),
                },
            )

            return session_data

        except Exception as e:
            logger.error(
                f"Sınav başlatma hatası: {e}", extra_data={"session_id": session_id}
            )
            raise

    async def get_current_question(self, session_id: str) -> Question | None:
        """
        Mevcut soruyu getir

        Args:
            session_id: Sınav oturum ID'si

        Returns:
            Optional[Question]: Mevcut soru veya None
        """
        try:
            if session_id not in self.active_sessions:
                return None

            session_data = self.active_sessions[session_id]

            if session_data.status != ExamStatus.IN_PROGRESS:
                return None

            if session_data.current_question_index >= len(session_data.questions):
                return None

            question_id = session_data.questions[session_data.current_question_index]

            async with get_db_session_context() as db_session:
                result = await db_session.execute(
                    select(Question).where(
                        Question.id == question_id, Question.is_active == True
                    )
                )
                question = result.scalar_one_or_none()

                return question

        except Exception as e:
            logger.error(
                f"Mevcut soru getirme hatası: {e}",
                extra_data={"session_id": session_id},
            )
            return None

    async def save_answer(
        self,
        session_id: str,
        question_id: str,
        selected_answer: str | None,
        response_time: float | None = None,
    ) -> bool:
        """
        Cevap kaydet

        Args:
            session_id: Sınav oturum ID'si
            question_id: Soru ID'si
            selected_answer: Seçilen cevap (A, B, C, D, E veya None)
            response_time: Cevaplama süresi (saniye)

        Returns:
            bool: Kaydetme başarı durumu
        """
        try:
            if session_id not in self.active_sessions:
                return False

            session_data = self.active_sessions[session_id]

            if session_data.status != ExamStatus.IN_PROGRESS:
                return False

            # Cevabı kaydet (normalize: uppercase + strip)
            if selected_answer:
                session_data.answers[question_id] = selected_answer.strip().upper()
            elif question_id in session_data.answers:
                del session_data.answers[question_id]

            # Cevaplama süresini kaydet
            if response_time:
                session_data.time_spent_per_question[question_id] = response_time

            # Veritabanına kaydet — UPSERT (SELECT+UPDATE/INSERT yerine tek islem)
            async with get_db_session_context() as db_session:
                # Normalize answer for DB consistency (uppercase + strip)
                normalized_answer = (
                    selected_answer.strip().upper()
                    if selected_answer
                    else selected_answer
                )

                from sqlalchemy.dialects.postgresql import insert as pg_insert

                stmt = pg_insert(StudentAnswer).values(
                    id=str(uuid.uuid4()),
                    exam_session_id=session_id,
                    question_id=question_id,
                    selected_answer=normalized_answer,
                    response_time_seconds=response_time or 0.0,
                )
                stmt = stmt.on_conflict_do_update(
                    constraint="uq_student_answer",
                    set_={
                        "selected_answer": normalized_answer,
                        "response_time_seconds": response_time or 0.0,
                        "answered_at": datetime.now(),
                        "answer_changes": StudentAnswer.answer_changes + 1,
                    },
                )
                await db_session.execute(stmt)
                await db_session.commit()

            # Redis L2 persist (periodic, not every answer for performance)
            # Persist every 5th answer or when flagged
            if len(session_data.answers) % 5 == 0:
                from core.exam_session_store import persist_session

                await persist_session(session_data)

            logger.debug(
                "Cevap kaydedildi",
                extra_data={
                    "session_id": session_id,
                    "question_id": question_id,
                    "answer": selected_answer,
                    "response_time": response_time,
                },
            )

            return True

        except Exception as e:
            logger.error(
                f"Cevap kaydetme hatası: {e}",
                extra_data={"session_id": session_id, "question_id": question_id},
            )
            return False

    async def navigate_to_question(
        self, session_id: str, question_index: int
    ) -> Question | None:
        """
        Belirli bir soruya git

        Args:
            session_id: Sınav oturum ID'si
            question_index: Soru indeksi (0-based)

        Returns:
            Optional[Question]: Hedef soru veya None
        """
        try:
            if session_id not in self.active_sessions:
                return None

            session_data = self.active_sessions[session_id]

            if session_data.status != ExamStatus.IN_PROGRESS:
                return None

            if 0 <= question_index < len(session_data.questions):
                session_data.current_question_index = question_index
                return await self.get_current_question(session_id)

            return None

        except Exception as e:
            logger.error(
                f"Soru navigasyon hatası: {e}",
                extra_data={"session_id": session_id, "question_index": question_index},
            )
            return None

    async def flag_question(
        self, session_id: str, question_id: str, flagged: bool
    ) -> bool:
        """
        Soruyu işaretle veya işareti kaldır

        Args:
            session_id: Sınav oturum ID'si
            question_id: Soru ID'si
            flagged: İşaretli durumu

        Returns:
            bool: İşlem başarı durumu
        """
        try:
            if session_id not in self.active_sessions:
                return False

            session_data = self.active_sessions[session_id]

            if flagged:
                if question_id not in session_data.flagged_questions:
                    session_data.flagged_questions.append(question_id)
            elif question_id in session_data.flagged_questions:
                session_data.flagged_questions.remove(question_id)

            logger.debug(
                "Soru işaretleme güncellendi",
                extra_data={
                    "session_id": session_id,
                    "question_id": question_id,
                    "flagged": flagged,
                },
            )

            return True

        except Exception as e:
            logger.error(
                f"Soru işaretleme hatası: {e}",
                extra_data={"session_id": session_id, "question_id": question_id},
            )
            return False

    async def get_remaining_time(self, session_id: str) -> int | None:
        """
        Kalan süreyi getir (saniye)

        Args:
            session_id: Sınav oturum ID'si

        Returns:
            Optional[int]: Kalan süre (saniye) veya None
        """
        try:
            if session_id not in self.active_sessions:
                return None

            session_data = self.active_sessions[session_id]

            if (
                session_data.status != ExamStatus.IN_PROGRESS
                or not session_data.started_at
            ):
                return None

            elapsed_time = datetime.now() - session_data.started_at
            total_duration = timedelta(
                minutes=session_data.exam_config.duration_minutes
            )
            remaining = total_duration - elapsed_time

            return max(0, int(remaining.total_seconds()))

        except Exception as e:
            logger.error(
                f"Kalan süre hesaplama hatası: {e}",
                extra_data={"session_id": session_id},
            )
            return None

    async def complete_exam(
        self, session_id: str, manual_completion: bool = True
    ) -> ExamPerformanceMetrics:
        """
        Sınavı tamamla ve performans analizi yap

        Args:
            session_id: Sınav oturum ID'si
            manual_completion: Manuel tamamlama mı?

        Returns:
            ExamPerformanceMetrics: Performans metrikleri
        """
        try:
            if session_id not in self.active_sessions:
                raise ValueError("Sınav oturumu bulunamadı")

            session_data = self.active_sessions[session_id]

            if session_data.status == ExamStatus.COMPLETED:
                # Zaten tamamlanmış
                return session_data.performance_metrics

            # Sınavı tamamla
            session_data.status = ExamStatus.COMPLETED
            session_data.completed_at = datetime.now()

            # Performans analizi yap
            performance_metrics = await self._analyze_performance(session_data)
            session_data.performance_metrics = performance_metrics

            # Veritabanını güncelle
            async with get_db_session_context() as db_session:
                await db_session.execute(
                    update(ExamSession)
                    .where(ExamSession.id == session_id)
                    .values(
                        status=ExamStatus.COMPLETED.value,
                        completed_at=session_data.completed_at,
                        total_correct=performance_metrics.correct_answers,
                        total_wrong=performance_metrics.wrong_answers,
                        total_empty=performance_metrics.empty_answers,
                        raw_score=performance_metrics.raw_score,
                        scaled_score=performance_metrics.raw_score,
                        estimated_ability=performance_metrics.estimated_ability,
                    )
                )
                await db_session.commit()

            # Otomatik kaydetme task'ını durdur
            if session_id in self.auto_save_tasks:
                self.auto_save_tasks[session_id].cancel()
                del self.auto_save_tasks[session_id]

            # Redis L2 cleanup — completed exams no longer need session state
            from core.exam_session_store import delete_session

            await delete_session(session_id)

            logger.info(
                "Sınav tamamlandı",
                extra_data={
                    "session_id": session_id,
                    "student_id": session_data.student_id,
                    "completed_at": session_data.completed_at.isoformat(),
                    "net_score": performance_metrics.net_score,
                    "raw_score": performance_metrics.raw_score,
                },
            )

            return performance_metrics

        except Exception as e:
            logger.error(
                f"Sınav tamamlama hatası: {e}", extra_data={"session_id": session_id}
            )
            raise

    async def get_session_data(self, session_id: str) -> ExamSessionData | None:
        """
        Sınav oturum verilerini getir

        Args:
            session_id: Sınav oturum ID'si

        Returns:
            Optional[ExamSessionData]: Sınav oturum verisi veya None
        """
        # L1: in-memory dict
        session = self.active_sessions.get(session_id)
        if session:
            return session

        # L2: Redis fallback (restart recovery)
        from core.exam_session_store import load_session

        session = await load_session(session_id)
        if session:
            # Populate L1 cache
            self.active_sessions[session_id] = session
        return session

    async def get_unanswered_questions(self, session_id: str) -> list[str]:
        """
        Cevaplanmamış soruların ID listesini getir - REQ-1.6

        Args:
            session_id: Sınav oturum ID'si

        Returns:
            List[str]: Cevaplanmamış soru ID'leri
        """
        try:
            if session_id not in self.active_sessions:
                return []

            session_data = self.active_sessions[session_id]

            # Tüm sorulardan cevaplananları çıkar
            unanswered = [
                q_id
                for q_id in session_data.questions
                if q_id not in session_data.answers
            ]

            return unanswered

        except Exception as e:
            logger.error(
                f"Cevaplanmamış sorular getirme hatası: {e}",
                extra_data={"session_id": session_id},
            )
            return []

    async def get_completion_percentage(self, session_id: str) -> float:
        """
        Sınav tamamlanma yüzdesini hesapla - REQ-1.6

        Args:
            session_id: Sınav oturum ID'si

        Returns:
            float: Tamamlanma yüzdesi (0-100 arası)
        """
        try:
            if session_id not in self.active_sessions:
                return 0.0

            session_data = self.active_sessions[session_id]

            total_questions = len(session_data.questions)
            if total_questions == 0:
                return 0.0

            answered_questions = len(session_data.answers)
            completion_percentage = (answered_questions / total_questions) * 100

            return round(completion_percentage, 2)

        except Exception as e:
            logger.error(
                f"Tamamlanma yüzdesi hesaplama hatası: {e}",
                extra_data={"session_id": session_id},
            )
            return 0.0

    async def get_answer_statistics(self, session_id: str) -> dict[str, int]:
        """
        Cevap istatistiklerini getir - REQ-1.6

        Args:
            session_id: Sınav oturum ID'si

        Returns:
            Dict[str, int]: Cevap istatistikleri
                - total_questions: Toplam soru sayısı
                - answered_questions: Cevaplanan soru sayısı
                - unanswered_questions: Cevaplanmamış soru sayısı
                - completion_percentage: Tamamlanma yüzdesi
        """
        try:
            if session_id not in self.active_sessions:
                return {
                    "total_questions": 0,
                    "answered_questions": 0,
                    "unanswered_questions": 0,
                    "completion_percentage": 0.0,
                }

            session_data = self.active_sessions[session_id]

            total_questions = len(session_data.questions)
            answered_questions = len(session_data.answers)
            unanswered_questions = total_questions - answered_questions
            completion_percentage = await self.get_completion_percentage(session_id)

            return {
                "total_questions": total_questions,
                "answered_questions": answered_questions,
                "unanswered_questions": unanswered_questions,
                "completion_percentage": completion_percentage,
            }

        except Exception as e:
            logger.error(
                f"Cevap istatistikleri getirme hatası: {e}",
                extra_data={"session_id": session_id},
            )
            return {
                "total_questions": 0,
                "answered_questions": 0,
                "unanswered_questions": 0,
                "completion_percentage": 0.0,
            }

    async def get_subject_performance(
        self, session_id: str
    ) -> list[SubjectPerformance]:
        """
        Konu bazlı performans analizi

        Args:
            session_id: Sınav oturum ID'si

        Returns:
            List[SubjectPerformance]: Konu performansları
        """
        try:
            if session_id not in self.active_sessions:
                return []

            subject_stats = {}

            async with get_db_session_context() as db_session:
                # Sınav sorularını ve cevapları getir
                result = await db_session.execute(
                    select(Question, StudentAnswer)
                    .join(ExamQuestion, Question.id == ExamQuestion.question_id)
                    .outerjoin(
                        StudentAnswer,
                        and_(
                            StudentAnswer.question_id == Question.id,
                            StudentAnswer.exam_session_id == session_id,
                        ),
                    )
                    .where(ExamQuestion.exam_session_id == session_id)
                    .order_by(ExamQuestion.question_order)
                )

                for question, answer in result:
                    # QuestionBankItem.subject_area is String, not Enum
                    subject = (
                        question.subject_area.lower()
                        if isinstance(question.subject_area, str)
                        else question.subject_area.value
                    )

                    if subject not in subject_stats:
                        subject_stats[subject] = {
                            "total": 0,
                            "correct": 0,
                            "wrong": 0,
                            "empty": 0,
                            "total_time": 0.0,
                            "total_difficulty": 0.0,
                        }

                    stats = subject_stats[subject]
                    stats["total"] += 1
                    stats["total_difficulty"] += question.irt_difficulty or 0.0

                    if answer and answer.selected_answer:
                        # Cevap verilmiş
                        if (answer.selected_answer or "").strip().upper() == (
                            question.correct_answer or ""
                        ).strip().upper():
                            stats["correct"] += 1
                        else:
                            stats["wrong"] += 1

                        stats["total_time"] += answer.response_time_seconds
                    else:
                        # Boş cevap
                        stats["empty"] += 1

            # SubjectPerformance objelerini oluştur
            subject_performances = []
            for subject, stats in subject_stats.items():
                success_rate = (
                    (stats["correct"] / stats["total"]) * 100
                    if stats["total"] > 0
                    else 0
                )
                avg_response_time = (
                    stats["total_time"] / (stats["correct"] + stats["wrong"])
                    if (stats["correct"] + stats["wrong"]) > 0
                    else 0
                )
                avg_difficulty = (
                    stats["total_difficulty"] / stats["total"]
                    if stats["total"] > 0
                    else 0
                )

                subject_performance = SubjectPerformance(
                    subject=subject,
                    total_questions=stats["total"],
                    correct_answers=stats["correct"],
                    wrong_answers=stats["wrong"],
                    empty_answers=stats["empty"],
                    success_rate=success_rate,
                    average_response_time=avg_response_time,
                    difficulty_level=avg_difficulty,
                )

                subject_performances.append(subject_performance)

            return subject_performances

        except Exception as e:
            logger.error(
                f"Konu performans analizi hatası: {e}",
                extra_data={"session_id": session_id},
            )
            return []

    # Frontend zorluk → DB difficulty_level mapping
    # Her seviye 2 DB seviyesini kapsar (yeterli soru havuzu için)
    DIFFICULTY_MAP: dict[str, list[str]] = {
        "kolay": ["VERY_EASY", "EASY"],
        "orta": ["EASY", "MEDIUM"],
        "zor": ["MEDIUM", "HARD"],
        "cok_zor": ["HARD", "VERY_HARD"],
    }

    async def _select_questions(self, exam_config: OSYMExamConfig) -> list[Question]:
        """
        Sınav için soruları seç

        Args:
            exam_config: Sınav konfigürasyonu

        Returns:
            List[Question]: Seçilen sorular
        """
        selected_questions = []
        difficulty_levels = None
        if exam_config.difficulty:
            difficulty_levels = self.DIFFICULTY_MAP.get(exam_config.difficulty)

        async with get_db_session_context() as db_session:
            for subject, count in exam_config.subject_distribution.items():
                # Base quality filters
                base_filters = [
                    Question.exam_type == exam_config.exam_type.value.upper(),
                    Question.subject_area == subject,
                    Question.is_active == True,  # noqa: E712
                    Question.question_text.isnot(None),
                    func.length(Question.question_text) >= 50,
                    Question.option_a.isnot(None),
                    func.length(Question.option_a) > 0,
                    Question.option_b.isnot(None),
                    func.length(Question.option_b) > 0,
                    Question.option_c.isnot(None),
                    func.length(Question.option_c) > 0,
                    Question.option_d.isnot(None),
                    func.length(Question.option_d) > 0,
                    Question.option_a != Question.option_b,
                    # P1-3: Seçenek minimum uzunluğu
                    func.length(Question.option_a) >= 2,
                    func.length(Question.option_b) >= 2,
                    func.length(Question.option_c) >= 2,
                    func.length(Question.option_d) >= 2,
                    # P0-2: Passage kontrolü — kısa metin + passage referansı = paragraf eksik
                    # Her iki form: diacritics'siz (OCR) ve Türkçe karakterli
                    or_(
                        and_(
                            ~func.lower(Question.question_text).contains(
                                "parcaya gore"
                            ),
                            ~func.lower(Question.question_text).contains(
                                "parçaya göre"
                            ),
                        ),
                        func.length(Question.question_text) >= 300,
                    ),
                    or_(
                        and_(
                            ~func.lower(Question.question_text).contains("metne gore"),
                            ~func.lower(Question.question_text).contains("metne göre"),
                        ),
                        func.length(Question.question_text) >= 300,
                    ),
                    or_(
                        and_(
                            ~func.lower(Question.question_text).contains("bu parcada"),
                            ~func.lower(Question.question_text).contains("bu parçada"),
                        ),
                        func.length(Question.question_text) >= 300,
                    ),
                    # P0-3: Geometri/Fizik görsel bağımlılık filtresi
                    or_(
                        ~Question.subject_area.in_(["GEOMETRI", "FIZIK"]),
                        Question.question_image_url.isnot(None),
                        func.length(Question.question_text) >= 500,
                    ),
                    # P2-3: Reddedilen sorular hariç
                    or_(
                        Question.quality_review_status.is_(None),
                        Question.quality_review_status != "rejected",
                    ),
                ]

                # Difficulty filter (if specified)
                if difficulty_levels:
                    filters = base_filters + [
                        Question.difficulty_level.in_(difficulty_levels),
                    ]
                else:
                    filters = base_filters

                # P1-1: Matematik dışı derslerde LaTeX formül içeren soruları hariç tut
                # Verified: 0 hits for x^2/2x+ in social subjects (77,336 questions checked)
                # $\frac/$\sqrt: LaTeX delimiter — safe filter
                # x^2, 2x +: No delimiter — theoretical false positive risk, 0 actual hits
                if subject in ("TURKCE", "EDEBIYAT", "TARIH", "COGRAFYA", "SOSYAL"):
                    filters.extend(
                        [
                            ~Question.question_text.contains("$\\frac"),
                            ~Question.question_text.contains("$\\sqrt"),
                            ~Question.question_text.contains("x^2"),
                            ~Question.question_text.contains("2x +"),
                        ]
                    )

                result = await db_session.execute(
                    select(Question)
                    .where(and_(*filters))
                    .order_by(func.random())
                    .limit(count)
                )

                questions = result.scalars().all()

                # Fallback: zorluk filtresiyle yetersiz soru varsa filtresiz tekrar dene
                if len(questions) < count and difficulty_levels:
                    logger.warning(
                        f"Zorluk filtresi ile yetersiz soru: {subject} "
                        f"({len(questions)}/{count}), filtre kaldırılıyor"
                    )
                    fallback_result = await db_session.execute(
                        select(Question)
                        .where(and_(*base_filters))
                        .order_by(func.random())
                        .limit(count)
                    )
                    questions = fallback_result.scalars().all()

                if len(questions) < count:
                    logger.warning(
                        f"Yetersiz soru: {subject} için {count} istendi, {len(questions)} bulundu "
                        f"(exam_type={exam_config.exam_type.value})"
                    )
                selected_questions.extend(questions)

        if len(selected_questions) < exam_config.total_questions:
            logger.warning(
                f"Toplam soru eksik: {exam_config.total_questions} istendi, "
                f"{len(selected_questions)} seçildi (exam_type={exam_config.exam_type.value})"
            )

        return selected_questions

    async def _analyze_performance(
        self, session_data: ExamSessionData
    ) -> ExamPerformanceMetrics:
        """
        Performans analizi yap

        Args:
            session_data: Sınav oturum verisi

        Returns:
            ExamPerformanceMetrics: Performans metrikleri
        """
        try:
            total_questions = len(session_data.questions)
            answered_questions = len(session_data.answers)
            correct_answers = 0
            wrong_answers = 0

            async with get_db_session_context() as db_session:
                # Doğru cevapları tek sorguda getir (N+1 yerine batch)
                question_ids = list(session_data.answers.keys())
                if question_ids:
                    result = await db_session.execute(
                        select(Question.id, Question.correct_answer).where(
                            Question.id.in_(question_ids)
                        )
                    )
                    correct_answers_map = {
                        str(row.id): row.correct_answer for row in result
                    }
                else:
                    correct_answers_map = {}

                for question_id, student_answer in session_data.answers.items():
                    correct_answer = correct_answers_map.get(question_id)

                    if (
                        correct_answer
                        and student_answer
                        and correct_answer.strip().upper()
                        == student_answer.strip().upper()
                    ):
                        correct_answers += 1
                    else:
                        wrong_answers += 1

            empty_answers = total_questions - answered_questions

            # Net hesaplama (ÖSYM sistemine göre)
            net_score = correct_answers - (wrong_answers / 4)
            raw_score = (
                (correct_answers / total_questions) * 100 if total_questions > 0 else 0
            )

            # IRT tabanlı yetenek tahmini (basit implementasyon)
            estimated_ability = self._estimate_ability(
                correct_answers, wrong_answers, total_questions
            )
            confidence_level = self._calculate_confidence(
                answered_questions, total_questions
            )

            return ExamPerformanceMetrics(
                total_questions=total_questions,
                answered_questions=answered_questions,
                correct_answers=correct_answers,
                wrong_answers=wrong_answers,
                empty_answers=empty_answers,
                net_score=net_score,
                raw_score=raw_score,
                estimated_ability=estimated_ability,
                confidence_level=confidence_level,
            )

        except Exception as e:
            logger.error(
                f"Performans analizi hatası: {e}",
                extra_data={"session_id": session_data.session_id},
            )
            # Hata durumunda varsayılan değerler döndür
            return ExamPerformanceMetrics(
                total_questions=len(session_data.questions),
                answered_questions=len(session_data.answers),
                correct_answers=0,
                wrong_answers=0,
                empty_answers=len(session_data.questions) - len(session_data.answers),
                net_score=0.0,
                raw_score=0.0,
            )

    def _estimate_ability(self, correct: int, wrong: int, total: int) -> float:
        """
        IRT tabanlı yetenek tahmini (basit implementasyon)

        Args:
            correct: Doğru cevap sayısı
            wrong: Yanlış cevap sayısı
            total: Toplam soru sayısı

        Returns:
            float: Tahmini yetenek (-3 ile +3 arası)
        """
        if total == 0:
            return 0.0

        success_rate = correct / total

        # Logit dönüşümü ile yetenek tahmini
        if success_rate >= 0.99:
            success_rate = 0.99
        elif success_rate <= 0.01:
            success_rate = 0.01

        import math

        ability = math.log(success_rate / (1 - success_rate))

        # -3 ile +3 arası normalize et
        return max(-3.0, min(3.0, ability))

    def _calculate_confidence(self, answered: int, total: int) -> float:
        """
        Güven seviyesi hesapla

        Args:
            answered: Cevaplanan soru sayısı
            total: Toplam soru sayısı

        Returns:
            float: Güven seviyesi (0-1 arası)
        """
        if total == 0:
            return 0.0

        completion_rate = answered / total

        # Basit güven hesaplama
        return min(1.0, completion_rate * 1.2)

    async def _auto_save_task(self, session_id: str):
        """
        Otomatik kaydetme task'ı

        Args:
            session_id: Sınav oturum ID'si
        """
        try:
            while session_id in self.active_sessions:
                session_data = self.active_sessions[session_id]

                if session_data.status != ExamStatus.IN_PROGRESS:
                    break

                # Otomatik kaydetme
                await self._perform_auto_save(session_id)

                # Bekleme süresi
                await asyncio.sleep(session_data.exam_config.auto_save_interval)

        except asyncio.CancelledError:
            logger.debug(f"Otomatik kaydetme task'ı iptal edildi: {session_id}")
        except Exception as e:
            logger.error(
                f"Otomatik kaydetme task hatası: {e}",
                extra_data={"session_id": session_id},
            )

    async def _perform_auto_save(self, session_id: str):
        """
        Otomatik kaydetme işlemi

        Args:
            session_id: Sınav oturum ID'si
        """
        try:
            session_data = self.active_sessions[session_id]

            # Veritabanını güncelle
            async with get_db_session_context() as db_session:
                await db_session.execute(
                    update(ExamSession)
                    .where(ExamSession.id == session_id)
                    .values(
                        current_question_index=session_data.current_question_index,
                        updated_at=datetime.now(),
                    )
                )
                await db_session.commit()

            session_data.last_auto_save = datetime.now()

            logger.debug(
                "Otomatik kaydetme tamamlandı", extra_data={"session_id": session_id}
            )

        except Exception as e:
            logger.error(
                f"Otomatik kaydetme hatası: {e}", extra_data={"session_id": session_id}
            )

    async def _auto_complete_task(self, session_id: str):
        """
        Otomatik tamamlama task'ı

        Args:
            session_id: Sınav oturum ID'si
        """
        try:
            session_data = self.active_sessions[session_id]

            if not session_data.started_at:
                return

            # Sınav süresini bekle
            duration = timedelta(minutes=session_data.exam_config.duration_minutes)
            end_time = session_data.started_at + duration

            now = datetime.now()
            if end_time > now:
                wait_time = (end_time - now).total_seconds()
                await asyncio.sleep(wait_time)

            # Sınavı otomatik tamamla
            if session_data.status == ExamStatus.IN_PROGRESS:
                await self.complete_exam(session_id, manual_completion=False)

        except asyncio.CancelledError:
            logger.debug(f"Otomatik tamamlama task'ı iptal edildi: {session_id}")
        except Exception as e:
            logger.error(
                f"Otomatik tamamlama task hatası: {e}",
                extra_data={"session_id": session_id},
            )


# Global ÖSYM sınav motoru instance
osym_exam_engine = OSYMExamEngine()
