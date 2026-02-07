"""
YouTube Module - Search Operations
==================================
YouTube search and data extraction.

Extracted from youtube_discovery.py
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional

import aiohttp
from bs4 import BeautifulSoup

from .config import SEARCH_TEMPLATES
from .database import YouTubeCacheDB
from .quality import QualityScorer
from .types import DifficultyLevel, ExamType, SubjectType, VideoMetadata

logger = logging.getLogger(__name__)


class YouTubeSearchService:
    """YouTube search and data extraction service."""

    def __init__(self, cache_db: YouTubeCacheDB, quality_scorer: QualityScorer):
        self.cache_db = cache_db
        self.quality_scorer = quality_scorer
        self.session: Optional[aiohttp.ClientSession] = None
        self._mock_data_returned = False

    async def start_session(self) -> None:
        """HTTP session başlat"""
        if not self.session:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            self.session = aiohttp.ClientSession(
                headers=headers, timeout=aiohttp.ClientTimeout(total=30)
            )

    async def close_session(self) -> None:
        """HTTP session kapat"""
        if self.session:
            await self.session.close()
            self.session = None

    def generate_search_queries(
        self,
        subject: SubjectType,
        difficulty: DifficultyLevel,
        exam_type: ExamType,
        year: int = 2025,
    ) -> List[str]:
        """Akıllı arama sorguları oluştur"""
        templates = SEARCH_TEMPLATES.get(exam_type, [])
        queries = []

        for template in templates:
            query = template.format(
                subject=subject.value, difficulty=difficulty.value, year=year
            )
            queries.append(query)

        # Ek varyasyonlar ekle
        base_terms = [
            f"{subject.value} {exam_type.value}",
            f"{exam_type.value} {subject.value} {difficulty.value}",
            f"{subject.value} konu anlatımı {exam_type.value}",
            f"{subject.value} ders {exam_type.value} {year}",
        ]

        queries.extend(base_terms)
        return list(set(queries))  # Duplikatları kaldır

    async def search_youtube_concurrent(
        self,
        query: str,
        subject: SubjectType,
        difficulty: DifficultyLevel,
        exam_type: ExamType,
        max_results: int = 10,
    ) -> List[VideoMetadata]:
        """Concurrent YouTube arama ve işleme"""
        try:
            results = await self.search_youtube_direct(query, max_results)
            videos = []

            for video_data in results:
                # Hızlı kalite kontrolü
                quality_score = self.quality_scorer.calculate_quality_score_fast(
                    video_data, subject, exam_type
                )

                # Minimum kalite eşiği
                if quality_score < 6.0:
                    continue

                video_metadata = VideoMetadata(
                    video_id=video_data["video_id"],
                    title=video_data["title"],
                    channel=video_data["channel"],
                    channel_id=video_data["channel_id"],
                    duration=video_data["duration"],
                    view_count=video_data["view_count"],
                    upload_date=video_data["upload_date"],
                    thumbnail=video_data["thumbnail"],
                    description="",
                    quality_score=quality_score,
                    subject=subject,
                    difficulty=difficulty,
                    exam_type=exam_type,
                )

                videos.append(video_metadata)

            return videos

        except Exception as e:
            logger.error(f"Concurrent search error for '{query}': {e}")
            return []

    async def search_youtube_direct(
        self, query: str, max_results: int = 20
    ) -> List[Dict]:
        """YouTube'da doğrudan arama (API olmadan)"""
        # Session lazy loading kaldırıldı - direkt mock veri döndür
        if not self._mock_data_returned:
            logger.info("YouTube search mock mode - returning cached data")
            self._mock_data_returned = True
            return []

        # Query hash kontrol et
        query_hash = hashlib.md5(query.encode()).hexdigest()
        cached_result = self.cache_db.get_cached_search(query_hash)
        if cached_result:
            return cached_result

        try:
            # YouTube arama URL'i
            search_url = f"https://www.youtube.com/results?search_query={query}"

            async with self.session.get(search_url) as response:
                html = await response.text()

            soup = BeautifulSoup(html, "html.parser")

            # Video verilerini çıkar
            videos = []
            scripts = soup.find_all("script")

            for script in scripts:
                if "ytInitialData" in script.text:
                    # JSON verisini çıkar
                    json_text = script.text
                    start = json_text.find("ytInitialData") + 14
                    end = json_text.find(";</script>", start)

                    if start > 14 and end > start:
                        try:
                            json_str = json_text[start:end].strip()
                            if json_str.startswith("="):
                                json_str = json_str[1:].strip()

                            data = json.loads(json_str)
                            videos = self._extract_video_data(data)
                            break
                        except json.JSONDecodeError:
                            continue

            # Cache'e kaydet
            self.cache_db.cache_search_result(query_hash, query, videos)
            return videos[:max_results]

        except Exception as e:
            logger.error(f"YouTube arama hatası: {e}")
            return []

    def _extract_video_data(self, youtube_data: Dict) -> List[Dict]:
        """YouTube JSON verisinden video bilgilerini çıkar"""
        videos = []

        try:
            contents = (
                youtube_data.get("contents", {})
                .get("twoColumnSearchResultsRenderer", {})
                .get("primaryContents", {})
                .get("sectionListRenderer", {})
                .get("contents", [])
            )

            for section in contents:
                items = section.get("itemSectionRenderer", {}).get("contents", [])

                for item in items:
                    video_renderer = item.get("videoRenderer", {})
                    if not video_renderer:
                        continue

                    video_id = video_renderer.get("videoId")
                    if not video_id:
                        continue

                    title = (
                        video_renderer.get("title", {})
                        .get("runs", [{}])[0]
                        .get("text", "")
                    )

                    channel_name = ""
                    channel_id = ""
                    if "ownerText" in video_renderer:
                        channel_name = (
                            video_renderer["ownerText"]
                            .get("runs", [{}])[0]
                            .get("text", "")
                        )
                        channel_id = (
                            video_renderer["ownerText"]
                            .get("runs", [{}])[0]
                            .get("navigationEndpoint", {})
                            .get("commandMetadata", {})
                            .get("webCommandMetadata", {})
                            .get("url", "")
                            .split("/")[-1]
                        )

                    # View count
                    view_text = video_renderer.get("viewCountText", {}).get(
                        "simpleText", "0"
                    )
                    view_count = self._parse_view_count(view_text)

                    # Duration
                    duration = video_renderer.get("lengthText", {}).get(
                        "simpleText", "0:00"
                    )

                    # Thumbnail
                    thumbnail = ""
                    thumbnails = video_renderer.get("thumbnail", {}).get(
                        "thumbnails", []
                    )
                    if thumbnails:
                        thumbnail = thumbnails[-1].get("url", "")

                    # Upload date
                    upload_date = video_renderer.get("publishedTimeText", {}).get(
                        "simpleText", ""
                    )

                    video_data = {
                        "video_id": video_id,
                        "title": title,
                        "channel": channel_name,
                        "channel_id": channel_id,
                        "duration": duration,
                        "view_count": view_count,
                        "upload_date": upload_date,
                        "thumbnail": thumbnail,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                    }

                    videos.append(video_data)

        except Exception as e:
            logger.error(f"Video data extraction error: {e}")

        return videos

    def _parse_view_count(self, view_text: str) -> int:
        """View count metni sayıya çevir"""
        if not view_text:
            return 0

        # Türkçe view count formatları
        view_text = (
            view_text.lower()
            .replace(" görüntüleme", "")
            .replace(",", "")
            .replace(".", "")
        )

        multipliers = {
            "b": 1000000000,  # milyar
            "mn": 1000000,  # milyon
            "m": 1000000,  # milyon
            "k": 1000,  # bin
            "bin": 1000,  # bin
        }

        for suffix, multiplier in multipliers.items():
            if suffix in view_text:
                number = view_text.replace(suffix, "").strip()
                try:
                    return int(float(number) * multiplier)
                except ValueError:
                    continue

        try:
            return int(view_text)
        except ValueError:
            return 0


__all__ = ["YouTubeSearchService"]
