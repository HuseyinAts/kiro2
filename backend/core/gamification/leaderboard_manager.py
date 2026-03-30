"""
Leaderboard Manager - Task 91.4
Redis tabanlı liderlik tablosu yönetim sistemi

Özellikler:
- Global, haftalık, aylık liderlik tabloları
- Redis Sorted Sets ile hızlı sıralama
- Kullanıcı sıralaması ve yakın kullanıcılar
- Otomatik periyodik sıfırlama
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from redis import Redis
from sqlalchemy.orm import Session

from core.structured_logger import get_logger
from models.database import User

logger = get_logger(__name__)


class LeaderboardType:
    """Liderlik tablosu tipleri"""

    GLOBAL = "global"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    FRIENDS = "friends"
    CLASS = "class"


class LeaderboardManager:
    """Redis tabanlı liderlik tablosu yönetim sistemi"""

    def __init__(self, db: Session, redis_client: Redis):
        self.db = db
        self.redis = redis_client
        self.cache_ttl = 300  # 5 dakika

    def _get_redis_key(
        self, leaderboard_type: str, identifier: str | None = None
    ) -> str:
        """Redis key oluştur"""
        if leaderboard_type == LeaderboardType.GLOBAL:
            return "leaderboard:global"
        if leaderboard_type == LeaderboardType.WEEKLY:
            week_num = datetime.now(UTC).isocalendar()[1]
            year = datetime.now(UTC).year
            return f"leaderboard:weekly:{year}:w{week_num}"
        if leaderboard_type == LeaderboardType.MONTHLY:
            month = datetime.now(UTC).strftime("%Y-%m")
            return f"leaderboard:monthly:{month}"
        if leaderboard_type == LeaderboardType.FRIENDS:
            return f"leaderboard:friends:{identifier}"
        if leaderboard_type == LeaderboardType.CLASS:
            return f"leaderboard:class:{identifier}"
        return f"leaderboard:{leaderboard_type}"

    def update_score(
        self,
        user_id: str,
        score: int,
        leaderboard_type: str = LeaderboardType.GLOBAL,
        identifier: str | None = None,
    ) -> bool:
        """
        Kullanıcının skorunu güncelle

        Args:
            user_id: Kullanıcı ID'si
            score: Yeni skor
            leaderboard_type: Liderlik tablosu tipi
            identifier: Class veya friends için ID
        """
        try:
            redis_key = self._get_redis_key(leaderboard_type, identifier)

            # Redis sorted set'e ekle/güncelle
            self.redis.zadd(redis_key, {str(user_id): score})

            # Weekly ve monthly için TTL ayarla
            if leaderboard_type == LeaderboardType.WEEKLY:
                # Haftanın sonuna kadar
                now = datetime.now(UTC)
                days_until_sunday = (6 - now.weekday()) % 7
                ttl = (days_until_sunday + 1) * 86400  # Saniye cinsinden
                self.redis.expire(redis_key, ttl)
            elif leaderboard_type == LeaderboardType.MONTHLY:
                # Ayın sonuna kadar
                now = datetime.now(UTC)
                next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
                ttl = int((next_month - now).total_seconds())
                self.redis.expire(redis_key, ttl)

            logger.info(
                f"Leaderboard score updated: user={user_id}, type={leaderboard_type}, score={score}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to update leaderboard: {e}")
            return False

    def get_leaderboard(
        self,
        leaderboard_type: str = LeaderboardType.GLOBAL,
        limit: int = 100,
        offset: int = 0,
        identifier: str | None = None,
    ) -> list[dict]:
        """
        Liderlik tablosunu getir

        Returns:
            [
                {
                    "rank": 1,
                    "user_id": "...",
                    "username": "...",
                    "score": 1000,
                    "avatar_url": "..."
                }
            ]
        """
        try:
            redis_key = self._get_redis_key(leaderboard_type, identifier)

            # Redis'ten sıralı listeyi al (yüksekten düşüğe)
            user_scores = self.redis.zrevrange(
                redis_key, offset, offset + limit - 1, withscores=True
            )

            if not user_scores:
                return []

            # Kullanıcı bilgilerini veritabanından al
            user_ids = [
                UUID(user_id.decode() if isinstance(user_id, bytes) else user_id)
                for user_id, _ in user_scores
            ]

            users = self.db.query(User).filter(User.id.in_(user_ids)).all()

            # User ID'ye göre dict oluştur
            user_dict = {str(user.id): user for user in users}

            # Sonuçları birleştir
            leaderboard = []
            for idx, (user_id_bytes, score) in enumerate(user_scores):
                user_id = (
                    user_id_bytes.decode()
                    if isinstance(user_id_bytes, bytes)
                    else user_id_bytes
                )
                user = user_dict.get(user_id)

                if user:
                    leaderboard.append(
                        {
                            "rank": offset + idx + 1,
                            "user_id": user_id,
                            "username": user.username,
                            "score": int(score),
                            "level": user.level or 1,
                            "avatar_url": getattr(user, "avatar_url", None),
                        }
                    )

            return leaderboard

        except Exception as e:
            logger.error(f"Failed to get leaderboard: {e}")
            return []

    def get_user_rank(
        self,
        user_id: str,
        leaderboard_type: str = LeaderboardType.GLOBAL,
        identifier: str | None = None,
    ) -> dict | None:
        """
        Kullanıcının sırasını getir

        Returns:
            {
                "rank": 42,
                "score": 500,
                "total_users": 1000,
                "percentile": 95.8
            }
        """
        try:
            redis_key = self._get_redis_key(leaderboard_type, identifier)
            user_id_str = str(user_id)

            # Kullanıcının skorunu al
            score = self.redis.zscore(redis_key, user_id_str)
            if score is None:
                return None

            # Sırasını al (0-indexed, reverse order)
            rank = self.redis.zrevrank(redis_key, user_id_str)
            if rank is None:
                return None

            # Toplam kullanıcı sayısı
            total_users = self.redis.zcard(redis_key)

            # Yüzdelik dilim hesapla
            percentile = (
                ((total_users - rank) / total_users * 100) if total_users > 0 else 0
            )

            return {
                "rank": rank + 1,  # 1-indexed
                "score": int(score),
                "total_users": total_users,
                "percentile": round(percentile, 2),
            }

        except Exception as e:
            logger.error(f"Failed to get user rank: {e}")
            return None

    def get_nearby_users(
        self,
        user_id: str,
        leaderboard_type: str = LeaderboardType.GLOBAL,
        range_size: int = 5,
        identifier: str | None = None,
    ) -> dict:
        """
        Kullanıcının yakınındaki kullanıcıları getir

        Returns:
            {
                "user": {...},
                "above": [{...}, {...}],
                "below": [{...}, {...}]
            }
        """
        try:
            redis_key = self._get_redis_key(leaderboard_type, identifier)
            user_id_str = str(user_id)

            # Kullanıcının sırasını al
            rank = self.redis.zrevrank(redis_key, user_id_str)
            if rank is None:
                return {"user": None, "above": [], "below": []}

            # Yakındaki kullanıcıları al
            start = max(0, rank - range_size)
            end = rank + range_size

            nearby = self.get_leaderboard(
                leaderboard_type=leaderboard_type,
                limit=end - start + 1,
                offset=start,
                identifier=identifier,
            )

            # Kullanıcının indexini bul
            user_data = None
            above = []
            below = []

            for entry in nearby:
                if entry["user_id"] == user_id_str:
                    user_data = entry
                elif user_data is None:
                    above.append(entry)
                else:
                    below.append(entry)

            return {"user": user_data, "above": above, "below": below}

        except Exception as e:
            logger.error(f"Failed to get nearby users: {e}")
            return {"user": None, "above": [], "below": []}

    def get_user_position_change(
        self,
        user_id: str,
        leaderboard_type: str = LeaderboardType.GLOBAL,
        identifier: str | None = None,
    ) -> int | None:
        """
        Kullanıcının konum değişimini getir (önceki snapshot ile karşılaştır)

        Returns:
            int: Pozitif değer = yükseldi, negatif = düştü, 0 = değişmedi
        """
        try:
            redis_key = self._get_redis_key(leaderboard_type, identifier)
            snapshot_key = f"{redis_key}:snapshot"
            user_id_str = str(user_id)

            # Mevcut sıra
            current_rank = self.redis.zrevrank(redis_key, user_id_str)
            if current_rank is None:
                return None

            # Önceki sıra
            previous_rank_str = self.redis.hget(snapshot_key, user_id_str)
            if previous_rank_str is None:
                # İlk kez, snapshot oluştur
                self.redis.hset(snapshot_key, user_id_str, current_rank)
                self.redis.expire(snapshot_key, 86400)  # 24 saat
                return 0

            previous_rank = int(previous_rank_str)

            # Snapshot'ı güncelle
            self.redis.hset(snapshot_key, user_id_str, current_rank)

            # Değişim (ters: düşük rank = daha iyi)
            change = previous_rank - current_rank

            return change

        except Exception as e:
            logger.error(f"Failed to get position change: {e}")
            return None

    def reset_leaderboard(
        self, leaderboard_type: str, identifier: str | None = None
    ) -> bool:
        """Liderlik tablosunu sıfırla"""
        try:
            redis_key = self._get_redis_key(leaderboard_type, identifier)
            self.redis.delete(redis_key)

            # Snapshot'ı da sil
            snapshot_key = f"{redis_key}:snapshot"
            self.redis.delete(snapshot_key)

            logger.info(f"Leaderboard reset: {leaderboard_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to reset leaderboard: {e}")
            return False

    def sync_from_database(self, leaderboard_type: str = LeaderboardType.GLOBAL) -> int:
        """
        Veritabanından Redis'e senkronize et

        Returns:
            int: Senkronize edilen kullanıcı sayısı
        """
        try:
            if leaderboard_type == LeaderboardType.GLOBAL:
                # Toplam XP'ye göre sırala
                users = (
                    self.db.query(User)
                    .filter(User.total_xp.isnot(None))
                    .order_by(User.total_xp.desc())
                    .all()
                )

                redis_key = self._get_redis_key(LeaderboardType.GLOBAL)

                # Pipeline ile toplu güncelle
                pipe = self.redis.pipeline()
                for user in users:
                    pipe.zadd(redis_key, {str(user.id): user.total_xp or 0})
                pipe.execute()

                logger.info(f"Synced {len(users)} users to global leaderboard")
                return len(users)

            return 0

        except Exception as e:
            logger.error(f"Failed to sync leaderboard: {e}")
            return 0


# Global instance
_leaderboard_manager: LeaderboardManager | None = None


def get_leaderboard_manager(db: Session, redis_client: Redis) -> LeaderboardManager:
    """Get or create Leaderboard Manager instance"""
    global _leaderboard_manager
    if _leaderboard_manager is None:
        _leaderboard_manager = LeaderboardManager(db, redis_client)
    return _leaderboard_manager
