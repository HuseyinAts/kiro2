# -*- coding: utf-8 -*-
"""
Sınav Cevap Takip Servisi
Türkiye Üniversite Sınavları Hazırlık Platformu

Bu modül sınav cevaplarının takibi için servisleri sağlar:
- Boş bırakılan soruların takibi
- Cevaplanan/cevaplanmayan soru sayısı
- Tamamlanma yüzdesi hesaplama
- Cevap durumu analizi

REQ-1.6: Sınav arayüzü gereksinimleri
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.structured_logger import get_logger
from models.database import ExamSession, StudentAnswer

logger = get_logger("exam_answer_tracking")


@dataclass
class AnswerStatus:
    """Cevap durumu bilgisi"""

    question_id: str
    question_order: int
    is_answered: bool
    selected_answer: Optional[str]
    is_empty: bool
    response_time_seconds: float
    answered_at: Optional[datetime]


@dataclass
class CompletionStats:
    """Tamamlanma istatistikleri"""

    total_questions: int
    answered_questions: int
    unanswered_questions: int
    empty_answers: int
    completion_percentage: float
    unanswered_question_ids: List[str]
    unanswered_question_orders: List[int]


class ExamAnswerTrackingService:
    """Sınav cevap takip servisi"""

    def __init__(self, db_session: AsyncSession):
        """
        Servisi başlat

        Args:
            db_session: Veritabanı oturumu
        """
        self.db_session = db_session

    async def get_answer_status(
        self, exam_session_id: str, question_id: str
    ) -> Optional[AnswerStatus]:
        """
        Belirli bir sorunun cevap durumunu getir

        Args:
            exam_session_id: Sınav oturum ID'si
            question_id: Soru ID'si

        Returns:
            Cevap durumu bilgisi veya None

        REQ-1.6: Boş bırakma takibi
        """
        try:
            # Cevabı veritabanından getir
            result = await self.db_session.execute(
                select(StudentAnswer).where(
                    and_(
                        StudentAnswer.exam_session_id == exam_session_id,
                        StudentAnswer.question_id == question_id,
                    )
                )
            )

            answer = result.scalar_one_or_none()

            if not answer:
                # Henüz cevap verilmemiş
                return AnswerStatus(
                    question_id=question_id,
                    question_order=0,  # Sıra bilgisi ayrıca alınmalı
                    is_answered=False,
                    selected_answer=None,
                    is_empty=True,
                    response_time_seconds=0.0,
                    answered_at=None,
                )

            # Cevap durumunu oluştur
            is_empty = answer.selected_answer is None
            is_answered = not is_empty

            return AnswerStatus(
                question_id=question_id,
                question_order=0,  # Sıra bilgisi ayrıca alınmalı
                is_answered=is_answered,
                selected_answer=answer.selected_answer,
                is_empty=is_empty,
                response_time_seconds=answer.response_time_seconds,
                answered_at=answer.answered_at,
            )

        except Exception as e:
            logger.error(
                f"Cevap durumu getirme hatası: {e}",
                extra_data={
                    "exam_session_id": exam_session_id,
                    "question_id": question_id,
                },
            )
            return None

    async def get_completion_stats(self, exam_session_id: str) -> CompletionStats:
        """
        Sınav tamamlanma istatistiklerini hesapla

        Args:
            exam_session_id: Sınav oturum ID'si

        Returns:
            Tamamlanma istatistikleri

        REQ-1.6: Tamamlanma yüzdesi hesaplama
        """
        try:
            # Sınav oturumunu getir
            exam_result = await self.db_session.execute(
                select(ExamSession).where(ExamSession.id == exam_session_id)
            )

            exam_session = exam_result.scalar_one_or_none()

            if not exam_session:
                logger.error(f"Sınav oturumu bulunamadı: {exam_session_id}")
                return CompletionStats(
                    total_questions=0,
                    answered_questions=0,
                    unanswered_questions=0,
                    empty_answers=0,
                    completion_percentage=0.0,
                    unanswered_question_ids=[],
                    unanswered_question_orders=[],
                )

            total_questions = exam_session.total_questions

            # Tüm cevapları getir
            answers_result = await self.db_session.execute(
                select(StudentAnswer).where(
                    StudentAnswer.exam_session_id == exam_session_id
                )
            )

            answers = answers_result.scalars().all()

            # Cevaplanan ve boş soruları say
            answered_count = 0
            empty_count = 0
            answered_question_ids: Set[str] = set()

            for answer in answers:
                answered_question_ids.add(answer.question_id)

                if answer.selected_answer is None:
                    empty_count += 1
                else:
                    answered_count += 1

            # Cevaplanmayan soruları bul
            # Sınavdaki tüm soruları getir
            from models.database import ExamQuestion

            exam_questions_result = await self.db_session.execute(
                select(ExamQuestion)
                .where(ExamQuestion.exam_session_id == exam_session_id)
                .order_by(ExamQuestion.question_order)
            )

            exam_questions = exam_questions_result.scalars().all()

            unanswered_question_ids = []
            unanswered_question_orders = []

            for exam_question in exam_questions:
                if exam_question.question_id not in answered_question_ids:
                    unanswered_question_ids.append(exam_question.question_id)
                    unanswered_question_orders.append(exam_question.question_order)

            # Toplam cevaplanan soru sayısı (boş dahil)
            total_answered = len(answered_question_ids)
            unanswered_count = total_questions - total_answered

            # Tamamlanma yüzdesi
            completion_percentage = (
                (total_answered / total_questions * 100) if total_questions > 0 else 0.0
            )

            stats = CompletionStats(
                total_questions=total_questions,
                answered_questions=answered_count,  # Sadece dolu cevaplar
                unanswered_questions=unanswered_count,
                empty_answers=empty_count,
                completion_percentage=completion_percentage,
                unanswered_question_ids=unanswered_question_ids,
                unanswered_question_orders=unanswered_question_orders,
            )

            logger.info(
                "Tamamlanma istatistikleri hesaplandı",
                extra_data={
                    "exam_session_id": exam_session_id,
                    "completion_percentage": completion_percentage,
                    "answered": answered_count,
                    "empty": empty_count,
                    "unanswered": unanswered_count,
                },
            )

            return stats

        except Exception as e:
            logger.error(
                f"Tamamlanma istatistikleri hesaplama hatası: {e}",
                extra_data={"exam_session_id": exam_session_id},
            )
            return CompletionStats(
                total_questions=0,
                answered_questions=0,
                unanswered_questions=0,
                empty_answers=0,
                completion_percentage=0.0,
                unanswered_question_ids=[],
                unanswered_question_orders=[],
            )

    async def get_all_answer_statuses(self, exam_session_id: str) -> List[AnswerStatus]:
        """
        Sınavdaki tüm soruların cevap durumlarını getir

        Args:
            exam_session_id: Sınav oturum ID'si

        Returns:
            Tüm soruların cevap durumları listesi

        REQ-1.6: Cevap durumu takibi
        """
        try:
            # Sınavdaki tüm soruları getir
            from models.database import ExamQuestion

            exam_questions_result = await self.db_session.execute(
                select(ExamQuestion)
                .where(ExamQuestion.exam_session_id == exam_session_id)
                .order_by(ExamQuestion.question_order)
            )

            exam_questions = exam_questions_result.scalars().all()

            # Tüm cevapları getir
            answers_result = await self.db_session.execute(
                select(StudentAnswer).where(
                    StudentAnswer.exam_session_id == exam_session_id
                )
            )

            answers = answers_result.scalars().all()

            # Cevapları soru ID'sine göre eşle
            answer_map: Dict[str, StudentAnswer] = {
                answer.question_id: answer for answer in answers
            }

            # Her soru için cevap durumu oluştur
            statuses = []

            for exam_question in exam_questions:
                question_id = exam_question.question_id
                answer = answer_map.get(question_id)

                if answer:
                    is_empty = answer.selected_answer is None
                    is_answered = not is_empty

                    status = AnswerStatus(
                        question_id=question_id,
                        question_order=exam_question.question_order,
                        is_answered=is_answered,
                        selected_answer=answer.selected_answer,
                        is_empty=is_empty,
                        response_time_seconds=answer.response_time_seconds,
                        answered_at=answer.answered_at,
                    )
                else:
                    # Henüz cevap verilmemiş
                    status = AnswerStatus(
                        question_id=question_id,
                        question_order=exam_question.question_order,
                        is_answered=False,
                        selected_answer=None,
                        is_empty=True,
                        response_time_seconds=0.0,
                        answered_at=None,
                    )

                statuses.append(status)

            logger.info(
                "Tüm cevap durumları getirildi",
                extra_data={
                    "exam_session_id": exam_session_id,
                    "total_questions": len(statuses),
                },
            )

            return statuses

        except Exception as e:
            logger.error(
                f"Cevap durumları getirme hatası: {e}",
                extra_data={"exam_session_id": exam_session_id},
            )
            return []

    async def update_exam_session_stats(self, exam_session_id: str) -> bool:
        """
        Sınav oturumu istatistiklerini güncelle

        Args:
            exam_session_id: Sınav oturum ID'si

        Returns:
            Başarılı ise True

        REQ-1.6: Otomatik istatistik güncelleme
        """
        try:
            # Tamamlanma istatistiklerini hesapla
            stats = await self.get_completion_stats(exam_session_id)

            # Sınav oturumunu güncelle
            exam_result = await self.db_session.execute(
                select(ExamSession).where(ExamSession.id == exam_session_id)
            )

            exam_session = exam_result.scalar_one_or_none()

            if not exam_session:
                logger.error(f"Sınav oturumu bulunamadı: {exam_session_id}")
                return False

            # İstatistikleri güncelle
            exam_session.total_empty = stats.empty_answers

            await self.db_session.commit()

            logger.info(
                "Sınav oturumu istatistikleri güncellendi",
                extra_data={
                    "exam_session_id": exam_session_id,
                    "total_empty": stats.empty_answers,
                },
            )

            return True

        except Exception as e:
            logger.error(
                f"Sınav oturumu istatistikleri güncelleme hatası: {e}",
                extra_data={"exam_session_id": exam_session_id},
            )
            await self.db_session.rollback()
            return False

    async def mark_answer_as_empty(
        self, exam_session_id: str, question_id: str
    ) -> bool:
        """
        Bir cevabı boş olarak işaretle

        Args:
            exam_session_id: Sınav oturum ID'si
            question_id: Soru ID'si

        Returns:
            Başarılı ise True

        REQ-1.6: Boş cevap işaretleme
        """
        try:
            # Mevcut cevabı kontrol et
            result = await self.db_session.execute(
                select(StudentAnswer).where(
                    and_(
                        StudentAnswer.exam_session_id == exam_session_id,
                        StudentAnswer.question_id == question_id,
                    )
                )
            )

            answer = result.scalar_one_or_none()

            if answer:
                # Mevcut cevabı boş olarak güncelle
                answer.selected_answer = None
                answer.is_correct = None
            else:
                # Yeni boş cevap oluştur
                answer = StudentAnswer(
                    exam_session_id=exam_session_id,
                    question_id=question_id,
                    selected_answer=None,
                    is_correct=None,
                    response_time_seconds=0.0,
                    answer_changes=0,
                    time_to_first_answer=0.0,
                )
                self.db_session.add(answer)

            await self.db_session.commit()

            # Sınav oturumu istatistiklerini güncelle
            await self.update_exam_session_stats(exam_session_id)

            logger.info(
                "Cevap boş olarak işaretlendi",
                extra_data={
                    "exam_session_id": exam_session_id,
                    "question_id": question_id,
                },
            )

            return True

        except Exception as e:
            logger.error(
                f"Boş cevap işaretleme hatası: {e}",
                extra_data={
                    "exam_session_id": exam_session_id,
                    "question_id": question_id,
                },
            )
            await self.db_session.rollback()
            return False


    async def update_error_type(
        self,
        exam_session_id: str,
        question_id: str,
        error_type: str,
        student_id: str,
    ) -> bool:
        """
        Öğrencinin yanlış cevabına hata tipi ata (F8 Error Taxonomy)

        Args:
            exam_session_id: Sınav oturum ID'si
            question_id: Soru ID'si
            error_type: Hata tipi (concept, procedural, careless, knowledge_gap)
            student_id: Kimlik doğrulama için öğrenci ID'si

        Returns:
            Başarılı ise True

        Hata tipleri:
        - concept: Kavram hatası — konuyu yanlış anladım
        - procedural: İşlem hatası — doğru düşündüm ama uygulama yanlış
        - careless: Dikkatsizlik — biliyordum ama dikkat etmedim
        - knowledge_gap: Bilgi eksikliği — bu konuyu hiç bilmiyordum
        """
        valid_types = {"concept", "procedural", "careless", "knowledge_gap"}
        if error_type not in valid_types:
            logger.warning(
                f"Geçersiz hata tipi: {error_type}",
                extra_data={"valid_types": list(valid_types)},
            )
            return False

        try:
            # Ownership check: verify student owns this exam session
            exam_result = await self.db_session.execute(
                select(ExamSession).where(
                    and_(
                        ExamSession.id == exam_session_id,
                        ExamSession.student_id == student_id,
                    )
                )
            )
            exam_session = exam_result.scalar_one_or_none()
            if not exam_session:
                logger.warning(
                    "Sınav oturumu bulunamadı veya erişim reddedildi",
                    extra_data={
                        "exam_session_id": exam_session_id,
                        "student_id": student_id,
                    },
                )
                return False

            # Find the student answer
            result = await self.db_session.execute(
                select(StudentAnswer).where(
                    and_(
                        StudentAnswer.exam_session_id == exam_session_id,
                        StudentAnswer.question_id == question_id,
                    )
                )
            )
            answer = result.scalar_one_or_none()

            if not answer:
                logger.warning(
                    "Cevap bulunamadı",
                    extra_data={
                        "exam_session_id": exam_session_id,
                        "question_id": question_id,
                    },
                )
                return False

            # Only allow error_type on wrong answers (is_correct == False)
            if answer.is_correct is True:
                logger.warning(
                    "Doğru cevaba hata tipi atanamaz",
                    extra_data={"question_id": question_id},
                )
                return False

            answer.error_type = error_type
            await self.db_session.commit()

            logger.info(
                "Hata tipi atandı",
                extra_data={
                    "exam_session_id": exam_session_id,
                    "question_id": question_id,
                    "error_type": error_type,
                },
            )
            return True

        except Exception as e:
            logger.error(
                f"Hata tipi atama hatası: {e}",
                extra_data={
                    "exam_session_id": exam_session_id,
                    "question_id": question_id,
                },
            )
            await self.db_session.rollback()
            return False


async def create_answer_tracking_service(
    db_session: AsyncSession,
) -> ExamAnswerTrackingService:
    """
    Cevap takip servisi oluştur

    Args:
        db_session: Veritabanı oturumu

    Returns:
        ExamAnswerTrackingService instance
    """
    return ExamAnswerTrackingService(db_session)
