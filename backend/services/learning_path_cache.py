"""
Learning Path Cache Service - P1.8
Requirements: Cache learning path data to improve performance

Features:
- Cache learning path creation results
- Cache resource search results
- Cache quiz data
- Cache student progress
- Cache completion status
- Intelligent cache invalidation
- Profile-based cache keys
"""

import hashlib
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from core.multi_layer_cache import MultiLayerCache
from core.structured_logger import get_logger
from core.metrics_collector import get_metrics_collector

logger = get_logger(__name__)


class LearningPathCache:
    """
    Learning Path specific caching layer

    Provides high-level caching for:
    - Learning path creation (AI agent results)
    - Resource search results (video recommendations)
    - Quiz data
    - Student progress
    - Completion status

    Cache Keys:
    - learning_path:{student_id}:{subject_hash}
    - resources:{subject}:{difficulty}:{keywords_hash}
    - quiz:{quiz_id}
    - progress:{path_id}
    - completion:{path_id}
    """

    # Cache TTL values (in seconds)
    LEARNING_PATH_TTL = 3600  # 1 hour - learning paths
    RESOURCE_SEARCH_TTL = 1800  # 30 minutes - search results
    QUIZ_TTL = 7200  # 2 hours - quiz data (relatively static)
    PROGRESS_TTL = 300  # 5 minutes - student progress (frequently updated)
    COMPLETION_TTL = 600  # 10 minutes - completion status
    PROFILE_TTL = 1800  # 30 minutes - student profiles

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize Learning Path cache

        Args:
            redis_url: Redis connection URL
        """
        self.cache = MultiLayerCache(
            redis_url=redis_url,
            l1_max_size=100,  # 100 most accessed items in memory
            default_ttl=self.LEARNING_PATH_TTL,
            namespace="learning_path",
        )
        self.metrics = get_metrics_collector()
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize cache connection

        Returns:
            True if successful, False otherwise
        """
        if self._initialized:
            return True

        success = await self.cache.initialize()
        if success:
            logger.info(
                "learning_path_cache_initialized", redis_url=self.cache.redis_url
            )
            self._initialized = True
        else:
            logger.warning("learning_path_cache_init_failed", fallback="in_memory_only")
            self._initialized = True  # Continue with L1 only

        return success

    async def close(self):
        """Close cache connections"""
        await self.cache.close()
        logger.info("learning_path_cache_closed")

    def _make_profile_hash(self, student_profile: Dict[str, Any]) -> str:
        """
        Create hash from student profile for cache key

        Only includes fields that affect learning path generation:
        - grade_level
        - learning_style
        - interests
        - difficulty_preference

        Args:
            student_profile: Student profile data

        Returns:
            MD5 hash of relevant profile fields
        """
        # Extract only relevant fields for learning path
        relevant_fields = {
            "grade_level": student_profile.get("grade_level"),
            "learning_style": student_profile.get("learning_style"),
            "interests": student_profile.get("interests", []),
            "difficulty_preference": student_profile.get("difficulty_preference"),
        }

        # Create deterministic JSON string (sorted keys)
        profile_json = json.dumps(relevant_fields, sort_keys=True)

        # Return MD5 hash (first 16 chars for brevity)
        return hashlib.md5(profile_json.encode()).hexdigest()[:16]

    def _make_search_hash(
        self, subject: str, difficulty: Optional[str], keywords: Optional[List[str]]
    ) -> str:
        """
        Create hash for resource search parameters

        Args:
            subject: Subject to search (e.g., "matematik")
            difficulty: Difficulty level
            keywords: Additional search keywords

        Returns:
            MD5 hash of search parameters
        """
        search_params = {
            "subject": subject.lower(),
            "difficulty": difficulty.lower() if difficulty else None,
            "keywords": sorted([k.lower() for k in keywords]) if keywords else [],
        }

        search_json = json.dumps(search_params, sort_keys=True)
        return hashlib.md5(search_json.encode()).hexdigest()[:16]

    # ============================================================================
    # Learning Path Creation Cache
    # ============================================================================

    async def get_learning_path(
        self, student_id: str, subject: str, student_profile: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached learning path

        Args:
            student_id: Student ID
            subject: Subject (e.g., "matematik")
            student_profile: Student profile data

        Returns:
            Cached learning path or None
        """
        profile_hash = self._make_profile_hash(student_profile)
        cache_key = f"path:{student_id}:{subject}:{profile_hash}"

        result = await self.cache.get(cache_key)

        if result:
            logger.info(
                "learning_path_cache_hit",
                student_id=student_id,
                subject=subject,
                cache_key=cache_key,
            )

        return result

    async def set_learning_path(
        self,
        student_id: str,
        subject: str,
        student_profile: Dict[str, Any],
        learning_path: Dict[str, Any],
    ) -> bool:
        """
        Cache learning path

        Args:
            student_id: Student ID
            subject: Subject
            student_profile: Student profile data
            learning_path: Learning path to cache

        Returns:
            True if successful
        """
        profile_hash = self._make_profile_hash(student_profile)
        cache_key = f"path:{student_id}:{subject}:{profile_hash}"

        success = await self.cache.set(
            cache_key, learning_path, ttl=self.LEARNING_PATH_TTL
        )

        if success:
            logger.info(
                "learning_path_cached",
                student_id=student_id,
                subject=subject,
                cache_key=cache_key,
                ttl=self.LEARNING_PATH_TTL,
            )

        return success

    async def invalidate_learning_path(
        self, student_id: str, subject: Optional[str] = None
    ) -> int:
        """
        Invalidate learning path cache for student

        Args:
            student_id: Student ID
            subject: Optional subject filter (if None, invalidates all subjects)

        Returns:
            Number of entries invalidated
        """
        # For now, we need to invalidate by pattern
        # This is a limitation - ideally we'd track all cache keys per student

        # Invalidate specific subject
        if subject:
            # We can't know the profile hash, so we use wildcard invalidation
            pattern = f"path:{student_id}:{subject}:*"
            count = await self.cache.delete_pattern(pattern)
        else:
            # Invalidate all subjects for student
            pattern = f"path:{student_id}:*"
            count = await self.cache.delete_pattern(pattern)

        logger.info(
            "learning_path_cache_invalidated",
            student_id=student_id,
            subject=subject,
            count=count,
        )

        return count

    # ============================================================================
    # Resource Search Cache
    # ============================================================================

    async def get_resource_search(
        self,
        subject: str,
        difficulty: Optional[str] = None,
        keywords: Optional[List[str]] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached resource search results

        Args:
            subject: Subject to search
            difficulty: Difficulty level
            keywords: Additional keywords

        Returns:
            Cached search results or None
        """
        search_hash = self._make_search_hash(subject, difficulty, keywords)
        cache_key = f"resources:{search_hash}"

        result = await self.cache.get(cache_key)

        if result:
            logger.info(
                "resource_search_cache_hit",
                subject=subject,
                difficulty=difficulty,
                cache_key=cache_key,
            )

        return result

    async def set_resource_search(
        self,
        subject: str,
        resources: List[Dict[str, Any]],
        difficulty: Optional[str] = None,
        keywords: Optional[List[str]] = None,
    ) -> bool:
        """
        Cache resource search results

        Args:
            subject: Subject searched
            resources: Search results to cache
            difficulty: Difficulty level
            keywords: Additional keywords

        Returns:
            True if successful
        """
        search_hash = self._make_search_hash(subject, difficulty, keywords)
        cache_key = f"resources:{search_hash}"

        success = await self.cache.set(
            cache_key, resources, ttl=self.RESOURCE_SEARCH_TTL
        )

        if success:
            logger.info(
                "resource_search_cached",
                subject=subject,
                difficulty=difficulty,
                cache_key=cache_key,
                result_count=len(resources),
                ttl=self.RESOURCE_SEARCH_TTL,
            )

        return success

    # ============================================================================
    # Quiz Cache
    # ============================================================================

    async def get_quiz(self, quiz_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached quiz data

        Args:
            quiz_id: Quiz ID

        Returns:
            Cached quiz or None
        """
        cache_key = f"quiz:{quiz_id}"
        result = await self.cache.get(cache_key)

        if result:
            logger.debug("quiz_cache_hit", quiz_id=quiz_id)

        return result

    async def set_quiz(self, quiz_id: str, quiz_data: Dict[str, Any]) -> bool:
        """
        Cache quiz data

        Args:
            quiz_id: Quiz ID
            quiz_data: Quiz to cache

        Returns:
            True if successful
        """
        cache_key = f"quiz:{quiz_id}"

        success = await self.cache.set(cache_key, quiz_data, ttl=self.QUIZ_TTL)

        if success:
            logger.debug("quiz_cached", quiz_id=quiz_id, ttl=self.QUIZ_TTL)

        return success

    async def invalidate_quiz(self, quiz_id: str) -> bool:
        """
        Invalidate quiz cache

        Args:
            quiz_id: Quiz ID

        Returns:
            True if successful
        """
        cache_key = f"quiz:{quiz_id}"
        success = await self.cache.delete(cache_key)

        if success:
            logger.info("quiz_cache_invalidated", quiz_id=quiz_id)

        return success

    # ============================================================================
    # Student Progress Cache
    # ============================================================================

    async def get_progress(self, path_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached student progress

        Args:
            path_id: Learning path ID

        Returns:
            Cached progress or None
        """
        cache_key = f"progress:{path_id}"
        result = await self.cache.get(cache_key)

        if result:
            logger.debug("progress_cache_hit", path_id=path_id)

        return result

    async def set_progress(self, path_id: str, progress: Dict[str, Any]) -> bool:
        """
        Cache student progress

        Args:
            path_id: Learning path ID
            progress: Progress data to cache

        Returns:
            True if successful
        """
        cache_key = f"progress:{path_id}"

        success = await self.cache.set(cache_key, progress, ttl=self.PROGRESS_TTL)

        if success:
            logger.debug("progress_cached", path_id=path_id, ttl=self.PROGRESS_TTL)

        return success

    async def invalidate_progress(self, path_id: str) -> bool:
        """
        Invalidate progress cache (called after progress update)

        Args:
            path_id: Learning path ID

        Returns:
            True if successful
        """
        cache_key = f"progress:{path_id}"
        success = await self.cache.delete(cache_key)

        if success:
            logger.debug("progress_cache_invalidated", path_id=path_id)

        return success

    # ============================================================================
    # Completion Status Cache
    # ============================================================================

    async def get_completion(self, path_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached completion status

        Args:
            path_id: Learning path ID

        Returns:
            Cached completion status or None
        """
        cache_key = f"completion:{path_id}"
        result = await self.cache.get(cache_key)

        if result:
            logger.debug("completion_cache_hit", path_id=path_id)

        return result

    async def set_completion(self, path_id: str, completion: Dict[str, Any]) -> bool:
        """
        Cache completion status

        Args:
            path_id: Learning path ID
            completion: Completion data to cache

        Returns:
            True if successful
        """
        cache_key = f"completion:{path_id}"

        success = await self.cache.set(cache_key, completion, ttl=self.COMPLETION_TTL)

        if success:
            logger.debug("completion_cached", path_id=path_id, ttl=self.COMPLETION_TTL)

        return success

    async def invalidate_completion(self, path_id: str) -> bool:
        """
        Invalidate completion cache (called after completion update)

        Args:
            path_id: Learning path ID

        Returns:
            True if successful
        """
        cache_key = f"completion:{path_id}"
        success = await self.cache.delete(cache_key)

        if success:
            logger.debug("completion_cache_invalidated", path_id=path_id)

        return success

    # ============================================================================
    # Student Profile Cache
    # ============================================================================

    async def get_student_profile(self, student_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached student profile

        Args:
            student_id: Student ID

        Returns:
            Cached profile or None
        """
        cache_key = f"profile:{student_id}"
        result = await self.cache.get(cache_key)

        if result:
            logger.debug("profile_cache_hit", student_id=student_id)

        return result

    async def set_student_profile(
        self, student_id: str, profile: Dict[str, Any]
    ) -> bool:
        """
        Cache student profile

        Args:
            student_id: Student ID
            profile: Profile data to cache

        Returns:
            True if successful
        """
        cache_key = f"profile:{student_id}"

        success = await self.cache.set(cache_key, profile, ttl=self.PROFILE_TTL)

        if success:
            logger.debug("profile_cached", student_id=student_id, ttl=self.PROFILE_TTL)

        return success

    async def invalidate_student_profile(self, student_id: str) -> bool:
        """
        Invalidate profile cache (called after profile update)

        Also invalidates all learning paths for this student since profile affects path generation

        Args:
            student_id: Student ID

        Returns:
            True if successful
        """
        # Invalidate profile
        profile_key = f"profile:{student_id}"
        await self.cache.delete(profile_key)

        # Invalidate all learning paths for this student
        await self.invalidate_learning_path(student_id)

        logger.info(
            "student_cache_invalidated",
            student_id=student_id,
            invalidated=["profile", "learning_paths"],
        )

        return True

    # ============================================================================
    # Cache Statistics & Health
    # ============================================================================

    def get_cache_metrics(self) -> Dict[str, Any]:
        """
        Get cache performance metrics

        Returns:
            Dictionary with cache statistics
        """
        return self.cache.metrics.to_dict()

    async def health_check(self) -> Dict[str, Any]:
        """
        Check cache health

        Returns:
            Health status dictionary
        """
        health = {
            "initialized": self._initialized,
            "redis_enabled": self.cache._redis_enabled,
            "l1_cache_size": len(self.cache._l1_cache),
            "l1_cache_max": self.cache.l1_max_size,
            "metrics": self.get_cache_metrics(),
        }

        # Test Redis connection
        if self.cache._redis:
            try:
                await self.cache._redis.ping()
                health["redis_status"] = "healthy"
            except Exception as e:
                health["redis_status"] = "unhealthy"
                health["redis_error"] = str(e)
        else:
            health["redis_status"] = "disabled"

        return health


# ============================================================================
# Singleton instance
# ============================================================================

_learning_path_cache_instance: Optional[LearningPathCache] = None


def get_learning_path_cache(
    redis_url: str = "redis://localhost:6379/0",
) -> LearningPathCache:
    """
    Get singleton Learning Path cache instance

    Args:
        redis_url: Redis connection URL

    Returns:
        LearningPathCache instance
    """
    global _learning_path_cache_instance

    if _learning_path_cache_instance is None:
        _learning_path_cache_instance = LearningPathCache(redis_url=redis_url)

    return _learning_path_cache_instance
