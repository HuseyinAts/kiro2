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
from services.learning_event_service import GamificationDBService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/realms", tags=["realms"])


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


# ---------------------------------------------------------------------------
# Quest Chain — multi-step progression per realm
# ---------------------------------------------------------------------------

# Her realm icin 5 adimli gorev zinciri
QUEST_CHAINS: dict[str, list[dict[str, Any]]] = {
    "matematik": [
        {
            "step": 1,
            "title": "Sayi Sezgisi",
            "desc": "5 temel islem sorusu coz",
            "type": "quiz",
            "target": 5,
            "xp": 20,
        },
        {
            "step": 2,
            "title": "Denklem Avi",
            "desc": "3 denklem sorusunu dogru cevapla",
            "type": "quiz",
            "target": 3,
            "xp": 30,
        },
        {
            "step": 3,
            "title": "Fonksiyon Ustasi",
            "desc": "Fonksiyon konusundan 5 soru",
            "type": "quiz",
            "target": 5,
            "xp": 40,
        },
        {
            "step": 4,
            "title": "Limit Seferi",
            "desc": "Limit sorularinda %80+ basari",
            "type": "accuracy",
            "target": 80,
            "xp": 50,
        },
        {
            "step": 5,
            "title": "Matematik Efendisi",
            "desc": "10 karisik soruda %70+ basari",
            "type": "boss",
            "target": 70,
            "xp": 100,
        },
    ],
    "fizik": [
        {
            "step": 1,
            "title": "Kuvvet Kesfet",
            "desc": "5 Newton sorusu coz",
            "type": "quiz",
            "target": 5,
            "xp": 20,
        },
        {
            "step": 2,
            "title": "Enerji Donusumu",
            "desc": "Enerji problemlerini coz",
            "type": "quiz",
            "target": 4,
            "xp": 30,
        },
        {
            "step": 3,
            "title": "Dalga Yolculugu",
            "desc": "Dalga mekanigindan 5 soru",
            "type": "quiz",
            "target": 5,
            "xp": 40,
        },
        {
            "step": 4,
            "title": "Elektrik Ustasi",
            "desc": "Elektrik konusunda %75+",
            "type": "accuracy",
            "target": 75,
            "xp": 50,
        },
        {
            "step": 5,
            "title": "Fizik Efendisi",
            "desc": "Boss meydan okumasi",
            "type": "boss",
            "target": 70,
            "xp": 100,
        },
    ],
    "kimya": [
        {
            "step": 1,
            "title": "Atom Modeli",
            "desc": "5 atom yapisi sorusu",
            "type": "quiz",
            "target": 5,
            "xp": 20,
        },
        {
            "step": 2,
            "title": "Periyodik Kesfet",
            "desc": "Element ozellikleri",
            "type": "quiz",
            "target": 4,
            "xp": 30,
        },
        {
            "step": 3,
            "title": "Kimyasal Baglar",
            "desc": "Bag turlerinden 5 soru",
            "type": "quiz",
            "target": 5,
            "xp": 40,
        },
        {
            "step": 4,
            "title": "Reaksiyon Dengesi",
            "desc": "%80+ basari",
            "type": "accuracy",
            "target": 80,
            "xp": 50,
        },
        {
            "step": 5,
            "title": "Kimya Efendisi",
            "desc": "Boss meydan okumasi",
            "type": "boss",
            "target": 70,
            "xp": 100,
        },
    ],
    "biyoloji": [
        {
            "step": 1,
            "title": "Hucre Yapisi",
            "desc": "5 hucre sorusu coz",
            "type": "quiz",
            "target": 5,
            "xp": 20,
        },
        {
            "step": 2,
            "title": "DNA Sifresi",
            "desc": "Genetik problemleri",
            "type": "quiz",
            "target": 4,
            "xp": 30,
        },
        {
            "step": 3,
            "title": "Ekosistem",
            "desc": "Ekoloji konusundan 5 soru",
            "type": "quiz",
            "target": 5,
            "xp": 40,
        },
        {
            "step": 4,
            "title": "Evrim Yolculugu",
            "desc": "%75+ basari",
            "type": "accuracy",
            "target": 75,
            "xp": 50,
        },
        {
            "step": 5,
            "title": "Biyoloji Efendisi",
            "desc": "Boss meydan okumasi",
            "type": "boss",
            "target": 70,
            "xp": 100,
        },
    ],
    "turkce": [
        {
            "step": 1,
            "title": "Sozcuk Bilgisi",
            "desc": "5 anlam sorusu",
            "type": "quiz",
            "target": 5,
            "xp": 20,
        },
        {
            "step": 2,
            "title": "Cumle Yapisi",
            "desc": "Cumle analizi",
            "type": "quiz",
            "target": 4,
            "xp": 30,
        },
        {
            "step": 3,
            "title": "Paragraf Ustasi",
            "desc": "5 paragraf sorusu",
            "type": "quiz",
            "target": 5,
            "xp": 40,
        },
        {
            "step": 4,
            "title": "Anlam Derinligi",
            "desc": "%80+ basari",
            "type": "accuracy",
            "target": 80,
            "xp": 50,
        },
        {
            "step": 5,
            "title": "Turkce Efendisi",
            "desc": "Boss meydan okumasi",
            "type": "boss",
            "target": 70,
            "xp": 100,
        },
    ],
    "tarih": [
        {
            "step": 1,
            "title": "Ilk Caglar",
            "desc": "5 tarih sorusu",
            "type": "quiz",
            "target": 5,
            "xp": 20,
        },
        {
            "step": 2,
            "title": "Osmanli Donemi",
            "desc": "Osmanli sorulari",
            "type": "quiz",
            "target": 4,
            "xp": 30,
        },
        {
            "step": 3,
            "title": "Cumhuriyet",
            "desc": "Inkilap tarihi",
            "type": "quiz",
            "target": 5,
            "xp": 40,
        },
        {
            "step": 4,
            "title": "Kronoloji Ustasi",
            "desc": "%75+ basari",
            "type": "accuracy",
            "target": 75,
            "xp": 50,
        },
        {
            "step": 5,
            "title": "Tarih Efendisi",
            "desc": "Boss meydan okumasi",
            "type": "boss",
            "target": 70,
            "xp": 100,
        },
    ],
}

