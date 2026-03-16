"""
YouTube API Entegrasyonu
Eğitim videoları arama ve öneri
Teknofest 2025 - Eğitim Eylemci Projesi
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class YouTubeVideo:
    """YouTube video modeli"""

    video_id: str
    title: str
    description: str
    channel_name: str
    channel_id: str
    thumbnail_url: str
    duration: Optional[str]
    view_count: Optional[int]
    like_count: Optional[int]
    published_at: datetime
    tags: List[str]
    language: str
    caption_available: bool
    educational_score: float  # 0-1 arası eğitim değeri skoru


class YouTubeService:
    """YouTube API servisi"""

    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY", "")
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.educational_channels = self._load_educational_channels()
        self.session = None
        self.rate_limit_delay = 0.1  # 100ms delay between requests
        self.max_retries = 3

    def _load_educational_channels(self) -> Dict[str, float]:
        """Eğitim kanalları ve güvenilirlik skorları"""
        return {
            # Türkçe eğitim kanalları
            "UCY0pGqP5L7s7d9HuXndvazA": 1.0,  # Khan Academy Türkçe
            "UCzKPRFPpDrqQmz7G8OmRH5Q": 0.9,  # BTK Akademi
            "UC_xsc5nsdVkHscvA0SWxBAw": 0.9,  # Evrim Ağacı
            "UCWzx1P6f2EYls1__9RM3qZw": 0.8,  # Barış Özcan
            "UC2sUP5sX8jXwkfBfRt9qgjg": 0.8,  # TonguçAkademi
            "UCnzWmJVXiLDREXMO5aZgqJA": 0.8,  # Hocalara Geldik
            # İngilizce eğitim kanalları
            "UC8butISFwT-Wl7EV0hUK0BQ": 1.0,  # Khan Academy
            "UCEWpbFLzoYGPfuWUMFPSaoA": 0.9,  # CrashCourse
            "UCsooa4yRKGN_zEE8iknghZA": 0.9,  # TED-Ed
            "UC7IcJI8PUf5Z3zKxnZvTBog": 0.8,  # School of Life
            "UC6nSFiPRc5g8DyT3MB0u": 0.8,  # MinutePhysics
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

    async def search_educational_videos(
        self,
        query: str,
        subject: Optional[str] = None,
        grade_level: Optional[str] = None,
        language: str = "tr",
        max_results: int = 20,
        order: str = "relevance",
    ) -> List[YouTubeVideo]:
        """
        Eğitim videoları ara (Gerçek YouTube API)

        Args:
            query: Arama sorgusu
            subject: Ders/konu
            grade_level: Sınıf seviyesi
            language: Dil kodu
            max_results: Maksimum sonuç
            order: Sıralama (relevance, viewCount, rating, date)

        Returns:
            Video listesi
        """
        try:
            # DEBUG: Log api_key status
            import os
            actual_key = os.getenv("YOUTUBE_API_KEY", "NOT_FOUND")
            logger.info(f"YouTube API Key status: present={bool(self.api_key)}, env_var={actual_key[:10] if actual_key else 'NONE'}...")
            if not self.api_key:
                logger.warning("YouTube API key not found, using fallback")
                return await self._fallback_search(query, max_results)

            # Arama sorgusunu oluştur
            search_query = self._build_search_query(query, subject, grade_level)

            # API çağrısı için parametreler
            params = {
                "part": "snippet",
                "q": search_query,
                "type": "video",
                "maxResults": min(max_results, 50),  # YouTube API limiti
                "order": order,
                "relevanceLanguage": language,
                "key": self.api_key,
            }

            # Eğitim kategorisi filtresi
            if subject:
                params["videoCategoryId"] = "27"  # Education category

            # API çağrısı yap
            logger.info(f"YouTube API call: params={params}")
            search_results = await self._make_api_request("search", params)
            logger.info(f"YouTube API response: has_results={bool(search_results)}, has_items={'items' in (search_results or {})}")
            logger.info(f"YouTube API response keys: {list(search_results.keys()) if search_results else 'None'}")

            if not search_results or "items" not in search_results:
                logger.warning("No search results from YouTube API - using fallback")
                return await self._fallback_search(query, max_results)

            # Video ID'lerini topla
            video_ids = [
                item["id"]["videoId"]
                for item in search_results["items"]
                if item["id"]["kind"] == "youtube#video"
            ]

            if not video_ids:
                return []

            # Video detaylarını al
            videos = await self._get_video_details(video_ids)

            # Eğitim skorlarını hesapla
            for video in videos:
                video.educational_score = self._calculate_educational_score(video)

            # Skora göre sırala
            videos.sort(key=lambda v: v.educational_score, reverse=True)

            logger.info(f"Found {len(videos)} educational videos for '{query}'")
            return videos

        except Exception as e:
            logger.error(f"YouTube search error: {str(e)}")
            return await self._fallback_search(query, max_results)

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

            async with session.get(url, params=params) as response:
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
                        raise Exception("YouTube API quota exceeded")
                    elif error_reason == "keyInvalid":
                        logger.error("Invalid YouTube API key")
                        raise Exception("Invalid YouTube API key")
                    else:
                        logger.error(f"YouTube API error 403: {error_reason}")
                        raise Exception(f"YouTube API access denied: {error_reason}")
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
                        raise Exception("Rate limit exceeded, max retries reached")
                else:
                    logger.error(
                        f"YouTube API error {response.status}: {await response.text()}"
                    )
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

    async def _get_video_details(self, video_ids: List[str]) -> List[YouTubeVideo]:
        """
        Video detaylarını al

        Args:
            video_ids: Video ID listesi

        Returns:
            Video listesi
        """
        try:
            if not video_ids:
                return []

            # Video ID'lerini 50'şer grupla (YouTube API limiti)
            videos = []
            for i in range(0, len(video_ids), 50):
                batch_ids = video_ids[i : i + 50]

                params = {
                    "part": "snippet,statistics,contentDetails",
                    "id": ",".join(batch_ids),
                    "key": self.api_key,
                }

                video_data = await self._make_api_request("videos", params)

                if video_data and "items" in video_data:
                    for item in video_data["items"]:
                        video = self._parse_video_data(item)
                        if video:
                            videos.append(video)

            return videos

        except Exception as e:
            logger.error(f"Error getting video details: {str(e)}")
            return []

    def _parse_video_data(self, item: Dict[str, Any]) -> Optional[YouTubeVideo]:
        """
        YouTube API yanıtından video objesi oluştur

        Args:
            item: YouTube API video item

        Returns:
            YouTubeVideo objesi
        """
        try:
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            content_details = item.get("contentDetails", {})

            # Tarih parse et
            published_at = datetime.fromisoformat(
                snippet.get("publishedAt", "").replace("Z", "+00:00")
            )

            # Thumbnail URL
            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = (
                thumbnails.get("maxres", {}).get("url")
                or thumbnails.get("high", {}).get("url")
                or thumbnails.get("medium", {}).get("url")
                or thumbnails.get("default", {}).get("url")
                or ""
            )

            # Caption availability check
            caption_available = content_details.get("caption", "false") == "true"

            # Tags
            tags = snippet.get("tags", [])

            # Language detection
            language = (
                snippet.get("defaultLanguage")
                or snippet.get("defaultAudioLanguage")
                or "tr"
            )

            # Educational score calculation - safe fallback
            try:
                educational_score = self._calculate_educational_score(item)
            except (AttributeError, TypeError):
                # Fallback if item is a dict and function expects YouTubeVideo
                educational_score = 0.5

            # Safe video_id extraction
            video_id = ""
            if isinstance(item, dict):
                video_id = item.get("id", {}).get("videoId", "") if isinstance(item.get("id"), dict) else str(item.get("id", ""))
            elif isinstance(item, str):
                video_id = item

            return YouTubeVideo(
                video_id=video_id,
                title=snippet.get("title", ""),
                description=snippet.get("description", ""),
                channel_name=snippet.get("channelTitle", ""),
                channel_id=snippet.get("channelId", ""),
                thumbnail_url=thumbnail_url,
                duration=content_details.get("duration"),
                view_count=int(statistics.get("viewCount", 0)),
                like_count=int(statistics.get("likeCount", 0)),
                published_at=published_at,
                tags=tags,
                language=language,
                caption_available=caption_available,
                educational_score=educational_score,
            )

        except Exception as e:
            import traceback
            logger.error(f"Error parsing video data: {str(e)}\nStack: {traceback.format_exc(limit=5)}")
            return None

    def _calculate_educational_score(self, video_item: Dict[str, Any]) -> float:
        """
        Video için eğitim değeri skoru hesapla

        Args:
            video_item: YouTube API video item

        Returns:
            Eğitim skoru (0-1 arası)
        """
        try:
            snippet = video_item.get("snippet", {})
            statistics = video_item.get("statistics", {})
            content_details = video_item.get("contentDetails", {})

            score = 0.0

            # Kanal güvenilirliği
            channel_id = snippet.get("channelId", "")
            if channel_id in self.educational_channels:
                score += self.educational_channels[channel_id] * 0.4
            else:
                score += 0.2  # Bilinmeyen kanal için düşük skor

            # Başlık ve açıklama analizi
            title = snippet.get("title", "").lower()
            description = snippet.get("description", "").lower()

            # Eğitim anahtar kelimeleri
            educational_keywords = [
                "ders",
                "öğren",
                "eğitim",
                "kurs",
                "tutorial",
                "nasıl",
                "anlatım",
                "lesson",
                "learn",
                "education",
                "course",
                "how to",
                "tutorial",
                "matematik",
                "fen",
                "fizik",
                "kimya",
                "biyoloji",
                "tarih",
                "coğrafya",
                "math",
                "science",
                "physics",
                "chemistry",
                "biology",
                "history",
            ]

            keyword_matches = sum(
                1
                for keyword in educational_keywords
                if keyword in title or keyword in description
            )

            if keyword_matches > 0:
                score += min(keyword_matches * 0.05, 0.2)

            # Video süresi (çok kısa veya çok uzun videolar düşük puan)
            duration = content_details.get("duration", "")
            duration_minutes = self._parse_duration_to_minutes(duration)

            if 5 <= duration_minutes <= 60:  # 5-60 dakika ideal
                score += 0.1
            elif 1 <= duration_minutes <= 120:  # 1-120 dakika kabul edilebilir
                score += 0.05

            # View/Like oranı
            view_count = int(statistics.get("viewCount", 0))
            like_count = int(statistics.get("likeCount", 0))

            if view_count > 0 and like_count > 0:
                like_ratio = like_count / view_count
                if like_ratio > 0.01:  # %1'den fazla like oranı
                    score += 0.1
                elif like_ratio > 0.005:  # %0.5'ten fazla
                    score += 0.05

            # Caption availability
            if content_details.get("caption", "false") == "true":
                score += 0.1

            # Tags quality
            tags = snippet.get("tags", [])
            if len(tags) > 3:  # İyi etiketlenmiş
                score += 0.05

            return min(score, 1.0)

        except Exception as e:
            logger.error(f"Error calculating educational score: {str(e)}")
            return 0.5

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

    async def extract_video_metadata(self, video_id: str) -> Dict[str, Any]:
        """
        Video için detaylı metadata çıkar

        Args:
            video_id: YouTube video ID

        Returns:
            Detaylı metadata dict
        """
        try:
            params = {
                "part": "snippet,statistics,contentDetails,status,topicDetails",
                "id": video_id,
                "key": self.api_key,
            }

            video_data = await self._make_api_request("videos", params)

            if not video_data or "items" not in video_data or not video_data["items"]:
                return {}

            item = video_data["items"][0]
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            content_details = item.get("contentDetails", {})
            status = item.get("status", {})
            topic_details = item.get("topicDetails", {})

            # Comprehensive metadata extraction
            metadata = {
                # Basic info
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "channel_name": snippet.get("channelTitle", ""),
                "channel_id": snippet.get("channelId", ""),
                "published_at": snippet.get("publishedAt", ""),
                # Content details
                "duration": content_details.get("duration", ""),
                "duration_minutes": self._parse_duration_to_minutes(
                    content_details.get("duration", "")
                ),
                "definition": content_details.get("definition", ""),
                "caption_available": content_details.get("caption", "false") == "true",
                "licensed_content": content_details.get("licensedContent", False),
                # Statistics
                "view_count": int(statistics.get("viewCount", 0)),
                "like_count": int(statistics.get("likeCount", 0)),
                "comment_count": int(statistics.get("commentCount", 0)),
                # Status
                "upload_status": status.get("uploadStatus", ""),
                "privacy_status": status.get("privacyStatus", ""),
                "license": status.get("license", ""),
                "embeddable": status.get("embeddable", True),
                "public_stats_viewable": status.get("publicStatsViewable", True),
                # Topics (if available)
                "topic_categories": topic_details.get("topicCategories", []),
                "relevant_topic_ids": topic_details.get("relevantTopicIds", []),
                # Language and localization
                "default_language": snippet.get("defaultLanguage", ""),
                "default_audio_language": snippet.get("defaultAudioLanguage", ""),
                # Thumbnails
                "thumbnails": snippet.get("thumbnails", {}),
                # Tags and categorization
                "tags": snippet.get("tags", []),
                "category_id": snippet.get("categoryId", ""),
                # Educational scoring
                "educational_score": self._calculate_educational_score(item),
                # Accessibility features
                "accessibility_features": self._extract_accessibility_features(item),
                # Quality indicators
                "quality_indicators": self._extract_quality_indicators(item),
                # Difficulty estimation
                "estimated_difficulty": self._estimate_difficulty_level(item),
                # Content classification
                "content_classification": self._classify_content_type(item),
            }

            return metadata

        except Exception as e:
            logger.error(f"Error extracting video metadata for {video_id}: {str(e)}")
            return {}

    def _extract_accessibility_features(self, video_item: Dict[str, Any]) -> List[str]:
        """Video erişilebilirlik özelliklerini çıkar"""
        features = []

        content_details = video_item.get("contentDetails", {})
        snippet = video_item.get("snippet", {})

        # Caption availability
        if content_details.get("caption", "false") == "true":
            features.append("captions_available")
            features.append("transcript_available")

        # High definition
        if content_details.get("definition", "") == "hd":
            features.append("high_definition")

        # Multiple language support (if tags indicate)
        tags = snippet.get("tags", [])
        if any("subtitle" in tag.lower() or "altyazı" in tag.lower() for tag in tags):
            features.append("multilingual_subtitles")

        return features

    def _extract_quality_indicators(self, video_item: Dict[str, Any]) -> Dict[str, Any]:
        """Video kalite göstergelerini çıkar"""
        snippet = video_item.get("snippet", {})
        statistics = video_item.get("statistics", {})
        content_details = video_item.get("contentDetails", {})

        view_count = int(statistics.get("viewCount", 0))
        like_count = int(statistics.get("likeCount", 0))
        comment_count = int(statistics.get("commentCount", 0))

        indicators = {
            "view_count": view_count,
            "engagement_rate": (like_count + comment_count) / max(view_count, 1),
            "like_ratio": like_count / max(view_count, 1),
            "has_description": len(snippet.get("description", "")) > 100,
            "well_tagged": len(snippet.get("tags", [])) >= 5,
            "hd_quality": content_details.get("definition", "") == "hd",
            "recent_upload": self._is_recent_upload(snippet.get("publishedAt", "")),
            "channel_verified": snippet.get("channelId", "")
            in self.educational_channels,
        }

        return indicators

    def _estimate_difficulty_level(self, video_item: Dict[str, Any]) -> str:
        """Video zorluk seviyesini tahmin et"""
        snippet = video_item.get("snippet", {})
        title = snippet.get("title", "").lower()
        description = snippet.get("description", "").lower()
        tags = [tag.lower() for tag in snippet.get("tags", [])]

        # Zorluk belirten anahtar kelimeler
        beginner_keywords = [
            "temel",
            "başlangıç",
            "giriş",
            "basic",
            "intro",
            "beginner",
            "101",
        ]
        advanced_keywords = [
            "ileri",
            "uzman",
            "advanced",
            "expert",
            "master",
            "professional",
        ]

        text_content = f"{title} {description} {' '.join(tags)}"

        beginner_count = sum(
            1 for keyword in beginner_keywords if keyword in text_content
        )
        advanced_count = sum(
            1 for keyword in advanced_keywords if keyword in text_content
        )

        if beginner_count > advanced_count:
            return "beginner"
        elif advanced_count > beginner_count:
            return "advanced"
        else:
            return "intermediate"

    def _classify_content_type(self, video_item: Dict[str, Any]) -> str:
        """Video içerik türünü sınıflandır"""
        snippet = video_item.get("snippet", {})
        title = snippet.get("title", "").lower()
        description = snippet.get("description", "").lower()

        # İçerik türü anahtar kelimeleri
        if any(
            keyword in title or keyword in description
            for keyword in ["ders", "lesson", "lecture", "anlatım"]
        ):
            return "lecture"
        elif any(
            keyword in title or keyword in description
            for keyword in ["tutorial", "nasıl", "how to", "adım"]
        ):
            return "tutorial"
        elif any(
            keyword in title or keyword in description
            for keyword in ["soru", "çözüm", "problem", "solution"]
        ):
            return "problem_solving"
        elif any(
            keyword in title or keyword in description
            for keyword in ["deney", "experiment", "pratik", "practice"]
        ):
            return "practical"
        elif any(
            keyword in title or keyword in description
            for keyword in ["özet", "summary", "review", "tekrar"]
        ):
            return "review"
        else:
            return "general_educational"

    def _is_recent_upload(self, published_at: str) -> bool:
        """Video son 2 yılda yüklenmiş mi?"""
        try:
            if not published_at:
                return False

            pub_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            days_old = (datetime.now() - pub_date.replace(tzinfo=None)).days

            return days_old <= 730  # 2 yıl

        except Exception:
            return False

            video = YouTubeVideo(
                video_id=item["id"],
                title=snippet.get("title", ""),
                description=snippet.get("description", ""),
                channel_name=snippet.get("channelTitle", ""),
                channel_id=snippet.get("channelId", ""),
                thumbnail_url=thumbnail_url,
                duration=content_details.get("duration"),
                view_count=int(statistics.get("viewCount", 0)),
                like_count=int(statistics.get("likeCount", 0)),
                published_at=published_at,
                tags=tags,
                language=language,
                caption_available=caption_available,
                educational_score=0.0,  # Will be calculated later
            )

            return video

        except Exception as e:
            logger.error(f"Error parsing video data: {str(e)}")
            return None

    async def _fallback_search(
        self, query: str, max_results: int
    ) -> List[YouTubeVideo]:
        """
        API olmadığında fallback arama

        Args:
            query: Arama sorgusu
            max_results: Maksimum sonuç

        Returns:
            Simüle edilmiş video listesi
        """
        logger.info(f"Using fallback search for: {query}")

        # Simüle edilmiş videolar
        fallback_videos = [
            YouTubeVideo(
                video_id="fallback_001",
                title=f"{query} - Konu Anlatımı",
                description=f"{query} konusunda detaylı açıklama ve örnekler",
                channel_name="Eğitim Kanalı",
                channel_id="UC_education_channel",
                thumbnail_url="https://img.youtube.com/vi/fallback_001/maxresdefault.jpg",
                duration="PT15M30S",
                view_count=25000,
                like_count=1200,
                published_at=datetime.now(),
                tags=[query.lower(), "eğitim", "ders"],
                language="tr",
                caption_available=True,
                educational_score=0.8,
            ),
            YouTubeVideo(
                video_id="fallback_002",
                title=f"{query} - Soru Çözümü",
                description=f"{query} konusunda örnek sorular ve çözümleri",
                channel_name="Matematik Kanalı",
                channel_id="UC_math_channel",
                thumbnail_url="https://img.youtube.com/vi/fallback_002/maxresdefault.jpg",
                duration="PT20M45S",
                view_count=18000,
                like_count=950,
                published_at=datetime.now(),
                tags=[query.lower(), "soru", "çözüm"],
                language="tr",
                caption_available=True,
                educational_score=0.75,
            ),
            YouTubeVideo(
                video_id="fallback_003",
                title=f"{query} - Pratik Uygulamalar",
                description=f"{query} konusunda pratik örnekler ve uygulamalar",
                channel_name="Fen Kanalı",
                channel_id="UC_science_channel",
                thumbnail_url="https://img.youtube.com/vi/fallback_003/maxresdefault.jpg",
                duration="PT12M20S",
                view_count=32000,
                like_count=1800,
                published_at=datetime.now(),
                tags=[query.lower(), "pratik", "uygulama"],
                language="tr",
                caption_available=False,
                educational_score=0.7,
            ),
        ]

        return fallback_videos[:max_results]

    def _build_search_query(
        self, query: str, subject: Optional[str], grade_level: Optional[str]
    ) -> str:
        """Arama sorgusunu oluştur"""
        parts = [query]

        if subject:
            parts.append(subject)

        if grade_level:
            # Sınıf seviyesini Türkçe'ye çevir
            grade_mapping = {
                "8": "8. sınıf LGS",
                "9": "9. sınıf",
                "10": "10. sınıf",
                "11": "11. sınıf",
                "12": "12. sınıf TYT AYT YKS",
            }
            grade_text = grade_mapping.get(grade_level, grade_level)
            parts.append(grade_text)

        # Eğitim anahtar kelimeleri ekle
        parts.extend(["ders", "konu anlatımı", "eğitim"])

        return " ".join(parts)

    async def _simulate_api_call(self, params: Dict[str, Any]) -> List[YouTubeVideo]:
        """API çağrısını simüle et (gerçek uygulamada YouTube API kullanılacak)"""
        # Örnek videolar
        sample_videos = [
            YouTubeVideo(
                video_id="abc123",
                title="Matematik - Denklemler Konu Anlatımı",
                description="8. sınıf matematik denklemler konusu detaylı anlatım",
                channel_name="Tonguç Akademi",
                channel_id="UC2sUP5sX8jXwkfBfRt9qgjg",
                thumbnail_url="https://i.ytimg.com/vi/abc123/maxresdefault.jpg",
                duration="PT15M30S",
                view_count=50000,
                like_count=2000,
                published_at=datetime.now(),
                tags=["matematik", "denklem", "8.sınıf", "LGS"],
                language="tr",
                caption_available=True,
                educational_score=0,
            ),
            YouTubeVideo(
                video_id="def456",
                title="Fen Bilimleri - Hücre Bölünmesi",
                description="Mitoz ve mayoz bölünme konu anlatımı",
                channel_name="Khan Academy Türkçe",
                channel_id="UCY0pGqP5L7s7d9HuXndvazA",
                thumbnail_url="https://i.ytimg.com/vi/def456/maxresdefault.jpg",
                duration="PT20M15S",
                view_count=75000,
                like_count=3500,
                published_at=datetime.now(),
                tags=["fen", "biyoloji", "hücre", "mitoz", "mayoz"],
                language="tr",
                caption_available=True,
                educational_score=0,
            ),
            YouTubeVideo(
                video_id="ghi789",
                title="Türkçe - Paragraf Soruları Çözüm Teknikleri",
                description="YKS TYT paragraf soru çözüm stratejileri",
                channel_name="Hocalara Geldik",
                channel_id="UCnzWmJVXiLDREXMO5aZgqJA",
                thumbnail_url="https://i.ytimg.com/vi/ghi789/maxresdefault.jpg",
                duration="PT25M45S",
                view_count=100000,
                like_count=5000,
                published_at=datetime.now(),
                tags=["türkçe", "paragraf", "YKS", "TYT"],
                language="tr",
                caption_available=True,
                educational_score=0,
            ),
        ]

        # Sorguya göre filtrele
        query = params.get("q", "").lower()
        filtered_videos = []
        for video in sample_videos:
            if any(
                word in video.title.lower() or word in video.description.lower()
                for word in query.split()
            ):
                filtered_videos.append(video)

        return filtered_videos[: params.get("maxResults", 10)]

    def _calculate_educational_score(self, video: YouTubeVideo) -> float:
        """
        Videonun eğitim değeri skorunu hesapla (Geliştirilmiş algoritma)

        Args:
            video: YouTube videosu

        Returns:
            Eğitim skoru (0-1)
        """
        score = 0.0

        # 1. Kanal güvenilirliği (30% ağırlık)
        channel_score = self.educational_channels.get(video.channel_id, 0.5)
        score += channel_score * 0.3

        # 2. Başlık ve açıklama analizi (25% ağırlık)
        educational_keywords = {
            # Türkçe eğitim kelimeleri
            "ders": 1.0,
            "konu": 1.0,
            "anlatım": 1.0,
            "öğren": 1.0,
            "eğitim": 1.0,
            "üniversite": 0.9,
            "lise": 0.9,
            "sınıf": 0.9,
            "okul": 0.8,
            "LGS": 1.0,
            "YKS": 1.0,
            "TYT": 1.0,
            "AYT": 1.0,
            "KPSS": 0.9,
            "matematik": 1.0,
            "fen": 1.0,
            "fizik": 1.0,
            "kimya": 1.0,
            "biyoloji": 1.0,
            "tarih": 1.0,
            "coğrafya": 1.0,
            "türkçe": 1.0,
            "edebiyat": 1.0,
            "geometri": 1.0,
            "cebir": 1.0,
            "analiz": 1.0,
            "trigonometri": 1.0,
            "soru": 0.8,
            "çözüm": 0.8,
            "örnek": 0.7,
            "test": 0.7,
            "deneme": 0.7,
            "açıklama": 0.6,
            "rehber": 0.6,
            "tutorial": 0.6,
            "nasıl": 0.5,
            # İngilizce eğitim kelimeleri
            "education": 1.0,
            "tutorial": 0.8,
            "lesson": 1.0,
            "course": 0.9,
            "learn": 0.8,
            "study": 0.7,
            "academic": 0.8,
            "university": 0.9,
            "school": 0.8,
            "teaching": 0.9,
            "explanation": 0.7,
        }

        title_lower = video.title.lower()
        desc_lower = video.description.lower()

        keyword_score = 0.0
        for keyword, weight in educational_keywords.items():
            if keyword in title_lower:
                keyword_score += weight * 0.7  # Başlıkta daha önemli
            if keyword in desc_lower:
                keyword_score += weight * 0.3  # Açıklamada daha az önemli

        keyword_score = min(keyword_score / 3, 1.0)  # Normalize et
        score += keyword_score * 0.25

        # 3. Video süresi optimizasyonu (15% ağırlık)
        duration_score = 0.0
        if video.duration:
            try:
                duration_minutes = self._parse_duration_to_minutes(video.duration)
                if 8 <= duration_minutes <= 25:  # İdeal süre
                    duration_score = 1.0
                elif 5 <= duration_minutes <= 45:  # Kabul edilebilir süre
                    duration_score = 0.7
                elif 3 <= duration_minutes <= 60:  # Sınır süre
                    duration_score = 0.4
                else:
                    duration_score = 0.2  # Çok kısa veya çok uzun
            except (ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Duration parsing failed: {e}")
                duration_score = 0.5  # Parse edilemezse orta değer

        score += duration_score * 0.15

        # 4. Etkileşim kalitesi (10% ağırlık)
        engagement_score = 0.0
        if video.view_count and video.like_count and video.view_count > 0:
            like_ratio = video.like_count / video.view_count
            # Eğitim videoları için normal like oranı %1-5 arası
            if like_ratio >= 0.03:  # %3 ve üzeri çok iyi
                engagement_score = 1.0
            elif like_ratio >= 0.015:  # %1.5-3 arası iyi
                engagement_score = 0.8
            elif like_ratio >= 0.005:  # %0.5-1.5 arası orta
                engagement_score = 0.6
            else:
                engagement_score = 0.3  # Düşük etkileşim

        score += engagement_score * 0.1

        # 5. Altyazı ve erişilebilirlik (10% ağırlık)
        accessibility_score = 0.0
        if video.caption_available:
            accessibility_score += 0.7

        # Başlıkta açıklayıcı kelimeler varsa
        explanatory_words = [
            "nasıl",
            "nedir",
            "açıklama",
            "anlatım",
            "rehber",
            "tutorial",
        ]
        if any(word in title_lower for word in explanatory_words):
            accessibility_score += 0.3

        accessibility_score = min(accessibility_score, 1.0)
        score += accessibility_score * 0.1

        # 6. İçerik kalitesi göstergeleri (10% ağırlık)
        quality_score = 0.0

        # Başlık kalitesi
        if len(video.title) >= 20:  # Yeterince açıklayıcı başlık
            quality_score += 0.3

        # Açıklama kalitesi
        if len(video.description) >= 100:  # Detaylı açıklama
            quality_score += 0.3

        # Tag kalitesi
        if len(video.tags) >= 3:  # Yeterli tag
            quality_score += 0.2

        # Kanal adında eğitim göstergesi
        channel_name_lower = video.channel_name.lower()
        educational_channel_indicators = [
            "akademi",
            "eğitim",
            "ders",
            "okul",
            "öğretmen",
            "hoca",
        ]
        if any(
            indicator in channel_name_lower
            for indicator in educational_channel_indicators
        ):
            quality_score += 0.2

        quality_score = min(quality_score, 1.0)
        score += quality_score * 0.1

        # Final score normalization
        final_score = min(max(score, 0.0), 1.0)

        return final_score

    def _parse_duration_to_minutes(self, duration: str) -> int:
        """
        ISO 8601 duration formatını dakikaya çevir

        Args:
            duration: PT15M30S formatında süre

        Returns:
            Dakika cinsinden süre
        """
        try:
            # PT15M30S -> 15.5 dakika
            duration = duration.replace("PT", "")

            hours = 0
            minutes = 0
            seconds = 0

            if "H" in duration:
                hours = int(duration.split("H")[0])
                duration = duration.split("H")[1]

            if "M" in duration:
                minutes = int(duration.split("M")[0])
                duration = duration.split("M")[1]

            if "S" in duration:
                seconds = int(duration.replace("S", ""))

            total_minutes = hours * 60 + minutes + seconds / 60
            return int(total_minutes)

        except (ValueError, IndexError, AttributeError) as e:
            logger.debug(f"Duration parsing failed: {e}")
            return 15  # Default 15 dakika

    async def get_video_details_by_id(self, video_id: str) -> Optional[YouTubeVideo]:
        """
        Video ID'ye göre video detaylarını getir

        Args:
            video_id: YouTube video ID

        Returns:
            Video detayları
        """
        try:
            if not self.api_key:
                return None

            params = {
                "part": "snippet,statistics,contentDetails",
                "id": video_id,
                "key": self.api_key,
            }

            video_data = await self._make_api_request("videos", params)

            if video_data and "items" in video_data and len(video_data["items"]) > 0:
                video = self._parse_video_data(video_data["items"][0])
                if video:
                    video.educational_score = self._calculate_educational_score(video)
                return video

            return None

        except Exception as e:
            logger.error(f"Get video details error: {str(e)}")
            return None

    async def get_video_captions(
        self, video_id: str, language: str = "tr"
    ) -> Optional[str]:
        """
        Video altyazılarını getir

        Args:
            video_id: YouTube video ID
            language: Dil kodu

        Returns:
            Altyazı metni
        """
        try:
            if not self.api_key:
                return None

            # Önce caption listesini al
            params = {"part": "snippet", "videoId": video_id, "key": self.api_key}

            captions_data = await self._make_api_request("captions", params)

            if not captions_data or "items" not in captions_data:
                return None

            # İstenen dilde caption bul
            caption_id = None
            for item in captions_data["items"]:
                if item["snippet"]["language"] == language:
                    caption_id = item["id"]
                    break

            # Eğer istenen dil yoksa İngilizce dene
            if not caption_id:
                for item in captions_data["items"]:
                    if item["snippet"]["language"] == "en":
                        caption_id = item["id"]
                        break

            # Eğer hiç caption yoksa
            if not caption_id:
                return None

            # Caption içeriğini al (Bu özel izin gerektirir)
            # Şimdilik None döndür, gerçek uygulamada OAuth gerekli
            logger.info(
                f"Caption found for video {video_id} but download requires OAuth"
            )
            return None

        except Exception as e:
            logger.error(f"Get video captions error: {str(e)}")
            return None

    async def search_by_channel(
        self, channel_id: str, query: Optional[str] = None, max_results: int = 20
    ) -> List[YouTubeVideo]:
        """
        Belirli bir kanalda arama yap

        Args:
            channel_id: YouTube kanal ID
            query: Arama sorgusu (opsiyonel)
            max_results: Maksimum sonuç

        Returns:
            Video listesi
        """
        try:
            if not self.api_key:
                return []

            params = {
                "part": "snippet",
                "channelId": channel_id,
                "type": "video",
                "maxResults": min(max_results, 50),
                "order": "relevance",
                "key": self.api_key,
            }

            if query:
                params["q"] = query

            search_results = await self._make_api_request("search", params)

            if not search_results or "items" not in search_results:
                return []

            # Video ID'lerini topla
            video_ids = [
                item["id"]["videoId"]
                for item in search_results["items"]
                if item["id"]["kind"] == "youtube#video"
            ]

            if not video_ids:
                return []

            # Video detaylarını al
            videos = await self._get_video_details(video_ids)

            # Eğitim skorlarını hesapla
            for video in videos:
                video.educational_score = self._calculate_educational_score(video)

            return videos

        except Exception as e:
            logger.error(f"Search by channel error: {str(e)}")
            return []

    async def get_channel_videos(
        self, channel_id: str, max_results: int = 50
    ) -> List[YouTubeVideo]:
        """
        Kanal videolarını getir

        Args:
            channel_id: YouTube kanal ID
            max_results: Maksimum video sayısı

        Returns:
            Video listesi
        """
        try:
            # Eğitim kanalı mı kontrol et
            if channel_id not in self.educational_channels:
                logger.warning(
                    f"Channel {channel_id} is not in educational channels list"
                )

            # API çağrısı (simüle edilmiş)
            return await self._simulate_api_call(
                {"channelId": channel_id, "maxResults": max_results}
            )

        except Exception as e:
            logger.error(f"Get channel videos error: {str(e)}")
            return []

    async def get_playlists(
        self, channel_id: Optional[str] = None, query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Oynatma listelerini getir

        Args:
            channel_id: Kanal ID (opsiyonel)
            query: Arama sorgusu (opsiyonel)

        Returns:
            Playlist listesi
        """
        try:
            # Örnek playlist'ler
            playlists = [
                {
                    "playlist_id": "PLxxx1",
                    "title": "8. Sınıf Matematik Konu Anlatımları",
                    "description": "LGS matematik konuları",
                    "video_count": 25,
                    "channel_name": "Tonguç Akademi",
                },
                {
                    "playlist_id": "PLxxx2",
                    "title": "TYT Fizik Soru Çözümleri",
                    "description": "TYT fizik soru bankası çözümleri",
                    "video_count": 40,
                    "channel_name": "Hocalara Geldik",
                },
            ]

            if query:
                # Sorguya göre filtrele
                playlists = [
                    p for p in playlists if query.lower() in p["title"].lower()
                ]

            return playlists

        except Exception as e:
            logger.error(f"Get playlists error: {str(e)}")
            return []

    def format_duration(self, duration: str) -> str:
        """
        ISO 8601 süre formatını okunabilir formata çevir

        Args:
            duration: PT15M30S formatında süre

        Returns:
            "15:30" formatında süre
        """
        try:
            # PT15M30S -> 15:30
            duration = duration.replace("PT", "")

            hours = 0
            minutes = 0
            seconds = 0

            if "H" in duration:
                hours = int(duration.split("H")[0])
                duration = duration.split("H")[1]

            if "M" in duration:
                minutes = int(duration.split("M")[0])
                duration = duration.split("M")[1]

            if "S" in duration:
                seconds = int(duration.replace("S", ""))

            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes}:{seconds:02d}"

        except (ValueError, IndexError, AttributeError) as e:
            logger.debug(f"Duration formatting failed: {e}")
            return duration

    async def get_trending_educational(
        self, region: str = "TR", category: str = "Education"
    ) -> List[YouTubeVideo]:
        """
        Trend olan eğitim videolarını getir

        Args:
            region: Bölge kodu
            category: Kategori

        Returns:
            Trend video listesi
        """
        try:
            params = {
                "part": "snippet,statistics",
                "chart": "mostPopular",
                "regionCode": region,
                "videoCategoryId": "27",  # Education
                "maxResults": 20,
            }

            return await self._simulate_api_call(params)

        except Exception as e:
            logger.error(f"Get trending error: {str(e)}")
            return []


# Singleton instance
youtube_service = YouTubeService()
