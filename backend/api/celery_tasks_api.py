"""
Celery Task Status API
PHASE 1 Sprint 3: Async Processing

Endpoints for checking background task status and results
"""
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from celery.result import AsyncResult
from core.celery_app import celery_app
from core.structured_logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/tasks", tags=["Background Tasks"])


class TaskStatusResponse(BaseModel):
    """Task status response model"""
    task_id: str
    status: str  # PENDING, STARTED, SUCCESS, FAILURE, RETRY
    result: Optional[Any] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None


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
    description="Background task'ın durumunu ve sonucunu getir"
)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Get background task status and result
    
    Args:
        task_id: Celery task ID
    
    Returns:
        Task status with result or error
        
    Example:
        GET /api/v1/tasks/abc123-def456-789/status
        
        Response:
        {
            "task_id": "abc123-def456-789",
            "status": "SUCCESS",
            "result": {"email": "user@example.com", "sent": true}
        }
    """
    try:
        # Get task result from Celery
        task_result = AsyncResult(task_id, app=celery_app)
        
        response = {
            "task_id": task_id,
            "status": task_result.status,
            "result": None,
            "error": None,
            "traceback": None,
        }
        
        # Add result or error based on status
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
            detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post(
    "/{task_id}/cancel",
    summary="Task'ı İptal Et",
    description="Çalışan veya bekleyen task'ı iptal et"
)
async def cancel_task(task_id: str) -> Dict[str, Any]:
    """
    Cancel a running or pending task
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Cancellation result
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        
        if task_result.status in ["SUCCESS", "FAILURE"]:
            return {
                "success": False,
                "message": f"Task already completed with status: {task_result.status}"
            }
            
        # Revoke the task
        celery_app.control.revoke(task_id, terminate=True)
        
        logger.info("task_cancelled", task_id=task_id)
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "Task cancelled successfully"
        }
        
    except Exception as e:
        logger.error("task_cancel_failed", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get(
    "/active",
    response_model=Dict[str, Any],
    summary="Aktif Task'ları Listele",
    description="Şu anda çalışan task'ları listele"
)
async def list_active_tasks() -> Dict[str, Any]:
    """
    List all active (running) tasks
    
    Returns:
        List of active tasks
    """
    try:
        # Get active tasks from all workers
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        
        if not active_tasks:
            return {
                "active_tasks": [],
                "total_count": 0,
                "message": "No active tasks"
            }
            
        # Format task info
        tasks = []
        for worker, task_list in active_tasks.items():
            for task in task_list:
                tasks.append({
                    "task_id": task.get("id"),
                    "task_name": task.get("name"),
                    "worker": worker,
                    "args": task.get("args"),
                    "kwargs": task.get("kwargs"),
                })
                
        logger.info("active_tasks_listed", count=len(tasks))
        
        return {
            "active_tasks": tasks,
            "total_count": len(tasks)
        }
        
    except Exception as e:
        logger.error("active_tasks_list_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get(
    "/stats",
    response_model=Dict[str, Any],
    summary="Task İstatistikleri",
    description="Celery worker ve queue istatistikleri"
)
async def get_task_stats() -> Dict[str, Any]:
    """
    Get Celery worker and queue statistics
    
    Returns:
        Worker and queue stats
    """
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
            detail="Islem basarisiz. Lutfen tekrar deneyin."
        )
