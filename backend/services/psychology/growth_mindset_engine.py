from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.streak_tracking import PerformanceHistory, StreakTracking

logger = structlog.get_logger(__name__)


class GrowthMindsetEngine:
    """
    Engine to generate non-toxic, data-driven motivation messages
    based on student performance and streak data.
    """

    @staticmethod
    async def generate_message(db: AsyncSession, user_id: str) -> dict:
        """
        Analyzes the user's last 7 days of performance and current streak,
        and returns a personalized Growth Mindset message.
        """
        try:
            # 1. Fetch Streak
            streak_stmt = select(StreakTracking).filter_by(user_id=user_id).limit(1)
            streak_result = await db.execute(streak_stmt)
            streak = streak_result.scalar_one_or_none()

            # 2. Fetch Performance History (Last 7 Days)
            now = datetime.now(UTC)
            seven_days_ago = now - timedelta(days=7)

            perf_stmt = (
                select(PerformanceHistory)
                .filter(
                    PerformanceHistory.user_id == user_id,
                    PerformanceHistory.recorded_at >= seven_days_ago,
                )
                .order_by(desc(PerformanceHistory.recorded_at))
            )

            perf_result = await db.execute(perf_stmt)
            performances = perf_result.scalars().all()

            current_streak = streak.current_streak if streak else 0

            # Analyze Performance Trend
            if len(performances) >= 2:
                # Compare first half vs second half or just latest vs previous avg
                recent = performances[0]
                past_avg = sum(p.score for p in performances[1:]) / len(
                    performances[1:]
                )

                if recent.score > past_avg + 10:
                    # Improvement
                    return {
                        "type": "improvement",
                        "title": "Gelişim Gözlemlendi 📈",
                        "message": f"Son testlerinde başarı oranın ortalamana göre {int(recent.score - past_avg)} puan arttı. Doğru stratejilerle ilerliyorsun, zeka esnektir ve sen onu esnetiyorsun.",
                    }
                if recent.score < past_avg - 10:
                    # Decline
                    return {
                        "type": "resilience",
                        "title": "Öğrenme Fırsatı 🧠",
                        "message": "Son testlerdeki hataların kalıcı öğrenmenin en doğal parçasıdır. Zorlanıyorsan beynin yeni sinir ağları kuruyor demektir. Hatalarını analiz etmeye odaklan.",
                    }

            # 3. Analyze Streak Habit
            if current_streak >= 3:
                return {
                    "type": "habit",
                    "title": "İstikrar Şampiyonu 🔥",
                    "message": f"Tam {current_streak} gündür aralıksız pratik yapıyorsun. Başarı büyük sıçramalarla değil, bu küçük adımların birikmesiyle gelir.",
                }

            # 4. Default / Neutral
            return {
                "type": "neutral",
                "title": "Odaklanma Zamanı 🎯",
                "message": "Dışarıdaki rekabeti unut, sadece dünkü kendinle yarışıyorsun. Her soru, zihnini geliştirmek için bir egzersizdir.",
            }

        except Exception as e:
            logger.error("growth_mindset_engine_error", error=str(e), user_id=user_id)
            return {
                "type": "neutral",
                "title": "Odaklanma Zamanı 🎯",
                "message": "Zeka geliştirilebilir bir kastır. Bugün beynini hangi konuyla esnetmek istersin?",
            }
