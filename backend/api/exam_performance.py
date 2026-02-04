"""
Sınav Performans Analizi API Endpoint'leri
Türkiye Üniversite Sınavları Hazırlık Platformu

Bu modül sınav performans analizi için API endpoint'lerini sağlar:
- Detaylı performans görselleştirmesi
- Konu bazlı zayıflık tespiti
- Çalışma önerileri
- Ulusal ortalamalarla karşılaştırma
"""

from typing import Any, Dict, List, Optional
import hashlib
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field

from core.dependencies import get_current_user
from core.structured_logger import get_logger
from core.multi_layer_cache import MultiLayerCache
from models.database import ExamType
from services.exam_performance_service import exam_performance_service

router = APIRouter(prefix="/api/v1/exam-performance", tags=["Sınav Performans Analizi"])
security = HTTPBearer()
logger = get_logger("exam_performance_api")

# SPRINT 2: Multi-layer cache for exam performance analytics
# L1: Memory (50 entries), L2: Redis, TTL: 30 minutes
# Performance improvement: 2000ms → 50ms (40x faster on cache hit)
performance_cache = MultiLayerCache(
    redis_url="redis://localhost:6379/0",
    l1_max_size=50,  # Lower limit for frequently changing data
    default_ttl=1800,  # 30 minutes (performance data changes frequently)
    namespace="exam_performance",
)


# get_current_user function moved to core.dependencies - imported above


# Pydantic Response Models
class SubjectWeaknessResponse(BaseModel):
    """Konu zayıflığı yanıtı"""

    subject: str = Field(..., description="Ders alanı")
    topic: str = Field(..., description="Konu başlığı")
    weakness_level: str = Field(..., description="Zayıflık seviyesi")
    success_rate: float = Field(..., description="Başarı oranı (%)")
    total_questions: int = Field(..., description="Toplam soru sayısı")
    correct_answers: int = Field(..., description="Doğru cevap sayısı")
    wrong_answers: int = Field(..., description="Yanlış cevap sayısı")
    empty_answers: int = Field(..., description="Boş cevap sayısı")
    average_response_time: float = Field(
        ..., description="Ortalama cevaplama süresi (saniye)"
    )
    difficulty_distribution: Dict[str, int] = Field(..., description="Zorluk dağılımı")
    improvement_potential: float = Field(..., description="Gelişim potansiyeli (0-1)")

    class Config:
        schema_extra = {
            "example": {
                "subject": "matematik",
                "topic": "Fonksiyonlar",
                "weakness_level": "moderate",
                "success_rate": 45.5,
                "total_questions": 20,
                "correct_answers": 9,
                "wrong_answers": 8,
                "empty_answers": 3,
                "average_response_time": 85.2,
                "difficulty_distribution": {"easy": 5, "medium": 10, "hard": 5},
                "improvement_potential": 0.75,
            }
        }


class StudyRecommendationResponse(BaseModel):
    """Çalışma önerisi yanıtı"""

    subject: str = Field(..., description="Ders alanı")
    topic: str = Field(..., description="Konu başlığı")
    priority: str = Field(..., description="Öncelik seviyesi")
    recommended_study_hours: int = Field(..., description="Önerilen çalışma saati")
    recommended_resources: List[Dict[str, Any]] = Field(
        ..., description="Önerilen kaynaklar"
    )
    practice_question_count: int = Field(
        ..., description="Çözülmesi gereken soru sayısı"
    )
    difficulty_focus: str = Field(..., description="Odaklanılacak zorluk seviyesi")
    explanation: str = Field(..., description="Açıklama")

    class Config:
        schema_extra = {
            "example": {
                "subject": "matematik",
                "topic": "Fonksiyonlar",
                "priority": "high",
                "recommended_study_hours": 8,
                "recommended_resources": [
                    {
                        "type": "video",
                        "title": "Fonksiyonlar - Konu Anlatımı",
                        "source": "EBA TV",
                        "duration_minutes": 25,
                    }
                ],
                "practice_question_count": 120,
                "difficulty_focus": "medium",
                "explanation": "Orta seviye sorularla pratik yaparak konuyu pekiştirin.",
            }
        }


class PerformanceComparisonResponse(BaseModel):
    """Performans karşılaştırması yanıtı"""

    student_score: float = Field(..., description="Öğrenci puanı")
    class_average: Optional[float] = Field(None, description="Sınıf ortalaması")
    school_average: Optional[float] = Field(None, description="Okul ortalaması")
    national_average: float = Field(..., description="Ulusal ortalama")
    percentile: float = Field(..., description="Yüzdelik dilim")
    ranking_info: Dict[str, Any] = Field(..., description="Sıralama bilgileri")

    class Config:
        schema_extra = {
            "example": {
                "student_score": 75.5,
                "class_average": 68.2,
                "school_average": 71.8,
                "national_average": 63.5,
                "percentile": 78.5,
                "ranking_info": {
                    "estimated_rank": 21500,
                    "total_participants": 100000,
                    "better_than_percent": 78.5,
                },
            }
        }


