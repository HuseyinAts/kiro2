# -*- coding: utf-8 -*-
"""
Sınav Cevap Takip API Endpoint'leri
Türkiye Üniversite Sınavları Hazırlık Platformu

Bu modül sınav cevap takibi için API endpoint'lerini sağlar:
- Boş bırakılan soruların listesi
- Tamamlanma yüzdesi
- Cevap durumu sorgulama

REQ-1.6: Sınav arayüzü gereksinimleri
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field

from core.database import get_async_session
from core.dependencies import get_current_user
from core.structured_logger import get_logger
from services.exam_answer_tracking_service import (
    create_answer_tracking_service,
)

router = APIRouter(prefix="/api/v1/exam-answer-tracking", tags=["Sınav Cevap Takibi"])
security = HTTPBearer()
logger = get_logger("exam_answer_tracking_api")


# Pydantic Response Models
class AnswerStatusResponse(BaseModel):
    """Cevap durumu yanıtı"""

    question_id: str = Field(..., description="Soru ID'si")
    question_order: int = Field(..., description="Soru sırası")
    is_answered: bool = Field(..., description="Cevaplandı mı?")
    selected_answer: str | None = Field(
        None, description="Seçilen cevap (A, B, C, D, E)"
    )
    is_empty: bool = Field(..., description="Boş mu?")
    response_time_seconds: float = Field(..., description="Cevaplama süresi (saniye)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "question_id": "q123",
                "question_order": 5,
                "is_answered": True,
                "selected_answer": "B",
                "is_empty": False,
                "response_time_seconds": 45.2,
            }
        }
    }


class CompletionStatsResponse(BaseModel):
    """Tamamlanma istatistikleri yanıtı"""

    total_questions: int = Field(..., description="Toplam soru sayısı")
    answered_questions: int = Field(..., description="Cevaplanan soru sayısı (dolu)")
    unanswered_questions: int = Field(..., description="Cevaplanmayan soru sayısı")
    empty_answers: int = Field(..., description="Boş bırakılan soru sayısı")
    completion_percentage: float = Field(..., description="Tamamlanma yüzdesi")
    unanswered_question_ids: List[str] = Field(
        ..., description="Cevaplanmayan soru ID'leri"
    )
    unanswered_question_orders: List[int] = Field(
        ..., description="Cevaplanmayan soru sıraları"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_questions": 120,
                "answered_questions": 95,
                "unanswered_questions": 15,
                "empty_answers": 10,
                "completion_percentage": 87.5,
                "unanswered_question_ids": ["q45", "q67", "q89"],
                "unanswered_question_orders": [45, 67, 89],
            }
        }
    }


@router.get(
    "/{exam_session_id}/completion-stats",
    response_model=CompletionStatsResponse,
    summary="Sınav Tamamlanma İstatistikleri",
)
async def get_completion_statistics(
    exam_session_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Sınav tamamlanma istatistiklerini getir

    Bu endpoint aşağıdaki bilgileri sağlar:
    - **Toplam Soru Sayısı**: Sınavdaki toplam soru sayısı
    - **Cevaplanan Sorular**: Dolu cevap verilen sorular
    - **Cevaplanmayan Sorular**: Hiç dokunulmamış sorular
    - **Boş Cevaplar**: Boş bırakılan sorular
    - **Tamamlanma Yüzdesi**: Genel ilerleme yüzdesi
    - **Cevaplanmayan Soru Listesi**: ID ve sıra numaraları

    REQ-1.6: Tamamlanma yüzdesi hesaplama
    """
    try:
        async with get_async_session() as db_session:
            service = await create_answer_tracking_service(db_session)

            stats = await service.get_completion_stats(exam_session_id)

            logger.info(
                "Tamamlanma istatistikleri sunuldu",
                extra_data={
                    "exam_session_id": exam_session_id,
                    "user_id": current_user["user_id"],
                    "completion_percentage": stats.completion_percentage,
                },
            )

            return CompletionStatsResponse(
                total_questions=stats.total_questions,
                answered_questions=stats.answered_questions,
                unanswered_questions=stats.unanswered_questions,
                empty_answers=stats.empty_answers,
                completion_percentage=stats.completion_percentage,
                unanswered_question_ids=stats.unanswered_question_ids,
                unanswered_question_orders=stats.unanswered_question_orders,
            )

    except Exception as e:
        logger.error(
            f"Tamamlanma istatistikleri hatası: {e}",
            extra_data={
                "exam_session_id": exam_session_id,
                "user_id": current_user["user_id"],
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tamamlanma istatistikleri alınırken hata oluştu",
        )


@router.get(
    "/{exam_session_id}/answer-statuses",
    response_model=List[AnswerStatusResponse],
    summary="Tüm Cevap Durumları",
)
async def get_all_answer_statuses(
    exam_session_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Sınavdaki tüm soruların cevap durumlarını getir

    Her soru için:
    - Cevaplandı mı?
    - Hangi seçenek işaretlendi?
    - Boş mu?
    - Cevaplama süresi

    REQ-1.6: Cevap durumu takibi
    """
    try:
        async with get_async_session() as db_session:
            service = await create_answer_tracking_service(db_session)

            statuses = await service.get_all_answer_statuses(exam_session_id)

            response = [
                AnswerStatusResponse(
                    question_id=status.question_id,
                    question_order=status.question_order,
                    is_answered=status.is_answered,
                    selected_answer=status.selected_answer,
                    is_empty=status.is_empty,
                    response_time_seconds=status.response_time_seconds,
                )
                for status in statuses
            ]

            logger.info(
                "Cevap durumları sunuldu",
                extra_data={
                    "exam_session_id": exam_session_id,
                    "user_id": current_user["user_id"],
                    "total_questions": len(response),
                },
            )

            return response

    except Exception as e:
        logger.error(
            f"Cevap durumları hatası: {e}",
            extra_data={
                "exam_session_id": exam_session_id,
                "user_id": current_user["user_id"],
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cevap durumları alınırken hata oluştu",
        )


@router.get(
    "/{exam_session_id}/unanswered-questions",
    response_model=List[int],
    summary="Cevaplanmayan Soru Sıraları",
)
async def get_unanswered_questions(
    exam_session_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Cevaplanmayan soruların sıra numaralarını getir

    Öğrencinin gözden kaçırdığı soruları görmek için kullanılır.

    REQ-1.6: Cevaplanmayan soru takibi
    """
    try:
        async with get_async_session() as db_session:
            service = await create_answer_tracking_service(db_session)

            stats = await service.get_completion_stats(exam_session_id)

            logger.info(
                "Cevaplanmayan sorular sunuldu",
                extra_data={
                    "exam_session_id": exam_session_id,
                    "user_id": current_user["user_id"],
                    "unanswered_count": len(stats.unanswered_question_orders),
                },
            )

            return stats.unanswered_question_orders

    except Exception as e:
        logger.error(
            f"Cevaplanmayan sorular hatası: {e}",
            extra_data={
                "exam_session_id": exam_session_id,
                "user_id": current_user["user_id"],
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cevaplanmayan sorular alınırken hata oluştu",
        )


@router.get(
    "/{exam_session_id}/empty-answers",
    response_model=List[int],
    summary="Boş Bırakılan Soru Sıraları",
)
async def get_empty_answers(
    exam_session_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Boş bırakılan soruların sıra numaralarını getir

    Öğrencinin bilinçli olarak boş bıraktığı soruları görmek için kullanılır.

    REQ-1.6: Boş cevap takibi
    """
    try:
        async with get_async_session() as db_session:
            service = await create_answer_tracking_service(db_session)

            statuses = await service.get_all_answer_statuses(exam_session_id)

            # Boş cevapları filtrele
            empty_orders = [
                status.question_order
                for status in statuses
                if status.is_empty and status.is_answered
            ]

            logger.info(
                "Boş cevaplar sunuldu",
                extra_data={
                    "exam_session_id": exam_session_id,
                    "user_id": current_user["user_id"],
                    "empty_count": len(empty_orders),
                },
            )

            return empty_orders

    except Exception as e:
        logger.error(
            f"Boş cevaplar hatası: {e}",
            extra_data={
                "exam_session_id": exam_session_id,
                "user_id": current_user["user_id"],
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Boş cevaplar alınırken hata oluştu",
        )


@router.post(
    "/{exam_session_id}/mark-empty/{question_id}",
    status_code=status.HTTP_200_OK,
    summary="Cevabı Boş Olarak İşaretle",
)
async def mark_answer_as_empty(
    exam_session_id: str,
    question_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Bir cevabı boş olarak işaretle

    Öğrenci bir soruyu bilinçli olarak boş bırakmak istediğinde kullanılır.

    REQ-1.6: Boş cevap işaretleme
    """
    try:
        async with get_async_session() as db_session:
            service = await create_answer_tracking_service(db_session)

            success = await service.mark_answer_as_empty(
                exam_session_id=exam_session_id, question_id=question_id
            )

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cevap boş olarak işaretlenemedi",
                )

            logger.info(
                "Cevap boş olarak işaretlendi",
                extra_data={
                    "exam_session_id": exam_session_id,
                    "question_id": question_id,
                    "user_id": current_user["user_id"],
                },
            )

            return {"success": True, "message": "Cevap boş olarak işaretlendi"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Boş işaretleme hatası: {e}",
            extra_data={
                "exam_session_id": exam_session_id,
                "question_id": question_id,
                "user_id": current_user["user_id"],
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cevap boş olarak işaretlenirken hata oluştu",
        )
