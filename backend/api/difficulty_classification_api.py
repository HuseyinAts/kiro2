"""
Zorluk Seviyesi Sınıflandırma API
Task 74: Difficulty Level Classification API Endpoints

Session 149 (GF112): `DifficultyClassificationService` is a ~700-line sync ORM
service that cannot be refactored in a single session. The `core.database.get_db`
dependency is a sync shim over an async engine, so `db.query(...)` inside the
service trips `MissingGreenlet` (same class as Wave 10/11 GF86/GF87/GF95 and
Wave 13 GF115). Until the service is ported to async, all 8 handlers use the
`_degrade_db_error()` helper to catch DBAPI / MissingGreenlet / AttributeError
and return a structured 503, matching the GF22/GF41/GF106 optional-dep
degradation pattern.

API Endpoints:
- GET /api/v1/difficulty/classify/{question_id}
- GET /api/v1/difficulty/visual-indicator/{level}
- POST /api/v1/difficulty/filter
- GET /api/v1/difficulty/distribution
- POST /api/v1/difficulty/update-realtime
- POST /api/v1/difficulty/batch-update
- GET /api/v1/difficulty/trend/{question_id}
- GET /api/v1/difficulty/calibrate-thresholds
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import AuthenticatedUser, get_current_admin_user
from services.difficulty_classification_service import (
    DifficultyClassificationService,
    DifficultyLevel,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/difficulty", tags=["Difficulty Classification"])


_DEGRADE_MSG = (
    "Zorluk siniflandirma servisi gecici olarak kullanilamiyor: "
    "veritabani katmani yeniden yapilandiriliyor."
)


def _degrade_db_error(exc: Exception, context: str) -> HTTPException:
    """Convert async/sync mismatch or DB errors to structured 503.

    The sync `DifficultyClassificationService` calls sync ORM against an
    async engine, which raises:
      - sqlalchemy.exc.MissingGreenlet (wrapped in DBAPIError)
      - AttributeError on AsyncSession.query
      - Any SQLAlchemyError subclass

    Matches GF22/GF41/GF106 structured degradation pattern.
    """
    logger.error(f"{context}: {type(exc).__name__}: {exc}")
    return HTTPException(status_code=503, detail=_DEGRADE_MSG)


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
    irt_based_difficulty: float | None = None
    performance_based_difficulty: float | None = None
    visual_indicator: dict
    metadata: dict = {}


class FilterRequest(BaseModel):
    """Zorluk filtreleme isteği"""

    difficulty_levels: list[str] = Field(
        ..., description="Zorluk seviyeleri: very_easy, easy, medium, hard, very_hard"
    )
    topic_id: str | None = None
    limit: int = Field(50, ge=1, le=200)


class BatchUpdateRequest(BaseModel):
    """Toplu güncelleme isteği"""

    question_ids: list[str]
    update_threshold_days: int = Field(7, ge=1, le=365)


class RealtimeUpdateRequest(BaseModel):
    """Gerçek zamanlı güncelleme isteği"""

    question_id: str
    new_response_data: dict


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/classify/{question_id}", response_model=DifficultyClassificationResponse)
def classify_question_difficulty(
    question_id: str,
    force_recalculate: bool = Query(
        False, description="Cache'i atla ve yeniden hesapla"
    ),
    db: Session = Depends(get_db),
):
    """Soruyu 5 seviyeli zorluk ölçeğinde sınıflandır."""
    try:
        service = DifficultyClassificationService(db)
        classification = service.classify_question(
            question_id, force_recalculate=force_recalculate
        )

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

    except HTTPException:
        raise
    except (DBAPIError, SQLAlchemyError, AttributeError) as e:
        raise _degrade_db_error(e, f"classify_question_difficulty({question_id})")
    except Exception as e:
        logger.error(f"Error classifying question {question_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/visual-indicator/{level}")
def get_visual_indicator(level: str):
    """Zorluk seviyesi için görsel gösterge bilgisi al."""
    try:
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
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/filter")
def filter_questions_by_difficulty(
    request: FilterRequest, db: Session = Depends(get_db)
):
    """Zorluk seviyesine göre soruları filtrele."""
    try:
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
    except (DBAPIError, SQLAlchemyError, AttributeError) as e:
        raise _degrade_db_error(e, "filter_questions_by_difficulty")
    except Exception as e:
        logger.error(f"Error filtering questions: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/distribution")
def get_difficulty_distribution(
    topic_id: str | None = Query(None, description="Opsiyonel konu filtresi"),
    db: Session = Depends(get_db),
):
    """Zorluk seviyesi dağılımını al."""
    try:
        service = DifficultyClassificationService(db)
        distribution = service.get_difficulty_distribution(topic_id=topic_id)

        total = sum(distribution.values())

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

    except HTTPException:
        raise
    except (DBAPIError, SQLAlchemyError, AttributeError) as e:
        raise _degrade_db_error(e, "get_difficulty_distribution")
    except Exception as e:
        logger.error(f"Error getting difficulty distribution: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/update-realtime")
def update_difficulty_realtime(
    request: RealtimeUpdateRequest,
    _admin: AuthenticatedUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Yeni yanıt verisi geldiğinde zorluk seviyesini gerçek zamanlı güncelle."""
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

    except HTTPException:
        raise
    except (DBAPIError, SQLAlchemyError, AttributeError) as e:
        raise _degrade_db_error(e, "update_difficulty_realtime")
    except Exception as e:
        logger.error(f"Error updating difficulty realtime: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/batch-update")