# Varsayilan chain (tanimlanmamis realm'ler icin)
DEFAULT_CHAIN = [
    {
        "step": 1,
        "title": "Kesfet",
        "desc": "5 soru coz",
        "type": "quiz",
        "target": 5,
        "xp": 20,
    },
    {
        "step": 2,
        "title": "Pekistir",
        "desc": "4 soru daha",
        "type": "quiz",
        "target": 4,
        "xp": 30,
    },
    {
        "step": 3,
        "title": "Derinles",
        "desc": "5 zor soru",
        "type": "quiz",
        "target": 5,
        "xp": 40,
    },
    {
        "step": 4,
        "title": "Uzmanlas",
        "desc": "%75+ basari",
        "type": "accuracy",
        "target": 75,
        "xp": 50,
    },
    {
        "step": 5,
        "title": "Efendi",
        "desc": "Boss meydan okumasi",
        "type": "boss",
        "target": 70,
        "xp": 100,
    },
]


@router.get("/{slug}/quest-chain")
async def get_quest_chain(
    slug: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Realm'in quest chain'ini ve ogrencinin ilerlemesini getir."""
    realm = await _get_realm_or_404(slug, db)
    progress = await _get_or_create_progress(current_user.id, realm.id, db)
    await db.commit()

    chain = QUEST_CHAINS.get(slug, DEFAULT_CHAIN)
    current_step = progress.quest_stop or 0

    steps = []
    for q in chain:
        step_status = "locked"
        if q["step"] < current_step:
            step_status = "completed"
        elif q["step"] == current_step:
            step_status = "active"
        elif q["step"] == current_step + 1:
            step_status = "available"

        steps.append(
            {
                **q,
                "status": step_status,
            }
        )

    return {
        "realm_slug": slug,
        "realm_name": realm.name,
        "current_step": current_step,
        "total_steps": len(chain),
        "completed": progress.completed_at is not None,
        "steps": steps,
    }


@router.post("/{slug}/quest-chain/advance")
async def advance_quest_chain(
    slug: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Quest chain'de bir adim ilerle. XP odul ver."""
    realm = await _get_realm_or_404(slug, db)
    progress = await _get_or_create_progress(current_user.id, realm.id, db)

    if progress.completed_at is not None:
        return {
            "success": True,
            "message": "Alem zaten tamamlandi.",
            "already_completed": True,
        }

    chain = QUEST_CHAINS.get(slug, DEFAULT_CHAIN)
    current_step = progress.quest_stop or 0
    next_step = current_step + 1

    if next_step > len(chain):
        return {
            "success": True,
            "message": "Tum adimlar tamamlandi.",
            "already_completed": True,
        }

    # Idempotency: Check if XP already granted for this step
    from models.gamification import XPTransaction

    existing_tx = await db.execute(
        select(XPTransaction).where(
            XPTransaction.student_id == str(current_user.id),
            XPTransaction.source == "realm_quest",
            XPTransaction.topic_id == f"{slug}_step{next_step}",
        )
    )
    if existing_tx.scalar_one_or_none():
        return {
            "success": True,
            "message": "Bu adim zaten tamamlandi.",
            "already_completed": True,
            "step_completed": next_step,
        }

    step_data = chain[next_step - 1]
    xp_reward = step_data["xp"]

    progress.quest_stop = next_step
    progress.xp_earned = (progress.xp_earned or 0) + xp_reward

    # XP transaction with unique topic_id for idempotency
    xp_tx = XPTransaction(
        student_id=str(current_user.id),
        amount=xp_reward,
        source="realm_quest",
        topic_id=f"{slug}_step{next_step}",
    )
    db.add(xp_tx)

    # Son adim ise realm'i tamamla
    is_final = next_step >= len(chain)
    if is_final:
        progress.completed_at = datetime.now(UTC)

    # Use GamificationDBService instead of raw SQL
    await GamificationDBService.award_xp(
        student_id=str(current_user.id),
        amount=xp_reward,
        source="realm_quest",
        db=db,
    )

    await db.commit()

    return {
        "success": True,
        "realm_slug": slug,
        "step_completed": next_step,
        "step_title": step_data["title"],
        "xp_earned": xp_reward,
        "total_steps": len(chain),
        "realm_completed": is_final,
        "message": f"'{step_data['title']}' tamamlandi! +{xp_reward} XP"
        + (" Alem fethedildi!" if is_final else ""),
    }
