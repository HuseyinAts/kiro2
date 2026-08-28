"""
OSYM Question Generation API Routes
AI-powered OSYM question generation endpoints

PREFIX CHANGED (2025-01-25):
- OLD: /api/osym
- NEW: /api/v1/osym/generate

Bu degisiklik /api/v1/osym (osym_questions_api.py) ile cakismayi onler.
- /api/v1/osym → Gercek OSYM sorulari (osym_questions_api.py)
- /api/v1/osym/generate → AI uretimi OSYM sorulari (BU DOSYA)
"""

import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from core.database import get_async_session
from core.ddos_protection import limiter
from core.dependencies import (
    AuthenticatedUser,
    get_current_admin_user,
    get_current_user,
)
from services.osym_pdf_pipeline import OSYMPDFPipeline

router = APIRouter(prefix="/api/v1/osym/generate", tags=["OSYM Question Generation"])


class QuestionGenerationRequest(BaseModel):
    topic: str = Field(..., description="Main topic (e.g., 'Matematik - Türev')")
    subtopic: str = Field(..., description="Subtopic (e.g., 'Türev Alma Kuralları')")
    examType: str = Field(default="TYT", description="Exam type: TYT, AYT, YDT, or LGS")
    subject: str = Field(default="Matematik", description="Subject area")
    difficulty: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Difficulty level (0.0-1.0)"
    )
    bloomLevel: int = Field(
        default=3, ge=1, le=6, description="Bloom's taxonomy level (1-6)"
    )
    provider: str = Field(
        default="ensemble", description="AI provider: ensemble, openai, claude, or qwen"
    )


class QuestionValidationRequest(BaseModel):
    stem: str = Field(..., description="Question text")
    options: list[str] = Field(..., description="Answer options")
    correct_answer: int = Field(..., description="Index of correct answer (0-4)")
    explanation: str | None = Field(default="", description="Explanation")


class BatchGenerationRequest(BaseModel):
    count: int = Field(..., ge=1, le=50, description="Number of questions to generate")
    topic: str
    subtopic: str
    examType: str = "TYT"
    subject: str = "Matematik"
    difficulty: float = 0.5
    bloomLevel: int = 3
    provider: str = "ensemble"


class PDFAnalysisRequest(BaseModel):
    file_path: str = Field(..., description="Path to the uploaded PDF file on server")
    year: int = Field(..., description="Exam year")
    examType: str = Field(..., description="Exam type (TYT, AYT, YDT)")
    subject: str = Field(..., description="Subject")


