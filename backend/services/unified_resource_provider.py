"""
Unified Resource Provider
FAZ 3.1: Content Management Refactoring
Combines YouTube, EBA TV, Khan Academy and custom resources into a single interface

DEPRECATED: No API consumers. The active pipeline uses
learning_path_v2.py -> facade.py -> resource_discovery.py.
Safe to delete in a future cleanup PR.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ResourcePlatform(Enum):
    """Supported resource platforms"""

    YOUTUBE = "youtube"
    EBA_TV = "eba_tv"
    KHAN_ACADEMY = "khan_academy"
    CUSTOM = "custom"


class ResourceType(Enum):
    """Types of educational resources"""

    VIDEO = "video"
    ARTICLE = "article"
    INTERACTIVE = "interactive"
    QUIZ = "quiz"
    PDF = "pdf"
    EXERCISE = "exercise"


class ContentQuality(Enum):
    """Content quality levels"""

    EXCELLENT = "excellent"  # 4.5+ rating
    GOOD = "good"  # 3.5-4.5 rating
    AVERAGE = "average"  # 2.5-3.5 rating
    POOR = "poor"  # Below 2.5


@dataclass
class UnifiedResource:
    """Unified resource representation across all platforms"""

    id: str
    title: str
    platform: ResourcePlatform
    resource_type: ResourceType
    url: str
    subject: str
    topic: str
    subtopic: str | None = None
    grade_level: int = 12
    difficulty: str = "medium"
    duration_seconds: int | None = None
    thumbnail_url: str | None = None
    description: str | None = None
    quality_score: float = 0.0
    quality_level: ContentQuality = ContentQuality.AVERAGE
    language: str = "tr"
    has_subtitles: bool = False
    has_transcript: bool = False
    view_count: int = 0
    like_count: int = 0
    rating: float = 0.0
    keywords: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "platform": self.platform.value,
            "resource_type": self.resource_type.value,
            "url": self.url,
            "subject": self.subject,
            "topic": self.topic,
            "subtopic": self.subtopic,
            "grade_level": self.grade_level,
            "difficulty": self.difficulty,
            "duration_seconds": self.duration_seconds,
            "duration_formatted": self._format_duration(),
            "thumbnail_url": self.thumbnail_url,
            "description": self.description,
            "quality_score": self.quality_score,
            "quality_level": self.quality_level.value,
            "language": self.language,
            "has_subtitles": self.has_subtitles,
            "has_transcript": self.has_transcript,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "rating": self.rating,
            "keywords": self.keywords,
            "created_at": self.created_at.isoformat(),
        }

    def _format_duration(self) -> str:
        """Format duration as HH:MM:SS"""
        if not self.duration_seconds:
            return "00:00"

        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        seconds = self.duration_seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"


class ResourceProviderBase(ABC):
    """Base class for resource providers"""

    @abstractmethod
    async def search(
        self,
        query: str,
        subject: str | None = None,
        topic: str | None = None,
        grade_level: int | None = None,
        limit: int = 10,
    ) -> list[UnifiedResource]:
        """Search for resources"""

    @abstractmethod
    async def get_by_id(self, resource_id: str) -> UnifiedResource | None:
        """Get resource by ID"""

    @abstractmethod
    async def get_recommendations(
        self,
        user_id: int,
        subject: str,
        topic: str | None = None,
        limit: int = 5,
    ) -> list[UnifiedResource]:
        """Get personalized recommendations"""

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Check provider health"""


