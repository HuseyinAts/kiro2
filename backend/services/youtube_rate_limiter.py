"""
YouTube API Rate Limiter ve Quota Tracker (Task 12)
YouTube API quota'sını izler ve rate limiting uygular

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.7, 7.8, 7.9

Author: AI Assistant
Date: 2025-10-30
"""
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from core.cache import cache_manager
from core.structured_logger import get_logger

logger = get_logger("youtube_rate_limiter")


@dataclass
class YouTubeQuotaInfo:
    """YouTube API quota bilgisi"""

    daily_limit: int = 10000  # YouTube API günlük quota limiti
    used_quota: int = 0
    remaining_quota: int = 10000
    reset_time: datetime = None
    last_updated: datetime = None

    def __post_init__(self):
        # Convert string to datetime if needed
        if isinstance(self.reset_time, str):
            self.reset_time = datetime.fromisoformat(self.reset_time)
        elif self.reset_time is None:
            # Quota her gün gece yarısı (PST) sıfırlanır
            # Basitleştirme için: 24 saat sonra
            self.reset_time = datetime.now() + timedelta(days=1)

        if isinstance(self.last_updated, str):
            self.last_updated = datetime.fromisoformat(self.last_updated)
        elif self.last_updated is None:
            self.last_updated = datetime.now()


