"""
Gamification API - Oyunlastirma ve Motivasyon Sistemi
DB-backed: XPTransaction, Streak, Badge tablolari uzerinden calisir.

Endpoints:
- Puan Sistemi: /api/v1/gamification/points/*
- Seviye Sistemi: /api/v1/gamification/level/*
- Rozet Sistemi: /api/v1/gamification/badges/*
- Liderlik Tablosu: /api/v1/gamification/leaderboard/*
- Basarilar: /api/v1/gamification/achievements/*
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from core.database import get_db, get_db_session, get_redis_client
from core.dependencies import AuthenticatedUser, get_current_user
from core.gamification.leaderboard_manager import (
    LeaderboardType,
    get_leaderboard_manager,
)
from core.redis_cache import get_cache
from models.user_achievement import UserAchievement
from services.learning_event_service import GamificationDBService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/gamification", tags=["Gamification"])


# ============================================================================
# Pydantic Models
# ============================================================================


class PointSummary(BaseModel):
    total_points: int = Field(..., description="Toplam puan")
    daily_points: int = Field(..., description="Bugun kazanilan puan")
    weekly_points: int = Field(..., description="Bu hafta kazanilan puan")
    last_updated: datetime = Field(..., description="Son guncelleme zamani")


class LevelInfo(BaseModel):
    current_level: int = Field(..., description="Mevcut seviye")
    total_xp: int = Field(..., description="Toplam XP")
    xp_for_next_level: int = Field(..., description="Sonraki seviye icin gereken XP")
    progress_percentage: float = Field(..., description="Ilerleme yuzdesi")


class BadgeInfo(BaseModel):
    badge_id: str
    name: str
    description: str
    category: str
    rarity: str
    icon: str
    earned: bool
    earned_at: datetime | None = None


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    username: str
    avatar: str | None = None
    points: int
    level: int


class LeaderboardResponse(BaseModel):
    period: str
    entries: list[LeaderboardEntry]
    user_rank: int | None = None
    total_users: int


# ============================================================================
# Puan Sistemi Endpoints (DB-backed)
# ============================================================================


@router.get("/points", response_model=dict[str, Any])
async def get_points_summary(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Kullanicinin puan ozetini getir (DB-backed)."""
    try:
        user_id = str(current_user.id)
        cache = get_cache()
        cache_key = f"gamification_points:{user_id}"

        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        summary_data = await GamificationDBService.get_points_summary(
            student_id=user_id, db=db
        )

        summary = PointSummary(
            total_points=summary_data["total_points"],
            daily_points=summary_data["daily_points"],
            weekly_points=summary_data["weekly_points"],
            last_updated=datetime.now(UTC),
        )

        result = {
            "success": True,
            "data": summary.model_dump(mode="json"),
            "message": "Puan ozeti basariyla getirildi",
        }

        cache.set(cache_key, result, ttl=300)
        return result

    except Exception as e:
        logger.error(f"Puan ozeti hatasi: {e!s}")
        raise HTTPException(status_code=500, detail=f"Puan ozeti alinamadi: {e!s}")


@router.get("/points/history", response_model=dict[str, Any])
async def get_point_history(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    days: int = Query(30, ge=1, le=365, description="Kac gunluk gecmis"),
    limit: int | None = Query(None, ge=1, le=1000, description="Maksimum kayit sayisi"),
):
    """Kullanicinin puan gecmisini getir (DB-backed)."""
    try:
        user_id = str(current_user.id)

        transactions = await GamificationDBService.get_point_history(
            student_id=user_id, days=days, limit=limit, db=db
        )

        return {
            "success": True,
            "data": {
                "transactions": transactions,
                "total_count": len(transactions),
                "period_days": days,
            },
            "message": f"Son {days} gunluk puan gecmisi getirildi",
        }

    except Exception as e:
        logger.error(f"Puan gecmisi hatasi: {e!s}")
        raise HTTPException(status_code=500, detail=f"Puan gecmisi alinamadi: {e!s}")


