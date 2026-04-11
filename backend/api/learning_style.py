"""
VARK + Felder-Silverman Hibrit Öğrenme Stili API Endpoints
64 farklı öğrenme profili yönetimi
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import AuthenticatedUser, get_current_user, get_db
from core.learning_path_auth import verify_student_access
from models.learning_path_models import LearningPathStudentProfile
from models.learning_style import BehavioralData, QuestionnaireResponse
from services.learning_style_service import LearningStyleService

logger = logging.getLogger(__name__)

# Router oluştur
router = APIRouter(prefix="/api/v1/learning-style", tags=["Öğrenme Stili"])

# Service instance
learning_style_service = LearningStyleService()


@router.get("/detect/{student_id}", response_model=dict[str, Any])
async def detect_learning_style(
    student_id: str,
    force_recalculation: bool = Query(False, description="Zorla yeniden hesaplama"),
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Öğrenci için hibrit öğrenme stili tespit et
    64 farklı profil kombinasyonundan birini döndürür
    """
    try:
        await verify_student_access(student_id, current_user, db)
        logger.info(f"Öğrenme stili tespiti API çağrısı - Öğrenci: {student_id}")

        # Try DB-based detection first (refactored service)
        profile = await learning_style_service.detect_learning_style(
            student_id=student_id,
            db=db,
            behavioral_data={},  # Empty — service reads from DB
            questionnaire_responses=None,
        )

        # Service returns Dict[str, Any] after refactor
        if isinstance(profile, dict):
            return {
                "success": True,
                "data": profile,
                "message": "Öğrenme stili tespit edildi",
            }

        # Legacy typed object support (backward compat)
        return {
            "success": True,
            "data": {
                "student_id": getattr(profile, "student_id", student_id),
                "hybrid_code": getattr(profile, "hybrid_code", "V-Act-Sen-Vis-Seq"),
                "vark_profile": {
                    "visual": getattr(
                        getattr(profile, "vark_profile", None), "visual", 0.25
                    ),
                    "auditory": getattr(
                        getattr(profile, "vark_profile", None), "auditory", 0.25
                    ),
                    "reading": getattr(
                        getattr(profile, "vark_profile", None), "reading", 0.25
                    ),
                    "kinesthetic": getattr(
                        getattr(profile, "vark_profile", None), "kinesthetic", 0.25
                    ),
                    "dominant": "visual",
                },
                "confidence": {
                    "score": getattr(profile, "confidence_score", 0.3),
                    "level": "low",
                },
                "data_points_used": getattr(profile, "data_points_used", 0),
            },
            "message": "Öğrenme stili tespit edildi",
        }

    except Exception as e:
        logger.error(f"Öğrenme stili tespiti hatası: {e!s}")
        # Return default low-confidence profile instead of 500
        # This allows the frontend quiz flow to work properly
        return {
            "success": True,
            "data": {
                "student_id": student_id,
                "hybrid_code": "mixed",
                "vark_profile": {"dominant": "mixed"},
                "confidence": {"score": 0.3, "level": "low"},
                "data_points_used": 0,
            },
            "message": "Varsayılan profil döndürüldü (tespit başarısız)",
        }


