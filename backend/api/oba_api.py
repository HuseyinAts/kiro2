"""
Oba (Guild/Clan) API - Topluluk Sistemi
Endpoints: /api/v1/oba/*

Ozellikler:
- Oba olustur / detay / listele
- Katil / ayril
- Uyeler listesi
- XP havuzu
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.dependencies import AuthenticatedUser, get_current_user
from models.gamification import Oba, ObaUye

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/oba", tags=["Oba (Guild)"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ObaCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)


class ObaOut(BaseModel):
    id: int
    name: str
    description: str | None
    xp_pool: int
    max_members: int
    member_count: int
    my_role: str | None = None


class ObaUyeOut(BaseModel):
    user_id: str
    display_name: str
    role: str
    joined_at: str | None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/list", response_model=dict[str, Any])
async def list_obalar(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    """Tum obalari listele."""
    result = await db.execute(
        select(Oba).order_by(Oba.xp_pool.desc()).offset(offset).limit(limit)
    )
    obalar = result.scalars().all()

    # Her oba icin uye sayisi
    items = []
    for oba in obalar:
        count_r = await db.execute(
            select(func.count()).select_from(ObaUye).where(ObaUye.oba_id == oba.id)
        )
        member_count = count_r.scalar() or 0

        # Kullanicinin rolu
        my_r = await db.execute(
            select(ObaUye.role).where(
                ObaUye.oba_id == oba.id, ObaUye.user_id == str(current_user.id)
            )
        )
        my_role = my_r.scalar_one_or_none()

        items.append(
            ObaOut(
                id=oba.id,
                name=oba.name,
                description=oba.description,
                xp_pool=oba.xp_pool or 0,
                max_members=oba.max_members or 20,
                member_count=member_count,
                my_role=my_role,
            )
        )

    return {"success": True, "data": items}


@router.get("/my", response_model=dict[str, Any])
async def get_my_oba(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Kullanicinin obasi."""
    user_id = str(current_user.id)
    result = await db.execute(select(ObaUye).where(ObaUye.user_id == user_id))
    membership = result.scalar_one_or_none()
    if not membership:
        return {
            "success": True,
            "data": None,
            "message": "Henuz bir obaya katilmadiniz",
        }

    oba_r = await db.execute(select(Oba).where(Oba.id == membership.oba_id))
    oba = oba_r.scalar_one_or_none()
    if not oba:
        return {"success": False, "data": None, "message": "Oba bulunamadi"}

    count_r = await db.execute(
        select(func.count()).select_from(ObaUye).where(ObaUye.oba_id == oba.id)
    )
    member_count = count_r.scalar() or 0

    return {
        "success": True,
        "data": ObaOut(
            id=oba.id,
            name=oba.name,
            description=oba.description,
            xp_pool=oba.xp_pool or 0,
            max_members=oba.max_members or 20,
            member_count=member_count,
            my_role=membership.role,
        ).model_dump(),
    }


