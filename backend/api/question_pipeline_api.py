"""
Soru Üretim Pipeline API Endpoints
FastAPI endpoints for question generation pipeline

Endpoints:
- POST /api/v1/generate-question - Pipeline başlat
- GET /api/v1/pipeline-status/{pipeline_id} - Durum sorgula
- GET /api/v1/question/{question_id} - Soru getir
- GET /api/v1/pipeline-metrics - Performans metrikleri
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, ConfigDict, Field

from pipeline import PipelineOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/question-pipeline", tags=["Question Pipeline"])

# Global orchestrator instance
_orchestrator: Optional[PipelineOrchestrator] = None


def get_orchestrator() -> PipelineOrchestrator:
    """Orchestrator singleton döndür"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PipelineOrchestrator()
    return _orchestrator


# Request/Response Models

class GenerateQuestionRequest(BaseModel):
    """Soru üretim isteği"""
    kazanim: str = Field(..., description="MEB kazanımı", min_length=10)
    subject: str = Field(..., description="Ders (matematik, fizik, vb.)")
    topic: str = Field(..., description="Konu")
    grade_level: int = Field(11, ge=9, le=12, description="Sınıf seviyesi")
    target_difficulty: str = Field("orta", description="Hedef zorluk: kolay, orta, zor")
    question_type: str = Field("çoktan_seçmeli", description="Soru tipi")
    correct_answer: Optional[str] = Field(None, description="Doğru cevap (opsiyonel)")
    context: Optional[str] = Field(None, description="Ek bağlam")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "kazanim": "İkinci dereceden bir bilinmeyenli denklemleri çözer",
            "subject": "matematik",
            "topic": "İkinci Dereceden Denklemler",
            "grade_level": 10,
            "target_difficulty": "orta",
            "question_type": "çoktan_seçmeli"
        }
    })


class PipelineResponse(BaseModel):
    """Pipeline başlatma yanıtı"""
    pipeline_id: str
    status: str
    message: str
    estimated_duration: float = Field(description="Tahmini süre (saniye)")


class PipelineStatusResponse(BaseModel):
    """Pipeline durum yanıtı"""
    pipeline_id: str
    status: str
    current_stage: Optional[str]
    progress: float = Field(ge=0, le=1)
    stages_completed: int
    final_score: Optional[float]
    decision: Optional[str]
    total_duration: float
    errors: List[Dict[str, Any]] = []


class GeneratedQuestionResponse(BaseModel):
    """Üretilen soru yanıtı"""
    pipeline_id: str
    question_id: Optional[str]
    question_text: str
    context: Optional[str]
    options: List[Dict[str, Any]]
    correct_answer: str
    bloom_level: str
    irt_parameters: Dict[str, float]
    quality_scores: Dict[str, float]
    final_score: float
    status: str
    created_at: datetime


class PipelineMetricsResponse(BaseModel):
    """Pipeline metrikleri yanıtı"""
    total_pipelines: int
    completed: int
    failed: int
    success_rate: float
    avg_duration: float
    avg_score: float
    questions_per_hour: float
    stages: List[str]


# In-memory storage (production'da Redis/DB kullanılmalı)
_generated_questions: Dict[str, Dict] = {}


# Endpoints

