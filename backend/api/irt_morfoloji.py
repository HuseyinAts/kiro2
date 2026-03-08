"""
IRT + Türkçe Morfoloji API
ÖSYM ve ETS standartlarını aşan soru analizi API'si
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from algorithms.irt_morfoloji_service import IRTParameters, irt_morfoloji_service
from core.dependencies import get_current_user, AuthenticatedUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/irt-morfoloji", tags=["IRT Morfoloji"])


class QuestionAnalysisRequest(BaseModel):
    """Soru analizi isteği"""

    question_id: str = Field(..., description="Soru ID")
    question_text: str = Field(..., description="Soru metni")
    correct_answer: str = Field(..., description="Doğru cevap")
    student_responses: Optional[List[Dict[str, Any]]] = Field(
        None, description="Öğrenci yanıtları"
    )
    base_difficulty: Optional[float] = Field(None, description="Temel zorluk seviyesi")


class BatchAnalysisRequest(BaseModel):
    """Toplu analiz isteği"""

    questions: List[Dict[str, Any]] = Field(..., description="Soru listesi")


class MorphologyInsightsRequest(BaseModel):
    """Morfoloji içgörü isteği"""

    text: str = Field(..., description="Analiz edilecek metin")


class DifficultyRecommendationRequest(BaseModel):
    """Zorluk önerisi isteği"""

    current_difficulty: float = Field(..., description="Mevcut zorluk")
    student_performance: float = Field(..., description="Öğrenci performansı (0-1)")
    morphology_complexity: float = Field(
        ..., description="Morfolojik karmaşıklık (0-1)"
    )


@router.post("/analyze-question")
async def analyze_question(
    request: QuestionAnalysisRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Tek soru IRT + Morfoloji analizi
    """
    try:
        logger.info(f"IRT + Morfoloji analizi başlatıldı - Soru: {request.question_id}")

        analysis = await irt_morfoloji_service.analyze_question_irt_morphology(
            question_id=request.question_id,
            question_text=request.question_text,
            correct_answer=request.correct_answer,
            student_responses=request.student_responses,
            base_difficulty=request.base_difficulty,
        )

        return {
            "success": True,
            "data": {
                "question_id": analysis.question_id,
                "question_text": analysis.question_text,
                "irt_parameters": {
                    "difficulty": analysis.irt_parameters.difficulty,
                    "discrimination": analysis.irt_parameters.discrimination,
                    "guessing": analysis.irt_parameters.guessing,
                    "upper_asymptote": analysis.irt_parameters.upper_asymptote,
                },
                "morphology_complexity": {
                    "word": analysis.morphology_complexity.word,
                    "root": analysis.morphology_complexity.root,
                    "suffixes": analysis.morphology_complexity.suffixes,
                    "suffix_count": analysis.morphology_complexity.suffix_count,
                    "overall_complexity": analysis.morphology_complexity.overall_complexity,
                },
                "adjusted_difficulty": analysis.adjusted_difficulty,
                "turkish_difficulty_factor": analysis.turkish_difficulty_factor,
                "osym_ets_comparison": analysis.osym_ets_comparison,
                "recommendations": analysis.recommendations,
                "analysis_confidence": analysis.analysis_confidence,
                "metadata": analysis.metadata,
            },
            "message": "IRT + Morfoloji analizi başarıyla tamamlandı",
        }

    except Exception as e:
        logger.error(f"IRT + Morfoloji analiz hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Analiz sırasında hata oluştu: {str(e)}"
        )


