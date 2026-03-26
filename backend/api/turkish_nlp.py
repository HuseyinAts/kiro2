"""
Türkçe NLP API Endpoints
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.turkish_nlp_service import turkish_nlp_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/turkish-nlp", tags=["Turkish NLP"])


# Request/Response Models
class MorphologyAnalysisRequest(BaseModel):
    """Morfolojik analiz isteği"""

    word: str = Field(
        ..., description="Analiz edilecek kelime", min_length=1, max_length=100
    )


class MorphologyAnalysisResponse(BaseModel):
    """Morfolojik analiz yanıtı"""

    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str


class TextNormalizationRequest(BaseModel):
    """Metin normalizasyon isteği"""

    text: str = Field(
        ..., description="Normalize edilecek metin", min_length=1, max_length=10000
    )


class TextNormalizationResponse(BaseModel):
    """Metin normalizasyon yanıtı"""

    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str


class TextComplexityRequest(BaseModel):
    """Metin karmaşıklık analizi isteği"""

    text: str = Field(
        ..., description="Analiz edilecek metin", min_length=1, max_length=10000
    )


class TextComplexityResponse(BaseModel):
    """Metin karmaşıklık analizi yanıtı"""

    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str


class BatchMorphologyRequest(BaseModel):
    """Toplu morfolojik analiz isteği"""

    words: List[str] = Field(
        ..., description="Analiz edilecek kelimeler", min_items=1, max_items=100
    )


class BatchMorphologyResponse(BaseModel):
    """Toplu morfolojik analiz yanıtı"""

    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str


@router.post("/morphology/analyze", response_model=MorphologyAnalysisResponse)
async def analyze_morphology(request: MorphologyAnalysisRequest):
    """
    Kelimenin morfolojik analizini yap

    Bu endpoint, verilen Türkçe kelimenin kök, ek, türetim derinliği ve
    karmaşıklık skorunu analiz eder.
    """
    try:
        # NLP servisini başlat
        async with turkish_nlp_service as nlp:
            await nlp.initialize()

            # Morfolojik analiz yap
            analysis = await nlp.analyze_morphology(request.word)

            if analysis:
                return MorphologyAnalysisResponse(
                    success=True,
                    data={
                        "word": analysis.word,
                        "root": analysis.root,
                        "suffixes": analysis.suffixes,
                        "pos_tag": analysis.pos_tag,
                        "derivational_depth": analysis.derivational_depth,
                        "is_compound": analysis.is_compound,
                        "compound_parts": analysis.compound_parts,
                        "complexity_score": analysis.complexity_score,
                    },
                    message="Morfolojik analiz başarıyla tamamlandı",
                )
            else:
                return MorphologyAnalysisResponse(
                    success=False, data=None, message="Kelime analiz edilemedi"
                )

    except Exception as e:
        logger.error(f"Morfolojik analiz API hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/morphology/batch", response_model=BatchMorphologyResponse)
async def batch_morphology_analysis(request: BatchMorphologyRequest):
    """
    Birden fazla kelimenin morfolojik analizini yap

    Bu endpoint, verilen kelime listesinin tamamı için morfolojik analiz yapar.
    """
    try:
        async with turkish_nlp_service as nlp:
            await nlp.initialize()

            results = []

            for word in request.words:
                analysis = await nlp.analyze_morphology(word)

                if analysis:
                    results.append(
                        {
                            "word": analysis.word,
                            "root": analysis.root,
                            "suffixes": analysis.suffixes,
                            "pos_tag": analysis.pos_tag,
                            "derivational_depth": analysis.derivational_depth,
                            "is_compound": analysis.is_compound,
                            "compound_parts": analysis.compound_parts,
                            "complexity_score": analysis.complexity_score,
                        }
                    )
                else:
                    results.append({"word": word, "error": "Analiz edilemedi"})

            return BatchMorphologyResponse(
                success=True,
                data={
                    "analyses": results,
                    "total_words": len(request.words),
                    "successful_analyses": len(
                        [r for r in results if "error" not in r]
                    ),
                },
                message=f"{len(results)} kelimenin morfolojik analizi tamamlandı",
            )

    except Exception as e:
        logger.error(f"Toplu morfolojik analiz API hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/text/normalize", response_model=TextNormalizationResponse)
async def normalize_text(request: TextNormalizationRequest):
    """
    Metni normalize et ve temizle

    Bu endpoint, Türkçe metindeki encoding sorunları, yazım hataları ve
    karakter normalizasyonu işlemlerini gerçekleştirir.
    """
    try:
        async with turkish_nlp_service as nlp:
            await nlp.initialize()

            # Metin normalizasyonu yap
            result = await nlp.normalize_text(request.text)

            return TextNormalizationResponse(
                success=True,
                data={
                    "original_text": result.original_text,
                    "normalized_text": result.normalized_text,
                    "corrections": result.corrections,
                    "encoding_issues_fixed": result.encoding_issues_fixed,
                    "turkish_chars_normalized": result.turkish_chars_normalized,
                    "improvement_summary": {
                        "total_corrections": len(result.corrections),
                        "encoding_fixes": result.encoding_issues_fixed,
                        "character_normalizations": result.turkish_chars_normalized,
                    },
                },
                message="Metin normalizasyonu başarıyla tamamlandı",
            )

    except Exception as e:
        logger.error(f"Metin normalizasyon API hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/text/complexity", response_model=TextComplexityResponse)
async def analyze_text_complexity(request: TextComplexityRequest):
    """
    Metnin karmaşıklığını analiz et

    Bu endpoint, Türkçe metnin genel karmaşıklığını, okunabilirlik skorunu
    ve karmaşık kelimeleri analiz eder.
    """
    try:
        async with turkish_nlp_service as nlp:
            await nlp.initialize()

            # Karmaşıklık analizi yap
            complexity_result = await nlp.analyze_text_complexity(request.text)

            return TextComplexityResponse(
                success=True,
                data=complexity_result,
                message="Metin karmaşıklık analizi başarıyla tamamlandı",
            )

    except Exception as e:
        logger.error(f"Metin karmaşıklık analizi API hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/health")
async def health_check():
    """
    NLP servis sağlık kontrolü

    Bu endpoint, Türkçe NLP servisinin ve Zemberek bağlantısının
    durumunu kontrol eder.
    """
    try:
        async with turkish_nlp_service as nlp:
            zemberek_status = await nlp.initialize()

            return {
                "success": True,
                "data": {
                    "service_status": "healthy",
                    "zemberek_connection": "connected"
                    if zemberek_status
                    else "fallback_mode",
                    "features": {
                        "morphological_analysis": True,
                        "text_normalization": True,
                        "complexity_analysis": True,
                        "batch_processing": True,
                    },
                },
                "message": "Türkçe NLP servisi çalışıyor",
            }

    except Exception as e:
        logger.error(f"NLP servis sağlık kontrolü hatası: {e}")
        return {
            "success": False,
            "data": {"service_status": "unhealthy", "error": str(e)},
            "message": "Türkçe NLP servisinde sorun var",
        }


@router.get("/word/complexity/{word}")
async def get_word_complexity(word: str):
    """
    Tek kelimenin karmaşıklık skorunu al

    Bu endpoint, verilen kelimenin hızlı karmaşıklık skorunu döndürür.
    """
    try:
        if not word or len(word) > 100:
            raise HTTPException(
                status_code=400, detail="Kelime 1-100 karakter arasında olmalıdır"
            )

        async with turkish_nlp_service as nlp:
            complexity_score = nlp.get_word_complexity(word)

            return {
                "success": True,
                "data": {
                    "word": word,
                    "complexity_score": complexity_score,
                    "complexity_level": (
                        "basit"
                        if complexity_score < 0.3
                        else "orta"
                        if complexity_score < 0.7
                        else "karmaşık"
                    ),
                },
                "message": "Kelime karmaşıklığı hesaplandı",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Kelime karmaşıklığı API hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/text/clean")
async def clean_text(request: dict):
    """
    Metni temizle ve düzelt

    Bu endpoint, metindeki gereksiz karakterleri, boşlukları ve
    formatting sorunlarını temizler.
    """
    try:
        text = request.get("text", "")

        if not text:
            raise HTTPException(status_code=400, detail="Metin boş olamaz")

        async with turkish_nlp_service as nlp:
            # Basit metin temizleme
            cleaned_text = nlp._clean_whitespace(text)

            # Encoding sorunlarını düzelt
            cleaned_text, encoding_fixes = nlp._fix_encoding_issues(cleaned_text)

            return {
                "success": True,
                "data": {
                    "original_text": text,
                    "cleaned_text": cleaned_text,
                    "changes_made": {
                        "encoding_fixes": encoding_fixes,
                        "whitespace_cleaned": text != cleaned_text,
                    },
                },
                "message": "Metin temizleme tamamlandı",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metin temizleme API hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )
