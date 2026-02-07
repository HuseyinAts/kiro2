"""
Zemberek NLP REST API Server
Port 8081 - Turkish NLP Service
Teknofest 2025 - Eğitim Eylemci Projesi
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Zemberek imports
try:
    from zemberek import (
        TurkishMorphology,
        TurkishSentenceNormalizer,
        TurkishSentenceExtractor,
        TurkishTokenizer,
    )

    ZEMBEREK_AVAILABLE = True
except ImportError as e:
    ZEMBEREK_AVAILABLE = False
    ZEMBEREK_ERROR = str(e)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Zemberek NLP API",
    description="Turkish Natural Language Processing Service",
    version="1.0.0",
)

# Initialize Zemberek components
morphology = None
normalizer = None
sentence_extractor = None
tokenizer = None

if ZEMBEREK_AVAILABLE:
    try:
        morphology = TurkishMorphology.create_with_defaults()
        normalizer = TurkishSentenceNormalizer(morphology)
        sentence_extractor = TurkishSentenceExtractor()
        tokenizer = TurkishTokenizer.DEFAULT
        logger.info("[Zemberek] All components initialized successfully")
    except Exception as e:
        logger.error(f"[Zemberek] Failed to initialize: {e}")
        ZEMBEREK_AVAILABLE = False
        ZEMBEREK_ERROR = str(e)


# Request/Response models
class TextRequest(BaseModel):
    text: str


class TokenizeRequest(BaseModel):
    text: str


class NormalizeRequest(BaseModel):
    text: str


class MorphologyRequest(BaseModel):
    word: str


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if ZEMBEREK_AVAILABLE else "degraded",
        "zemberek_available": ZEMBEREK_AVAILABLE,
        "error": ZEMBEREK_ERROR if not ZEMBEREK_AVAILABLE else None,
        "port": 8081,
    }


# Tokenization
@app.post("/tokenize")
async def tokenize_text(request: TokenizeRequest):
    """Tokenize Turkish text"""
    if not ZEMBEREK_AVAILABLE:
        raise HTTPException(status_code=503, detail="Zemberek not available")

    try:
        tokens = tokenizer.tokenize(request.text)
        return {
            "text": request.text,
            "tokens": [token.content for token in tokens],
            "count": len(tokens),
        }
    except Exception as e:
        logger.error(f"[Tokenize] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Normalization
@app.post("/normalize")
async def normalize_text(request: NormalizeRequest):
    """Normalize Turkish text (spelling, informal -> formal)"""
    if not ZEMBEREK_AVAILABLE:
        raise HTTPException(status_code=503, detail="Zemberek not available")

    try:
        normalized = normalizer.normalize(request.text)
        return {"original": request.text, "normalized": normalized}
    except Exception as e:
        logger.error(f"[Normalize] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Morphological analysis
@app.post("/analyze")
async def analyze_morphology(request: MorphologyRequest):
    """Morphological analysis of Turkish word"""
    if not ZEMBEREK_AVAILABLE:
        raise HTTPException(status_code=503, detail="Zemberek not available")

    try:
        analyses = morphology.analyze(request.word)

        results = []
        for analysis in analyses:
            results.append(
                {
                    "surface": request.word,
                    "lemma": str(analysis.get_lemmas()[0])
                    if analysis.get_lemmas()
                    else None,
                    "pos": str(analysis.get_pos()),
                    "morphemes": [str(m) for m in analysis.get_morphemes()],
                    "formatted": str(analysis),
                }
            )

        return {"word": request.word, "analyses": results, "count": len(results)}
    except Exception as e:
        logger.error(f"[Analyze] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Sentence extraction
@app.post("/sentences")
async def extract_sentences(request: TextRequest):
    """Extract sentences from Turkish text"""
    if not ZEMBEREK_AVAILABLE:
        raise HTTPException(status_code=503, detail="Zemberek not available")

    try:
        sentences = sentence_extractor.from_paragraph(request.text)
        return {"text": request.text, "sentences": sentences, "count": len(sentences)}
    except Exception as e:
        logger.error(f"[Sentences] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Root endpoint
@app.get("/")
async def root():
    """API information"""
    return {
        "service": "Zemberek NLP API",
        "version": "1.0.0",
        "status": "running" if ZEMBEREK_AVAILABLE else "degraded",
        "endpoints": {
            "GET /health": "Health check",
            "POST /tokenize": "Tokenize text",
            "POST /normalize": "Normalize text",
            "POST /analyze": "Morphological analysis",
            "POST /sentences": "Extract sentences",
        },
        "zemberek_available": ZEMBEREK_AVAILABLE,
    }


def main():
    """Start the Zemberek NLP server"""
    port = int(os.getenv("ZEMBEREK_PORT", "8081"))
    host = os.getenv("ZEMBEREK_HOST", "0.0.0.0")

    logger.info(f"[Zemberek NLP Server] Starting on {host}:{port}")
    logger.info(f"[Zemberek NLP Server] Zemberek available: {ZEMBEREK_AVAILABLE}")

    if not ZEMBEREK_AVAILABLE:
        logger.warning(
            f"[Zemberek NLP Server] Zemberek not available: {ZEMBEREK_ERROR}"
        )
        logger.warning(
            "[Zemberek NLP Server] Server will start but with limited functionality"
        )

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