class YouTubeResourceProvider(ResourceProviderBase):
    """YouTube resource provider"""

    def __init__(self):
        self._connected = False

    async def connect(self) -> None:
        """Initialize YouTube API connection"""
        # Import actual services when available
        try:
            from services.youtube_discovery import get_youtube_discovery

            self._youtube = await get_youtube_discovery()
            self._connected = True
            logger.info("[YouTube Provider] Connected")
        except ImportError:
            logger.warning("[YouTube Provider] Service not available, using mock")
            self._connected = True

    async def search(
        self,
        query: str,
        subject: str | None = None,
        topic: str | None = None,
        grade_level: int | None = None,
        limit: int = 10,
    ) -> list[UnifiedResource]:
        """Search YouTube for educational content"""
        if not self._connected:
            await self.connect()

        # Build search query with Turkish educational context
        search_parts = [query]
        if subject:
            search_parts.append(subject)
        if topic:
            search_parts.append(topic)
        search_parts.append("ders anlatımı")  # Educational focus

        full_query = " ".join(search_parts)

        # For now, return mock data - integrate with actual service
        resources = []
        for i in range(min(limit, 5)):
            resource = UnifiedResource(
                id=f"yt_{i}_{hash(query) % 10000}",
                title=f"{query} - {subject or 'Genel'} Ders Anlatımı #{i + 1}",
                platform=ResourcePlatform.YOUTUBE,
                resource_type=ResourceType.VIDEO,
                url=f"https://youtube.com/watch?v=example{i}",
                subject=subject or "Genel",
                topic=topic or query,
                grade_level=grade_level or 12,
                difficulty="medium",
                duration_seconds=600 + i * 120,
                quality_score=4.0 + (i * 0.1),
                quality_level=ContentQuality.GOOD,
                keywords=[query, subject or "", topic or ""],
            )
            resources.append(resource)

        return resources

    async def get_by_id(self, resource_id: str) -> UnifiedResource | None:
        """Get YouTube video by ID"""
        if not resource_id.startswith("yt_"):
            return None

        return UnifiedResource(
            id=resource_id,
            title="YouTube Video",
            platform=ResourcePlatform.YOUTUBE,
            resource_type=ResourceType.VIDEO,
            url=f"https://youtube.com/watch?v={resource_id[3:]}",
            subject="Genel",
            topic="Genel",
        )

    async def get_recommendations(
        self,
        user_id: int,
        subject: str,
        topic: str | None = None,
        limit: int = 5,
    ) -> list[UnifiedResource]:
        """Get personalized YouTube recommendations"""
        # Use search with topic to get relevant content
        return await self.search(
            query=topic or subject,
            subject=subject,
            topic=topic,
            limit=limit,
        )

    async def health_check(self) -> dict[str, Any]:
        """Check YouTube API health"""
        return {
            "platform": "youtube",
            "status": "healthy" if self._connected else "disconnected",
            "api_quota_remaining": 9500,  # Mock quota
            "last_check": datetime.now().isoformat(),
        }


class EBATVResourceProvider(ResourceProviderBase):
    """EBA TV resource provider"""

    def __init__(self):
        self._connected = False

    async def connect(self) -> None:
        """Initialize EBA TV connection"""
        try:
            from services.eba_tv_client import get_eba_client

            self._eba = await get_eba_client()
            self._connected = True
            logger.info("[EBA TV Provider] Connected")
        except ImportError:
            logger.warning("[EBA TV Provider] Service not available, using mock")
            self._connected = True

    async def search(
        self,
        query: str,
        subject: str | None = None,
        topic: str | None = None,
        grade_level: int | None = None,
        limit: int = 10,
    ) -> list[UnifiedResource]:
        """Search EBA TV for content"""
        if not self._connected:
            await self.connect()

        resources = []
        for i in range(min(limit, 5)):
            resource = UnifiedResource(
                id=f"eba_{i}_{hash(query) % 10000}",
                title=f"{subject or 'TYT'} - {topic or query} | EBA TV",
                platform=ResourcePlatform.EBA_TV,
                resource_type=ResourceType.VIDEO,
                url=f"https://eba.gov.tr/video/{i}",
                subject=subject or "Genel",
                topic=topic or query,
                grade_level=grade_level or 12,
                difficulty="medium",
                duration_seconds=1200 + i * 180,
                quality_score=4.2,
                quality_level=ContentQuality.GOOD,
                has_subtitles=True,
                has_transcript=True,
                keywords=[query, "EBA", "MEB", subject or ""],
            )
            resources.append(resource)

        return resources

    async def get_by_id(self, resource_id: str) -> UnifiedResource | None:
        """Get EBA TV video by ID"""
        if not resource_id.startswith("eba_"):
            return None

        return UnifiedResource(
            id=resource_id,
            title="EBA TV Video",
            platform=ResourcePlatform.EBA_TV,
            resource_type=ResourceType.VIDEO,
            url=f"https://eba.gov.tr/video/{resource_id[4:]}",
            subject="Genel",
            topic="Genel",
            has_subtitles=True,
            has_transcript=True,
        )

    async def get_recommendations(
        self,
        user_id: int,
        subject: str,
        topic: str | None = None,
        limit: int = 5,
    ) -> list[UnifiedResource]:
        """Get personalized EBA TV recommendations"""
        return await self.search(
            query=topic or subject,
            subject=subject,
            topic=topic,
            limit=limit,
        )

    async def health_check(self) -> dict[str, Any]:
        """Check EBA TV health"""
        return {
            "platform": "eba_tv",
            "status": "healthy" if self._connected else "disconnected",
            "api_available": True,
            "last_check": datetime.now().isoformat(),
        }


