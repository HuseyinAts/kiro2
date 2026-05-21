"""
Video Recommendation Service
Orchestrates video discovery, caching, and filtering for personalized recommendations
Teknofest 2025 - Eğitim Eylemci Projesi

RECOMMENDATION SERVICE HIERARCHY (2025-01-24):
Bu proje 4 oneri servisi iceriyor:

1. CONTENT RECOMMENDATIONS (Genel):
   - content_recommendation_service.py - Hybrid filtering (REQ-4)
   - ChromaDB embeddings + collaborative filtering

2. VIDEO RECOMMENDATIONS (YouTube):
   - video_recommendation_service.py (BU DOSYA) - Ana orchestrator
   - enhanced_resource_recommendation_engine.py - Ek filtreleme
   - video_recommendation_monitoring.py - Monitoring

3. YOUTUBE SEARCH:
   - semantic_youtube_search.py - Semantic search
   - advanced_youtube_search.py - Advanced filters

REFACTORING NEEDED:
video_recommendation_service.py ve enhanced_resource_recommendation_engine.py
birlestirilmeli veya sorumluluklar netlestirilmeli.

Onerilen yaklasim:
- video_recommendation_service.py: Caching + Orchestration
- enhanced_resource_recommendation_engine.py: Quality scoring + Filtering
"""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass

from core.multi_layer_cache import MultiLayerCache
from core.structured_logger import get_logger
from services.advanced_youtube_search import (
    AdvancedYouTubeSearch,
    TurkishEducationVideo,
)
from services.semantic_youtube_search import SemanticYouTubeSearch
from services.turkish_content_filter import TurkishContentFilter

logger = get_logger(__name__)


@dataclass
class StudentProfile:
    """Öğrenci profili - video önerileri için"""

    goals: list[str]
    currentLevel: dict[str, int]
    learningStyle: str
    preferences: dict = None

    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}


@dataclass
class VideoRecommendation:
    """Video öneri sonucu"""

    subject_exam: str
    videos: list[TurkishEducationVideo]
    total_count: int
    cache_hit: bool
    response_time_ms: int