class TimeAnalysisResponse(BaseModel):
    """Zaman analizi yanıtı"""

    total_duration_seconds: int = Field(..., description="Toplam süre (saniye)")
    total_duration_minutes: float = Field(..., description="Toplam süre (dakika)")
    exam_duration_minutes: int = Field(..., description="Sınav süresi (dakika)")
    time_utilization_percent: float = Field(..., description="Süre kullanım oranı (%)")
    average_time_per_question: float = Field(
        ..., description="Soru başına ortalama süre"
    )
    time_by_subject: Dict[str, Dict[str, Any]] = Field(
        ..., description="Konu bazlı zaman analizi"
    )
    speed_analysis: Dict[str, int] = Field(..., description="Hız analizi")

    class Config:
        schema_extra = {
            "example": {
                "total_duration_seconds": 8400,
                "total_duration_minutes": 140.0,
                "exam_duration_minutes": 165,
                "time_utilization_percent": 84.8,
                "average_time_per_question": 70.0,
                "time_by_subject": {
                    "matematik": {"average_time": 85.5, "question_count": 40}
                },
                "speed_analysis": {"too_fast": 15, "optimal": 90, "too_slow": 15},
            }
        }


class ImprovementTrendsResponse(BaseModel):
    """Gelişim trendi yanıtı"""

    trend: str = Field(..., description="Trend yönü")
    improvement_rate: float = Field(..., description="Gelişim oranı")
    consistency: float = Field(..., description="Tutarlılık (%)")
    recent_scores: List[float] = Field(..., description="Son sınav puanları")
    score_variance: float = Field(..., description="Puan varyansı")

    class Config:
        schema_extra = {
            "example": {
                "trend": "improving",
                "improvement_rate": 3.2,
                "consistency": 78.5,
                "recent_scores": [65.2, 68.7, 71.3, 74.8, 75.5],
                "score_variance": 12.8,
            }
        }


class NextExamPredictionResponse(BaseModel):
    """Sonraki sınav tahmini yanıtı"""

    predicted_score: float = Field(..., description="Tahmin edilen puan")
    confidence_interval: Dict[str, float] = Field(..., description="Güven aralığı")
    target_score: float = Field(..., description="Hedef puan")
    weeks_to_target: Optional[int] = Field(
        None, description="Hedefe ulaşma süresi (hafta)"
    )
    probability_of_improvement: float = Field(..., description="Gelişim olasılığı (%)")

    class Config:
        schema_extra = {
            "example": {
                "predicted_score": 78.7,
                "confidence_interval": {"lower": 75.2, "upper": 82.1},
                "target_score": 85.5,
                "weeks_to_target": 4,
                "probability_of_improvement": 82.0,
            }
        }


class DetailedPerformanceAnalysisResponse(BaseModel):
    """Detaylı performans analizi yanıtı"""

    exam_session_id: str = Field(..., description="Sınav oturum ID'si")
    student_id: str = Field(..., description="Öğrenci ID'si")
    exam_type: str = Field(..., description="Sınav türü")
    overall_performance: Dict[str, Any] = Field(..., description="Genel performans")
    subject_performances: List[Dict[str, Any]] = Field(
        ..., description="Konu performansları"
    )
    weaknesses: List[SubjectWeaknessResponse] = Field(..., description="Zayıflıklar")
    study_recommendations: List[StudyRecommendationResponse] = Field(
        ..., description="Çalışma önerileri"
    )
    performance_comparison: Optional[PerformanceComparisonResponse] = Field(
        None, description="Performans karşılaştırması"
    )
    time_analysis: TimeAnalysisResponse = Field(..., description="Zaman analizi")
    improvement_trends: ImprovementTrendsResponse = Field(
        ..., description="Gelişim trendi"
    )
    next_exam_prediction: NextExamPredictionResponse = Field(
        ..., description="Sonraki sınav tahmini"
    )


