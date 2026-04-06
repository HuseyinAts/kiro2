"""
PWA Sync & Push API — stub endpoints for frontend backgroundSyncService.ts and sw.ts

Frontend calls:
  POST /api/v1/sync/exam-sessions
  POST /api/v1/sync/study-notes
  POST /api/v1/sync/progress
  POST /api/v1/push/subscribe
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from core.dependencies import AuthenticatedUser, get_current_user

# Two routers: one for /sync, one for /push
sync_router = APIRouter(prefix="/api/v1/sync", tags=["PWA Sync"])
push_router = APIRouter(prefix="/api/v1/push", tags=["PWA Push"])

# Expose a combined router for loader.py
# NOTE: include_router calls MUST be after the route decorators below.
# FastAPI/Starlette's include_router takes a snapshot of child router routes
# at call time — if called before decorators, child router routes are empty.


class PushSubscription(BaseModel):
    endpoint: str
    keys: dict[str, str] = Field(default_factory=dict)


@push_router.post("/subscribe")
async def push_subscribe(
    subscription: PushSubscription,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Register push notification subscription — stub endpoint.
    Frontend: backgroundSyncService.ts
    """
    return {
        "success": True,
        "data": {"subscribed": False},
        "message": "Push subscription stub — not yet implemented",
    }


@sync_router.post("/exam-sessions")
async def sync_exam_sessions(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Sync offline exam sessions — stub endpoint.
    Frontend: backgroundSyncService.ts
    """
    return {
        "success": True,
        "data": {"synced": 0, "pending": 0},
        "message": "Exam session sync stub — not yet implemented",
    }


@sync_router.post("/study-notes")
async def sync_study_notes(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Sync offline study notes — stub endpoint.
    Frontend: backgroundSyncService.ts
    """
    return {
        "success": True,
        "data": {"synced": 0, "pending": 0},
        "message": "Study notes sync stub — not yet implemented",
    }


@sync_router.post("/progress")
async def sync_progress(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Sync offline progress data — stub endpoint.
    Frontend: backgroundSyncService.ts / sw.ts
    """
    return {
        "success": True,
        "data": {"synced": 0, "pending": 0},
        "message": "Progress sync stub — not yet implemented",
    }


# Expose combined router AFTER all route decorators
# so include_router captures the actual routes (not an empty snapshot)
router = APIRouter()
router.include_router(sync_router)
router.include_router(push_router)
