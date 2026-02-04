# -*- coding: utf-8 -*-
"""
Zemberek-NLP API Endpoints
Production-ready Türkçe NLP API

Endpoints:
- POST /morphology/analyze - Morfolojik analiz
- POST /morphology/batch - Toplu morfolojik analiz
- POST /tokenize - Tokenization
- POST /spell-check - Yazım kontrolü
- POST /normalize - Metin normalizasyon
- POST /sentences - Cümle ayırma
- GET /stats - Servis istatistikleri
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.auth_dependencies import get_current_user
from core.structured_logger import get_logger
from core.zemberek_service import (
    MorphemeAnalysis,
    POSTag,
    TokenInfo,
    get_zemberek_service,
)
from models.database import User

logger = get_logger(__name__)

router = APIRouter(prefix="/api/zemberek", tags=["Zemberek NLP"])


# ==================== REQUEST/RESPONSE MODELS ====================


class MorphologyRequest(BaseModel):
    """Morfoloji analiz isteği"""

    word: str = Field(
        ..., min_length=1, max_length=100, description="Analiz edilecek Türkçe kelime"
    )


class MorphologyResponse(BaseModel):
    """Morfoloji analiz yanıtı"""

    word: str
    lemma: str
    pos: str
    stem: str
    suffixes: List[str]
    morphemes: List[str]
    morpheme_types: List[str]
    complexity_score: float


class BatchMorphologyRequest(BaseModel):
    """Toplu morfoloji analiz isteği"""

    words: List[str] = Field(
        ..., min_items=1, max_items=100, description="Analiz edilecek kelimeler"
    )


class BatchMorphologyResponse(BaseModel):
    """Toplu morfoloji analiz yanıtı"""

    results: List[MorphologyResponse]
    total_count: int
    success_count: int


class TokenizeRequest(BaseModel):
    """Tokenization isteği"""

    text: str = Field(
        ..., min_length=1, max_length=10000, description="Tokenize edilecek metin"
    )


class TokenResponse(BaseModel):
    """Token yanıtı"""

    text: str
    normalized: str
    is_word: bool
    is_punctuation: bool
    is_number: bool
    position: int


class TokenizeResponse(BaseModel):
    """Tokenization yanıtı"""

    tokens: List[TokenResponse]
    token_count: int
    word_count: int


class SpellCheckRequest(BaseModel):
    """Yazım kontrolü isteği"""

    word: str = Field(
        ..., min_length=1, max_length=100, description="Kontrol edilecek kelime"
    )


class SpellCheckResponse(BaseModel):
    """Yazım kontrolü yanıtı"""

    word: str
    is_correct: bool
    suggestions: List[str]


class NormalizeRequest(BaseModel):
    """Normalizasyon isteği"""

    text: str = Field(
        ..., min_length=1, max_length=10000, description="Normalize edilecek metin"
    )


class NormalizeResponse(BaseModel):
    """Normalizasyon yanıtı"""

    original: str
    normalized: str


class SentenceRequest(BaseModel):
    """Cümle ayırma isteği"""

    text: str = Field(
        ..., min_length=1, max_length=10000, description="Cümlelere ayrılacak metin"
    )


class SentenceResponse(BaseModel):
    """Cümle ayırma yanıtı"""

    sentences: List[str]
    sentence_count: int


# ==================== ENDPOINTS ====================


@router.post("/morphology/analyze", response_model=MorphologyResponse)
async def analyze_morphology(
    request: MorphologyRequest, current_user: User = Depends(get_current_user)
):
    """
    Türkçe kelimenin morfolojik analizini yap

    - Kök/lemma belirleme
    - Ek analizi
    - Kelime türü (POS tag)
    - Karmaşıklık skoru
    """
    try:
        zemberek = await get_zemberek_service()
        analysis = await zemberek.analyze_morphology(request.word)

        logger.info(
            "morphology_analysis_completed",
            word=request.word,
            complexity=analysis.complexity_score,
            user_id=current_user.id,
        )

        return MorphologyResponse(
            word=analysis.surface,
            lemma=analysis.lemma,
            pos=analysis.pos.value,
            stem=analysis.stem,
            suffixes=analysis.suffixes,
            morphemes=analysis.morphemes,
            morpheme_types=[mt.value for mt in analysis.morpheme_types],
            complexity_score=round(analysis.complexity_score, 3),
        )

    except Exception as e:
        logger.error(f"Morphology analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Morfolojik analiz hatası: {str(e)}",
        )


@router.post("/morphology/batch", response_model=BatchMorphologyResponse)
async def batch_morphology_analysis(
    request: BatchMorphologyRequest, current_user: User = Depends(get_current_user)
):
    """
    Birden fazla kelime için morfolojik analiz

    - Paralel işleme
    - Toplu sonuç
    """
    try:
        zemberek = await get_zemberek_service()

        results = []
        success_count = 0

        for word in request.words:
            try:
                analysis = await zemberek.analyze_morphology(word)

                results.append(
                    MorphologyResponse(
                        word=analysis.surface,
                        lemma=analysis.lemma,
                        pos=analysis.pos.value,
                        stem=analysis.stem,
                        suffixes=analysis.suffixes,
                        morphemes=analysis.morphemes,
                        morpheme_types=[mt.value for mt in analysis.morpheme_types],
                        complexity_score=round(analysis.complexity_score, 3),
                    )
                )

                success_count += 1

            except Exception as e:
                logger.error(f"Batch analysis error for word '{word}': {e}")
                # Continue with other words

        logger.info(
            "batch_morphology_completed",
            total=len(request.words),
            success=success_count,
            user_id=current_user.id,
        )

        return BatchMorphologyResponse(
            results=results, total_count=len(request.words), success_count=success_count
        )

    except Exception as e:
        logger.error(f"Batch morphology error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/tokenize", response_model=TokenizeResponse)
async def tokenize_text(
    request: TokenizeRequest, current_user: User = Depends(get_current_user)
):
    """
    Metni token'lara ayır

    - Kelime/noktalama/sayı ayırma
    - Normalizasyon
    - Position tracking
    """
    try:
        zemberek = await get_zemberek_service()
        tokens = await zemberek.tokenize(request.text)

        token_responses = [
            TokenResponse(
                text=token.text,
                normalized=token.normalized,
                is_word=token.is_word,
                is_punctuation=token.is_punctuation,
                is_number=token.is_number,
                position=token.position,
            )
            for token in tokens
        ]

        word_count = sum(1 for t in tokens if t.is_word)

        logger.info(
            "tokenization_completed",
            total_tokens=len(tokens),
            word_count=word_count,
            user_id=current_user.id,
        )

        return TokenizeResponse(
            tokens=token_responses, token_count=len(tokens), word_count=word_count
        )

    except Exception as e:
        logger.error(f"Tokenization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/spell-check", response_model=SpellCheckResponse)
async def spell_check(
    request: SpellCheckRequest, current_user: User = Depends(get_current_user)
):
    """
    Yazım kontrolü

    - Doğru/yanlış tespiti
    - Öneri listesi
    """
    try:
        zemberek = await get_zemberek_service()
        result = await zemberek.spell_check(request.word)

        logger.info(
            "spell_check_completed",
            word=request.word,
            is_correct=result["is_correct"],
            user_id=current_user.id,
        )

        return SpellCheckResponse(
            word=result["word"],
            is_correct=result["is_correct"],
            suggestions=result.get("suggestions", []),
        )

    except Exception as e:
        logger.error(f"Spell check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/normalize", response_model=NormalizeResponse)
async def normalize_text(
    request: NormalizeRequest, current_user: User = Depends(get_current_user)
):
    """
    Metni normalize et

    - Küçük harfe çevirme
    - Türkçe karakter düzeltme
    - Boşluk normalizasyonu
    """
    try:
        zemberek = await get_zemberek_service()
        normalized = await zemberek.normalize_text(request.text)

        logger.info(
            "normalization_completed",
            original_length=len(request.text),
            normalized_length=len(normalized),
            user_id=current_user.id,
        )

        return NormalizeResponse(original=request.text, normalized=normalized)

    except Exception as e:
        logger.error(f"Normalization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/sentences", response_model=SentenceResponse)
async def detect_sentences(
    request: SentenceRequest, current_user: User = Depends(get_current_user)
):
    """
    Cümle sınırlarını tespit et

    - Noktalama bazlı ayırma
    - Türkçe cümle yapısı
    """
    try:
        zemberek = await get_zemberek_service()
        sentences = await zemberek.sentence_boundary_detection(request.text)

        logger.info(
            "sentence_detection_completed",
            sentence_count=len(sentences),
            user_id=current_user.id,
        )

        return SentenceResponse(sentences=sentences, sentence_count=len(sentences))

    except Exception as e:
        logger.error(f"Sentence detection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/stats")
async def get_zemberek_stats(current_user: User = Depends(get_current_user)):
    """
    Zemberek servis istatistikleri

    - Başlatma durumu
    - Fallback modu
    - Mevcut özellikler
    """
    try:
        zemberek = await get_zemberek_service()
        stats = await zemberek.get_service_stats()

        return {
            "success": True,
            "stats": stats,
            "endpoints": {
                "morphology": "/api/zemberek/morphology/analyze",
                "batch_morphology": "/api/zemberek/morphology/batch",
                "tokenize": "/api/zemberek/tokenize",
                "spell_check": "/api/zemberek/spell-check",
                "normalize": "/api/zemberek/normalize",
                "sentences": "/api/zemberek/sentences",
            },
        }

    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/health")
async def health_check():
    """
    Zemberek servis health check
    """
    try:
        zemberek = await get_zemberek_service()
        stats = await zemberek.get_service_stats()

        return {
            "status": "healthy" if stats["initialized"] else "degraded",
            "initialized": stats["initialized"],
            "fallback_mode": stats["use_fallback"],
            "message": "Zemberek service is running",
        }

    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
