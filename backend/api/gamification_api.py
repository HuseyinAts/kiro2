"""
Gamification API - Oyunlaştırma ve Motivasyon Sistemi
P2.2: Enhanced with real database integration

Bu API, öğrencilerin puan kazanma, seviye atlama, rozet toplama ve
liderlik tablosunda yarışma özelliklerini sağlar.

Endpoints:
- Puan Sistemi: /api/v1/gamification/points/*
- Seviye Sistemi: /api/v1/gamification/level/*
- Rozet Sistemi: /api/v1/gamification/badges/*
- Liderlik Tablosu: /api/v1/gamification/leaderboard/*

P2.2 Enhancements:
- Database integration (PostgreSQL + Redis)
- ExperienceManager, BadgeManager, LeaderboardManager integration
- User achievement tracking
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from redis import Redis

from core.database import get_db, get_redis_client
from core.dependencies import get_current_user, AuthenticatedUser
from core.redis_cache import get_cache
from core.gamification.leaderboard_manager import (
    get_leaderboard_manager,
    LeaderboardType,
)
from models.user_achievement import UserAchievement

logger = logging.getLogger(__name__)

# Router oluştur
router = APIRouter(prefix="/api/v1/gamification", tags=["Gamification"])


# ============================================================================
# Pydantic Models
# ============================================================================


class PointTransaction(BaseModel):
    """Puan işlem kaydı"""

    id: str
    user_id: str
    points: int
    reason: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime


class PointSummary(BaseModel):
    """Puan özet bilgileri"""

    total_points: int = Field(..., description="Toplam puan")
    daily_points: int = Field(..., description="Bugün kazanılan puan")
    weekly_points: int = Field(..., description="Bu hafta kazanılan puan")
    last_updated: datetime = Field(..., description="Son güncelleme zamanı")


class LevelInfo(BaseModel):
    """Seviye bilgileri"""

    current_level: int = Field(..., description="Mevcut seviye")
    total_xp: int = Field(..., description="Toplam XP")
    xp_for_next_level: int = Field(..., description="Sonraki seviye için gereken XP")
    progress_percentage: float = Field(..., description="İlerleme yüzdesi")


class BadgeInfo(BaseModel):
    """Rozet bilgileri"""

    badge_id: str
    name: str
    description: str
    category: str  # study, exam, social, special, milestone
    rarity: str  # common, rare, legendary
    icon: str
    earned: bool
    earned_at: Optional[datetime] = None


class LeaderboardEntry(BaseModel):
    """Liderlik tablosu girdisi"""

    rank: int
    user_id: str
    username: str
    avatar: Optional[str] = None
    points: int
    level: int


class LeaderboardResponse(BaseModel):
    """Liderlik tablosu yanıtı"""

    period: str  # weekly, monthly, alltime
    entries: List[LeaderboardEntry]
    user_rank: Optional[int] = None
    total_users: int


# ============================================================================
# Temporary In-Memory Storage (Demo amaçlı)
# ============================================================================

# Gerçek implementasyonda bu veriler database ve Redis'ten gelecek
_user_points = {}  # user_id -> total_points
_point_transactions = []  # List of transactions
_user_levels = {}  # user_id -> level_info
_user_badges = {}  # user_id -> List[badge_id]


# ============================================================================
# Puan Sistemi Endpoints
# ============================================================================


@router.get("/points", response_model=Dict[str, Any])
async def get_points_summary(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Kullanıcının puan özetini getir

    Returns:
        - total_points: Toplam puan
        - daily_points: Bugün kazanılan puan
        - weekly_points: Bu hafta kazanılan puan
    """
    try:
        user_id = str(current_user.id)
        # Redis cache kontrol
        cache = get_cache()
        cache_key = f"gamification_points:{user_id}"

        # Cache'den dene
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"[CACHE HIT] {cache_key}")
            return cached_result

        logger.info(f"[CACHE MISS] {cache_key}")
        logger.info(f"Puan özeti API çağrısı - Kullanıcı: {user_id}")

        # Demo data
        total_points = _user_points.get(user_id, 0)

        # Bugün ve bu hafta kazanılan puanları hesapla
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)

        daily_points = sum(
            t["points"]
            for t in _point_transactions
            if t["user_id"] == user_id and t["timestamp"] >= today_start
        )

        weekly_points = sum(
            t["points"]
            for t in _point_transactions
            if t["user_id"] == user_id and t["timestamp"] >= week_start
        )

        summary = PointSummary(
            total_points=total_points,
            daily_points=daily_points,
            weekly_points=weekly_points,
            last_updated=now,
        )

        result = {
            "success": True,
            "data": summary.model_dump(mode="json"),  # JSON-safe serialization
            "message": "Puan özeti başarıyla getirildi",
        }

        # Sonucu cache'le (5 dakika TTL)
        cache.set(cache_key, result, ttl=300)
        logger.info(f"[CACHE SET] {cache_key} (TTL: 300s)")

        return result

    except Exception as e:
        logger.error(f"Puan özeti hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Puan özeti alınamadı: {str(e)}")


