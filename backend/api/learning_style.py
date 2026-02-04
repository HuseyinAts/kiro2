"""
VARK + Felder-Silverman Hibrit Öğrenme Stili API Endpoints
64 farklı öğrenme profili yönetimi
"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from models.learning_style import BehavioralData, QuestionnaireResponse
from services.learning_style_service import LearningStyleService

logger = logging.getLogger(__name__)

# Router oluştur
router = APIRouter(prefix="/api/v1/learning-style", tags=["Öğrenme Stili"])

# Service instance
learning_style_service = LearningStyleService()


@router.get("/detect/{student_id}", response_model=Dict[str, Any])
async def detect_learning_style(
    student_id: str,
    force_recalculation: bool = Query(False, description="Zorla yeniden hesaplama"),
):
    """
    Öğrenci için hibrit öğrenme stili tespit et
    64 farklı profil kombinasyonundan birini döndürür
    """
    try:
        logger.info(f"Öğrenme stili tespiti API çağrısı - Öğrenci: {student_id}")

        profile = await learning_style_service.detect_learning_style(
            student_id=student_id, force_recalculation=force_recalculation
        )

        return {
            "success": True,
            "data": {
                "student_id": profile.student_id,
                "hybrid_code": profile.hybrid_code,
                "vark_profile": {
                    "visual": profile.vark_profile.visual,
                    "auditory": profile.vark_profile.auditory,
                    "reading": profile.vark_profile.reading,
                    "kinesthetic": profile.vark_profile.kinesthetic,
                    "dominant": profile.vark_profile.dominant_vark.value,
                },
                "felder_profile": {
                    "active_reflective": profile.felder_profile.active_reflective,
                    "sensing_intuitive": profile.felder_profile.sensing_intuitive,
                    "visual_verbal": profile.felder_profile.visual_verbal,
                    "sequential_global": profile.felder_profile.sequential_global,
                    "preferences": profile.felder_profile.learning_preferences,
                },
                "confidence": {
                    "score": profile.confidence_score,
                    "level": profile.confidence_level.value,
                },
                "data_points_used": profile.data_points_used,
                "detection_date": profile.detection_date.isoformat(),
                "last_updated": profile.last_updated.isoformat(),
            },
            "message": f"Hibrit öğrenme stili tespit edildi: {profile.hybrid_code}",
        }

    except Exception as e:
        logger.error(f"Öğrenme stili tespiti hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Öğrenme stili tespit edilemedi: {str(e)}"
        )


@router.get("/recommendations/{student_id}", response_model=Dict[str, Any])
async def get_content_recommendations(
    student_id: str,
    subject_area: str = Query("matematik", description="Konu alanı"),
    difficulty_level: str = Query("orta", description="Zorluk seviyesi"),
    force_refresh: bool = Query(False, description="Öneri yenileme"),
):
    """
    Hibrit profile göre kişiselleştirilmiş içerik önerileri
    """
    try:
        logger.info(
            f"İçerik önerisi API çağrısı - Öğrenci: {student_id}, Konu: {subject_area}"
        )

        recommendation = await learning_style_service.generate_content_recommendations(
            student_id=student_id,
            subject_area=subject_area,
            difficulty_level=difficulty_level,
            force_refresh=force_refresh,
        )

        return {
            "success": True,
            "data": {
                "student_id": recommendation.student_id,
                "hybrid_code": recommendation.hybrid_code,
                "subject_area": subject_area,
                "difficulty_level": difficulty_level,
                "recommended_content_types": recommendation.recommended_content_types,
                "content_weights": recommendation.content_weights,
                "learning_strategies": recommendation.learning_strategies,
                "study_techniques": recommendation.study_techniques,
                "adjustments": {
                    "difficulty": recommendation.difficulty_adjustment,
                    "pace": recommendation.pace_adjustment,
                },
                "confidence_score": recommendation.confidence_score,
                "generated_at": recommendation.generated_at.isoformat(),
            },
            "message": f"{len(recommendation.recommended_content_types)} içerik türü önerildi",
        }

    except Exception as e:
        logger.error(f"İçerik önerisi hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"İçerik önerisi oluşturulamadı: {str(e)}"
        )


@router.post("/behavioral-data/{student_id}", response_model=Dict[str, Any])
async def update_behavioral_data(student_id: str, behavioral_data: BehavioralData):
    """
    Yeni davranışsal veri ile öğrenme stilini güncelle
    """
    try:
        logger.info(f"Davranışsal veri güncelleme API çağrısı - Öğrenci: {student_id}")

        # Student ID'yi data'ya set et
        behavioral_data.student_id = student_id

        updated_profile = await learning_style_service.update_behavioral_data(
            student_id=student_id, new_data=behavioral_data
        )

        if updated_profile:
            return {
                "success": True,
                "data": {
                    "profile_updated": True,
                    "new_hybrid_code": updated_profile.hybrid_code,
                    "confidence_score": updated_profile.confidence_score,
                    "last_updated": updated_profile.last_updated.isoformat(),
                },
                "message": "Öğrenme stili güncellendi",
            }
        else:
            return {
                "success": True,
                "data": {"profile_updated": False, "data_recorded": True},
                "message": "Davranışsal veri kaydedildi, profil değişikliği yok",
            }

    except Exception as e:
        logger.error(f"Davranışsal veri güncelleme hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Davranışsal veri güncellenemedi: {str(e)}"
        )


@router.post("/questionnaire/{student_id}", response_model=Dict[str, Any])
async def submit_questionnaire(
    student_id: str, questionnaire_response: QuestionnaireResponse
):
    """
    Öğrenme stili anketi yanıtlarını kaydet
    """
    try:
        logger.info(
            f"Anket yanıtı API çağrısı - Öğrenci: {student_id}, Tür: {questionnaire_response.questionnaire_type}"
        )

        # Student ID'yi set et
        questionnaire_response.student_id = student_id

        # Anket yanıtını cache'e kaydet (gerçek implementasyonda database'e kaydedilecek)
        if student_id not in learning_style_service.questionnaire_cache:
            learning_style_service.questionnaire_cache[student_id] = []

        learning_style_service.questionnaire_cache[student_id].append(
            questionnaire_response
        )

        # Profil cache'ini temizle (yeniden hesaplama için)
        if student_id in learning_style_service.profiles_cache:
            del learning_style_service.profiles_cache[student_id]

        return {
            "success": True,
            "data": {
                "questionnaire_type": questionnaire_response.questionnaire_type,
                "completion_time": questionnaire_response.completion_time,
                "responses_count": len(questionnaire_response.responses),
            },
            "message": "Anket yanıtları kaydedildi",
        }

    except Exception as e:
        logger.error(f"Anket kaydetme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Anket kaydedilemedi: {str(e)}")


@router.get("/explanation/{student_id}", response_model=Dict[str, Any])
async def get_learning_style_explanation(student_id: str):
    """
    Öğrenci için öğrenme stili açıklaması
    """
    try:
        logger.info(f"Öğrenme stili açıklaması API çağrısı - Öğrenci: {student_id}")

        explanation = await learning_style_service.get_learning_style_explanation(
            student_id
        )

        return {
            "success": True,
            "data": explanation,
            "message": "Öğrenme stili açıklaması hazırlandı",
        }

    except Exception as e:
        logger.error(f"Açıklama hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Açıklama oluşturulamadı: {str(e)}"
        )


@router.get("/hybrid-codes", response_model=Dict[str, Any])
async def get_all_hybrid_codes():
    """
    Tüm 64 hibrit kod ve açıklamalarını döndür
    """
    try:
        logger.info("Tüm hibrit kodlar API çağrısı")

        hybrid_codes = await learning_style_service.get_all_hybrid_codes()

        return {
            "success": True,
            "data": {
                "total_combinations": len(hybrid_codes),
                "hybrid_codes": hybrid_codes,
            },
            "message": f"{len(hybrid_codes)} hibrit kod kombinasyonu",
        }

    except Exception as e:
        logger.error(f"Hibrit kodlar hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Hibrit kodlar alınamadı: {str(e)}"
        )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_learning_style_statistics():
    """
    Öğrenme stili istatistikleri
    """
    try:
        logger.info("Öğrenme stili istatistikleri API çağrısı")

        statistics = await learning_style_service.get_learning_style_statistics()

        return {
            "success": True,
            "data": statistics,
            "message": "İstatistikler hazırlandı",
        }

    except Exception as e:
        logger.error(f"İstatistik hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"İstatistikler alınamadı: {str(e)}"
        )


@router.get("/export/{student_id}", response_model=Dict[str, Any])
async def export_learning_profile(student_id: str):
    """
    Öğrenci öğrenme profilini dışa aktar
    """
    try:
        logger.info(f"Profil dışa aktarma API çağrısı - Öğrenci: {student_id}")

        export_data = await learning_style_service.export_learning_profile(student_id)

        return {
            "success": True,
            "data": export_data,
            "message": "Öğrenme profili dışa aktarıldı",
        }

    except Exception as e:
        logger.error(f"Dışa aktarma hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Profil dışa aktarılamadı: {str(e)}"
        )


@router.get(
    "/content-explanation/{hybrid_code}/{content_type}", response_model=Dict[str, Any]
)
async def get_content_explanation(hybrid_code: str, content_type: str):
    """
    Belirli hibrit kod ve içerik türü için açıklama
    """
    try:
        logger.info(
            f"İçerik açıklaması API çağrısı - Kod: {hybrid_code}, Tür: {content_type}"
        )

        explanation = await learning_style_service.recommender.get_content_explanation(
            hybrid_code=hybrid_code, content_type=content_type
        )

        return {
            "success": True,
            "data": {
                "hybrid_code": hybrid_code,
                "content_type": content_type,
                "explanation": explanation,
            },
            "message": "İçerik açıklaması hazırlandı",
        }

    except Exception as e:
        logger.error(f"İçerik açıklaması hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Açıklama oluşturulamadı: {str(e)}"
        )


@router.post("/update-recommendations/{student_id}", response_model=Dict[str, Any])
async def update_recommendations_based_on_performance(
    student_id: str, performance_data: Dict[str, float]
):
    """
    Performans verilerine göre önerileri güncelle
    """
    try:
        logger.info(
            f"Performans tabanlı öneri güncelleme API çağrısı - Öğrenci: {student_id}"
        )

        # Mevcut öneriyi al
        current_recommendation = (
            await learning_style_service.generate_content_recommendations(student_id)
        )

        # Performans tabanlı güncelleme
        updated_recommendation = await learning_style_service.recommender.update_recommendations_based_on_performance(
            student_id=student_id,
            current_recommendation=current_recommendation,
            performance_data=performance_data,
        )

        # Cache'i güncelle
        cache_key = f"{student_id}_matematik_orta"  # Varsayılan değerler
        learning_style_service.recommendations_cache[cache_key] = updated_recommendation

        return {
            "success": True,
            "data": {
                "student_id": updated_recommendation.student_id,
                "updated_content_types": updated_recommendation.recommended_content_types,
                "difficulty_adjustment": updated_recommendation.difficulty_adjustment,
                "pace_adjustment": updated_recommendation.pace_adjustment,
                "updated_at": updated_recommendation.generated_at.isoformat(),
            },
            "message": "Öneriler performans verilerine göre güncellendi",
        }

    except Exception as e:
        logger.error(f"Performans tabanlı güncelleme hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Öneriler güncellenemedi: {str(e)}"
        )


# Sağlık kontrolü endpoint'i
@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    Hibrit öğrenme stili sistemi sağlık kontrolü
    """
    try:
        # Sistem durumu kontrolü
        total_profiles = len(learning_style_service.profiles_cache)
        total_behavioral_data = sum(
            len(data) for data in learning_style_service.behavioral_data_cache.values()
        )
        total_questionnaires = sum(
            len(responses)
            for responses in learning_style_service.questionnaire_cache.values()
        )

        return {
            "success": True,
            "data": {
                "system_status": "healthy",
                "total_profiles": total_profiles,
                "total_behavioral_data_points": total_behavioral_data,
                "total_questionnaire_responses": total_questionnaires,
                "available_hybrid_combinations": 64,
                "detector_status": "active",
                "recommender_status": "active",
            },
            "message": "Hibrit öğrenme stili sistemi çalışıyor",
        }

    except Exception as e:
        logger.error(f"Sağlık kontrolü hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Sistem sağlık kontrolü başarısız: {str(e)}"
        )


@router.get("/cache-stats")
async def get_cache_stats():
    """Cache istatistiklerini getir"""
    from core.cache import cache_manager

    return {"success": True, "data": cache_manager.get_stats()}
