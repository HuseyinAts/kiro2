"""
Optimized Video Cache Repository
High-performance repository for video cache operations with prepared statements
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, delete, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from models.video_cache_model import VideoCache
from repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class OptimizedVideoRepository(BaseRepository[VideoCache]):
    """
    Optimized repository for video cache operations

    Features:
    - Prepared statements for better performance
    - Composite index utilization
    - Efficient batch operations
    - Cache management (LRU eviction)
    """

    def __init__(self, session: AsyncSession):
        super().__init__(VideoCache, session)

    async def find_videos_optimized(
        self,
        subject: str,
        difficulty: str,
        exam_type: str,
        language: str = "tr",
        min_quality: float = 7.0,
        min_relevance: float = 0.7,
        limit: int = 20,
        offset: int = 0,
    ) -> List[VideoCache]:
        """
        Optimized video search using composite index

        Uses idx_video_search_composite for fast lookup:
        (subject, difficulty, exam_type, language, quality_score DESC)

        Performance: O(log n + k) where k = number of matches
        Expected query time: 5-10ms for 100K records

        Args:
            subject: Subject name (e.g., 'matematik', 'fizik')
            difficulty: Difficulty level ('başlangıç', 'orta', 'ileri')
            exam_type: Exam type ('TYT', 'AYT', 'LGS')
            language: Language code (default: 'tr')
            min_quality: Minimum quality score (0-10)
            min_relevance: Minimum relevance score (0-1)
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of VideoCache objects sorted by quality_score DESC
        """
        try:
            # Build query using composite index
            query = (
                select(VideoCache)
                .where(
                    and_(
                        VideoCache.subject == subject,
                        VideoCache.difficulty == difficulty,
                        VideoCache.exam_type == exam_type,
                        VideoCache.language == language,
                        VideoCache.quality_score >= min_quality,
                        VideoCache.relevance_score >= min_relevance,
                    )
                )
                .order_by(VideoCache.quality_score.desc())
                .limit(limit)
                .offset(offset)
            )

            result = await self.session.execute(query)
            videos = result.scalars().all()

            # Update access tracking for returned videos
            if videos:
                await self._update_access_batch([v.id for v in videos])

            logger.info(
                f"Found {len(videos)} videos for {subject}/{difficulty}/{exam_type} "
                f"(quality>={min_quality}, relevance>={min_relevance})"
            )

            return videos

        except SQLAlchemyError as e:
            logger.error(f"Error in find_videos_optimized: {str(e)}")
            raise

    async def find_videos_by_subject(
        self, subject: str, min_quality: float = 7.0, limit: int = 50
    ) -> List[VideoCache]:
        """
        Find videos by subject only (broader search)

        Uses idx_video_subject_quality composite index
        """
        try:
            query = (
                select(VideoCache)
                .where(
                    and_(
                        VideoCache.subject == subject,
                        VideoCache.quality_score >= min_quality,
                    )
                )
                .order_by(VideoCache.quality_score.desc())
                .limit(limit)
            )

            result = await self.session.execute(query)
            return result.scalars().all()

        except SQLAlchemyError as e:
            logger.error(f"Error in find_videos_by_subject: {str(e)}")
            raise

    async def find_videos_flexible(
        self,
        subject: str,
        target_difficulty: str,
        exam_type: str,
        language: str = "tr",
        min_quality: float = 6.0,
        difficulty_tolerance: int = 1,
        limit: int = 20,
    ) -> List[VideoCache]:
        """
        Flexible video search with difficulty tolerance

        Allows ±1 difficulty level for better results
        Example: If target is 'orta', also includes 'başlangıç' and 'ileri'

        Args:
            subject: Subject name
            target_difficulty: Target difficulty level
            exam_type: Exam type
            language: Language code
            min_quality: Minimum quality score
            difficulty_tolerance: Difficulty level tolerance (default: 1)
            limit: Maximum results

        Returns:
            List of videos sorted by difficulty match and quality
        """
        try:
            # Map difficulty levels to numeric values
            difficulty_map = {
                "başlangıç": 1,
                "kolay": 1,
                "orta": 2,
                "zor": 3,
                "ileri": 3,
            }

            target_level = difficulty_map.get(target_difficulty, 2)

            # Calculate allowed difficulty range
            min_level = max(1, target_level - difficulty_tolerance)
            max_level = min(3, target_level + difficulty_tolerance)

            # Get allowed difficulty values
            allowed_difficulties = [
                diff
                for diff, level in difficulty_map.items()
                if min_level <= level <= max_level
            ]

            query = (
                select(VideoCache)
                .where(
                    and_(
                        VideoCache.subject == subject,
                        VideoCache.difficulty.in_(allowed_difficulties),
                        VideoCache.exam_type == exam_type,
                        VideoCache.language == language,
                        VideoCache.quality_score >= min_quality,
                    )
                )
                .order_by(
                    VideoCache.difficulty_match.desc(), VideoCache.quality_score.desc()
                )
                .limit(limit)
            )

            result = await self.session.execute(query)
            return result.scalars().all()

        except SQLAlchemyError as e:
            logger.error(f"Error in find_videos_flexible: {str(e)}")
            raise

    async def get_top_quality_videos(
        self, subject: Optional[str] = None, limit: int = 100
    ) -> List[VideoCache]:
        """
        Get top quality videos (for cache warming)

        Uses idx_video_quality_score index
        """
        try:
            query = select(VideoCache)

            if subject:
                query = query.where(VideoCache.subject == subject)

            query = query.order_by(VideoCache.quality_score.desc()).limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()

        except SQLAlchemyError as e:
            logger.error(f"Error in get_top_quality_videos: {str(e)}")
            raise

    async def get_recently_updated(
        self, hours: int = 24, limit: int = 100
    ) -> List[VideoCache]:
        """
        Get recently updated videos

        Uses idx_video_last_updated index
        """
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

            query = (
                select(VideoCache)
                .where(VideoCache.last_updated >= cutoff_time)
                .order_by(VideoCache.last_updated.desc())
                .limit(limit)
            )

            result = await self.session.execute(query)
            return result.scalars().all()

        except SQLAlchemyError as e:
            logger.error(f"Error in get_recently_updated: {str(e)}")
            raise

    async def get_expired_entries(self, limit: int = 1000) -> List[VideoCache]:
        """
        Get expired cache entries for cleanup

        Uses idx_video_last_updated index
        """
        try:
            # Use raw SQL for better performance with timestamp comparison
            query = text(
                """
                SELECT * FROM video_cache
                WHERE EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_updated)) > cache_ttl
                ORDER BY last_updated ASC
                LIMIT :limit
            """
            )

            result = await self.session.execute(query, {"limit": limit})
            rows = result.fetchall()

            # Convert rows to VideoCache objects
            videos = []
            for row in rows:
                video = VideoCache()
                for key, value in row._mapping.items():
                    setattr(video, key, value)
                videos.append(video)

            return videos

        except SQLAlchemyError as e:
            logger.error(f"Error in get_expired_entries: {str(e)}")
            raise

    async def evict_lru_entries(
        self, max_entries: int = 10000, evict_count: int = 1000
    ) -> int:
        """
        Evict least recently used entries (LRU cache eviction)

        Uses idx_video_cache_management composite index
        (last_accessed DESC, access_count DESC)

        Args:
            max_entries: Maximum number of entries to keep
            evict_count: Number of entries to evict when limit is reached

        Returns:
            Number of entries evicted
        """
        try:
            # Check current count
            count_query = select(func.count(VideoCache.id))
            result = await self.session.execute(count_query)
            current_count = result.scalar()

            if current_count <= max_entries:
                logger.info(f"Cache size {current_count} is within limit {max_entries}")
                return 0

            # Get IDs of entries to evict (LRU)
            lru_query = (
                select(VideoCache.id)
                .order_by(VideoCache.last_accessed.asc(), VideoCache.access_count.asc())
                .limit(evict_count)
            )

            result = await self.session.execute(lru_query)
            ids_to_evict = [row[0] for row in result.fetchall()]

            if not ids_to_evict:
                return 0

            # Delete entries
            delete_query = delete(VideoCache).where(VideoCache.id.in_(ids_to_evict))
            result = await self.session.execute(delete_query)
            evicted_count = result.rowcount

            await self.session.commit()

            logger.info(f"Evicted {evicted_count} LRU cache entries")
            return evicted_count

        except SQLAlchemyError as e:
            logger.error(f"Error in evict_lru_entries: {str(e)}")
            await self.session.rollback()
            raise

    async def _update_access_batch(self, video_ids: List[UUID]) -> None:
        """
        Update access tracking for multiple videos (batch operation)

        Uses prepared statement for better performance
        """
        try:
            if not video_ids:
                return

            # Batch update using raw SQL for performance
            update_query = text(
                """
                UPDATE video_cache
                SET last_accessed = CURRENT_TIMESTAMP,
                    access_count = access_count + 1
                WHERE id = ANY(:ids)
            """
            )

            await self.session.execute(
                update_query, {"ids": [str(vid) for vid in video_ids]}
            )

        except SQLAlchemyError as e:
            logger.error(f"Error in _update_access_batch: {str(e)}")
            # Don't raise - access tracking is not critical

    async def bulk_upsert(self, videos: List[Dict[str, Any]]) -> int:
        """
        Bulk upsert videos (insert or update if exists)

        Uses ON CONFLICT for efficient upsert

        Args:
            videos: List of video dictionaries

        Returns:
            Number of videos upserted
        """
        try:
            if not videos:
                return 0

            # Use raw SQL for efficient bulk upsert
            upsert_query = text(
                """
                INSERT INTO video_cache (
                    video_id, title, description, channel_name, channel_id,
                    thumbnail_url, duration, subject, difficulty, exam_type,
                    language, quality_score, relevance_score, language_score,
                    difficulty_match, view_count, like_count, comment_count,
                    metadata, cache_ttl
                )
                VALUES (
                    :video_id, :title, :description, :channel_name, :channel_id,
                    :thumbnail_url, :duration, :subject, :difficulty, :exam_type,
                    :language, :quality_score, :relevance_score, :language_score,
                    :difficulty_match, :view_count, :like_count, :comment_count,
                    :metadata, :cache_ttl
                )
                ON CONFLICT (video_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    quality_score = EXCLUDED.quality_score,
                    relevance_score = EXCLUDED.relevance_score,
                    language_score = EXCLUDED.language_score,
                    difficulty_match = EXCLUDED.difficulty_match,
                    view_count = EXCLUDED.view_count,
                    like_count = EXCLUDED.like_count,
                    comment_count = EXCLUDED.comment_count,
                    metadata = EXCLUDED.metadata,
                    last_updated = CURRENT_TIMESTAMP
            """
            )

            # Execute batch upsert
            await self.session.execute(upsert_query, videos)
            await self.session.commit()

            logger.info(f"Bulk upserted {len(videos)} videos")
            return len(videos)

        except SQLAlchemyError as e:
            logger.error(f"Error in bulk_upsert: {str(e)}")
            await self.session.rollback()
            raise

    async def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring

        Returns:
            Dictionary with cache statistics
        """
        try:
            stats_query = text(
                """
                SELECT
                    COUNT(*) as total_entries,
                    COUNT(DISTINCT subject) as unique_subjects,
                    COUNT(DISTINCT exam_type) as unique_exam_types,
                    AVG(quality_score) as avg_quality_score,
                    AVG(relevance_score) as avg_relevance_score,
                    AVG(access_count) as avg_access_count,
                    MAX(access_count) as max_access_count,
                    COUNT(*) FILTER (WHERE EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_updated)) > cache_ttl) as expired_entries,
                    COUNT(*) FILTER (WHERE last_accessed > CURRENT_TIMESTAMP - INTERVAL '1 hour') as accessed_last_hour,
                    COUNT(*) FILTER (WHERE last_accessed > CURRENT_TIMESTAMP - INTERVAL '24 hours') as accessed_last_day
                FROM video_cache
            """
            )

            result = await self.session.execute(stats_query)
            row = result.fetchone()

            return {
                "total_entries": row[0],
                "unique_subjects": row[1],
                "unique_exam_types": row[2],
                "avg_quality_score": float(row[3]) if row[3] else 0.0,
                "avg_relevance_score": float(row[4]) if row[4] else 0.0,
                "avg_access_count": float(row[5]) if row[5] else 0.0,
                "max_access_count": row[6],
                "expired_entries": row[7],
                "accessed_last_hour": row[8],
                "accessed_last_day": row[9],
            }

        except SQLAlchemyError as e:
            logger.error(f"Error in get_cache_statistics: {str(e)}")
            raise