@router.post("/create", response_model=dict[str, Any])
async def create_oba(
    body: ObaCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Yeni oba olustur. Olusturan otomatik 'bey' olur."""
    user_id = str(current_user.id)

    # Zaten bir obada mi?
    existing = await db.execute(select(ObaUye).where(ObaUye.user_id == user_id))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Zaten bir obaya uyesiniz. Once ayrilin.")

    # Isim benzersiz mi?
    name_check = await db.execute(select(Oba).where(Oba.name == body.name))
    if name_check.scalar_one_or_none():
        raise HTTPException(400, "Bu isimde bir oba zaten var.")

    oba = Oba(name=body.name, description=body.description)
    db.add(oba)
    await db.flush()

    member = ObaUye(oba_id=oba.id, user_id=user_id, role="bey")
    db.add(member)
    await db.commit()

    return {
        "success": True,
        "data": {"oba_id": oba.id, "name": oba.name, "role": "bey"},
        "message": f"'{oba.name}' obasi olusturuldu!",
    }


@router.post("/{oba_id}/join", response_model=dict[str, Any])
async def join_oba(
    oba_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Obaya katil."""
    user_id = str(current_user.id)

    # Zaten bir obada mi?
    existing = await db.execute(select(ObaUye).where(ObaUye.user_id == user_id))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Zaten bir obaya uyesiniz.")

    # Oba var mi?
    oba_r = await db.execute(select(Oba).where(Oba.id == oba_id))
    oba = oba_r.scalar_one_or_none()
    if not oba:
        raise HTTPException(404, "Oba bulunamadi.")

    # Dolu mu?
    count_r = await db.execute(
        select(func.count()).select_from(ObaUye).where(ObaUye.oba_id == oba_id)
    )
    member_count = count_r.scalar() or 0
    if member_count >= (oba.max_members or 20):
        raise HTTPException(400, "Oba dolu.")

    member = ObaUye(oba_id=oba_id, user_id=user_id, role="toycu")
    db.add(member)
    await db.commit()

    return {
        "success": True,
        "data": {"oba_id": oba_id, "role": "toycu"},
        "message": f"'{oba.name}' obasina katildiniz!",
    }


@router.post("/leave", response_model=dict[str, Any])
async def leave_oba(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Obadan ayril."""
    user_id = str(current_user.id)

    result = await db.execute(select(ObaUye).where(ObaUye.user_id == user_id))
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(400, "Herhangi bir obaya uye degilsiniz.")

    # Bey ayrilirsa ve baska uye varsa, en eski uyeyi bey yap
    if membership.role == "bey":
        next_r = await db.execute(
            select(ObaUye)
            .where(ObaUye.oba_id == membership.oba_id, ObaUye.user_id != user_id)
            .order_by(ObaUye.joined_at)
            .limit(1)
        )
        next_member = next_r.scalar_one_or_none()
        if next_member:
            next_member.role = "bey"
        else:
            # Son uye — obayi sil
            oba_r = await db.execute(select(Oba).where(Oba.id == membership.oba_id))
            oba = oba_r.scalar_one_or_none()
            if oba:
                await db.delete(oba)

    await db.delete(membership)
    await db.commit()

    return {"success": True, "message": "Obadan ayrildiniz."}


@router.get("/{oba_id}/members", response_model=dict[str, Any])
async def get_oba_members(
    oba_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Oba uyelerini getir."""
    from models.user import User

    result = await db.execute(
        select(ObaUye, User)
        .join(User, User.id == ObaUye.user_id)
        .where(ObaUye.oba_id == oba_id)
        .order_by(
            # bey > noker > toycu
            func.case(
                (ObaUye.role == "bey", 1),
                (ObaUye.role == "noker", 2),
                else_=3,
            )
        )
    )
    rows = result.all()

    members = []
    for uye, user in rows:
        members.append(
            ObaUyeOut(
                user_id=uye.user_id,
                display_name=getattr(user, "display_name", None)
                or getattr(user, "full_name", None)
                or uye.user_id[:8],
                role=uye.role or "toycu",
                joined_at=uye.joined_at.isoformat() if uye.joined_at else None,
            )
        )

    return {"success": True, "data": members}


@router.post("/{oba_id}/promote/{target_user_id}", response_model=dict[str, Any])
async def promote_member(
    oba_id: int,
    target_user_id: str,
    new_role: str = Query(..., pattern="^(toycu|noker|bey)$"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Uye rolunu degistir (sadece bey yapabilir)."""
    user_id = str(current_user.id)

    # Ben bey miyim?
    my_r = await db.execute(
        select(ObaUye).where(ObaUye.oba_id == oba_id, ObaUye.user_id == user_id)
    )
    my_membership = my_r.scalar_one_or_none()
    if not my_membership or my_membership.role != "bey":
        raise HTTPException(403, "Sadece bey rol degistirebilir.")

    # Hedef uye
    target_r = await db.execute(
        select(ObaUye).where(ObaUye.oba_id == oba_id, ObaUye.user_id == target_user_id)
    )
    target = target_r.scalar_one_or_none()
    if not target:
        raise HTTPException(404, "Uye bulunamadi.")

    # Bey devrederek
    if new_role == "bey":
        my_membership.role = "noker"

    target.role = new_role
    await db.commit()

    return {"success": True, "message": f"Rol guncellendi: {new_role}"}
