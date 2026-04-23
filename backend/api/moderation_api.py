"""
Moderation API — Icerik Raporlama ve Moderasyon
Endpoints: /api/v1/moderation/*

- Icerik raporla (report)
- Rapor listele/guncelle (admin)
- Kullanici engelle/coz
- Mute/ban durumu kontrol
- Content filter test (admin)
"""

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.dependencies import (
    AuthenticatedUser,
    UserRole,
    get_current_admin_user,
    get_current_user,
)
from models.social_safety import (
    BlockedUser,
    ContentReport,
    ModerationAction,
)
from services.social_content_filter import get_social_content_filter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/moderation", tags=["Moderation"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ReportCreate(BaseModel):
    reported_content_id: str
    content_type: str = Field(
        ...,
        pattern=r"^(chat_message|study_room_message|duel_chat|forum_post|forum_solution|profile_bio|mentor_message)$",
    )
    reported_user_id: str | None = None
    reason: str = Field(
        ...,
        pattern=r"^(harassment|inappropriate|spam|personal_info|flirting|bullying|other)$",
    )
    description: str | None = Field(None, max_length=500)


class ReportUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(reviewed|resolved|dismissed)$")
    resolution_note: str | None = None


class BlockRequest(BaseModel):
    blocked_id: str
    reason: str | None = Field(None, max_length=200)


class ModerationActionCreate(BaseModel):
    target_user_id: str
    action_type: str = Field(
        ...,
        pattern=r"^(warning|content_removed|muted_1h|muted_24h|banned_7d|banned_permanent|unban)$",
    )
    reason: str = Field(..., min_length=5, max_length=500)
    content_id: str | None = None
    report_id: str | None = None


class FilterTestRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    content_type: str = "chat_message"


# ---------------------------------------------------------------------------
# Report Endpoints
# ---------------------------------------------------------------------------


