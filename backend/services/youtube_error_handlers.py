"""
YouTube API Error Handlers
YouTube API hataları için özel error handling ve fallback mekanizmaları
Teknofest 2025 - Eğitim Eylemci Projesi
"""

import asyncio
import logging
import pickle
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


@dataclass
class FallbackResponse:
    """Fallback yanıt modeli"""

    videos: List[Any]
    source: str  # 'cache', 'mock', 'fallback'
    message: str


class QuotaExceededError(ExternalServiceError):
    """YouTube API quota aşıldı hatası"""

    def __init__(self, message: str = "YouTube API quota exceeded"):
        super().__init__(message=message, service_name="YouTube")


class InvalidAPIKeyError(ExternalServiceError):
    """Geçersiz YouTube API key hatası"""

    def __init__(self, message: str = "Invalid YouTube API key"):
        super().__init__(message=message, service_name="YouTube")


class RateLimitError(ExternalServiceError):
    """Rate limit aşıldı hatası"""

    def __init__(self, message: str = "YouTube API rate limit exceeded"):
        super().__init__(message=message, service_name="YouTube")


class YouTubeAPIErrorHandler:
    """
    YouTube API hata yönetimi

    API hatalarını yakalar ve uygun fallback mekanizmalarını devreye sokar:
    - Quota exceeded: Cache'den video önerileri döndür
    - Invalid API key: Mock data kullan
    - Rate limit: Exponential backoff ile retry yap
    """

    def __init__(self, cache_manager: Optional[Any] = None):
        """
        YouTubeAPIErrorHandler'ı başlat

        Args:
            cache_manager: Cache yöneticisi (opsiyonel)
        """
        self.cache_manager = cache_manager
        self.max_retries = 3
        self.base_delay = 1.0  # 1 saniye

        # Mock video data (API kullanılamadığında)
        self.mock_videos = self._create_mock_videos()

        logger.info("YouTube API Error Handler initialized")

    async def handle_api_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> FallbackResponse:
        """
        API hatasını yönet ve fallback yanıt döndür

        Args:
            error: Oluşan hata
            context: Hata bağlamı (subject, topic, vb.)

        Returns:
            FallbackResponse: Fallback yanıt
        """
        try:
            logger.warning(
                f"Handling YouTube API error: {type(error).__name__}: {str(error)}"
            )

            # Hata tipine göre fallback stratejisi belirle
            if isinstance(error, QuotaExceededError):
                return await self.get_cached_videos(context)

            elif isinstance(error, InvalidAPIKeyError):
                return await self.get_mock_videos(context)

            elif isinstance(error, RateLimitError):
                # Rate limit için retry yapılacak, burada fallback döndür
                logger.warning("Rate limit error, returning cached videos")
                return await self.get_cached_videos(context)

            else:
                # Genel hata - cache'den dene, yoksa mock data
                logger.error(f"Unhandled YouTube API error: {str(error)}")
                cached_response = await self.get_cached_videos(context)
                if cached_response.videos:
                    return cached_response
                return await self.get_mock_videos(context)

        except Exception as e:
            logger.error(f"Error in error handler: {str(e)}")
            return FallbackResponse(
                videos=[], source="error", message=f"Hata yönetimi başarısız: {str(e)}"
            )

    async def get_cached_videos(
        self, context: Optional[Dict[str, Any]] = None
    ) -> FallbackResponse:
        """
        Cache'den video önerilerini al

        Args:
            context: Arama bağlamı

        Returns:
            FallbackResponse: Cache'den alınan videolar
        """
        try:
            if not self.cache_manager:
                logger.warning("Cache manager not available, returning empty list")
                return FallbackResponse(
                    videos=[], source="cache", message="Cache yöneticisi mevcut değil"
                )

            # Cache key oluştur
            cache_key = self._build_cache_key(context)

            # Cache'den al
            cached_videos = await self.cache_manager.get(cache_key)

            if cached_videos:
                logger.info(f"Retrieved {len(cached_videos)} videos from cache")
                return FallbackResponse(
                    videos=cached_videos,
                    source="cache",
                    message="Önbellekten video önerileri alındı",
                )
            else:
                logger.warning("No cached videos found")
                return FallbackResponse(
                    videos=[], source="cache", message="Önbellekte video bulunamadı"
                )

        except Exception as e:
            logger.error(f"Error getting cached videos: {str(e)}")
            return FallbackResponse(
                videos=[], source="cache", message=f"Cache hatası: {str(e)}"
            )

    async def get_mock_videos(
        self, context: Optional[Dict[str, Any]] = None
    ) -> FallbackResponse:
        """
        Mock video data döndür

        Args:
            context: Arama bağlamı

        Returns:
            FallbackResponse: Mock videolar
        """
        try:
            subject = context.get("subject", "genel") if context else "genel"

            # Subject'e göre mock videoları filtrele
            filtered_videos = [
                video
                for video in self.mock_videos
                if subject.lower() in video.get("title", "").lower()
                or subject.lower() in video.get("description", "").lower()
            ]

            # Eğer subject'e özel video yoksa, tüm mock videoları döndür
            if not filtered_videos:
                filtered_videos = self.mock_videos[:5]

            logger.info(
                f"Returning {len(filtered_videos)} mock videos for subject '{subject}'"
            )

            return FallbackResponse(
                videos=filtered_videos,
                source="mock",
                message="Demo video önerileri gösteriliyor (API kullanılamıyor)",
            )

        except Exception as e:
            logger.error(f"Error getting mock videos: {str(e)}")
            return FallbackResponse(
                videos=[], source="mock", message=f"Mock data hatası: {str(e)}"
            )

    async def get_fallback_videos(
        self, context: Optional[Dict[str, Any]] = None
    ) -> FallbackResponse:
        """
        Genel fallback videoları döndür

        Args:
            context: Arama bağlamı

        Returns:
            FallbackResponse: Fallback videolar
        """
        # Önce cache'den dene
        cached_response = await self.get_cached_videos(context)
        if cached_response.videos:
            return cached_response

        # Cache'de yoksa mock data döndür
        return await self.get_mock_videos(context)

    async def retry_with_backoff(
        self, func, *args, max_retries: Optional[int] = None, **kwargs
    ) -> Any:
        """
        Exponential backoff ile retry yap

        Args:
            func: Çalıştırılacak fonksiyon
            *args: Fonksiyon argümanları
            max_retries: Maksimum retry sayısı
            **kwargs: Fonksiyon keyword argümanları

        Returns:
            Fonksiyon sonucu

        Raises:
            Son hatayı raise eder
        """
        max_retries = max_retries or self.max_retries
        last_error = None

        for retry_count in range(max_retries):
            try:
                # Fonksiyonu çalıştır
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Başarılı
                if retry_count > 0:
                    logger.info(f"Retry successful after {retry_count} attempts")

                return result

            except RateLimitError as e:
                last_error = e

                if retry_count < max_retries - 1:
                    # Exponential backoff hesapla
                    wait_time = self.base_delay * (2**retry_count)
                    logger.warning(
                        f"Rate limit hit, waiting {wait_time}s before retry "
                        f"(attempt {retry_count + 1}/{max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Max retries ({max_retries}) reached, giving up")
                    raise last_error

            except (QuotaExceededError, InvalidAPIKeyError) as e:
                # Bu hatalar için retry yapma, direkt fallback'e geç
                logger.error(f"Non-retryable error: {type(e).__name__}")
                raise e

            except Exception as e:
                last_error = e

                if retry_count < max_retries - 1:
                    wait_time = self.base_delay * (2**retry_count)
                    logger.warning(
                        f"Error occurred, retrying in {wait_time}s "
                        f"(attempt {retry_count + 1}/{max_retries}): {str(e)}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Max retries ({max_retries}) reached")
                    raise last_error

        # Bu noktaya gelmemeli ama güvenlik için
        if last_error:
            raise last_error

    def _build_cache_key(self, context: Optional[Dict[str, Any]]) -> str:
        """
        Cache key oluştur

        Args:
            context: Arama bağlamı

        Returns:
            Cache key
        """
        if not context:
            return "youtube:videos:default"

        subject = context.get("subject", "")
        topic = context.get("topic", "")
        difficulty = context.get("difficulty", "")

        parts = ["youtube", "videos"]
        if subject:
            parts.append(subject)
        if topic:
            parts.append(topic)
        if difficulty:
            parts.append(difficulty)

        return ":".join(parts)

    def _create_mock_videos(self) -> List[Dict[str, Any]]:
        """
        Mock video data oluştur

        Returns:
            Mock video listesi
        """
        return [
            {
                "video_id": "mock_math_1",
                "title": "Matematik Türev Konu Anlatımı - Temel Kavramlar",
                "channel_name": "TonguçAkademi",
                "channel_id": "mock_channel_1",
                "description": "Türev konusunu baştan sona anlatan kapsamlı video",
                "thumbnail_url": "https://i.ytimg.com/vi/mock_math_1/default.jpg",
                "duration": "PT15M30S",
                "duration_minutes": 15,
                "view_count": 50000,
                "like_count": 2500,
                "upload_date": "2024-01-15",
                "url": "https://www.youtube.com/watch?v=mock_math_1",
                "tags": ["matematik", "türev", "konu anlatımı"],
                "caption_available": True,
                "definition": "hd",
                "language": "tr",
            },
            {
                "video_id": "mock_physics_1",
                "title": "Fizik Hareket Konusu - Newton Yasaları",
                "channel_name": "Khan Academy Türkçe",
                "channel_id": "mock_channel_2",
                "description": "Newton'un hareket yasalarını detaylı açıklama",
                "thumbnail_url": "https://i.ytimg.com/vi/mock_physics_1/default.jpg",
                "duration": "PT20M45S",
                "duration_minutes": 20,
                "view_count": 75000,
                "like_count": 3800,
                "upload_date": "2024-02-10",
                "url": "https://www.youtube.com/watch?v=mock_physics_1",
                "tags": ["fizik", "hareket", "newton"],
                "caption_available": True,
                "definition": "hd",
                "language": "tr",
            },
            {
                "video_id": "mock_chemistry_1",
                "title": "Kimya Atom Yapısı - Periyodik Tablo",
                "channel_name": "KAMP Online",
                "channel_id": "mock_channel_3",
                "description": "Atom yapısı ve periyodik tablo detaylı anlatım",
                "thumbnail_url": "https://i.ytimg.com/vi/mock_chemistry_1/default.jpg",
                "duration": "PT18M20S",
                "duration_minutes": 18,
                "view_count": 60000,
                "like_count": 3000,
                "upload_date": "2024-03-05",
                "url": "https://www.youtube.com/watch?v=mock_chemistry_1",
                "tags": ["kimya", "atom", "periyodik tablo"],
                "caption_available": True,
                "definition": "hd",
                "language": "tr",
            },
            {
                "video_id": "mock_math_2",
                "title": "Matematik İntegral Konu Anlatımı",
                "channel_name": "Hocalara Geldik",
                "channel_id": "mock_channel_4",
                "description": "İntegral konusunu örneklerle açıklama",
                "thumbnail_url": "https://i.ytimg.com/vi/mock_math_2/default.jpg",
                "duration": "PT25M10S",
                "duration_minutes": 25,
                "view_count": 45000,
                "like_count": 2200,
                "upload_date": "2024-01-20",
                "url": "https://www.youtube.com/watch?v=mock_math_2",
                "tags": ["matematik", "integral", "konu anlatımı"],
                "caption_available": True,
                "definition": "hd",
                "language": "tr",
            },
            {
                "video_id": "mock_biology_1",
                "title": "Biyoloji Hücre Yapısı - Organeller",
                "channel_name": "Evrim Ağacı",
                "channel_id": "mock_channel_5",
                "description": "Hücre yapısı ve organellerin görevleri",
                "thumbnail_url": "https://i.ytimg.com/vi/mock_biology_1/default.jpg",
                "duration": "PT22M30S",
                "duration_minutes": 22,
                "view_count": 55000,
                "like_count": 2800,
                "upload_date": "2024-02-25",
                "url": "https://www.youtube.com/watch?v=mock_biology_1",
                "tags": ["biyoloji", "hücre", "organeller"],
                "caption_available": True,
                "definition": "hd",
                "language": "tr",
            },
        ]


