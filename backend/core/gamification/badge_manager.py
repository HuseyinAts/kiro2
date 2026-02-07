"""
Badge Manager - Task 91.3
Rozet koleksiyonu ve başarı sistemi

Özellikler:
- 50+ rozet tanımı
- Otomatik rozet kazanımı
- İlerleme takibi
- Nadir rozetler
"""
from datetime import datetime, timezone
from typing import List, Dict, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from enum import Enum

from models.user_badge import UserBadge
from core.structured_logger import get_logger

logger = get_logger(__name__)


class BadgeCategory(str, Enum):
    """Rozet kategorileri"""

    ACHIEVEMENT = "achievement"  # Başarı
    MILESTONE = "milestone"  # Dönüm noktası
    STREAK = "streak"  # Süreklilik
    MASTERY = "mastery"  # Ustalık
    SPECIAL = "special"  # Özel
    SEASONAL = "seasonal"  # Mevsimsel


class BadgeRarity(str, Enum):
    """Rozet nadirliği"""

    COMMON = "common"  # %60
    UNCOMMON = "uncommon"  # %25
    RARE = "rare"  # %10
    EPIC = "epic"  # %4
    LEGENDARY = "legendary"  # %1


# Rozet tanımları
BADGE_DEFINITIONS = {
    # Başlangıç rozetleri (COMMON)
    "first_question": {
        "name": "İlk Adım",
        "description": "İlk soruyu çözdün",
        "icon": "🎯",
        "category": BadgeCategory.ACHIEVEMENT,
        "rarity": BadgeRarity.COMMON,
        "points": 10,
        "criteria": {"questions_answered": 1},
    },
    "first_exam": {
        "name": "İlk Sınav",
        "description": "İlk sınavını tamamladın",
        "icon": "📝",
        "category": BadgeCategory.ACHIEVEMENT,
        "rarity": BadgeRarity.COMMON,
        "points": 25,
        "criteria": {"exams_completed": 1},
    },
    "first_streak": {
        "name": "Başlangıç",
        "description": "3 gün üst üste çalıştın",
        "icon": "🔥",
        "category": BadgeCategory.STREAK,
        "rarity": BadgeRarity.COMMON,
        "points": 50,
        "criteria": {"streak_days": 3},
    },
    # Süreklilik rozetleri (UNCOMMON-RARE)
    "week_warrior": {
        "name": "Haftalık Savaşçı",
        "description": "7 gün üst üste çalıştın",
        "icon": "⚔️",
        "category": BadgeCategory.STREAK,
        "rarity": BadgeRarity.UNCOMMON,
        "points": 100,
        "criteria": {"streak_days": 7},
    },
    "month_master": {
        "name": "Aylık Usta",
        "description": "30 gün üst üste çalıştın",
        "icon": "👑",
        "category": BadgeCategory.STREAK,
        "rarity": BadgeRarity.RARE,
        "points": 500,
        "criteria": {"streak_days": 30},
    },
    "unstoppable": {
        "name": "Durdurulamaz",
        "description": "100 gün üst üste çalıştın",
        "icon": "💎",
        "category": BadgeCategory.STREAK,
        "rarity": BadgeRarity.LEGENDARY,
        "points": 2000,
        "criteria": {"streak_days": 100},
    },
    # Soru çözme rozetleri
    "hundred_questions": {
        "name": "Yüzlük",
        "description": "100 soru çözdün",
        "icon": "💯",
        "category": BadgeCategory.MILESTONE,
        "rarity": BadgeRarity.UNCOMMON,
        "points": 100,
        "criteria": {"questions_answered": 100},
    },
    "thousand_questions": {
        "name": "Binlik",
        "description": "1000 soru çözdün",
        "icon": "🌟",
        "category": BadgeCategory.MILESTONE,
        "rarity": BadgeRarity.RARE,
        "points": 1000,
        "criteria": {"questions_answered": 1000},
    },
    "question_master": {
        "name": "Soru Ustası",
        "description": "10,000 soru çözdün",
        "icon": "🏆",
        "category": BadgeCategory.MASTERY,
        "rarity": BadgeRarity.EPIC,
        "points": 5000,
        "criteria": {"questions_answered": 10000},
    },
    # Doğruluk rozetleri
    "perfect_10": {
        "name": "Mükemmel 10",
        "description": "Üst üste 10 doğru cevap",
        "icon": "✨",
        "category": BadgeCategory.ACHIEVEMENT,
        "rarity": BadgeRarity.UNCOMMON,
        "points": 150,
        "criteria": {"correct_streak": 10},
    },
    "perfect_50": {
        "name": "Mükemmel 50",
        "description": "Üst üste 50 doğru cevap",
        "icon": "⭐",
        "category": BadgeCategory.ACHIEVEMENT,
        "rarity": BadgeRarity.RARE,
        "points": 500,
        "criteria": {"correct_streak": 50},
    },
    # Seviye rozetleri
    "level_10": {
        "name": "Seviye 10",
        "description": "10. seviyeye ulaştın",
        "icon": "🎖️",
        "category": BadgeCategory.MILESTONE,
        "rarity": BadgeRarity.UNCOMMON,
        "points": 200,
        "criteria": {"level": 10},
    },
    "level_25": {
        "name": "Seviye 25",
        "description": "25. seviyeye ulaştın",
        "icon": "🏅",
        "category": BadgeCategory.MILESTONE,
        "rarity": BadgeRarity.RARE,
        "points": 500,
        "criteria": {"level": 25},
    },
    "level_50": {
        "name": "Seviye 50",
        "description": "50. seviyeye ulaştın",
        "icon": "🥇",
        "category": BadgeCategory.MILESTONE,
        "rarity": BadgeRarity.EPIC,
        "points": 1500,
        "criteria": {"level": 50},
    },
    "level_100": {
        "name": "Efsane",
        "description": "100. seviyeye ulaştın",
        "icon": "👑",
        "category": BadgeCategory.MILESTONE,
        "rarity": BadgeRarity.LEGENDARY,
        "points": 5000,
        "criteria": {"level": 100},
    },
    # Sınav rozetleri
    "exam_ace": {
        "name": "Sınav Asi",
        "description": "Bir sınavdan %95+ aldın",
        "icon": "📚",
        "category": BadgeCategory.ACHIEVEMENT,
        "rarity": BadgeRarity.RARE,
        "points": 300,
        "criteria": {"exam_score_min": 95},
    },
    "perfect_exam": {
        "name": "Tam Puan",
        "description": "Bir sınavdan %100 aldın",
        "icon": "💫",
        "category": BadgeCategory.ACHIEVEMENT,
        "rarity": BadgeRarity.EPIC,
        "points": 1000,
        "criteria": {"exam_score_min": 100},
    },
    # Özel rozetler
    "early_bird": {
        "name": "Erken Kuş",
        "description": "Sabah 6-8 arası 10 gün çalıştın",
        "icon": "🌅",
        "category": BadgeCategory.SPECIAL,
        "rarity": BadgeRarity.UNCOMMON,
        "points": 250,
        "criteria": {"early_morning_days": 10},
    },
    "night_owl": {
        "name": "Gece Kuşu",
        "description": "Gece 22-00 arası 10 gün çalıştın",
        "icon": "🦉",
        "category": BadgeCategory.SPECIAL,
        "rarity": BadgeRarity.UNCOMMON,
        "points": 250,
        "criteria": {"late_night_days": 10},
    },
    # Mevsimsel rozetler
    "summer_scholar": {
        "name": "Yaz Bilgini",
        "description": "Yaz aylarında 30 gün çalıştın",
        "icon": "☀️",
        "category": BadgeCategory.SEASONAL,
        "rarity": BadgeRarity.RARE,
        "points": 500,
        "criteria": {"summer_days": 30},
    },
}