@router.post("/reports", response_model=dict[str, Any])
async def create_report(
    body: ReportCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Icerik raporla."""
    user_id = str(current_user.id)
    if body.reported_user_id == user_id:
        raise HTTPException(400, "Kendinizi raporlayamazsiniz.")

    report = ContentReport(
        reporter_id=user_id,
        reported_user_id=body.reported_user_id,
        reported_content_id=body.reported_content_id,
        content_type=body.content_type,
        reason=body.reason,
        description=body.description,
    )
    db.add(report)
    await db.commit()

    return {
        "success": True,
        "data": {"id": report.id, "status": "pending"},
        "message": "Raporunuz alindi, tesekkurler.",
    }


@router.get("/reports", response_model=dict[str, Any])
async def list_reports(
    current_user: AuthenticatedUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session),
    status: str | None = Query(
        None, pattern=r"^(pending|reviewed|resolved|dismissed)$"
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Raporlari listele (admin)."""
    stmt = select(ContentReport).order_by(ContentReport.created_at.desc())
    if status:
        stmt = stmt.where(ContentReport.status == status)
    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    reports = result.scalars().all()

    count_stmt = select(func.count()).select_from(ContentReport)
    if status:
        count_stmt = count_stmt.where(ContentReport.status == status)
    total = (await db.execute(count_stmt)).scalar() or 0

    return {
        "success": True,
        "data": {
            "items": [
                {
                    "id": r.id,
                    "reporter_id": r.reporter_id,
                    "reported_user_id": r.reported_user_id,
                    "content_type": r.content_type,
                    "reason": r.reason,
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in reports
            ],
            "total": total,
        },
    }


@router.patch("/reports/{report_id}", response_model=dict[str, Any])
async def update_report(
    report_id: str,
    body: ReportUpdate,
    current_user: AuthenticatedUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Rapor durumunu guncelle (admin only)."""
    result = await db.execute(
        select(ContentReport).where(ContentReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(404, "Rapor bulunamadi.")

    report.status = body.status
    report.resolution_note = body.resolution_note
    report.reviewed_by = str(current_user.id)
    report.reviewed_at = datetime.now(UTC)
    await db.commit()

    return {"success": True, "message": f"Rapor durumu: {body.status}"}


# ---------------------------------------------------------------------------
# Block Endpoints
# ---------------------------------------------------------------------------


@router.post("/block", response_model=dict[str, Any])
async def block_user(
    body: BlockRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Kullanici engelle."""
    user_id = str(current_user.id)
    if body.blocked_id == user_id:
        raise HTTPException(400, "Kendinizi engelleyemezsiniz.")

    existing = await db.execute(
        select(BlockedUser).where(
            BlockedUser.blocker_id == user_id,
            BlockedUser.blocked_id == body.blocked_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Bu kullanici zaten engelli.")

    block = BlockedUser(
        blocker_id=user_id,
        blocked_id=body.blocked_id,
        reason=body.reason,
    )
    db.add(block)
    await db.commit()

    return {"success": True, "message": "Kullanici engellendi."}


@router.delete("/block/{blocked_id}", response_model=dict[str, Any])
async def unblock_user(
    blocked_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Engeli kaldir."""
    user_id = str(current_user.id)
    result = await db.execute(
        select(BlockedUser).where(
            BlockedUser.blocker_id == user_id,
            BlockedUser.blocked_id == blocked_id,
        )
    )
    block = result.scalar_one_or_none()
    if not block:
        raise HTTPException(404, "Engel bulunamadi.")

    await db.delete(block)
    await db.commit()

    return {"success": True, "message": "Engel kaldirildi."}


@router.get("/block", response_model=dict[str, Any])
async def list_blocked(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Engellenen kullanicilari listele."""
    user_id = str(current_user.id)
    result = await db.execute(
        select(BlockedUser)
        .where(BlockedUser.blocker_id == user_id)
        .order_by(BlockedUser.created_at.desc())
    )
    blocks = result.scalars().all()

    return {
        "success": True,
        "data": [
            {
                "blocked_id": b.blocked_id,
                "reason": b.reason,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in blocks
        ],
    }


# ---------------------------------------------------------------------------
# Moderation Action Endpoints
# ---------------------------------------------------------------------------


@router.post("/actions", response_model=dict[str, Any])
async def create_action(
    body: ModerationActionCreate,
    current_user: AuthenticatedUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Moderasyon aksiyonu olustur (admin only)."""
    action = ModerationAction(
        moderator_id=str(current_user.id),
        target_user_id=body.target_user_id,
        action_type=body.action_type,
        reason=body.reason,
        content_id=body.content_id,
        report_id=body.report_id,
    )
    db.add(action)
    await db.commit()

    return {
        "success": True,
        "data": {"id": action.id, "action_type": body.action_type},
        "message": f"Aksiyon olusturuldu: {body.action_type}",
    }


@router.get("/check-status/{user_id}", response_model=dict[str, Any])
async def check_user_status(
    user_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Kullanicinin mute/ban durumunu kontrol et."""
    if str(user_id) != str(current_user.id) and current_user.role not in (
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    ):
        raise HTTPException(
            status_code=403,
            detail="Yalnizca kendi moderasyon durumunuzu goruntuleyebilirsiniz",
        )

    now = datetime.now(UTC)

    # Active mute
    mute_result = await db.execute(
        select(ModerationAction)
        .where(
            ModerationAction.target_user_id == user_id,
            ModerationAction.action_type.in_(["muted_1h", "muted_24h"]),
            ModerationAction.expires_at > now,
        )
        .order_by(ModerationAction.expires_at.desc())
        .limit(1)
    )
    active_mute = mute_result.scalar_one_or_none()

    # Active ban
    ban_result = await db.execute(
        select(ModerationAction)
        .where(
            ModerationAction.target_user_id == user_id,
            ModerationAction.action_type.in_(["banned_7d", "banned_permanent"]),
        )
        .where(
            (ModerationAction.expires_at > now)
            | (ModerationAction.action_type == "banned_permanent")
        )
        .order_by(ModerationAction.created_at.desc())
        .limit(1)
    )
    active_ban = ban_result.scalar_one_or_none()

    return {
        "success": True,
        "data": {
            "is_muted": active_mute is not None,
            "mute_expires": active_mute.expires_at.isoformat()
            if active_mute and active_mute.expires_at
            else None,
            "is_banned": active_ban is not None,
            "ban_type": active_ban.action_type if active_ban else None,
        },
    }


# ---------------------------------------------------------------------------
# Content Filter Test (Admin)
# ---------------------------------------------------------------------------


@router.post("/filter-test", response_model=dict[str, Any])
async def test_content_filter(
    body: FilterTestRequest,
    current_user: AuthenticatedUser = Depends(get_current_admin_user),
):
    """Content filter'i test et (yalnizca admin)."""
    content_filter = get_social_content_filter()
    result = await content_filter.filter_content(
        text=body.text,
        sender_id=str(current_user.id),
        content_type=body.content_type,
    )

    return {
        "success": True,
        "data": {
            "passed": result.passed,
            "blocked_layer": result.blocked_layer,
            "flag_reason": result.flag_reason,
            "confidence": result.confidence,
            "processing_ms": result.processing_ms,
            "sanitized_content": result.sanitized_content,
            "layers": {
                name: {
                    "passed": lr.passed,
                    "confidence": lr.confidence,
                    "details": lr.details,
                    "matched": lr.matched_patterns,
                }
                for name, lr in result.details.items()
            },
        },
    }
