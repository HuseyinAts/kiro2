"""
Photo Ask Service — F3 "Fotoğrafla Sor"
Pipeline: Upload → OCR → Embedding → pgvector similarity → AI fallback solution.

Reuses existing infrastructure:
- unified_ocr_service.py for OCR text extraction
- Ollama nomic-embed-text for embeddings
- pgvector HNSW for similarity search on question_bank
- LLMService (Qwen3) for AI-generated solutions when no match found
"""

import os
import time
import unicodedata
import uuid
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from core.quality_gate import safe_for_beta_sql
from core.structured_logger import get_logger

logger = get_logger("photo_ask_service")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
UPLOAD_DIR = Path(os.getenv("PHOTO_ASK_UPLOAD_DIR", "uploads/photo_ask"))

# Similarity thresholds
HIGH_SIMILARITY = 0.75  # Strong match — show directly
MIN_SIMILARITY = 0.40  # Minimum to consider as a potential match


async def save_upload(file_content: bytes, filename: str) -> Path:
    """Save uploaded image to disk. Returns the saved file path."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(filename).suffix or ".jpg"
    saved_name = f"{uuid.uuid4().hex}{ext}"
    saved_path = UPLOAD_DIR / saved_name
    saved_path.write_bytes(file_content)
    return saved_path


async def extract_text_from_image(image_path: Path) -> dict[str, Any]:
    """Extract text from image using OCR.

    Tries unified_ocr_service first (EasyOCR), falls back to basic OCR.
    Returns dict with 'text', 'confidence', 'processing_time_ms'.
    """
    start = time.monotonic()

    try:
        from services.unified_ocr_service import get_ocr_service

        ocr = get_ocr_service()
        result = await ocr.extract_text(str(image_path))
        elapsed_ms = int((time.monotonic() - start) * 1000)

        if isinstance(result, dict):
            return {
                "text": result.get("text", ""),
                "confidence": result.get("confidence", 0.0),
                "processing_time_ms": elapsed_ms,
            }
        # If result is a string
        return {
            "text": str(result),
            "confidence": 0.8,
            "processing_time_ms": elapsed_ms,
        }
    except ImportError:
        logger.warning("unified_ocr_service not available, using basic OCR")
    except Exception as e:
        logger.warning(f"Unified OCR failed: {e}, trying basic OCR")

    # Fallback: basic OCR service
    try:
        from services.ocr_service import OCRService

        ocr = OCRService()
        result = ocr.perform_ocr(str(image_path), language="tur+eng")
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {
            "text": result.get("text", ""),
            "confidence": result.get("confidence", 0.0),
            "processing_time_ms": elapsed_ms,
        }
    except Exception as e:
        logger.error(f"All OCR methods failed: {e}", exc_info=True)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {"text": "", "confidence": 0.0, "processing_time_ms": elapsed_ms}


async def find_similar_questions(
    *,
    db: AsyncSession,
    ocr_text: str,
    top_k: int = 5,
    min_similarity: float = MIN_SIMILARITY,
    subject_area: str | None = None,
) -> list[dict[str, Any]]:
    """Find similar questions in question_bank using pgvector similarity search.

    Steps:
    1. Normalize OCR text (NFC + Turkish)
    2. Generate embedding via Ollama nomic-embed-text
    3. Query pgvector HNSW index for nearest neighbors
    """
    if not ocr_text or len(ocr_text.strip()) < 10:
        return []

    # NFC normalize
    query_text = unicodedata.normalize("NFC", ocr_text.strip())
    prefixed = f"search_query: {query_text}"

    # Generate embedding
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/embed",
                json={"model": "nomic-embed-text", "input": prefixed},
            )
            resp.raise_for_status()
            result = resp.json()
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}", exc_info=True)
        return []

    embeddings = result.get("embeddings")
    if not embeddings or not isinstance(embeddings, list) or len(embeddings) == 0:
        logger.error("Embedding model returned invalid response")
        return []

    query_embedding = embeddings[0]
    vec_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    # Build pgvector query
    # Kalite kapısı (core/quality_gate.py) — kapısız sorgu 85.731 yargılanmamış/
    # reddedilmiş soruyu öğrenciye servis ediyordu. Burada dönen dict
    # correct_answer + explanation içerdiği için sızıntı doğrudan çözüm veriyor.
    # is_active YANINA gelir, yerine değil (bayat matview'a karşı canlı güvence).
    filters = [
        "q.embedding IS NOT NULL",
        "q.is_active = true",
        safe_for_beta_sql("q.id"),
    ]
    params: dict[str, Any] = {"emb": vec_str, "min_sim": min_similarity, "top_k": top_k}

    if subject_area:
        filters.append("q.subject_area = :subject_area")
        params["subject_area"] = subject_area.upper()

    where_clause = " AND ".join(filters)

    sql = sa_text(f"""
        SELECT q.id, q.question_text, q.question_image_url,
               q.exam_type, q.subject_area, q.source_book,
               q.difficulty_level, q.correct_answer,
               q.option_a, q.option_b, q.option_c, q.option_d, q.option_e,
               q.explanation,
               1 - (q.embedding <=> CAST(:emb AS vector)) as similarity
        FROM question_bank q
        WHERE {where_clause}
          AND 1 - (q.embedding <=> CAST(:emb AS vector)) >= :min_sim
        ORDER BY q.embedding <=> CAST(:emb AS vector)
        LIMIT :top_k
    """)

    result_rows = await db.execute(sql, params)
    rows = result_rows.fetchall()

    return [
        {
            "id": str(r.id),
            "question_text": r.question_text,
            "question_image_url": r.question_image_url,
            "exam_type": r.exam_type,
            "subject_area": r.subject_area,
            "source_book": r.source_book,
            "difficulty": r.difficulty_level,
            "correct_answer": r.correct_answer,
            "options": {
                "A": r.option_a,
                "B": r.option_b,
                "C": r.option_c,
                "D": r.option_d,
                "E": r.option_e,
            },
            "explanation": r.explanation,
            "similarity": round(float(r.similarity), 4),
        }
        for r in rows
    ]


async def generate_ai_solution(ocr_text: str) -> dict[str, Any]:
    """Generate AI solution for an unmatched question using LLM.

    Used as fallback when pgvector finds no similar questions.
    """
    try:
        from core.llm_service import LLMService

        llm = LLMService()
        prompt = (
            "Aşağıdaki soruyu adım adım çöz. Türkçe yanıt ver.\n\n"
            f"Soru:\n{ocr_text}\n\n"
            "Çözüm:"
        )

        if not llm._client:
            llm._client = httpx.AsyncClient(timeout=llm.timeout)

        resp = await llm._client.post(
            f"{llm.base_url}/api/generate",
            json={
                "model": llm.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 1024},
            },
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "solution": data.get("response", ""),
            "model": llm.model,
            "generated": True,
        }
    except Exception as e:
        logger.error(f"AI solution generation failed: {e}", exc_info=True)
        return {
            "solution": "",
            "model": "unavailable",
            "generated": False,
            "error": "AI çözüm servisi şu an kullanılamıyor",
        }


async def process_photo_ask(
    *,
    db: AsyncSession,
    file_content: bytes,
    filename: str,
    subject_area: str | None = None,
    student_id: str,
) -> dict[str, Any]:
    """Full photo-ask pipeline: save → OCR → search → (AI fallback).

    Returns:
        Dict with ocr_text, matched_questions, ai_solution (if no match),
        and processing metadata.
    """
    start = time.monotonic()

    # 1. Save upload
    saved_path = await save_upload(file_content, filename)

    # 2. OCR
    ocr_result = await extract_text_from_image(saved_path)
    ocr_text = ocr_result["text"]

    if not ocr_text or len(ocr_text.strip()) < 10:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {
            "status": "ocr_failed",
            "ocr_text": ocr_text,
            "ocr_confidence": ocr_result["confidence"],
            "matched_questions": [],
            "ai_solution": None,
            "total_time_ms": elapsed_ms,
            "message": "Görselden yeterli metin çıkarılamadı. Daha net bir fotoğraf deneyin.",
        }

    # 3. Similarity search
    matches = await find_similar_questions(
        db=db,
        ocr_text=ocr_text,
        top_k=5,
        subject_area=subject_area,
    )

    # 4. Determine response
    ai_solution = None
    has_strong_match = any(m["similarity"] >= HIGH_SIMILARITY for m in matches)

    if not matches:
        # No match — try AI solution
        ai_solution = await generate_ai_solution(ocr_text)
        response_status = "ai_solved"
        message = "Benzer soru bulunamadı. AI çözüm üretildi."
    elif has_strong_match:
        response_status = "matched"
        message = f"{len(matches)} benzer soru bulundu."
    else:
        # Weak matches — show them + provide AI solution
        ai_solution = await generate_ai_solution(ocr_text)
        response_status = "partial_match"
        message = f"{len(matches)} olası eşleşme bulundu (düşük benzerlik)."

    elapsed_ms = int((time.monotonic() - start) * 1000)

    logger.info(
        "Photo ask processed",
        extra_data={
            "student_id": student_id,
            "status": response_status,
            "ocr_confidence": ocr_result["confidence"],
            "match_count": len(matches),
            "top_similarity": matches[0]["similarity"] if matches else 0.0,
            "total_time_ms": elapsed_ms,
        },
    )

    return {
        "status": response_status,
        "ocr_text": ocr_text,
        "ocr_confidence": ocr_result["confidence"],
        "ocr_time_ms": ocr_result["processing_time_ms"],
        "matched_questions": matches,
        "ai_solution": ai_solution,
        "total_time_ms": elapsed_ms,
        "message": message,
    }
