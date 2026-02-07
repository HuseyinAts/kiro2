"""
Experience Manager - Task 91.2
Seviye ve deneyim puanı yönetim sistemi

Özellikler:
- XP kazanma ve seviye atlama
- Üstel seviye büyümesi
- Milestone rozetleri
- Seviye atlama bildirimleri
"""
from datetime import datetime, timezone
from typing import Optional, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from redis import Redis

from models.database import User
from core.structured_logger import get_logger

logger = get_logger(__name__)


class ExperienceManager:
    """Deneyim ve seviye yönetim sistemi"""

    # Seviye hesaplama formülü: Level * 100 * 1.5^Level
    BASE_XP = 100
    GROWTH_FACTOR = 1.5

    # Milestone seviyeleri
    MILESTONES = [10, 25, 50, 75, 100]

    def __init__(self, db: Session, redis_client: Redis):
        self.db = db
        self.redis = redis_client
        self.cache_ttl = 3600

    def calculate_xp_for_level(self, level: int) -> int:
        """Belirli bir seviyeye ulaşmak için gereken toplam XP"""
        total_xp = 0
        for lvl in range(1, level + 1):
            total_xp += int(self.BASE_XP * (self.GROWTH_FACTOR ** (lvl - 1)))
        return total_xp

    def calculate_level_from_xp(self, total_xp: int) -> int:
        """Toplam XP'den seviye hesapla"""
        level = 1
        accumulated_xp = 0

        while accumulated_xp <= total_xp:
            next_level_xp = int(self.BASE_XP * (self.GROWTH_FACTOR**level))
            if accumulated_xp + next_level_xp > total_xp:
                break
            accumulated_xp += next_level_xp
            level += 1

        return level

    def add_xp(self, user_id: UUID, xp_amount: int, source: str = "unknown") -> Dict:
        """
        Kullanıcıya XP ekle ve seviye kontrolü yap

        Returns:
            {
                "old_level": int,
                "new_level": int,
                "level_up": bool,
                "total_xp": int,
                "milestone_reached": bool,
                "milestone_level": int or None
            }
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")

        old_xp = user.total_xp or 0
        old_level = user.level or 1

        # XP ekle
        new_xp = old_xp + xp_amount
        new_level = self.calculate_level_from_xp(new_xp)

        # Kullanıcıyı güncelle
        user.total_xp = new_xp
        user.level = new_level

        level_up = new_level > old_level
        milestone_reached = False
        milestone_level = None

        if level_up:
            user.last_level_up_at = datetime.now(timezone.utc)
            logger.info(f"User {user_id} leveled up: {old_level} -> {new_level}")

            # Milestone kontrolü
            if new_level in self.MILESTONES:
                milestone_reached = True
                milestone_level = new_level
                logger.info(f"User {user_id} reached milestone level {new_level}")

        self.db.commit()

        # Cache güncelle
        self._update_cache(user_id, new_xp, new_level)

        return {
            "old_level": old_level,
            "new_level": new_level,
            "level_up": level_up,
            "total_xp": new_xp,
            "xp_gained": xp_amount,
            "milestone_reached": milestone_reached,
            "milestone_level": milestone_level,
            "source": source,
        }

    def get_level_progress(self, user_id: UUID) -> Dict:
        """Mevcut seviye ilerlemesini getir"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")

        current_xp = user.total_xp or 0
        current_level = user.level or 1

        # Mevcut seviye için gereken XP
        current_level_xp = self.calculate_xp_for_level(current_level)
        # Sonraki seviye için gereken XP
        next_level_xp = self.calculate_xp_for_level(current_level + 1)

        # Bu seviyede kazanılan XP
        xp_in_current_level = current_xp - current_level_xp
        # Bu seviyede gereken toplam XP
        xp_needed_for_next = next_level_xp - current_level_xp

        progress_percentage = (
            (xp_in_current_level / xp_needed_for_next) * 100
            if xp_needed_for_next > 0
            else 0
        )

        return {
            "current_level": current_level,
            "total_xp": current_xp,
            "xp_in_current_level": xp_in_current_level,
            "xp_needed_for_next": xp_needed_for_next,
            "progress_percentage": round(progress_percentage, 2),
            "next_level": current_level + 1,
            "next_milestone": self._get_next_milestone(current_level),
        }

    def _get_next_milestone(self, current_level: int) -> Optional[int]:
        """Sonraki milestone seviyesini bul"""
        for milestone in self.MILESTONES:
            if milestone > current_level:
                return milestone
        return None

    def _update_cache(self, user_id: UUID, xp: int, level: int):
        """Redis cache güncelle"""
        cache_key = f"user:{user_id}:level"
        cache_data = {
            "xp": xp,
            "level": level,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            self.redis.setex(cache_key, self.cache_ttl, str(cache_data))
        except Exception as e:
            logger.error(f"Cache update failed: {e}")

    def get_leaderboard_by_level(self, limit: int = 100) -> list:
        """Seviyeye göre liderlik tablosu"""
        users = (
            self.db.query(User)
            .filter(User.level.isnot(None))
            .order_by(User.level.desc(), User.total_xp.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "rank": idx + 1,
                "user_id": str(user.id),
                "username": user.username,
                "level": user.level,
                "total_xp": user.total_xp,
                "last_level_up": user.last_level_up_at.isoformat()
                if user.last_level_up_at
                else None,
            }
            for idx, user in enumerate(users)
        ]


# Global instance
_experience_manager: Optional[ExperienceManager] = None


def get_experience_manager(db: Session, redis_client: Redis) -> ExperienceManager:
    """Get or create Experience Manager instance"""
    global _experience_manager
    if _experience_manager is None:
        _experience_manager = ExperienceManager(db, redis_client)
    return _experience_manager
