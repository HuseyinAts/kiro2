"""YouTube Data API v3 search strategy for learning path recommendations.

This module provides integration with YouTube Data API to find educational
videos for personalized learning paths, with specific support for Turkish content.

Teknofest 2025 - Eğitim Eylemci Projesi
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import aiohttp

from agents.learning_path.config import get_learning_path_config
from agents.learning_path.strategies.resource_search import ResourceSearchStrategy

if TYPE_CHECKING:
    from agents.learning_path.models import KnowledgeLevel, LearningResource

logger = logging.getLogger(__name__)


class YouTubeSearchStrategy(ResourceSearchStrategy):
    """YouTube Data API v3 search strategy.

    This strategy searches YouTube for educational videos and normalizes
    results to LearningResource format. Supports Turkish content filtering,
    duration parsing, and difficulty estimation based on video metadata.

    Attributes:
        api_key: YouTube Data API v3 key
        base_url: YouTube API base URL
        config: Learning path configuration
    """

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize YouTube search strategy.

        Args:
            api_key: Optional YouTube API key override.
                     If not provided, reads from config/environment.
        """
        self.config = get_learning_path_config()
        self.api_key = api_key or self.config.YOUTUBE_API_KEY
        self.base_url = "https://www.googleapis.com/youtube/v3"

        if not self.api_key:
            logger.warning("YouTube API key not configured. Search will fail.")

    async def search(self, query: str, **filters: Any) -> list[LearningResource]:
        """Search YouTube for educational videos.

        Args:
            query: Search query string (e.g., "türev kavramı").
            **filters: Optional filters:
                - subject (str): Subject filter (e.g., "matematik")
                - difficulty_range (tuple): Min and max difficulty values
                - limit (int): Maximum number of results (default: 10)
                - language (str): Content language (default: "tr")

        Returns:
            List of learning resources from YouTube.

        Raises:
            None: Returns empty list on error.
        """
        try:
            # Validate API key
            if not self.api_key:
                logger.warning("YouTube API key not configured")
                return []

            # Extract filters
            subject = filters.get("subject")
            difficulty = filters.get("difficulty")
            limit = filters.get("limit", 10)
            language = filters.get("language", "tr")

            # Build optimized search query
            search_query = self._build_search_query(query, subject, difficulty)

            # Reuse one aiohttp session for both API calls (30-50% latency reduction)
            async with aiohttp.ClientSession() as session:
                # Search for video IDs
                video_ids = await self._search_videos(
                    search_query, limit, language, session=session
                )

                if not video_ids:
                    logger.info(f"No YouTube results for query: {search_query}")
                    return []

                # Get detailed video information
                videos = await self._get_video_details(video_ids, session=session)

            # Convert to LearningResource
            resources = []
            for video in videos:
                resource = self.normalize_result(video)
                if resource:
                    resources.append(resource)

            # Apply common filters (difficulty, etc.)
            filtered = self.apply_common_filters(resources, **filters)

            return filtered[:limit]

        except Exception as e:
            logger.warning(f"YouTube search failed: {e}")
            return []

    def get_platform_name(self) -> str:
        """Get platform identifier.

        Returns:
            Platform name string.
        """
        return "youtube"

    def normalize_result(self, raw_result: dict[str, Any]) -> LearningResource | None:
        """Convert YouTube API response to LearningResource.

        Args:
            raw_result: Raw YouTube API video details response.
                       Expected to have 'snippet' and 'contentDetails' keys.

        Returns:
            Normalized LearningResource or None if conversion fails.
        """
        try:
            from agents.learning_path.models import LearningResource
            from agents.learning_path.utils.duration_parser import (
                parse_iso8601_duration,
            )

            snippet = raw_result.get("snippet", {})
            content_details = raw_result.get("contentDetails", {})

            video_id = raw_result.get("id", "")
            if not video_id:
                return None

            title = snippet.get("title", "")
            description = snippet.get("description", "")[:500]

            # Parse ISO 8601 duration (e.g., PT10M30S)
            duration_str = content_details.get("duration", "PT10M")
            duration_minutes = parse_iso8601_duration(duration_str)

            # Estimate difficulty from title and description
            difficulty_level = self._estimate_difficulty(title, description)

            # Extract topics (tags)
            tags = self._extract_topics(title, description)

            # Get thumbnail URL (highest quality available)
            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = (
                thumbnails.get("maxres", {}).get("url", "")
                or thumbnails.get("high", {}).get("url", "")
                or thumbnails.get("medium", {}).get("url", "")
            )

            return LearningResource(
                resource_id=f"youtube-{video_id}",
                title=title,
                description=description,
                url=f"https://www.youtube.com/watch?v={video_id}",
                source="youtube",
                resource_type="video",
                difficulty_level=difficulty_level,
                estimated_time=duration_minutes,
                language="tr",
                tags=tags,
                rating=None,
                metadata={
                    "channel": snippet.get("channelTitle", ""),
                    "channel_id": snippet.get("channelId", ""),
                    "thumbnail": thumbnail_url,
                    "published_at": snippet.get("publishedAt", ""),
                    "view_count": int(
                        raw_result.get("statistics", {}).get("viewCount", 0) or 0
                    ),
                    "like_count": int(
                        raw_result.get("statistics", {}).get("likeCount", 0) or 0
                    ),
                    "definition": content_details.get("definition", "sd"),
                },
            )
        except Exception as e:
            logger.warning(f"Failed to normalize YouTube result: {e}")
            return None

    def _build_search_query(
        self, query: str, subject: str | None, difficulty: str | None = None
    ) -> str:
        """Build optimized Turkish educational search query.

        Args:
            query: Base search query.
            subject: Optional subject filter.
            difficulty: Optional difficulty level (başlangıç/orta/ileri).

        Returns:
            Optimized search query string.
        """
        parts = [query]
        # Avoid duplicating subject if already in query
        if subject and subject.lower() not in query.lower():
            parts.append(subject)

        # Add difficulty-appropriate Turkish terms
        if difficulty:
            diff_terms = {
                "başlangıç": "temel giriş seviye",
                "kolay": "temel giriş seviye",
                "orta": "konu anlatımı",
                "zor": "ileri seviye detaylı",
                "ileri": "ileri seviye detaylı çözüm",
            }
            parts.append(diff_terms.get(difficulty.lower(), "konu anlatımı"))
        else:
            parts.append("konu anlatımı")
        return " ".join(parts)

    async def _search_videos(
        self,
        query: str,
        limit: int,
        language: str = "tr",
        session: aiohttp.ClientSession | None = None,
    ) -> list[str]:
        """Search for video IDs using YouTube search endpoint.

        Args:
            query: Search query string.
            limit: Maximum number of video IDs to return.
            language: Content language (default: "tr").
            session: Optional shared aiohttp session for connection reuse.

        Returns:
            List of video IDs.
        """
        try:
            params = {
                "part": "id",
                "q": query,
                "type": "video",
                "videoDuration": "medium",  # 4-20 minutes
                "relevanceLanguage": language,
                "maxResults": str(min(limit, 50)),
                "key": self.api_key,
                "order": "relevance",
                "safeSearch": "strict",
                "fields": "items(id(videoId))",
            }

            async def _do_search(s: aiohttp.ClientSession) -> list[str]:
                async with s.get(
                    f"{self.base_url}/search",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.config.SEARCH_TIMEOUT),
                ) as resp:
                    if resp.status == 403:
                        logger.error("YouTube API quota exceeded")
                        return []
                    if resp.status != 200:
                        logger.warning(
                            f"YouTube search failed with status {resp.status}"
                        )
                        return []
                    data = await resp.json()
                    items = data.get("items", [])
                    return [item["id"]["videoId"] for item in items if "id" in item]

            if session:
                return await _do_search(session)
            async with aiohttp.ClientSession() as s:
                return await _do_search(s)

        except aiohttp.ClientError as e:
            logger.warning(f"YouTube search network error: {e}")
            return []
        except Exception as e:
            logger.warning(f"YouTube search unexpected error: {e}")
            return []

    async def _get_video_details(
        self,
        video_ids: list[str],
        session: aiohttp.ClientSession | None = None,
    ) -> list[dict]:
        """Get detailed information for video IDs.

        This includes contentDetails (duration), statistics (views), etc.

        Args:
            video_ids: List of YouTube video IDs.
            session: Optional shared aiohttp session for connection reuse.

        Returns:
            List of video detail dictionaries.
        """
        if not video_ids:
            return []

        try:
            params = {
                "part": "snippet,contentDetails,statistics",
                "id": ",".join(video_ids),
                "key": self.api_key,
                "fields": (
                    "items(id,"
                    "snippet(title,description,channelTitle,channelId,"
                    "publishedAt,thumbnails),"
                    "contentDetails(duration,definition),"
                    "statistics(viewCount,likeCount))"
                ),
            }

            async def _do_fetch(s: aiohttp.ClientSession) -> list[dict]:
                async with s.get(
                    f"{self.base_url}/videos",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.config.SEARCH_TIMEOUT),
                ) as resp:
                    if resp.status != 200:
                        logger.warning(
                            f"YouTube video details failed with status {resp.status}"
                        )
                        return []
                    data = await resp.json()
                    return data.get("items", [])

            if session:
                return await _do_fetch(session)
            async with aiohttp.ClientSession() as s:
                return await _do_fetch(s)

        except aiohttp.ClientError as e:
            logger.warning(f"YouTube video details network error: {e}")
            return []
        except Exception as e:
            logger.warning(f"YouTube video details unexpected error: {e}")
            return []

    def _estimate_difficulty(self, title: str, description: str) -> KnowledgeLevel:
        """Estimate difficulty from video title and description.

        Uses Turkish educational keywords to classify content difficulty.

        Args:
            title: Video title.
            description: Video description.

        Returns:
            KnowledgeLevel enum value.
        """
        from agents.learning_path.models import KnowledgeLevel

        text = (title + " " + description).lower()

        # Turkish difficulty indicators
        beginner_keywords = [
            "temel",
            "başlangıç",
            "giriş",
            "kolay",
            "basit",
            "ilkokul",
            "ortaokul",
            "5. sınıf",
            "6. sınıf",
            "7. sınıf",
            "8. sınıf",
        ]

        advanced_keywords = [
            "ileri",
            "zor",
            "detaylı",
            "kapsamlı",
            "profesyonel",
            "üniversite",
            "yüksek lisans",
            "yks",
            "ayt",
            "matematik analiz",
        ]

        intermediate_keywords = [
            "lise",
            "9. sınıf",
            "10. sınıf",
            "11. sınıf",
            "12. sınıf",
            "tyt",
        ]

        elementary_keywords = ["8. sınıf", "ortaokul son", "lgs"]

        # Count keyword occurrences
        beginner_count = sum(1 for kw in beginner_keywords if kw in text)
        elementary_count = sum(1 for kw in elementary_keywords if kw in text)
        advanced_count = sum(1 for kw in advanced_keywords if kw in text)
        intermediate_count = sum(1 for kw in intermediate_keywords if kw in text)

        # Determine difficulty level
        if beginner_count > max(elementary_count, advanced_count, intermediate_count):
            return KnowledgeLevel.BEGINNER
        if elementary_count > max(beginner_count, advanced_count, intermediate_count):
            return KnowledgeLevel.ELEMENTARY
        if advanced_count > max(beginner_count, elementary_count, intermediate_count):
            return KnowledgeLevel.ADVANCED
        if intermediate_count > 0:
            return KnowledgeLevel.INTERMEDIATE

        return KnowledgeLevel.INTERMEDIATE  # Default: intermediate

    def _extract_topics(self, title: str, description: str) -> list[str]:
        """Extract subject topics from title and description.

        Args:
            title: Video title.
            description: Video description.

        Returns:
            List of extracted topics (max 5).
        """
        text = (title + " " + description).lower()
        topics = []

        # YKS/TYT/AYT subject keywords
        subject_keywords = {
            "Matematik": ["matematik", "geometri", "trigonometri", "türev", "integral"],
            "Fizik": ["fizik", "hareket", "kuvvet", "enerji", "elektrik"],
            "Kimya": ["kimya", "atom", "mol", "reaksiyon", "asit"],
            "Biyoloji": ["biyoloji", "hücre", "dna", "ekosistem", "genetik"],
            "Türkçe": ["türkçe", "dil bilgisi", "sözcük", "cümle", "anlatım"],
            "Edebiyat": ["edebiyat", "şiir", "roman", "hikaye", "edebi"],
            "Tarih": ["tarih", "osmanlı", "cumhuriyet", "savaş", "medeniyet"],
            "Coğrafya": ["coğrafya", "iklim", "nüfus", "ekonomi", "harita"],
            "Felsefe": ["felsefe", "mantık", "düşünce", "bilgi", "varlık"],
            "Din Kültürü": ["din", "islam", "kuran", "peygamber", "ibadet"],
        }

        for topic, keywords in subject_keywords.items():
            if any(kw in text for kw in keywords):
                topics.append(topic)

        return topics[:5]

    def get_priority(self) -> int:
        """Get search priority for multi-platform searches.

        YouTube has high priority (-1) for Turkish educational content.

        Returns:
            Priority value (lower = higher priority).
        """
        return -1  # High priority for video content
