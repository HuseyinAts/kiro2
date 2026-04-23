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

from .badge_manager import BadgeManager
from .experience_manager import ExperienceManager
from .leaderboard_manager import LeaderboardManager
from .points_manager import PointsManager

__all__ = [
    "BadgeManager",
    "ExperienceManager",
    "LeaderboardManager",
    "PointsManager",
]