@router.post("/points/award", response_model=dict[str, Any])
async def award_points(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    points: int = Query(..., ge=1, le=1000, description="Verilecek puan miktari"),
    reason: str = Query(..., description="Puan verme nedeni"),
):
    """Kullaniciya puan ver (DB-backed)."""
    try:
        user_id = str(current_user.id)

        new_total = await GamificationDBService.award_xp(
            student_id=user_id,
            amount=points,
            source=reason,
            db=db,
        )
        await db.commit()

        # Invalidate points cache
        cache = get_cache()
        cache.delete(f"gamification_points:{user_id}")

        return {
            "success": True,
            "data": {
                "transaction": {
                    "user_id": user_id,
                    "points": points,
                    "reason": reason,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                "new_total": new_total,
            },
            "message": f"{points} puan basariyla verildi",
        }

    except Exception as e:
        logger.error(f"Puan verme hatasi: {e!s}")
        raise HTTPException(status_code=500, detail=f"Puan verilemedi: {e!s}")


# ============================================================================
# Seviye Sistemi Endpoints (DB-backed)
# ============================================================================


@router.get("/level", response_model=dict[str, Any])
async def get_level_info(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Kullanicinin seviye bilgilerini getir (DB-backed)."""
    try:
        user_id = str(current_user.id)

        summary = await GamificationDBService.get_points_summary(
            student_id=user_id, db=db
        )
        total_xp = summary["total_points"]
        current_level = calculate_level(total_xp)
        xp_for_next = xp_for_level(current_level + 1) - xp_for_level(current_level)
        xp_in_current = total_xp - xp_for_level(current_level)
        progress_pct = (xp_in_current / xp_for_next) * 100 if xp_for_next > 0 else 0

        level_info = LevelInfo(
            current_level=current_level,
            total_xp=total_xp,
            xp_for_next_level=xp_for_next,
            progress_percentage=round(progress_pct, 2),
        )

        return {
            "success": True,
            "data": level_info.model_dump(),
            "message": "Seviye bilgisi basariyla getirildi",
        }

    except Exception as e:
        logger.error(f"Seviye bilgisi hatasi: {e!s}")
        raise HTTPException(status_code=500, detail=f"Seviye bilgisi alinamadi: {e!s}")


@router.get("/level/progress", response_model=dict[str, Any])
async def get_level_progress(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Sonraki seviyeye ilerleme detaylarini getir."""
    try:
        user_id = str(current_user.id)

        summary = await GamificationDBService.get_points_summary(
            student_id=user_id, db=db
        )
        total_xp = summary["total_points"]
        current_level = calculate_level(total_xp)
        current_level_xp = xp_for_level(current_level)
        next_level_xp = xp_for_level(current_level + 1)
        xp_in_current = total_xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp

        return {
            "success": True,
            "data": {
                "current_level": current_level,
                "total_xp": total_xp,
                "xp_in_current_level": xp_in_current,
                "xp_needed_for_next": xp_needed,
                "progress_percentage": round((xp_in_current / xp_needed) * 100, 2)
                if xp_needed > 0
                else 0,
            },
            "message": "Seviye ilerlemesi basariyla getirildi",
        }

    except Exception as e:
        logger.error(f"Seviye ilerlemesi hatasi: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Seviye ilerlemesi alinamadi: {e!s}"
        )


# ============================================================================
# Rozet Sistemi Endpoints
# ============================================================================


@router.get("/badges", response_model=dict[str, Any])
async def get_all_badges(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    category: str | None = Query(None, description="Kategori filtresi"),
):
    """Tum rozetleri getir (kazanilan + kazanilmayan)."""
    try:
        user_id = str(current_user.id)

        all_badges = get_badge_definitions()
        if category:
            all_badges = [b for b in all_badges if b["category"] == category]

        # Check earned badges from DB
        from sqlalchemy import select

        from models.gamification import UserBadge as GamUserBadge

        result = await db.execute(
            select(GamUserBadge.badge_id).where(GamUserBadge.user_id == user_id)
        )
        earned_badge_db_ids = {row[0] for row in result.fetchall()}

        badges = []
        for badge_def in all_badges:
            badge_info = BadgeInfo(
                badge_id=badge_def["id"],
                name=badge_def["name"],
                description=badge_def["description"],
                category=badge_def["category"],
                rarity=badge_def["rarity"],
                icon=badge_def["icon"],
                earned=badge_def["id"] in [str(bid) for bid in earned_badge_db_ids],
                earned_at=None,
            )
            badges.append(badge_info.model_dump())

        return {
            "success": True,
            "data": {
                "badges": badges,
                "total_count": len(badges),
                "earned_count": sum(1 for b in badges if b["earned"]),
            },
            "message": "Rozetler basariyla getirildi",
        }

    except Exception as e:
        logger.error(f"Rozetler getirme hatasi: {e!s}")
        raise HTTPException(status_code=500, detail=f"Rozetler getirilemedi: {e!s}")


@router.get("/badges/earned", response_model=dict[str, Any])
async def get_earned_badges(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Sadece kazanilan rozetleri getir."""
    try:
        user_id = str(current_user.id)

        from sqlalchemy import select

        from models.gamification import UserBadge as GamUserBadge

        result = await db.execute(
            select(GamUserBadge).where(GamUserBadge.user_id == user_id)
        )
        earned_rows = result.scalars().all()

        all_badges = get_badge_definitions()
        badge_map = {b["id"]: b for b in all_badges}

        earned_badges = []
        for ub in earned_rows:
            badge_def = badge_map.get(str(ub.badge_id))
            if badge_def:
                earned_badges.append(
                    BadgeInfo(
                        badge_id=badge_def["id"],
                        name=badge_def["name"],
                        description=badge_def["description"],
                        category=badge_def["category"],
                        rarity=badge_def["rarity"],
                        icon=badge_def["icon"],
                        earned=True,
                        earned_at=ub.earned_at,
                    ).model_dump()
                )

        return {
            "success": True,
            "data": {"badges": earned_badges, "count": len(earned_badges)},
            "message": "Kazanilan rozetler basariyla getirildi",
        }

    except Exception as e:
        logger.error(f"Kazanilan rozetler hatasi: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Kazanilan rozetler getirilemedi: {e!s}"
        )


@router.get("/badges/categories", response_model=dict[str, Any])
async def get_badge_categories(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Kategori bazli rozet istatistikleri."""
    try:
        user_id = str(current_user.id)

        all_badges = get_badge_definitions()

        from sqlalchemy import select

        from models.gamification import UserBadge as GamUserBadge

        result = await db.execute(
            select(GamUserBadge.badge_id).where(GamUserBadge.user_id == user_id)
        )
        earned_ids = {str(row[0]) for row in result.fetchall()}

        categories: dict[str, dict[str, Any]] = {}
        for badge in all_badges:
            cat = badge["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "earned": 0}
            categories[cat]["total"] += 1
            if badge["id"] in earned_ids:
                categories[cat]["earned"] += 1

        for cat in categories:
            total = categories[cat]["total"]
            earned = categories[cat]["earned"]
            categories[cat]["completion_percentage"] = (
                round((earned / total) * 100, 2) if total > 0 else 0
            )

        return {
            "success": True,
            "data": {"categories": categories},
            "message": "Kategori istatistikleri basariyla getirildi",
        }

    except Exception as e:
        logger.error(f"Kategori istatistikleri hatasi: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Kategori istatistikleri alinamadi: {e!s}"
        )


# ============================================================================
# Liderlik Tablosu Endpoints
# ============================================================================


@router.get("/leaderboard", response_model=dict[str, Any])
async def get_leaderboard(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    period: str = Query(
        "alltime", description="Zaman dilimi (weekly, monthly, alltime)"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Kac kisi gosterilecek"),
):
    """Liderlik tablosunu getir (DB-backed)."""
    try:
        user_id = str(current_user.id)
        cache = get_cache()
        cache_key = f"leaderboard:{period}:{limit}"

        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        # Query top users by total_xp
        from sqlalchemy import select

        from models.database import User

        stmt = (
            select(User.id, User.email, User.total_xp)
            .where(User.total_xp > 0)
            .order_by(User.total_xp.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        rows = result.fetchall()

        entries = []
        user_rank = None
        for rank, row in enumerate(rows, 1):
            uid = str(row[0])
            xp = row[2] or 0
            level = calculate_level(xp)
            entries.append(
                LeaderboardEntry(
                    rank=rank,
                    user_id=uid,
                    username=row[1].split("@")[0] if row[1] else f"User_{uid[:8]}",
                    avatar=None,
                    points=xp,
                    level=level,
                ).model_dump()
            )
            if uid == user_id:
                user_rank = rank

        response_data = LeaderboardResponse(
            period=period,
            entries=[LeaderboardEntry(**e) for e in entries],
            user_rank=user_rank,
            total_users=len(rows),
        )

        result_dict = {
            "success": True,
            "data": response_data.model_dump(),
            "message": "Liderlik tablosu basariyla getirildi",
        }

        cache.set(cache_key, result_dict, ttl=60)
        return result_dict

    except Exception as e:
        logger.error(f"Liderlik tablosu hatasi: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Liderlik tablosu alinamadi: {e!s}"
        )


# ============================================================================
# Gamification Profile Endpoint (NEW)
# ============================================================================


@router.get("/profile", response_model=dict[str, Any])
async def get_gamification_profile(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Kullanicinin tam gamification profilini getir (XP + Level + Streak)."""
    try:
        user_id = str(current_user.id)

        summary = await GamificationDBService.get_points_summary(
            student_id=user_id, db=db
        )
        streak = await GamificationDBService.get_streak(student_id=user_id, db=db)

        total_xp = summary["total_points"]
        current_level = calculate_level(total_xp)
        xp_for_next = xp_for_level(current_level + 1) - xp_for_level(current_level)
        xp_in_current = total_xp - xp_for_level(current_level)

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "total_xp": total_xp,
                "daily_xp": summary["daily_points"],
                "weekly_xp": summary["weekly_points"],
                "current_level": current_level,
                "xp_for_next_level": xp_for_next,
                "level_progress_pct": round((xp_in_current / xp_for_next) * 100, 2)
                if xp_for_next > 0
                else 0,
                "streak": streak,
            },
            "message": "Gamification profili basariyla getirildi",
        }

    except Exception as e:
        logger.error(f"Gamification profil hatasi: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Gamification profili alinamadi: {e!s}"
        )


# ============================================================================
# Helper Functions
# ============================================================================


def calculate_level(total_xp: int) -> int:
    """Toplam XP'den seviye hesapla. Formula: Level * 100 * 1.5^Level"""
    level = 1
    while xp_for_level(level) <= total_xp:
        level += 1
    return level - 1


def xp_for_level(level: int) -> int:
    """Belirli bir seviyeye ulasmak icin gereken toplam XP."""
    if level == 1:
        return 0
    return sum(int(lv * 100 * (1.5**lv)) for lv in range(1, level))


def get_badge_definitions() -> list[dict[str, Any]]:
    """Rozet tanimlari."""
    return [
        {
            "id": "consistent_7",
            "name": "Kararli Ogrenci",
            "description": "7 gun ust uste calis",
            "category": "study",
            "rarity": "common",
            "icon": "badge_fire",
        },
        {
            "id": "consistent_30",
            "name": "Azimli Ogrenci",
            "description": "30 gun ust uste calis",
            "category": "study",
            "rarity": "rare",
            "icon": "badge_muscle",
        },
        {
            "id": "consistent_100",
            "name": "Efsane Ogrenci",
            "description": "100 gun ust uste calis",
            "category": "study",
            "rarity": "legendary",
            "icon": "badge_crown",
        },
        {
            "id": "first_exam_80",
            "name": "Parlak Baslangic",
            "description": "Ilk denemede %80 uzeri al",
            "category": "exam",
            "rarity": "common",
            "icon": "badge_star",
        },
        {
            "id": "perfect_score",
            "name": "Mukemmeliyetci",
            "description": "Tam puan al",
            "category": "exam",
            "rarity": "rare",
            "icon": "badge_100",
        },
        {
            "id": "top_10",
            "name": "Yildiz Ogrenci",
            "description": "Liderlik tablosunda ilk 10'a gir",
            "category": "social",
            "rarity": "rare",
            "icon": "badge_sparkle",
        },
        {
            "id": "night_owl",
            "name": "Gece Kusu",
            "description": "Gece 00:00-06:00 arasi calis",
            "category": "special",
            "rarity": "common",
            "icon": "badge_owl",
        },
        {
            "id": "early_bird",
            "name": "Erken Kus",
            "description": "Sabah 05:00-07:00 arasi calis",
            "category": "special",
            "rarity": "common",
            "icon": "badge_bird",
        },
        {
            "id": "level_10",
            "name": "Seviye 10 Ustasi",
            "description": "10. seviyeye ulas",
            "category": "milestone",
            "rarity": "common",
            "icon": "badge_trophy",
        },
        {
            "id": "level_50",
            "name": "Seviye 50 Efsanesi",
            "description": "50. seviyeye ulas",
            "category": "milestone",
            "rarity": "legendary",
            "icon": "badge_crown_gold",
        },
    ]


# ============================================================================
# P2.2: Achievement Endpoints (existing DB-backed)
# ============================================================================


@router.get("/achievements", response_model=dict[str, Any])
async def get_user_achievements(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Kullanicinin tum basarilarini getir (P2.2)."""
    try:
        from sqlalchemy import select as sa_select

        user_id = str(current_user.id)
        result = await db.execute(
            sa_select(UserAchievement)
            .where(UserAchievement.user_id == UUID(user_id))
            .order_by(
                UserAchievement.is_completed.desc(),
                UserAchievement.progress_percentage.desc(),
            )
        )
        achievements = result.scalars().all()

        completed_count = sum(1 for a in achievements if a.is_completed)
        in_progress_count = len(achievements) - completed_count

        return {
            "success": True,
            "data": {
                "achievements": [a.to_dict() for a in achievements],
                "completed_count": completed_count,
                "in_progress_count": in_progress_count,
                "total_count": len(achievements),
            },
            "message": "Basarilar basariyla getirildi",
        }
    except Exception as e:
        logger.error(f"Basarilar getirme hatasi: {e!s}")
        raise HTTPException(status_code=500, detail=f"Basarilar getirilemedi: {e!s}")


@router.get("/achievements/completed", response_model=dict[str, Any])
async def get_completed_achievements(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Sadece tamamlanmis basarilari getir (P2.2)."""
    try:
        from sqlalchemy import select as sa_select

        user_id = str(current_user.id)
        result = await db.execute(
            sa_select(UserAchievement)
            .where(
                UserAchievement.user_id == UUID(user_id),
                UserAchievement.is_completed == True,  # noqa: E712
            )
            .order_by(UserAchievement.completed_at.desc())
        )
        completed = result.scalars().all()

        return {
            "success": True,
            "data": {
                "achievements": [a.to_dict() for a in completed],
                "count": len(completed),
            },
            "message": "Tamamlanmis basarilar basariyla getirildi",
        }
    except Exception as e:
        logger.error(f"Tamamlanmis basarilar hatasi: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Tamamlanmis basarilar getirilemedi: {e!s}"
        )


@router.get("/leaderboard/nearby", response_model=dict[str, Any])
async def get_nearby_users_in_leaderboard(
    current_user: AuthenticatedUser = Depends(get_current_user),
    leaderboard_type: str = Query(
        LeaderboardType.GLOBAL, description="Liderlik tablosu turu"
    ),
    range_size: int = Query(
        5, ge=1, le=20, description="Her iki yondeki kullanici sayisi"
    ),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
):
    """Liderlik tablosunda kullanicinin yakinindaki kullanicilari getir (P2.2)."""
    try:
        user_id = str(current_user.id)
        leaderboard_manager = get_leaderboard_manager(db, redis)
        result = leaderboard_manager.get_nearby_users(
            user_id=UUID(user_id),
            leaderboard_type=leaderboard_type,
            range_size=range_size,
            with_details=True,
        )
        return {
            "success": True,
            "data": result,
            "message": "Yakindaki kullanicilar basariyla getirildi",
        }
    except Exception as e:
        logger.error(f"Yakindaki kullanicilar hatasi: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Yakindaki kullanicilar getirilemedi: {e!s}"
        )


@router.get("/leaderboard/rank", response_model=dict[str, Any])
async def get_user_leaderboard_rank(
    current_user: AuthenticatedUser = Depends(get_current_user),
    leaderboard_type: str = Query(
        LeaderboardType.GLOBAL, description="Liderlik tablosu turu"
    ),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
):
    """Kullanicinin liderlik tablosundaki siralamasini getir (P2.2)."""
    try:
        user_id = str(current_user.id)
        leaderboard_manager = get_leaderboard_manager(db, redis)
        rank_info = leaderboard_manager.get_user_rank(
            user_id=UUID(user_id), leaderboard_type=leaderboard_type
        )
        if not rank_info:
            return {
                "success": False,
                "data": None,
                "message": "Kullanici liderlik tablosunda bulunamadi",
            }
        return {
            "success": True,
            "data": rank_info,
            "message": "Kullanici siralamasi basariyla getirildi",
        }
    except Exception as e:
        logger.error(f"Kullanici siralamasi hatasi: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Kullanici siralamasi getirilemedi: {e!s}"
        )


@router.get("/leaderboard/stats", response_model=dict[str, Any])
async def get_leaderboard_statistics(
    current_user: AuthenticatedUser = Depends(get_current_user),
    leaderboard_type: str = Query(
        LeaderboardType.GLOBAL, description="Liderlik tablosu turu"
    ),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
):
    """Liderlik tablosu istatistiklerini getir (P2.2)."""
    try:
        leaderboard_manager = get_leaderboard_manager(db, redis)
        stats = leaderboard_manager.get_leaderboard_stats(leaderboard_type)
        return {
            "success": True,
            "data": stats,
            "message": "Liderlik tablosu istatistikleri basariyla getirildi",
        }
    except Exception as e:
        logger.error(f"Liderlik tablosu istatistikleri hatasi: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Liderlik tablosu istatistikleri alinamadi: {e!s}"
        )


# ============================================================================
# F14: Segmented Leaderboard
# ============================================================================


@router.get("/leaderboard/peer-group", response_model=dict[str, Any])
async def get_peer_group_leaderboard(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(20, ge=1, le=100, description="Kac kisi gosterilecek"),
    period: str = Query("weekly", description="Zaman dilimi (weekly, monthly)"),
):
    """Benzer seviye ogrenciler arasinda siralama (DB-backed)."""
    try:
        user_id = str(current_user.id)
        from sqlalchemy import select

        from models.database import User

        # Get user's XP
        user_result = await db.execute(select(User.total_xp).where(User.id == user_id))
        user_row = user_result.first()
        user_xp = user_row[0] if user_row else 0

        # Find peers within +/- 20% range
        tolerance = max(50, int(user_xp * 0.2))
        stmt = (
            select(User.id, User.total_xp)
            .where(User.total_xp.between(user_xp - tolerance, user_xp + tolerance))
            .order_by(User.total_xp.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        peers = result.fetchall()

        entries = []
        for rank, (uid, xp) in enumerate(peers, 1):
            entries.append(
                {
                    "user_id": str(uid),
                    "points": xp or 0,
                    "rank": rank,
                    "is_current_user": str(uid) == user_id,
                    "improvement": 0,
                }
            )

        return {
            "success": True,
            "data": {
                "entries": entries,
                "total_peers": len(peers),
                "user_rank": next(
                    (e["rank"] for e in entries if e["is_current_user"]), None
                ),
                "period": period,
            },
        }
    except Exception as e:
        logger.error(f"Peer group leaderboard hatasi: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Peer group leaderboard alinamadi: {e!s}"
        )


@router.get("/leaderboard/improvement", response_model=dict[str, Any])
async def get_improvement_leaderboard(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(10, ge=1, le=50, description="Top N gelisim"),
):
    """Bu haftanin en cok gelisen ogrencileri (DB-backed)."""
    try:
        from sqlalchemy import select

        from models.database import User

        stmt = (
            select(User.id, User.total_xp)
            .where(User.total_xp > 0)
            .order_by(User.total_xp.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        rows = result.fetchall()

        entries = []
        for rank, (uid, xp) in enumerate(rows, 1):
            entries.append(
                {
                    "user_id": str(uid),
                    "current_points": xp or 0,
                    "previous_points": xp or 0,
                    "improvement": 0,
                    "rank": rank,
                }
            )

        return {
            "success": True,
            "data": {"entries": entries, "period": "weekly"},
        }
    except Exception as e:
        logger.error(f"Improvement leaderboard hatasi: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Improvement leaderboard alinamadi: {e!s}"
        )