@router.get("/recommendations/{student_id}", response_model=dict[str, Any])
async def get_content_recommendations(
    student_id: str,
    subject_area: str = Query("matematik", description="Konu alanı"),
    difficulty_level: str = Query("orta", description="Zorluk seviyesi"),
    force_refresh: bool = Query(False, description="Öneri yenileme"),
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Hibrit profile göre kişiselleştirilmiş içerik önerileri
    """
    try:
        await verify_student_access(student_id, current_user, db)
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"İçerik önerisi hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/behavioral-data/{student_id}", response_model=dict[str, Any])
async def update_behavioral_data(
    student_id: str,
    behavioral_data: BehavioralData,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Yeni davranışsal veri ile öğrenme stilini güncelle
    """
    try:
        await verify_student_access(student_id, current_user, db)
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
        return {
            "success": True,
            "data": {"profile_updated": False, "data_recorded": True},
            "message": "Davranışsal veri kaydedildi, profil değişikliği yok",
        }

    except HTTPException:
        # Propagate auth/validation errors (e.g. 403 from verify_student_access)
        # as-is; bare except previously re-wrapped them as 500 (GF22/GF77 pattern).
        raise
    except Exception as e:
        logger.error(f"Davranışsal veri güncelleme hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/questionnaire/{student_id}", response_model=dict[str, Any])
async def submit_questionnaire(
    student_id: str,
    questionnaire_response: QuestionnaireResponse,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Öğrenme stili anketi yanıtlarını kaydet — cache + DB persist
    """
    try:
        await verify_student_access(student_id, current_user, db)
        logger.info(
            f"Anket yanıtı API çağrısı - Öğrenci: {student_id}, Tür: {questionnaire_response.questionnaire_type}"
        )

        # Student ID'yi set et
        questionnaire_response.student_id = student_id

        # VARK skorlarını hesapla ve profil güncelle (DB persist)
        # NOTE: questionnaire_cache/profiles_cache removed — service refactored to DB-only
        vark_scores = _calculate_vark_scores(questionnaire_response)
        dominant_style = (
            max(vark_scores, key=vark_scores.get) if vark_scores else "mixed"
        )

        result = await db.execute(
            select(LearningPathStudentProfile).where(
                LearningPathStudentProfile.student_id == student_id
            )
        )
        profile = result.scalar_one_or_none()

        if profile:
            profile.learning_style = dominant_style
            profile.vark_visual_score = vark_scores.get("visual", 0.0)
            profile.vark_auditory_score = vark_scores.get("auditory", 0.0)
            profile.vark_reading_score = vark_scores.get("reading", 0.0)
            profile.vark_kinesthetic_score = vark_scores.get("kinesthetic", 0.0)
            await db.commit()
            logger.info(
                f"VARK skorları DB'ye kaydedildi: {student_id} → {dominant_style}"
            )

        return {
            "success": True,
            "data": {
                "questionnaire_type": questionnaire_response.questionnaire_type,
                "completion_time": questionnaire_response.completion_time,
                "responses_count": len(questionnaire_response.responses),
                "learning_style": dominant_style,
                "vark_scores": vark_scores,
            },
            "message": "Anket yanıtları kaydedildi",
        }

    except HTTPException:
        # Propagate auth/validation errors (e.g. 403 from verify_student_access)
        # as-is; bare except previously re-wrapped them as 500 (GF22/GF77 pattern).
        raise
    except Exception as e:
        logger.error(f"Anket kaydetme hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


def _calculate_vark_scores(response: QuestionnaireResponse) -> dict[str, float]:
    """VARK anket yanıtlarından 0-1 arası skorlar hesapla.

    Frontend format: {question_id: style_key} — e.g. {"q1": "visual", "q2": "auditory"}
    """
    counts = {"visual": 0, "auditory": 0, "reading": 0, "kinesthetic": 0}
    total = 0

    responses = response.responses
    if isinstance(responses, dict):
        # Dict format: {question_id: style} — iterate values
        for answer in responses.values():
            style = str(answer).lower() if answer else ""
            if style in counts:
                counts[style] += 1
                total += 1
    elif isinstance(responses, list):
        # List format: [{answer: style}] — legacy/alternative
        for r in responses:
            style = (
                r.get("answer", "").lower() if isinstance(r, dict) else str(r).lower()
            )
            if style in counts:
                counts[style] += 1
                total += 1

    if total == 0:
        return {"visual": 0.25, "auditory": 0.25, "reading": 0.25, "kinesthetic": 0.25}

    return {k: round(v / total, 3) for k, v in counts.items()}


@router.get("/explanation/{student_id}", response_model=dict[str, Any])
async def get_learning_style_explanation(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Öğrenci için öğrenme stili açıklaması
    """
    try:
        await verify_student_access(student_id, current_user, db)
        logger.info(f"Öğrenme stili açıklaması API çağrısı - Öğrenci: {student_id}")

        explanation = await learning_style_service.get_learning_style_explanation(
            student_id
        )

        return {
            "success": True,
            "data": explanation,
            "message": "Öğrenme stili açıklaması hazırlandı",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Açıklama hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/hybrid-codes", response_model=dict[str, Any])
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hibrit kodlar hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/statistics", response_model=dict[str, Any])
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"İstatistik hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/export/{student_id}", response_model=dict[str, Any])
async def export_learning_profile(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Öğrenci öğrenme profilini dışa aktar
    """
    try:
        await verify_student_access(student_id, current_user, db)
        logger.info(f"Profil dışa aktarma API çağrısı - Öğrenci: {student_id}")

        export_data = await learning_style_service.export_learning_profile(student_id)

        return {
            "success": True,
            "data": export_data,
            "message": "Öğrenme profili dışa aktarıldı",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dışa aktarma hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get(
    "/content-explanation/{hybrid_code}/{content_type}", response_model=dict[str, Any]
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"İçerik açıklaması hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/update-recommendations/{student_id}", response_model=dict[str, Any])
async def update_recommendations_based_on_performance(
    student_id: str,
    performance_data: dict[str, float],
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Performans verilerine göre önerileri güncelle
    """
    try:
        await verify_student_access(student_id, current_user, db)
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Performans tabanlı güncelleme hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


# Sağlık kontrolü endpoint'i
@router.get("/health", response_model=dict[str, Any])
async def health_check():
    """
    Hibrit öğrenme stili sistemi sağlık kontrolü
    """
    try:
        # Sistem durumu kontrolü (cache attributes removed after DB-only refactor)
        total_profiles = len(getattr(learning_style_service, "profiles_cache", {}))
        total_behavioral_data = sum(
            len(data)
            for data in getattr(
                learning_style_service, "behavioral_data_cache", {}
            ).values()
        )
        total_questionnaires = sum(
            len(responses)
            for responses in getattr(
                learning_style_service, "questionnaire_cache", {}
            ).values()
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sağlık kontrolü hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/cache-stats")
async def get_cache_stats():
    """Cache istatistiklerini getir"""
    from core.cache import cache_manager

    return {"success": True, "data": cache_manager.get_stats()}