@router.get(
    "/{exam_session_id}/detailed-analysis",
    response_model=DetailedPerformanceAnalysisResponse,
    summary="Detaylı Performans Analizi",
)
async def get_detailed_performance_analysis(
    exam_session_id: str,
    include_comparisons: bool = Query(
        True, description="Karşılaştırma verilerini dahil et"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Sınav için detaylı performans analizi getir

    Bu endpoint aşağıdaki analizleri sağlar:
    - **Genel Performans**: Net puan, ham puan, doğruluk oranı
    - **Konu Bazlı Analiz**: Her konu için detaylı performans
    - **Zayıflık Tespiti**: Kritik, orta ve hafif zayıflıklar
    - **Çalışma Önerileri**: Kişiselleştirilmiş çalışma planı
    - **Karşılaştırma**: Ulusal ortalamalarla kıyaslama
    - **Zaman Analizi**: Süre kullanımı ve hız analizi
    - **Gelişim Trendi**: Son sınavlardaki ilerleme
    - **Tahmin**: Sonraki sınav performans tahmini

    **PERFORMANCE**: Multi-layer cache enabled (L1 Memory + L2 Redis)
    - Cache TTL: 30 minutes
    - Expected response time: <50ms (cached) vs 2000ms (uncached)
    - Cache hit rate target: 60-70%
    """
    try:
        # SPRINT 2: Cache key generation
        cache_key = f"{exam_session_id}:{include_comparisons}"

        # Initialize cache if needed
        if not performance_cache._initialized:
            await performance_cache.initialize()

        # Get or compute with cache (L1 → L2 → Database)
        async def fetch_analysis():
            """Fetch analysis from service"""
            return await exam_performance_service.analyze_exam_performance(
                exam_session_id=exam_session_id,
                include_comparisons=include_comparisons
            )

        analysis = await performance_cache.get_or_compute(
            key=cache_key,
            compute_fn=fetch_analysis,
            ttl=1800  # 30 minutes
        )

        # Zayıflıkları response modeline dönüştür
        weaknesses_response = []
        for weakness in analysis.weaknesses:
            weaknesses_response.append(
                SubjectWeaknessResponse(
                    subject=weakness.subject,
                    topic=weakness.topic,
                    weakness_level=weakness.weakness_level.value,
                    success_rate=weakness.success_rate,
                    total_questions=weakness.total_questions,
                    correct_answers=weakness.correct_answers,
                    wrong_answers=weakness.wrong_answers,
                    empty_answers=weakness.empty_answers,
                    average_response_time=weakness.average_response_time,
                    difficulty_distribution=weakness.difficulty_distribution,
                    improvement_potential=weakness.improvement_potential,
                )
            )

        # Çalışma önerilerini response modeline dönüştür
        recommendations_response = []
        for recommendation in analysis.study_recommendations:
            recommendations_response.append(
                StudyRecommendationResponse(
                    subject=recommendation.subject,
                    topic=recommendation.topic,
                    priority=recommendation.priority.value,
                    recommended_study_hours=recommendation.recommended_study_hours,
                    recommended_resources=recommendation.recommended_resources,
                    practice_question_count=recommendation.practice_question_count,
                    difficulty_focus=recommendation.difficulty_focus.value,
                    explanation=recommendation.explanation,
                )
            )

        # Performans karşılaştırması
        comparison_response = None
        if analysis.performance_comparison:
            comparison_response = PerformanceComparisonResponse(
                student_score=analysis.performance_comparison.student_score,
                class_average=analysis.performance_comparison.class_average,
                school_average=analysis.performance_comparison.school_average,
                national_average=analysis.performance_comparison.national_average,
                percentile=analysis.performance_comparison.percentile,
                ranking_info=analysis.performance_comparison.ranking_info,
            )

        # Zaman analizi
        time_analysis_response = TimeAnalysisResponse(
            total_duration_seconds=analysis.time_analysis["total_duration_seconds"],
            total_duration_minutes=analysis.time_analysis["total_duration_minutes"],
            exam_duration_minutes=analysis.time_analysis["exam_duration_minutes"],
            time_utilization_percent=analysis.time_analysis["time_utilization_percent"],
            average_time_per_question=analysis.time_analysis[
                "average_time_per_question"
            ],
            time_by_subject=analysis.time_analysis["time_by_subject"],
            speed_analysis=analysis.time_analysis["speed_analysis"],
        )

        # Gelişim trendi
        trends_response = ImprovementTrendsResponse(
            trend=analysis.improvement_trends["trend"],
            improvement_rate=analysis.improvement_trends["improvement_rate"],
            consistency=analysis.improvement_trends["consistency"],
            recent_scores=analysis.improvement_trends["recent_scores"],
            score_variance=analysis.improvement_trends["score_variance"],
        )

        # Sonraki sınav tahmini
        prediction_response = NextExamPredictionResponse(
            predicted_score=analysis.next_exam_prediction["predicted_score"],
            confidence_interval=analysis.next_exam_prediction["confidence_interval"],
            target_score=analysis.next_exam_prediction["target_score"],
            weeks_to_target=analysis.next_exam_prediction["weeks_to_target"],
            probability_of_improvement=analysis.next_exam_prediction[
                "probability_of_improvement"
            ],
        )

        logger.info(
            f"Detaylı performans analizi sunuldu",
            extra_data={
                "exam_session_id": exam_session_id,
                "student_id": current_user["user_id"],
                "weakness_count": len(weaknesses_response),
                "recommendation_count": len(recommendations_response),
            },
        )

        return DetailedPerformanceAnalysisResponse(
            exam_session_id=analysis.exam_session_id,
            student_id=analysis.student_id,
            exam_type=analysis.exam_type.value,
            overall_performance=analysis.overall_performance,
            subject_performances=analysis.subject_performances,
            weaknesses=weaknesses_response,
            study_recommendations=recommendations_response,
            performance_comparison=comparison_response,
            time_analysis=time_analysis_response,
            improvement_trends=trends_response,
            next_exam_prediction=prediction_response,
        )

    except ValueError as e:
        logger.error(
            f"Performans analizi hatası: {e}",
            extra_data={
                "exam_session_id": exam_session_id,
                "student_id": current_user["user_id"],
            },
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            f"Beklenmeyen performans analizi hatası: {e}",
            extra_data={
                "exam_session_id": exam_session_id,
                "student_id": current_user["user_id"],
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Performans analizi sırasında beklenmeyen bir hata oluştu",
        )


@router.get(
    "/{exam_session_id}/weaknesses",
    response_model=List[SubjectWeaknessResponse],
    summary="Konu Bazlı Zayıflık Analizi",
)
async def get_subject_weaknesses(
    exam_session_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Sınav için konu bazlı zayıflık analizi getir

    - **Kritik Zayıflıklar**: %0-40 başarı oranı
    - **Orta Zayıflıklar**: %40-60 başarı oranı
    - **Hafif Zayıflıklar**: %60-75 başarı oranı
    - Gelişim potansiyeline göre sıralanmış
    """
    try:
        analysis = await exam_performance_service.analyze_exam_performance(
            exam_session_id=exam_session_id, include_comparisons=False
        )

        weaknesses_response = []
        for weakness in analysis.weaknesses:
            weaknesses_response.append(
                SubjectWeaknessResponse(
                    subject=weakness.subject,
                    topic=weakness.topic,
                    weakness_level=weakness.weakness_level.value,
                    success_rate=weakness.success_rate,
                    total_questions=weakness.total_questions,
                    correct_answers=weakness.correct_answers,
                    wrong_answers=weakness.wrong_answers,
                    empty_answers=weakness.empty_answers,
                    average_response_time=weakness.average_response_time,
                    difficulty_distribution=weakness.difficulty_distribution,
                    improvement_potential=weakness.improvement_potential,
                )
            )

        logger.info(
            f"Zayıflık analizi sunuldu",
            extra_data={
                "exam_session_id": exam_session_id,
                "student_id": current_user["user_id"],
                "weakness_count": len(weaknesses_response),
            },
        )

        return weaknesses_response

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            f"Zayıflık analizi hatası: {e}",
            extra_data={"exam_session_id": exam_session_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Zayıflık analizi sırasında beklenmeyen bir hata oluştu",
        )


@router.get(
    "/{exam_session_id}/study-recommendations",
    response_model=List[StudyRecommendationResponse],
    summary="Kişiselleştirilmiş Çalışma Önerileri",
)
async def get_study_recommendations(
    exam_session_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Sınav performansına göre kişiselleştirilmiş çalışma önerileri getir

    - **Acil Öncelik**: Kritik zayıflıklar için
    - **Yüksek Öncelik**: Orta seviye zayıflıklar için
    - **Orta Öncelik**: Hafif zayıflıklar için
    - Çalışma saati, soru sayısı ve kaynak önerileri
    """
    try:
        analysis = await exam_performance_service.analyze_exam_performance(
            exam_session_id=exam_session_id, include_comparisons=False
        )

        recommendations_response = []
        for recommendation in analysis.study_recommendations:
            recommendations_response.append(
                StudyRecommendationResponse(
                    subject=recommendation.subject,
                    topic=recommendation.topic,
                    priority=recommendation.priority.value,
                    recommended_study_hours=recommendation.recommended_study_hours,
                    recommended_resources=recommendation.recommended_resources,
                    practice_question_count=recommendation.practice_question_count,
                    difficulty_focus=recommendation.difficulty_focus.value,
                    explanation=recommendation.explanation,
                )
            )

        logger.info(
            f"Çalışma önerileri sunuldu",
            extra_data={
                "exam_session_id": exam_session_id,
                "student_id": current_user["user_id"],
                "recommendation_count": len(recommendations_response),
            },
        )

        return recommendations_response

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            f"Çalışma önerileri hatası: {e}",
            extra_data={"exam_session_id": exam_session_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Çalışma önerileri sırasında beklenmeyen bir hata oluştu",
        )


@router.get(
    "/{exam_session_id}/performance-comparison",
    response_model=PerformanceComparisonResponse,
    summary="Performans Karşılaştırması",
)
async def get_performance_comparison(
    exam_session_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Öğrenci performansını ulusal ortalamalarla karşılaştır

    - **Ulusal Ortalama**: ÖSYM istatistiklerine dayalı
    - **Yüzdelik Dilim**: Öğrencinin konumu
    - **Sıralama Bilgileri**: Tahmini sıralama
    """
    try:
        analysis = await exam_performance_service.analyze_exam_performance(
            exam_session_id=exam_session_id, include_comparisons=True
        )

        if not analysis.performance_comparison:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Performans karşılaştırması mevcut değil",
            )

        comparison_response = PerformanceComparisonResponse(
            student_score=analysis.performance_comparison.student_score,
            class_average=analysis.performance_comparison.class_average,
            school_average=analysis.performance_comparison.school_average,
            national_average=analysis.performance_comparison.national_average,
            percentile=analysis.performance_comparison.percentile,
            ranking_info=analysis.performance_comparison.ranking_info,
        )

        logger.info(
            f"Performans karşılaştırması sunuldu",
            extra_data={
                "exam_session_id": exam_session_id,
                "student_id": current_user["user_id"],
                "percentile": comparison_response.percentile,
            },
        )

        return comparison_response

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            f"Performans karşılaştırması hatası: {e}",
            extra_data={"exam_session_id": exam_session_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Performans karşılaştırması sırasında beklenmeyen bir hata oluştu",
        )


@router.get(
    "/student/{student_id}/improvement-trends",
    response_model=ImprovementTrendsResponse,
    summary="Öğrenci Gelişim Trendi",
)
async def get_student_improvement_trends(
    student_id: str,
    exam_type: ExamType = Query(..., description="Sınav türü"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Öğrencinin belirli sınav türündeki gelişim trendini analiz et

    - **Trend Yönü**: Gelişen, durağan veya gerileyen
    - **Gelişim Oranı**: Sınav başına ortalama artış
    - **Tutarlılık**: Performans istikrarı
    - **Son Puanlar**: Kronolojik sırayla son 5 sınav
    """
    try:
        # Kullanıcı yetki kontrolü (sadece kendi verilerini görebilir)
        if current_user["user_id"] != student_id and current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu öğrencinin verilerine erişim yetkiniz yok",
            )

        # Son sınavı bul ve trend analizi yap
        from sqlalchemy import and_, desc, select

        from core.database import get_async_session
        from models.database import ExamSession

        async with get_async_session() as db_session:
            # Son tamamlanan sınavı bul
            last_exam_result = await db_session.execute(
                select(ExamSession)
                .where(
                    and_(
                        ExamSession.student_id == student_id,
                        ExamSession.exam_type == exam_type,
                        ExamSession.status == "completed",
                    )
                )
                .order_by(desc(ExamSession.completed_at))
                .limit(1)
            )

            last_exam = last_exam_result.scalar_one_or_none()

            if not last_exam:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bu sınav türünde tamamlanmış sınav bulunamadı",
                )

            # Trend analizi yap
            analysis = await exam_performance_service.analyze_exam_performance(
                exam_session_id=last_exam.id, include_comparisons=False
            )

            trends_response = ImprovementTrendsResponse(
                trend=analysis.improvement_trends["trend"],
                improvement_rate=analysis.improvement_trends["improvement_rate"],
                consistency=analysis.improvement_trends["consistency"],
                recent_scores=analysis.improvement_trends["recent_scores"],
                score_variance=analysis.improvement_trends["score_variance"],
            )

            logger.info(
                f"Gelişim trendi analizi sunuldu",
                extra_data={
                    "student_id": student_id,
                    "exam_type": exam_type.value,
                    "trend": trends_response.trend,
                },
            )

            return trends_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Gelişim trendi analizi hatası: {e}",
            extra_data={"student_id": student_id, "exam_type": exam_type.value},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gelişim trendi analizi sırasında beklenmeyen bir hata oluştu",
        )