class VideoRecommendationService:
    """
    Video öneri servisi - cache, filtering ve orchestration

    Bu servis:
    1. Cache kontrolü yapar (student profile hash)
    2. Cache miss durumunda parallel video discovery yapar
    3. Türkçe içerik filtreleme uygular
    4. Relevance ve difficulty filtering yapar
    5. Sonuçları cache'e yazar
    6. Metrik toplar
    """

    def __init__(
        self,
        cache: MultiLayerCache,
        advanced_search: AdvancedYouTubeSearch,
        semantic_search: SemanticYouTubeSearch,
        content_filter: TurkishContentFilter,
    ):
        """
        VideoRecommendationService'i başlat

        Args:
            cache: Multi-layer cache (Memory + Redis)
            advanced_search: Advanced YouTube search servisi
            semantic_search: Semantic YouTube search servisi
            content_filter: Turkish content filter servisi
        """
        self.cache = cache
        self.advanced_search = advanced_search
        self.semantic_search = semantic_search
        self.content_filter = content_filter

        # Metrics (internal tracking)
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_response_time = 0.0

        logger.info("VideoRecommendationService initialized with MultiLayerCache")

    async def get_recommendations(
        self, student_profile: StudentProfile, request_id: str
    ) -> list[VideoRecommendation]:
        """
        Öğrenci profiline göre video önerileri al

        Flow:
        1. Cache key oluştur (student profile hash)
        2. Cache kontrolü yap
        3. Cache miss ise parallel video discovery
        4. Türkçe içerik filtreleme
        5. Relevance ve difficulty filtering
        6. Cache'e yaz
        7. Metrik topla

        Args:
            student_profile: Öğrenci profili
            request_id: Unique request ID

        Returns:
            List[VideoRecommendation]: Video önerileri
        """
        start_time = time.time()
        self.total_requests += 1

        logger.info(
            f"[{request_id}] Video recommendations requested for profile: "
            f"goals={student_profile.goals[:2]}, "
            f"style={student_profile.learningStyle}"
        )

        try:
            # 1. Cache key oluştur
            cache_key = self._generate_cache_key(student_profile)
            logger.debug(f"[{request_id}] Cache key: {cache_key}")

            # 2. Cache kontrolü
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                self.cache_hits += 1
                logger.info(
                    f"[{request_id}] Cache HIT - returning cached recommendations"
                )

                # Deserialize cached recommendations
                recommendations = self._deserialize_recommendations(cached_result)

                # Update cache_hit flag
                for rec in recommendations:
                    rec.cache_hit = True
                    rec.response_time_ms = int((time.time() - start_time) * 1000)

                return recommendations

            # 3. Cache miss - video discovery
            self.cache_misses += 1
            logger.info(f"[{request_id}] Cache MISS - discovering videos")

            recommendations = await self._discover_videos(student_profile, request_id)

            # 4. Cache'e yaz
            await self.cache.set(
                cache_key,
                self._serialize_recommendations(recommendations),
                ttl=3600,  # 1 hour
            )
            logger.debug(f"[{request_id}] Recommendations cached")

            # 5. Metrik kaydet
            response_time = (time.time() - start_time) * 1000
            self.total_response_time += response_time

            # Update response time in recommendations
            for rec in recommendations:
                rec.response_time_ms = int(response_time)

            logger.info(
                f"[{request_id}] Recommendations completed in {response_time:.0f}ms - "
                f"{sum(r.total_count for r in recommendations)} videos"
            )

            return recommendations

        except Exception as e:
            logger.error(
                f"[{request_id}] Error getting recommendations: {e!s}", exc_info=True
            )
            # Return empty recommendations on error
            return []

    async def _discover_videos(
        self, profile: StudentProfile, request_id: str
    ) -> list[VideoRecommendation]:
        """
        Paralel video discovery ve filtreleme

        Her hedef için:
        1. Advanced + Semantic search (parallel)
        2. Merge ve deduplicate
        3. Turkish content filtering
        4. Relevance ve difficulty filtering
        5. Quality score'a göre sırala
        6. Top 5 al

        Args:
            profile: Student profile
            request_id: Request ID

        Returns:
            List[VideoRecommendation]: Filtered recommendations
        """
        tasks = []

        # Her hedef için paralel arama (max 3 hedef)
        goals_to_process = profile.goals[:3]
        logger.info(f"[{request_id}] Processing {len(goals_to_process)} goals")

        for goal in goals_to_process:
            task = self._search_for_goal(goal, profile, request_id)
            tasks.append(task)

        # Paralel execution
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Hataları filtrele
        recommendations = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"[{request_id}] Error processing goal '{goals_to_process[i]}': {result!s}"
                , exc_info=True)
            else:
                recommendations.append(result)

        logger.info(
            f"[{request_id}] Discovery completed: {len(recommendations)} recommendations"
        )

        return recommendations

    async def _search_for_goal(
        self, goal: str, profile: StudentProfile, request_id: str
    ) -> VideoRecommendation:
        """
        Tek bir hedef için video arama

        Args:
            goal: Öğrenci hedefi (örn: "TYT Matematik")
            profile: Student profile
            request_id: Request ID

        Returns:
            VideoRecommendation: Filtered video recommendation
        """
        try:
            # Konu ve zorluk seviyesi belirle
            subject = self._extract_subject(goal)
            exam_type = self._extract_exam_type(goal)
            difficulty = self._determine_difficulty(subject, profile.currentLevel)

            logger.debug(
                f"[{request_id}] Searching for: subject={subject}, "
                f"exam_type={exam_type}, difficulty={difficulty}"
            )

            # Hybrid search: Advanced + Semantic (parallel)
            advanced_task = self.advanced_search.search_videos_with_filters(
                subject=subject,
                exam_type=exam_type,
                difficulty=difficulty,
                max_results=10,
            )

            semantic_task = self.semantic_search.semantic_search_videos(
                subject=subject,
                exam_type=exam_type,
                difficulty=difficulty,
                max_results=10,
            )

            # Execute parallel
            advanced_videos, semantic_results = await asyncio.gather(
                advanced_task, semantic_task, return_exceptions=True
            )

            # Handle errors
            if isinstance(advanced_videos, Exception):
                logger.warning(
                    f"[{request_id}] Advanced search failed: {advanced_videos!s}"
                )
                advanced_videos = []

            if isinstance(semantic_results, Exception):
                logger.warning(
                    f"[{request_id}] Semantic search failed: {semantic_results!s}"
                )
                semantic_results = []

            # Convert semantic results to TurkishEducationVideo
            semantic_videos = self._convert_semantic_to_turkish_videos(
                semantic_results, subject, difficulty, exam_type
            )

            # Merge ve deduplicate
            all_videos = self._merge_videos(advanced_videos, semantic_videos)
            logger.debug(f"[{request_id}] Merged {len(all_videos)} videos")

            # Türkçe içerik filtreleme
            filtered_videos = await self._filter_turkish_content(all_videos, request_id)
            logger.debug(
                f"[{request_id}] Filtered to {len(filtered_videos)} Turkish videos"
            )

            # Quality score'a göre sırala ve top 5 al
            sorted_videos = sorted(
                filtered_videos, key=lambda v: v.quality_score, reverse=True
            )[:5]

            return VideoRecommendation(
                subject_exam=f"{subject.title()} {exam_type}",
                videos=sorted_videos,
                total_count=len(sorted_videos),
                cache_hit=False,
                response_time_ms=0,  # Will be updated later
            )

        except Exception as e:
            logger.error(
                f"[{request_id}] Error in _search_for_goal: {e!s}", exc_info=True
            )
            # Return empty recommendation
            return VideoRecommendation(
                subject_exam=f"{goal}",
                videos=[],
                total_count=0,
                cache_hit=False,
                response_time_ms=0,
            )

    def _generate_cache_key(self, profile: StudentProfile) -> str:
        """
        Cache key oluştur - student profile hash

        Args:
            profile: Student profile

        Returns:
            str: Cache key
        """
        # Profile'ı deterministic JSON'a çevir
        profile_dict = {
            "goals": sorted(profile.goals),  # Sort for consistency
            "currentLevel": profile.currentLevel,
            "learningStyle": profile.learningStyle,
        }

        profile_str = json.dumps(profile_dict, sort_keys=True)
        profile_hash = hashlib.md5(profile_str.encode()).hexdigest()

        return f"video_rec:{profile_hash}"

    def _extract_subject(self, goal: str) -> str:
        """
        Hedeften konu çıkar

        Args:
            goal: Öğrenci hedefi

        Returns:
            str: Konu (matematik, fizik, etc.)
        """
        goal_lower = goal.lower()

        # Konu keyword mapping
        subject_keywords = {
            "matematik": ["matematik", "math", "geometri", "algebra", "trigonometri"],
            "fizik": ["fizik", "physics", "mekanik", "elektrik"],
            "kimya": ["kimya", "chemistry", "organik", "inorganik"],
            "biyoloji": ["biyoloji", "biology", "genetik", "hücre"],
            "turkce": ["türkçe", "turkish", "edebiyat", "dil bilgisi"],
            "tarih": ["tarih", "history", "osmanlı", "cumhuriyet"],
            "cografya": ["coğrafya", "geography", "harita"],
        }

        # Keyword matching
        for subject, keywords in subject_keywords.items():
            if any(kw in goal_lower for kw in keywords):
                return subject

        # Default: matematik
        return "matematik"

    def _extract_exam_type(self, goal: str) -> str:
        """
        Hedeften sınav tipini çıkar

        Args:
            goal: Öğrenci hedefi

        Returns:
            str: Sınav tipi (TYT, AYT, YDT, LGS)
        """
        goal_upper = goal.upper()

        exam_types = ["TYT", "AYT", "YDT", "LGS", "KPSS"]

        for exam_type in exam_types:
            if exam_type in goal_upper:
                return exam_type

        # Default: TYT
        return "TYT"

    def _determine_difficulty(self, subject: str, current_level: dict[str, int]) -> str:
        """
        Zorluk seviyesi belirle

        Args:
            subject: Konu
            current_level: Mevcut seviye dict (konu -> 0-100)

        Returns:
            str: Zorluk seviyesi (başlangıç, orta, ileri)
        """
        # Konuya göre seviye al (default: 50)
        level = current_level.get(subject, 50)

        # Seviye -> zorluk mapping (ASCII — matches DifficultyLevel enum values)
        if level < 30:
            return "baslangic"
        if level < 70:
            return "orta"
        return "ileri"

    def _merge_videos(
        self,
        advanced_videos: list[TurkishEducationVideo],
        semantic_videos: list[TurkishEducationVideo],
    ) -> list[TurkishEducationVideo]:
        """
        İki video listesini merge et ve deduplicate yap

        Args:
            advanced_videos: Advanced search sonuçları
            semantic_videos: Semantic search sonuçları

        Returns:
            List[TurkishEducationVideo]: Merged ve deduplicated videolar
        """
        # Video ID'lere göre deduplicate
        seen_ids = set()
        merged = []

        # Önce advanced videos (daha güvenilir)
        for video in advanced_videos:
            if video.video_id not in seen_ids:
                seen_ids.add(video.video_id)
                merged.append(video)

        # Sonra semantic videos
        for video in semantic_videos:
            if video.video_id not in seen_ids:
                seen_ids.add(video.video_id)
                merged.append(video)

        return merged

    def _convert_semantic_to_turkish_videos(
        self, semantic_results: list, subject: str, difficulty: str, exam_type: str
    ) -> list[TurkishEducationVideo]:
        """
        Semantic search sonuçlarını TurkishEducationVideo'ya çevir

        Args:
            semantic_results: Semantic search results
            subject: Konu
            difficulty: Zorluk
            exam_type: Sınav tipi

        Returns:
            List[TurkishEducationVideo]: Converted videos
        """
        converted = []

        for result in semantic_results:
            try:
                # SemanticVideoMatch -> TurkishEducationVideo
                video = TurkishEducationVideo(
                    video_id=result.video_id,
                    title=result.title,
                    channel=result.channel,
                    channel_id=result.channel_id,
                    duration=result.duration,
                    view_count=result.view_count,
                    upload_date=result.upload_date,
                    thumbnail=result.thumbnail,
                    description=result.description,
                    quality_score=result.quality_score * 10,  # 0-1 -> 0-10
                    subject=subject,
                    difficulty=difficulty,
                    exam_type=exam_type,
                    language_score=result.language_score * 10,  # 0-1 -> 0-10
                    education_relevance=result.subject_relevance * 10,  # 0-1 -> 0-10
                    url=result.url,
                )
                converted.append(video)
            except Exception as e:
                logger.warning(f"Error converting semantic result: {e!s}")
                continue

        return converted

    async def _filter_turkish_content(
        self, videos: list[TurkishEducationVideo], request_id: str
    ) -> list[TurkishEducationVideo]:
        """
        Türkçe içerik filtreleme

        Args:
            videos: Video listesi
            request_id: Request ID

        Returns:
            List[TurkishEducationVideo]: Filtered videos
        """
        filtered = []

        for video in videos:
            try:
                # Turkish content validation
                validation_result = await self.content_filter.validate_turkish_content(
                    video_title=video.title,
                    video_description=video.description,
                    channel_name=video.channel,
                )

                # Türkçe ise ekle
                if validation_result.is_turkish:
                    filtered.append(video)
                else:
                    logger.debug(
                        f"[{request_id}] Filtered out non-Turkish video: {video.title[:50]}"
                    )

            except Exception as e:
                logger.warning(f"[{request_id}] Error filtering video: {e!s}")
                # Hata durumunda videoyu dahil et (safe side)
                filtered.append(video)

        return filtered

    def _serialize_recommendations(
        self, recommendations: list[VideoRecommendation]
    ) -> dict:
        """
        Recommendations'ı cache için serialize et

        Args:
            recommendations: Video recommendations

        Returns:
            dict: Serialized data
        """
        return {
            "recommendations": [
                {
                    "subject_exam": rec.subject_exam,
                    "videos": [
                        {
                            "video_id": v.video_id,
                            "title": v.title,
                            "channel": v.channel,
                            "channel_id": v.channel_id,
                            "duration": v.duration,
                            "view_count": v.view_count,
                            "upload_date": v.upload_date,
                            "thumbnail": v.thumbnail,
                            "description": v.description,
                            "quality_score": v.quality_score,
                            "subject": v.subject,
                            "difficulty": v.difficulty,
                            "exam_type": v.exam_type,
                            "language_score": v.language_score,
                            "education_relevance": v.education_relevance,
                            "url": v.url,
                        }
                        for v in rec.videos
                    ],
                    "total_count": rec.total_count,
                    "cache_hit": rec.cache_hit,
                    "response_time_ms": rec.response_time_ms,
                }
                for rec in recommendations
            ]
        }

    def _deserialize_recommendations(self, data: dict) -> list[VideoRecommendation]:
        """
        Cache'den gelen data'yı deserialize et

        Args:
            data: Cached data

        Returns:
            List[VideoRecommendation]: Deserialized recommendations
        """
        recommendations = []

        for rec_data in data.get("recommendations", []):
            videos = [
                TurkishEducationVideo(
                    video_id=v["video_id"],
                    title=v["title"],
                    channel=v["channel"],
                    channel_id=v["channel_id"],
                    duration=v["duration"],
                    view_count=v["view_count"],
                    upload_date=v["upload_date"],
                    thumbnail=v["thumbnail"],
                    description=v["description"],
                    quality_score=v["quality_score"],
                    subject=v["subject"],
                    difficulty=v["difficulty"],
                    exam_type=v["exam_type"],
                    language_score=v["language_score"],
                    education_relevance=v["education_relevance"],
                    url=v["url"],
                )
                for v in rec_data.get("videos", [])
            ]

            recommendation = VideoRecommendation(
                subject_exam=rec_data["subject_exam"],
                videos=videos,
                total_count=rec_data["total_count"],
                cache_hit=rec_data.get("cache_hit", True),
                response_time_ms=rec_data.get("response_time_ms", 0),
            )

            recommendations.append(recommendation)

        return recommendations

    def get_metrics(self) -> dict:
        """
        Servis metriklerini al (service + cache metrics)

        Returns:
            dict: Comprehensive metrics
        """
        avg_response_time = (
            self.total_response_time / self.total_requests
            if self.total_requests > 0
            else 0
        )

        cache_hit_rate = (
            (self.cache_hits / self.total_requests * 100)
            if self.total_requests > 0
            else 0
        )

        # Get multi-layer cache stats
        cache_stats = self.cache.get_stats()

        return {
            "service": {
                "total_requests": self.total_requests,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_hit_rate": f"{cache_hit_rate:.1f}%",
                "avg_response_time_ms": f"{avg_response_time:.0f}",
                "total_response_time_ms": f"{self.total_response_time:.0f}",
            },
            "cache": cache_stats,
        }


# Global instance (will be initialized in main.py)
_video_recommendation_service: VideoRecommendationService | None = None


async def get_video_recommendation_service() -> VideoRecommendationService:
    """
    Video recommendation service instance'ını al

    Returns:
        VideoRecommendationService: Service instance
    """
    global _video_recommendation_service

    if _video_recommendation_service is None:
        # Lazy initialization
        import os

        from core.multi_layer_cache import get_multi_layer_cache
        from services.advanced_youtube_search import advanced_youtube_search
        from services.semantic_youtube_search import semantic_youtube_search
        from services.turkish_content_filter import turkish_content_filter

        # Get multi-layer cache instance
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        cache = await get_multi_layer_cache(
            redis_url=redis_url, namespace="video_cache"
        )

        _video_recommendation_service = VideoRecommendationService(
            cache=cache,
            advanced_search=advanced_youtube_search,
            semantic_search=semantic_youtube_search,
            content_filter=turkish_content_filter,
        )

        logger.info("VideoRecommendationService instance created with MultiLayerCache")

    return _video_recommendation_service
