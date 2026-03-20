"""
Realm (Alem) API

FAZ-2 Gorev 2.3 — Master Plan v2.0
Endpoints (tum route'lar auth gerektirir):
  GET  /api/v1/realms/                      -> tum alemler + ogrenci progress
  GET  /api/v1/realms/{slug}                -> tek alem detay
  GET  /api/v1/realms/{slug}/progress       -> BKT, quest_step, xp, kilit durumu
  POST /api/v1/realms/{slug}/quest/start    -> gorevi baslat (quest_step = 0 -> 1)
  POST /api/v1/realms/{slug}/quest/complete -> gorevi tamamla -> XP ver + badge kontrol
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session as get_async_db
from core.dependencies import AuthenticatedUser, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/realms", tags=["realms"])


# ---------------------------------------------------------------------------
# DB helper (lazy import gamification models)
# ---------------------------------------------------------------------------


async def _get_realm_or_404(slug: str, db: AsyncSession):
    try:
        from models.gamification import Realm

        stmt = select(Realm).where(Realm.slug == slug, Realm.is_active == True)
        result = await db.execute(stmt)
        realm = result.scalar_one_or_none()
        if realm is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alem bulunamadi: {slug}",
            )
        return realm
    except ImportError as e:
        raise HTTPException(
            status_code=503, detail="Gamification modeli yuklenemedi"
        ) from e


async def _get_or_create_progress(student_id: str, realm_id: int, db: AsyncSession):
    from models.gamification import RealmProgress

    stmt = select(RealmProgress).where(
        RealmProgress.student_id == student_id,
        RealmProgress.realm_id == realm_id,
    )
    result = await db.execute(stmt)
    progress = result.scalar_one_or_none()
    if progress is None:
        progress = RealmProgress(
            student_id=student_id,
            realm_id=realm_id,
            bkt_score=0.0,
            quest_stop=0,
            xp_earned=0,
        )
        db.add(progress)
        await db.flush()
    return progress


def _realm_to_dict(realm) -> dict[str, Any]:
    return {
        "id": realm.id,
        "slug": realm.slug,
        "name": realm.name,
        "era": realm.era,
        "npc_name": realm.npc_name,
        "npc_title": realm.npc_title,
        "tech_stack": realm.tech_stack,
        "color_primary": realm.color_primary,
        "color_secondary": realm.color_secondary,
        "order_index": realm.order_index,
        "is_active": realm.is_active,
    }


# ---------------------------------------------------------------------------
# GET /realms/
# ---------------------------------------------------------------------------


@router.get("/")
async def list_realms(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Tum aktif alemleri + ogrenci progress bilgisi ile listele."""
    from models.gamification import Realm, RealmProgress

    # Tum aktif alemler
    stmt = select(Realm).where(Realm.is_active == True).order_by(Realm.order_index)
    result = await db.execute(stmt)
    realms = result.scalars().all()

    # Ogrencinin progress kayitlari
    prog_stmt = select(RealmProgress).where(RealmProgress.student_id == current_user.id)
    prog_result = await db.execute(prog_stmt)
    progress_map: dict[int, Any] = {p.realm_id: p for p in prog_result.scalars().all()}

    items = []
    for r in realms:
        prog = progress_map.get(r.id)
        item = _realm_to_dict(r)
        item["progress"] = {
            "bkt_score": float(prog.bkt_score) if prog else 0.0,
            "quest_stop": prog.quest_stop if prog else 0,
            "xp_earned": prog.xp_earned if prog else 0,
            "completed": prog.completed_at is not None if prog else False,
        }
        items.append(item)

    return {"realms": items, "total": len(items)}


# ---------------------------------------------------------------------------
# GET /realms/{slug}
# ---------------------------------------------------------------------------


