"""
EBA TV API Router

TRT EBA TV içerik entegrasyonu için API endpoint'leri.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import JSONResponse

from core.dependencies import get_current_admin_user, get_current_user
from integrations.ebatv_service import (
    EBAContentCategory,
    EBAGradeLevel,
    EBAtvService,
    EBAVideoMetadata,
    get_ebatv_service,
)
from models.ebatv_content import (
    EBAContentModerationRequest,
    EBAContentModerationResponse,
    EBAContentRecommendationRequest,
    EBAContentRecommendationResponse,
    EBAContentStatistics,
    EBAVideoSearchResponse,
)

logger = logging.getLogger(__name__)

# Router oluştur
router = APIRouter(
    prefix="/api/v1/eba-tv",
    tags=["EBA TV"],
    responses={
        404: {"description": "İçerik bulunamadı"},
        500: {"description": "Sunucu hatası"},
    },
)


@router.get("/", summary="EBA TV Ana Sayfa")
async def eba_tv_home():
    """EBA TV API ana sayfa bilgileri"""

    return {
        "success": True,
        "message": "EBA TV İçerik Entegrasyonu API'si",
        "version": "1.0.0",
        "features": [
            "İçerik arama ve filtreleme",
            "Kalite analizi",
            "Müfredat uyumu",
            "Kişiselleştirilmiş öneriler",
            "İçerik moderasyonu",
            "Kullanım analitikleri",
        ],
        "endpoints": {
            "content": "/content",
            "search": "/search",
            "recommendations": "/recommendations",
            "statistics": "/statistics",
            "quality": "/quality",
            "moderation": "/moderation",
        },
    }


@router.get(
    "/content", summary="Tüm EBA TV İçeriklerini Getir", response_model=Dict[str, Any]
)
async def get_all_eba_content(
    force_refresh: bool = Query(False, description="Cache'i yenile"),
    ebatv_service: EBAtvService = Depends(get_ebatv_service),
):
    """
    Tüm EBA TV içeriklerini getir

    - **force_refresh**: Cache'i yenilemek için True
    """

    try:
        content_collection = await ebatv_service.get_all_content(
            force_refresh=force_refresh
        )

        return {
            "success": True,
            "data": {
                "total_videos": content_collection.total_count,
                "videos": [
                    {
                        "id": i,
                        "title": video.title,
                        "description": video.description,
                        "duration_minutes": video.duration_minutes,
                        "category": video.category.value,
                        "grade_level": video.grade_level.value,
                        "difficulty_level": video.difficulty_level.value,
                        "quality_score": video.quality_score,
                        "video_url": str(video.video_url),
                        "thumbnail_url": str(video.thumbnail_url)
                        if video.thumbnail_url
                        else None,
                        "subject_topics": video.subject_topics,
                        "accessibility_features": video.accessibility_features,
                        "curriculum_alignment": video.curriculum_alignment,
                        "created_date": video.created_date.isoformat(),
                        "last_updated": video.last_updated.isoformat(),
                    }
                    for i, video in enumerate(content_collection.videos)
                ],
                "categories": content_collection.categories,
                "grade_levels": content_collection.grade_levels,
                "quality_distribution": content_collection.quality_distribution,
                "last_updated": content_collection.last_updated.isoformat(),
            },
            "message": f"{content_collection.total_count} EBA TV videosu başarıyla getirildi",
        }

    except Exception as e:
        logger.error(f"EBA TV içerik getirme hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get(
    "/search", summary="EBA TV İçerik Arama", response_model=EBAVideoSearchResponse
)
async def search_eba_content(
    query: str = Query(..., min_length=1, max_length=100, description="Arama sorgusu"),
    grade_level: Optional[str] = Query(None, description="Sınıf seviyesi filtresi"),
    category: Optional[str] = Query(None, description="Kategori filtresi"),
    min_quality: float = Query(6.0, ge=0, le=10, description="Minimum kalite skoru"),
    max_duration: Optional[int] = Query(
        None, ge=1, le=180, description="Maksimum süre (dakika)"
    ),
    accessibility_required: bool = Query(
        False, description="Erişilebilirlik gerekli mi"
    ),
    ebatv_service: EBAtvService = Depends(get_ebatv_service),
):
    """
    EBA TV içeriklerinde arama yap

    - **query**: Arama sorgusu (zorunlu)
    - **grade_level**: Sınıf seviyesi filtresi (5-12)
    - **category**: Kategori filtresi
    - **min_quality**: Minimum kalite skoru (0-10)
    - **max_duration**: Maksimum video süresi (dakika)
    - **accessibility_required**: Erişilebilirlik özellikleri gerekli mi
    """

    try:
        start_time = datetime.now()

        # Enum dönüşümleri
        grade_enum = None
        if grade_level:
            try:
                grade_enum = EBAGradeLevel(grade_level)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Geçersiz sınıf seviyesi: {grade_level}"
                )

        category_enum = None
        if category:
            try:
                category_enum = EBAContentCategory(category)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Geçersiz kategori: {category}"
                )

        # Arama yap
        results = await ebatv_service.search_content(
            query=query,
            grade_level=grade_enum,
            category=category_enum,
            min_quality=min_quality,
        )

        # Süre filtresi uygula
        if max_duration:
            results = [
                video for video in results if video.duration_minutes <= max_duration
            ]

        # Erişilebilirlik filtresi uygula
        if accessibility_required:
            results = [
                video
                for video in results
                if video.accessibility_features
                and len(video.accessibility_features) > 0
            ]

        # Arama süresini hesapla
        search_time = (datetime.now() - start_time).total_seconds() * 1000

        # Yanıt oluştur
        response_videos = []
        for video in results:
            response_videos.append(
                EBAVideoMetadata(
                    title=video.title,
                    description=video.description,
                    duration_minutes=video.duration_minutes,
                    category=video.category,
                    grade_level=video.grade_level,
                    subject_topics=video.subject_topics,
                    difficulty_level=video.difficulty_level,
                    video_url=video.video_url,
                    thumbnail_url=video.thumbnail_url,
                    transcript=video.transcript,
                    quality_score=video.quality_score,
                    curriculum_alignment=video.curriculum_alignment,
                    accessibility_features=video.accessibility_features,
                    created_date=video.created_date,
                    last_updated=video.last_updated,
                )
            )

        return EBAVideoSearchResponse(
            videos=response_videos,
            total_results=len(results),
            search_query=query,
            filters_applied={
                "grade_level": grade_level,
                "category": category,
                "min_quality": min_quality,
                "max_duration": max_duration,
                "accessibility_required": accessibility_required,
            },
            search_time_ms=search_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"EBA TV arama hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post(
    "/recommendations",
    summary="Kişiselleştirilmiş EBA TV Önerileri",
    response_model=EBAContentRecommendationResponse,
)
async def get_eba_recommendations(
    request: EBAContentRecommendationRequest,
    current_user=Depends(get_current_user),
    ebatv_service: EBAtvService = Depends(get_ebatv_service),
):
    """
    Öğrenci profiline göre kişiselleştirilmiş EBA TV içerik önerileri

    - **student_id**: Öğrenci ID'si
    - **grade_level**: Öğrenci sınıf seviyesi
    - **weak_subjects**: Zayıf olunan konular
    - **learning_style**: Öğrenme stili
    - **max_recommendations**: Maksimum öneri sayısı
    """

    try:
        # Enum dönüşümleri
        grade_enum = EBAGradeLevel(request.grade_level)
        category_enums = [EBAContentCategory(cat) for cat in request.weak_subjects]

        # Önerileri getir
        recommendations = await ebatv_service.get_recommended_content(
            student_grade=grade_enum,
            weak_subjects=category_enums,
            learning_style=request.learning_style,
        )

        # Maksimum öneri sayısını uygula
        recommendations = recommendations[: request.max_recommendations]

        # Öneri nedenlerini oluştur
        recommendation_reasons = {}
        for i, video in enumerate(recommendations):
            reasons = []

            if video.category in category_enums:
                reasons.append(f"Zayıf konu: {video.category.value}")

            if request.learning_style == "visual" and video.duration_minutes <= 20:
                reasons.append("Görsel öğrenme stiline uygun kısa video")

            if video.quality_score >= 8.0:
                reasons.append("Yüksek kalite skoru")

            if video.curriculum_alignment.get("alignment_score", 0) > 0.7:
                reasons.append("Yüksek müfredat uyumu")

            recommendation_reasons[str(i)] = " | ".join(reasons)

        # Kişiselleştirme skorunu hesapla
        personalization_score = 0.0
        if recommendations:
            total_score = sum(
                video.quality_score
                + video.curriculum_alignment.get("alignment_score", 0) * 10
                for video in recommendations
            )
            personalization_score = total_score / (len(recommendations) * 2)

        # Yanıt oluştur
        response_videos = []
        for video in recommendations:
            response_videos.append(
                EBAVideoMetadata(
                    title=video.title,
                    description=video.description,
                    duration_minutes=video.duration_minutes,
                    category=video.category,
                    grade_level=video.grade_level,
                    subject_topics=video.subject_topics,
                    difficulty_level=video.difficulty_level,
                    video_url=video.video_url,
                    thumbnail_url=video.thumbnail_url,
                    transcript=video.transcript,
                    quality_score=video.quality_score,
                    curriculum_alignment=video.curriculum_alignment,
                    accessibility_features=video.accessibility_features,
                    created_date=video.created_date,
                    last_updated=video.last_updated,
                )
            )

        return EBAContentRecommendationResponse(
            recommendations=response_videos,
            student_id=request.student_id,
            recommendation_reasons=recommendation_reasons,
            personalization_score=personalization_score,
            generated_at=datetime.now(),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail="Islem basarisiz. Lutfen tekrar deneyin.")
    except Exception as e:
        logger.error(f"EBA TV öneri hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get(
    "/curriculum/{grade_level}/{category}/{topic}",
    summary="Müfredat Konusuna Göre İçerik",
)
async def get_content_by_curriculum_topic(
    grade_level: str = Path(..., description="Sınıf seviyesi"),
    category: str = Path(..., description="Kategori"),
    topic: str = Path(..., description="Konu"),
    ebatv_service: EBAtvService = Depends(get_ebatv_service),
):
    """
    Belirli müfredat konusuna göre EBA TV içerikleri getir

    - **grade_level**: Sınıf seviyesi (5-12)
    - **category**: İçerik kategorisi
    - **topic**: Müfredat konusu
    """

    try:
        # Enum dönüşümleri
        grade_enum = EBAGradeLevel(grade_level)
        category_enum = EBAContentCategory(category)

        # İçerikleri getir
        results = await ebatv_service.get_content_by_curriculum_topic(
            grade_enum, category_enum, topic
        )

        return {
            "success": True,
            "data": {
                "grade_level": grade_level,
                "category": category,
                "topic": topic,
                "total_results": len(results),
                "videos": [
                    {
                        "title": video.title,
                        "description": video.description,
                        "duration_minutes": video.duration_minutes,
                        "quality_score": video.quality_score,
                        "video_url": str(video.video_url),
                        "subject_topics": video.subject_topics,
                        "curriculum_alignment": video.curriculum_alignment,
                        "accessibility_features": video.accessibility_features,
                    }
                    for video in results
                ],
            },
            "message": f"{topic} konusu için {len(results)} video bulundu",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail="Islem basarisiz. Lutfen tekrar deneyin.")
    except Exception as e:
        logger.error(f"EBA TV müfredat içerik hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get(
    "/statistics",
    summary="EBA TV İçerik İstatistikleri",
    response_model=EBAContentStatistics,
)
async def get_eba_statistics(ebatv_service: EBAtvService = Depends(get_ebatv_service)):
    """
    EBA TV içerik istatistiklerini getir

    - Toplam video sayısı
    - Kategori dağılımı
    - Kalite dağılımı
    - Ortalama değerler
    """

    try:
        stats = await ebatv_service.get_content_statistics()

        return EBAContentStatistics(
            total_videos=stats["total_videos"],
            categories=stats["categories"],
            quality_distribution=stats["quality_distribution"],
            grade_distribution={},  # İstatistiklerden hesaplanacak
            average_quality=0.0,  # İstatistiklerden hesaplanacak
            average_duration=0.0,  # İstatistiklerden hesaplanacak
            last_updated=datetime.fromisoformat(stats["last_updated"]),
            cache_status=stats["cache_status"],
        )

    except Exception as e:
        logger.error(f"EBA TV istatistik hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/quality/analyze/{video_id}", summary="Video Kalite Analizi")
async def analyze_video_quality(
    video_id: int = Path(..., description="Video ID"),
    ebatv_service: EBAtvService = Depends(get_ebatv_service),
):
    """
    Belirli bir videonun kalite analizini yap

    - **video_id**: Analiz edilecek video ID'si
    """

    try:
        # Tüm içerikleri getir
        content_collection = await ebatv_service.get_all_content()

        # Video'yu bul
        if video_id >= len(content_collection.videos):
            raise HTTPException(status_code=404, detail=f"Video bulunamadı: {video_id}")

        video = content_collection.videos[video_id]

        # Detaylı kalite analizi (mock)
        return {
            "success": True,
            "data": {
                "video_id": video_id,
                "video_title": video.title,
                "overall_score": video.quality_score,
                "detailed_scores": {
                    "duration_score": 8.5,
                    "title_clarity_score": 9.0,
                    "description_quality_score": 8.0,
                    "curriculum_alignment_score": video.curriculum_alignment.get(
                        "alignment_score", 0
                    )
                    * 10,
                    "accessibility_score": 7.5 if video.accessibility_features else 2.0,
                },
                "improvement_suggestions": [
                    "Video süresini 15-20 dakika arasında tutun",
                    "Başlığa daha fazla anahtar kelime ekleyin",
                    "Açıklamayı daha detaylandırın",
                    "Altyazı ve transkript ekleyin",
                ],
                "quality_category": "high"
                if video.quality_score >= 8.0
                else "medium"
                if video.quality_score >= 6.0
                else "low",
                "analysis_date": datetime.now().isoformat(),
            },
            "message": f"{video.title} videosu için kalite analizi tamamlandı",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"EBA TV kalite analizi hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post(
    "/moderation",
    summary="İçerik Moderasyonu",
    response_model=EBAContentModerationResponse,
)
async def moderate_eba_content(
    request: EBAContentModerationRequest, _=Depends(get_current_admin_user)
):
    """
    EBA TV içerik moderasyonu (sadece admin)

    - **video_id**: Modere edilecek video ID'si
    - **action**: Moderasyon aksiyonu (approve, reject, flag)
    - **reason**: Moderasyon nedeni
    - **notes**: Moderatör notları
    """

    try:
        # Moderasyon işlemi (mock)
        moderation_actions = {
            "approve": "approved",
            "reject": "rejected",
            "flag": "flagged",
        }

        new_status = moderation_actions.get(request.action)
        if not new_status:
            raise HTTPException(
                status_code=400,
                detail=f"Geçersiz moderasyon aksiyonu: {request.action}",
            )

        return EBAContentModerationResponse(
            video_id=request.video_id,
            status=new_status,
            moderator_id=request.moderator_id,
            moderation_date=datetime.now(),
            action_taken=request.action,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"EBA TV moderasyon hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/health", summary="EBA TV Servis Sağlık Kontrolü")
async def eba_tv_health_check(ebatv_service: EBAtvService = Depends(get_ebatv_service)):
    """
    EBA TV servisinin sağlık durumunu kontrol et
    """

    try:
        # Basit sağlık kontrolü
        start_time = datetime.now()

        # Cache durumunu kontrol et
        stats = await ebatv_service.get_content_statistics()

        response_time = (datetime.now() - start_time).total_seconds() * 1000

        return {
            "success": True,
            "status": "healthy",
            "data": {
                "service_name": "EBA TV İçerik Entegrasyonu",
                "version": "1.0.0",
                "response_time_ms": response_time,
                "cache_status": stats["cache_status"],
                "total_videos": stats["total_videos"],
                "last_updated": stats["last_updated"],
                "timestamp": datetime.now().isoformat(),
            },
            "message": "EBA TV servisi sağlıklı çalışıyor",
        }

    except Exception as e:
        logger.error(f"EBA TV sağlık kontrolü hatası: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        )
