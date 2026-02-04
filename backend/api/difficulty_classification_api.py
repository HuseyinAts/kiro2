"""
Zorluk Seviyesi Sınıflandırma API
Task 74: Difficulty Level Classification API Endpoints

API Endpoints:
- GET /api/v1/difficulty/classify/{question_id} - Soru zorluğunu sınıflandır
- GET /api/v1/difficulty/visual-indicator/{level} - Görsel gösterge bilgisi
- POST /api/v1/difficulty/filter - Zorluğa göre soru filtrele
- GET /api/v1/difficulty/distribution - Zorluk dağılımı
- POST /api/v1/difficulty/update-realtime - Gerçek zamanlı güncelleme
- POST /api/v1/difficulty/batch-update - Toplu güncelleme
- GET /api/v1/difficulty/trend/{question_id} - Zorluk trendi
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from services.difficulty_classification_service import (
    DifficultyClassificationService,
    DifficultyLevel,
    get_difficulty_label,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/difficulty", tags=["Difficulty Classification"])


# ============================================================================
# Request/Response Models
# ============================================================================


class DifficultyClassificationResponse(BaseModel):
    """Zorluk sınıflandırma yanıtı"""

    question_id: str
    difficulty_level: str
    difficulty_score: float
    classification_method: str
    confidence: float
    irt_based_difficulty: Optional[float] = None
    performance_based_difficulty: Optional[float] = None
    visual_indicator: dict
    metadata: dict = {}


class FilterRequest(BaseModel):
    """Zorluk filtreleme isteği"""

    difficulty_levels: List[str] = Field(
        ..., description="Zorluk seviyeleri: very_easy, easy, medium, hard, very_hard"
    )
    topic_id: Optional[str] = None
    limit: int = Field(50, ge=1, le=200)


class BatchUpdateRequest(BaseModel):
    """Toplu güncelleme isteği"""

    question_ids: List[str]
    update_threshold_days: int = Field(7, ge=1, le=365)


class RealtimeUpdateRequest(BaseModel):
    """Gerçek zamanlı güncelleme isteği"""

    question_id: str
    new_response_data: dict


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/classify/{question_id}", response_model=DifficultyClassificationResponse)
async def classify_question_difficulty(
    question_id: str,
    force_recalculate: bool = Query(
        False, description="Cache'i atla ve yeniden hesapla"
    ),
    db: Session = Depends(get_db),
):
    """
    Soruyu 5 seviyeli zorluk ölçeğinde sınıflandır

    - **question_id**: Soru ID
    - **force_recalculate**: Cache'i atla ve yeniden hesapla

    Returns:
        Zorluk sınıflandırma sonucu (seviye, skor, görsel gösterge)
    """
    try:
        service = DifficultyClassificationService(db)
        classification = service.classify_question(
            question_id, force_recalculate=force_recalculate
        )

        # Görsel gösterge bilgisi ekle
        visual_indicator = service.get_visual_difficulty_indicator(
            classification.difficulty_level
        )

        return DifficultyClassificationResponse(
            question_id=classification.question_id,
            difficulty_level=classification.difficulty_level.value,
            difficulty_score=classification.difficulty_score,
            classification_method=classification.classification_method,
            confidence=classification.confidence,
            irt_based_difficulty=classification.irt_based_difficulty,
            performance_based_difficulty=classification.performance_based_difficulty,
            visual_indicator=visual_indicator,
            metadata=classification.metadata,
        )

    except Exception as e:
        logger.error(f"Error classifying question {question_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visual-indicator/{level}")
async def get_visual_indicator(level: str):
    """
    Zorluk seviyesi için görsel gösterge bilgisi al

    - **level**: Zorluk seviyesi (very_easy, easy, medium, hard, very_hard)

    Returns:
        Görsel gösterge bilgileri (renk, ikon, emoji, CSS class)
    """
    try:
        # String'i enum'a çevir
        level_map = {
            "very_easy": DifficultyLevel.VERY_EASY,
            "easy": DifficultyLevel.EASY,
            "medium": DifficultyLevel.MEDIUM,
            "hard": DifficultyLevel.HARD,
            "very_hard": DifficultyLevel.VERY_HARD,
        }

        difficulty_level = level_map.get(level.lower())
        if not difficulty_level:
            raise HTTPException(
                status_code=400, detail=f"Invalid difficulty level: {level}"
            )

        service = DifficultyClassificationService(None)
        indicator = service.get_visual_difficulty_indicator(difficulty_level)

        return indicator

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting visual indicator for {level}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/filter")
async def filter_questions_by_difficulty(
    request: FilterRequest, db: Session = Depends(get_db)
):
    """
    Zorluk seviyesine göre soruları filtrele

    - **difficulty_levels**: İstenen zorluk seviyeleri
    - **topic_id**: Opsiyonel konu filtresi
    - **limit**: Maksimum sonuç sayısı

    Returns:
        Filtrelenmiş soru ID listesi
    """
    try:
        # String'leri enum'a çevir
        level_map = {
            "very_easy": DifficultyLevel.VERY_EASY,
            "easy": DifficultyLevel.EASY,
            "medium": DifficultyLevel.MEDIUM,
            "hard": DifficultyLevel.HARD,
            "very_hard": DifficultyLevel.VERY_HARD,
        }

        difficulty_levels = []
        for level_str in request.difficulty_levels:
            level = level_map.get(level_str.lower())
            if level:
                difficulty_levels.append(level)

        if not difficulty_levels:
            raise HTTPException(
                status_code=400, detail="No valid difficulty levels provided"
            )

        service = DifficultyClassificationService(db)
        question_ids = service.filter_questions_by_difficulty(
            difficulty_levels=difficulty_levels,
            topic_id=request.topic_id,
            limit=request.limit,
        )

        return {
            "success": True,
            "question_ids": question_ids,
            "count": len(question_ids),
            "filters": {
                "difficulty_levels": request.difficulty_levels,
                "topic_id": request.topic_id,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error filtering questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/distribution")
async def get_difficulty_distribution(
    topic_id: Optional[str] = Query(None, description="Opsiyonel konu filtresi"),
    db: Session = Depends(get_db),
):
    """
    Zorluk seviyesi dağılımını al

    - **topic_id**: Opsiyonel konu filtresi

    Returns:
        Zorluk seviyesi dağılımı (her seviyede kaç soru var)
    """
    try:
        service = DifficultyClassificationService(db)
        distribution = service.get_difficulty_distribution(topic_id=topic_id)

        # Toplam soru sayısı
        total = sum(distribution.values())

        # Yüzdelik dağılım
        percentages = {}
        if total > 0:
            for level, count in distribution.items():
                percentages[level] = round((count / total) * 100, 1)

        return {
            "success": True,
            "distribution": distribution,
            "percentages": percentages,
            "total_questions": total,
            "topic_id": topic_id,
        }

    except Exception as e:
        logger.error(f"Error getting difficulty distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-realtime")
async def update_difficulty_realtime(
    request: RealtimeUpdateRequest, db: Session = Depends(get_db)
):
    """
    Yeni yanıt verisi geldiğinde zorluk seviyesini gerçek zamanlı güncelle

    - **question_id**: Soru ID
    - **new_response_data**: Yeni yanıt verisi

    Returns:
        Güncellenmiş zorluk sınıflandırması
    """
    try:
        service = DifficultyClassificationService(db)
        classification = service.update_difficulty_realtime(
            question_id=request.question_id, new_response_data=request.new_response_data
        )

        visual_indicator = service.get_visual_difficulty_indicator(
            classification.difficulty_level
        )

        return {
            "success": True,
            "classification": {
                "question_id": classification.question_id,
                "difficulty_level": classification.difficulty_level.value,
                "difficulty_score": classification.difficulty_score,
                "classification_method": classification.classification_method,
                "confidence": classification.confidence,
                "visual_indicator": visual_indicator,
                "metadata": classification.metadata,
            },
        }

    except Exception as e:
        logger.error(f"Error updating difficulty realtime: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-update")
async def batch_update_difficulties(
    request: BatchUpdateRequest, db: Session = Depends(get_db)
):
    """
    Toplu zorluk güncellemesi yap

    - **question_ids**: Güncellenecek soru ID listesi
    - **update_threshold_days**: Kaç günden eski güncellemeler yenilensin

    Returns:
        Güncellenen soru sayısı ve sonuçlar
    """
    try:
        service = DifficultyClassificationService(db)
        results = service.batch_update_difficulties(
            question_ids=request.question_ids,
            update_threshold_days=request.update_threshold_days,
        )

        # Sonuçları formatla
        formatted_results = {}
        for question_id, classification in results.items():
            formatted_results[question_id] = {
                "difficulty_level": classification.difficulty_level.value,
                "difficulty_score": classification.difficulty_score,
                "classification_method": classification.classification_method,
                "confidence": classification.confidence,
            }

        return {
            "success": True,
            "updated_count": len(results),
            "total_requested": len(request.question_ids),
            "results": formatted_results,
        }

    except Exception as e:
        logger.error(f"Error batch updating difficulties: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend/{question_id}")
async def get_difficulty_trend(
    question_id: str,
    recent_days: int = Query(30, ge=7, le=90, description="Son kaç günlük veri"),
    historical_days: int = Query(
        90, ge=30, le=365, description="Toplam kaç günlük geçmiş"
    ),
    db: Session = Depends(get_db),
):
    """
    Soru için zorluk trendi analizi

    - **question_id**: Soru ID
    - **recent_days**: Son kaç günlük veri kullanılacak
    - **historical_days**: Toplam kaç günlük geçmiş kullanılacak

    Returns:
        Zorluk trendi analizi (yükseliyor/düşüyor/stabil)
    """
    try:
        service = DifficultyClassificationService(db)
        trend = service.analyze_difficulty_trend(
            question_id=question_id,
            recent_days=recent_days,
            historical_days=historical_days,
        )

        # Başarı oranı analizi ekle
        success_analysis = service.get_success_rate_analysis(
            question_id=question_id, time_window_days=historical_days
        )

        return {
            "success": True,
            "question_id": question_id,
            "trend": trend,
            "success_analysis": success_analysis,
        }

    except Exception as e:
        logger.error(f"Error getting difficulty trend for {question_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calibrate-thresholds")
async def calibrate_irt_thresholds(
    topic_id: Optional[str] = Query(
        None, description="Belirli bir konu için kalibre et"
    ),
    db: Session = Depends(get_db),
):
    """
    IRT eşiklerini soru havuzuna göre kalibre et

    - **topic_id**: Opsiyonel konu filtresi

    Returns:
        Kalibre edilmiş eşik değerleri
    """
    try:
        from models.question_bank import QuestionBankItem

        # Soruları al
        query = db.query(QuestionBankItem).filter(QuestionBankItem.is_active == True)

        if topic_id:
            query = query.filter(QuestionBankItem.primary_topic_id == topic_id)

        questions = query.all()

        # Veriyi hazırla
        questions_data = [
            {"irt_difficulty": q.irt_difficulty}
            for q in questions
            if q.irt_difficulty is not None
        ]

        if not questions_data:
            raise HTTPException(
                status_code=404, detail="No questions with IRT data found"
            )

        service = DifficultyClassificationService(db)
        thresholds = service.calibrate_thresholds(questions_data)

        return {
            "success": True,
            "thresholds": {
                "very_easy_max": thresholds.very_easy_max,
                "easy_max": thresholds.easy_max,
                "medium_max": thresholds.medium_max,
                "hard_max": thresholds.hard_max,
            },
            "sample_size": len(questions_data),
            "topic_id": topic_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calibrating thresholds: {e}")
        raise HTTPException(status_code=500, detail=str(e))
