"""
Gamification Module - Oyunlaştırma ve Motivasyon Sistemi

Bu modül, öğrencilerin öğrenme sürecini oyunlaştırarak motivasyonu artırmak,
düzenli çalışmayı teşvik etmek ve başarıları görünür kılmak için tasarlanmıştır.

Bileşenler:
- PointsManager: Puan kazanma ve takip sistemi
- ExperienceManager: Seviye ve deneyim puanı yönetimi
- BadgeManager: Rozet koleksiyonu ve başarı sistemi
- LeaderboardManager: Liderlik tablosu ve sıralama
- GamificationNotificationService: Motivasyon bildirimleri
"""

from .points_manager import PointsManager
from .experience_manager import ExperienceManager
from .badge_manager import BadgeManager
from .leaderboard_manager import LeaderboardManager

__all__ = [
    "PointsManager",
    "ExperienceManager",
    "BadgeManager",
    "LeaderboardManager",
]