class KhanAcademyResourceProvider(ResourceProviderBase):
    """Khan Academy resource provider"""

    def __init__(self):
        self._connected = False

    async def connect(self) -> None:
        """Initialize Khan Academy connection"""
        try:
            from services.khan_academy_client import get_khan_client

            self._khan = await get_khan_client()
            self._connected = True
            logger.info("[Khan Academy Provider] Connected")
        except ImportError:
            logger.warning("[Khan Academy Provider] Service not available, using mock")
            self._connected = True

    async def search(
        self,
        query: str,
        subject: str | None = None,
        topic: str | None = None,
        grade_level: int | None = None,
        limit: int = 10,
    ) -> list[UnifiedResource]:
        """Search Khan Academy for content"""
        if not self._connected:
            await self.connect()

        resources = []
        for i in range(min(limit, 5)):
            resource = UnifiedResource(
                id=f"khan_{i}_{hash(query) % 10000}",
                title=f"{topic or query} | Khan Academy Türkçe",
                platform=ResourcePlatform.KHAN_ACADEMY,
                resource_type=ResourceType.VIDEO
                if i % 2 == 0
                else ResourceType.EXERCISE,
                url=f"https://tr.khanacademy.org/content/{i}",
                subject=subject or "Matematik",
                topic=topic or query,
                grade_level=grade_level or 12,
                difficulty="medium",
                duration_seconds=480 + i * 60 if i % 2 == 0 else None,
                quality_score=4.5,
                quality_level=ContentQuality.EXCELLENT,
                has_subtitles=True,
                language="tr",
                keywords=[query, "Khan Academy", subject or ""],
            )
            resources.append(resource)

        return resources

    async def get_by_id(self, resource_id: str) -> UnifiedResource | None:
        """Get Khan Academy content by ID"""
        if not resource_id.startswith("khan_"):
            return None

        return UnifiedResource(
            id=resource_id,
            title="Khan Academy Content",
            platform=ResourcePlatform.KHAN_ACADEMY,
            resource_type=ResourceType.VIDEO,
            url=f"https://tr.khanacademy.org/content/{resource_id[5:]}",
            subject="Matematik",
            topic="Genel",
            has_subtitles=True,
        )

    async def get_recommendations(
        self,
        user_id: int,
        subject: str,
        topic: str | None = None,
        limit: int = 5,
    ) -> list[UnifiedResource]:
        """Get personalized Khan Academy recommendations"""
        return await self.search(
            query=topic or subject,
            subject=subject,
            topic=topic,
            limit=limit,
        )

    async def health_check(self) -> dict[str, Any]:
        """Check Khan Academy health"""
        return {
            "platform": "khan_academy",
            "status": "healthy" if self._connected else "disconnected",
            "api_available": True,
            "last_check": datetime.now().isoformat(),
        }


