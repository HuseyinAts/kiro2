"""
Celery Task Status API
PHASE 1 Sprint 3: Async Processing

Endpoints for checking background task status and results
"""

from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from core.celery_app import celery_app
from core.dependencies import AuthenticatedUser, get_current_user
from core.structured_logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/tasks", tags=["Background Tasks"])


class TaskStatusResponse(BaseModel):
    """Task status response model"""

    task_id: str
    status: str  # PENDING, STARTED, SUCCESS, FAILURE, RETRY
    result: Any | None = None
    error: str | None = None
    traceback: str | None = None
    progress: dict[str, Any] | None = None


class TaskInfo(BaseModel):
    """Task information"""

    task_id: str
    task_name: str
    queue: str
    status: str


@router.get(
    "/{task_id}/status",
    response_model=TaskStatusResponse,
    summary="Task Durumunu Sorgula",
    description="Background task'ın durumunu ve sonucunu getir",
)
async def get_task_status(
    task_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> TaskStatusResponse:
    """Get background task status and result"""
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        response = {
            "task_id": task_id,
            "status": task_result.status,
            "result": None,
            "error": None,
            "traceback": None,
        }

        if task_result.status == "SUCCESS":
            response["result"] = task_result.result
        elif task_result.status == "FAILURE":
            response["error"] = str(task_result.result)
            response["traceback"] = task_result.traceback
        elif task_result.status == "PENDING":
            response["result"] = {"message": "Task is queued"}
        elif task_result.status == "STARTED":
            response["result"] = {"message": "Task is running"}

        logger.info("task_status_checked", task_id=task_id, status=task_result.status)

        return TaskStatusResponse(**response)

    except Exception as e:
        logger.error("task_status_check_failed", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post(
    "/{task_id}/cancel",
    summary="Task'ı İptal Et",
    description="Çalışan veya bekleyen task'ı iptal et",
)
async def cancel_task(
    task_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Cancel a running or pending task"""
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        if task_result.status in ["SUCCESS", "FAILURE"]:
            return {
                "success": False,
                "message": f"Task already completed with status: {task_result.status}",
            }

        celery_app.control.revoke(task_id, terminate=True)

        logger.info("task_cancelled", task_id=task_id)

        return {
            "success": True,
            "task_id": task_id,
            "message": "Task cancelled successfully",
        }

    except Exception as e:
        logger.error("task_cancel_failed", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get(
    "/active",
    response_model=dict[str, Any],
    summary="Aktif Task'ları Listele",
    description="Şu anda çalışan task'ları listele",
)
async def list_active_tasks(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """List all active (running) tasks"""
    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()

        if not active_tasks:
            return {"active_tasks": [], "total_count": 0, "message": "No active tasks"}

        tasks = []
        for worker, task_list in active_tasks.items():
            for task in task_list:
                tasks.append(
                    {
                        "task_id": task.get("id"),
                        "task_name": task.get("name"),
                        "worker": worker,
                        "args": task.get("args"),
                        "kwargs": task.get("kwargs"),
                    }
                )

        logger.info("active_tasks_listed", count=len(tasks))

        return {"active_tasks": tasks, "total_count": len(tasks)}

    except Exception as e:
        logger.error("active_tasks_list_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get(
    "/stats",
    response_model=dict[str, Any],
    summary="Task İstatistikleri",
    description="Celery worker ve queue istatistikleri",
)
async def get_task_stats(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Get Celery worker and queue statistics"""
    try:
        inspect = celery_app.control.inspect()

        stats = inspect.stats()
        active = inspect.active()
        scheduled = inspect.scheduled()

        return {
            "workers": stats or {},
            "active_tasks": sum(len(tasks) for tasks in (active or {}).values()),
            "scheduled_tasks": sum(len(tasks) for tasks in (scheduled or {}).values()),
        }

    except Exception as e:
        logger.error("task_stats_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
