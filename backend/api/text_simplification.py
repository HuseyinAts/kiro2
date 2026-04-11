"""
Metin Basitleştirme API Endpoints
Task 80: Text Simplification for Dyslexia Support
Requirements: REQ-50.57 - REQ-50.72
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.dependencies import AuthenticatedUser, get_current_user
from core.text_simplification_service import text_simplification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/text-simplification", tags=["Text Simplification"])


# Request/Response Models
class ComplexWordsRequest(BaseModel):
    """Karmaşık kelime tespiti isteği"""

    text: str = Field(
        ..., min_length=1, max_length=10000, description="Analiz edilecek metin"
    )
    complexity_threshold: float = Field(
        0.6, ge=0.0, le=1.0, description="Karmaşıklık eşiği"
    )


class ComplexWordsResponse(BaseModel):
    """Karmaşık kelime tespiti yanıtı"""

    success: bool
    data: dict
    message: str


class SimplifyTextRequest(BaseModel):
    """Metin basitleştirme isteği"""

    text: str = Field(
        ..., min_length=1, max_length=10000, description="Basitleştirilecek metin"
    )
    complexity_threshold: float = Field(
        0.6, ge=0.0, le=1.0, description="Karmaşıklık eşiği"
    )
    max_sentence_length: int = Field(
        20, ge=5, le=50, description="Maksimum cümle uzunluğu (kelime)"
    )
    replace_synonyms: bool = Field(
        True, description="Eşanlamlı değiştirme yapılsın mı?"
    )
    split_sentences: bool = Field(True, description="Cümle bölme yapılsın mı?")
    require_confirmation: bool = Field(False, description="Kullanıcı onayı gerekli mi?")


class SimplifyTextResponse(BaseModel):
    """Metin basitleştirme yanıtı"""

    success: bool
    data: dict
    message: str


class FleschScoreRequest(BaseModel):
    """Flesch-Kincaid skoru isteği"""

    text: str = Field(
        ..., min_length=1, max_length=10000, description="Analiz edilecek metin"
    )


class FleschScoreResponse(BaseModel):
    """Flesch-Kincaid skoru yanıtı"""

    success: bool
    data: dict
    message: str


# Task 80.1: Karmaşık Kelime Tespiti Endpoint
@router.post("/detect-complex-words", response_model=ComplexWordsResponse)
async def detect_complex_words(
    request: ComplexWordsRequest,
    _current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Metindeki karmaşık kelimeleri tespit et

    Bu endpoint:
    - Karmaşıklık skorunu hesaplar
    - Kelime frekansını analiz eder
    - Basit eşanlamlılar önerir
    - Zorluk eşiğini uygular

    Requirements: REQ-50.57, REQ-50.58, REQ-50.59, REQ-50.60
    """
    try:
        logger.info(f"Karmaşık kelime tespiti - Metin uzunluğu: {len(request.text)}")

        # Karmaşık kelimeleri tespit et
        complex_words = text_simplification_service.detect_complex_words(
            text=request.text, complexity_threshold=request.complexity_threshold
        )

        # Yanıt verilerini hazırla
        response_data = {
            "complex_words": [
                {
                    "word": cw.word,
                    "complexity_score": round(cw.complexity_score, 3),
                    "frequency_score": round(cw.frequency_score, 3),
                    "position": cw.position,
                    "suggested_replacements": cw.suggested_replacements,
                }
                for cw in complex_words
            ],
            "total_complex_words": len(complex_words),
            "complexity_threshold": request.complexity_threshold,
            "text_length": len(request.text),
            "word_count": len(request.text.split()),
        }

        return ComplexWordsResponse(
            success=True,
            data=response_data,
            message=f"{len(complex_words)} karmaşık kelime tespit edildi",
        )

    except Exception as e:
        logger.error(f"Karmaşık kelime tespiti hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


# Task 80.2 & 80.3 & 80.4: Tam Basitleştirme Endpoint
@router.post("/simplify", response_model=SimplifyTextResponse)
async def simplify_text(
    request: SimplifyTextRequest,
    _current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Metni kapsamlı şekilde basitleştir

    Bu endpoint:
    - Karmaşık kelimeleri basit eşanlamlılarıyla değiştirir
    - Uzun cümleleri böler
    - Flesch-Kincaid okunabilirlik skorunu hesaplar
    - İyileştirme önerileri sunar

    Requirements: REQ-50.57 - REQ-50.72
    """
    try:
        logger.info(f"Metin basitleştirme - Metin uzunluğu: {len(request.text)}")

        # Metni basitleştir
        result = text_simplification_service.simplify_text(
            text=request.text,
            complexity_threshold=request.complexity_threshold,
            max_sentence_length=request.max_sentence_length,
            replace_synonyms=request.replace_synonyms,
            split_sentences=request.split_sentences,
            require_confirmation=request.require_confirmation,
        )

        # Yanıt verilerini hazırla
        response_data = {
            "original_text": result.original_text,
            "simplified_text": result.simplified_text,
            "statistics": {
                "complex_words_replaced": result.complex_words_replaced,
                "sentences_split": result.sentences_split,
                "readability_improvement": result.readability_improvement,
                "original_flesch_score": result.original_flesch_score,
                "simplified_flesch_score": result.simplified_flesch_score,
            },
            "suggestions": result.suggestions,
            "improvement_percentage": round(
                (result.readability_improvement / max(result.original_flesch_score, 1))
                * 100,
                2,
            ),
        }

        return SimplifyTextResponse(
            success=True,
            data=response_data,
            message=f"Metin başarıyla basitleştirildi (Okunabilirlik: {result.readability_improvement:+.2f})",
        )

    except Exception as e:
        logger.error(f"Metin basitleştirme hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


# Task 80.4: Flesch-Kincaid Skoru Endpoint
@router.post("/flesch-score", response_model=FleschScoreResponse)
async def calculate_flesch_score(
    request: FleschScoreRequest,
    _current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Türkçe metin için Flesch-Kincaid okunabilirlik skorunu hesapla

    Bu endpoint:
    - Flesch Reading Ease skorunu hesaplar (0-100)
    - Flesch-Kincaid Grade Level'ı hesaplar
    - Zorluk seviyesini belirler
    - Sınıf seviyesi tahmini yapar
    - İyileştirme önerileri sunar

    Requirements: REQ-50.69, REQ-50.70, REQ-50.71, REQ-50.72
    """
    try:
        logger.info(
            f"Flesch-Kincaid skoru hesaplama - Metin uzunluğu: {len(request.text)}"
        )

        # Flesch-Kincaid skorunu hesapla
        flesch_result = text_simplification_service.calculate_flesch_kincaid_score(
            request.text
        )

        # Yanıt verilerini hazırla
        response_data = {
            "flesch_reading_ease": flesch_result["flesch_reading_ease"],
            "flesch_kincaid_grade": flesch_result["flesch_kincaid_grade"],
            "grade_level": flesch_result["grade_level"],
            "difficulty": flesch_result["difficulty"],
            "statistics": flesch_result["statistics"],
            "interpretation": {
                "score_range": _get_score_range(flesch_result["flesch_reading_ease"]),
                "target_audience": _get_target_audience(
                    flesch_result["flesch_reading_ease"]
                ),
                "recommendations": _get_readability_recommendations(flesch_result),
            },
        }

        return FleschScoreResponse(
            success=True,
            data=response_data,
            message=f"Okunabilirlik skoru: {flesch_result['flesch_reading_ease']:.2f} ({flesch_result['difficulty']})",
        )

    except Exception as e:
        logger.error(f"Flesch-Kincaid skoru hesaplama hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


def _get_score_range(score: float) -> str:
    """Skor aralığını belirle"""
    if score >= 90:
        return "90-100: Çok Kolay"
    if score >= 80:
        return "80-90: Kolay"
    if score >= 70:
        return "70-80: Oldukça Kolay"
    if score >= 60:
        return "60-70: Standart"
    if score >= 50:
        return "50-60: Oldukça Zor"
    if score >= 30:
        return "30-50: Zor"
    return "0-30: Çok Zor"


def _get_target_audience(score: float) -> str:
    """Hedef kitleyi belirle"""
    if score >= 90:
        return "İlkokul 1-2. sınıf öğrencileri"
    if score >= 80:
        return "İlkokul 3-4. sınıf öğrencileri"
    if score >= 70:
        return "Ortaokul 5-6. sınıf öğrencileri"
    if score >= 60:
        return "Ortaokul 7-8. sınıf öğrencileri"
    if score >= 50:
        return "Lise 9-10. sınıf öğrencileri"
    if score >= 30:
        return "Lise 11-12. sınıf öğrencileri"
    return "Üniversite öğrencileri ve yetişkinler"


def _get_readability_recommendations(flesch_result: dict) -> list:
    """Okunabilirlik önerileri sun"""
    recommendations = []
    score = flesch_result["flesch_reading_ease"]
    stats = flesch_result.get("statistics", {})

    if score < 50:
        recommendations.append("Metni basitleştirmeyi düşünün")
        recommendations.append("Daha kısa cümleler kullanın")
        recommendations.append("Basit kelimeler tercih edin")

    avg_words = stats.get("avg_words_per_sentence", 0)
    if avg_words > 20:
        recommendations.append(
            f"Ortalama cümle uzunluğu çok yüksek ({avg_words:.1f} kelime)"
        )
        recommendations.append("Cümleleri 15-20 kelimeye indirin")

    avg_syllables = stats.get("avg_syllables_per_word", 0)
    if avg_syllables > 2.5:
        recommendations.append(f"Ortalama hece sayısı yüksek ({avg_syllables:.1f})")
        recommendations.append("Daha kısa kelimeler kullanın")

    if not recommendations:
        recommendations.append("Metin okunabilirliği iyi seviyede")

    return recommendations


@router.get("/health")
async def health_check():
    """
    Metin basitleştirme servisinin sağlık kontrolü
    """
    try:
        return {
            "success": True,
            "message": "Metin basitleştirme servisi çalışıyor",
            "data": {
                "service_status": "healthy",
                "features": {
                    "complex_word_detection": True,
                    "synonym_replacement": True,
                    "sentence_splitting": True,
                    "flesch_kincaid_scoring": True,
                },
                "word_database_size": len(text_simplification_service.common_words),
                "synonym_dictionary_size": len(text_simplification_service.synonyms),
            },
        }

    except Exception as e:
        logger.error(f"Sağlık kontrolü hatası: {e}")
        return {
            "success": False,
            "message": f"Sistem hatası: {e!s}",
            "data": {"service_status": "unhealthy", "error": str(e)},
        }
