"""
Hızlı Öğrenme Stili API
Performans optimizasyonu için minimal endpoints
"""
import logging

from fastapi import APIRouter, HTTPException

from services.fast_learning_service import FastLearningStyleService

logger = logging.getLogger(__name__)

# Router oluştur
router = APIRouter(prefix="/api/v1/fast-learning", tags=["Hızlı Öğrenme Stili"])

# Service instance
fast_service = FastLearningStyleService()


@router.get("/detect/{student_id}")
async def fast_detect_learning_style(student_id: str):
    """Hızlı öğrenme stili tespiti"""
    try:
        profile = await fast_service.detect_learning_style(student_id)

        return {
            "success": True,
            "data": {
                "student_id": profile.student_id,
                "hybrid_code": profile.hybrid_code,
                "confidence_score": profile.confidence_score,
                "vark_dominant": profile.vark_profile.dominant_vark.value,
            },
            "message": f"Hızlı profil tespit edildi: {profile.hybrid_code}",
            "mode": "fast",
        }

    except Exception as e:
        logger.error(f"Hızlı tespit hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Hızlı tespit başarısız: {str(e)}")


@router.get("/recommendations/{student_id}")
async def fast_get_recommendations(student_id: str):
    """Hızlı içerik önerileri"""
    try:
        recommendation = await fast_service.generate_content_recommendations(student_id)

        return {
            "success": True,
            "data": {
                "student_id": recommendation.student_id,
                "hybrid_code": recommendation.hybrid_code,
                "recommended_content_types": recommendation.recommended_content_types,
                "learning_strategies": recommendation.learning_strategies,
            },
            "message": "Hızlı öneriler hazırlandı",
            "mode": "fast",
        }

    except Exception as e:
        logger.error(f"Hızlı öneri hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Hızlı öneriler başarısız: {str(e)}"
        )


@router.get("/explanation/{student_id}")
async def fast_get_explanation(student_id: str):
    """Hızlı açıklama"""
    try:
        explanation = await fast_service.get_learning_style_explanation(student_id)

        return {
            "success": True,
            "data": explanation,
            "message": "Hızlı açıklama hazırlandı",
            "mode": "fast",
        }

    except Exception as e:
        logger.error(f"Hızlı açıklama hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Hızlı açıklama başarısız: {str(e)}"
        )


@router.get("/health")
async def fast_health_check():
    """Hızlı sağlık kontrolü"""
    return {
        "success": True,
        "status": "healthy",
        "mode": "fast",
        "message": "Hızlı öğrenme stili sistemi çalışıyor",
        "features": ["fast_detection", "simple_recommendations", "minimal_processing"],
    }