class UnifiedResourceService:
    """
    Unified Resource Service
    Combines all resource providers into a single interface
    """

    def __init__(self):
        self.providers: dict[ResourcePlatform, ResourceProviderBase] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all resource providers"""
        if self._initialized:
            return

        # Initialize providers
        youtube_provider = YouTubeResourceProvider()
        await youtube_provider.connect()
        self.providers[ResourcePlatform.YOUTUBE] = youtube_provider

        eba_provider = EBATVResourceProvider()
        await eba_provider.connect()
        self.providers[ResourcePlatform.EBA_TV] = eba_provider

        khan_provider = KhanAcademyResourceProvider()
        await khan_provider.connect()
        self.providers[ResourcePlatform.KHAN_ACADEMY] = khan_provider

        self._initialized = True
        logger.info("[Unified Resource Service] All providers initialized")

    async def search(
        self,
        query: str,
        platforms: list[ResourcePlatform] | None = None,
        subject: str | None = None,
        topic: str | None = None,
        grade_level: int | None = None,
        resource_type: ResourceType | None = None,
        min_quality: ContentQuality | None = None,
        limit: int = 20,
    ) -> list[UnifiedResource]:
        """
        Search across all or specified platforms

        Args:
            query: Search query
            platforms: Platforms to search (None = all)
            subject: Subject filter
            topic: Topic filter
            grade_level: Grade level filter
            resource_type: Resource type filter
            min_quality: Minimum quality level
            limit: Maximum results

        Returns:
            Combined list of resources sorted by quality
        """
        if not self._initialized:
            await self.initialize()

        # Default to all platforms
        target_platforms = platforms or list(self.providers.keys())

        # Search concurrently across platforms
        tasks = []
        for platform in target_platforms:
            if platform in self.providers:
                provider = self.providers[platform]
                tasks.append(
                    provider.search(
                        query=query,
                        subject=subject,
                        topic=topic,
                        grade_level=grade_level,
                        limit=limit // len(target_platforms) + 1,
                    )
                )

        # Gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine and filter results
        all_resources: list[UnifiedResource] = []
        for result in results:
            if isinstance(result, list):
                all_resources.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Provider error: {result}")

        # Filter by resource type
        if resource_type:
            all_resources = [
                r for r in all_resources if r.resource_type == resource_type
            ]

        # Filter by minimum quality
        if min_quality:
            quality_order = [
                ContentQuality.POOR,
                ContentQuality.AVERAGE,
                ContentQuality.GOOD,
                ContentQuality.EXCELLENT,
            ]
            min_index = quality_order.index(min_quality)
            all_resources = [
                r
                for r in all_resources
                if quality_order.index(r.quality_level) >= min_index
            ]

        # Sort by quality score (descending)
        all_resources.sort(key=lambda r: r.quality_score, reverse=True)

        return all_resources[:limit]

    async def get_resource(
        self,
        resource_id: str,
    ) -> UnifiedResource | None:
        """
        Get a resource by ID from any platform

        Args:
            resource_id: Resource ID (prefixed with platform)

        Returns:
            Resource if found
        """
        if not self._initialized:
            await self.initialize()

        # Determine platform from ID prefix
        platform_map = {
            "yt_": ResourcePlatform.YOUTUBE,
            "eba_": ResourcePlatform.EBA_TV,
            "khan_": ResourcePlatform.KHAN_ACADEMY,
        }

        for prefix, platform in platform_map.items():
            if resource_id.startswith(prefix):
                provider = self.providers.get(platform)
                if provider:
                    return await provider.get_by_id(resource_id)

        return None

    async def get_recommendations(
        self,
        user_id: int,
        subject: str,
        topic: str | None = None,
        platforms: list[ResourcePlatform] | None = None,
        limit: int = 10,
    ) -> list[UnifiedResource]:
        """
        Get personalized recommendations across platforms

        Args:
            user_id: User ID for personalization
            subject: Subject for recommendations
            topic: Optional topic focus
            platforms: Platforms to use (None = all)
            limit: Maximum recommendations

        Returns:
            Personalized resource recommendations
        """
        if not self._initialized:
            await self.initialize()

        target_platforms = platforms or list(self.providers.keys())

        # Get recommendations concurrently
        tasks = []
        for platform in target_platforms:
            if platform in self.providers:
                provider = self.providers[platform]
                tasks.append(
                    provider.get_recommendations(
                        user_id=user_id,
                        subject=subject,
                        topic=topic,
                        limit=limit // len(target_platforms) + 1,
                    )
                )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_recommendations: list[UnifiedResource] = []
        for result in results:
            if isinstance(result, list):
                all_recommendations.extend(result)

        # Sort by quality and relevance
        all_recommendations.sort(key=lambda r: r.quality_score, reverse=True)

        return all_recommendations[:limit]

    async def get_by_subject(
        self,
        subject: str,
        topic: str | None = None,
        grade_level: int | None = None,
        limit: int = 20,
    ) -> dict[str, list[UnifiedResource]]:
        """
        Get resources organized by platform for a subject

        Args:
            subject: Subject to get resources for
            topic: Optional topic filter
            grade_level: Optional grade level filter
            limit: Maximum per platform

        Returns:
            Dictionary of platform -> resources
        """
        if not self._initialized:
            await self.initialize()

        result: dict[str, list[UnifiedResource]] = {}

        for platform, provider in self.providers.items():
            resources = await provider.search(
                query=topic or subject,
                subject=subject,
                topic=topic,
                grade_level=grade_level,
                limit=limit,
            )
            result[platform.value] = resources

        return result

    async def health_check(self) -> dict[str, Any]:
        """
        Check health of all providers

        Returns:
            Health status for each provider
        """
        if not self._initialized:
            await self.initialize()

        health_results = {}
        for platform, provider in self.providers.items():
            health_results[platform.value] = await provider.health_check()

        # Overall status
        all_healthy = all(h.get("status") == "healthy" for h in health_results.values())

        return {
            "overall_status": "healthy" if all_healthy else "degraded",
            "providers": health_results,
            "timestamp": datetime.now().isoformat(),
        }

    async def get_statistics(self) -> dict[str, Any]:
        """
        Get resource statistics

        Returns:
            Statistics across all platforms
        """
        return {
            "providers_count": len(self.providers),
            "active_providers": [p.value for p in self.providers.keys()],
            "supported_types": [t.value for t in ResourceType],
            "quality_levels": [q.value for q in ContentQuality],
            "initialized": self._initialized,
        }


# Global service instance
_unified_resource_service: UnifiedResourceService | None = None


async def get_unified_resource_service() -> UnifiedResourceService:
    """Get global unified resource service"""
    global _unified_resource_service
    if _unified_resource_service is None:
        _unified_resource_service = UnifiedResourceService()
        await _unified_resource_service.initialize()
    return _unified_resource_service
