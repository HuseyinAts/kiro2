"""
Parent Social Settings API — Veli Sosyal Kontrolleri
Endpoints: /api/v1/parent-social/*

- Cocugun sosyal ayarlarini gor/guncelle
- Aktivite ozeti
- Bayrak uyarilari
- Acil kapatma (panic button)
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.dependencies import AuthenticatedUser, get_current_user
from models.social_safety import (
    ContentReport,
    MessageAuditLog,
    ModerationAction,
    ParentSocialSettings,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/parent-social", tags=["Parent Social"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class SocialSettingsUpdate(BaseModel):
    social_enabled: bool | None = None
    chat_enabled: bool | None = None
    study_rooms_enabled: bool | None = None
    duels_enabled: bool | None = None
    forum_enabled: bool | None = None
    notifications_enabled: bool | None = None
    visibility_level: str | None = Field(None, pattern=r"^(full|summary|none)$")
    max_daily_messages: int | None = Field(None, ge=0, le=1000)
    allowed_hours_start: int | None = Field(None, ge=0, le=23)
    allowed_hours_end: int | None = Field(None, ge=0, le=23)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/settings/{student_id}", response_model=dict[str, Any])
async def get_social_settings(
    student_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Cocugun sosyal ayarlarini getir."""
    parent_id = str(current_user.id)

    result = await db.execute(
        select(ParentSocialSettings).where(
            ParentSocialSettings.parent_id == parent_id,
            ParentSocialSettings.student_id == student_id,
        )
    )
    settings = result.scalar_one_or_none()

    if not settings:
        # Varsayilan ayarlarla olustur
        settings = ParentSocialSettings(
            parent_id=parent_id,
            student_id=student_id,
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return {
        "success": True,
        "data": {
            "student_id": settings.student_id,
            "social_enabled": settings.social_enabled,
            "chat_enabled": settings.chat_enabled,
            "study_rooms_enabled": settings.study_rooms_enabled,
            "duels_enabled": settings.duels_enabled,
            "forum_enabled": settings.forum_enabled,
            "notifications_enabled": settings.notifications_enabled,
            "visibility_level": settings.visibility_level,
            "max_daily_messages": settings.max_daily_messages,
            "allowed_hours_start": settings.allowed_hours_start,
            "allowed_hours_end": settings.allowed_hours_end,
        },
    }


@router.put("/settings/{student_id}", response_model=dict[str, Any])
async def update_social_settings(
    student_id: str,
    body: SocialSettingsUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Cocugun sosyal ayarlarini guncelle."""
    parent_id = str(current_user.id)

    result = await db.execute(
        select(ParentSocialSettings).where(
            ParentSocialSettings.parent_id == parent_id,
            ParentSocialSettings.student_id == student_id,
        )
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = ParentSocialSettings(
            parent_id=parent_id,
            student_id=student_id,
        )
        db.add(settings)

    # Sadece gonderilen alanlari guncelle
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)

    await db.commit()

    return {"success": True, "message": "Sosyal ayarlar guncellendi."}


@router.get("/activity/{student_id}", response_model=dict[str, Any])
async def get_student_activity(
    student_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    days: int = Query(7, ge=1, le=30),
):
    """Cocugun son X gunluk sosyal aktivite ozetini getir."""
    parent_id = str(current_user.id)

    # Veli-ogrenci iliskisi kontrol
    settings_check = await db.execute(
        select(ParentSocialSettings.id).where(
            ParentSocialSettings.parent_id == parent_id,
            ParentSocialSettings.student_id == student_id,
        )
    )
    if not settings_check.scalar_one_or_none():
        raise HTTPException(403, "Bu ogrenciye erisim yetkiniz yok.")

    from datetime import UTC, datetime, timedelta

    since = datetime.now(UTC) - timedelta(days=days)

    # Mesaj sayisi
    msg_count = (
        await db.execute(
            select(func.count())
            .select_from(MessageAuditLog)
            .where(
                MessageAuditLog.sender_id == student_id,
                MessageAuditLog.created_at >= since,
            )
        )
    ).scalar() or 0

    # Bayrakli mesaj sayisi
    flagged_count = (
        await db.execute(
            select(func.count())
            .select_from(MessageAuditLog)
            .where(
                MessageAuditLog.sender_id == student_id,
                MessageAuditLog.created_at >= since,
                MessageAuditLog.flagged.is_(True),
            )
        )
    ).scalar() or 0

    # Rapor sayisi (raporlayan veya raporlanan)
    report_count = (
        await db.execute(
            select(func.count())
            .select_from(ContentReport)
            .where(
                ContentReport.created_at >= since,
                (ContentReport.reporter_id == student_id)
                | (ContentReport.reported_user_id == student_id),
            )
        )
    ).scalar() or 0

    # Moderasyon aksiyonu
    action_count = (
        await db.execute(
            select(func.count())
            .select_from(ModerationAction)
            .where(
                ModerationAction.target_user_id == student_id,
                ModerationAction.created_at >= since,
            )
        )
    ).scalar() or 0

    return {
        "success": True,
        "data": {
            "student_id": student_id,
            "period_days": days,
            "total_messages": msg_count,
            "flagged_messages": flagged_count,
            "reports_involved": report_count,
            "moderation_actions": action_count,
            "safety_score": _calculate_safety_score(
                msg_count, flagged_count, report_count, action_count
            ),
        },
    }


@router.get("/flags/{student_id}", response_model=dict[str, Any])
async def get_student_flags(
    student_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(10, ge=1, le=50),
):
    """Cocugun bayrakli mesajlarini getir (hash + sebep, icerik degil)."""
    parent_id = str(current_user.id)

    settings_check = await db.execute(
        select(ParentSocialSettings.id).where(
            ParentSocialSettings.parent_id == parent_id,
            ParentSocialSettings.student_id == student_id,
        )
    )
    if not settings_check.scalar_one_or_none():
        raise HTTPException(403, "Bu ogrenciye erisim yetkiniz yok.")

    result = await db.execute(
        select(MessageAuditLog)
        .where(
            MessageAuditLog.sender_id == student_id,
            MessageAuditLog.flagged.is_(True),
        )
        .order_by(MessageAuditLog.created_at.desc())
        .limit(limit)
    )
    flags = result.scalars().all()

    return {
        "success": True,
        "data": [
            {
                "id": f.id,
                "content_type": f.content_type,
                "flag_reason": f.flag_reason,
                "content_length": f.content_length,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in flags
        ],
    }


@router.post("/disable-all/{student_id}", response_model=dict[str, Any])
async def disable_all_social(
    student_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Acil durum: Tum sosyal ozellikleri kapat (panic button)."""
    parent_id = str(current_user.id)

    result = await db.execute(
        select(ParentSocialSettings).where(
            ParentSocialSettings.parent_id == parent_id,
            ParentSocialSettings.student_id == student_id,
        )
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = ParentSocialSettings(
            parent_id=parent_id,
            student_id=student_id,
        )
        db.add(settings)

    settings.social_enabled = False
    settings.chat_enabled = False
    settings.study_rooms_enabled = False
    settings.duels_enabled = False
    settings.forum_enabled = False
    settings.notifications_enabled = False

    await db.commit()

    logger.warning(
        "PANIC: Parent %s disabled all social for student %s",
        parent_id,
        student_id,
    )

    return {
        "success": True,
        "message": "Tum sosyal ozellikler kapatildi.",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _calculate_safety_score(
    total_msgs: int,
    flagged: int,
    reports: int,
    actions: int,
) -> int:
    """0-100 guvenlik skoru. 100 = temiz, 0 = cok sorunlu."""
    if total_msgs == 0:
        return 100

    score = 100.0
    # Bayrakli mesaj orani
    flag_ratio = flagged / max(total_msgs, 1)
    score -= flag_ratio * 200  # %10 bayrak = -20 puan

    # Raporlar ve aksiyonlar agir ceza
    score -= reports * 10
    score -= actions * 20

    return max(0, min(100, int(score)))
