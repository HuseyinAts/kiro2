"""
Wave 2B Quality Evaluation API Routes
Production-ready endpoints for quality evaluation
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from core.database import get_db_session
from core.dependencies import AuthenticatedUser, get_current_user
from services.bertscore_evaluator import BERTScoreEvaluator
from services.comprehensive_quality_evaluator import ComprehensiveQualityEvaluator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/quality", tags=["Wave 2B Quality"])

# Global evaluator instance (initialized on startup)
_evaluator: ComprehensiveQualityEvaluator | None = None


# Request/Response Models
class QuestionEvaluationRequest(BaseModel):
    question_text: str = Field(..., min_length=10, max_length=1000)
    difficulty: str | None = Field(None, description="kolay, orta, zor")
    subject: str | None = Field(None, description="Matematik, Fizik, etc.")
    correct_answer: str | None = Field(None, description="A, B, C, D, E")
    evaluation_stage: str = Field(
        "standard", description="quick, standard, thorough, complete"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "question_text": "Bir sayının 3 katı 15'tir. Bu sayı kaçtır?",
                "difficulty": "kolay",
                "subject": "Matematik",
                "evaluation_stage": "standard",
            }
        }
    }


class EvaluationResponse(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=1.0)
    overall_grade: str
    decision: str  # APPROVE, REVIEW, REJECT
    bloom_level: int | None = None
    bloom_confidence: float | None = None
    strengths: list[str] = []
    weaknesses: list[str] = []
    recommendations: list[str] = []
    execution_time_ms: float

    model_config = {
        "json_schema_extra": {
            "example": {
                "overall_score": 0.85,
                "overall_grade": "Good",
                "decision": "APPROVE",
                "bloom_level": 3,
                "bloom_confidence": 0.95,
                "strengths": ["Clear question", "Good length"],
                "weaknesses": [],
                "recommendations": [],
                "execution_time_ms": 1523.5,
            }
        }
    }


class BatchEvaluationRequest(BaseModel):
    questions: list[dict[str, Any]] = Field(..., min_items=1, max_items=50)
    evaluation_stage: str = Field(
        "standard", description="quick, standard, thorough, complete"
    )


class BatchEvaluationResponse(BaseModel):
    total: int
    approved: int
    review: int
    rejected: int
    average_score: float
    results: list[dict[str, Any]]
    execution_time_ms: float


class BERTScoreRequest(BaseModel):
    candidate: str = Field(..., min_length=10)
    reference: str = Field(..., min_length=10)


class BERTScoreResponse(BaseModel):
    f1_score: float
    precision: float
    recall: float
    interpretation: str
    is_similar: bool  # F1 > 0.85


# Helper Functions
async def get_evaluator() -> ComprehensiveQualityEvaluator:
    """Get or initialize the global evaluator"""
    global _evaluator

    if _evaluator is None:
        osym_ref = await load_osym_reference_questions()
        _evaluator = ComprehensiveQualityEvaluator(osym_reference_questions=osym_ref)
        logger.info("ComprehensiveQualityEvaluator initialized")

    return _evaluator


async def load_osym_reference_questions(limit: int = 30) -> list[dict]:
    """Load OSYM reference questions from database"""
    async for db in get_db_session():
        try:
            query = text(
                """
                SELECT
                    question_text,
                    difficulty_level,
                    subject_area,
                    correct_answer
                FROM question_bank
                WHERE is_active = true
                AND correct_answer IS NOT NULL
                AND question_text IS NOT NULL
                AND LENGTH(question_text) > 50
                ORDER BY RANDOM()
                LIMIT :limit
            """
            )

            result = await db.execute(query, {"limit": limit})
            rows = result.fetchall()

            questions = []
            for row in rows:
                questions.append(
                    {
                        "question_text": row[0],
                        "difficulty": row[1],
                        "subject": row[2],
                        "correct_answer": row[3],
                    }
                )

            logger.info(f"Loaded {len(questions)} OSYM reference questions")
            return questions

        except Exception as e:
            logger.error(f"Failed to load OSYM reference: {e}")
            return []


# API Endpoints


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_question(
    request: QuestionEvaluationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Evaluate a single question with Wave 2B quality pipeline."""
    start_time = datetime.now()

    try:
        evaluator = await get_evaluator()

        question = {
            "question_text": request.question_text,
            "difficulty": request.difficulty,
            "subject": request.subject,
            "correct_answer": request.correct_answer,
        }

        evaluation = evaluator.evaluate(question, stage=request.evaluation_stage)
        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return EvaluationResponse(
            overall_score=evaluation.overall_score,
            overall_grade=evaluation.overall_grade,
            decision=evaluation.decision,
            bloom_level=evaluation.bloom_level,
            bloom_confidence=evaluation.bloom_confidence,
            strengths=evaluation.strengths[:5],
            weaknesses=evaluation.weaknesses[:5],
            recommendations=evaluation.recommendations[:5],
            execution_time_ms=round(execution_time, 2),
        )

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/evaluate-batch", response_model=BatchEvaluationResponse)
async def evaluate_batch(
    request: BatchEvaluationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Evaluate multiple questions in batch."""
    start_time = datetime.now()

    try:
        evaluator = await get_evaluator()

        results = []
        stats = {"approved": 0, "review": 0, "rejected": 0, "scores": []}

        for question in request.questions:
            try:
                evaluation = evaluator.evaluate(
                    question, stage=request.evaluation_stage
                )

                stats["scores"].append(evaluation.overall_score)
                if evaluation.decision == "APPROVE":
                    stats["approved"] += 1
                elif evaluation.decision == "REVIEW":
                    stats["review"] += 1
                else:
                    stats["rejected"] += 1

                results.append(
                    {
                        "question_text": question.get("question_text", "")[:100],
                        "overall_score": evaluation.overall_score,
                        "decision": evaluation.decision,
                        "bloom_level": evaluation.bloom_level,
                    }
                )

            except Exception as e:
                logger.error(f"Question evaluation failed: {e}")
                continue

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return BatchEvaluationResponse(
            total=len(request.questions),
            approved=stats["approved"],
            review=stats["review"],
            rejected=stats["rejected"],
            average_score=sum(stats["scores"]) / len(stats["scores"])
            if stats["scores"]
            else 0,
            results=results,
            execution_time_ms=round(execution_time, 2),
        )

    except Exception as e:
        logger.error(f"Batch evaluation failed: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/bertscore", response_model=BERTScoreResponse)
async def calculate_bertscore(
    request: BERTScoreRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Calculate BERTScore semantic similarity between two questions."""
    try:
        evaluator = BERTScoreEvaluator()

        if not evaluator.is_available():
            raise HTTPException(
                status_code=503,
                detail="BERTScore not available. Check HuggingFace token.",
            )

        result = evaluator.evaluate_single(request.candidate, request.reference)

        if not result:
            raise HTTPException(status_code=500, detail="BERTScore calculation failed")

        return BERTScoreResponse(
            f1_score=result["f1"],
            precision=result["precision"],
            recall=result["recall"],
            interpretation=result["interpretation"],
            is_similar=result["f1"] > 0.85,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"BERTScore calculation failed: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for Wave 2B services."""
    try:
        evaluator = await get_evaluator()
        bertscore = BERTScoreEvaluator()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "comprehensive_evaluator": True,
                "bertscore": bertscore.is_available(),
                "bloom_classifier": True,
                "osym_benchmark": len(evaluator._osym_questions) > 0
                if evaluator._osym_questions
                else False,
            },
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@router.get("/stats")
async def get_evaluation_stats():
    """Get current evaluation statistics and configuration."""
    try:
        evaluator = await get_evaluator()

        return {
            "version": "Wave 2B v1.0",
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "bloom_enabled": True,
                "bertscore_enabled": BERTScoreEvaluator().is_available(),
                "benchmark_enabled": len(evaluator._osym_questions) > 0
                if evaluator._osym_questions
                else False,
                "osym_reference_count": len(evaluator._osym_questions)
                if evaluator._osym_questions
                else 0,
            },
            "thresholds": {
                "excellent": ">= 0.90",
                "good": ">= 0.80",
                "acceptable": ">= 0.70",
                "needs_improvement": "< 0.70",
            },
        }

    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


# Startup event to initialize evaluator
async def initialize_wave2b():
    """Initialize Wave 2B evaluator on startup"""
    try:
        await get_evaluator()
        logger.info("Wave 2B Quality API initialized successfully")
    except Exception as e:
        logger.error(f"Wave 2B initialization failed: {e}")