@router.get("/points/history", response_model=Dict[str, Any])
async def get_point_history(
    current_user: AuthenticatedUser = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365, description="Kaç günlük geçmiş"),
    limit: Optional[int] = Query(
        None, ge=1, le=1000, description="Maksimum kayıt sayısı"
    ),
):
    """
    Kullanıcının puan geçmişini getir

    Args:
        days: Kaç günlük geçmiş (default: 30)
        limit: Maksimum kayıt sayısı
    """
    try:
        user_id = str(current_user.id)
        logger.info(f"Puan geçmişi API çağrısı - Kullanıcı: {user_id}, Gün: {days}")

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Kullanıcının işlemlerini filtrele
        transactions = [
            t
            for t in _point_transactions
            if t["user_id"] == user_id and t["timestamp"] >= cutoff_date
        ]

        # Tarihe göre sırala (en yeni önce)
        transactions.sort(key=lambda x: x["timestamp"], reverse=True)

        # Limit uygula
        if limit:
            transactions = transactions[:limit]

        return {
            "success": True,
            "data": {
                "transactions": transactions,
                "total_count": len(transactions),
                "period_days": days,
            },
            "message": f"Son {days} günlük puan geçmişi getirildi",
        }

    except Exception as e:
        logger.error(f"Puan geçmişi hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Puan geçmişi alınamadı: {str(e)}")


@router.post("/points/award", response_model=Dict[str, Any])
async def award_points(
    current_user: AuthenticatedUser = Depends(get_current_user),
    points: int = Query(..., ge=1, le=1000, description="Verilecek puan miktarı"),
    reason: str = Query(..., description="Puan verme nedeni"),
):
    """
    Kullanıcıya puan ver (authenticated user kendine puan verir)

    Args:
        points: Verilecek puan miktarı
        reason: Puan verme nedeni
    """
    try:
        user_id = str(current_user.id)
        logger.info(
            f"Puan verme API çağrısı - Kullanıcı: {user_id}, Puan: {points}, Neden: {reason}"
        )

        # Toplam puanı güncelle
        current_points = _user_points.get(user_id, 0)
        new_points = current_points + points
        _user_points[user_id] = new_points

        # Transaction kaydet
        transaction = {
            "id": f"txn_{len(_point_transactions) + 1}",
            "user_id": user_id,
            "points": points,
            "reason": reason,
            "metadata": None,
            "timestamp": datetime.now(timezone.utc),
        }
        _point_transactions.append(transaction)

        return {
            "success": True,
            "data": {"transaction": transaction, "new_total": new_points},
            "message": f"{points} puan başarıyla verildi",
        }

    except Exception as e:
        logger.error(f"Puan verme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Puan verilemedi: {str(e)}")


# ============================================================================
# Seviye Sistemi Endpoints
# ============================================================================


