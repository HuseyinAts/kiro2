"""
Hybrid Question Generation API
ÖSYM-Guided AI Question Generation Endpoints

Methods:
1. osym_guided - Few-shot with 3 ÖSYM examples (default, recommended)
2. ensemble - Multi-model generation, pick best (high quality)
3. progressive - Fine-tuned if available, else few-shot (future)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.dependencies import (
    get_current_user,  # fixed: was auth_dependencies (no blacklist)
)
from core.structured_logger import get_logger
from models.database import User

# Import hybrid generator
from services.hybrid_question_generator import HybridQuestionGenerator

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/questions/hybrid", tags=["Hybrid Question Generation"]
)


# ==================== REQUEST/RESPONSE MODELS ====================


class HybridQuestionRequest(BaseModel):
    """Hibrit soru üretim isteği"""

    subject: str = Field(..., description="Ders adı (Matematik, Fizik, Türkçe, vb.)")
    topic: str = Field(..., description="Konu başlığı (Türev,Limit, vb.)")
    difficulty: str = Field(
        default="orta", description="Zorluk seviyesi (kolay, orta, zor)"
    )
    exam_type: str = Field(default="TYT", description="Sınav tipi (TYT, AYT, YDT)")
    method: str = Field(
        default="osym_guided",
        description="Generation method: osym_guided (default), ensemble, progressive",
    )
    provider: str = Field(
        default="claude",
        description="AI provider for osym_guided: claude (default), openai",
    )
    validate: bool = Field(default=True, description="Run quality validation checks")
    enable_wave2b: bool = Field(
        default=False,
        description="✨ Enable Wave 2B quality evaluation (BERTScore + Bloom + ÖSYM Benchmark)",
    )
    wave2b_threshold: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
        description="Minimum quality threshold for Wave 2B (0.0-1.0)",
    )


class HybridQuestionResponse(BaseModel):
    """Hibrit soru üretim yanıtı"""

    success: bool
    question: dict
    method_used: str
    generation_time_seconds: float
    quality_metrics: dict


class BulkHybridRequest(BaseModel):
    """Toplu hibrit soru isteği"""

    subject: str
    topics: list[str]
    count_per_topic: int = Field(default=5, ge=1, le=20)
    difficulty: str = Field(default="orta")
    exam_type: str = Field(default="TYT")
    method: str = Field(default="osym_guided")
    enable_wave2b: bool = Field(
        default=False, description="✨ Enable Wave 2B quality evaluation"
    )


# ==================== ENDPOINTS ====================


@router.post("/generate", response_model=HybridQuestionResponse)
async def generate_hybrid_question(
    request: HybridQuestionRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Hibrit soru üretimi - ÖSYM kalitesinde AI soruları

    **Methods**:
    - `osym_guided`: 3 ÖSYM örneği ile few-shot (önerilen) ⭐
    - `ensemble`: Multi-model, en iyisini seç (yüksek kalite)
    - `progressive`: Fine-tuned model varsa kullan, yoksa few-shot

    **Features**:
    - ÖSYM style compliance (0.85-0.90)
    - IRT parameter validation
    - Turkish morphology check
    - Quality scoring (5 metrics)

    **Example**:
    ```json
    {
        "subject": "Matematik",
        "topic": "Türev Alma Kuralları",
        "difficulty": "orta",
        "exam_type": "TYT",
        "method": "osym_guided",
        "provider": "claude"
    }
    ```
    """
    import os
    import time

    from sqlalchemy import text

    start_time = time.time()

    # Fail fast with a structured 503 when the upstream LLM dependency is
    # missing. Without this, the generator raises deep inside and the bare
    # except at the bottom re-wraps as a generic 500 (GF22/GF56/GF57 pattern).
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="Hibrit soru üretimi şu an kullanılamıyor (LLM API key yapılandırılmamış).",
        )

    try:
        # Load ÖSYM reference questions if Wave 2B is enabled
        osym_reference = None
        if request.enable_wave2b:
            try:
                query = text(
                    """
                    SELECT metin as question_text, zorluk as difficulty,
                           konu as subject, dogru_cevap as correct_answer
                    FROM sorular
                    WHERE dogru_cevap IS NOT NULL AND metin IS NOT NULL
                    AND LENGTH(metin) > 100
                    ORDER BY RANDOM()
                    LIMIT 30
                """
                )
                result = await session.execute(query)
                rows = result.fetchall()
                osym_reference = [
                    {
                        "question_text": row[0],
                        "difficulty": row[1],
                        "subject": row[2],
                        "correct_answer": row[3],
                    }
                    for row in rows
                ]
                logger.info(
                    f"Loaded {len(osym_reference)} ÖSYM reference questions for Wave 2B"
                )
            except Exception as e:
                logger.warning(f"Failed to load ÖSYM reference: {e}")

        # Initialize hybrid generator
        generator = HybridQuestionGenerator(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            enable_wave2b=request.enable_wave2b,
            wave2b_threshold=request.wave2b_threshold,
            osym_reference_questions=osym_reference,
        )

        # Generate based on method
        if request.method == "osym_guided":
            logger.info(
                "Generating ÖSYM-guided question",
                user_id=current_user.id,
                subject=request.subject,
                topic=request.topic,
                provider=request.provider,
            )

            question = await generator.generate_osym_quality_question(
                subject=request.subject,
                topic=request.topic,
                difficulty=request.difficulty,
                exam_type=request.exam_type,
                provider=request.provider,
                validate=request.validate,
            )

        elif request.method == "ensemble":
            logger.info(
                "Generating ensemble question",
                user_id=current_user.id,
                subject=request.subject,
            )

            question = await generator.generate_ensemble(
                subject=request.subject,
                topic=request.topic,
                difficulty=request.difficulty,
                exam_type=request.exam_type,
            )

        elif request.method == "progressive":
            logger.info(
                "Generating progressive question",
                user_id=current_user.id,
                subject=request.subject,
            )

            question = await generator.generate_progressive(
                subject=request.subject,
                topic=request.topic,
                difficulty=request.difficulty,
                exam_type=request.exam_type,
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid method: {request.method}. Use: osym_guided, ensemble, or progressive",
            )

        generation_time = time.time() - start_time

        # Extract quality metrics
        quality_metrics = {
            "osym_compliance": question.get("osym_compliance_score", 0.0),
            "overall_quality": question.get("quality_score", 0.0),
            "grammar_score": question.get("grammar_score", 0.0),
            "irt_difficulty": question.get("irt_difficulty", 0.0),
            "irt_discrimination": question.get("irt_discrimination", 0.0),
            "morphology_complexity": question.get("morphology_complexity", 0.0),
            "readability_score": question.get("readability_score", 0.0),
            "is_valid": question.get("is_valid", True),
            "issues": question.get("validation_issues", []),
        }

        # Add Wave 2B metrics if available
        if request.enable_wave2b and question.get("wave2b_evaluation"):
            wave2b = question["wave2b_evaluation"]
            quality_metrics["wave2b"] = {
                "enabled": True,
                "overall_score": wave2b.get("overall_score", 0.0),
                "overall_grade": wave2b.get("overall_grade", "N/A"),
                "decision": wave2b.get("decision", "N/A"),
                "bloom_level": wave2b.get("bloom_level"),
                "bloom_confidence": wave2b.get("bloom_confidence", 0.0),
                "strengths": wave2b.get("strengths", []),
                "weaknesses": wave2b.get("weaknesses", []),
                "bertscore_f1": wave2b.get("bertscore_f1"),
                "benchmark_similarity": wave2b.get("benchmark_similarity"),
            }
        else:
            quality_metrics["wave2b"] = {"enabled": False}

        logger.info(
            "Hybrid question generated successfully",
            user_id=current_user.id,
            method=request.method,
            quality=quality_metrics["overall_quality"],
            time_seconds=generation_time,
        )

        return HybridQuestionResponse(
            success=True,
            question=question,
            method_used=request.method,
            generation_time_seconds=round(generation_time, 2),
            quality_metrics=quality_metrics,
        )

    except HTTPException:
        # Propagate 400/503 raised above (and any inner HTTPException) as-is;
        # bare except previously re-wrapped them as 500 (GF22/GF77 pattern).
        raise
    except Exception as e:
        logger.error(
            f"Hybrid question generation error: {e}",
            user_id=current_user.id,
            method=request.method,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/generate-bulk")
async def generate_bulk_hybrid_questions(
    request: BulkHybridRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Toplu hibrit soru üretimi

    Birden fazla konu için aynı anda soru üretir.

    **Example**:
    ```json
    {
        "subject": "Matematik",
        "topics": ["Türev", "Limit", "İntegral"],
        "count_per_topic": 5,
        "difficulty": "orta",
        "method": "osym_guided"
    }
    ```

    **Returns**: 15 soru (5 x 3 topic)
    """
    import os
    import time

    from sqlalchemy import text

    start_time = time.time()

    try:
        # Load ÖSYM reference if Wave 2B enabled
        osym_reference = None
        if request.enable_wave2b:
            try:
                query = text(
                    """
                    SELECT metin as question_text, zorluk as difficulty,
                           konu as subject, dogru_cevap as correct_answer
                    FROM sorular
                    WHERE dogru_cevap IS NOT NULL AND metin IS NOT NULL
                    AND LENGTH(metin) > 100
                    ORDER BY RANDOM()
                    LIMIT 30
                """
                )
                result = await session.execute(query)
                rows = result.fetchall()
                osym_reference = [
                    {
                        "question_text": row[0],
                        "difficulty": row[1],
                        "subject": row[2],
                        "correct_answer": row[3],
                    }
                    for row in rows
                ]
                logger.info(
                    f"Loaded {len(osym_reference)} ÖSYM references for bulk generation"
                )
            except Exception as e:
                logger.warning(f"Failed to load ÖSYM reference: {e}")

        generator = HybridQuestionGenerator(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            enable_wave2b=request.enable_wave2b,
            osym_reference_questions=osym_reference,
        )

        all_questions = []
        topic_results = {}

        # Generate for each topic
        for topic in request.topics:
            logger.info(f"Generating {request.count_per_topic} questions for {topic}")

            topic_questions = []
            for i in range(request.count_per_topic):
                try:
                    question = await generator.generate_osym_quality_question(
                        subject=request.subject,
                        topic=topic,
                        difficulty=request.difficulty,
                        exam_type=request.exam_type,
                        provider="claude",
                        validate=True,
                    )
                    topic_questions.append(question)
                    all_questions.append(question)

                except Exception as e:
                    logger.error(
                        f"Failed to generate question {i + 1} for {topic}: {e}"
                    )
                    continue

            topic_results[topic] = {
                "requested": request.count_per_topic,
                "generated": len(topic_questions),
                "success_rate": len(topic_questions) / request.count_per_topic,
            }

        generation_time = time.time() - start_time

        # Calculate average quality
        avg_quality = (
            sum(q.get("quality_score", 0) for q in all_questions) / len(all_questions)
            if all_questions
            else 0
        )
        avg_osym = (
            sum(q.get("osym_compliance_score", 0) for q in all_questions)
            / len(all_questions)
            if all_questions
            else 0
        )

        logger.info(
            "Bulk generation complete",
            user_id=current_user.id,
            total_questions=len(all_questions),
            avg_quality=avg_quality,
            time_seconds=generation_time,
        )

        return {
            "success": True,
            "questions": all_questions,
            "total_generated": len(all_questions),
            "total_requested": len(request.topics) * request.count_per_topic,
            "success_rate": len(all_questions)
            / (len(request.topics) * request.count_per_topic),
            "by_topic": topic_results,
            "average_quality": round(avg_quality, 2),
            "average_osym_compliance": round(avg_osym, 2),
            "generation_time_seconds": round(generation_time, 2),
        }

    except Exception as e:
        logger.error(f"Bulk generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/methods")
async def get_generation_methods():
    """
    Available generation methods

    Returns information about each method
    """
    return {
        "methods": {
            "osym_guided": {
                "name": "ÖSYM-Guided Few-Shot",
                "description": "Uses 3 ÖSYM examples for AI generation",
                "recommended": True,
                "quality": "8.5-9.0/10",
                "speed": "3-5 seconds",
                "cost": "$0.008/question",
                "osym_compliance": "0.85-0.90",
                "features": [
                    "RAG: Retrieves similar ÖSYM questions",
                    "Style analysis: ÖSYM pattern matching",
                    "IRT validation",
                    "Turkish morphology check",
                ],
            },
            "ensemble": {
                "name": "Multi-Model Ensemble",
                "description": "Generates with multiple models, picks best",
                "recommended": False,
                "quality": "9.0/10",
                "speed": "10-15 seconds",
                "cost": "$0.025/question",
                "osym_compliance": "0.90",
                "features": [
                    "Claude + GPT-4 generation",
                    "Quality comparison",
                    "Best question selection",
                ],
            },
            "progressive": {
                "name": "Progressive Learning",
                "description": "Fine-tuned model if available, else few-shot",
                "recommended": False,
                "quality": "9.5/10 (when fine-tuned)",
                "speed": "2-3 seconds (fine-tuned)",
                "cost": "$0.005/question (fine-tuned)",
                "osym_compliance": "0.95 (fine-tuned)",
                "features": [
                    "Uses fine-tuned model when available",
                    "Fallback to few-shot",
                    "Future implementation",
                ],
            },
        },
        "default": "osym_guided",
    }


@router.get("/stats")
async def get_hybrid_generation_stats(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Hibrit soru üretim istatistikleri

    Returns statistics about hybrid question generation
    """
    try:
        # TODO: Implement actual database queries
        # For now, return mock stats

        return {
            "total_generated": 0,
            "by_method": {"osym_guided": 0, "ensemble": 0, "progressive": 0},
            "by_subject": {},
            "average_quality": 0.0,
            "average_osym_compliance": 0.0,
            "average_generation_time": 0.0,
        }

    except Exception as e:
        logger.error(f"Error fetching hybrid stats: {e}")
        return {"total_generated": 0, "error": str(e)}