@router.post("/batch-analyze")
async def batch_analyze_questions(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Toplu soru analizi
    """
    try:
        logger.info(
            f"Toplu IRT + Morfoloji analizi başlatıldı - {len(request.questions)} soru"
        )

        # Arka planda işlem başlat
        background_tasks.add_task(
            _process_batch_analysis, request.questions, current_user.id
        )

        return {
            "success": True,
            "data": {
                "batch_id": f"batch_{current_user.id}_{len(request.questions)}",
                "question_count": len(request.questions),
                "status": "processing",
            },
            "message": f"{len(request.questions)} soru toplu analizi başlatıldı",
        }

    except Exception as e:
        logger.error(f"Toplu analiz hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Toplu analiz sırasında hata oluştu: {str(e)}"
        )


@router.post("/morphology-insights")
async def get_morphology_insights(
    request: MorphologyInsightsRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Metin morfoloji içgörüleri
    """
    try:
        logger.info("Morfoloji içgörü analizi başlatıldı")

        insights = await irt_morfoloji_service.get_morphology_insights(request.text)

        return {
            "success": True,
            "data": insights,
            "message": "Morfoloji içgörüleri başarıyla oluşturuldu",
        }

    except Exception as e:
        logger.error(f"Morfoloji içgörü hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Morfoloji analizi sırasında hata oluştu: {str(e)}"
        )


@router.post("/difficulty-recommendation")
async def get_difficulty_recommendation(
    request: DifficultyRecommendationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Zorluk seviyesi önerisi
    """
    try:
        logger.info("Zorluk önerisi hesaplanıyor")

        (
            new_difficulty,
            recommendation,
        ) = await irt_morfoloji_service.get_difficulty_recommendation(
            request.current_difficulty,
            request.student_performance,
            request.morphology_complexity,
        )

        return {
            "success": True,
            "data": {
                "current_difficulty": request.current_difficulty,
                "recommended_difficulty": new_difficulty,
                "adjustment": new_difficulty - request.current_difficulty,
                "recommendation": recommendation,
                "student_performance": request.student_performance,
                "morphology_factor": request.morphology_complexity,
            },
            "message": "Zorluk önerisi başarıyla hesaplandı",
        }

    except Exception as e:
        logger.error(f"Zorluk önerisi hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Zorluk önerisi sırasında hata oluştu: {str(e)}"
        )


@router.post("/calculate-probability")
async def calculate_irt_probability(
    student_ability: float,
    difficulty: float,
    discrimination: float,
    guessing: float = 0.20,
    morphology_adjustment: bool = True,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    IRT olasılık hesaplama
    """
    try:
        irt_params = IRTParameters(
            difficulty=difficulty,
            discrimination=discrimination,
            guessing=guessing,
            upper_asymptote=1.0,
        )

        probability = await irt_morfoloji_service.calculate_irt_probability(
            student_ability, irt_params, morphology_adjustment
        )

        return {
            "success": True,
            "data": {
                "student_ability": student_ability,
                "irt_parameters": {
                    "difficulty": difficulty,
                    "discrimination": discrimination,
                    "guessing": guessing,
                },
                "probability": probability,
                "morphology_adjusted": morphology_adjustment,
            },
            "message": "IRT olasılık başarıyla hesaplandı",
        }

    except Exception as e:
        logger.error(f"IRT olasılık hesaplama hatası: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Olasılık hesaplama sırasında hata oluştu: {str(e)}",
        )


@router.get("/service-stats")
async def get_service_stats(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Servis istatistikleri
    """
    try:
        stats = irt_morfoloji_service.get_service_stats()

        return {
            "success": True,
            "data": stats,
            "message": "Servis istatistikleri başarıyla alındı",
        }

    except Exception as e:
        logger.error(f"Servis istatistik hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"İstatistik alınırken hata oluştu: {str(e)}"
        )


async def _process_batch_analysis(questions: List[Dict[str, Any]], user_id: str):
    """
    Arka planda toplu analiz işlemi
    """
    try:
        logger.info(f"Arka plan toplu analizi başlatıldı - Kullanıcı: {user_id}")

        results = await irt_morfoloji_service.batch_analyze_questions(questions)

        # Sonuçları veritabanına kaydet (implementasyon gerekli)
        # await save_batch_analysis_results(user_id, results)

        logger.info(f"Toplu analiz tamamlandı - {len(results)} soru işlendi")

    except Exception as e:
        logger.error(f"Arka plan toplu analiz hatası: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Servis sağlık kontrolü
    """
    return {
        "success": True,
        "data": {
            "service": "IRT + Türkçe Morfoloji API",
            "status": "healthy",
            "version": "1.0.0",
        },
        "message": "Servis çalışıyor",
    }


# Servisle tam uyumlu ek endpoint'ler


class QuickAssessmentRequest(BaseModel):
    """Hızlı değerlendirme isteği"""

    question_text: str = Field(..., description="Soru metni")
    target_difficulty: float = Field(
        0.0, ge=-4.0, le=4.0, description="Hedef zorluk seviyesi"
    )
    target_student_level: str = Field(
        "orta", description="Hedef öğrenci seviyesi (temel/orta/ileri)"
    )


class StudentQuestionRecommendationRequest(BaseModel):
    """Öğrenci soru önerisi isteği"""

    student_id: str = Field(..., description="Öğrenci ID")
    subject: str = Field(..., description="Konu")
    target_success_rate: float = Field(
        0.7, ge=0.0, le=1.0, description="Hedef başarı oranı"
    )
    question_pool: Optional[List[str]] = Field(None, description="Soru havuzu ID'leri")


class QualityAnalysisRequest(BaseModel):
    """Toplu kalite analizi isteği"""

    questions: List[Dict[str, Any]] = Field(..., description="Soru listesi")
    quality_threshold: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Minimum kalite eşiği"
    )


class OSYMETSComparisonRequest(BaseModel):
    """ÖSYM/ETS karşılaştırma isteği"""

    question_id: str = Field(..., description="Soru ID")


@router.post("/quick-assessment")
async def quick_assessment(
    request: QuickAssessmentRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Soru için hızlı ön değerlendirme

    Morfolojik analiz ile tahmini zorluk ve uygunluk skorunu hızlıca hesaplar.
    """
    try:
        from services.irt_morfoloji_service import IRTMorfolojiService

        service = IRTMorfolojiService()
        result = await service.hizli_soru_degerlendirmesi(
            soru_metni=request.question_text,
            hedef_zorluk=request.target_difficulty,
            hedef_ogrenci_seviyesi=request.target_student_level,
        )

        return {
            "success": True,
            "data": result,
            "message": "Hızlı değerlendirme tamamlandı",
        }

    except Exception as e:
        logger.error(f"Hızlı değerlendirme hatası: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Hızlı değerlendirme sırasında hata oluştu: {str(e)}",
        )


@router.post("/recommend-questions")
async def recommend_questions_for_student(
    request: StudentQuestionRecommendationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Öğrenci profiline uygun soru önerisi

    IRT parametreleri ve morfoloji uyumu bazında optimal sorular önerir.
    """
    try:
        from services.irt_morfoloji_service import IRTMorfolojiService

        service = IRTMorfolojiService()
        recommendations = await service.ogrenci_uyumlu_soru_onerisi(
            ogrenci_id=request.student_id,
            konu=request.subject,
            hedef_basari_orani=request.target_success_rate,
            soru_havuzu=request.question_pool,
        )

        return {
            "success": True,
            "data": {
                "student_id": request.student_id,
                "subject": request.subject,
                "recommendations": recommendations,
                "recommendation_count": len(recommendations),
            },
            "message": f"{len(recommendations)} uygun soru önerildi",
        }

    except Exception as e:
        logger.error(f"Soru önerisi hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Soru önerisi sırasında hata oluştu: {str(e)}"
        )


@router.post("/bulk-quality-analysis")
async def bulk_quality_analysis(
    request: QualityAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Toplu soru kalite analizi

    Birden fazla sorunun IRT + Morfoloji kalite analizini yapar.
    """
    try:
        from services.irt_morfoloji_service import IRTMorfolojiService

        service = IRTMorfolojiService()
        analysis_result = await service.toplu_soru_kalite_analizi(
            soru_listesi=request.questions, kalite_esigi=request.quality_threshold
        )

        return {
            "success": True,
            "data": analysis_result,
            "message": f"{analysis_result['toplam_soru_sayisi']} soru kalite analizi tamamlandı",
        }

    except Exception as e:
        logger.error(f"Toplu kalite analizi hatası: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Toplu kalite analizi sırasında hata oluştu: {str(e)}",
        )


@router.post("/osym-ets-comparison")
async def osym_ets_comparison(
    request: OSYMETSComparisonRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    ÖSYM ve ETS standartları ile karşılaştırma

    Sorunun ÖSYM ve ETS standartlarına göre kalitesini değerlendirir.
    Türkçe morfoloji avantajını gösterir.
    """
    try:
        from services.irt_morfoloji_service import IRTMorfolojiService

        service = IRTMorfolojiService()
        comparison = await service.osym_ets_karsilastirma_raporu(
            soru_id=request.question_id
        )

        return {
            "success": True,
            "data": comparison,
            "message": "ÖSYM/ETS karşılaştırma raporu oluşturuldu",
        }

    except Exception as e:
        logger.error(f"ÖSYM/ETS karşılaştırma hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Karşılaştırma sırasında hata oluştu: {str(e)}"
        )


@router.get("/full-analysis/{question_id}")
async def get_full_question_analysis(
    question_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Tam kapsamlı soru analizi

    Belirtilen soru için IRT parametreleri, morfoloji analizi,
    kalite metrikleri ve önerileri içeren tam rapor.
    """
    try:
        from services.irt_morfoloji_service import IRTMorfolojiService

        service = IRTMorfolojiService()

        if question_id not in service.soru_analizleri:
            raise HTTPException(
                status_code=404, detail=f"Soru bulunamadı: {question_id}"
            )

        analysis = service.soru_analizleri[question_id]

        return {
            "success": True,
            "data": {
                "soru_id": analysis.soru_id,
                "konu": analysis.konu,
                "sinav_tipi": analysis.sinav_tipi,
                "irt_parametreleri": {
                    "difficulty": analysis.irt_parametreleri.difficulty,
                    "discrimination": analysis.irt_parametreleri.discrimination,
                    "guessing": analysis.irt_parametreleri.guessing,
                    "morfoloji_faktoru": analysis.irt_parametreleri.morfoloji_faktoru,
                },
                "morfoloji_analizi": {
                    "ortalama_skor": analysis.morfoloji_analizi.ortalama_morfoloji_skoru,
                    "toplam_kelime": analysis.morfoloji_analizi.toplam_kelime_sayisi,
                    "ortalama_ek": analysis.morfoloji_analizi.ortalama_ek_sayisi,
                    "ek_cesitliligi": analysis.morfoloji_analizi.ek_tipi_cesitliligi,
                },
                "zorluk_seviyesi": analysis.zorluk_seviyesi,
                "kalite_skoru": analysis.get_soru_kalite_skoru(),
                "iyilestirme_onerileri": analysis.iyilestirme_onerileri,
                "analiz_tarihi": analysis.analiz_tarihi.isoformat(),
            },
            "message": "Tam soru analizi başarıyla getirildi",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tam analiz getirme hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Analiz getirilirken hata oluştu: {str(e)}"
        )
