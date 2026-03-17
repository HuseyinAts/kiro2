"""
YouTube Module - Database Operations
=====================================
SQLite cache operations for YouTube video discovery.

Extracted from youtube_discovery.py
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from .models import DifficultyLevel, ExamType, SubjectType, VideoMetadata

logger = logging.getLogger(__name__)


class YouTubeCacheDB:
    """SQLite cache database for YouTube videos."""

    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.db_path = self.cache_dir / "youtube_cache.db"
        self._init_database()

    def _init_database(self) -> None:
        """Cache veritabanını başlat"""
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

    def get_cached_videos(
        self,
        subject: SubjectType,
        difficulty: DifficultyLevel,
        exam_type: ExamType,
        max_age_hours: int = 24,
    ) -> list[VideoMetadata]:
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

    def cache_video(self, video: VideoMetadata) -> None:
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

    def get_cached_search(
        self, query_hash: str, max_age_hours: int = 6
    ) -> list[dict] | None:
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

    def cache_search_result(
        self, query_hash: str, query: str, results: list[dict]
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


__all__ = ["YouTubeCacheDB"]