class YouTubeRateLimiter:
    """
    YouTube API için özel rate limiter ve quota tracker

    Features:
    - YouTube API quota tracking (günlük 10,000 limit)
    - Quota kullanımı izleme ve uyarı
    - Cache-first stratejisi (quota tasarrufu)
    - Adaptive rate limiting (quota'ya göre)
    - Quota reset tracking

    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.7, 7.8, 7.9
    """

    # YouTube API operation costs (quota units)
    OPERATION_COSTS = {
        "search": 100,  # search.list operation
        "video_details": 1,  # videos.list operation
        "channel_details": 1,  # channels.list operation
    }

    # Quota thresholds for warnings
    QUOTA_WARNING_THRESHOLD = 0.8  # 80% kullanıldığında uyar
    QUOTA_CRITICAL_THRESHOLD = 0.95  # 95% kullanıldığında kritik uyarı

    def __init__(self):
        self.cache_key = "youtube:quota:info"
        self._quota_info: Optional[YouTubeQuotaInfo] = None

    async def initialize(self) -> bool:
        """
        Rate limiter'ı başlat ve quota bilgisini yükle

        Returns:
            bool: Başarılı ise True
        """
        try:
            # Cache'den quota bilgisini yükle
            cached_quota = await cache_manager.get(self.cache_key)

            if cached_quota:
                self._quota_info = YouTubeQuotaInfo(**cached_quota)
                logger.info(
                    f"YouTube quota bilgisi yüklendi: {self._quota_info.remaining_quota}/{self._quota_info.daily_limit}",
                    extra_data={
                        "used_quota": self._quota_info.used_quota,
                        "remaining_quota": self._quota_info.remaining_quota,
                        "reset_time": self._quota_info.reset_time.isoformat(),
                    },
                )
            else:
                # Yeni quota bilgisi oluştur
                self._quota_info = YouTubeQuotaInfo()
                await self._save_quota_info()
                logger.info("Yeni YouTube quota bilgisi oluşturuldu")

            # Quota reset kontrolü
            await self._check_quota_reset()

            return True

        except Exception as e:
            logger.error(f"YouTube rate limiter başlatma hatası: {e}")
            # Fallback: yeni quota bilgisi oluştur
            self._quota_info = YouTubeQuotaInfo()
            return False

    async def check_quota_available(
        self, operation: str = "search", required_quota: Optional[int] = None
    ) -> tuple[bool, str]:
        """
        Quota'nın yeterli olup olmadığını kontrol et

        Args:
            operation: YouTube API operasyonu ('search', 'video_details', etc.)
            required_quota: Gerekli quota (None ise operation'dan hesaplanır)

        Returns:
            Tuple of (is_available, message)
        """
        if not self._quota_info:
            await self.initialize()

        # Quota reset kontrolü
        await self._check_quota_reset()

        # Gerekli quota'yı hesapla
        if required_quota is None:
            required_quota = self.OPERATION_COSTS.get(operation, 1)

        # Quota yeterli mi?
        if self._quota_info.remaining_quota >= required_quota:
            return True, "Quota available"

        # Quota yetersiz
        reset_time_str = self._quota_info.reset_time.strftime("%H:%M:%S")
        message = (
            f"YouTube API quota yetersiz. "
            f"Kalan: {self._quota_info.remaining_quota}, "
            f"Gerekli: {required_quota}. "
            f"Quota sıfırlanma: {reset_time_str}"
        )

        logger.warning(
            "YouTube API quota yetersiz",
            extra_data={
                "remaining_quota": self._quota_info.remaining_quota,
                "required_quota": required_quota,
                "reset_time": reset_time_str,
            },
        )

        return False, message

    async def consume_quota(
        self, operation: str = "search", quota_amount: Optional[int] = None
    ) -> bool:
        """
        Quota tüket

        Args:
            operation: YouTube API operasyonu
            quota_amount: Tüketilecek quota (None ise operation'dan hesaplanır)

        Returns:
            bool: Başarılı ise True
        """
        if not self._quota_info:
            await self.initialize()

        # Quota miktarını hesapla
        if quota_amount is None:
            quota_amount = self.OPERATION_COSTS.get(operation, 1)

        # Quota tüket
        self._quota_info.used_quota += quota_amount
        self._quota_info.remaining_quota = max(
            0, self._quota_info.daily_limit - self._quota_info.used_quota
        )
        self._quota_info.last_updated = datetime.now()

        # Cache'e kaydet
        await self._save_quota_info()

        # Quota uyarıları
        await self._check_quota_warnings()

        logger.debug(
            f"YouTube quota tüketildi: {quota_amount} units",
            extra_data={
                "operation": operation,
                "quota_amount": quota_amount,
                "remaining_quota": self._quota_info.remaining_quota,
                "used_quota": self._quota_info.used_quota,
            },
        )

        return True

    async def get_quota_info(self) -> YouTubeQuotaInfo:
        """
        Mevcut quota bilgisini al

        Returns:
            YouTubeQuotaInfo: Quota bilgisi
        """
        if not self._quota_info:
            await self.initialize()

        await self._check_quota_reset()

        return self._quota_info

    async def reset_quota(self) -> None:
        """
        Quota'yı manuel olarak sıfırla (test veya yeni gün için)
        """
        self._quota_info = YouTubeQuotaInfo()
        await self._save_quota_info()

        logger.info("YouTube quota manuel olarak sıfırlandı")

    async def _check_quota_reset(self) -> None:
        """
        Quota reset zamanını kontrol et ve gerekirse sıfırla
        """
        if not self._quota_info:
            return

        now = datetime.now()

        # Reset zamanı geçti mi?
        if now >= self._quota_info.reset_time:
            logger.info(
                "YouTube quota otomatik sıfırlandı (yeni gün)",
                extra_data={
                    "previous_used": self._quota_info.used_quota,
                    "reset_time": self._quota_info.reset_time.isoformat(),
                },
            )

            # Quota'yı sıfırla
            self._quota_info = YouTubeQuotaInfo()
            await self._save_quota_info()

    async def _check_quota_warnings(self) -> None:
        """
        Quota kullanım oranını kontrol et ve uyarı ver
        """
        if not self._quota_info:
            return

        usage_ratio = self._quota_info.used_quota / self._quota_info.daily_limit

        # Kritik seviye (%95+)
        if usage_ratio >= self.QUOTA_CRITICAL_THRESHOLD:
            logger.error(
                f"[CRITICAL] YouTube API quota kritik seviyede: %{usage_ratio * 100:.1f}",
                extra_data={
                    "used_quota": self._quota_info.used_quota,
                    "daily_limit": self._quota_info.daily_limit,
                    "remaining_quota": self._quota_info.remaining_quota,
                    "usage_ratio": usage_ratio,
                },
            )

        # Uyarı seviyesi (%80+)
        elif usage_ratio >= self.QUOTA_WARNING_THRESHOLD:
            logger.warning(
                f"[WARNING] YouTube API quota yüksek seviyede: %{usage_ratio * 100:.1f}",
                extra_data={
                    "used_quota": self._quota_info.used_quota,
                    "daily_limit": self._quota_info.daily_limit,
                    "remaining_quota": self._quota_info.remaining_quota,
                    "usage_ratio": usage_ratio,
                },
            )

    async def _save_quota_info(self) -> None:
        """
        Quota bilgisini cache'e kaydet
        """
        try:
            quota_dict = {
                "daily_limit": self._quota_info.daily_limit,
                "used_quota": self._quota_info.used_quota,
                "remaining_quota": self._quota_info.remaining_quota,
                "reset_time": self._quota_info.reset_time.isoformat(),
                "last_updated": self._quota_info.last_updated.isoformat(),
            }

            # 25 saat TTL (quota reset'ten biraz sonra)
            await cache_manager.set(self.cache_key, quota_dict, ttl=90000)  # 25 hours

        except Exception as e:
            logger.error(f"Quota bilgisi kaydetme hatası: {e}")

    def should_use_cache(self) -> bool:
        """
        Cache kullanılmalı mı? (Quota tasarrufu için)

        Returns:
            bool: Cache kullanılmalıysa True
        """
        if not self._quota_info:
            return True  # Güvenli taraf: cache kullan

        usage_ratio = self._quota_info.used_quota / self._quota_info.daily_limit

        # Quota %80'in üzerindeyse agresif cache kullan
        if usage_ratio >= self.QUOTA_WARNING_THRESHOLD:
            return True

        # Normal durumda cache stratejisine bırak
        return False


# Global singleton instance
_youtube_rate_limiter: Optional[YouTubeRateLimiter] = None


def get_youtube_rate_limiter() -> YouTubeRateLimiter:
    """
    YouTube rate limiter singleton instance'ını al

    Returns:
        YouTubeRateLimiter: Global rate limiter instance
    """
    global _youtube_rate_limiter

    if _youtube_rate_limiter is None:
        _youtube_rate_limiter = YouTubeRateLimiter()

    return _youtube_rate_limiter
