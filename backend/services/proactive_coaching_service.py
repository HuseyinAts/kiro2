"""
Proactive Coaching Service — F6 Proaktif AI Koçluk

Öğrencinin hata örüntülerini, FSRS birikimini ve oturum sıklığını analiz ederek
1-3 adet eyleme yönelik koçluk önerisi üretir.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from core.structured_logger import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger("proactive_coaching_service")

# Burnout eşikleri
BURNOUT_MIN_SESSIONS = 3  # Bu kadar veriden önce karar verme
BURNOUT_MIN_DURATION_SEC = 600  # 10 dakikanın altı → düşük bağlılık sinyali
BURNOUT_IDLE_DAYS = 3  # Son 3 günde oturum yoksa uyarı ver

# Hata yüzdesi eşiği
WEAKNESS_ERROR_THRESHOLD = 0.40  # %40 üzeri hata → zayıf konu uyarısı

# Öneri türleri
SUGGESTION_TYPES = {
    "weakness_alert": "Zayıf Konu Uyarısı",
    "burnout_warning": "Dinlenme Önerisi",
    "streak_encouragement": "Seri Teşviki",
    "topic_recommendation": "Konu Tavsiyesi",
}


async def generate_suggestions(*, db: AsyncSession, student_id: str) -> list[dict]:
    """Öğrencinin örüntülerini analiz ederek koçluk önerileri üretir.

    Zayıf konular, burnout sinyalleri, FSRS birikimi ve seri durumu
    değerlendirilerek 1-3 öneri döndürülür.

    Returns:
        Her öğe: {id, type, title, message, priority, action_url}
    """
    suggestions: list[dict] = []

    try:
        # 1. Burnout sinyali kontrolü
        burnout = await detect_burnout_signals(db=db, student_id=student_id)
        if burnout.get("is_at_risk"):
            signals = burnout.get("signals", [])
            signal_desc = signals[0] if signals else "düşük çalışma süresi"
            suggestions.append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "burnout_warning",
                    "title": SUGGESTION_TYPES["burnout_warning"],
                    "message": (
                        f"Son günlerde çalışma süren azalıyor ({signal_desc}). "
                        "Kısa bir mola vermen performansını artırabilir."
                    ),
                    "priority": 1,
                    "action_url": "/dashboard/wellness",
                }
            )

        # 2. Zayıf konu analizi (son 7 günün StudentAnswer kayıtları)
        weakness = await _analyze_weakness_patterns(db=db, student_id=student_id)
        if weakness:
            suggestions.append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "weakness_alert",
                    "title": SUGGESTION_TYPES["weakness_alert"],
                    "message": (
                        f"{weakness['topic']} konusunda son 7 günde "
                        f"%{weakness['error_rate']:.0f} hata oranı tespit edildi. "
                        "Bu konuya odaklanmanı öneririz."
                    ),
                    "priority": 2,
                    "action_url": f"/learning-path?topic={weakness['topic_id']}",
                }
            )

        # 3. FSRS birikmiş kart kontrolü
        fsrs_due = await _count_fsrs_due(db=db, student_id=student_id)
        if fsrs_due > 5:
            suggestions.append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "topic_recommendation",
                    "title": SUGGESTION_TYPES["topic_recommendation"],
                    "message": (
                        f"Tekrar edilmeyi bekleyen {fsrs_due} kart var. "
                        "Uzun süreli hafıza için bugün tekrar yapmayı unutma!"
                    ),
                    "priority": 3,
                    "action_url": "/review-queue",
                }
            )

    except Exception as exc:
        logger.warning(
            "Coaching suggestion generation fallback",
            extra_data={"student_id": student_id, "error": str(exc)},
        )
        # DB tablosu henüz yoksa varsayılan teşvik önerisi döndür
        suggestions = [
            {
                "id": str(uuid.uuid4()),
                "type": "streak_encouragement",
                "title": SUGGESTION_TYPES["streak_encouragement"],
                "message": (
                    "Çalışmaya devam et! Her gün biraz çalışmak büyük fark yaratır."
                ),
                "priority": 3,
                "action_url": "/dashboard",
            }
        ]

    # Önceliklere göre sırala, en fazla 3 öneri döndür
    suggestions.sort(key=lambda s: s.get("priority", 99))
    return suggestions[:3]


async def detect_burnout_signals(*, db: AsyncSession, student_id: str) -> dict:
    """Burnout göstergelerini kontrol eder.

    Azalan oturum sıklığı, kısa oturumlar ve ardı ardına yanlış cevaplar
    incelenir.

    Returns:
        {is_at_risk: bool, signals: [str], recommendation: str}
    """
    signals: list[str] = []

    try:
        from sqlalchemy import and_, select
        from sqlalchemy import func as sa_func

        from models.coaching import StudentEngagementSignal  # lazy import

        week_ago = datetime.now(UTC) - timedelta(days=7)

        # Son 7 günün oturum süresi ortalaması
        result = await db.execute(
            select(
                sa_func.avg(StudentEngagementSignal.value).label("avg_duration"),
                sa_func.count().label("session_count"),
            ).where(
                and_(
                    StudentEngagementSignal.student_id == student_id,
                    StudentEngagementSignal.signal_type == "session_duration",
                    StudentEngagementSignal.recorded_at >= week_ago,
                )
            )
        )
        row = result.one_or_none()

        if row and row.session_count and row.session_count >= BURNOUT_MIN_SESSIONS:
            avg_sec = float(row.avg_duration or 0)
            if avg_sec < BURNOUT_MIN_DURATION_SEC:
                avg_min = round(avg_sec / 60, 1)
                signals.append(f"ortalama oturum süresi {avg_min} dk (hedef: 10+ dk)")

        # Son 3 günde oturum var mı?
        three_days_ago = datetime.now(UTC) - timedelta(days=BURNOUT_IDLE_DAYS)
        recent_result = await db.execute(
            select(sa_func.count()).where(
                and_(
                    StudentEngagementSignal.student_id == student_id,
                    StudentEngagementSignal.signal_type == "session_duration",
                    StudentEngagementSignal.recorded_at >= three_days_ago,
                )
            )
        )
        recent_count = recent_result.scalar() or 0
        if recent_count == 0:
            signals.append(f"son {BURNOUT_IDLE_DAYS} günde hiç oturum yok")

    except Exception as exc:
        logger.debug(
            "Burnout signal DB unavailable",
            extra_data={"student_id": student_id, "error": str(exc)},
        )

    is_at_risk = len(signals) > 0
    recommendation = (
        "Günlük 15-20 dakikalık düzenli çalışma seansları planla."
        if is_at_risk
        else "Çalışma rutinin iyi görünüyor, böyle devam et!"
    )

    return {
        "is_at_risk": is_at_risk,
        "signals": signals,
        "recommendation": recommendation,
    }


async def record_engagement_signal(
    *, db: AsyncSession, student_id: str, signal_type: str, value: float
) -> dict:
    """Davranışsal bağlılık sinyali kaydeder.

    Args:
        db: Veritabanı oturumu.
        student_id: Öğrenci kimliği.
        signal_type: Sinyal türü
            (session_duration, post_error_pause, answer_speed_trend).
        value: Sayısal değer (süre için saniye, trend için normalize skor).

    Returns:
        {id, student_id, signal_type, value, recorded_at}
    """
    try:
        from models.coaching import StudentEngagementSignal  # lazy import

        signal = StudentEngagementSignal(
            student_id=student_id,
            signal_type=signal_type,
            value=value,
        )
        db.add(signal)
        await db.commit()
        await db.refresh(signal)

        return {
            "id": signal.id,
            "student_id": student_id,
            "signal_type": signal_type,
            "value": value,
            "recorded_at": signal.recorded_at.isoformat(),
        }

    except Exception as exc:
        logger.warning(
            "Engagement signal record fallback",
            extra_data={
                "student_id": student_id,
                "signal_type": signal_type,
                "error": str(exc),
            },
        )
        return {
            "id": None,
            "student_id": student_id,
            "signal_type": signal_type,
            "value": value,
            "recorded_at": datetime.now(UTC).isoformat(),
        }


async def record_suggestion_interaction(
    *, db: AsyncSession, suggestion_id: str, student_id: str, action: str
) -> dict:
    """Öğrencinin bir öneriyle etkileşimini kaydeder.

    Args:
        db: Veritabanı oturumu.
        suggestion_id: Öneri kimliği (UUID string).
        student_id: Öğrenci kimliği.
        action: 'clicked' veya 'dismissed'.

    Returns:
        {suggestion_id, student_id, action, recorded_at, success}
    """
    if action not in ("clicked", "dismissed"):
        return {
            "suggestion_id": suggestion_id,
            "student_id": student_id,
            "action": action,
            "success": False,
            "error": "Geçersiz eylem. 'clicked' veya 'dismissed' kullanın.",
        }

    try:
        from sqlalchemy import select

        from models.coaching import CoachingEvent  # lazy import

        result = await db.execute(
            select(CoachingEvent).where(CoachingEvent.id == suggestion_id)
        )
        event = result.scalar_one_or_none()

        now = datetime.now(UTC)
        if event:
            if action == "clicked":
                event.clicked_at = now
            else:
                event.dismissed_at = now
            await db.commit()

        logger.info(
            "Suggestion interaction recorded",
            extra_data={
                "suggestion_id": suggestion_id,
                "student_id": student_id,
                "action": action,
            },
        )

        return {
            "suggestion_id": suggestion_id,
            "student_id": student_id,
            "action": action,
            "recorded_at": now.isoformat(),
            "success": True,
        }

    except Exception as exc:
        logger.warning(
            "Suggestion interaction DB fallback",
            extra_data={
                "suggestion_id": suggestion_id,
                "student_id": student_id,
                "error": str(exc),
            },
        )
        return {
            "suggestion_id": suggestion_id,
            "student_id": student_id,
            "action": action,
            "recorded_at": datetime.now(UTC).isoformat(),
            "success": False,
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# İç yardımcılar
# ---------------------------------------------------------------------------


async def _analyze_weakness_patterns(
    *, db: AsyncSession, student_id: str
) -> dict | None:
    """Son 7 günün StudentAnswer kayıtlarından en zayıf konuyu bulur."""
    try:
        from sqlalchemy import and_, case, select
        from sqlalchemy import func as sa_func

        from models.exam_db import StudentAnswer  # lazy import

        week_ago = datetime.now(UTC) - timedelta(days=7)

        result = await db.execute(
            select(
                StudentAnswer.topic_id,
                sa_func.count().label("total"),
                sa_func.sum(case((~StudentAnswer.is_correct, 1), else_=0)).label(
                    "errors"
                ),
            )
            .where(
                and_(
                    StudentAnswer.student_id == student_id,
                    StudentAnswer.answered_at >= week_ago,
                    StudentAnswer.topic_id.isnot(None),
                )
            )
            .group_by(StudentAnswer.topic_id)
            .having(sa_func.count() >= 5)  # En az 5 soru çözülmüş konular
            .order_by(
                (
                    sa_func.sum(case((~StudentAnswer.is_correct, 1), else_=0))
                    / sa_func.count()
                ).desc()
            )
            .limit(1)
        )
        row = result.first()

        if not row or not row.errors:
            return None

        error_rate = (row.errors / row.total) * 100
        if error_rate < WEAKNESS_ERROR_THRESHOLD * 100:
            return None

        return {
            "topic_id": str(row.topic_id),
            "topic": f"Konu-{str(row.topic_id)[:6]}",
            "total_questions": row.total,
            "error_count": row.errors,
            "error_rate": error_rate,
        }

    except Exception:
        return None


async def _count_fsrs_due(*, db: AsyncSession, student_id: str) -> int:
    """Bugün tekrar edilmesi gereken FSRS kartlarını sayar."""
    try:
        from sqlalchemy import and_, select

        from models.fsrs import FSRSCard  # lazy import

        now = datetime.now(UTC)

        result = await db.execute(
            select(FSRSCard)
            .where(
                and_(
                    FSRSCard.student_id == student_id,
                    FSRSCard.next_review_at <= now,
                    FSRSCard.is_active == True,  # noqa: E712
                )
            )
            .limit(50)  # 50 üzerini saymaya gerek yok
        )
        return len(result.scalars().all())

    except Exception:
        return 0
