"""
Video Quality Validator Service
Video erişilebilirliği ve kalitesini doğrular
Teknofest 2025 - Eğitim Eylemci Projesi
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp

from services.youtube_error_handlers import (
    QuotaExceededError,
    InvalidAPIKeyError,
    RateLimitError,
    TimeoutHandler,
)

logger = logging.getLogger(__name__)


@dataclass
class VideoAccessibilityResult:
    """Video erişilebilirlik sonucu"""

    is_accessible: bool
    is_embeddable: bool
    privacy_status: str  # public, private, unlisted
    error_reason: Optional[str]


class VideoQualityValidator:
    """
    Video kalite doğrulama servisi

    YouTube API kullanarak video erişilebilirliğini kontrol eder
    ve kalite skorlaması yapar.
    """

    def __init__(self):
        """VideoQualityValidator'ı başlat"""
        self.api_key = os.getenv("YOUTUBE_API_KEY", "")
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_delay = 0.1  # 100ms delay between requests
        self.max_retries = 3

        # Timeout handler
        self.timeout_handler = TimeoutHandler(default_timeout=10)

        # Güvenilir eğitim kanalları
        self.trusted_channels = {
            "TonguçAkademi",
            "Khan Academy Türkçe",
            "KAMP Online",
            "Hocalara Geldik",
            "MEB Uzaktan Eğitim",
            "BTK Akademi",
            "Evrim Ağacı",
            "Matematik Öğretmeni",
            "Fizik Öğretmeni",
            "Kimya Öğretmeni",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def validate_video_accessibility(
        self, video_id: str
    ) -> VideoAccessibilityResult:
        """
        Video erişilebilirliğini kontrol eder

        Args:
            video_id: YouTube video ID

        Returns:
            VideoAccessibilityResult: Erişilebilirlik sonucu
        """
        try:
            if not self.api_key:
                logger.warning(
                    f"YouTube API key not found, assuming video {video_id} is accessible"
                )
                return VideoAccessibilityResult(
                    is_accessible=True,
                    is_embeddable=True,
                    privacy_status="public",
                    error_reason=None,
                )

            # YouTube API'den video bilgilerini al
            params = {
                "part": "status,contentDetails",
                "id": video_id,
                "key": self.api_key,
            }

            video_data = await self._make_api_request("videos", params)

            if not video_data or "items" not in video_data or not video_data["items"]:
                logger.warning(f"Video {video_id} not found")
                return VideoAccessibilityResult(
                    is_accessible=False,
                    is_embeddable=False,
                    privacy_status="unknown",
                    error_reason="Video not found",
                )

            item = video_data["items"][0]
            status = item.get("status", {})
            content_details = item.get("contentDetails", {})

            # Erişilebilirlik kontrolü
            upload_status = status.get("uploadStatus", "")
            privacy_status = status.get("privacyStatus", "")
            is_embeddable = status.get("embeddable", True)

            # Video erişilebilir mi?
            is_accessible = upload_status == "processed" and privacy_status in [
                "public",
                "unlisted",
            ]

            error_reason = None
            if not is_accessible:
                if upload_status != "processed":
                    error_reason = f"Upload status: {upload_status}"
                elif privacy_status not in ["public", "unlisted"]:
                    error_reason = f"Privacy status: {privacy_status}"

            result = VideoAccessibilityResult(
                is_accessible=is_accessible,
                is_embeddable=is_embeddable,
                privacy_status=privacy_status,
                error_reason=error_reason,
            )

            logger.info(
                f"Video {video_id} accessibility: {is_accessible} "
                f"(privacy: {privacy_status}, embeddable: {is_embeddable})"
            )

            return result

        except Exception as e:
            logger.error(f"Video accessibility check error for {video_id}: {str(e)}")
            return VideoAccessibilityResult(
                is_accessible=False,
                is_embeddable=False,
                privacy_status="unknown",
                error_reason=str(e),
            )

    async def calculate_quality_score(self, video_metadata: Dict[str, Any]) -> float:
        """
        Video kalite skoru hesaplar

        Quality Factors:
        - View count (normalized): 0-0.2
        - Like ratio: 0-0.2
        - Duration (5-60 min ideal): 0-0.2
        - Caption availability: 0-0.1
        - HD quality: 0-0.1
        - Channel trust: 0-0.2

        Args:
            video_metadata: Video metadata dictionary

        Returns:
            float: 0.0-1.0 arası kalite skoru
        """
        try:
            score = 0.0

            # 1. View count (normalized, 0-0.2)
            view_count = video_metadata.get("view_count", 0)
            if 10000 <= view_count <= 500000:
                score += 0.2
            elif 5000 <= view_count < 10000 or 500000 < view_count <= 1000000:
                score += 0.15
            elif view_count > 1000000:
                score += 0.1  # Çok popüler videolar eğitim odaklı olmayabilir
            elif 1000 <= view_count < 5000:
                score += 0.05

            logger.debug(f"View count score: {view_count} views")

            # 2. Like ratio (0-0.2)
            like_count = video_metadata.get("like_count", 0)
            if view_count > 0 and like_count > 0:
                like_ratio = like_count / view_count
                if like_ratio > 0.02:  # %2+
                    score += 0.2
                elif like_ratio > 0.01:  # %1-2
                    score += 0.15
                elif like_ratio > 0.005:  # %0.5-1
                    score += 0.1
                elif like_ratio > 0.002:  # %0.2-0.5
                    score += 0.05

                logger.debug(
                    f"Like ratio score: {like_ratio:.4f} ({like_count}/{view_count})"
                )

            # 3. Duration (0-0.2)
            duration_minutes = video_metadata.get("duration_minutes", 0)
            if 5 <= duration_minutes <= 60:
                score += 0.2
            elif 3 <= duration_minutes < 5 or 60 < duration_minutes <= 90:
                score += 0.1
            elif 1 <= duration_minutes < 3 or 90 < duration_minutes <= 120:
                score += 0.05

            logger.debug(f"Duration score: {duration_minutes} minutes")

            # 4. Caption availability (0-0.1)
            if video_metadata.get("caption_available", False):
                score += 0.1
                logger.debug("Caption available: +0.1")

            # 5. HD quality (0-0.1)
            if video_metadata.get("definition", "") == "hd":
                score += 0.1
                logger.debug("HD quality: +0.1")

            # 6. Channel trust (0-0.2)
            channel_name = video_metadata.get("channel_name", "")
            if self._is_trusted_channel(channel_name):
                score += 0.2
                logger.debug(f"Trusted channel: {channel_name} +0.2")

            final_score = min(score, 1.0)

            logger.info(f"Quality score: {final_score:.2f} for video")

            return final_score

        except Exception as e:
            logger.error(f"Quality score calculation error: {str(e)}")
            # Return 0.0 for invalid metadata, not 0.5
            return 0.0

    async def batch_validate_videos(
        self, video_ids: List[str], timeout_seconds: int = 5
    ) -> Dict[str, VideoAccessibilityResult]:
        """
        Toplu video doğrulama (paralel)

        Args:
            video_ids: Video ID listesi
            timeout_seconds: Timeout süresi (saniye)

        Returns:
            Dict[str, VideoAccessibilityResult]: Video ID -> Sonuç mapping
        """
        try:
            if not video_ids:
                return {}

            logger.info(
                f"Batch validating {len(video_ids)} videos with {timeout_seconds}s timeout"
            )

            # Paralel validation tasks oluştur
            tasks = [
                self.validate_video_accessibility(video_id) for video_id in video_ids
            ]

            # Timeout ile çalıştır
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=timeout_seconds,
                )
            except asyncio.TimeoutError:
                logger.warning(f"Batch validation timed out after {timeout_seconds}s")
                # Timeout durumunda kısmi sonuçlar döndür
                results = [
                    VideoAccessibilityResult(
                        is_accessible=False,
                        is_embeddable=False,
                        privacy_status="unknown",
                        error_reason="Validation timeout",
                    )
                    for _ in video_ids
                ]

            # Sonuçları dictionary'e dönüştür
            result_dict = {}
            for video_id, result in zip(video_ids, results):
                if isinstance(result, Exception):
                    logger.error(f"Error validating video {video_id}: {str(result)}")
                    result_dict[video_id] = VideoAccessibilityResult(
                        is_accessible=False,
                        is_embeddable=False,
                        privacy_status="unknown",
                        error_reason=str(result),
                    )
                else:
                    result_dict[video_id] = result

            # İstatistikler
            accessible_count = sum(1 for r in result_dict.values() if r.is_accessible)
            logger.info(
                f"Batch validation complete: {accessible_count}/{len(video_ids)} "
                f"videos accessible"
            )

            return result_dict

        except Exception as e:
            logger.error(f"Batch validation error: {str(e)}")
            return {}

    async def _make_api_request(
        self, endpoint: str, params: Dict[str, Any], retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        YouTube API'ye istek gönder

        Args:
            endpoint: API endpoint
            params: Parametreler
            retry_count: Retry sayısı

        Returns:
            API yanıtı
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/{endpoint}"

            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)

            async with session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 403:
                    # Quota exceeded or API key invalid
                    error_data = await response.json()
                    error_reason = (
                        error_data.get("error", {})
                        .get("errors", [{}])[0]
                        .get("reason", "unknown")
                    )

                    if error_reason == "quotaExceeded":
                        logger.error("YouTube API quota exceeded")
                        raise QuotaExceededError("YouTube API quota exceeded")
                    elif error_reason == "keyInvalid":
                        logger.error("Invalid YouTube API key")
                        raise InvalidAPIKeyError("Invalid YouTube API key")
                    else:
                        logger.error(f"YouTube API error 403: {error_reason}")
                        raise Exception(f"YouTube API access denied: {error_reason}")
                elif response.status == 404:
                    logger.warning(f"Resource not found (404)")
                    return None
                elif response.status == 429:
                    # Rate limit exceeded
                    if retry_count < self.max_retries:
                        wait_time = (2**retry_count) * self.rate_limit_delay
                        logger.warning(
                            f"Rate limit hit, waiting {wait_time}s before retry"
                        )
                        await asyncio.sleep(wait_time)
                        return await self._make_api_request(
                            endpoint, params, retry_count + 1
                        )
                    else:
                        raise RateLimitError("Rate limit exceeded, max retries reached")
                else:
                    logger.error(
                        f"YouTube API error {response.status}: {await response.text()}"
                    )
                    return None

        except asyncio.TimeoutError:
            logger.error(f"API request timeout for {endpoint}")
            if retry_count < self.max_retries:
                return await self._make_api_request(endpoint, params, retry_count + 1)
            return None
        except aiohttp.ClientError as e:
            logger.error(f"Network error calling YouTube API: {str(e)}")
            if retry_count < self.max_retries:
                await asyncio.sleep(1)
                return await self._make_api_request(endpoint, params, retry_count + 1)
            return None
        except Exception as e:
            logger.error(f"Error calling YouTube API: {str(e)}")
            return None

    def _is_trusted_channel(self, channel_name: str) -> bool:
        """
        Güvenilir kanal kontrolü

        Args:
            channel_name: Kanal adı

        Returns:
            bool: Güvenilir kanal ise True
        """
        if not channel_name:
            return False

        # Tam eşleşme
        if channel_name in self.trusted_channels:
            return True

        # Case-insensitive ve kısmi eşleşme
        channel_lower = channel_name.lower().strip()
        for trusted in self.trusted_channels:
            trusted_lower = trusted.lower()
            # Tam eşleşme (case-insensitive)
            if trusted_lower == channel_lower:
                return True
            # Kısmi eşleşme - kanal adı güvenilir kanalı içeriyor veya tam tersi
            if trusted_lower in channel_lower or channel_lower in trusted_lower:
                return True

        return False

    def _parse_duration_to_minutes(self, duration: str) -> int:
        """
        YouTube duration formatını dakikaya çevir

        Args:
            duration: PT15M30S formatında süre

        Returns:
            Dakika cinsinden süre
        """
        if not duration:
            return 0

        try:
            # PT15M30S -> 15.5 dakika
            duration = duration.replace("PT", "")

            hours = 0
            minutes = 0
            seconds = 0

            # Hours
            if "H" in duration:
                hours_str = duration.split("H")[0]
                hours = int(hours_str) if hours_str.isdigit() else 0
                duration = duration.split("H")[1] if "H" in duration else duration

            # Minutes
            if "M" in duration:
                minutes_str = duration.split("M")[0]
                minutes = int(minutes_str) if minutes_str.isdigit() else 0
                duration = duration.split("M")[1] if "M" in duration else duration

            # Seconds
            if "S" in duration:
                seconds_str = duration.split("S")[0]
                seconds = int(seconds_str) if seconds_str.isdigit() else 0

            total_minutes = hours * 60 + minutes + (seconds / 60)
            return int(total_minutes)

        except Exception as e:
            logger.error(f"Error parsing duration {duration}: {str(e)}")
            return 15  # Default 15 minutes


# Global instance
video_quality_validator = VideoQualityValidator()


async def get_video_quality_validator() -> VideoQualityValidator:
    """Video quality validator instance'ını al"""
    return video_quality_validator
