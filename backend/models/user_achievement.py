"""
User Achievement Model - P2.2
Kullanıcı başarı takip modeli

Özellikler:
- Milestone başarıları
- İlerleme takibi
- Ödül sistemi
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base


class AchievementType:
    """Başarı tipleri"""

    MILESTONE = "milestone"  # Dönüm noktası
    STREAK = "streak"  # Süreklilik
    MASTERY = "mastery"  # Ustalık
    SOCIAL = "social"  # Sosyal
    SPECIAL = "special"  # Özel


class UserAchievement(Base):
    """Kullanıcı başarı takip modeli"""

    __tablename__ = "user_achievements"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Başarı bilgileri
    achievement_id = Column(
        String(100), nullable=False, index=True
    )  # Achievement definition ID
    achievement_type = Column(
        String(50), nullable=False
    )  # milestone, streak, mastery, etc.
    achievement_name = Column(String(200), nullable=False)
    achievement_description = Column(Text, nullable=True)

    # İlerleme bilgileri
    progress_current = Column(Integer, default=0, nullable=False)  # Mevcut ilerleme
    progress_target = Column(Integer, nullable=False)  # Hedef değer
    progress_percentage = Column(
        Integer, default=0, nullable=False
    )  # Yüzde olarak ilerleme

    # Durum
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Ödül bilgileri
    reward_xp = Column(Integer, default=0)  # Kazanılan XP
    reward_points = Column(Integer, default=0)  # Kazanılan puan
    reward_badge_id = Column(String(100), nullable=True)  # Verilen rozet ID

    # Extra data (renamed from metadata to avoid SQLAlchemy reserved word conflict)
    extra_data = Column(JSON, nullable=True)  # Ek bilgiler (JSON format)

    # Zaman damgaları
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    user = relationship("User", back_populates="achievements")

    def __repr__(self):
        return f"<UserAchievement(user_id={self.user_id}, achievement={self.achievement_id}, progress={self.progress_percentage}%)>"

    def to_dict(self):
        """Dictionary representation"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "achievement_id": self.achievement_id,
            "achievement_type": self.achievement_type,
            "achievement_name": self.achievement_name,
            "achievement_description": self.achievement_description,
            "progress": {
                "current": self.progress_current,
                "target": self.progress_target,
                "percentage": self.progress_percentage,
            },
            "is_completed": self.is_completed,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "reward": {
                "xp": self.reward_xp,
                "points": self.reward_points,
                "badge_id": self.reward_badge_id,
            },
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def update_progress(self, new_value: int) -> bool:
        """
        İlerlemeyi güncelle ve tamamlanma durumunu kontrol et

        Args:
            new_value: Yeni ilerleme değeri

        Returns:
            bool: Başarı tamamlandı mı?
        """
        self.progress_current = new_value  # type: ignore[assignment]
        target = int(self.progress_target or 0)
        percentage = int((new_value / target) * 100) if target > 0 else 0
        self.progress_percentage = min(percentage, 100)  # type: ignore

        current = int(self.progress_current or 0)
        if current >= target and not self.is_completed:
            self.is_completed = True  # type: ignore[assignment]
            self.completed_at = datetime.now(UTC)  # type: ignore[assignment]
            return True

        self.updated_at = datetime.now(UTC)  # type: ignore[assignment]
        return False

    def increment_progress(self, increment: int = 1) -> bool:
        """
        İlerlemeyi artır

        Args:
            increment: Artış miktarı

        Returns:
            bool: Başarı tamamlandı mı?
        """
        current = int(self.progress_current or 0)
        return self.update_progress(current + increment)

    class Config:
        from_attributes = True
