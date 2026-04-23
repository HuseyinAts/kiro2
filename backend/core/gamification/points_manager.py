"""
Points Manager - Puan Yönetim Sistemi

Bu modül, öğrencilerin puan kazanma, takip etme ve geçmişini görüntüleme
işlemlerini yönetir.

Puan Kazanma Mekanizmaları:
- Doğru cevap: Zorluk bazlı (Kolay: 10, Orta: 25, Zor: 50 puan)
- Günlük hedef tamamlama: 100 bonus puan
- Sınav tamamlama: 50-500 puan (performansa göre)
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from redis import Redis
from sqlalchemy.orm import Session

from models.database import User
from models.point_transaction import PointTransaction


class PointsManager:
    """Puan yönetim sistemi"""

    def __init__(self, db: Session, redis_client: Redis):
        """
        PointsManager başlatıcı

        Args:
            db: SQLAlchemy database session
            redis_client: Redis client instance
        """
        self.db = db
        self.redis = redis_client
        self.cache_ttl = 3600  # 1 saat

    def award_points(
        self, user_id: UUID, points: int, reason: str, metadata: dict | None = None
    ) -> PointTransaction:
        """
        Kullanıcıya puan ver ve transaction kaydet

        Args:
            user_id: Kullanıcı ID
            points: Verilecek puan miktarı
            reason: Puan verme nedeni
            metadata: Ek bilgiler (opsiyonel)

        Returns:
            PointTransaction: Puan işlem kaydı
        """
        # Redis'te toplam puanı güncelle (cache)
        cache_key = f"user:{user_id}:points"
        current_points = self.redis.get(cache_key)

        if current_points is None:
            # Cache'de yoksa veritabanından al
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            current_points = user.total_points or 0
        else:
            current_points = int(current_points)

        new_points = current_points + points
        self.redis.setex(cache_key, self.cache_ttl, new_points)

        # Veritabanına transaction kaydet
        transaction = PointTransaction(
            user_id=user_id,
            points=points,
            reason=reason,
            metadata=metadata,
            timestamp=datetime.now(UTC),
        )
        self.db.add(transaction)

        # User tablosundaki toplam puanı güncelle
        user = self.db.query(User).filter(User.id == user_id).first()
        user.total_points = new_points

        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    def calculate_question_points(self, difficulty: str, is_correct: bool) -> int:
        """
        Soru zorluğuna göre puan hesapla

        Args:
            difficulty: Soru zorluğu (easy, medium, hard)
            is_correct: Cevap doğru mu?

        Returns:
            int: Kazanılan puan miktarı

        Puan Tablosu:
        - Kolay: 10 puan
        - Orta: 25 puan
        - Zor: 50 puan
        """
        if not is_correct:
            return 0

        points_map = {
            "easy": 10,
            "kolay": 10,
            "medium": 25,
            "orta": 25,
            "hard": 50,
            "zor": 50,
        }
        return points_map.get(difficulty.lower(), 10)

    def calculate_exam_points(
        self, score_percentage: float, total_questions: int
    ) -> int:
        """
        Sınav performansına göre puan hesapla

        Args:
            score_percentage: Başarı yüzdesi (0-100)
            total_questions: Toplam soru sayısı

        Returns:
            int: Kazanılan puan miktarı (50-500 arası)
        """
        # Temel puan: 50-500 arası
        base_points = int(50 + (score_percentage / 100) * 450)

        # Soru sayısı bonusu (daha uzun sınavlar daha fazla puan)
        question_bonus = min(total_questions // 10, 50)

        return base_points + question_bonus

    def award_daily_goal_bonus(self, user_id: UUID) -> PointTransaction | None:
        """
        Günlük hedef tamamlama bonusu ver

        Args:
            user_id: Kullanıcı ID

        Returns:
            PointTransaction veya None (zaten verilmişse)
        """
        # Bugün zaten verilmiş mi kontrol et
        today_start = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        existing_bonus = (
            self.db.query(PointTransaction)
            .filter(
                PointTransaction.user_id == user_id,
                PointTransaction.reason == "daily_goal_completed",
                PointTransaction.timestamp >= today_start,
            )
            .first()
        )

        if existing_bonus:
            return None

        # Bonus ver
        return self.award_points(
            user_id=user_id,
            points=100,
            reason="daily_goal_completed",
            metadata={"date": today_start.isoformat()},
        )

    def get_total_points(self, user_id: UUID) -> int:
        """
        Kullanıcının toplam puanını getir (cache'den veya DB'den)

        Args:
            user_id: Kullanıcı ID

        Returns:
            int: Toplam puan
        """
        cache_key = f"user:{user_id}:points"
        cached_points = self.redis.get(cache_key)

        if cached_points is not None:
            return int(cached_points)

        # Cache'de yoksa veritabanından al
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return 0

        total_points = user.total_points or 0

        # Cache'e kaydet
        self.redis.setex(cache_key, self.cache_ttl, total_points)

        return total_points

    def get_daily_points(self, user_id: UUID) -> int:
        """
        Bugün kazanılan toplam puanı getir

        Args:
            user_id: Kullanıcı ID

        Returns:
            int: Bugün kazanılan puan
        """
        today_start = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        transactions = (
            self.db.query(PointTransaction)
            .filter(
                PointTransaction.user_id == user_id,
                PointTransaction.timestamp >= today_start,
            )
            .all()
        )

        return sum(t.points for t in transactions)

    def get_weekly_points(self, user_id: UUID) -> int:
        """
        Bu hafta kazanılan toplam puanı getir

        Args:
            user_id: Kullanıcı ID

        Returns:
            int: Bu hafta kazanılan puan
        """
        week_start = datetime.now(UTC) - timedelta(days=7)
        transactions = (
            self.db.query(PointTransaction)
            .filter(
                PointTransaction.user_id == user_id,
                PointTransaction.timestamp >= week_start,
            )
            .all()
        )

        return sum(t.points for t in transactions)

    def get_point_history(
        self, user_id: UUID, days: int = 30, limit: int | None = None
    ) -> list[PointTransaction]:
        """
        Son N günlük puan geçmişini getir

        Args:
            user_id: Kullanıcı ID
            days: Kaç günlük geçmiş (default: 30)
            limit: Maksimum kayıt sayısı (opsiyonel)

        Returns:
            List[PointTransaction]: Puan işlem kayıtları
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        query = (
            self.db.query(PointTransaction)
            .filter(
                PointTransaction.user_id == user_id,
                PointTransaction.timestamp >= cutoff_date,
            )
            .order_by(PointTransaction.timestamp.desc())
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_point_summary(self, user_id: UUID) -> dict:
        """
        Kullanıcının puan özetini getir

        Args:
            user_id: Kullanıcı ID

        Returns:
            dict: Puan özet bilgileri
        """
        return {
            "total_points": self.get_total_points(user_id),
            "daily_points": self.get_daily_points(user_id),
            "weekly_points": self.get_weekly_points(user_id),
            "last_updated": datetime.now(UTC).isoformat(),
        }

    def invalidate_cache(self, user_id: UUID):
        """
        Kullanıcının puan cache'ini temizle

        Args:
            user_id: Kullanıcı ID
        """
        cache_key = f"user:{user_id}:points"
        self.redis.delete(cache_key)
