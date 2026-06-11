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
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from cachetools import TTLCache
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
    # Beta pratik: kör-çözüm doğrulamasından geçmiş (verified_provisional) havuzdan
    # karışık soru seç; standart base_filters/subject_distribution UYGULANMAZ.
    beta_practice: bool = False


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
        # P2: Question ID pool cache — avoids ORDER BY RANDOM() (TTL 1 hour, max 200 keys)
        self._question_pool_cache: TTLCache = TTLCache(maxsize=200, ttl=3600)
        # P2: Performance analysis cache — idempotent re-call protection (TTL 1 hour, max 500 sessions)
        self._performance_cache: TTLCache = TTLCache(maxsize=500, ttl=3600)

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
                duration_minutes=135,  # ÖSYM TYT: 135 dakika (2 saat 15 dk)
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
                duration_minutes=180,  # ÖSYM AYT: 180 dakika (3 saat)
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
                    new_dist = self.ayt_field_configs[field_type].copy()
                    exam_config.subject_distribution = new_dist
                    exam_config.total_questions = sum(new_dist.values())

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
                    new_dist = self.ydt_language_configs[language].copy()
                    exam_config.subject_distribution = new_dist
                    exam_config.total_questions = sum(new_dist.values())

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
                if custom_config.get("beta_practice"):
                    # Beta pratik: subject_distribution/base_filters yok say,
                    # verified_provisional havuzundan karışık seç (bkz. _select_beta_questions)
                    exam_config.beta_practice = True
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
            # L1 + L2 fallback: restart sonrası session L1'de olmayabilir
            session_data = await self.get_session_data(session_id)
            if not session_data:
                raise ValueError("Sınav oturumu bulunamadı")

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

            # Otomatik tamamlama task'ını başlat ve takip et
            self.auto_save_tasks[f"autoclose:{session_id}"] = asyncio.create_task(
                self._auto_complete_task(session_id)
            )

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
            session_data = await self.get_session_data(session_id)
            if not session_data:
                return None

            if session_data.status != ExamStatus.IN_PROGRESS:
                return None

            if session_data.current_question_index >= len(session_data.questions):
                return None

            question_id = session_data.questions[session_data.current_question_index]

            async with get_db_session_context() as db_session:
                result = await db_session.execute(
                    select(Question).where(
                        Question.id == question_id, Question.is_active.is_(True)
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
            if not question_id or not str(question_id).strip():
                logger.warning(
                    "save_answer: bos question_id reddedildi",
                    extra_data={"session_id": session_id},
                )
                return False

            session_data = await self.get_session_data(session_id)
            if not session_data:
                return False

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

            # Veritabanına kaydet — UPSERT işlemini arka plana al (DB pool starvation'u engellemek için)
            import asyncio
            from core.database import get_db_session_context
            from models.exam_db import StudentAnswer
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            import uuid

            if not hasattr(self, "_db_queue"):
                self._db_queue = asyncio.Queue()
                self._db_worker_task = None

            if self._db_worker_task is None or self._db_worker_task.done():
                async def _db_worker():
                    while True:
                        batch = []
                        try:
                            # Wait for at least 1 item
                            item = await self._db_queue.get()
                            batch.append(item)
                            
                            # Drain the queue up to 1000 items
                            while len(batch) < 1000:
                                try:
                                    batch.append(self._db_queue.get_nowait())
                                except asyncio.QueueEmpty:
                                    break
                            
                            # Bulk UPSERT
                            if batch:
                                async with get_db_session_context() as db_session:
                                    stmt = pg_insert(StudentAnswer)
                                    stmt = stmt.on_conflict_do_update(
                                        constraint="uq_student_answer",
                                        set_={
                                            "selected_answer": stmt.excluded.selected_answer,
                                            "response_time_seconds": stmt.excluded.response_time_seconds,
                                            "answered_at": datetime.now(),
                                            "answer_changes": StudentAnswer.answer_changes + 1,
                                        },
                                    )
                                    await db_session.execute(stmt, batch)
                                    await db_session.commit()
                        except Exception as e:
                            logger.error(f"Bulk DB worker error: {e}")
                        finally:
                            for _ in batch:
                                self._db_queue.task_done()
                
                self._db_worker_task = asyncio.create_task(_db_worker())

            normalized_answer = (
                selected_answer.strip().upper()
                if selected_answer
                else selected_answer
            )
            
            import os
            if os.environ.get("TESTING") == "true":
                # Testlerde senkron çalıştır
                async def _sync_save():
                    async with get_db_session_context() as db_session:
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
                                "selected_answer": stmt.excluded.selected_answer,
                                "response_time_seconds": stmt.excluded.response_time_seconds,
                                "answered_at": datetime.now(),
                                "answer_changes": StudentAnswer.answer_changes + 1,
                            },
                        )
                        await db_session.execute(stmt)
                        await db_session.commit()
                await _sync_save()
            else:
                import uuid
                # Gerçek yük altında global batch queue'ya at
                self._db_queue.put_nowait(
                    {
                        "id": str(uuid.uuid4()),
                        "exam_session_id": session_id,
                        "question_id": question_id,
                        "selected_answer": normalized_answer,
                        "response_time_seconds": response_time or 0.0,
                        "answer_changes": 0,
                        "time_to_first_answer": 0.0,
                    }
                )

            # Redis L2 persist - Debounced to prevent massive concurrent updates for same session
            from core.exam_session_store import persist_session

            if os.environ.get("TESTING") == "true":
                await persist_session(session_data)
            else:
                if not hasattr(self, "_persist_tasks"):
                    self._persist_tasks = {}
                    
                if session_id not in self._persist_tasks:
                    async def _debounced_persist():
                        try:
                            await asyncio.sleep(0.2)  # Wait for burst to finish
                            await persist_session(session_data)
                        finally:
                            self._persist_tasks.pop(session_id, None)
                            
                    self._persist_tasks[session_id] = asyncio.create_task(_debounced_persist())

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
            session_data = await self.get_session_data(session_id)
            if not session_data:
                return None

            if session_data.status != ExamStatus.IN_PROGRESS:
                return None

            if 0 <= question_index < len(session_data.questions):
                session_data.current_question_index = question_index
                from core.exam_session_store import persist_session

                await persist_session(session_data)
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
            session_data = await self.get_session_data(session_id)
            if not session_data:
                return False

            if flagged:
                if question_id not in session_data.flagged_questions:
                    session_data.flagged_questions.append(question_id)
            elif question_id in session_data.flagged_questions:
                session_data.flagged_questions.remove(question_id)

            from core.exam_session_store import persist_session

            await persist_session(session_data)

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
            session_data = await self.get_session_data(session_id)
            if not session_data:
                return None

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
            session_data = await self.get_session_data(session_id)
            if not session_data:
                raise ValueError("Sınav oturumu bulunamadı")

            if session_data.status == ExamStatus.COMPLETED:
                # Zaten tamamlanmış
                return session_data.performance_metrics

            # Sınavı tamamla
            session_data.status = ExamStatus.COMPLETED
            session_data.completed_at = datetime.now()

            # Performans analizi yap
            performance_metrics = await self._analyze_performance(session_data)
            session_data.performance_metrics = performance_metrics

            # Çalışma süresi hesapla
            time_spent: int | None = None
            if session_data.started_at and session_data.completed_at:
                time_spent = int(
                    (
                        session_data.completed_at - session_data.started_at
                    ).total_seconds()
                )

            # Veritabanını güncelle
            async with get_db_session_context() as db_session:
                update_values: dict = {
                    "status": ExamStatus.COMPLETED.value,
                    "completed_at": session_data.completed_at,
                    "total_correct": performance_metrics.correct_answers,
                    "total_wrong": performance_metrics.wrong_answers,
                    "total_empty": performance_metrics.empty_answers,
                    "raw_score": performance_metrics.raw_score,
                    # K-B6: Basit ölçekleme — 100 + 15*θ (YKS benzeri, gerçek ÖSYM kamuya açık değil)
                    "scaled_score": round(
                        100 + 15 * performance_metrics.estimated_ability, 2
                    ),
                    "estimated_ability": performance_metrics.estimated_ability,
                }
                if time_spent is not None:
                    update_values["time_spent_seconds"] = time_spent
                await db_session.execute(
                    update(ExamSession)
                    .where(ExamSession.id == session_id)
                    .values(**update_values)
                )
                await db_session.commit()

            # Otomatik kaydetme task'ını durdur
            if session_id in self.auto_save_tasks:
                self.auto_save_tasks[session_id].cancel()
                del self.auto_save_tasks[session_id]

            # Otomatik tamamlama task'ını durdur
            autoclose_key = f"autoclose:{session_id}"
            if autoclose_key in self.auto_save_tasks:
                self.auto_save_tasks[autoclose_key].cancel()
                del self.auto_save_tasks[autoclose_key]

            # L1 eviction first — prevent concurrent persist_session() after Redis delete
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]

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
        # L1 cache stampede protection
        if not hasattr(self, "_session_locks"):
            self._session_locks = {}
            
        if session_id not in self._session_locks:
            import asyncio
            self._session_locks[session_id] = asyncio.Lock()
            
        # L1 cache stampede protection WITHOUT asyncio.Lock convoys
        if not hasattr(self, "_session_loading"):
            self._session_loading = {}
            
        session = self.active_sessions.get(session_id)
        if session:
            return session
            
        if session_id in self._session_loading:
            # Wait for the first request to finish loading
            return await self._session_loading[session_id]
            
        # We are the first request, let's load it
        import asyncio
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._session_loading[session_id] = future
        
        try:
            # L2: Redis fallback (restart recovery)
            from core.exam_session_store import load_session
            session = await load_session(session_id)
            
            # L3: DB fallback
            if not session:
                session = await self._reconstruct_session_from_db(session_id)
                if session and session.status != ExamStatus.COMPLETED:
                    from core.exam_session_store import persist_session
                    await persist_session(session)
                    
            if session:
                self.active_sessions[session_id] = session
                
            # Resolve future so all waiters wake up
            future.set_result(session)
        except Exception as e:
            future.set_exception(e)
            raise
        finally:
            # Cleanup
            self._session_loading.pop(session_id, None)

            # Restore auto_complete timer for IN_PROGRESS sessions (EX-12)
            autoclose_key = f"autoclose:{session_id}"
            if (
                session.status == ExamStatus.IN_PROGRESS
                and autoclose_key not in self.auto_save_tasks
            ):
                self.auto_save_tasks[autoclose_key] = asyncio.create_task(
                    self._auto_complete_task(session_id)
                )
        return session

    async def _reconstruct_session_from_db(
        self, session_id: str
    ) -> "ExamSessionData | None":
        """Redis L2 miss → exam_sessions tablosundan oturumu yeniden kur.

        Multi-worker (in-memory L1 paylaşılmaz) + Redis anahtar kaybı
        senaryolarında sınav devam ettirme (resume) için DB source-of-truth.
        """
        try:
            from models.exam_db import ExamQuestion, ExamSession, StudentAnswer

            async with get_db_session_context() as db:
                row = (
                    await db.execute(
                        select(ExamSession).where(ExamSession.id == session_id)
                    )
                ).scalar_one_or_none()
                if not row:
                    return None

                q_ids = (
                    (
                        await db.execute(
                            select(ExamQuestion.question_id)
                            .where(ExamQuestion.exam_session_id == session_id)
                            .order_by(ExamQuestion.question_order)
                        )
                    )
                    .scalars()
                    .all()
                )

                ans_rows = (
                    await db.execute(
                        select(
                            StudentAnswer.question_id,
                            StudentAnswer.selected_answer,
                        ).where(StudentAnswer.exam_session_id == session_id)
                    )
                ).all()
                answers = {str(qid): sel for qid, sel in ans_rows if sel}

            config = OSYMExamConfig(
                exam_type=row.exam_type,
                total_questions=row.total_questions,
                duration_minutes=row.duration_minutes,
                subject_distribution={},
            )
            # Tamamlanmış sınav için performans metriklerini de DB'den kur —
            # aksi halde get_performance_analysis live-branch'i (perf None) 400 atar.
            perf = None
            if str(row.status) == "completed":
                _c = row.total_correct or 0
                _w = row.total_wrong or 0
                _e = row.total_empty or 0
                perf = ExamPerformanceMetrics(
                    total_questions=row.total_questions,
                    answered_questions=_c + _w,
                    correct_answers=_c,
                    wrong_answers=_w,
                    empty_answers=_e,
                    net_score=float(_c),  # ÖSYM 2023+ ceza yok → net = doğru
                    raw_score=float(row.raw_score or 0.0),
                    percentile=row.percentile,
                    estimated_ability=float(row.estimated_ability or 0.0),
                    confidence_level=float(row.ability_confidence or 0.0),
                )
            return ExamSessionData(
                session_id=str(row.id),
                student_id=str(row.student_id),
                exam_config=config,
                status=ExamStatus(row.status),
                started_at=row.started_at,
                completed_at=row.completed_at,
                current_question_index=row.current_question_index or 0,
                questions=[str(q) for q in q_ids],
                answers=answers,
                performance_metrics=perf,
            )
        except Exception as e:
            logger.error(
                f"DB session reconstruct hatası: {e}",
                extra_data={"session_id": session_id},
            )
            return None

    async def get_unanswered_questions(self, session_id: str) -> list[str]:
        """
        Cevaplanmamış soruların ID listesini getir - REQ-1.6

        Args:
            session_id: Sınav oturum ID'si

        Returns:
            List[str]: Cevaplanmamış soru ID'leri
        """
        try:
            session_data = await self.get_session_data(session_id)
            if not session_data:
                return []

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
            session_data = await self.get_session_data(session_id)
            if not session_data:
                return 0.0

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
            session_data = await self.get_session_data(session_id)
            if not session_data:
                return {
                    "total_questions": 0,
                    "answered_questions": 0,
                    "unanswered_questions": 0,
                    "completion_percentage": 0.0,
                }

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
            # NOT: session_data guard'ı kaldırıldı — konu kırılımı tamamen
            # DB join'den (ExamQuestion+StudentAnswer+Question, session_id ile)
            # hesaplanır. complete_exam session'ı Redis'ten siler ama
            # ExamQuestion/StudentAnswer satırları DB'de kalır, bu yüzden
            # tamamlanmış sınavlarda da çalışır. Bilinmeyen session_id → [].
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

                        stats["total_time"] += answer.response_time_seconds or 0
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

    async def _select_beta_questions(self, count: int) -> list[Question]:
        """Beta pratik için soru seç.

        Kör-çözüm doğrulamasından geçmiş (pipeline_metadata.verified_provisional
        == 'true') havuzdan rastgele ``count`` soru döndürür: kör solver DB cevabını
        GÖRMEDEN aynı cevabı bulmuş + okunabilir + çözülebilir + figürsüz
        (verified core build, 31 May 2026, ~2,734 soru). Standart ``base_filters``
        UYGULANMAZ — bu gate proxy'lerden daha güçlüdür ve cevap-doğruluğunu da
        dairesel olmadan teyit eder.

        ``provisional`` (gold değil): tek kör-solver run'ı kalıcı ground-truth
        SAYILMAZ (K1b dairesellik tekrarı riski). İkinci bağımsız sinyal (farklı
        model re-solve veya insan-GT) ile teyit edilince ``verified_gold``'a terfi.

        Cache anahtarı ``BETA:*`` ile standart subject havuzundan ayrıdır;
        beta-dışı sorunun beta moduna sızması mümkün değildir.
        """
        cache_key = "BETA:verified_provisional:all"
        pool = self._question_pool_cache.get(cache_key)
        if pool is None:
            async with get_db_session_context() as db_session:
                id_result = await db_session.execute(
                    select(Question.id).where(
                        Question.is_active.is_(True),
                        Question.pipeline_metadata.op("->>")("verified_provisional")
                        == "true",
                    )
                )
                pool = [row[0] for row in id_result.all()]
                if pool:
                    self._question_pool_cache[cache_key] = pool

        if not pool:
            logger.warning("Beta clean havuzu boş — beta pratik soru seçilemedi")
            return []

        sampled_ids = random.sample(pool, min(count, len(pool)))
        async with get_db_session_context() as db_session:
            result = await db_session.execute(
                select(Question).where(
                    Question.id.in_(sampled_ids),
                    Question.is_active.is_(True),
                )
            )
            return list(result.scalars().all())

    async def _select_questions(self, exam_config: OSYMExamConfig) -> list[Question]:
        """
        Sınav için soruları seç

        Args:
            exam_config: Sınav konfigürasyonu

        Returns:
            List[Question]: Seçilen sorular
        """
        # Beta pratik: subject_distribution ve proxy base_filters'ı atla,
        # doğrudan beta_clean havuzundan karışık seç.
        if getattr(exam_config, "beta_practice", False):
            return await self._select_beta_questions(exam_config.total_questions)

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

                # P2: Cached ID pool + random.sample (replaces ORDER BY RANDOM())
                difficulty_key = (
                    ",".join(difficulty_levels) if difficulty_levels else "all"
                )
                cache_key = f"{exam_config.exam_type.value}:{subject}:{difficulty_key}"

                pool = self._question_pool_cache.get(cache_key)
                if pool is None:
                    id_result = await db_session.execute(
                        select(Question.id).where(and_(*filters))
                    )
                    pool = [row[0] for row in id_result.all()]
                    if pool:
                        self._question_pool_cache[cache_key] = pool

                if len(pool) >= count:
                    sampled_ids = random.sample(pool, count)
                    result = await db_session.execute(
                        select(Question).where(
                            Question.id.in_(sampled_ids),
                            Question.is_active.is_(True),
                        )
                    )
                    questions = result.scalars().all()
                elif pool:
                    result = await db_session.execute(
                        select(Question).where(
                            Question.id.in_(pool),
                            Question.is_active.is_(True),
                        )
                    )
                    questions = result.scalars().all()
                else:
                    questions = []

                # Fallback: zorluk filtresiyle yetersiz soru varsa filtresiz tekrar dene
                if len(questions) < count and difficulty_levels:
                    logger.warning(
                        f"Zorluk filtresi ile yetersiz soru: {subject} "
                        f"({len(questions)}/{count}), filtre kaldırılıyor"
                    )
                    fallback_key = f"{exam_config.exam_type.value}:{subject}:all"
                    fallback_pool = self._question_pool_cache.get(fallback_key)
                    if fallback_pool is None:
                        fb_result = await db_session.execute(
                            select(Question.id).where(and_(*base_filters))
                        )
                        fallback_pool = [row[0] for row in fb_result.all()]
                        if fallback_pool:
                            self._question_pool_cache[fallback_key] = fallback_pool

                    if len(fallback_pool) >= count:
                        sampled_ids = random.sample(fallback_pool, count)
                        fb_q = await db_session.execute(
                            select(Question).where(
                                Question.id.in_(sampled_ids),
                                Question.is_active.is_(True),
                            )
                        )
                        questions = fb_q.scalars().all()
                    elif fallback_pool:
                        fb_q = await db_session.execute(
                            select(Question).where(
                                Question.id.in_(fallback_pool),
                                Question.is_active.is_(True),
                            )
                        )
                        questions = fb_q.scalars().all()

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
        cached: ExamPerformanceMetrics | None = self._performance_cache.get(
            session_data.session_id
        )
        if cached is not None:
            return cached

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
                            Question.id.in_(question_ids),
                            Question.is_active.is_(True),
                        )
                    )
                    correct_answers_map = {
                        str(row.id): row.correct_answer for row in result
                    }
                else:
                    correct_answers_map = {}

                # is_correct takibi: (question_id, bool) listesi
                is_correct_results: list[tuple[str, bool]] = []

                for question_id, student_answer in session_data.answers.items():
                    correct_answer = correct_answers_map.get(question_id)
                    is_corr = bool(
                        correct_answer
                        and student_answer
                        and correct_answer.strip().upper()
                        == student_answer.strip().upper()
                    )
                    if is_corr:
                        correct_answers += 1
                    else:
                        wrong_answers += 1
                    is_correct_results.append((question_id, is_corr))

                # --- is_correct bulk UPDATE (120 ayri → 2 toplu) ---
                if is_correct_results:
                    correct_ids = [q for q, ok in is_correct_results if ok]
                    wrong_ids = [q for q, ok in is_correct_results if not ok]
                    all_answered_ids = list(session_data.answers.keys())

                    if correct_ids:
                        await db_session.execute(
                            update(StudentAnswer)
                            .where(
                                and_(
                                    StudentAnswer.exam_session_id
                                    == session_data.session_id,
                                    StudentAnswer.question_id.in_(correct_ids),
                                )
                            )
                            .values(is_correct=True)
                        )
                    if wrong_ids:
                        await db_session.execute(
                            update(StudentAnswer)
                            .where(
                                and_(
                                    StudentAnswer.exam_session_id
                                    == session_data.session_id,
                                    StudentAnswer.question_id.in_(wrong_ids),
                                )
                            )
                            .values(is_correct=False)
                        )

                    # --- times_asked / times_correct batch update ---

                    if all_answered_ids:
                        await db_session.execute(
                            update(Question)
                            .where(Question.id.in_(all_answered_ids))
                            .values(times_asked=Question.times_asked + 1)
                        )
                    if correct_ids:
                        await db_session.execute(
                            update(Question)
                            .where(Question.id.in_(correct_ids))
                            .values(times_correct=Question.times_correct + 1)
                        )

                    await db_session.commit()
                    logger.info(
                        f"is_correct + times_asked guncellendi: "
                        f"{len(is_correct_results)} cevap, {len(correct_ids)} dogru",
                        extra_data={"session_id": session_data.session_id},
                    )

            empty_answers = total_questions - answered_questions

            # Net hesaplama — ÖSYM 2023'ten itibaren 1/4 ceza kaldırıldı
            net_score = float(correct_answers)
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

            result = ExamPerformanceMetrics(
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
            self._performance_cache[session_data.session_id] = result
            return result

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
            session_data = self.active_sessions.get(session_id)
            if not session_data:
                return

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

    async def get_student_exams(self, student_id: str) -> list[ExamSessionData]:
        """Get all exam sessions for a student (L1 dict + L2 Redis merged, deduped)."""
        from core.exam_session_store import get_student_sessions

        l1 = {
            s.session_id: s
            for s in self.active_sessions.values()
            if s.student_id == student_id
        }
        l2 = await get_student_sessions(student_id)
        for s in l2:
            if s.session_id not in l1:
                l1[s.session_id] = s
                self.active_sessions[s.session_id] = s
        return list(l1.values())

    async def _auto_complete_task(self, session_id: str):
        """
        Otomatik tamamlama task'ı

        Args:
            session_id: Sınav oturum ID'si
        """
        try:
            session_data = self.active_sessions.get(session_id)
            if not session_data:
                return

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
# K-B5 FIXED: 10 direct active_sessions lookups replaced with get_session_data(session_id)
# which implements L1 (in-memory) → L2 (Redis) fallback. Mutating methods now call
# persist_session() to sync state across workers. Multi-worker deployments are supported.
osym_exam_engine = OSYMExamEngine()


async def session_to_sinav_sonucu(session_id: str):
    """Convert an exam session to legacy SinavSonucu format.

    Shared adapter used by advanced_reports and ogretmen_service.
    """
    from models import KonuPerformansi, SinavSonucu, SinavTipi

    session = await osym_exam_engine.get_session_data(session_id)
    if not session or not session.performance_metrics:
        return None
    metrics = session.performance_metrics
    exam_type_map = {"tyt": SinavTipi.TYT, "ayt": SinavTipi.AYT, "ydt": SinavTipi.YDT}
    sinav_tipi = exam_type_map.get(session.exam_config.exam_type.value, SinavTipi.TYT)
    subject_perfs = await osym_exam_engine.get_subject_performance(session_id)
    konu_performanslari = [
        KonuPerformansi(
            konu=sp.subject,
            toplam_soru=sp.total_questions,
            dogru_sayisi=sp.correct_answers,
            yanlis_sayisi=sp.wrong_answers,
            bos_sayisi=sp.empty_answers,
            basari_yuzdesi=sp.success_rate,
            ortalama_sure=sp.average_response_time,
        )
        for sp in subject_perfs
    ]
    zayif = [kp.konu for kp in konu_performanslari if kp.basari_yuzdesi < 50]
    guclu = [kp.konu for kp in konu_performanslari if kp.basari_yuzdesi >= 70]
    return SinavSonucu(
        sonuc_id=session_id,
        sinav_id=session_id,
        ogrenci_id=session.student_id,
        sinav_tipi=sinav_tipi,
        toplam_soru=metrics.total_questions,
        dogru_sayisi=metrics.correct_answers,
        yanlis_sayisi=metrics.wrong_answers,
        bos_sayisi=metrics.empty_answers,
        net_sayisi=metrics.net_score,
        ham_puan=metrics.raw_score,
        konu_performanslari=konu_performanslari,
        zayif_konular=zayif,
        guclu_konular=guclu,
    )
