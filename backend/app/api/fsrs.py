"""
KIRO2 — FSRS API Router
========================
Endpoint'ler:
  GET  /api/v1/fsrs/due                → Vadesi gelen kartları listele
  POST /api/v1/fsrs/review             → Tek yanıt güncelleme (standalone)
  GET  /api/v1/fsrs/stats              → Kullanıcı istatistikleri
  GET  /api/v1/fsrs/due-count          → Hızlı kart sayısı (badge için)

Bu dosya ayrıca eski FSRS API uyumluluğunu da korur.
"""

from __future__ import annotations

import logging
from uuid import UUID
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

# Yeni API bağımlılıkları
from app.core.deps import User, get_current_user, get_db
from app.schemas.fsrs_schemas import (
    DueCountResponse,
    DueItemResponse,
    ReviewRequest,
    ReviewResponse,
    StatsResponse,
)
from app.services.fsrs_service import FSRSService

# Eski API bağımlılıkları
from core.dependencies import get_current_user as get_current_user_old, get_db as get_db_old
from models.database import User as DBUser
from services._deprecated.fsrs_service import FSRSService as DeprecatedFSRSService

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/api/v1/fsrs", tags=["FSRS"])
fsrs_service = DeprecatedFSRSService()


# ==================== ESKİ API PYDANTIC MODELLERİ ====================

class CreateFlashcardRequest(BaseModel):
    """Flashcard oluşturma isteği"""
    subject: str = Field(..., description="Konu (Matematik, Türkçe, vb.)")
    topic: str = Field(..., description="Alt konu")
    content: str = Field(..., description="Kart içeriği")
    answer: str = Field(..., description="Cevap")


class ReviewFlashcardRequest(BaseModel):
    """Flashcard inceleme isteği"""
    grade: int = Field(
        ..., ge=1, le=4, description="Değerlendirme (1=Again, 2=Hard, 3=Good, 4=Easy)"
    )
    response_time_ms: int = Field(..., ge=0, description="Yanıt süresi (milisaniye)")


class FlashcardResponse(BaseModel):
    """Flashcard yanıt modeli"""
    id: str
    subject: str
    topic: str
    content: str
    answer: str
    difficulty: float
    stability: float
    retrievability: float
    due_date: str | None
    state: str
    review_count: int
    lapse_count: int
    retention_probability: float
    is_overdue: bool


class StudyRecommendationsResponse(BaseModel):
    """Çalışma önerileri yanıt modeli"""
    due_cards_count: int
    upcoming_cards_count: int
    difficult_cards_count: int
    cultural_period: str
    period_advice: str
    recommended_study_time: int
    priority_subjects: list[str]
    total_cards: int
    new_cards: int
    learning_cards: int
    review_cards: int


class StudySessionResponse(BaseModel):
    """Çalışma oturumu yanıt modeli"""
    session_id: str
    duration_minutes: int | None = None
    cards_reviewed: int = 0
    cards_learned: int = 0
    average_grade: float | None = None
    success_rate: float = 0.0


# ==================== YENİ API ENDPOINT'LERİ ====================