def batch_update_difficulties(
    request: BatchUpdateRequest,
    _admin: AuthenticatedUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Toplu zorluk güncellemesi yap."""
    try:
        service = DifficultyClassificationService(db)
        results = service.batch_update_difficulties(
            question_ids=request.question_ids,
            update_threshold_days=request.update_threshold_days,
        )

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

    except HTTPException:
        raise
    except (DBAPIError, SQLAlchemyError, AttributeError) as e:
        raise _degrade_db_error(e, "batch_update_difficulties")
    except Exception as e:
        logger.error(f"Error batch updating difficulties: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/trend/{question_id}")
def get_difficulty_trend(
    question_id: str,
    recent_days: int = Query(30, ge=7, le=90, description="Son kaç günlük veri"),
    historical_days: int = Query(
        90, ge=30, le=365, description="Toplam kaç günlük geçmiş"
    ),
    db: Session = Depends(get_db),
):
    """Soru için zorluk trendi analizi."""
    try:
        service = DifficultyClassificationService(db)
        trend = service.analyze_difficulty_trend(
            question_id=question_id,
            recent_days=recent_days,
            historical_days=historical_days,
        )

        success_analysis = service.get_success_rate_analysis(
            question_id=question_id, time_window_days=historical_days
        )

        return {
            "success": True,
            "question_id": question_id,
            "trend": trend,
            "success_analysis": success_analysis,
        }

    except HTTPException:
        raise
    except (DBAPIError, SQLAlchemyError, AttributeError) as e:
        raise _degrade_db_error(e, f"get_difficulty_trend({question_id})")
    except Exception as e:
        logger.error(f"Error getting difficulty trend for {question_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/calibrate-thresholds")
def calibrate_irt_thresholds(
    topic_id: str | None = Query(None, description="Belirli bir konu için kalibre et"),
    db: Session = Depends(get_db),
):
    """IRT eşiklerini soru havuzuna göre kalibre et."""
    try:
        from models.question_bank import QuestionBankItem

        query = db.query(QuestionBankItem).filter(QuestionBankItem.is_active == True)

        if topic_id:
            query = query.filter(QuestionBankItem.primary_topic_id == topic_id)

        questions = query.all()

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
    except (DBAPIError, SQLAlchemyError, AttributeError) as e:
        raise _degrade_db_error(e, "calibrate_irt_thresholds")
    except Exception as e:
        logger.error(f"Error calibrating thresholds: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )
