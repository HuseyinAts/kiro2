"""
YouTube Cache Manager Mixin

SQLite tabanli video ve arama cache yonetimi.
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from .models import DifficultyLevel, ExamType, SubjectType, VideoMetadata

if TYPE_CHECKING:
    from .discovery import YouTubeDiscovery

logger = logging.getLogger(__name__)


class CacheManagerMixin:
    """Cache yonetimi mixin'i"""

    # Type hints for mixin attributes
    db_path: Path
    cache_dir: Path

    def _init_database(self: "YouTubeDiscovery") -> None:
        """Cache veritabanini baslat"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS video_cache (
                    video_id TEXT PRIMARY KEY,
                    title TEXT,
                    channel TEXT,
                    channel_id TEXT,
                    duration TEXT,
                    view_count INTEGER,
                    upload_date TEXT,
                    thumbnail TEXT,
                    description TEXT,
                    quality_score REAL,
                    subject TEXT,
                    difficulty TEXT,
                    exam_type TEXT,
                    language TEXT,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS channel_rss (
                    channel_id TEXT PRIMARY KEY,
                    channel_name TEXT,
                    rss_url TEXT,
                    last_check TIMESTAMP,
                    video_count INTEGER DEFAULT 0,
                    quality_rating REAL DEFAULT 0.0
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS search_cache (
                    query_hash TEXT PRIMARY KEY,
                    query TEXT,
                    results TEXT,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

    def _get_cached_videos(
        self: "YouTubeDiscovery",
        subject: SubjectType,
        difficulty: DifficultyLevel,
        exam_type: ExamType,
        max_age_hours: int = 24,
    ) -> List[VideoMetadata]:
        """Cache'den video listesi al"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM video_cache
                WHERE subject = ? AND difficulty = ? AND exam_type = ?
                AND last_updated > ?
                ORDER BY quality_score DESC
            """,
                (subject.value, difficulty.value, exam_type.value, cutoff_time),
            )

            videos = []
            for row in cursor.fetchall():
                video = VideoMetadata(
                    video_id=row[0],
                    title=row[1],
                    channel=row[2],
                    channel_id=row[3],
                    duration=row[4],
                    view_count=row[5],
                    upload_date=row[6],
                    thumbnail=row[7],
                    description=row[8],
                    quality_score=row[9],
                    subject=SubjectType(row[10]),
                    difficulty=DifficultyLevel(row[11]),
                    exam_type=ExamType(row[12]),
                )
                videos.append(video)

            return videos

    def _cache_video(self: "YouTubeDiscovery", video: VideoMetadata) -> None:
        """Video'yu cache'e kaydet"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO video_cache
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
                (
                    video.video_id,
                    video.title,
                    video.channel,
                    video.channel_id,
                    video.duration,
                    video.view_count,
                    video.upload_date,
                    video.thumbnail,
                    video.description,
                    video.quality_score,
                    video.subject.value,
                    video.difficulty.value,
                    video.exam_type.value,
                    video.language,
                ),
            )

    def _get_cached_search(
        self: "YouTubeDiscovery", query_hash: str, max_age_hours: int = 6
    ) -> Optional[List[Dict]]:
        """Arama sonucunu cache'den al"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT results FROM search_cache
                WHERE query_hash = ? AND cached_at > ?
            """,
                (query_hash, cutoff_time),
            )

            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None

    def _cache_search_result(
        self: "YouTubeDiscovery", query_hash: str, query: str, results: List[Dict]
    ) -> None:
        """Arama sonucunu cache'e kaydet"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO search_cache
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (query_hash, query, json.dumps(results)),
            )

    def clear_expired_cache(
        self: "YouTubeDiscovery", max_age_hours: int = 72
    ) -> int:
        """Suresi dolmus cache kayitlarini temizle"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        with sqlite3.connect(self.db_path) as conn:
            # Video cache temizle
            cursor = conn.execute(
                "DELETE FROM video_cache WHERE last_updated < ?", (cutoff_time,)
            )
            video_count = cursor.rowcount

            # Search cache temizle
            cursor = conn.execute(
                "DELETE FROM search_cache WHERE cached_at < ?", (cutoff_time,)
            )
            search_count = cursor.rowcount

            total_deleted = video_count + search_count
            logger.info(f"Expired cache cleared: {total_deleted} records")
            return total_deleted

    def get_cache_stats(self: "YouTubeDiscovery") -> Dict:
        """Cache istatistiklerini al"""
        with sqlite3.connect(self.db_path) as conn:
            video_count = conn.execute(
                "SELECT COUNT(*) FROM video_cache"
            ).fetchone()[0]
            search_count = conn.execute(
                "SELECT COUNT(*) FROM search_cache"
            ).fetchone()[0]
            channel_count = conn.execute(
                "SELECT COUNT(*) FROM channel_rss"
            ).fetchone()[0]

            return {
                "video_cache_count": video_count,
                "search_cache_count": search_count,
                "channel_count": channel_count,
            }