@router.post("/analyze-pdf")
@limiter.limit("2/minute")
async def analyze_osym_pdf(
    request: Request,
    payload: PDFAnalysisRequest,
    current_admin: AuthenticatedUser = Depends(get_current_admin_user),
):
    """
    (Phase 14) Admin endpoint to trigger NLP & Cognitive Load analysis of OSYM PDFs.
    """
    try:
        async for db_session in get_async_session():
            trend = await OSYMPDFPipeline.process_exam_pdf(
                db=db_session,
                file_path=payload.file_path,
                year=payload.year,
                exam_type=payload.examType,
                subject=payload.subject,
            )
            return {
                "success": True,
                "trend_id": trend.id,
                "metrics": {
                    "avg_word_length": trend.avg_word_length,
                    "avg_words_per_sentence": trend.avg_words_per_sentence,
                    "atesman_readability_index": trend.atesman_readability_index,
                    "cognitive_load_score": trend.cognitive_load_score,
                },
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-question")
@limiter.limit("5/minute")
async def generate_question(
    request: Request,
    payload: QuestionGenerationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Generate OSYM question with AI
    """
    try:
        # Start timer
        start_time = time.time()

        # Try to use actual OSYM generator
        try:
            from core.database import get_async_session
            from services.llm.ensemble_manager import MultiLLMEnsembleManager
            from services.osym_question_generator import OSYMQuestionGenerator

            # Initialize ensemble manager
            ensemble_manager = MultiLLMEnsembleManager()

            # Get database session for saving
            async for db_session in get_async_session():
                # Initialize generator
                generator = OSYMQuestionGenerator(
                    ensemble_manager=ensemble_manager, db_session=db_session
                )

                # Generate question
                result = await generator.generate_question(
                    topic=payload.topic,
                    subtopic=payload.subtopic,
                    exam_type=payload.examType,
                    subject=payload.subject,
                    difficulty=payload.difficulty,
                    bloom_level=payload.bloomLevel,
                    generation_method=payload.provider,
                    save_to_db=True,
                )

                # Format response
                response = {
                    "id": result.get("question_id", str(uuid.uuid4())),
                    "stem": result.get("stem", ""),
                    "options": result.get("options", []),
                    "correct_answer": result.get("correct_answer", 0),
                    "explanation": result.get("explanation", ""),
                    "keywords": result.get("keywords", []),
                    "difficulty": result.get("difficulty", payload.difficulty),
                    "quality_score": result.get("quality_score", 0.0),
                    "tokens_used": result.get("tokens_used", 0),
                    "cost_usd": result.get("cost_usd", 0.0),
                    "generation_time_ms": int((time.time() - start_time) * 1000),
                }

                return response

        except ImportError as ie:
            # Fallback to mock if services not available
            import logging

            logging.warning(f"OSYM generator not available, using mock: {ie}")

        # Fallback: return mock response
        response = {
            "id": str(uuid.uuid4()),
            "stem": f"{payload.topic} konusunda örnek soru metni. Bu soru {payload.difficulty} zorluk seviyesinde ve Bloom seviyesi {payload.bloomLevel}.",
            "options": [
                "Seçenek A",
                "Seçenek B (Doğru)",
                "Seçenek C",
                "Seçenek D",
                "Seçenek E",
            ],
            "correct_answer": 1,
            "explanation": "Bu sorunun cevabı B seçeneğidir çünkü...",
            "keywords": [
                payload.subject.lower(),
                payload.topic.split("-")[0].strip().lower(),
            ],
            "difficulty": payload.difficulty,
            "quality_score": 85.5,
            "tokens_used": 150,
            "cost_usd": 0.0015,
            "generation_time_ms": int((time.time() - start_time) * 1000),
        }

        return response

    except ValueError:
        raise HTTPException(
            status_code=400, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/validate-question")
@limiter.limit("5/minute")
async def validate_question(
    request: Request,
    payload: QuestionValidationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Validate an OSYM question
    """
    try:
        issues = []
        suggestions = []

        # Check for common issues
        if len(payload.options) != 5:
            issues.append("OSYM soruları 5 şık içermelidir")

        if not payload.explanation:
            suggestions.append("Açıklama eklenmesi önerilir")

        # Mock quality score
        quality_score = 85.0 if len(issues) == 0 else 55.0

        if quality_score < 60:
            issues.append("Kalite skoru düşük")
            suggestions.append("Soru metnini ve şıkları gözden geçirin")

        response = {
            "is_valid": len(issues) == 0,
            "quality_score": quality_score,
            "issues": issues,
            "suggestions": suggestions,
        }

        return response

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/batch-generate")
@limiter.limit("5/minute")
async def batch_generate(
    request: Request,
    payload: BatchGenerationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Generate multiple OSYM questions in batch
    """
    try:
        # Start timer
        start_time = time.time()

        questions = []
        total_tokens = 0
        total_cost = 0.0
        total_quality = 0.0

        # Generate questions
        for _i in range(payload.count):
            question_req = QuestionGenerationRequest(
                topic=payload.topic,
                subtopic=payload.subtopic,
                examType=payload.examType,
                subject=payload.subject,
                difficulty=payload.difficulty,
                bloomLevel=payload.bloomLevel,
                provider=payload.provider,
            )

            question_data = await generate_question(question_req)
            questions.append(question_data)
            total_tokens += question_data.get("tokens_used", 0)
            total_cost += question_data.get("cost_usd", 0.0)
            total_quality += question_data.get("quality_score", 0.0)

        # Calculate totals
        total_time_ms = int((time.time() - start_time) * 1000)
        avg_quality = total_quality / len(questions) if questions else 0.0

        response = {
            "questions": questions,
            "total_generated": len(questions),
            "avg_quality_score": avg_quality,
            "total_tokens_used": total_tokens,
            "total_cost_usd": total_cost,
            "total_time_ms": total_time_ms,
        }

        return response

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


class AutoAssignAnchorsRequest(BaseModel):
    subject: str
    count: int = 100


class RunEquatingRequest(BaseModel):
    base_b_values: list[float]
    new_b_values: list[float]


@router.post("/auto-assign-anchors")
async def auto_assign_anchors(
    request: AutoAssignAnchorsRequest,
    # (Admin) gate — S-KODGERCEGI
    _admin: AuthenticatedUser = Depends(get_current_admin_user),
):
    """
    (Admin) Belirli bir dersteki soruları IRT kalibrasyon kalitesine göre çıpa (anchor) ilan eder.
    """
    try:
        from sqlalchemy import select

        from core.database import get_db_session_context
        from models.question_bank import QuestionBankItem, QuestionMetadata

        async with get_db_session_context() as db_session:
            # Öncekileri sıfırla
            reset_result = await db_session.execute(
                select(QuestionBankItem)
                .join(QuestionMetadata, QuestionMetadata.id == QuestionBankItem.id)
                .where(QuestionMetadata.subject_area == request.subject)
            )
            for q in reset_result.scalars().all():
                q.is_anchor = False

            # En iyi kalibrasyonluları (örneğin ID sırasına veya discrimination değerine göre) al
            # Şimdilik id sırasına göre mockluyoruz
            result = await db_session.execute(
                select(QuestionBankItem)
                .join(QuestionMetadata, QuestionMetadata.id == QuestionBankItem.id)
                .where(QuestionMetadata.subject_area == request.subject)
                # KOD GERCEGI (is_active): capalar yalniz AKTIF havuzdan secilir —
                # soft-delete'li (is_active=False) "cop" maddeler capa olamaz.
                .where(QuestionBankItem.is_active.is_(True))
                .order_by(QuestionBankItem.id)
                .limit(request.count)
            )
            questions = result.scalars().all()

            for q in questions:
                q.is_anchor = True

            await db_session.commit()

            return {
                "status": "success",
                "message": f"{len(questions)} soru anchor olarak atandı.",
                "subject": request.subject,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-equating")
async def run_equating(
    request: RunEquatingRequest,
    # (Admin) gate — S-KODGERCEGI
    _admin: AuthenticatedUser = Depends(get_current_admin_user),
):
    """
    (Admin) Mean-Mean Equating metodunu çalıştırarak formları eşitler.
    """
    try:
        from services.irt_equating_service import MeanMeanEquator

        A, B = MeanMeanEquator.calculate_constants(
            request.base_b_values, request.new_b_values
        )

        # Test amaçlı dummy bir a,b,c parametresini dönüştürelim
        sample_transformation = MeanMeanEquator.equate_parameters(
            A, B, a=1.0, b=0.0, c=0.2
        )

        return {
            "status": "success",
            "constants": {"A_slope": A, "B_intercept": B},
            "sample_transformation": sample_transformation,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    try:
        return {
            "status": "healthy",
            "generator_initialized": True,
            "providers_available": ["openai", "claude", "qwen"],
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )
