"""Invidious API search strategy for learning path recommendations.

Invidious is an open-source alternative YouTube frontend with a free REST API.
No API key required — useful as a fallback when YouTube API quota is exceeded.

API docs: https://docs.invidious.io/api/
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import aiohttp

from ..config import get_learning_path_config
from ..models import KnowledgeLevel, LearningResource
from .resource_search import ResourceSearchStrategy

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Public Invidious instances (fallback chain)
_DEFAULT_INSTANCES = [
    "https://vid.puffyan.us",
    "https://invidious.snopyta.org",
    "https://yewtu.be",
    "https://inv.nadeko.net",
]


class InvidiousSearchStrategy(ResourceSearchStrategy):
    """Invidious API search strategy — free YouTube alternative.

    No API key needed. Searches YouTube content via public Invidious instances.
    Supports region filtering (TR) and subtitle detection.
    """

    def __init__(self, instances: list[str] | None = None) -> None:
        """Initialize Invidious search strategy.

        Args:
            instances: Optional list of Invidious instance base URLs.
        """
        self.config = get_learning_path_config()
        self.instances = instances or _DEFAULT_INSTANCES

    async def search(
        self,
        query: str,
        subject: str | None = None,
        difficulty_range: tuple[float, float] = (-4.0, 4.0),
        limit: int = 10,
        **_filters: Any,
    ) -> list[LearningResource]:
        """Search Invidious for educational videos.

        Args:
            query: Search query string.
            subject: Optional subject filter.
            difficulty_range: Min and max difficulty values.
            limit: Maximum number of results to return.

        Returns:
            List of learning resources.
        """
        try:
            self.validate_query(query)

            search_query = query
            if subject:
                search_query = f"{query} {subject} konu anlatımı"

            results = await self._search_with_fallback(search_query, limit)

            resources = []
            for item in results:
                resource = self.normalize_result(item)
                if resource:
                    resources.append(resource)

            return resources[:limit]

        except Exception as e:
            logger.warning(f"Invidious search failed: {e}")
            return []

    def get_platform_name(self) -> str:
        """Get platform identifier."""
        return "invidious"

    def get_priority(self) -> int:
        """Lower priority than YouTube (fallback role)."""
        return 1

    def normalize_result(self, raw_result: dict[str, Any]) -> LearningResource | None:
        """Convert Invidious API response to LearningResource.

        Args:
            raw_result: Raw Invidious search result.

        Returns:
            Normalized LearningResource or None.
        """
        try:
            video_id = raw_result.get("videoId", "")
            if not video_id:
                return None

            title = raw_result.get("title", "")
            description = raw_result.get("description", "")[:500]

            # Duration in seconds
            length_seconds = raw_result.get("lengthSeconds", 600)
            duration_minutes = max(1, length_seconds // 60)

            # Estimate difficulty from title + description
            difficulty_level = self._estimate_difficulty(title, description)

            # View count
            view_count = raw_result.get("viewCount", 0)

            # Thumbnail
            thumbnails = raw_result.get("videoThumbnails", [])
            thumbnail_url = ""
            for thumb in thumbnails:
                if thumb.get("quality") in ("medium", "high", "maxres"):
                    thumbnail_url = thumb.get("url", "")
                    break

            return LearningResource(
                resource_id=f"invidious-{video_id}",
                title=title,
                description=description,
                url=f"https://www.youtube.com/watch?v={video_id}",
                source="invidious",
                resource_type="video",
                difficulty_level=difficulty_level,
                estimated_time=duration_minutes,
                language="tr",
                tags=self._extract_topics(title, description),
                rating=None,
                metadata={
                    "channel": raw_result.get("author", ""),
                    "channel_id": raw_result.get("authorId", ""),
                    "thumbnail": thumbnail_url,
                    "published_at": str(raw_result.get("published", "")),
                    "view_count": view_count,
                    "like_count": 0,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to normalize Invidious result: {e}")
            return None

    async def _search_with_fallback(
        self, query: str, limit: int
    ) -> list[dict[str, Any]]:
        """Search with instance fallback chain.

        Tries each Invidious instance until one succeeds.

        Args:
            query: Search query.
            limit: Maximum results.

        Returns:
            List of raw search results.
        """
        params = {
            "q": query,
            "type": "video",
            "region": "TR",
            "sort_by": "relevance",
            "fields": (
                "videoId,title,description,lengthSeconds,viewCount,"
                "author,authorId,videoThumbnails,published"
            ),
        }

        async with aiohttp.ClientSession() as session:
            for instance in self.instances:
                try:
                    async with session.get(
                        f"{instance}/api/v1/search",
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as resp:
                        if resp.status != 200:
                            logger.debug(f"Invidious {instance} returned {resp.status}")
                            continue

                        data = await resp.json()
                        if not isinstance(data, list):
                            continue

                        # Filter to video type only
                        videos = [
                            item
                            for item in data
                            if item.get("type") == "video" and item.get("videoId")
                        ]

                        if videos:
                            logger.debug(
                                f"Invidious {instance} returned {len(videos)} videos"
                            )
                            return videos[:limit]

                except (aiohttp.ClientError, TimeoutError) as e:
                    logger.debug(f"Invidious {instance} failed: {e}")
                    continue
                except Exception as e:
                    logger.debug(f"Invidious {instance} unexpected error: {e}")
                    continue

        logger.warning("All Invidious instances failed")
        return []

    def _estimate_difficulty(self, title: str, description: str) -> KnowledgeLevel:
        """Estimate difficulty from Turkish educational keywords."""
        text = (title + " " + description).lower()

        beginner_kw = ["temel", "başlangıç", "giriş", "kolay", "basit", "ilkokul"]
        advanced_kw = ["ileri", "zor", "detaylı", "üniversite", "yks", "ayt"]
        intermediate_kw = ["lise", "tyt", "9. sınıf", "10. sınıf", "11. sınıf"]

        adv = sum(1 for kw in advanced_kw if kw in text)
        beg = sum(1 for kw in beginner_kw if kw in text)
        mid = sum(1 for kw in intermediate_kw if kw in text)

        if adv > max(beg, mid):
            return KnowledgeLevel.ADVANCED
        if beg > max(adv, mid):
            return KnowledgeLevel.BEGINNER
        return KnowledgeLevel.INTERMEDIATE

    def _extract_topics(self, title: str, description: str) -> list[str]:
        """Extract subject topics from Turkish content."""
        text = (title + " " + description).lower()
        topics = []

        subject_keywords = {
            "Matematik": ["matematik", "geometri", "türev", "integral"],
            "Fizik": ["fizik", "hareket", "kuvvet", "enerji"],
            "Kimya": ["kimya", "atom", "mol", "reaksiyon"],
            "Biyoloji": ["biyoloji", "hücre", "genetik", "ekosistem"],
            "Türkçe": ["türkçe", "dil bilgisi", "paragraf"],
            "Tarih": ["tarih", "osmanlı", "cumhuriyet"],
            "Coğrafya": ["coğrafya", "iklim", "nüfus"],
        }

        for topic, keywords in subject_keywords.items():
            if any(kw in text for kw in keywords):
                topics.append(topic)

        return topics[:5]