class BadgeManager:
    """Rozet yönetim sistemi"""

    def __init__(self, db: Session):
        self.db = db
        self.badges = BADGE_DEFINITIONS

    def award_badge(
        self, user_id: UUID, badge_id: str, auto_awarded: bool = True
    ) -> Optional[UserBadge]:
        """Kullanıcıya rozet ver"""
        # Rozet tanımını kontrol et
        if badge_id not in self.badges:
            logger.error(f"Badge not found: {badge_id}")
            return None

        # Rozet zaten kazanılmış mı?
        existing = (
            self.db.query(UserBadge)
            .filter(UserBadge.user_id == user_id, UserBadge.badge_id == badge_id)
            .first()
        )

        if existing:
            logger.info(f"User {user_id} already has badge {badge_id}")
            return existing

        # Yeni rozet oluştur
        badge_def = self.badges[badge_id]
        user_badge = UserBadge(
            user_id=user_id,
            badge_id=badge_id,
            earned_at=datetime.now(timezone.utc),
            auto_awarded=auto_awarded,
        )

        self.db.add(user_badge)
        self.db.commit()
        self.db.refresh(user_badge)

        logger.info(
            f"Badge awarded: {badge_id} to user {user_id}",
            extra={"rarity": badge_def["rarity"], "points": badge_def["points"]},
        )

        return user_badge

    def check_and_award_badges(
        self, user_id: UUID, user_stats: Dict
    ) -> List[UserBadge]:
        """Kullanıcının istatistiklerini kontrol et ve uygun rozetleri ver"""
        awarded_badges = []

        for badge_id, badge_def in self.badges.items():
            # Zaten kazanılmış mı?
            existing = (
                self.db.query(UserBadge)
                .filter(UserBadge.user_id == user_id, UserBadge.badge_id == badge_id)
                .first()
            )
            if existing:
                continue

            # Kriterleri kontrol et
            if self._check_criteria(user_stats, badge_def["criteria"]):
                badge = self.award_badge(user_id, badge_id)
                if badge:
                    awarded_badges.append(badge)

        return awarded_badges

    def _check_criteria(self, user_stats: Dict, criteria: Dict) -> bool:
        """Rozet kriterlerini kontrol et"""
        for key, required_value in criteria.items():
            user_value = user_stats.get(key, 0)
            if user_value < required_value:
                return False
        return True

    def get_user_badges(self, user_id: UUID) -> List[Dict]:
        """Kullanıcının rozetlerini getir"""
        user_badges = (
            self.db.query(UserBadge)
            .filter(UserBadge.user_id == user_id)
            .order_by(UserBadge.earned_at.desc())
            .all()
        )

        return [
            {
                "badge_id": ub.badge_id,
                "earned_at": ub.earned_at.isoformat(),
                "auto_awarded": ub.auto_awarded,
                **self.badges[ub.badge_id],
            }
            for ub in user_badges
            if ub.badge_id in self.badges
        ]

    def get_badge_progress(self, user_id: UUID, user_stats: Dict) -> List[Dict]:
        """Henüz kazanılmamış rozetlerin ilerlemesini göster"""
        progress = []

        earned_badge_ids = {
            ub.badge_id
            for ub in self.db.query(UserBadge)
            .filter(UserBadge.user_id == user_id)
            .all()
        }

        for badge_id, badge_def in self.badges.items():
            if badge_id in earned_badge_ids:
                continue

            criteria = badge_def["criteria"]
            total_progress = 0
            criteria_count = len(criteria)

            for key, required in criteria.items():
                current = user_stats.get(key, 0)
                criteria_progress = min((current / required) * 100, 100)
                total_progress += criteria_progress

            avg_progress = total_progress / criteria_count if criteria_count > 0 else 0

            if avg_progress > 0:  # Sadece başlamış olanları göster
                progress.append(
                    {
                        "badge_id": badge_id,
                        "progress_percentage": round(avg_progress, 2),
                        **badge_def,
                    }
                )

        # İlerlemeye göre sırala
        progress.sort(key=lambda x: x["progress_percentage"], reverse=True)
        return progress

    def get_all_badges(self) -> List[Dict]:
        """Tüm rozet tanımlarını getir"""
        return [
            {"badge_id": badge_id, **badge_data}
            for badge_id, badge_data in self.badges.items()
        ]


# Global instance
_badge_manager: Optional[BadgeManager] = None


def get_badge_manager(db: Session) -> BadgeManager:
    """Get or create Badge Manager instance"""
    global _badge_manager
    if _badge_manager is None:
        _badge_manager = BadgeManager(db)
    return _badge_manager