@router.get("/level", response_model=Dict[str, Any])
async def get_level_info(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Kullanıcının seviye bilgilerini getir

    Returns:
        - current_level: Mevcut seviye
        - total_xp: Toplam XP
        - xp_for_next_level: Sonraki seviye için gereken XP
        - progress_percentage: İlerleme yüzdesi
    """
    try:
        user_id = str(current_user.id)
        logger.info(f"Seviye bilgisi API çağrısı - Kullanıcı: {user_id}")

        # Demo data - Gerçek implementasyonda ExperienceManager kullanılacak
        total_xp = _user_points.get(user_id, 0)  # XP = Points for demo
        current_level = calculate_level(total_xp)
        xp_for_next = xp_for_level(current_level + 1) - xp_for_level(current_level)
        xp_in_current_level = total_xp - xp_for_level(current_level)
        progress_percentage = (
            (xp_in_current_level / xp_for_next) * 100 if xp_for_next > 0 else 0
        )

        level_info = LevelInfo(
            current_level=current_level,
            total_xp=total_xp,
            xp_for_next_level=xp_for_next,
            progress_percentage=round(progress_percentage, 2),
        )

        return {
            "success": True,
            "data": level_info.model_dump(),
            "message": "Seviye bilgisi başarıyla getirildi",
        }

    except Exception as e:
        logger.error(f"Seviye bilgisi hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Seviye bilgisi alınamadı: {str(e)}"
        )


@router.get("/level/progress", response_model=Dict[str, Any])
async def get_level_progress(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Sonraki seviyeye ilerleme detaylarını getir
    """
    try:
        user_id = str(current_user.id)
        logger.info(f"Seviye ilerlemesi API çağrısı - Kullanıcı: {user_id}")

        total_xp = _user_points.get(user_id, 0)
        current_level = calculate_level(total_xp)
        current_level_xp = xp_for_level(current_level)
        next_level_xp = xp_for_level(current_level + 1)
        xp_in_current_level = total_xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp

        return {
            "success": True,
            "data": {
                "current_level": current_level,
                "total_xp": total_xp,
                "xp_in_current_level": xp_in_current_level,
                "xp_needed_for_next": xp_needed,
                "progress_percentage": round((xp_in_current_level / xp_needed) * 100, 2)
                if xp_needed > 0
                else 0,
            },
            "message": "Seviye ilerlemesi başarıyla getirildi",
        }

    except Exception as e:
        logger.error(f"Seviye ilerlemesi hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Seviye ilerlemesi alınamadı: {str(e)}"
        )


# ============================================================================
# Rozet Sistemi Endpoints
# ============================================================================


@router.get("/badges", response_model=Dict[str, Any])
async def get_all_badges(
    current_user: AuthenticatedUser = Depends(get_current_user),
    category: Optional[str] = Query(None, description="Kategori filtresi"),
):
    """
    Tüm rozetleri getir (kazanılan + kazanılmayan)

    Args:
        category: Kategori filtresi (study, exam, social, special, milestone)
    """
    try:
        user_id = str(current_user.id)
        logger.info(
            f"Tüm rozetler API çağrısı - Kullanıcı: {user_id}, Kategori: {category}"
        )

        # Demo badge definitions
        all_badges = get_badge_definitions()

        # Kategori filtresi uygula
        if category:
            all_badges = [b for b in all_badges if b["category"] == category]

        # Kullanıcının kazandığı rozetler
        earned_badge_ids = _user_badges.get(user_id, [])

        # Badge bilgilerini hazırla
        badges = []
        for badge_def in all_badges:
            badge_info = BadgeInfo(
                badge_id=badge_def["id"],
                name=badge_def["name"],
                description=badge_def["description"],
                category=badge_def["category"],
                rarity=badge_def["rarity"],
                icon=badge_def["icon"],
                earned=badge_def["id"] in earned_badge_ids,
                earned_at=None,  # Gerçek implementasyonda timestamp olacak
            )
            badges.append(badge_info.model_dump())

        return {
            "success": True,
            "data": {
                "badges": badges,
                "total_count": len(badges),
                "earned_count": len(earned_badge_ids),
            },
            "message": "Rozetler başarıyla getirildi",
        }

    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()
        logger.error(f"Rozetler getirme hatası: {str(e)}\nTraceback: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Rozetler getirilemedi: {str(e)}\nTrace: {error_trace}",
        )


@router.get("/badges/earned", response_model=Dict[str, Any])
async def get_earned_badges(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Sadece kazanılan rozetleri getir
    """
    try:
        user_id = str(current_user.id)
        logger.info(f"Kazanılan rozetler API çağrısı - Kullanıcı: {user_id}")

        earned_badge_ids = _user_badges.get(user_id, [])
        all_badges = get_badge_definitions()

        earned_badges = []
        for badge_def in all_badges:
            if badge_def["id"] in earned_badge_ids:
                badge_info = BadgeInfo(
                    badge_id=badge_def["id"],
                    name=badge_def["name"],
                    description=badge_def["description"],
                    category=badge_def["category"],
                    rarity=badge_def["rarity"],
                    icon=badge_def["icon"],
                    earned=True,
                    earned_at=datetime.now(timezone.utc),  # Demo
                )
                earned_badges.append(badge_info.model_dump())

        return {
            "success": True,
            "data": {"badges": earned_badges, "count": len(earned_badges)},
            "message": "Kazanılan rozetler başarıyla getirildi",
        }

    except Exception as e:
        logger.error(f"Kazanılan rozetler hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Kazanılan rozetler getirilemedi: {str(e)}"
        )


@router.get("/badges/categories", response_model=Dict[str, Any])
async def get_badge_categories(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Kategori bazlı rozet istatistikleri
    """
    try:
        user_id = str(current_user.id)
        logger.info(f"Rozet kategorileri API çağrısı - Kullanıcı: {user_id}")

        all_badges = get_badge_definitions()
        earned_badge_ids = _user_badges.get(user_id, [])

        # Kategori bazlı istatistikler
        categories = {}
        for badge in all_badges:
            cat = badge["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "earned": 0}
            categories[cat]["total"] += 1
            if badge["id"] in earned_badge_ids:
                categories[cat]["earned"] += 1

        # Tamamlanma yüzdelerini hesapla
        for cat in categories:
            total = categories[cat]["total"]
            earned = categories[cat]["earned"]
            categories[cat]["completion_percentage"] = (
                round((earned / total) * 100, 2) if total > 0 else 0
            )

        return {
            "success": True,
            "data": {"categories": categories},
            "message": "Kategori istatistikleri başarıyla getirildi",
        }

    except Exception as e:
        logger.error(f"Kategori istatistikleri hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Kategori istatistikleri alınamadı: {str(e)}"
        )


# ============================================================================
# Liderlik Tablosu Endpoints
# ============================================================================


@router.get("/leaderboard", response_model=Dict[str, Any])
async def get_leaderboard(
    current_user: AuthenticatedUser = Depends(get_current_user),
    period: str = Query(
        "alltime", description="Zaman dilimi (weekly, monthly, alltime)"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Kaç kişi gösterilecek"),
):
    """
    Liderlik tablosunu getir

    Args:
        period: Zaman dilimi (weekly, monthly, alltime)
        limit: Kaç kişi gösterilecek
    """
    try:
        user_id = str(current_user.id)
        # Redis cache kontrol
        cache = get_cache()
        cache_key = f"leaderboard:{period}:{limit}"

        # Cache'den dene
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"[CACHE HIT] {cache_key}")
            return cached_result

        logger.info(f"[CACHE MISS] {cache_key}")
        logger.info(f"Liderlik tablosu API çağrısı - Period: {period}, Limit: {limit}")

        # Demo data - Gerçek implementasyonda Redis Sorted Sets kullanılacak
        # Tüm kullanıcıları puana göre sırala
        sorted_users = sorted(_user_points.items(), key=lambda x: x[1], reverse=True)

        # İlk N kullanıcıyı al
        top_users = sorted_users[:limit]

        # Leaderboard entries oluştur
        entries = []
        for rank, (uid, points) in enumerate(top_users, 1):
            level = calculate_level(points)
            entry = LeaderboardEntry(
                rank=rank,
                user_id=uid,
                username=f"User_{uid[:8]}",  # Demo
                avatar=None,
                points=points,
                level=level,
            )
            entries.append(entry)

        # Kullanıcının kendi sıralaması
        user_rank = None
        if user_id:
            for rank, (uid, _) in enumerate(sorted_users, 1):
                if uid == user_id:
                    user_rank = rank
                    break

        response = LeaderboardResponse(
            period=period,
            entries=entries,
            user_rank=user_rank,
            total_users=len(_user_points),
        )

        result = {
            "success": True,
            "data": response.model_dump(),
            "message": "Liderlik tablosu başarıyla getirildi",
        }

        # Sonucu cache'le (1 dakika TTL - leaderboard sık değişir)
        cache.set(cache_key, result, ttl=60)
        logger.info(f"[CACHE SET] {cache_key} (TTL: 60s)")

        return result

    except Exception as e:
        logger.error(f"Liderlik tablosu hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Liderlik tablosu alınamadı: {str(e)}"
        )


# ============================================================================
# Helper Functions
# ============================================================================


def calculate_level(total_xp: int) -> int:
    """
    Toplam XP'den seviye hesapla
    Formula: Level * 100 * 1.5^Level
    """
    level = 1
    while xp_for_level(level) <= total_xp:
        level += 1
    return level - 1


def xp_for_level(level: int) -> int:
    """Belirli bir seviyeye ulaşmak için gereken toplam XP"""
    if level == 1:
        return 0
    return sum(int(l * 100 * (1.5**l)) for l in range(1, level))


def get_badge_definitions() -> List[Dict[str, Any]]:
    """Rozet tanımlarını getir (Demo)"""
    return [
        # Çalışma Rozetleri
        {
            "id": "consistent_7",
            "name": "Kararlı Öğrenci",
            "description": "7 gün üst üste çalış",
            "category": "study",
            "rarity": "common",
            "icon": "badge_fire",
        },
        {
            "id": "consistent_30",
            "name": "Azimli Öğrenci",
            "description": "30 gün üst üste çalış",
            "category": "study",
            "rarity": "rare",
            "icon": "badge_muscle",
        },
        {
            "id": "consistent_100",
            "name": "Efsane Öğrenci",
            "description": "100 gün üst üste çalış",
            "category": "study",
            "rarity": "legendary",
            "icon": "badge_crown",
        },
        # Sınav Rozetleri
        {
            "id": "first_exam_80",
            "name": "Parlak Başlangıç",
            "description": "İlk denemede %80 üzeri al",
            "category": "exam",
            "rarity": "common",
            "icon": "badge_star",
        },
        {
            "id": "perfect_score",
            "name": "Mükemmeliyetçi",
            "description": "Tam puan al",
            "category": "exam",
            "rarity": "rare",
            "icon": "badge_100",
        },
        # Sosyal Rozetler
        {
            "id": "top_10",
            "name": "Yıldız Öğrenci",
            "description": "Liderlik tablosunda ilk 10'a gir",
            "category": "social",
            "rarity": "rare",
            "icon": "badge_sparkle",
        },
        # Özel Rozetler
        {
            "id": "night_owl",
            "name": "Gece Kuşu",
            "description": "Gece 00:00-06:00 arası çalış",
            "category": "special",
            "rarity": "common",
            "icon": "badge_owl",
        },
        {
            "id": "early_bird",
            "name": "Erken Kuş",
            "description": "Sabah 05:00-07:00 arası çalış",
            "category": "special",
            "rarity": "common",
            "icon": "badge_bird",
        },
        # Milestone Rozetleri
        {
            "id": "level_10",
            "name": "Seviye 10 Ustası",
            "description": "10. seviyeye ulaş",
            "category": "milestone",
            "rarity": "common",
            "icon": "badge_trophy",
        },
        {
            "id": "level_50",
            "name": "Seviye 50 Efsanesi",
            "description": "50. seviyeye ulaş",
            "category": "milestone",
            "rarity": "legendary",
            "icon": "badge_crown_gold",
        },
    ]


# ============================================================================
# P2.2: New Achievement Endpoints
# ============================================================================


@router.get("/achievements", response_model=Dict[str, Any])
async def get_user_achievements(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Kullanıcının tüm başarılarını getir (P2.2)

    Returns:
        - achievements: Tüm başarılar (tamamlanmış + devam eden)
        - completed_count: Tamamlanmış başarı sayısı
        - in_progress_count: Devam eden başarı sayısı
    """
    try:
        user_id = str(current_user.id)
        logger.info(f"Başarılar API çağrısı - Kullanıcı: {user_id}")

        # Kullanıcının başarılarını getir
        achievements = (
            db.query(UserAchievement)
            .filter(UserAchievement.user_id == UUID(user_id))
            .order_by(
                UserAchievement.is_completed.desc(),
                UserAchievement.progress_percentage.desc(),
            )
            .all()
        )

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
            "message": "Başarılar başarıyla getirildi",
        }

    except Exception as e:
        logger.error(f"Başarılar getirme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Başarılar getirilemedi: {str(e)}")


@router.get("/achievements/completed", response_model=Dict[str, Any])
async def get_completed_achievements(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Sadece tamamlanmış başarıları getir (P2.2)
    """
    try:
        user_id = str(current_user.id)
        logger.info(f"Tamamlanmış başarılar API çağrısı - Kullanıcı: {user_id}")

        completed = (
            db.query(UserAchievement)
            .filter(
                UserAchievement.user_id == UUID(user_id),
                UserAchievement.is_completed == True,
            )
            .order_by(UserAchievement.completed_at.desc())
            .all()
        )

        return {
            "success": True,
            "data": {
                "achievements": [a.to_dict() for a in completed],
                "count": len(completed),
            },
            "message": "Tamamlanmış başarılar başarıyla getirildi",
        }

    except Exception as e:
        logger.error(f"Tamamlanmış başarılar hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Tamamlanmış başarılar getirilemedi: {str(e)}"
        )


@router.get("/leaderboard/nearby", response_model=Dict[str, Any])
async def get_nearby_users_in_leaderboard(
    current_user: AuthenticatedUser = Depends(get_current_user),
    leaderboard_type: str = Query(
        LeaderboardType.GLOBAL, description="Liderlik tablosu türü"
    ),
    range_size: int = Query(
        5, ge=1, le=20, description="Her iki yöndeki kullanıcı sayısı"
    ),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
):
    """
    Liderlik tablosunda kullanıcının yakınındaki kullanıcıları getir (P2.2)

    Args:
        leaderboard_type: Liderlik tablosu türü (global:xp, weekly:xp, etc.)
        range_size: Her iki yöndeki kullanıcı sayısı
    """
    try:
        user_id = str(current_user.id)
        logger.info(
            f"Yakındaki kullanıcılar API çağrısı - Kullanıcı: {user_id}, Tür: {leaderboard_type}"
        )

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
            "message": "Yakındaki kullanıcılar başarıyla getirildi",
        }

    except Exception as e:
        logger.error(f"Yakındaki kullanıcılar hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Yakındaki kullanıcılar getirilemedi: {str(e)}"
        )


@router.get("/leaderboard/rank", response_model=Dict[str, Any])
async def get_user_leaderboard_rank(
    current_user: AuthenticatedUser = Depends(get_current_user),
    leaderboard_type: str = Query(
        LeaderboardType.GLOBAL, description="Liderlik tablosu türü"
    ),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
):
    """
    Kullanıcının liderlik tablosundaki sıralamasını getir (P2.2)

    Returns:
        - rank: Sıralama
        - score: Skor
        - total_users: Toplam kullanıcı sayısı
        - percentile: Yüzdelik dilim
    """
    try:
        user_id = str(current_user.id)
        logger.info(
            f"Kullanıcı sıralaması API çağrısı - Kullanıcı: {user_id}, Tür: {leaderboard_type}"
        )

        leaderboard_manager = get_leaderboard_manager(db, redis)

        rank_info = leaderboard_manager.get_user_rank(
            user_id=UUID(user_id), leaderboard_type=leaderboard_type
        )

        if not rank_info:
            return {
                "success": False,
                "data": None,
                "message": "Kullanıcı liderlik tablosunda bulunamadı",
            }

        return {
            "success": True,
            "data": rank_info,
            "message": "Kullanıcı sıralaması başarıyla getirildi",
        }

    except Exception as e:
        logger.error(f"Kullanıcı sıralaması hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Kullanıcı sıralaması getirilemedi: {str(e)}"
        )


@router.get("/leaderboard/stats", response_model=Dict[str, Any])
async def get_leaderboard_statistics(
    current_user: AuthenticatedUser = Depends(get_current_user),
    leaderboard_type: str = Query(
        LeaderboardType.GLOBAL, description="Liderlik tablosu türü"
    ),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
):
    """
    Liderlik tablosu istatistiklerini getir (P2.2)

    Returns:
        - total_users: Toplam kullanıcı sayısı
        - top_score: En yüksek skor
        - avg_score: Ortalama skor
    """
    try:
        logger.info(
            f"Liderlik tablosu istatistikleri API çağrısı - Tür: {leaderboard_type}"
        )

        leaderboard_manager = get_leaderboard_manager(db, redis)

        stats = leaderboard_manager.get_leaderboard_stats(leaderboard_type)

        return {
            "success": True,
            "data": stats,
            "message": "Liderlik tablosu istatistikleri başarıyla getirildi",
        }

    except Exception as e:
        logger.error(f"Liderlik tablosu istatistikleri hatası: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Liderlik tablosu istatistikleri alınamadı: {str(e)}",
        )