class ValidationErrorHandler:
    """
    Validation hata yönetimi

    Video validation başarısızlıklarını loglar ve alternatif video arar.
    """

    def __init__(self, metrics_collector: Optional[Any] = None):
        """
        ValidationErrorHandler'ı başlat

        Args:
            metrics_collector: Metrik toplayıcı (opsiyonel)
        """
        self.metrics_collector = metrics_collector
        self.failure_counts = {}

        logger.info("Validation Error Handler initialized")

    def handle_validation_failure(
        self, video_id: str, failure_type: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Validation başarısızlığını yönet

        Failure Types:
        - turkish_filter_failed: Türkçe filtresi başarısız
        - relevance_too_low: Konu uygunluğu düşük
        - accessibility_failed: Erişilebilirlik kontrolü başarısız
        - quality_too_low: Kalite skoru düşük

        Args:
            video_id: Video ID
            failure_type: Başarısızlık tipi
            details: Ek detaylar
        """
        try:
            logger.warning(
                f"Video {video_id} failed validation: {failure_type}"
                + (f" - {details}" if details else "")
            )

            # Başarısızlık sayacını güncelle
            if failure_type not in self.failure_counts:
                self.failure_counts[failure_type] = 0
            self.failure_counts[failure_type] += 1

            # Metrikleri kaydet
            if self.metrics_collector:
                self.metrics_collector.record_failure(
                    video_id=video_id, failure_type=failure_type, details=details
                )

        except Exception as e:
            logger.error(f"Error handling validation failure: {str(e)}")

    def get_failure_stats(self) -> Dict[str, int]:
        """
        Başarısızlık istatistiklerini al

        Returns:
            Başarısızlık sayıları
        """
        return self.failure_counts.copy()

    def reset_stats(self) -> None:
        """İstatistikleri sıfırla"""
        self.failure_counts = {}
        logger.info("Validation failure stats reset")


class TimeoutHandler:
    """
    Timeout yönetimi

    Async işlemleri timeout ile çalıştırır ve timeout durumunda
    uygun fallback mekanizmasını devreye sokar.
    """

    def __init__(self, default_timeout: int = 5):
        """
        TimeoutHandler'ı başlat

        Args:
            default_timeout: Varsayılan timeout süresi (saniye)
        """
        self.default_timeout = default_timeout
        logger.info(
            f"Timeout Handler initialized with {default_timeout}s default timeout"
        )

    async def with_timeout(
        self, coro, timeout_seconds: Optional[int] = None, fallback_value: Any = None
    ) -> Any:
        """
        Timeout ile async işlem yürüt

        Args:
            coro: Coroutine
            timeout_seconds: Timeout süresi (saniye)
            fallback_value: Timeout durumunda döndürülecek değer

        Returns:
            İşlem sonucu veya fallback değeri
        """
        timeout = timeout_seconds or self.default_timeout

        try:
            result = await asyncio.wait_for(coro, timeout=timeout)
            return result

        except asyncio.TimeoutError:
            logger.warning(
                f"Operation timed out after {timeout}s, returning fallback value"
            )
            return fallback_value

        except Exception as e:
            logger.error(f"Error during timeout operation: {str(e)}")
            return fallback_value

    async def with_timeout_and_retry(
        self,
        coro_func,
        *args,
        timeout_seconds: Optional[int] = None,
        max_retries: int = 2,
        **kwargs,
    ) -> Any:
        """
        Timeout ve retry ile async işlem yürüt

        Args:
            coro_func: Coroutine fonksiyonu
            *args: Fonksiyon argümanları
            timeout_seconds: Timeout süresi (saniye)
            max_retries: Maksimum retry sayısı
            **kwargs: Fonksiyon keyword argümanları

        Returns:
            İşlem sonucu

        Raises:
            Son hatayı raise eder
        """
        timeout = timeout_seconds or self.default_timeout
        last_error = None

        for retry_count in range(max_retries + 1):
            try:
                coro = coro_func(*args, **kwargs)
                result = await asyncio.wait_for(coro, timeout=timeout)

                if retry_count > 0:
                    logger.info(f"Operation successful after {retry_count} retries")

                return result

            except asyncio.TimeoutError as e:
                last_error = e

                if retry_count < max_retries:
                    logger.warning(
                        f"Operation timed out, retrying "
                        f"(attempt {retry_count + 1}/{max_retries + 1})"
                    )
                    await asyncio.sleep(0.5)
                else:
                    logger.error(
                        f"Operation timed out after {max_retries + 1} attempts"
                    )
                    raise last_error

            except Exception as e:
                last_error = e
                logger.error(f"Error during operation: {str(e)}")
                raise e

        if last_error:
            raise last_error


# Global instances
youtube_error_handler = YouTubeAPIErrorHandler()
validation_error_handler = ValidationErrorHandler()
timeout_handler = TimeoutHandler()


async def get_youtube_error_handler() -> YouTubeAPIErrorHandler:
    """YouTube error handler instance'ını al"""
    return youtube_error_handler


async def get_validation_error_handler() -> ValidationErrorHandler:
    """Validation error handler instance'ını al"""
    return validation_error_handler


async def get_timeout_handler() -> TimeoutHandler:
    """Timeout handler instance'ını al"""
    return timeout_handler
