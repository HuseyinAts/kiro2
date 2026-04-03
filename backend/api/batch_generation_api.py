"""
Batch Question Generation API
REST endpoints for batch question generation
"""

from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.dependencies import get_current_admin_user
from services.batch_question_generator import BatchQuestionGenerator
from tasks.question_generation_tasks import generate_question_batch

router = APIRouter(prefix="/api/v1/batch", tags=["batch-generation"])


# Request/Response Models
class BatchGenerationRequest(BaseModel):
    batch_size: int = Field(
        ..., ge=50, le=500, description="Number of questions (50-500)"
    )
    exam_type: str = Field(..., description="TYT/AYT/YDT")
    subject: str = Field(..., description="Subject area")
    topics: list[str] | None = Field(None, description="Specific topics")
    difficulty_min: float = Field(0.3, ge=0.0, le=1.0)
    difficulty_max: float = Field(0.7, ge=0.0, le=1.0)
    bloom_levels: list[int] | None = Field(None, description="Bloom levels 1-6")
    generation_method: str = Field(
        "ensemble", description="ensemble/openai/claude/qwen"
    )
    priority: str = Field("normal", description="urgent/normal/low")


class BatchStatusResponse(BaseModel):
    task_id: str
    state: str
    current: int
    total: int
    percent: float
    status: str
    result: dict[str, Any] | None = None


class BatchResultResponse(BaseModel):
    success: bool
    batch_id: str
    total: int
    successful: int
    failed: int
    success_rate: float
    avg_quality_score: float
    question_ids: list[int]
    errors: list[str]


# Endpoints
@router.post("/generate", response_model=dict[str, Any])
async def start_batch_generation(
    request: BatchGenerationRequest, _=Depends(get_current_admin_user)
) -> dict[str, Any]:
    """Start batch question generation.

    Args:
        request: Batch generation configuration

    Returns:
        Task ID and status for tracking

    Raises:
        HTTPException: If validation fails or task cannot start
    """
    try:
        # Validate request
        if request.difficulty_min >= request.difficulty_max:
            raise HTTPException(400, "difficulty_min must be < difficulty_max")

        # Estimate time
        batch_gen = BatchQuestionGenerator()
        estimated_time = batch_gen.estimate_generation_time(
            request.batch_size, request.generation_method
        )

        # Start Celery task
        task = generate_question_batch.apply_async(
            kwargs={
                "batch_size": request.batch_size,
                "exam_type": request.exam_type,
                "subject": request.subject,
                "topics": request.topics,
                "difficulty_range": (request.difficulty_min, request.difficulty_max),
                "bloom_levels": request.bloom_levels,
                "generation_method": request.generation_method,
                "priority": request.priority,
            },
            priority={"urgent": 9, "normal": 5, "low": 3}.get(request.priority, 5),
        )

        return {
            "task_id": task.id,
            "status": "QUEUED",
            "estimated_time_seconds": estimated_time,
            "message": f"Batch generation started: {request.batch_size} questions",
        }

    except Exception:
        raise HTTPException(500, "Islem basarisiz. Lutfen tekrar deneyin.")


@router.get("/status/{task_id}", response_model=BatchStatusResponse)
async def get_batch_status(
    task_id: str, _=Depends(get_current_admin_user)
) -> dict[str, Any]:
    """Get batch generation task status."""
    try:
        result = AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "state": result.state,
            "current": 0,
            "total": 0,
            "percent": 0.0,
            "status": "Unknown",
        }

        if result.state == "PENDING":
            response["status"] = "Task is waiting to start"
        elif result.state == "PROGRESS":
            info = result.info
            response["current"] = info.get("current", 0)
            response["total"] = info.get("total", 0)
            response["percent"] = (
                (response["current"] / response["total"] * 100)
                if response["total"] > 0
                else 0
            )
            response["status"] = info.get("status", "Processing...")
        elif result.state == "SUCCESS":
            response["current"] = response["total"] = 100
            response["percent"] = 100.0
            response["status"] = "Completed"
            response["result"] = result.result
        elif result.state == "FAILURE":
            response["status"] = "Failed"

        return response

    except Exception:
        raise HTTPException(500, "Islem basarisiz. Lutfen tekrar deneyin.")


@router.get("/results/{task_id}", response_model=BatchResultResponse)
async def get_batch_results(
    task_id: str, _=Depends(get_current_admin_user)
) -> BatchResultResponse:
    """Get batch generation results."""
    try:
        result = AsyncResult(task_id)

        if result.state != "SUCCESS":
            raise HTTPException(
                400, f"Task not completed. Current state: {result.state}"
            )

        data = result.result

        return BatchResultResponse(
            success=data.get("success", False),
            batch_id=task_id,
            total=data["results"]["total"],
            successful=data["results"]["successful"],
            failed=data["results"]["failed"],
            success_rate=data["results"]["success_rate"],
            avg_quality_score=data["results"]["avg_quality_score"],
            question_ids=data["results"]["question_ids"],
            errors=data["results"].get("errors", []),
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(500, "Islem basarisiz. Lutfen tekrar deneyin.")


@router.delete("/cancel/{task_id}")
async def cancel_batch_generation(
    task_id: str, _=Depends(get_current_admin_user)
) -> dict[str, Any]:
    """Cancel running batch generation."""
    try:
        result = AsyncResult(task_id)
        result.revoke(terminate=True)

        return {"success": True, "task_id": task_id, "message": "Task cancelled"}

    except Exception:
        raise HTTPException(500, "Islem basarisiz. Lutfen tekrar deneyin.")


@router.get("/queue/stats")
async def get_queue_stats(_=Depends(get_current_admin_user)) -> dict[str, Any]:
    """Get queue statistics."""
    try:
        from core.celery_app import celery_app

        # Get active/scheduled/reserved tasks
        inspect = celery_app.control.inspect()

        active = inspect.active() or {}
        scheduled = inspect.scheduled() or {}
        reserved = inspect.reserved() or {}

        # Count tasks
        active_count = sum(len(tasks) for tasks in active.values())
        scheduled_count = sum(len(tasks) for tasks in scheduled.values())
        reserved_count = sum(len(tasks) for tasks in reserved.values())

        return {
            "active_tasks": active_count,
            "scheduled_tasks": scheduled_count,
            "reserved_tasks": reserved_count,
            "total_pending": active_count + scheduled_count + reserved_count,
            "workers": len(active.keys()),
            "queues": ["default", "bulk", "emails", "reports"],
        }

    except Exception:
        raise HTTPException(500, "Islem basarisiz. Lutfen tekrar deneyin.")
