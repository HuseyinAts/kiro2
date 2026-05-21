"""Study Rooms API stub — S180 #5 fix for FE↔BE 404 cascade.

Frontend has 40+ `/api/v1/study-rooms/*` calls (ChatInterface, FileManager,
StudyRoomList, StudyRoomView, VideoConference, WhiteboardSync) but backend
had ZERO endpoints. Pre-fix this resulted in silent 404 cascade: every
room creation, message send, file upload, whiteboard sync got "Not Found"
without context — UX showed generic error, monitoring couldn't tag the
gap.

This stub returns explicit 501 NOT IMPLEMENTED for every study-rooms
path so:
  1. Frontend can render a "Feature coming soon" UX instead of "Not Found"
  2. Backend logs every call → real-traffic data for prioritization
  3. When the real implementation lands, this file gets deleted in
     a single PR (no path collision risk).

Real implementation tracker: see EVIDENCE_BASED_DEEP_REVIEW.md §IV (the
40+ endpoint inventory under FE↔BE 404 risk).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/study-rooms", tags=["Study Rooms (stub)"])


def _raise_not_implemented(request: Request) -> None:
    """Log call + raise 501 with frontend-friendly hint."""
    logger.info(
        "[study-rooms stub] %s %s — not implemented yet",
        request.method,
        request.url.path,
    )
    raise HTTPException(
        status_code=501,
        detail={
            "error": "not_implemented",
            "feature": "study_rooms",
            "message": (
                "Study Rooms backend is not yet implemented. Tracking "
                "issue: docs/audits/2026-05-22_product_ready_audit/04_"
                "integration.md §1."
            ),
            "frontend_hint": "Render 'Feature coming soon' placeholder.",
        },
    )


# ---- Room CRUD ----
@router.get("/my-rooms")
async def my_rooms(request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


@router.get("/joined")
async def joined_rooms(request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


@router.get("/public")
async def public_rooms(request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


@router.post("/create")
async def create_room(request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


@router.get("/{room_id}")
async def room_detail(room_id: str, request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


@router.delete("/{room_id}")
async def delete_room(room_id: str, request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


@router.post("/{room_id}/join")
async def join_room(room_id: str, request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


@router.post("/{room_id}/leave")
async def leave_room(room_id: str, request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


# ---- Messages ----
@router.get("/{room_id}/messages")
async def list_messages(room_id: str, request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


@router.post("/{room_id}/messages")
async def post_message(room_id: str, request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


@router.delete("/{room_id}/messages/{message_id}")
async def delete_message(
    room_id: str, message_id: str, request: Request
) -> dict[str, Any]:
    _raise_not_implemented(request)


@router.post("/{room_id}/messages/{message_id}/reaction")
async def react_to_message(
    room_id: str, message_id: str, request: Request
) -> dict[str, Any]:
    _raise_not_implemented(request)


# ---- Files ----
@router.get("/{room_id}/files")
async def list_files(room_id: str, request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


@router.post("/{room_id}/files/upload")
async def upload_file(room_id: str, request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


@router.post("/{room_id}/files/{file_id}/download")
async def download_file(room_id: str, file_id: str, request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


@router.delete("/{room_id}/files/{file_id}")
async def delete_file(room_id: str, file_id: str, request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


@router.get("/{room_id}/files/{file_id}/versions")
async def file_versions(room_id: str, file_id: str, request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


@router.post("/{room_id}/upload")
async def upload_attachment(room_id: str, request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


# ---- Whiteboard ----
@router.get("/{room_id}/whiteboard")
async def get_whiteboard(room_id: str, request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


@router.post("/{room_id}/whiteboard/sync")
async def sync_whiteboard(room_id: str, request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


# ---- Video conference ----
@router.post("/{room_id}/video/join")
async def join_video(room_id: str, request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


@router.post("/{room_id}/video/leave")
async def leave_video(room_id: str, request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)


@router.get("/{room_id}/video/participants")
async def video_participants(room_id: str, request: Request) -> dict[str, Any]:
    _raise_not_implemented(request)