@router.get(
    "/due",
    response_model=list[DueItemResponse],
    summary="Vadesi gelen tekrar kartlarını getir",
)
async def get_due_items(
    subject_id: UUID | None = Query(None, description="Derse göre filtrele"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DueItemResponse]:
    svc = FSRSService(db)
    items = await svc.get_due_items(
        str(current_user.id),
        subject_id=str(subject_id) if subject_id else None,
        limit=limit,
    )
    results = []
    for s, irt in items:
        if not isinstance(irt, dict):
            logger.warning(
                "get_due_items: beklenen dict, alınan %s — atlanıyor", type(irt)
            )
            continue
        results.append(
            DueItemResponse(
                question_id=s.question_id,
                stability=round(s.stability, 3),
                difficulty=round(s.difficulty, 2),
                due_date=s.due_date,
                retrievability=round(s.retrievability, 3),
                urgency_score=round(s.urgency_score, 3),
                state=s.state,
                reps=s.reps,
                lapses=s.lapses,
                stem=irt.get("question_text"),
                options={
                    "A": irt.get("option_a", ""),
                    "B": irt.get("option_b", ""),
                    "C": irt.get("option_c", ""),
                    "D": irt.get("option_d", ""),
                },
                subject_id=irt.get("subject_id"),
            )
        )
    return results


@router.post(
    "/review",
    response_model=ReviewResponse,
    summary="Standalone tekrar yanıtla (CAT dışı)",
)
async def submit_review(
    body: ReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewResponse:
    svc = FSRSService(db)
    result = await svc.apply_review(
        user_id=str(current_user.id),
        question_id=str(body.question_id),
        is_correct=body.is_correct,
        response_ms=body.response_ms,
        item_b=body.item_b,
    )
    ns = result.new_state
    return ReviewResponse(
        question_id=ns.question_id,
        new_stability=round(ns.stability, 3),
        new_difficulty=round(ns.difficulty, 2),
        interval_days=result.interval_days,
        due_date=ns.due_date,
        state=ns.state,
        puan=result.puan,
    )


@router.get(
    "/due-count",
    response_model=DueCountResponse,
    summary="Vadesi gelen kart sayısı (hızlı)",
)
async def get_due_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DueCountResponse:
    svc = FSRSService(db)
    count = await svc.get_due_count(str(current_user.id))
    return DueCountResponse(count=count)


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Öğrencinin FSRS istatistikleri",
)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StatsResponse:
    from sqlalchemy import text

    result = await db.execute(
        text("""
        SELECT
            COUNT(*)                                            AS total,
            SUM(CASE WHEN state = 0 THEN 1 ELSE 0 END)         AS new_count,
            SUM(CASE WHEN state IN (1,3) THEN 1 ELSE 0 END)    AS learning,
            SUM(CASE WHEN state = 2 THEN 1 ELSE 0 END)         AS review,
            SUM(CASE WHEN due_date <= NOW() + INTERVAL '4 hours'
                      AND state IN (1,2,3)
                     THEN 1 ELSE 0 END)                         AS due_now,
            ROUND(AVG(stability)::NUMERIC, 2)                  AS avg_stability,
            SUM(lapses)                                         AS total_lapses
        FROM user_item_fsrs
        WHERE user_id = :uid
    """),
        {"uid": str(current_user.id)},
    )

    row = result.fetchone()
    if not row or not row.total:
        return StatsResponse()

    return StatsResponse(
        total_cards=int(row.total),
        new_count=int(row.new_count or 0),
        learning_count=int(row.learning or 0),
        review_count=int(row.review or 0),
        due_now=int(row.due_now or 0),
        avg_stability=float(row.avg_stability or 0),
        total_lapses=int(row.total_lapses or 0),
    )


# ==================== ESKİ API ENDPOINT'LERİ (UYUMLULUK KATMANI) ====================

@router.post("/flashcards", response_model=dict[str, Any])
async def create_flashcard(
    request: CreateFlashcardRequest,
    current_user: DBUser = Depends(get_current_user_old),
    db: Session = Depends(get_db_old),
):
    try:
        card = await fsrs_service.create_flashcard(
            student_id=current_user.id,
            subject=request.subject,
            topic=request.topic,
            content=request.content,
            answer=request.answer,
            db=db,
        )
        return {
            "success": True,
            "message": "Flashcard başarıyla oluşturuldu",
            "data": {
                "id": card.id,
                "subject": card.subject,
                "topic": card.topic,
                "content": card.content,
                "answer": card.answer,
                "due_date": card.due_date.isoformat() if card.due_date else None,
                "state": card.state,
            },
        }
    except Exception as e:
        logger.error(f"Flashcard oluşturma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/flashcards/due", response_model=dict[str, Any])
async def get_due_flashcards(
    limit: int = Query(20, ge=1, le=100, description="Maksimum kart sayısı"),
    current_user: DBUser = Depends(get_current_user_old),
    db: Session = Depends(get_db_old),
):
    try:
        due_cards = await fsrs_service.get_due_cards(
            student_id=current_user.id, limit=limit, db=db
        )
        return {
            "success": True,
            "message": f"{len(due_cards)} vadesi gelen kart bulundu",
            "data": {"cards": due_cards, "total_count": len(due_cards)},
        }
    except Exception as e:
        logger.error(f"Vadesi gelen kartları getirme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/flashcards/{card_id}/review", response_model=dict[str, Any])
async def review_flashcard(
    card_id: str,
    request: ReviewFlashcardRequest,
    current_user: DBUser = Depends(get_current_user_old),
    db: Session = Depends(get_db_old),
):
    try:
        result = await fsrs_service.review_flashcard(
            card_id=card_id,
            grade=request.grade,
            response_time_ms=request.response_time_ms,
            student_id=current_user.id,
            db=db,
        )
        grade_descriptions = {
            1: "Tekrar et (Again) - Kartı hatırlamadınız",
            2: "Zor (Hard) - Kartı zorlanarak hatırladınız",
            3: "İyi (Good) - Kartı başarıyla hatırladınız",
            4: "Kolay (Easy) - Kartı çok kolay hatırladınız",
        }
        result["grade_description"] = grade_descriptions.get(
            request.grade, "Bilinmeyen"
        )
        result["message"] = (
            f"Kart incelendi. Sonraki tekrar: {result['interval_days']} gün sonra"
        )
        return {
            "success": True,
            "message": "Flashcard başarıyla incelendi",
            "data": result,
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
    except Exception as e:
        logger.error(f"Flashcard inceleme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/recommendations", response_model=dict[str, Any])
async def get_study_recommendations(
    current_user: DBUser = Depends(get_current_user_old), db: Session = Depends(get_db_old)
):
    try:
        recommendations = await fsrs_service.get_study_recommendations(
            student_id=current_user.id, db=db
        )
        return {
            "success": True,
            "message": "Çalışma önerileri başarıyla getirildi",
            "data": recommendations,
        }
    except Exception as e:
        logger.error(f"Çalışma önerileri getirme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/statistics", response_model=dict[str, Any])
async def get_student_statistics(
    current_user: DBUser = Depends(get_current_user_old), db: Session = Depends(get_db_old)
):
    try:
        statistics = await fsrs_service.get_student_statistics(
            student_id=current_user.id, db=db
        )
        return {
            "success": True,
            "message": "İstatistikler başarıyla getirildi",
            "data": statistics,
        }
    except Exception as e:
        logger.error(f"İstatistik getirme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/study-sessions/start", response_model=dict[str, Any])
async def start_study_session(
    session_type: str = Query(
        "regular", description="Oturum türü (regular, exam_prep, review)"
    ),
    current_user: DBUser = Depends(get_current_user_old),
    db: Session = Depends(get_db_old),
):
    try:
        session_id = await fsrs_service.start_study_session(
            student_id=current_user.id, session_type=session_type, db=db
        )
        return {
            "success": True,
            "message": "Çalışma oturumu başlatıldı",
            "data": {
                "session_id": session_id,
                "session_type": session_type,
                "started_at": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"Çalışma oturumu başlatma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/study-sessions/{session_id}/end", response_model=dict[str, Any])
async def end_study_session(
    session_id: str,
    current_user: DBUser = Depends(get_current_user_old),
    db: Session = Depends(get_db_old),
):
    try:
        summary = await fsrs_service.end_study_session(session_id=session_id, db=db)
        return {
            "success": True,
            "message": "Çalışma oturumu sonlandırıldı",
            "data": summary,
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
    except Exception as e:
        logger.error(f"Çalışma oturumu sonlandırma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/cultural-periods", response_model=dict[str, Any])
async def get_cultural_periods_info():
    try:
        cultural_info = {
            "periods": {
                "normal": {
                    "name": "Normal Dönem",
                    "description": "Düzenli eğitim-öğretim dönemi",
                    "effect_multiplier": 1.0,
                    "recommendations": "Normal çalışma rutininizi sürdürün",
                },
                "ramadan": {
                    "name": "Ramazan Ayı",
                    "description": "Oruç tutma ve dini ibadetlerin yoğun olduğu dönem",
                    "effect_multiplier": 0.75,
                    "recommendations": "Sahur sonrası ve iftar öncesi çalışma saatleri daha verimli olabilir",
                },
                "exam_season": {
                    "name": "Sınav Dönemi",
                    "description": "Okul sınavları ve merkezi sınavların yapıldığı dönem",
                    "effect_multiplier": 1.35,
                    "recommendations": "Kısa aralıklarla tekrar yapın ve stres yönetimi tekniklerini kullanın",
                },
                "summer_break": {
                    "name": "Yaz Tatili",
                    "description": "Okul tatili dönemi",
                    "effect_multiplier": 0.60,
                    "recommendations": "Düzenli çalışma rutini oluşturun, unutmayı önlemek için hafif tekrarlar yapın",
                },
                "religious_holiday": {
                    "name": "Dini Bayramlar",
                    "description": "Ramazan ve Kurban bayramları",
                    "effect_multiplier": 0.80,
                    "recommendations": "Bayram döneminde aile zamanı ile çalışma dengesini kurun",
                },
            },
            "cultural_factors": {
                "group_study_bonus": {
                    "name": "Grup Çalışması Bonusu",
                    "multiplier": 1.25,
                    "description": "Türk öğrencilerin grup çalışmasını tercih etme eğilimi",
                },
                "family_pressure": {
                    "name": "Aile Baskısı Faktörü",
                    "multiplier": 1.15,
                    "description": "Aile beklentilerinin öğrenci performansına etkisi",
                },
                "weekend_effect": {
                    "name": "Hafta Sonu Etkisi",
                    "multiplier": 0.90,
                    "description": "Hafta sonlarında çalışma motivasyonundaki azalma",
                },
            },
            "algorithm_info": {
                "name": "Türk Öğrenci Davranışlarına Optimize Edilmiş FSRS",
                "version": "1.0",
                "parameters_count": 17,
                "training_data": "10,000 Türk öğrenci verisi",
                "cultural_adaptations": 8,
                "description": "Anki'nin FSRS 4.5 algoritmasını Türk kültürüne uyarlayan devrimsel sistem",
            },
        }
        return {
            "success": True,
            "message": "Kültürel dönem bilgileri getirildi",
            "data": cultural_info,
        }
    except Exception as e:
        logger.error(f"Kültürel dönem bilgileri getirme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/health", response_model=dict[str, Any])
async def fsrs_health_check():
    try:
        algorithm_status = "healthy"
        test_params = fsrs_service.fsrs_algorithm.turkish_params
        if len(test_params) != 17:
            algorithm_status = "unhealthy"

        return {
            "success": True,
            "message": "FSRS sistemi sağlık kontrolü tamamlandı",
            "data": {
                "algorithm_status": algorithm_status,
                "parameters_count": len(test_params),
                "cultural_adjustments_count": len(
                    fsrs_service.fsrs_algorithm.cultural_adjustments
                ),
                "service_status": "healthy",
                "timestamp": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"FSRS sağlık kontrolü hatası: {e}")
        return {
            "success": False,
            "message": "FSRS sistemi sağlık kontrolünde hata",
            "data": {
                "algorithm_status": "unhealthy",
                "service_status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        }