@router.post(
    "/generate-question",
    response_model=PipelineResponse,
    summary="Soru üretim pipeline'ı başlat",
    description="MEB kazanımına göre ÖSYM standardında soru üretir"
)
async def generate_question(
    request: GenerateQuestionRequest,
    background_tasks: BackgroundTasks,
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator)
):
    """
    Soru üretim pipeline'ı başlat

    Pipeline 6 aşamadan oluşur:
    1. Content Generator - İçerik üretimi
    2. Difficulty Calibration - IRT zorluk kalibrasyonu
    3. Distractor Generator - Çeldirici üretimi
    4. ÖSYM Compliance - Format kontrolü
    5. Language QA - Dil kalitesi
    6. Quality Gate - Final onay
    """
    try:
        # Input hazırla
        initial_input = request.dict()

        # Background'da çalıştır
        import uuid
        pipeline_id = str(uuid.uuid4())

        async def run_pipeline():
            try:
                result = await orchestrator.execute_pipeline(
                    initial_input=initial_input,
                    pipeline_id=pipeline_id
                )
                # Sonucu kaydet
                _generated_questions[pipeline_id] = result
            except Exception as e:
                logger.error(f"Pipeline {pipeline_id} failed: {e}")
                _generated_questions[pipeline_id] = {
                    "pipeline_id": pipeline_id,
                    "status": "failed",
                    "error": str(e)
                }

        background_tasks.add_task(run_pipeline)

        return PipelineResponse(
            pipeline_id=pipeline_id,
            status="running",
            message="Soru üretim pipeline'ı başlatıldı",
            estimated_duration=120.0  # ~2 dakika
        )

    except Exception as e:
        logger.error(f"Generate question error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/generate-question/sync",
    response_model=GeneratedQuestionResponse,
    summary="Soru üret (senkron)",
    description="Senkron soru üretimi - sonuç bekler"
)
async def generate_question_sync(
    request: GenerateQuestionRequest,
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator)
):
    """Senkron soru üretimi - tamamlanana kadar bekler"""
    try:
        initial_input = request.dict()

        result = await orchestrator.execute_pipeline(initial_input)

        if result.get("status") == "failed":
            raise HTTPException(status_code=500, detail="Pipeline failed")

        question = result.get("question", {})

        return GeneratedQuestionResponse(
            pipeline_id=result.get("pipeline_id", ""),
            question_id=question.get("question_id"),
            question_text=question.get("question_text", ""),
            context=question.get("context"),
            options=question.get("options", []),
            correct_answer=question.get("correct_answer", ""),
            bloom_level=question.get("bloom_level", ""),
            irt_parameters={
                "difficulty": question.get("irt_difficulty", 0.0),
                "discrimination": question.get("irt_discrimination", 1.0),
                "guessing": question.get("irt_guessing", 0.25)
            },
            quality_scores=question.get("stage_scores", {}),
            final_score=result.get("final_score", 0.0),
            status=result.get("decision", "rejected"),
            created_at=datetime.now(timezone.utc)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sync generate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/pipeline-status/{pipeline_id}",
    response_model=PipelineStatusResponse,
    summary="Pipeline durumu sorgula"
)
async def get_pipeline_status(
    pipeline_id: str,
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator)
):
    """Pipeline çalışma durumunu sorgula"""
    try:
        # Orchestrator'dan kontrol et
        status = await orchestrator.get_pipeline_status(pipeline_id)

        if status:
            return PipelineStatusResponse(**status)

        # Tamamlanmış pipeline'ları kontrol et
        if pipeline_id in _generated_questions:
            result = _generated_questions[pipeline_id]
            return PipelineStatusResponse(
                pipeline_id=pipeline_id,
                status=result.get("status", "completed"),
                current_stage=None,
                progress=1.0,
                stages_completed=6,
                final_score=result.get("final_score"),
                decision=result.get("decision"),
                total_duration=result.get("total_duration", 0.0),
                errors=[]
            )

        raise HTTPException(status_code=404, detail="Pipeline bulunamadı")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/question/{pipeline_id}",
    response_model=GeneratedQuestionResponse,
    summary="Üretilen soruyu getir"
)
async def get_generated_question(pipeline_id: str):
    """Pipeline'dan üretilen soruyu getir"""
    try:
        if pipeline_id not in _generated_questions:
            raise HTTPException(status_code=404, detail="Soru bulunamadı")

        result = _generated_questions[pipeline_id]

        if result.get("status") == "failed":
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Pipeline failed")
            )

        question = result.get("question", {})

        return GeneratedQuestionResponse(
            pipeline_id=pipeline_id,
            question_id=question.get("question_id"),
            question_text=question.get("question_text", ""),
            context=question.get("context"),
            options=question.get("options", []),
            correct_answer=question.get("correct_answer", ""),
            bloom_level=question.get("bloom_level", ""),
            irt_parameters={
                "difficulty": question.get("irt_difficulty", 0.0),
                "discrimination": question.get("irt_discrimination", 1.0),
                "guessing": question.get("irt_guessing", 0.25)
            },
            quality_scores=question.get("stage_scores", {}),
            final_score=result.get("final_score", 0.0),
            status=result.get("decision", "rejected"),
            created_at=datetime.now(timezone.utc)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get question error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/pipeline-metrics",
    response_model=PipelineMetricsResponse,
    summary="Pipeline performans metrikleri"
)
async def get_pipeline_metrics(
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator)
):
    """Pipeline performans metriklerini getir"""
    try:
        metrics = orchestrator.get_metrics()

        # Saat başına soru hesapla
        avg_duration = metrics.get("avg_duration", 120)
        if avg_duration > 0:
            questions_per_hour = 3600 / avg_duration
        else:
            questions_per_hour = 0

        return PipelineMetricsResponse(
            total_pipelines=metrics.get("total_pipelines", 0),
            completed=metrics.get("completed", 0),
            failed=metrics.get("failed", 0),
            success_rate=metrics.get("success_rate", 0),
            avg_duration=metrics.get("avg_duration", 0),
            avg_score=metrics.get("avg_score", 0),
            questions_per_hour=round(questions_per_hour, 1),
            stages=metrics.get("stages", [])
        )

    except Exception as e:
        logger.error(f"Get metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/pipeline-cancel/{pipeline_id}",
    summary="Pipeline'ı iptal et"
)
async def cancel_pipeline(
    pipeline_id: str,
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator)
):
    """Çalışan pipeline'ı iptal et"""
    try:
        success = await orchestrator.cancel_pipeline(pipeline_id)

        if success:
            return {"message": f"Pipeline {pipeline_id} iptal edildi"}
        else:
            raise HTTPException(
                status_code=400,
                detail="Pipeline iptal edilemedi (tamamlanmış veya bulunamadı)"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/pipeline-stages",
    summary="Pipeline aşamalarını listele"
)
async def list_pipeline_stages(
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator)
):
    """Pipeline aşamalarını ve ağırlıklarını listele"""
    stages = []
    for stage_name in orchestrator.get_stage_order():
        stage = orchestrator.stages.get(stage_name)
        if stage:
            stages.append({
                "name": stage_name,
                "weight": stage.get_stage_weight(),
                "info": stage.get_stage_info()
            })

    return {
        "stages": stages,
        "total_stages": len(stages),
        "parallel_groups": orchestrator.PARALLEL_GROUPS
    }
