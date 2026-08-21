import asyncio
import logging
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from pydantic import ConfigDict

from core.cqrs.base import Command, CommandHandler
from core.osym_exam_engine import ExamStatus, osym_exam_engine
from models.database import ExamType

logger = logging.getLogger(__name__)


def _get_engine():
    import sys

    if "api.sinav" in sys.modules:
        return getattr(sys.modules["api.sinav"], "osym_exam_engine", osym_exam_engine)
    return osym_exam_engine


class CreateExamCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    student_id: str
    exam_type: Any
    custom_config: dict[str, Any] | None = None


class CreateExamCommandHandler(CommandHandler[CreateExamCommand, dict[str, Any]]):
    async def handle(self, command: CreateExamCommand) -> dict[str, Any]:
        engine = _get_engine()
        try:
            session_id = await engine.create_exam_session(
                student_id=command.student_id,
                exam_type=command.exam_type,
                custom_config=command.custom_config,
            )

            session_data = await engine.get_session_data(session_id)

            if not session_data:
                raise RuntimeError("Sınav oturumu oluşturulamadı")

            logger.info(
                "ÖSYM sınavı oluşturuldu",
                extra={
                    "session_id": session_id,
                    "student_id": command.student_id,
                    "exam_type": command.exam_type.value,
                },
            )

            return {
                "session_id": session_data.session_id,
                "student_id": session_data.student_id,
                "exam_type": session_data.exam_config.exam_type.value,
                "status": session_data.status.value,
                "total_questions": session_data.exam_config.total_questions,
                "duration_minutes": session_data.exam_config.duration_minutes,
                "current_question_index": session_data.current_question_index,
                "started_at": session_data.started_at,
                "completed_at": session_data.completed_at,
            }
        except ValueError as e:
            logger.error(
                f"Sınav oluşturma hatası: {e}",
                extra={
                    "student_id": command.student_id,
                    "exam_type": command.exam_type.value,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            logger.error(
                f"Beklenmeyen sınav oluşturma hatası: {e}",
                extra={
                    "student_id": command.student_id,
                    "exam_type": command.exam_type.value,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Sınav oluşturulurken beklenmeyen bir hata oluştu",
            )


class CreateBetaPracticeCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    student_id: str
    num_questions: int


class CreateBetaPracticeCommandHandler(
    CommandHandler[CreateBetaPracticeCommand, dict[str, Any]]
):
    async def handle(self, command: CreateBetaPracticeCommand) -> dict[str, Any]:
        num = max(1, min(int(command.num_questions), 50))
        engine = _get_engine()
        try:
            session_id = await engine.create_exam_session(
                student_id=command.student_id,
                exam_type=ExamType.TYT,
                custom_config={
                    "beta_practice": True,
                    "question_count": num,
                    "duration_minutes": 120,
                },
            )
            session_data = await engine.get_session_data(session_id)
            if not session_data:
                raise ValueError("Beta pratik oturumu oluşturulamadı")

            logger.info(
                "Beta pratik testi oluşturuldu",
                extra={
                    "session_id": session_id,
                    "student_id": command.student_id,
                    "num_questions": num,
                },
            )

            return {
                "session_id": session_data.session_id,
                "student_id": session_data.student_id,
                "exam_type": session_data.exam_config.exam_type.value,
                "status": session_data.status.value,
                "total_questions": session_data.exam_config.total_questions,
                "duration_minutes": session_data.exam_config.duration_minutes,
                "current_question_index": session_data.current_question_index,
                "started_at": session_data.started_at,
                "completed_at": session_data.completed_at,
            }
        except ValueError as e:
            logger.error(
                f"Beta pratik oluşturma hatası: {e}",
                extra={"student_id": command.student_id},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Beta pratik testi oluşturulamadı. Lütfen tekrar deneyin.",
            )
        except Exception as e:
            logger.error(
                f"Beklenmeyen beta pratik hatası: {e}",
                extra={"student_id": command.student_id},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Beta pratik testi oluşturulurken beklenmeyen bir hata oluştu",
            )


class StartExamCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    student_id: str
    session_id: str


class StartExamCommandHandler(CommandHandler[StartExamCommand, dict[str, Any]]):
    async def handle(self, command: StartExamCommand) -> dict[str, Any]:
        engine = _get_engine()
        try:
            session_data = await engine.get_session_data(command.session_id)
            if not session_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Sınav oturumu bulunamadı",
                )

            if str(session_data.student_id) != str(command.student_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu sınava erişim yetkiniz yok",
                )

            updated_session = await engine.start_exam(command.session_id)

            logger.info(
                "ÖSYM sınavı başlatıldı",
                extra={
                    "session_id": command.session_id,
                    "student_id": command.student_id,
                    "exam_type": updated_session.exam_config.exam_type.value,
                },
            )

            return {
                "session_id": updated_session.session_id,
                "student_id": updated_session.student_id,
                "exam_type": updated_session.exam_config.exam_type.value,
                "status": updated_session.status.value,
                "total_questions": updated_session.exam_config.total_questions,
                "duration_minutes": updated_session.exam_config.duration_minutes,
                "current_question_index": updated_session.current_question_index,
                "started_at": updated_session.started_at,
                "completed_at": updated_session.completed_at,
            }
        except ValueError as e:
            logger.error(
                f"Sınav başlatma hatası: {e}",
                extra={
                    "session_id": command.session_id,
                    "student_id": command.student_id,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Islem basarisiz. Lutfen tekrar deneyin.",
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Beklenmeyen sınav başlatma hatası: {e}",
                extra={
                    "session_id": command.session_id,
                    "student_id": command.student_id,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Sınav başlatılırken beklenmeyen bir hata oluştu",
            )


class SaveAnswerCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    student_id: str
    session_id: str
    question_id: str
    selected_answer: str | None = None
    response_time: float | None = None
    rating: int | None = None


class SaveAnswerCommandHandler(CommandHandler[SaveAnswerCommand, dict[str, Any]]):
    async def handle(self, command: SaveAnswerCommand) -> dict[str, Any]:
        engine = _get_engine()
        try:
            session_data = await engine.get_session_data(command.session_id)
            if not session_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Sınav oturumu bulunamadı",
                )

            if str(session_data.student_id) != str(command.student_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu sınava erişim yetkiniz yok",
                )

            success = await engine.save_answer(
                session_id=command.session_id,
                question_id=command.question_id,
                selected_answer=command.selected_answer,
                response_time=command.response_time,
            )

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cevap kaydedilemedi",
                )

            logger.debug(
                "Cevap kaydedildi",
                extra={
                    "session_id": command.session_id,
                    "question_id": command.question_id,
                    "answer": command.selected_answer,
                    "response_time": command.response_time,
                },
            )

            bkt_result = None
            if True:
                try:
                    import os as _os

                    if _os.environ.get("ALGO_FIRE_AND_FORGET", "yes").lower() in (
                        "1",
                        "true",
                        "yes",
                    ):
                        if not hasattr(asyncio, "_bkt_semaphore"):
                            asyncio._bkt_semaphore = asyncio.Semaphore(10)

                        async def _background_bkt_full(
                            student_id_val,
                            session_id_val,
                            question_id_val,
                            selected_answer_val,
                            rating_input,
                        ):
                            from sqlalchemy import select

                            from core.database import get_db_session_context
                            from models.exam_db import StudentAnswer
                            from models.question_bank import (
                                QuestionBankItem as Question,
                            )
                            from models.question_bank import (
                                QuestionContent,
                                QuestionMetadata,
                                QuestionStatistics,
                            )
                            from services.bkt_service import BKTService

                            async with asyncio._bkt_semaphore:
                                async with get_db_session_context() as bg_db:
                                    try:
                                        q = await bg_db.execute(
                                            select(
                                                QuestionContent.correct_answer,
                                                Question.primary_topic_id,
                                                QuestionMetadata.subject_area,
                                                QuestionStatistics.irt_discrimination,
                                                QuestionStatistics.irt_difficulty,
                                                QuestionStatistics.irt_guessing,
                                            )
                                            .outerjoin(
                                                QuestionContent,
                                                QuestionContent.id == Question.id,
                                            )
                                            .outerjoin(
                                                QuestionMetadata,
                                                QuestionMetadata.id == Question.id,
                                            )
                                            .outerjoin(
                                                QuestionStatistics,
                                                QuestionStatistics.id == Question.id,
                                            )
                                            .where(Question.id == question_id_val)
                                        )
                                        row = q.first()
                                        if not (row and row.primary_topic_id):
                                            return

                                        correct = bool(
                                            row.correct_answer
                                            and selected_answer_val.strip().upper()
                                            == row.correct_answer.strip().upper()
                                        )
                                        rating = rating_input or (3 if correct else 1)
                                        subject_slug = (
                                            row.subject_area or "matematik"
                                        ).lower()

                                        answered_questions = []
                                        responses = []
                                        try:
                                            prev = await bg_db.execute(
                                                select(
                                                    StudentAnswer.question_id,
                                                    StudentAnswer.is_correct,
                                                ).where(
                                                    StudentAnswer.exam_session_id
                                                    == session_id_val,
                                                    StudentAnswer.is_correct.isnot(
                                                        None
                                                    ),
                                                )
                                            )
                                            prev_rows = prev.all()
                                            if prev_rows:
                                                prev_qids = [
                                                    r.question_id for r in prev_rows
                                                ]
                                                prev_correct_map = {
                                                    r.question_id: r.is_correct
                                                    for r in prev_rows
                                                }
                                                irt_q = await bg_db.execute(
                                                    select(
                                                        Question.id,
                                                        QuestionStatistics.irt_discrimination,
                                                        QuestionStatistics.irt_difficulty,
                                                        QuestionStatistics.irt_guessing,
                                                    )
                                                    .outerjoin(
                                                        QuestionStatistics,
                                                        QuestionStatistics.id
                                                        == Question.id,
                                                    )
                                                    .where(Question.id.in_(prev_qids))
                                                )
                                                for irt_row in irt_q.all():
                                                    answered_questions.append(
                                                        {
                                                            "irt_a": float(
                                                                irt_row.irt_discrimination
                                                                or 1.0
                                                            ),
                                                            "irt_b": float(
                                                                irt_row.irt_difficulty
                                                                or 0.0
                                                            ),
                                                            "irt_c": float(
                                                                irt_row.irt_guessing
                                                                or 0.2
                                                            ),
                                                        }
                                                    )
                                                    responses.append(
                                                        bool(
                                                            prev_correct_map.get(
                                                                irt_row.id
                                                            )
                                                        )
                                                    )
                                        except Exception as irt_err:
                                            logger.debug(
                                                "IRT history fetch skipped: %s", irt_err
                                            )

                                        answered_questions.append(
                                            {
                                                "irt_a": float(
                                                    row.irt_discrimination or 1.0
                                                ),
                                                "irt_b": float(
                                                    row.irt_difficulty or 0.0
                                                ),
                                                "irt_c": float(row.irt_guessing or 0.2),
                                            }
                                        )
                                        responses.append(correct)

                                        await BKTService.record_answer(
                                            student_id=student_id_val,
                                            topic_id=str(row.primary_topic_id),
                                            subject_slug=subject_slug,
                                            correct=correct,
                                            rating=rating,
                                            db=bg_db,
                                            answered_questions=answered_questions,
                                            responses=responses,
                                        )
                                        await bg_db.commit()
                                    except Exception:
                                        logger.exception(
                                            "BKT pipeline FAILED session=%s qid=%s — degraded mode",
                                            session_id_val,
                                            question_id_val,
                                        )

                        _task = asyncio.create_task(
                            _background_bkt_full(
                                command.student_id,
                                command.session_id,
                                command.question_id,
                                command.selected_answer,
                                command.rating,
                            )
                        )

                        def _on_done(
                            t, sid=command.session_id, qid=command.question_id
                        ):
                            try:
                                exc = t.exception()
                            except asyncio.CancelledError:
                                return
                            if exc is None:
                                return
                            try:
                                from services.bkt_service import _ALGO_ERRORS

                                _ALGO_ERRORS["bkt_write"] = (
                                    _ALGO_ERRORS.get("bkt_write", 0) + 1
                                )
                            except Exception as sayac_hatasi:
                                # Sayac guncellenemezse ASIL hata yine de
                                # asagida loglanir; ama sayacin kendisinin
                                # dustugu SESSIZ gecmemeli -- yoksa
                                # _ALGO_ERRORS bir sagligi olcuyor gibi
                                # gorunup aslinda eksik sayar (#495 sinifi).
                                logger.debug(
                                    "BKT hata sayaci guncellenemedi: %s",
                                    sayac_hatasi,
                                )
                            logger.exception(
                                "BKT fire-and-forget FAILED session=%s qid=%s",
                                sid,
                                qid,
                                exc_info=exc,
                            )

                        _task.add_done_callback(_on_done)
                        bkt_result = {"deferred": True}
                    else:
                        from sqlalchemy import select

                        from core.database import get_db_session_context
                        from models.exam_db import StudentAnswer
                        from models.question_bank import (
                            QuestionBankItem as Question,
                        )
                        from models.question_bank import (
                            QuestionContent,
                            QuestionMetadata,
                            QuestionStatistics,
                        )
                        from services.bkt_service import BKTService

                        async with get_db_session_context() as db:
                            q = await db.execute(
                                select(
                                    QuestionContent.correct_answer,
                                    Question.primary_topic_id,
                                    QuestionMetadata.subject_area,
                                    QuestionStatistics.irt_discrimination,
                                    QuestionStatistics.irt_difficulty,
                                    QuestionStatistics.irt_guessing,
                                )
                                .outerjoin(
                                    QuestionContent, QuestionContent.id == Question.id
                                )
                                .outerjoin(
                                    QuestionMetadata, QuestionMetadata.id == Question.id
                                )
                                .outerjoin(
                                    QuestionStatistics,
                                    QuestionStatistics.id == Question.id,
                                )
                                .where(Question.id == command.question_id)
                            )
                            row = q.first()
                            if row and row.primary_topic_id:
                                correct = bool(
                                    row.correct_answer
                                    and command.selected_answer.strip().upper()
                                    == row.correct_answer.strip().upper()
                                )
                                rating = command.rating or (3 if correct else 1)
                                subject_slug = (row.subject_area or "matematik").lower()

                                answered_questions = []
                                responses = []
                                try:
                                    prev = await db.execute(
                                        select(
                                            StudentAnswer.question_id,
                                            StudentAnswer.is_correct,
                                        ).where(
                                            StudentAnswer.exam_session_id
                                            == command.session_id,
                                            StudentAnswer.is_correct.isnot(None),
                                        )
                                    )
                                    prev_rows = prev.all()
                                    if prev_rows:
                                        prev_qids = [r.question_id for r in prev_rows]
                                        prev_correct_map = {
                                            r.question_id: r.is_correct
                                            for r in prev_rows
                                        }
                                        irt_q = await db.execute(
                                            select(
                                                Question.id,
                                                QuestionStatistics.irt_discrimination,
                                                QuestionStatistics.irt_difficulty,
                                                QuestionStatistics.irt_guessing,
                                            )
                                            .outerjoin(
                                                QuestionStatistics,
                                                QuestionStatistics.id == Question.id,
                                            )
                                            .where(Question.id.in_(prev_qids))
                                        )
                                        for irt_row in irt_q.all():
                                            answered_questions.append(
                                                {
                                                    "irt_a": float(
                                                        irt_row.irt_discrimination
                                                        or 1.0
                                                    ),
                                                    "irt_b": float(
                                                        irt_row.irt_difficulty or 0.0
                                                    ),
                                                    "irt_c": float(
                                                        irt_row.irt_guessing or 0.2
                                                    ),
                                                }
                                            )
                                            responses.append(
                                                bool(prev_correct_map.get(irt_row.id))
                                            )
                                except Exception as irt_err:
                                    logger.debug(
                                        "IRT history fetch skipped: %s", irt_err
                                    )

                                answered_questions.append(
                                    {
                                        "irt_a": float(row.irt_discrimination or 1.0),
                                        "irt_b": float(row.irt_difficulty or 0.0),
                                        "irt_c": float(row.irt_guessing or 0.2),
                                    }
                                )
                                responses.append(correct)

                                bkt_result = await BKTService.record_answer(
                                    student_id=command.student_id,
                                    topic_id=str(row.primary_topic_id),
                                    subject_slug=subject_slug,
                                    correct=correct,
                                    rating=rating,
                                    db=db,
                                    answered_questions=answered_questions,
                                    responses=responses,
                                )
                                await db.commit()
                except Exception:
                    logger.exception(
                        "BKT pipeline FAILED session=%s qid=%s — degraded mode",
                        command.session_id,
                        command.question_id,
                    )

            algorithm_degraded = bkt_result is None
            return {
                "success": True,
                "message": "Cevap başarıyla kaydedildi",
                "auto_saved": True,
                "algorithm": bkt_result,
                "algorithm_degraded": algorithm_degraded,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Cevap kaydetme hatası: {e}",
                extra={
                    "session_id": command.session_id,
                    "question_id": command.question_id,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cevap kaydedilirken beklenmeyen bir hata oluştu",
            )


class NavigateQuestionCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    student_id: str
    session_id: str
    question_index: int


class NavigateQuestionCommandHandler(
    CommandHandler[NavigateQuestionCommand, dict[str, Any]]
):
    async def handle(self, command: NavigateQuestionCommand) -> dict[str, Any]:
        engine = _get_engine()
        try:
            session_data = await engine.get_session_data(command.session_id)
            if not session_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Sınav oturumu bulunamadı",
                )

            if str(session_data.student_id) != str(command.student_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu sınava erişim yetkiniz yok",
                )

            question = await engine.navigate_to_question(
                command.session_id, command.question_index
            )

            if not question:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Hedef soru bulunamadı veya geçersiz soru indeksi",
                )

            return {
                "id": question.id,
                "question_text": question.question_text,
                "question_image_url": question.question_image_url,
                "image_alt_text": question.image_ocr_text[:200]
                if question.image_ocr_text
                else None,
                "image_width": question.image_width,
                "image_height": question.image_height,
                "option_a": question.option_a,
                "option_b": question.option_b,
                "option_c": question.option_c,
                "option_d": question.option_d,
                "option_e": question.option_e,
                "subject_area": question.subject_area,
                "topic": question.primary_topic_id or question.subject_area,
                "difficulty": question.difficulty_level.value
                if question.difficulty_level
                else "medium",
                "question_order": command.question_index + 1,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Soru navigasyon hatası: {e}",
                extra={
                    "session_id": command.session_id,
                    "question_index": command.question_index,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Soru navigasyonunda beklenmeyen bir hata oluştu",
            )


class FlagQuestionCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    student_id: str
    session_id: str
    question_id: str
    flagged: bool


class FlagQuestionCommandHandler(CommandHandler[FlagQuestionCommand, dict[str, Any]]):
    async def handle(self, command: FlagQuestionCommand) -> dict[str, Any]:
        engine = _get_engine()
        try:
            session_data = await engine.get_session_data(command.session_id)
            if not session_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Sınav oturumu bulunamadı",
                )

            if str(session_data.student_id) != str(command.student_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu sınava erişim yetkiniz yok",
                )

            success = await engine.flag_question(
                session_id=command.session_id,
                question_id=command.question_id,
                flagged=command.flagged,
            )

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Soru işaretleme işlemi başarısız",
                )

            return {
                "success": True,
                "message": "Soru işaretleme durumu güncellendi",
                "flagged": command.flagged,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Soru işaretleme hatası: {e}",
                extra={
                    "session_id": command.session_id,
                    "question_id": command.question_id,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Soru işaretleme sırasında beklenmeyen bir hata oluştu",
            )


class CompleteExamCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    student_id: str
    session_id: str


class CompleteExamCommandHandler(CommandHandler[CompleteExamCommand, dict[str, Any]]):
    async def handle(self, command: CompleteExamCommand) -> dict[str, Any]:
        engine = _get_engine()
        try:
            session_data = await engine.get_session_data(command.session_id)
            if not session_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Sınav oturumu bulunamadı",
                )

            if str(session_data.student_id) != str(command.student_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu sınava erişim yetkiniz yok",
                )

            performance_metrics = await engine.complete_exam(
                command.session_id, manual_completion=True
            )

            logger.info(
                "ÖSYM sınavı tamamlandı",
                extra={
                    "session_id": command.session_id,
                    "student_id": command.student_id,
                    "net_score": performance_metrics.net_score,
                    "raw_score": performance_metrics.raw_score,
                },
            )

            try:
                from core.database import get_db_session_context
                from services.learning_event_service import LearningEventService

                async with get_db_session_context() as db:
                    event_report = await LearningEventService.on_exam_completed(
                        student_id=str(command.student_id),
                        correct_answers=performance_metrics.correct_answers,
                        total_questions=performance_metrics.total_questions,
                        net_score=performance_metrics.net_score,
                        db=db,
                    )
                    logger.info(
                        "Exam event report",
                        extra={"report": str(event_report)},
                    )
            except Exception as event_err:
                logger.warning("Exam event processing skipped: %s", event_err)

            subject_perfs = await engine.get_subject_performance(command.session_id)
            konu_data = [
                {
                    "subject": p.subject,
                    "total_questions": p.total_questions,
                    "correct_answers": p.correct_answers,
                    "wrong_answers": p.wrong_answers,
                    "empty_answers": p.empty_answers,
                    "success_rate": p.success_rate,
                    "average_response_time": p.average_response_time,
                    "difficulty_level": p.difficulty_level,
                    # B3: konu kırılımı. Eklemeli sözleşme — mevcut 8 alan korunur.
                    # Bunlar geçmeden GET /performance ayırt edilemez satırlar döner.
                    "topic_code": p.topic_code,
                    "topic_name": p.topic_name,
                }
                for p in subject_perfs
            ]

            return {
                "total_questions": performance_metrics.total_questions,
                "answered_questions": performance_metrics.answered_questions,
                "correct_answers": performance_metrics.correct_answers,
                "wrong_answers": performance_metrics.wrong_answers,
                "empty_answers": performance_metrics.empty_answers,
                "net_score": performance_metrics.net_score,
                "raw_score": performance_metrics.raw_score,
                "percentile": performance_metrics.percentile,
                "estimated_ability": performance_metrics.estimated_ability,
                "confidence_level": performance_metrics.confidence_level,
                "konu_performanslari": konu_data,
            }
        except ValueError as e:
            logger.error(
                f"Sınav tamamlama hatası: {e}",
                extra={"session_id": command.session_id},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Islem basarisiz. Lutfen tekrar deneyin.",
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Beklenmeyen sınav tamamlama hatası: {e}",
                extra={"session_id": command.session_id},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Sınav tamamlanırken beklenmeyen bir hata oluştu",
            )


class CancelExamCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    student_id: str
    session_id: str


class CancelExamCommandHandler(CommandHandler[CancelExamCommand, dict[str, Any]]):
    async def handle(self, command: CancelExamCommand) -> dict[str, Any]:
        engine = _get_engine()
        try:
            session_data = await engine.get_session_data(command.session_id)
            if not session_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Sınav oturumu bulunamadı",
                )

            if str(session_data.student_id) != str(command.student_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu sınava erişim yetkiniz yok",
                )

            if session_data.status not in [
                ExamStatus.NOT_STARTED,
                ExamStatus.IN_PROGRESS,
            ]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tamamlanmış veya iptal edilmiş sınavlar tekrar iptal edilemez",
                )

            session_data.status = ExamStatus.ABANDONED
            session_data.completed_at = datetime.now()

            if command.session_id in engine.auto_save_tasks:
                engine.auto_save_tasks[command.session_id].cancel()
                del engine.auto_save_tasks[command.session_id]

            autoclose_key = f"autoclose:{command.session_id}"
            if autoclose_key in engine.auto_save_tasks:
                engine.auto_save_tasks[autoclose_key].cancel()
                del engine.auto_save_tasks[autoclose_key]

            if command.session_id in engine.active_sessions:
                del engine.active_sessions[command.session_id]

            logger.info(
                "ÖSYM sınavı iptal edildi",
                extra={
                    "session_id": command.session_id,
                    "student_id": command.student_id,
                },
            )

            return {
                "success": True,
                "message": "Sınav başarıyla iptal edildi",
                "session_id": command.session_id,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Sınav iptal etme hatası: {e}",
                extra={"session_id": command.session_id},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Sınav iptal edilirken beklenmeyen bir hata oluştu",
            )