@router.get("/{slug}")
async def get_realm(
    slug: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Tek alem detayi."""
    realm = await _get_realm_or_404(slug, db)
    return _realm_to_dict(realm)


# ---------------------------------------------------------------------------
# GET /realms/{slug}/progress
# ---------------------------------------------------------------------------


@router.get("/{slug}/progress")
async def get_realm_progress(
    slug: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """BKT, quest_step, xp ve kilit durumu."""
    realm = await _get_realm_or_404(slug, db)
    progress = await _get_or_create_progress(current_user.id, realm.id, db)
    await db.commit()

    from services.bkt_service import ZPDManager

    bkt_score = float(progress.bkt_score)
    return {
        "realm_slug": slug,
        "bkt_score": bkt_score,
        "quest_stop": progress.quest_stop,
        "xp_earned": progress.xp_earned,
        "completed": progress.completed_at is not None,
        "zpd_zone": ZPDManager.zone(bkt_score),
        "unlock_3d": ZPDManager.unlock_3d(bkt_score),
        "recommended_difficulty": ZPDManager.recommended_difficulty(bkt_score),
    }


# ---------------------------------------------------------------------------
# POST /realms/{slug}/quest/start
# ---------------------------------------------------------------------------


@router.post("/{slug}/quest/start")
async def start_quest(
    slug: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Gorevi baslat — quest_stop 0 ise 1'e ayarla."""
    realm = await _get_realm_or_404(slug, db)
    progress = await _get_or_create_progress(current_user.id, realm.id, db)

    if progress.quest_stop == 0:
        progress.quest_stop = 1

    await db.commit()
    return {
        "realm_slug": slug,
        "quest_stop": progress.quest_stop,
        "message": "Gorev basladi!",
    }


# ---------------------------------------------------------------------------
# POST /realms/{slug}/quest/complete
# ---------------------------------------------------------------------------


@router.post("/{slug}/quest/complete")
async def complete_quest(
    slug: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Gorevi tamamla -> XP ver + realm tamamlama badge kontrol."""
    realm = await _get_realm_or_404(slug, db)
    progress = await _get_or_create_progress(current_user.id, realm.id, db)

    if progress.completed_at is not None:
        return {
            "realm_slug": slug,
            "message": "Zaten tamamlandi",
            "xp_earned": progress.xp_earned,
            "already_completed": True,
        }

    # Realm tamamlama XP: 200 XP
    xp_reward = 200
    progress.xp_earned = (progress.xp_earned or 0) + xp_reward
    progress.completed_at = datetime.now(UTC)

    # XP transaction kaydi
    from models.gamification import XPTransaction

    xp_tx = XPTransaction(
        student_id=current_user.id,
        amount=xp_reward,
        source="realm",
        topic_id=None,
    )
    db.add(xp_tx)

    # Kullanici toplam XP guncelle
    from sqlalchemy import text

    await db.execute(
        text("UPDATE users SET total_xp = COALESCE(total_xp, 0) + :xp WHERE id = :uid"),
        {"xp": xp_reward, "uid": current_user.id},
    )

    # Realm mastery badge kontrol
    badge_earned = None
    try:
        from models.gamification import Badge, UserBadge

        badge_slug = f"usta_{slug}"
        badge_stmt = select(Badge).where(Badge.slug == badge_slug)
        badge_result = await db.execute(badge_stmt)
        badge = badge_result.scalar_one_or_none()
        if badge:
            ub_stmt = select(UserBadge).where(
                UserBadge.user_id == current_user.id,
                UserBadge.badge_id == badge.id,
            )
            ub_result = await db.execute(ub_stmt)
            if ub_result.scalar_one_or_none() is None:
                user_badge = UserBadge(user_id=current_user.id, badge_id=badge.id)
                db.add(user_badge)
                badge_earned = badge.name
    except Exception as e:
        logger.debug("Badge kontrol hatasi: %s", e)

    await db.commit()

    return {
        "realm_slug": slug,
        "message": "Tebrikler! Alem tamamlandi.",
        "xp_earned": xp_reward,
        "total_xp_in_realm": progress.xp_earned,
        "badge_earned": badge_earned,
        "already_completed": False,
    }
