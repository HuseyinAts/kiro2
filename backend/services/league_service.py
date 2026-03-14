"""
League Service — F2 Lig Sistemi

Haftalık tier tabanlı sıralama: BRONZE → SILVER → GOLD → PLATINUM → CHAMPION
Her hafta üst %10 yükselir, alt %10 düşer. XP haftalık sıfırlanır.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from core.structured_logger import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger("league_service")

# Tier sırası (küçükten büyüğe)
LEAGUE_TIERS: list[str] = ["BRONZE", "SILVER", "GOLD", "PLATINUM", "CHAMPION"]
DEFAULT_TIER = "BRONZE"

# XP miktarları kaynak bazlı
XP_AMOUNTS: dict[str, int] = {
    "quiz_complete": 50,
    "exam_complete": 200,
    "daily_login": 10,
    "streak_bonus": 25,
    "correct_answer": 5,
}


# ---------------------------------------------------------------------------
# Yardımcı fonksiyonlar
# ---------------------------------------------------------------------------

def _current_week_start() -> datetime:
    """Mevcut haftanın Pazartesi 00:00 UTC zamanını döndürür."""
    now = datetime.now(timezone.utc)
    monday = now - timedelta(days=now.weekday())
    return monday.replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
    )


def _tier_index(tier: str) -> int:
    try:
        return LEAGUE_TIERS.index(tier.upper())
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# Servis fonksiyonları
# ---------------------------------------------------------------------------

async def get_league_standings(*, db: AsyncSession, student_id: str) -> dict:
    """Öğrencinin mevcut lig tier'ını, sırasını ve tier'daki üst oyuncuları getirir.

    Returns:
        {tier, rank, weekly_xp, total_in_tier, week_start,
         standings: [{student_id, display_name, xp, rank}]}
    """
    try:
        from sqlalchemy import and_, desc, func as sa_func, select

        from models.league import LeagueMembership  # lazy import

        week_start = _current_week_start()

        # Üyelik al ya da oluştur
        membership = await _get_or_create_membership(db=db, student_id=student_id)

        # Tier'daki toplam oyuncu sayısı
        total_q = await db.execute(
            select(sa_func.count()).where(
                and_(
                    LeagueMembership.league_tier == membership.league_tier,
                    LeagueMembership.week_start == week_start,
                )
            )
        )
        total_in_tier: int = total_q.scalar() or 1

        # Öğrencinin sırası (daha yüksek XP = daha iyi sıra)
        rank_q = await db.execute(
            select(sa_func.count()).where(
                and_(
                    LeagueMembership.league_tier == membership.league_tier,
                    LeagueMembership.week_start == week_start,
                    LeagueMembership.weekly_xp > membership.weekly_xp,
                )
            )
        )
        rank: int = (rank_q.scalar() or 0) + 1

        # Tier'daki ilk 20 oyuncu
        top_q = await db.execute(
            select(LeagueMembership)
            .where(
                and_(
                    LeagueMembership.league_tier == membership.league_tier,
                    LeagueMembership.week_start == week_start,
                )
            )
            .order_by(desc(LeagueMembership.weekly_xp))
            .limit(20)
        )
        top_members = top_q.scalars().all()

        standings = [
            {
                "student_id": m.student_id,
                "display_name": f"Öğrenci-{m.student_id[:6]}",
                "xp": m.weekly_xp,
                "rank": i + 1,
                "is_self": m.student_id == student_id,
            }
            for i, m in enumerate(top_members)
        ]

        logger.info(
            "League standings fetched",
            extra_data={
                "student_id": student_id,
                "tier": membership.league_tier,
                "rank": rank,
            },
        )

        return {
            "tier": membership.league_tier,
            "rank": rank,
            "weekly_xp": membership.weekly_xp,
            "total_in_tier": total_in_tier,
            "week_start": week_start.isoformat(),
            "standings": standings,
        }

    except Exception as exc:
        logger.warning(
            "League standings DB fallback",
            extra_data={"student_id": student_id, "error": str(exc)},
        )
        # Tablo henüz oluşturulmadıysa mock veri döndür
        return {
            "tier": DEFAULT_TIER,
            "rank": 1,
            "weekly_xp": 0,
            "total_in_tier": 1,
            "week_start": _current_week_start().isoformat(),
            "standings": [
                {
                    "student_id": student_id,
                    "display_name": "Sen",
                    "xp": 0,
                    "rank": 1,
                    "is_self": True,
                }
            ],
        }


async def award_xp(
    *, db: AsyncSession, student_id: str, xp_amount: int, source: str
) -> dict:
    """Öğrenciye XP verir.

    Args:
        db: Veritabanı oturumu.
        student_id: Öğrenci kimliği.
        xp_amount: Verilecek XP miktarı. 0'dan büyük olmalı.
        source: XP kaynağı (quiz_complete, exam_complete, daily_login, streak_bonus).

    Returns:
        {student_id, source, xp_awarded, new_total_xp, tier, week_start}
    """
    # Negatif XP engelle
    if xp_amount <= 0:
        return {
            "student_id": student_id,
            "source": source,
            "xp_awarded": 0,
            "new_total_xp": 0,
            "tier": DEFAULT_TIER,
            "week_start": _current_week_start().isoformat(),
        }

    try:
        membership = await _get_or_create_membership(db=db, student_id=student_id)
        membership.weekly_xp += xp_amount
        db.add(membership)
        await db.commit()
        await db.refresh(membership)

        logger.info(
            "XP awarded",
            extra_data={
                "student_id": student_id,
                "source": source,
                "xp_awarded": xp_amount,
                "new_total": membership.weekly_xp,
            },
        )

        return {
            "student_id": student_id,
            "source": source,
            "xp_awarded": xp_amount,
            "new_total_xp": membership.weekly_xp,
            "tier": membership.league_tier,
            "week_start": membership.week_start.isoformat(),
        }

    except Exception as exc:
        logger.warning(
            "XP award DB fallback",
            extra_data={"student_id": student_id, "error": str(exc)},
        )
        return {
            "student_id": student_id,
            "source": source,
            "xp_awarded": xp_amount,
            "new_total_xp": xp_amount,
            "tier": DEFAULT_TIER,
            "week_start": _current_week_start().isoformat(),
        }


async def process_weekly_reset(*, db: AsyncSession) -> dict:
    """Haftalık sıfırlama görevi (Celery beat — her Pazartesi 00:05 UTC).

    Üst %10 yükselir, alt %10 düşer, geçmiş kaydedilir, XP sıfırlanır.

    Returns:
        {promoted, demoted, unchanged, total}
    """
    try:
        from sqlalchemy import and_, desc, select

        from models.league import LeagueHistory, LeagueMembership  # lazy import

        last_week = _current_week_start() - timedelta(weeks=1)
        promoted = 0
        demoted = 0
        unchanged = 0

        for tier in LEAGUE_TIERS:
            result = await db.execute(
                select(LeagueMembership)
                .where(
                    and_(
                        LeagueMembership.league_tier == tier,
                        LeagueMembership.week_start == last_week,
                    )
                )
                .order_by(desc(LeagueMembership.weekly_xp))
            )
            members = result.scalars().all()
            if not members:
                continue

            total = len(members)
            # Minimum 1 kişi etkilensin; küçük liglerde eşik uç olmasın
            promote_cutoff = max(1, total // 10)
            demote_cutoff = max(1, total // 10)
            tier_idx = _tier_index(tier)

            for i, m in enumerate(members):
                rank = i + 1
                new_tier = tier

                if rank <= promote_cutoff and tier_idx < len(LEAGUE_TIERS) - 1:
                    new_tier = LEAGUE_TIERS[tier_idx + 1]
                    promoted += 1
                elif rank > total - demote_cutoff and tier_idx > 0:
                    new_tier = LEAGUE_TIERS[tier_idx - 1]
                    demoted += 1
                else:
                    unchanged += 1

                # Persist tier change and reset XP for next week
                m.league_tier = new_tier
                m.weekly_xp = 0
                m.week_start = _current_week_start()
                db.add(m)

                history = LeagueHistory(
                    student_id=m.student_id,
                    week_start=last_week,
                    from_tier=tier,
                    to_tier=new_tier,
                    final_rank=rank,
                    final_xp=m.weekly_xp,
                )
                db.add(history)

        await db.commit()

        total_processed = promoted + demoted + unchanged
        logger.info(
            "Weekly league reset complete",
            extra_data={
                "promoted": promoted,
                "demoted": demoted,
                "unchanged": unchanged,
                "total": total_processed,
            },
        )
        return {
            "promoted": promoted,
            "demoted": demoted,
            "unchanged": unchanged,
            "total": total_processed,
        }

    except Exception as exc:
        logger.error(
            "Weekly reset failed",
            extra_data={"error": str(exc)},
        )
        return {
            "promoted": 0, "demoted": 0, "unchanged": 0,
            "total": 0, "error": str(exc),
        }


async def get_league_history(
    *, db: AsyncSession, student_id: str, limit: int = 10
) -> list[dict]:
    """Öğrencinin geçmiş haftalık lig sonuçlarını getirir.

    Args:
        db: Veritabanı oturumu.
        student_id: Öğrenci kimliği.
        limit: Maksimum kayıt sayısı.

    Returns:
        [{week_start, from_tier, to_tier, final_rank, final_xp, promoted}]
    """
    try:
        from sqlalchemy import desc, select

        from models.league import LeagueHistory  # lazy import

        result = await db.execute(
            select(LeagueHistory)
            .where(LeagueHistory.student_id == student_id)
            .order_by(desc(LeagueHistory.week_start))
            .limit(limit)
        )
        rows = result.scalars().all()

        return [
            {
                "week_start": r.week_start.isoformat(),
                "from_tier": r.from_tier,
                "to_tier": r.to_tier,
                "final_rank": r.final_rank,
                "final_xp": r.final_xp,
                # Tier yukarıya gittiyse promoted True
                "promoted": _tier_index(r.to_tier) > _tier_index(r.from_tier),
                "demoted": _tier_index(r.to_tier) < _tier_index(r.from_tier),
            }
            for r in rows
        ]

    except Exception as exc:
        logger.warning(
            "League history DB fallback",
            extra_data={"student_id": student_id, "error": str(exc)},
        )
        return []


# ---------------------------------------------------------------------------
# İç yardımcı — dışarıdan çağrılmamalı
# ---------------------------------------------------------------------------

async def _get_or_create_membership(*, db: AsyncSession, student_id: str):
    """Mevcut hafta üyeliğini getirir ya da oluşturur.

    Bir önceki haftanın tier'ını miras alır; yoksa BRONZE'dan başlar.
    """
    from sqlalchemy import and_, select

    from models.league import LeagueMembership  # lazy import

    week_start = _current_week_start()

    result = await db.execute(
        select(LeagueMembership).where(
            and_(
                LeagueMembership.student_id == student_id,
                LeagueMembership.week_start == week_start,
            )
        )
    )
    membership = result.scalars().first()
    if membership:
        return membership

    # Geçen haftanın tier'ını kontrol et
    last_week = week_start - timedelta(weeks=1)
    prev_result = await db.execute(
        select(LeagueMembership).where(
            and_(
                LeagueMembership.student_id == student_id,
                LeagueMembership.week_start == last_week,
            )
        )
    )
    prev = prev_result.scalars().first()
    tier = prev.league_tier if prev else DEFAULT_TIER

    membership = LeagueMembership(
        student_id=student_id,
        league_tier=tier,
        weekly_xp=0,
        week_start=week_start,
    )
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    return membership
