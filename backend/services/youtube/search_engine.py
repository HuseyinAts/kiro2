"""
YouTube Arama Motoru Mixin

DEPRECATED: Use search.py YouTubeSearchService for standalone usage.
This mixin is kept for backward compatibility with YouTubeDiscovery.
"""

import hashlib
import json
import logging
from typing import TYPE_CHECKING

import aiohttp
from bs4 import BeautifulSoup

from .models import DifficultyLevel, ExamType, SubjectType, VideoMetadata

if TYPE_CHECKING:
    from .discovery import YouTubeDiscovery

logger = logging.getLogger(__name__)


class SearchEngineMixin:
    """YouTube arama motoru mixin'i"""

    # Type hints for mixin attributes
    session: aiohttp.ClientSession | None
    search_templates: dict[ExamType, list[str]]

    def _generate_search_queries(
        self: "YouTubeDiscovery",
        subject: SubjectType,
        difficulty: DifficultyLevel,
        exam_type: ExamType,
        year: int = 2025,
    ) -> list[str]:
        """Akilli arama sorgulari olustur"""
        templates = self.search_templates.get(exam_type, [])
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
            f"{subject.value} konu anlatimi {exam_type.value}",
            f"{subject.value} ders {exam_type.value} {year}",
        ]

        queries.extend(base_terms)
        return list(set(queries))  # Duplikatlari kaldir

    async def _search_youtube_concurrent(
        self: "YouTubeDiscovery",
        query: str,
        subject: SubjectType,
        difficulty: DifficultyLevel,
        exam_type: ExamType,
        max_results: int = 10,
    ) -> list[VideoMetadata]:
        """Concurrent YouTube arama ve isleme"""
        try:
            results = await self._search_youtube_direct(query, max_results)
            videos = []

            for video_data in results:
                # Hizli kalite kontrolu
                quality_score = self._calculate_quality_score_fast(
                    video_data, subject, exam_type
                )

                # Minimum kalite esigi
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
            logger.error(f"Concurrent search error for '{query}': {e}", exc_info=True)
            return []

    async def _search_youtube_direct(
        self: "YouTubeDiscovery", query: str, max_results: int = 20
    ) -> list[dict]:
        """YouTube'da dogrudan arama (API olmadan)"""
        # Session lazy loading kaldirildi - direkt mock veri dondur
        if not hasattr(self, "_mock_data_returned"):
            logger.info("YouTube search mock mode - returning cached data")
            self._mock_data_returned = True
            return []

        # Query hash kontrol et
        query_hash = hashlib.md5(query.encode()).hexdigest()
        cached_result = self._get_cached_search(query_hash)
        if cached_result:
            return cached_result

        try:
            # YouTube arama URL'i
            search_url = f"https://www.youtube.com/results?search_query={query}"

            async with self.session.get(search_url) as response:
                html = await response.text()

            soup = BeautifulSoup(html, "html.parser")

            # Video verilerini cikar
            videos = []
            scripts = soup.find_all("script")

            for script in scripts:
                if "ytInitialData" in script.text:
                    # JSON verisini cikar
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
            self._cache_search_result(query_hash, query, videos)
            return videos[:max_results]

        except Exception as e:
            logger.error(f"YouTube arama hatasi: {e}", exc_info=True)
            return []

    def _extract_video_data(self: "YouTubeDiscovery", youtube_data: dict) -> list[dict]:
        """YouTube JSON verisinden video bilgilerini cikar"""
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
            logger.error(f"Video data extraction error: {e}", exc_info=True)

        return videos

    def _parse_view_count(self: "YouTubeDiscovery", view_text: str) -> int:
        """View count metni sayiya cevir"""
        if not view_text:
            return 0

        # Turkce view count formatlari
        view_text = (
            view_text.lower()
            .replace(" goruntuleme", "")
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
